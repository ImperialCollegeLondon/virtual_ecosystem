"""The ''animal'' module provides animal module functionality.

Notes:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
"""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil, exp, sqrt

from numpy import timedelta64

import virtual_ecosystem.models.animal.scaling_functions as sf
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_traits import DietType
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.decay import (
    CarcassPool,
    HerbivoryWaste,
    find_decay_consumed_split,
)
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup
from virtual_ecosystem.models.animal.plant_resources import PlantResources
from virtual_ecosystem.models.animal.protocols import Consumer, DecayPool


class AnimalCohort:
    """This is a class of animal cohorts."""

    def __init__(
        self,
        functional_group: FunctionalGroup,
        mass: float,
        age: float,
        individuals: int,
        constants: AnimalConsts = AnimalConsts(),
    ) -> None:
        if age < 0:
            raise ValueError("Age must be a positive number.")
        """Check if age is a positive number. """

        if mass < 0:
            raise ValueError("Mass must be a positive number.")
        """Check if mass is a positive number."""

        """The constructor for the AnimalCohort class."""
        self.functional_group = functional_group
        """The functional group of the animal cohort which holds constants."""
        self.name = functional_group.name
        """The functional type name of the animal cohort."""
        self.mass_current = mass
        """The current average body mass of an individual [kg]."""
        self.age = age
        """The age of the animal cohort [days]."""
        self.individuals = individuals
        """The number of individuals in this cohort."""
        self.constants = constants
        """Animal constants."""
        self.damuth_density: int = sf.damuths_law(
            self.functional_group.adult_mass, self.functional_group.damuths_law_terms
        )
        """The number of individuals in an average cohort of this type."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.is_mature: bool = False
        """Whether the cohort has reached adult body-mass."""
        self.time_to_maturity: float = 0.0
        """The amount of time [days] between birth and adult body-mass."""
        self.time_since_maturity: float = 0.0
        """The amount of time [days] since reaching adult body-mass."""
        self.reproductive_mass: float = 0.0
        """The pool of biomass from which the material of reproduction is drawn."""
        self.prey_groups = sf.prey_group_selection(
            self.functional_group.diet,
            self.functional_group.adult_mass,
            self.functional_group.prey_scaling,
        )
        """The identification of useable food resources."""
        self.decay_fraction_excrement: float = find_decay_consumed_split(
            microbial_decay_rate=self.constants.decay_rate_excrement,
            animal_scavenging_rate=self.constants.scavenging_rate_excrement,
        )
        """The fraction of excrement which decays before it gets consumed."""
        self.decay_fraction_carcasses: float = find_decay_consumed_split(
            microbial_decay_rate=self.constants.decay_rate_carcasses,
            animal_scavenging_rate=self.constants.scavenging_rate_carcasses,
        )
        """The fraction of carcass biomass which decays before it gets consumed."""

    def metabolize(self, temperature: float, dt: timedelta64) -> float:
        """The function to reduce body mass through metabolism.

        This method currently employs a toy 50/50 split of basal and field metabolism
        through the metabolic_rate scaling function. Ecothermic metabolism is a function
        of environmental temperature. Endotherms are unaffected by temperature change.
        This method will later drive the processing of carbon and nitrogen metabolic
        products.

        TODO: Update with stoichiometry

        Args:
            temperature: Current air temperature (K)
            dt: Number of days over which the metabolic costs should be calculated.

        Returns:
            The mass of metabolic waste produced.

        """

        if dt < timedelta64(0, "D"):
            raise ValueError("dt cannot be negative.")

        if self.mass_current < 0:
            raise ValueError("mass_current cannot be negative.")

        #  kg/day metabolic rate * number of days
        potential_mass_metabolized = sf.metabolic_rate(
            self.mass_current,
            temperature,
            self.functional_group.metabolic_rate_terms,
            self.functional_group.metabolic_type,
        ) * float(dt / timedelta64(1, "D"))

        actual_mass_metabolized = min(self.mass_current, potential_mass_metabolized)

        self.mass_current -= actual_mass_metabolized

        # returns total metabolic waste from cohort to animal_communities for tracking
        # in data object
        return actual_mass_metabolized * self.individuals

    def excrete(self, excreta_mass: float, excrement_pool: DecayPool) -> None:
        """Transfers nitrogenous metabolic wastes to the excrement pool.

        This method will not be fully implemented until the stoichiometric rework. All
        current metabolic wastes are carbonaceous and so all this does is provide a link
        joining metabolism to a soil pool for later use.

        TODO: Update with sensible (rather than hardcoded) stoichiometry

        Args:
            excreta_mass: The total mass of carbonaceous wastes excreted by the cohort.
            excrement_pool: The pool of wastes to which the excreted nitrogenous wastes
                flow.

        """
        excrement_pool.decomposed_nitrogen += (
            excreta_mass * self.constants.nitrogen_excreta_proportion
        )
        # TODO - Carbon and phosphorus flows are just hardcoded fractions of the
        # nitrogen flow. This needs to be changed when proper animal stoichiometry is
        # done.
        excrement_pool.decomposed_carbon += (
            0.5 * excreta_mass * self.constants.nitrogen_excreta_proportion
        )
        excrement_pool.decomposed_phosphorus += (
            0.01 * excreta_mass * self.constants.nitrogen_excreta_proportion
        )

    def respire(self, excreta_mass: float) -> float:
        """Transfers carbonaceous metabolic wastes to the atmosphere.

        This method will not be fully implemented until the stoichiometric rework. All
        current metabolic wastes are carbonaceous and so all this does is return the
        excreta mass for updating data["total_animal_respiration"] in metabolize
        community.

        TODO: Update with stoichiometry

        Args:
            excreta_mass: The total mass of carbonaceous wastes excreted by the cohort.

        Return: The total mass of carbonaceous wastes excreted by the cohort.

        """

        return excreta_mass * self.constants.carbon_excreta_proportion

    def defecate(
        self,
        excrement_pool: DecayPool,
        mass_consumed: float,
    ) -> None:
        """Transfer waste mass from an animal cohort to the excrement pool.

        Waste mass is transferred to the excrement pool, split between a decomposed and
        a scavengable compartment. Carbon, nitrogen and phosphorus are all transferred.
        An assumption here is that the stoichiometric ratios of the flows to each
        compartment are equal, i.e. the nutrient split between compartments is
        calculated identically to the carbon split.

        TODO: Needs to be reworked to use carbon mass rather than total mass.
        TODO: update for current conversion efficiency
        TODO: Update with stoichiometry

        Args:
            excrement_pool: The local ExcrementSoil pool in which waste is deposited.
            mass_consumed: The amount of mass flowing through cohort digestion.
        """
        # Find total waste mass, the total amount of waste is then found by the
        # average cohort member * number individuals.
        waste_carbon = mass_consumed * self.functional_group.conversion_efficiency
        # TODO - replace this with sensible stoichiometry
        waste_nitrogen = 0.1 * waste_carbon
        waste_phosphorus = 0.01 * waste_carbon

        # This total waste is then split between decay and scavengeable excrement
        excrement_pool.scavengeable_carbon += (
            (1 - self.decay_fraction_excrement) * waste_carbon * self.individuals
        )
        excrement_pool.decomposed_carbon += (
            self.decay_fraction_excrement * waste_carbon * self.individuals
        )
        # Key assumption here is that the split between scavengable and decomposed pools
        # has equal stochiometries
        excrement_pool.scavengeable_nitrogen += (
            (1 - self.decay_fraction_excrement) * waste_nitrogen * self.individuals
        )
        excrement_pool.decomposed_nitrogen += (
            self.decay_fraction_excrement * waste_nitrogen * self.individuals
        )
        excrement_pool.scavengeable_phosphorus += (
            (1 - self.decay_fraction_excrement) * waste_phosphorus * self.individuals
        )
        excrement_pool.decomposed_phosphorus += (
            self.decay_fraction_excrement * waste_phosphorus * self.individuals
        )

    def increase_age(self, dt: timedelta64) -> None:
        """The function to modify cohort age as time passes and flag maturity.

        Args:
            dt: The amount of time that should be added to cohort age.

        """

        dt_float = float(dt / timedelta64(1, "D"))

        self.age += dt_float

        if self.is_mature is True:
            self.time_since_maturity += dt_float
        elif (
            self.is_mature is False
            and self.mass_current >= self.functional_group.adult_mass
        ):
            self.is_mature = True
            self.time_to_maturity = self.age

    def die_individual(self, number_dead: int, carcass_pool: CarcassPool) -> None:
        """The function to reduce the number of individuals in the cohort through death.

        Currently, all cohorts are crafted as single km2 grid cohorts. This means that
        very large animal will have one or fewer cohort members per grid. As changes
        are made to capture large body size and multi-grid occupancy, this will be
        updated.

        Mass of dead individuals is transferred to the carcass pool, split between a
        decomposed and a scavengable compartment. Carbon, nitrogen and phosphorus are
        all transferred. An assumption here is that the stoichiometric ratios of the
        flows to each compartment are equal, i.e. the nutrient split between
        compartments is calculated identically to the carbon split.

        TODO: This needs to take in carbon mass not total mass
        TODO: This needs to use proper stochiometry

        Args:
            number_dead: The number of individuals by which to decrease the population
                count.
            carcass_pool: The resident pool of animal carcasses to which the dead
                individuals are delivered.

        """
        self.individuals -= number_dead

        # Find total mass contained in the carcasses
        # TODO - This mass needs to be total mass not carbon mass
        carcass_mass = number_dead * self.mass_current

        # TODO - Carcass stochiometries are found using a hard coded ratio, this needs
        # to go once stoichiometry is properly implemented
        carcass_mass_nitrogen = 0.1 * carcass_mass
        carcass_mass_phosphorus = 0.01 * carcass_mass

        # Split this mass between carcass decay, and scavengeable carcasses
        carcass_pool.scavengeable_carbon += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass
        carcass_pool.decomposed_carbon += self.decay_fraction_carcasses * carcass_mass
        carcass_pool.scavengeable_nitrogen += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_nitrogen
        carcass_pool.decomposed_nitrogen += (
            self.decay_fraction_carcasses * carcass_mass_nitrogen
        )
        carcass_pool.scavengeable_phosphorus += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_phosphorus
        carcass_pool.decomposed_phosphorus += (
            self.decay_fraction_carcasses * carcass_mass_phosphorus
        )

    def update_carcass_pool(self, carcass_mass: float, carcass_pool: DecayPool) -> None:
        """Updates the carcass pool based on consumed mass and predator's efficiency.

        Mass of dead individuals is transferred to the carcass pool, split between a
        decomposed and a scavengable compartment. Carbon, nitrogen and phosphorus are
        all transferred. An assumption here is that the stoichiometric ratios of the
        flows to each compartment are equal, i.e. the nutrient split between
        compartments is calculated identically to the carbon split.

        TODO: This needs to take in carbon mass not total mass
        TODO: This needs to use proper stochiometry

        Args:
            carcass_mass: The total mass consumed from the prey cohort.
            carcass_pool: The pool to which remains of eaten individuals are delivered.
        """

        # TODO - Carcass stochiometries are found using a hard coded ratio, this needs
        # to go once stoichiometry is properly implemented
        carcass_mass_nitrogen = 0.1 * carcass_mass
        carcass_mass_phosphorus = 0.01 * carcass_mass

        # TODO - This also needs to be updated to carbon mass rather than total mass
        # terms
        # Update the carcass pool with the remainder
        carcass_pool.scavengeable_carbon += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass
        carcass_pool.decomposed_carbon += self.decay_fraction_carcasses * carcass_mass
        carcass_pool.scavengeable_nitrogen += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_nitrogen
        carcass_pool.decomposed_nitrogen += (
            self.decay_fraction_carcasses * carcass_mass_nitrogen
        )
        carcass_pool.scavengeable_phosphorus += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_phosphorus
        carcass_pool.decomposed_phosphorus += (
            self.decay_fraction_carcasses * carcass_mass_phosphorus
        )

    def get_eaten(
        self,
        potential_consumed_mass: float,
        predator: Consumer,
        carcass_pool: DecayPool,
    ) -> float:
        """Removes individuals according to mass demands of a predation event.

        It finds the smallest whole number of prey required to satisfy the predators
        mass demands and caps at then caps it at the available population.

        Args:
            potential_consumed_mass: The mass intended to be consumed by the predator.
            predator: The predator consuming the cohort.
            carcass_pool: The pool to which remains of eaten individuals are delivered.

        Returns:
            The actual mass consumed by the predator, closely matching consumed_mass.
        """

        # Mass of an average individual in the cohort
        individual_mass = self.mass_current

        max_individuals_killed = ceil(potential_consumed_mass / individual_mass)
        actual_individuals_killed = min(max_individuals_killed, self.individuals)

        # Calculate the mass represented by the individuals actually killed
        actual_mass_killed = actual_individuals_killed * individual_mass

        # Calculate the actual amount of mass consumed by the predator
        actual_mass_consumed = min(actual_mass_killed, potential_consumed_mass)

        # Calculate the amount of mass that goes into carcass pool
        carcass_mass = (actual_mass_killed - actual_mass_consumed) + (
            actual_mass_consumed * (1 - predator.functional_group.mechanical_efficiency)
        )

        # Update the number of individuals in the prey cohort
        self.individuals -= actual_individuals_killed

        # Update the carcass pool with carcass mass
        self.update_carcass_pool(carcass_mass, carcass_pool)

        return actual_mass_consumed

    def calculate_alpha(self) -> float:
        """Calculate search efficiency.

        This utilizes the alpha_i_k scaling function to determine the effective rate at
        which an individual herbivore searches its environment, factoring in the
        herbivore's current mass.

        TODO: update name

        Returns:
            A float representing the search efficiency rate in [ha/(day*g)].
        """

        return sf.alpha_i_k(self.constants.alpha_0_herb, self.mass_current)

    def calculate_potential_consumed_biomass(
        self, target_plant: PlantResources, alpha: float
    ) -> float:
        """Calculate potential consumed biomass for the target plant.

        This method computes the potential consumed biomass based on the search
        efficiency (alpha),the fraction of the total plant stock available to the cohort
        (phi), and the biomass of the target plant.

        TODO: give A_cell a grid size reference

        Args:
            target_plant: The plant resource being targeted by the herbivore cohort.
            alpha: The search efficiency rate of the herbivore cohort.

        Returns:
            A float representing the potential consumed biomass of the target plant by
            the cohort [g/day].
        """

        phi = self.functional_group.constants.phi_herb_t
        A_cell = 1.0  # temporary
        return sf.k_i_k(alpha, phi, target_plant.mass_current, A_cell)

    def calculate_total_handling_time_for_herbivory(
        self, plant_list: Sequence[PlantResources], alpha: float
    ) -> float:
        """Calculate total handling time across all plant resources.

        This aggregates the handling times for consuming each plant resource in the
        list, incorporating the search efficiency and other scaling factors to compute
        the total handling time required by the cohort.

        TODO: give A_cell a grid size reference.

        Args:
            plant_list: A sequence of plant resources available for consumption by the
            cohort.
            alpha: The search efficiency rate of the herbivore cohort.

        Returns:
            A float representing the total handling time in days required by the cohort
            for all available plant resources.
        """

        phi = self.functional_group.constants.phi_herb_t
        A_cell = 1.0  # temporary
        return sum(
            sf.k_i_k(alpha, phi, plant.mass_current, A_cell)
            + sf.H_i_k(
                self.constants.h_herb_0,
                self.constants.M_herb_ref,
                self.mass_current,
                self.constants.b_herb,
            )
            for plant in plant_list
        )

    def F_i_k(
        self, plant_list: Sequence[PlantResources], target_plant: PlantResources
    ) -> float:
        """Method to determine instantaneous herbivory rate on plant k.

        This method integrates the calculated search efficiency, potential consumed
        biomass of the target plant, and the total handling time for all available
        plant resources to determine the rate at which the target plant is consumed by
        the cohort.

        TODO: update name

        Args:
            plant_list: A sequence of plant resources available for consumption by the
                 cohort.
            target_plant: The specific plant resource being targeted by the herbivore
                 cohort for consumption.

        Returns:
            The instantaneous consumption rate [g/day] of the target plant resource by
              the herbivore cohort.
        """
        alpha = self.calculate_alpha()
        k = self.calculate_potential_consumed_biomass(target_plant, alpha)
        total_handling_t = self.calculate_total_handling_time_for_herbivory(
            plant_list, alpha
        )
        B_k = target_plant.mass_current  # current plant biomass
        N = self.individuals  # herb cohort size
        return N * (k / (1 + total_handling_t)) * (1 / B_k)

    def calculate_theta_opt_i(self) -> float:
        """Calculate the optimal predation param based on predator-prey mass ratio.

        TODO: update name

        Returns:
            Float value of the optimal predation parameter for use in calculating the
            probability of a predation event being successful.

        """
        return sf.theta_opt_i(
            self.constants.theta_opt_min_f,
            self.constants.theta_opt_f,
            self.constants.sigma_opt_f,
        )

    def calculate_predation_success_probability(self, M_target: float) -> float:
        """Calculate the probability of a successful predation event.

        Args:
            M_target: the body mass of the animal cohort being targeted for predation.

        Returns:
            A float value of the probability that a predation event is successful.

        """
        M_i = self.mass_current
        theta_opt_i = self.calculate_theta_opt_i()
        return sf.w_bar_i_j(
            M_i,
            M_target,
            theta_opt_i,
            self.constants.sigma_opt_pred_prey,
        )

    def calculate_predation_search_rate(self, w_bar: float) -> float:
        """Calculate the search rate of the predator.

        Args:
            w_bar: Probability of successfully capturing prey.

        Returns:
            A float value of the search rate in ha/day

        """
        return sf.alpha_i_j(self.constants.alpha_0_pred, self.mass_current, w_bar)

    def calculate_potential_prey_consumed(
        self, alpha: float, theta_i_j: float
    ) -> float:
        """Calculate the potential number of prey consumed.

        TODO: give A_cell a grid size reference

        Args:
            alpha: the predation search rate
            theta_i_j: The cumulative density of organisms with a mass lying within the
              same predator specific mass bin.

        Returns:
            The potential number of prey items consumed.

        """
        A_cell = 1.0  # temporary
        return sf.k_i_j(alpha, self.individuals, A_cell, theta_i_j)

    def calculate_total_handling_time_for_predation(self) -> float:
        """Calculate the total handling time for preying on available animal cohorts.

        Returns:
            A float value of handling time in days.

        """
        return sf.H_i_j(
            self.constants.h_pred_0,
            self.constants.M_pred_ref,
            self.mass_current,
            self.constants.b_pred,
        )

    def F_i_j_individual(
        self, animal_list: Sequence[AnimalCohort], target_cohort: AnimalCohort
    ) -> float:
        """Method to determine instantaneous predation rate on cohort j.

        Args:
            animal_list: A sequence of animal cohorts that can be consumed by the
                predator.
            target_cohort: The prey cohort from which mass will be consumed.

        Returns:
            Float fraction of target cohort consumed per day.


        """
        w_bar = self.calculate_predation_success_probability(target_cohort.mass_current)
        alpha = self.calculate_predation_search_rate(w_bar)
        theta_i_j = self.theta_i_j(animal_list)  # Assumes implementation of theta_i_j
        k_target = self.calculate_potential_prey_consumed(alpha, theta_i_j)
        total_handling_t = self.calculate_total_handling_time_for_predation()
        N_i = self.individuals
        N_target = target_cohort.individuals

        return N_i * (k_target / (1 + total_handling_t)) * (1 / N_target)

    def calculate_consumed_mass_predation(
        self, animal_list: Sequence[AnimalCohort], target_cohort: AnimalCohort
    ) -> float:
        """Calculates the mass to be consumed from a prey cohort by the predator.

        This method utilizes the F_i_j_individual method to determine the rate at which
        the target cohort is consumed, and then calculates the actual mass to be
        consumed based on this rate and other model parameters.

        TODO: Replace delta_t with time step reference

        Args:
            animal_list: A sequence of animal cohorts that can be consumed by the
                predator.
            target_cohort: The prey cohort from which mass will be consumed.

        Returns:
            The mass to be consumed from the target cohort by the predator (in kg).
        """
        F = self.F_i_j_individual(animal_list, target_cohort)
        delta_t = 30.0  # days

        # Calculate the consumed mass based on Mad. formula for delta_mass_predation
        consumed_mass = (
            target_cohort.mass_current
            * target_cohort.individuals
            * (
                1
                - exp(-(F * delta_t * self.constants.tau_f * self.constants.sigma_f_t))
            )
        )

        return consumed_mass

    def delta_mass_predation(
        self,
        animal_list: Sequence[AnimalCohort],
        excrement_pool: DecayPool,
        carcass_pool: CarcassPool,
    ) -> float:
        """This method handles mass assimilation from predation.

        This is Madingley's delta_assimilation_mass_predation

        Args:
            animal_list: A sequence of animal cohorts that can be consumed by the
                         predator.
            excrement_pool: A pool representing the excrement in the grid cell.
            carcass_pool: A pool representing the animal carcasses in the grid cell.

        Returns:
            The change in mass experienced by the predator.
        """

        total_consumed_mass = 0.0  # Initialize the total consumed mass

        for cohort in animal_list:
            # Calculate the mass to be consumed from this cohort
            consumed_mass = self.calculate_consumed_mass_predation(animal_list, cohort)
            # Call get_eaten on the prey cohort to update its mass and individuals
            actual_consumed_mass = cohort.get_eaten(consumed_mass, self, carcass_pool)
            # Update total mass gained by the predator
            total_consumed_mass += actual_consumed_mass

        # Process waste generated from predation, separate from herbivory b/c diff waste
        self.defecate(excrement_pool, total_consumed_mass)
        return total_consumed_mass

    def calculate_consumed_mass_herbivory(
        self, plant_list: Sequence[PlantResources], target_plant: PlantResources
    ) -> float:
        """Calculates the mass to be consumed from a plant resource by the herbivore.

        This method utilizes the F_i_k method to determine the rate at which the target
        plant is consumed, and then calculates the actual mass to be consumed based on
        this rate and other model parameters.

        TODO: Replace delta_t with actual time step reference

        Args:
            plant_list: A sequence of plant resources that can be consumed by the
                herbivore.
            target_plant: The plant resource from which mass will be consumed.

        Returns:
            The mass to be consumed from the target plant by the herbivore (in kg).
        """
        F = self.F_i_k(plant_list, target_plant)  # Adjusting this call as necessary
        delta_t = 30.0  # days

        consumed_mass = target_plant.mass_current * (
            1 - exp(-(F * delta_t * self.constants.tau_f * self.constants.sigma_f_t))
        )
        return consumed_mass

    def delta_mass_herbivory(
        self,
        plant_list: Sequence[PlantResources],
        excrement_pool: DecayPool,
        plant_waste_pool: HerbivoryWaste,
    ) -> float:
        """This method handles mass assimilation from herbivory.

        TODO: update name
        TODO: At present this just takes a single herbivory waste pool (for leaves),
        this probably should change to be a list of waste pools once herbivory for other
        plant tissues is added.

        Args:
            plant_list: A sequence of plant resources available for herbivory.
            excrement_pool: A pool representing the excrement in the grid cell.
            plant_waste_pool: Waste pool for plant biomass (at this point just leaves)
                that gets removed as part of herbivory but not actually consumed.

        Returns:
            The total plant mass consumed by the animal cohort in g.

        """
        total_consumed_mass = 0.0  # Initialize the total consumed mass

        for plant in plant_list:
            # Calculate the mass to be consumed from this plant
            consumed_mass = self.calculate_consumed_mass_herbivory(plant_list, plant)
            # Update the plant resource's state based on consumed mass
            actual_consumed_mass, excess_mass = plant.get_eaten(consumed_mass, self)
            # Update total mass gained by the herbivore
            total_consumed_mass += actual_consumed_mass
            plant_waste_pool.mass_current += excess_mass

        # Process waste generated from predation, separate from carnivory b/c diff waste
        self.defecate(excrement_pool, total_consumed_mass)
        return total_consumed_mass

    def forage_cohort(
        self,
        plant_list: Sequence[PlantResources],
        animal_list: Sequence[AnimalCohort],
        excrement_pool: DecayPool,
        carcass_pool: CarcassPool,
        herbivory_waste_pool: HerbivoryWaste,
    ) -> None:
        """This function handles selection of resources from a list for consumption.

        Args:
            plant_list: A sequence of plant resources available for herbivory.
            animal_list: A sequence of animal cohorts available for predation.
            excrement_pool: A pool representing the excrement in the grid cell.
            carcass_pool: A pool representing the carcasses in the grid cell.
            herbivory_waste_pool: A pool representing waste caused by herbivory.

        Return:
            A float value of the net change in consumer mass due to foraging.
        """
        if self.individuals == 0:
            LOGGER.warning("No individuals in cohort to forage.")
            return

        # Herbivore diet
        if self.functional_group.diet == DietType.HERBIVORE and plant_list:
            consumed_mass = self.delta_mass_herbivory(
                plant_list, excrement_pool, herbivory_waste_pool
            )  # Directly modifies the plant mass
            self.eat(consumed_mass)  # Accumulate net mass gain from each plant

        # Carnivore diet
        elif self.functional_group.diet == DietType.CARNIVORE and animal_list:
            # Calculate the mass gained from predation
            consumed_mass = self.delta_mass_predation(
                animal_list, excrement_pool, carcass_pool
            )
            # Update the predator's mass with the total gained mass
            self.eat(consumed_mass)

    def theta_i_j(self, animal_list: Sequence[AnimalCohort]) -> float:
        """Cumulative density method for delta_mass_predation.

        The cumulative density of organisms with a mass lying within the same predator
        specific mass bin as Mi.

        Madingley

        TODO: current format makes no sense, dig up the details in the supp
        TODO: update A_cell with real reference to grid zie
        TODO: update name

        Args:
            animal_list: A sequence of animal cohorts that can be consumed by the
                         predator.

        Returns:
            The float value of theta.
        """
        A_cell = 1.0  # temporary

        return sum(
            cohort.individuals / A_cell
            for cohort in animal_list
            if self.mass_current == cohort.mass_current
        )

    def eat(self, mass_consumed: float) -> None:
        """Handles the mass gain from consuming food.

        This method updates the consumer's mass based on the amount of food consumed.
        It assumes the `mass_consumed` has already been calculated and processed
        through `get_eaten`.

        TODO: non-reproductive functional groups should not store any reproductive mass

        Args:
            mass_consumed: The mass consumed by this consumer, calculated externally.

        Returns:
            The amount of consumed mass, adjusted for efficiency and used for waste
            output.
        """
        if self.individuals == 0:
            return

        # Adjust mass gain based on the consumer's current mass and reproductive
        # threshold
        if self.is_below_mass_threshold(
            self.constants.flow_to_reproductive_mass_threshold
        ):
            self.mass_current += mass_consumed  # Gains to reproductive or body mass
        else:
            self.reproductive_mass += mass_consumed

    def is_below_mass_threshold(self, mass_threshold: float) -> bool:
        """Check if cohort's total mass is below a certain threshold.

        Currently used for thesholding: birth, dispersal, trophic flow to reproductive
        mass.

        Args:
            mass_threshold: a float value holding a threshold ratio of current total
                mass to standard adult mass.

        Return:
            A bool of whether the current mass state is above the migration threshold.
        """
        return (
            self.mass_current + self.reproductive_mass
        ) / self.functional_group.adult_mass < mass_threshold

    def migrate_juvenile_probability(self) -> float:
        """The probability that a juvenile cohort will migrate to a new grid cell.

        TODO: This does not hold for diagonal moves or non-square grids.
        TODO: update A_cell to grid size reference

        Following Madingley's assumption that the probability of juvenile dispersal is
        equal to the proportion of the cohort individuals that would arrive in the
        neighboring cell after one full timestep's movement.

        Assuming cohort individuals are homogenously distributed within a grid cell and
        that the move is non-diagonal, the probability is then equal to the ratio of
        dispersal speed to the side-length of a grid cell.

        A homogenously distributed cohort with a partial presence in a grid cell will
        have a proportion of its individuals in the new grid cell equal to the
        proportion the new grid cell that it occupies (A_new / A_cell). This proportion
        will be equal to the cohorts velocity (V) multiplied by the elapsed time (t)
        multiplied by the length of one side of a grid cell (L) (V*t*L) (t is assumed
        to be 1 here). The area of the square grid cell is the square of the length of
        one side. The proportion of individuals in the new cell is then:
        A_new / A_cell = (V * T * L) / (L * L) = ((L/T) * T * L) / (L * L ) =
        dimensionless
        [m2   / m2     = (m/d * d * m) / (m * m) = m / m = dimensionless]

        Returns:
            The probability of diffusive natal dispersal to a neighboring grid cell.

        """

        A_cell = 1.0  # temporary
        grid_side = sqrt(A_cell)
        velocity = sf.juvenile_dispersal_speed(
            self.mass_current,
            self.constants.V_disp,
            self.constants.M_disp_ref,
            self.constants.o_disp,
        )

        # not a true probability as can be > 1, reduced to 1.0 in return statement
        probability_of_dispersal = velocity / grid_side

        return min(1.0, probability_of_dispersal)

    def inflict_non_predation_mortality(
        self, dt: float, carcass_pool: CarcassPool
    ) -> None:
        """Inflict combined background, senescence, and starvation mortalities.

        TODO: Review logic of mass_max = adult_mass
        TODO: Review the use of ceil in number_dead, it fails for large animals.

        Args:
            dt: The time passed in the timestep (days).
            carcass_pool: The local carcass pool to which dead individuals go.

        """

        pop_size = self.individuals
        mass_current = self.mass_current

        t_to_maturity = self.time_to_maturity
        t_since_maturity = self.time_since_maturity
        mass_max = self.functional_group.adult_mass  # this might not be only solution

        u_bg = sf.background_mortality(
            self.constants.u_bg
        )  # constant background mortality

        u_se = 0.0
        if self.is_mature:
            # senescence mortality is only experienced by mature adults.
            u_se = sf.senescence_mortality(
                self.constants.lambda_se, t_to_maturity, t_since_maturity
            )  # senesence mortality
        elif self.is_mature is False:
            u_se = 0.0

        u_st = sf.starvation_mortality(
            self.constants.lambda_max,
            self.constants.J_st,
            self.constants.zeta_st,
            mass_current,
            mass_max,
        )  # starvation mortality
        u_t = u_bg + u_se + u_st

        # Calculate the total number of dead individuals
        number_dead = ceil(pop_size * (1 - exp(-u_t * dt)))

        # Remove the dead individuals from the cohort
        self.die_individual(number_dead, carcass_pool)
