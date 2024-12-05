"""The ''animal'' module provides animal module functionality."""

from __future__ import annotations

import uuid
from math import ceil, exp, sqrt

from numpy import timedelta64

import virtual_ecosystem.models.animal.scaling_functions as sf
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_traits import DietType
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.decay import (
    CarcassPool,
    ExcrementPool,
    HerbivoryWaste,
    find_decay_consumed_split,
)
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup
from virtual_ecosystem.models.animal.protocols import Resource


class AnimalCohort:
    """This is a class of animal cohorts."""

    def __init__(
        self,
        functional_group: FunctionalGroup,
        mass: float,
        age: float,
        individuals: int,
        centroid_key: int,
        grid: Grid,
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
        self.centroid_key = centroid_key
        """The centroid key of the cohort's territory."""
        self.grid = grid
        """The the grid structure of the simulation."""
        self.constants = constants
        """Animal constants."""
        self.id: uuid.UUID = uuid.uuid4()
        """A unique identifier for the cohort."""
        # self.damuth_density: int = sf.damuths_law(
        #    self.functional_group.adult_mass, self.functional_group.damuths_law_terms
        # )
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
        self.prey_groups: dict[str, tuple[float, float]] = sf.prey_group_selection(
            self.functional_group.diet,
            self.functional_group.adult_mass,
            self.functional_group.prey_scaling,
        )
        """The identification of useable food resources."""
        self.territory_size = sf.territory_size(self.functional_group.adult_mass)
        """The size in hectares of the animal cohorts territory."""
        self.occupancy_proportion: float = 1.0 / self.territory_size
        """The proportion of the cohort that is within a territorial given grid cell."""
        self._initialize_territory(centroid_key)
        """Initialize the territory using the centroid grid key."""
        self.territory: list[int]
        """The list of grid cells currently occupied by the cohort."""
        # TODO - In future this should be parameterised using a constants dataclass, but
        # this hasn't yet been implemented for the animal model
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

    def get_territory_cells(self, centroid_key: int) -> list[int]:
        """This calls bfs_territory to determine the scope of the territory.

        TODO: local import of bfs_territory is temporary while deciding whether to keep
        animal_territory.py

        Args:
            centroid_key: The central grid cell key of the territory.

        """
        # Each grid cell is 1 hectare, territory size in grids is the same as hectares
        target_cell_number = int(self.territory_size)

        # Perform BFS to determine the territory cells
        territory_cells = sf.bfs_territory(
            centroid_key,
            target_cell_number,
            self.grid.cell_nx,
            self.grid.cell_ny,
        )

        return territory_cells

    def _initialize_territory(
        self,
        centroid_key: int,
    ) -> None:
        """This initializes the territory occupied by the cohort.

        TODO: local import of AnimalTerritory is temporary while deciding whether to
        keep the class

        Args:
            centroid_key: The grid cell key anchoring the territory.
        """

        self.territory = self.get_territory_cells(centroid_key)

    def update_territory(self, new_grid_cell_keys: list[int]) -> None:
        """Update territory details at initialization and after migration.

        Args:
            new_grid_cell_keys: The new list of grid cell keys the territory occupies.

        """

        self.territory = new_grid_cell_keys

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

    def excrete(
        self, excreta_mass: float, excrement_pools: list[ExcrementPool]
    ) -> None:
        """Transfers metabolic wastes to the excrement pool.

        This method handles nitrogenous and carbonaceous wastes, split between
        scavengeable and decomposed pools. Pending rework of stoichiometric
        calculations.

        Args:
            excreta_mass: The total mass of wastes excreted by the cohort.
            excrement_pools: The pools of waste to which the excreted wastes flow.
        """
        number_communities = len(excrement_pools)

        # Calculate excreta mass per community and proportionate nitrogen flow
        excreta_mass_per_community = excreta_mass / number_communities
        nitrogen_mass_per_community = (
            excreta_mass_per_community * self.constants.nitrogen_excreta_proportion
        )

        # Calculate scavengeable and decomposed nitrogen
        scavengeable_nitrogen_per_community = (
            1 - self.decay_fraction_excrement
        ) * nitrogen_mass_per_community
        decomposed_nitrogen_per_community = (
            self.decay_fraction_excrement * nitrogen_mass_per_community
        )

        # Carbon and phosphorus are fractions of nitrogen per community
        scavengeable_carbon_per_community = 0.5 * scavengeable_nitrogen_per_community
        decomposed_carbon_per_community = 0.5 * decomposed_nitrogen_per_community
        scavengeable_phosphorus_per_community = (
            0.01 * scavengeable_nitrogen_per_community
        )
        decomposed_phosphorus_per_community = 0.01 * decomposed_nitrogen_per_community

        for excrement_pool in excrement_pools:
            # Assign calculated nitrogen, carbon, and phosphorus to the pool
            excrement_pool.scavengeable_nitrogen += scavengeable_nitrogen_per_community
            excrement_pool.decomposed_nitrogen += decomposed_nitrogen_per_community
            excrement_pool.scavengeable_carbon += scavengeable_carbon_per_community
            excrement_pool.decomposed_carbon += decomposed_carbon_per_community
            excrement_pool.scavengeable_phosphorus += (
                scavengeable_phosphorus_per_community
            )
            excrement_pool.decomposed_phosphorus += decomposed_phosphorus_per_community

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
        excrement_pools: list[ExcrementPool],
        mass_consumed: float,
    ) -> None:
        """Transfer waste mass from an animal cohort to the excrement pools.

        Waste mass is transferred to the excrement pool(s), split between decomposed and
        scavengable compartments. Carbon, nitrogen, and phosphorus are transferred
        according to stoichiometric ratios. Mass is distributed over multiple excrement
        pools if provided.

        TODO: Needs to be reworked to use carbon mass rather than total mass.
        TODO: Update with current conversion efficiency and stoichiometry.

        Args:
            excrement_pools: The ExcrementPool objects in the cohort's territory in
                which waste is deposited.
            mass_consumed: The amount of mass flowing through cohort digestion.
        """
        number_communities = len(excrement_pools)

        # Calculate the total waste mass, which is the mass consumed times conversion
        # efficiency
        total_waste_mass = (
            mass_consumed
            * self.functional_group.conversion_efficiency
            * self.individuals
        )

        # Split the waste mass proportionally among communities
        waste_mass_per_community = total_waste_mass / number_communities

        # Calculate waste for carbon, nitrogen, and phosphorus using current
        # stoichiometry
        waste_carbon_per_community = waste_mass_per_community
        waste_nitrogen_per_community = 0.1 * waste_carbon_per_community
        waste_phosphorus_per_community = 0.01 * waste_carbon_per_community

        # Pre-calculate the scavengeable and decomposed fractions for each nutrient
        scavengeable_carbon_per_community = (
            1 - self.decay_fraction_excrement
        ) * waste_carbon_per_community
        decomposed_carbon_per_community = (
            self.decay_fraction_excrement * waste_carbon_per_community
        )

        scavengeable_nitrogen_per_community = (
            1 - self.decay_fraction_excrement
        ) * waste_nitrogen_per_community
        decomposed_nitrogen_per_community = (
            self.decay_fraction_excrement * waste_nitrogen_per_community
        )

        scavengeable_phosphorus_per_community = (
            1 - self.decay_fraction_excrement
        ) * waste_phosphorus_per_community
        decomposed_phosphorus_per_community = (
            self.decay_fraction_excrement * waste_phosphorus_per_community
        )

        # Distribute waste across each excrement pool
        for excrement_pool in excrement_pools:
            # Update carbon pools
            excrement_pool.scavengeable_carbon += scavengeable_carbon_per_community
            excrement_pool.decomposed_carbon += decomposed_carbon_per_community

            # Update nitrogen pools
            excrement_pool.scavengeable_nitrogen += scavengeable_nitrogen_per_community
            excrement_pool.decomposed_nitrogen += decomposed_nitrogen_per_community

            # Update phosphorus pools
            excrement_pool.scavengeable_phosphorus += (
                scavengeable_phosphorus_per_community
            )
            excrement_pool.decomposed_phosphorus += decomposed_phosphorus_per_community

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

    def die_individual(
        self, number_dead: int, carcass_pools: list[CarcassPool]
    ) -> None:
        """The function to reduce the number of individuals in the cohort through death.

        Currently, all cohorts are crafted as single km2 grid cohorts. This means that
        very large animal will have one or fewer cohort members per grid. As changes
        are made to capture large body size and multi-grid occupancy, this will be
        updated.

        Currently, this function is in an inbetween state where mass is removed from
        the animal cohort but it is recieved by the litter pool as energy. This will be
        fixed once the litter pools are updated for mass.

        TODO: Rework after update litter pools for mass

        Args:
            number_dead: The number of individuals by which to decrease the population
                count.
            carcass_pools: The resident pool of animal carcasses to which the dead
                individuals are delivered.

        """
        self.individuals -= number_dead

        # Find total mass contained in the carcasses
        carcass_mass = number_dead * self.mass_current

        self.update_carcass_pool(carcass_mass, carcass_pools)

    def update_carcass_pool(
        self, carcass_mass: float, carcass_pools: list[CarcassPool]
    ) -> None:
        """Updates the carcass pools after deaths.

        Carcass mass is transferred to the carcass pools, split between a decomposed and
        a scavengeable compartment. Carbon, nitrogen, and phosphorus are all transferred
        according to stoichiometric ratios.

        TODO: Update to handle proper carbon mass rather than total mass.
        TODO: Use dynamic stoichiometry once implemented.

        Args:
            carcass_mass: The total mass consumed from the prey cohort.
            carcass_pools: The pools to which remains of eaten individuals are
             delivered.
        """
        number_carcass_pools = len(carcass_pools)

        # Split carcass mass per pool
        carcass_mass_per_pool = carcass_mass / number_carcass_pools

        # Calculate stoichiometric proportions for nitrogen and phosphorus
        carcass_mass_nitrogen_per_pool = 0.1 * carcass_mass_per_pool
        carcass_mass_phosphorus_per_pool = 0.01 * carcass_mass_per_pool

        # Pre-calculate scavengeable and decomposed fractions for carbon, nitrogen,
        # and phosphorus
        scavengeable_carbon_per_pool = (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_per_pool
        decomposed_carbon_per_pool = (
            self.decay_fraction_carcasses * carcass_mass_per_pool
        )

        scavengeable_nitrogen_per_pool = (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_nitrogen_per_pool
        decomposed_nitrogen_per_pool = (
            self.decay_fraction_carcasses * carcass_mass_nitrogen_per_pool
        )

        scavengeable_phosphorus_per_pool = (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass_phosphorus_per_pool
        decomposed_phosphorus_per_pool = (
            self.decay_fraction_carcasses * carcass_mass_phosphorus_per_pool
        )

        # Distribute carcass mass across the carcass pools
        for carcass_pool in carcass_pools:
            # Update carbon pools
            carcass_pool.scavengeable_carbon += scavengeable_carbon_per_pool
            carcass_pool.decomposed_carbon += decomposed_carbon_per_pool

            # Update nitrogen pools
            carcass_pool.scavengeable_nitrogen += scavengeable_nitrogen_per_pool
            carcass_pool.decomposed_nitrogen += decomposed_nitrogen_per_pool

            # Update phosphorus pools
            carcass_pool.scavengeable_phosphorus += scavengeable_phosphorus_per_pool
            carcass_pool.decomposed_phosphorus += decomposed_phosphorus_per_pool

    def get_eaten(
        self,
        potential_consumed_mass: float,
        predator: AnimalCohort,
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> float:
        """Removes individuals according to mass demands of a predation event.

        It finds the smallest whole number of prey required to satisfy the predators
        mass demands and caps at then caps it at the available population.


        Args:
            potential_consumed_mass: The mass intended to be consumed by the predator.
            predator: The predator consuming the cohort.
            carcass_pools: The pools to which remains of eaten individuals are
              delivered.

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

        # set cohort to not alive if all the individuals are dead
        if self.individuals <= 0:
            self.is_alive = False

        # Find the intersection of prey and predator territories
        intersection_carcass_pools = self.find_intersecting_carcass_pools(
            predator.territory, carcass_pools
        )

        # Update the carcass pool with carcass mass
        self.update_carcass_pool(carcass_mass, intersection_carcass_pools)

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
        self, target_plant: Resource, alpha: float
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
        self, plant_list: list[Resource], alpha: float
    ) -> float:
        """Calculate total handling time across all plant resources.

        This aggregates the handling times for consuming each plant resource in the
        list, incorporating the search efficiency and other scaling factors to compute
        the total handling time required by the cohort.

        TODO: give A_cell a grid size reference.
        TODO: MGO - rework for territories

        Args:
            plant_list: A list of plant resources available for consumption by the
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

    def F_i_k(self, plant_list: list[Resource], target_plant: Resource) -> float:
        """Method to determine instantaneous herbivory rate on plant k.

        This method integrates the calculated search efficiency, potential consumed
        biomass of the target plant, and the total handling time for all available
        plant resources to determine the rate at which the target plant is consumed by
        the cohort.

        TODO: update name

        Args:
            plant_list: A list of plant resources available for consumption by the
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
        TODO: MGO - rework for territories

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
        self, animal_list: list[AnimalCohort], target_cohort: AnimalCohort
    ) -> float:
        """Method to determine instantaneous predation rate on cohort j.

        Args:
            animal_list: A list of animal cohorts that can be consumed by the
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
        self, animal_list: list[AnimalCohort], target_cohort: AnimalCohort
    ) -> float:
        """Calculates the mass to be consumed from a prey cohort by the predator.

        This method utilizes the F_i_j_individual method to determine the rate at which
        the target cohort is consumed, and then calculates the actual mass to be
        consumed based on this rate and other model parameters.

        TODO: Replace delta_t with time step reference

        Args:
            animal_list: A list of animal cohorts that can be consumed by the
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
        animal_list: list[AnimalCohort],
        excrement_pools: list[ExcrementPool],
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> float:
        """This method handles mass assimilation from predation.

        This is Madingley's delta_assimilation_mass_predation

        TODO: rethink defecate location

        Args:
            animal_list: A list of animal cohorts that can be consumed by the
                         predator.
            excrement_pools: The pools representing the excrement in the territory.
            carcass_pools: The pools to which animal carcasses are delivered.

        Returns:
            The change in mass experienced by the predator.
        """

        total_consumed_mass = 0.0  # Initialize the total consumed mass

        for prey_cohort in animal_list:
            # Calculate the mass to be consumed from this cohort
            consumed_mass = self.calculate_consumed_mass_predation(
                animal_list, prey_cohort
            )
            # Call get_eaten on the prey cohort to update its mass and individuals
            actual_consumed_mass = prey_cohort.get_eaten(
                consumed_mass, self, carcass_pools
            )
            # Update total mass gained by the predator
            total_consumed_mass += actual_consumed_mass

        # Process waste generated from predation, separate from herbivory b/c diff waste
        self.defecate(excrement_pools, total_consumed_mass)
        return total_consumed_mass

    def calculate_consumed_mass_herbivory(
        self, plant_list: list[Resource], target_plant: Resource
    ) -> float:
        """Calculates the mass to be consumed from a plant resource by the herbivore.

        This method utilizes the F_i_k method to determine the rate at which the target
        plant is consumed, and then calculates the actual mass to be consumed based on
        this rate and other model parameters.

        TODO: Replace delta_t with actual time step reference

        Args:
            plant_list: A list of plant resources that can be consumed by the
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
        plant_list: list[Resource],
        excrement_pools: list[ExcrementPool],
        herbivory_waste_pools: dict[int, HerbivoryWaste],
    ) -> float:
        """This method handles mass assimilation from herbivory.

        TODO: rethink defecate location
        TODO: At present this just takes a single herbivory waste pool (for leaves),
        this probably should change to be a list of waste pools once herbivory for other
        plant tissues is added.
        TODO: update name

        Args:
            plant_list: A list of plant resources available for herbivory.
            excrement_pools: The pools representing the excrement in the territory.
            herbivory_waste_pools: Waste pools for plant biomass (at this point just
              leaves) that gets removed as part of herbivory but not actually consumed.

        Returns:
            A float of the total plant mass consumed by the animal cohort in g.

        """
        total_consumed_mass = 0.0  # Initialize the total consumed mass

        for plant in plant_list:
            # Calculate the mass to be consumed from this plant
            consumed_mass = self.calculate_consumed_mass_herbivory(plant_list, plant)
            # Update the plant resource's state based on consumed mass
            actual_consumed_mass, excess_mass = plant.get_eaten(consumed_mass, self)
            # Update total mass gained by the herbivore
            total_consumed_mass += actual_consumed_mass
            herbivory_waste_pools[plant.cell_id].mass_current += excess_mass

        # Process waste generated from predation, separate from predation b/c diff waste
        self.defecate(excrement_pools, total_consumed_mass)

        return total_consumed_mass

    def forage_cohort(
        self,
        plant_list: list[Resource],
        animal_list: list[AnimalCohort],
        excrement_pools: list[ExcrementPool],
        carcass_pools: dict[int, list[CarcassPool]],
        herbivory_waste_pools: dict[int, HerbivoryWaste],
    ) -> None:
        """This function handles selection of resources from a list for consumption.

        Args:
            plant_list: A list of plant resources available for herbivory.
            animal_list: A list of animal cohorts available for predation.
            excrement_pools: The pools representing the excrement in the grid cell.
            carcass_pools: The pools to which animal carcasses are delivered.
            herbivory_waste_pools: A dict of pools representing waste caused by
                herbivory.

        Return:
            A float value of the net change in consumer mass due to foraging.
        """
        if self.individuals == 0:
            LOGGER.warning("No individuals in cohort to forage.")
            return

        if self.mass_current == 0:
            LOGGER.warning("No mass left in cohort to forage.")
            return

        # Herbivore diet
        if self.functional_group.diet == DietType.HERBIVORE and plant_list:
            consumed_mass = self.delta_mass_herbivory(
                plant_list, excrement_pools, herbivory_waste_pools
            )  # Directly modifies the plant mass
            self.eat(consumed_mass)  # Accumulate net mass gain from each plant

        # Carnivore diet
        elif self.functional_group.diet == DietType.CARNIVORE and animal_list:
            # Calculate the mass gained from predation
            consumed_mass = self.delta_mass_predation(
                animal_list, excrement_pools, carcass_pools
            )
            # Update the predator's mass with the total gained mass
            self.eat(consumed_mass)

    def theta_i_j(self, animal_list: list[AnimalCohort]) -> float:
        """Cumulative density method for delta_mass_predation.

        The cumulative density of organisms with a mass lying within the same predator
        specific mass bin as Mi.

        Madingley

        TODO: current mass bin format makes no sense, dig up the details in the supp
        TODO: update A_cell with real reference to grid size
        TODO: update name

        Args:
            animal_list: A list of animal cohorts that can be consumed by the
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
        self, dt: float, carcass_pools: list[CarcassPool]
    ) -> None:
        """Inflict combined background, senescence, and starvation mortalities.

        TODO: Review logic of mass_max = adult_mass
        TODO: Review the use of ceil in number_dead, it fails for large animals.

        Args:
            dt: The time passed in the timestep (days).
            carcass_pools: The local carcass pool to which dead individuals go.

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
        self.die_individual(number_dead, carcass_pools)

    def get_prey(
        self,
        communities: dict[int, list[AnimalCohort]],
    ) -> list[AnimalCohort]:
        """Collect suitable prey for a given consumer cohort.

        This method filters suitable prey from the list of animal cohorts across the
        territory defined by the cohort's grid cells.

        Args:
            communities: A dictionary mapping cell IDs to sets of Consumers
                (animal cohorts).
            consumer_cohort: The Consumer for which a prey list is being collected.

        Returns:
            A sequence of Consumers that can be preyed upon.
        """
        prey_list: list = []

        # Iterate over the grid cells in the consumer cohort's territory
        for cell_id in self.territory:
            potential_prey_cohorts = communities[cell_id]

            # Iterate over each Consumer (potential prey) in the current community
            for prey_cohort in potential_prey_cohorts:
                # Skip if this cohort is not a prey of the current predator
                if prey_cohort.functional_group not in self.prey_groups:
                    continue

                # Get the size range of the prey this predator eats
                min_size, max_size = self.prey_groups[prey_cohort.functional_group.name]

                # Filter the potential prey cohorts based on their size
                if (
                    min_size <= prey_cohort.mass_current <= max_size
                    and prey_cohort.individuals != 0
                    and prey_cohort is not self
                ):
                    prey_list.append(prey_cohort)

        return prey_list

    def get_plant_resources(
        self, plant_resources: dict[int, list[Resource]]
    ) -> list[Resource]:
        """Returns a list of plant resources in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the plant resources available in those grid cells.

        Args:
            plant_resources: A dictionary of plants where keys are grid cell IDs.

        Returns:
            A list of Resource objects in this territory.
        """
        plant_resources_in_territory: list = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.territory:
            # Check if the cell_id is within the provided plant resources
            if cell_id in plant_resources:
                plant_resources_in_territory.extend(plant_resources[cell_id])

        return plant_resources_in_territory

    def get_excrement_pools(
        self, excrement_pools: dict[int, list[ExcrementPool]]
    ) -> list[ExcrementPool]:
        """Returns a list of excrement pools in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the excrement pools available in those grid cells.

        Args:
            excrement_pools: A dictionary of excrement pools where keys are grid
                cell IDs.

        Returns:
            A list of ExcrementPool objects in this territory.
        """
        excrement_pools_in_territory: list[ExcrementPool] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.territory:
            # Check if the cell_id is within the provided excrement pools
            if cell_id in excrement_pools:
                excrement_pools_in_territory.extend(excrement_pools[cell_id])

        return excrement_pools_in_territory

    def get_herbivory_waste_pools(
        self, plant_waste: dict[int, HerbivoryWaste]
    ) -> list[HerbivoryWaste]:
        """Returns a list of herbivory waste pools in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the herbivory waste pools available in those grid cells.

        Args:
            plant_waste: A dictionary of herbivory waste pools where keys are grid
                cell IDs.

        Returns:
            A list of HerbivoryWaste objects in this territory.
        """
        plant_waste_pools_in_territory: list[HerbivoryWaste] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.territory:
            # Check if the cell_id is within the provided herbivory waste pools
            if cell_id in plant_waste:
                plant_waste_pools_in_territory.append(plant_waste[cell_id])

        return plant_waste_pools_in_territory

    def get_carcass_pools(
        self, carcass_pools: dict[int, list[CarcassPool]]
    ) -> list[CarcassPool]:
        """Returns a list of carcass pools in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the carcass pools available in those grid cells.

        Args:
            carcass_pools: A dictionary of carcass pools where keys are grid
                cell IDs.

        Returns:
            A list of CarcassPool objects in this territory.
        """
        carcass_pools_in_territory: list[CarcassPool] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.territory:
            # Check if the cell_id is within the provided carcass pools
            if cell_id in carcass_pools:
                carcass_pools_in_territory.extend(carcass_pools[cell_id])

        return carcass_pools_in_territory

    def find_intersecting_carcass_pools(
        self,
        prey_territory: list[int],
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> list[CarcassPool]:
        """Find the carcass pools of the intersection of two territories.

        Args:
            prey_territory: Another AnimalTerritory to find the intersection with.
            carcass_pools: A dictionary mapping cell IDs to CarcassPool objects.

        Returns:
            A list of CarcassPools in the intersecting grid cells.
        """
        intersecting_keys = set(self.territory) & set(prey_territory)
        intersecting_carcass_pools: list[CarcassPool] = []
        for cell_id in intersecting_keys:
            intersecting_carcass_pools.extend(carcass_pools[cell_id])
        return intersecting_carcass_pools
