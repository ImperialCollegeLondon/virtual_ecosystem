"""The ''animal'' module provides animal module functionality."""

from __future__ import annotations

import random
import uuid
from math import ceil, exp, sqrt
from typing import Literal

from numpy import timedelta64

import virtual_ecosystem.models.animal.scaling_functions as sf
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_traits import DietType, VerticalOccupancy
from virtual_ecosystem.models.animal.cnp import CNP
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
        """Check if age is a positive number."""
        if mass < 0:
            raise ValueError("Mass must be a positive number.")
        """Check if mass is a positive number."""
        self.functional_group = functional_group
        """The functional group of the animal cohort which holds constants."""
        self.name = functional_group.name
        """The functional type name of the animal cohort."""
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
        self.location_status: Literal["active", "migrated", "aquatic"] = "active"
        """Location status of the cohort, active means present and participating."""
        self.remaining_time_away: float = 0.0
        """Remaining time that the cohort is frozen in a migrated or aquatic state."""
        self.id: uuid.UUID = uuid.uuid4()
        """A unique identifier for the cohort."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.is_mature: bool = False
        """Whether the cohort has reached adult body-mass."""
        self.time_to_maturity: float = 0.0
        """The amount of time [days] between birth and adult body-mass."""
        self.time_since_maturity: float = 0.0
        """The amount of time [days] since reaching adult body-mass."""
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
        self.cnp_proportions: dict[str, float] = self.functional_group.cnp_proportions
        """The normalized stoichiometric proportions that constrains growth."""
        if not abs(sum(self.cnp_proportions.values()) - 1.0) < 1e-6:
            raise ValueError("CNP proportions must sum to 1.")

        self.mass_cnp = CNP(
            carbon=mass * self.cnp_proportions["carbon"],
            nitrogen=mass * self.cnp_proportions["nitrogen"],
            phosphorus=mass * self.cnp_proportions["phosphorus"],
        )
        """The mass of C, N, and P in the cohort, from total mass and proportions."""

        self.reproductive_mass_cnp = CNP(0.0, 0.0, 0.0)
        """The reproductive mass of each stoichiometric element found in the animal
          cohort, {"carbon": value, "nitrogen": value, "phosphorus": value}."""

    @property
    def mass_current(self) -> float:
        """Dynamically calculate the current total body mass from CNP object."""
        return self.mass_cnp.total

    @property
    def reproductive_mass(self) -> float:
        """Dynamically calculate the current reproductive mass from CNP object."""
        return self.reproductive_mass_cnp.total

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

    def grow(self, resource_intake: dict[str, float]) -> dict[str, float]:
        """Handles growth based on resource intake, enforcing stoichiometry.

        Args:
            resource_intake: A dictionary of the mass of C, N, and P available for
              intake.

        Returns:
            A dictionary of the excess elements (waste) that could not be used for
             growth.
        """

        # Determine the potential growth for each element
        potential_growth = {
            element: resource_intake[element] / self.cnp_proportions[element]
            for element in self.cnp_proportions
        }

        # Identify the limiting element based on the minimum growth
        max_growth = min(potential_growth.values())

        # Calculate the mass of each element used for growth
        used_carbon = max_growth * self.cnp_proportions["carbon"]
        used_nitrogen = max_growth * self.cnp_proportions["nitrogen"]
        used_phosphorus = max_growth * self.cnp_proportions["phosphorus"]

        # Update the mass_cnp object using the new add method
        self.mass_cnp.update(
            carbon=used_carbon, nitrogen=used_nitrogen, phosphorus=used_phosphorus
        )

        # Subtract the used mass from the resource intake to get waste
        resource_intake["carbon"] -= used_carbon
        resource_intake["nitrogen"] -= used_nitrogen
        resource_intake["phosphorus"] -= used_phosphorus

        return resource_intake

    def metabolize(self, temperature: float, dt: timedelta64) -> dict[str, float]:
        """The function to reduce body carbon mass through metabolism.

        This method reduces the carbon component of the cohort's body mass through
        metabolic activity. Metabolism is a function of environmental temperature
        for ectotherms, while endotherms are unaffected by temperature changes.

        TODO: Update with stoichiometry for nitrogen and phosphorus.

        Args:
            temperature: Current air temperature (K).
            dt: Number of days over which the metabolic costs should be calculated.

        Returns:
            The total carbon mass metabolized by the cohort.
        """

        if dt < timedelta64(0, "D"):
            raise ValueError("dt cannot be negative.")

        if self.mass_cnp.carbon < 0:
            raise ValueError("Carbon mass (C) cannot be negative.")

        # Calculate potential carbon metabolized (kg/day * number of days)
        potential_carbon_metabolized = sf.metabolic_rate(
            self.mass_current,
            temperature,
            self.functional_group.metabolic_rate_terms,
            self.functional_group.metabolic_type,
        ) * float(dt / timedelta64(1, "D"))

        # Ensure metabolized carbon does not exceed available carbon
        actual_carbon_metabolized = min(
            self.mass_cnp.carbon, potential_carbon_metabolized
        )

        # Subtract metabolized carbon directly from mass_cnp
        self.mass_cnp.update(carbon=-actual_carbon_metabolized)

        # Return the total metabolized carbon mass for the entire cohort
        return {
            "carbon": actual_carbon_metabolized * self.individuals,
            "nitrogen": 0.0,
            "phosphorus": 0.0,
        }

    def excrete(
        self, excreta_mass: dict[str, float], excrement_pools: list[ExcrementPool]
    ) -> None:
        """Transfers metabolic wastes to the excrement pools.

        Args:
            excreta_mass: Mass of C, N, and P to be excreted as a dictionary.
            excrement_pools: List of excrement pools for distributing waste.

        Raises:
            ValueError: For invalid keys or negative values in excreta_mass.
        """
        required_keys = {"carbon", "nitrogen", "phosphorus"}
        if not required_keys.issubset(excreta_mass.keys()):
            raise ValueError(
                f"excreta_mass must contain all required keys {required_keys}."
            )
        if any(value < 0 for value in excreta_mass.values()):
            raise ValueError("Excreta mass values must be non-negative.")

        number_communities = len(excrement_pools)
        if number_communities == 0:
            raise ValueError("No excrement pools provided for waste distribution.")

        # Distribute excreta mass evenly across pools
        for excrement_pool in excrement_pools:
            scavengeable_mass = {
                nutrient: (excreta_mass[nutrient] / number_communities)
                * (1 - self.decay_fraction_excrement)
                for nutrient in excreta_mass
            }
            decomposed_mass = {
                nutrient: (excreta_mass[nutrient] / number_communities)
                * self.decay_fraction_excrement
                for nutrient in excreta_mass
            }

            # Fixed method calls to pass individual values
            excrement_pool.scavengeable_cnp.update(
                carbon=scavengeable_mass["carbon"],
                nitrogen=scavengeable_mass["nitrogen"],
                phosphorus=scavengeable_mass["phosphorus"],
            )
            excrement_pool.decomposed_cnp.update(
                carbon=decomposed_mass["carbon"],
                nitrogen=decomposed_mass["nitrogen"],
                phosphorus=decomposed_mass["phosphorus"],
            )

    def respire(self, excreta_mass: dict[str, float]) -> float:
        """Transfers carbonaceous metabolic wastes to the atmosphere.

        This method processes the metabolic waste for carbon and returns the total
        mass respired to the atmosphere as a float. Currently, only carbon is affected.

        TODO: This method needs to be properly fleshed out or it will produce a small
        error in carbon totals.

        Args:
            excreta_mass: A dictionary representing the mass of each nutrient excreted
                by the cohort: {"carbon": value, "nitrogen": value,
                "phosphorus": value}.

        Returns:
            A float representing the total carbon mass respired to the atmosphere.
        """

        # Validate the input dictionary
        if "carbon" not in excreta_mass:
            raise ValueError("excreta_mass must contain the key 'C' for carbon.")
        if excreta_mass["carbon"] < 0:
            raise ValueError("Carbon mass in excreta_mass cannot be negative.")

        # Calculate the carbonaceous waste for respiration
        respired_mass = (
            excreta_mass["carbon"] * self.constants.carbon_excreta_proportion
        )

        return respired_mass

    def defecate(
        self, excrement_pools: list[ExcrementPool], mass_consumed: dict[str, float]
    ) -> None:
        """Transfers unassimilated waste mass from an cohort to the excrement pools.

        Args:
            excrement_pools: List of excrement pools for waste distribution.
            mass_consumed: Dictionary specifying the mass of each element in the
             consumed food.

        Raises:
            ValueError: If `mass_consumed` is missing required keys or contains negative
              values.
        """
        required_keys = {"carbon", "nitrogen", "phosphorus"}
        if not required_keys.issubset(mass_consumed.keys()):
            raise ValueError(
                f"mass_consumed must contain all required keys {required_keys}."
            )
        if any(value < 0 for value in mass_consumed.values()):
            raise ValueError("Mass values in mass_consumed must be non-negative.")

        number_communities = len(excrement_pools)
        if number_communities == 0:
            raise ValueError("No excrement pools provided for waste distribution.")

        # Compute total waste mass based on conversion efficiency and individuals
        total_waste_mass = {
            nutrient: mass
            * self.functional_group.conversion_efficiency
            * self.individuals
            for nutrient, mass in mass_consumed.items()
        }

        # Distribute waste across pools
        for excrement_pool in excrement_pools:
            scavengeable_mass = {
                nutrient: (total_waste_mass[nutrient] / number_communities)
                * (1 - self.decay_fraction_excrement)
                for nutrient in total_waste_mass
            }
            decomposed_mass = {
                nutrient: (total_waste_mass[nutrient] / number_communities)
                * self.decay_fraction_excrement
                for nutrient in total_waste_mass
            }

            # Use CNP methods for in-place updates
            excrement_pool.scavengeable_cnp.update(**scavengeable_mass)
            excrement_pool.decomposed_cnp.update(**decomposed_mass)

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
        self, number_of_deaths: int, carcass_pools: list[CarcassPool]
    ) -> None:
        """Handles the death of individuals in the cohort.

        Transfers the biomass of dead individuals to the carcass pools, distributing
        mass between scavengeable and decomposed compartments.

        Args:
            number_of_deaths (int): Number of individuals dying in the cohort.
            carcass_pools (list[CarcassPool]): Carcass pools receiving remains.

        Raises:
            ValueError: If `number_of_deaths` is invalid or exceeds the cohort size.
        """
        if number_of_deaths <= 0:
            raise ValueError("Number of deaths must be a positive integer.")
        if number_of_deaths > self.individuals:
            raise ValueError(
                f"Number of deaths ({number_of_deaths}) exceeds the number of "
                f"individuals in the cohort ({self.individuals})."
            )

        # Calculate total mass lost per element
        carbon_lost = self.mass_cnp.carbon * number_of_deaths
        nitrogen_lost = self.mass_cnp.nitrogen * number_of_deaths
        phosphorus_lost = self.mass_cnp.phosphorus * number_of_deaths

        # Reduce the cohort size
        self.individuals -= number_of_deaths

        # Transfer the lost mass to carcass pools
        self.update_carcass_pool(
            carbon_lost, nitrogen_lost, phosphorus_lost, carcass_pools
        )

    def update_carcass_pool(
        self,
        carbon: float,
        nitrogen: float,
        phosphorus: float,
        carcass_pools: list[CarcassPool],
    ) -> None:
        """Updates the carcass pools after deaths.

        Distributes carcass mass among pools, dividing it into scavengeable and
        decomposed fractions.

        Args:
            carbon (float): The total carbon mass to be distributed.
            nitrogen (float): The total nitrogen mass to be distributed.
            phosphorus (float): The total phosphorus mass to be distributed.
            carcass_pools (list[CarcassPool]): The carcass pools receiving the biomass.

        Raises:
            ValueError: If any input mass is negative or no carcass pools are provided.
        """
        if carbon < 0 or nitrogen < 0 or phosphorus < 0:
            raise ValueError(
                f"Carcass mass values must be non-negative. Provided: "
                f"carbon={carbon}, nitrogen={nitrogen}, phosphorus={phosphorus}"
            )

        number_carcass_pools = len(carcass_pools)
        if number_carcass_pools == 0:
            raise ValueError("No carcass pools provided for waste distribution.")

        # Distribute mass across pools
        carbon_per_pool = carbon / number_carcass_pools
        nitrogen_per_pool = nitrogen / number_carcass_pools
        phosphorus_per_pool = phosphorus / number_carcass_pools

        scavengeable_factor = 1 - self.decay_fraction_carcasses
        decomposed_factor = self.decay_fraction_carcasses

        for carcass_pool in carcass_pools:
            carcass_pool.scavengeable_cnp.update(
                carbon=carbon_per_pool * scavengeable_factor,
                nitrogen=nitrogen_per_pool * scavengeable_factor,
                phosphorus=phosphorus_per_pool * scavengeable_factor,
            )
            carcass_pool.decomposed_cnp.update(
                carbon=carbon_per_pool * decomposed_factor,
                nitrogen=nitrogen_per_pool * decomposed_factor,
                phosphorus=phosphorus_per_pool * decomposed_factor,
            )

    def get_eaten(
        self,
        potential_consumed_mass: float,
        predator: AnimalCohort,
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> dict[str, float]:
        """Handles predation, removing individuals and distributing biomass.

        Args:
            potential_consumed_mass: The mass intended to be consumed by the predator.
            predator: The predator consuming the cohort.
            carcass_pools: The pools to which remains of eaten individuals are
              delivered.

        Returns:
            A dictionary of the actual mass consumed by the predator in stoichiometric
              terms.
        """

        # Ensure the prey has nonzero body mass
        if self.mass_current <= 0:
            raise ValueError("Prey cohort mass must be greater than zero.")

        # Compute the mass of a single individual
        individual_mass = self.mass_current

        # Compute the maximum individuals that could be killed
        max_individuals_killed = ceil(potential_consumed_mass / individual_mass)
        actual_individuals_killed = min(max_individuals_killed, self.individuals)

        print("Max Individuals That Could Be Killed:", max_individuals_killed)
        print("Actual Individuals Removed:", actual_individuals_killed)

        # Compute total mass killed
        actual_mass_killed = actual_individuals_killed * individual_mass

        # Compute the actual mass that can be consumed, given predator's efficiency
        actual_mass_consumed = min(actual_mass_killed, potential_consumed_mass)
        consumed_mass_after_efficiency = (
            actual_mass_consumed * predator.functional_group.mechanical_efficiency
        )

        # Compute the carcass mass (mass that is not consumed)
        carcass_mass_total = actual_mass_killed - consumed_mass_after_efficiency

        # Convert consumed mass to stoichiometric proportions
        consumed_carbon = (
            self.mass_cnp.carbon / individual_mass
        ) * consumed_mass_after_efficiency
        consumed_nitrogen = (
            self.mass_cnp.nitrogen / individual_mass
        ) * consumed_mass_after_efficiency
        consumed_phosphorus = (
            self.mass_cnp.phosphorus / individual_mass
        ) * consumed_mass_after_efficiency

        # Convert carcass mass to stoichiometric proportions
        carcass_carbon = (self.mass_cnp.carbon / individual_mass) * carcass_mass_total
        carcass_nitrogen = (
            self.mass_cnp.nitrogen / individual_mass
        ) * carcass_mass_total
        carcass_phosphorus = (
            self.mass_cnp.phosphorus / individual_mass
        ) * carcass_mass_total

        # Remove individuals from the prey cohort
        self.individuals -= actual_individuals_killed

        # If no individuals remain, mark the cohort as dead
        if self.individuals <= 0:
            self.is_alive = False

        # Find the intersection of prey and predator territories
        intersection_carcass_pools = self.find_intersecting_carcass_pools(
            predator.territory, carcass_pools
        )

        # Update the carcass pool with the carcass mass
        self.update_carcass_pool(
            carcass_carbon,
            carcass_nitrogen,
            carcass_phosphorus,
            intersection_carcass_pools,
        )

        return {
            "carbon": consumed_carbon,
            "nitrogen": consumed_nitrogen,
            "phosphorus": consumed_phosphorus,
        }

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
        efficiency (alpha), the fraction of the total plant stock available to the
        cohort (phi), and the biomass of the target plant.

        Args:
            target_plant: The plant resource being targeted by the herbivore cohort.
            alpha: The search efficiency rate of the herbivore cohort.

        Returns:
            A float representing the potential consumed biomass of the target plant by
            the cohort [g/day].

        Raises:
            ValueError: If `target_plant.mass_current` is missing or negative.
            ValueError: If `alpha` is negative or zero.
        """

        # Validate that target_plant has a valid mass_current
        if (
            not hasattr(target_plant, "mass_current")
            or target_plant.mass_current is None
        ):
            raise ValueError(
                "target_plant.mass_current must be defined and non-negative."
            )
        if target_plant.mass_current < 0:
            raise ValueError(
                f"target_plant.mass_current must be non-negative."
                f"Got {target_plant.mass_current}."
            )

        # Validate alpha (search efficiency)
        if alpha <= 0:
            raise ValueError(f"alpha must be positive. Got {alpha}.")

        phi = self.functional_group.constants.phi_herb_t
        A_cell = 1.0  # Temporary value

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
        TODO: Update with stoichiometry

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
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> dict[str, float]:
        """Handles mass assimilation from predation.

        This is Madingley's delta_assimilation_mass_predation.

        Args:
            animal_list: A list of animal cohorts that can be consumed by the predator.
            carcass_pools: The pools to which animal carcasses are delivered.

        Returns:
            A dictionary representing the total change in mass (C, N, P) experienced by
            the predator: {"carbon": value, "nitrogen": value, "phosphorus": value}.

        Raises:
            ValueError: If `animal_list` or `carcass_pools` is None.
            ValueError: If `prey_cohort.get_eaten()` returns None.
            ValueError: If `self.calculate_consumed_mass_predation()` returns None.
        """

        # Validate inputs
        if animal_list is None:
            raise ValueError("animal_list cannot be None.")
        if carcass_pools is None:
            raise ValueError("carcass_pools cannot be None.")

        # If no prey are available, return zero change
        if not animal_list:
            return {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}

        # Initialize the total consumed mass as a stoichiometric dictionary
        total_consumed_mass = {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}

        for prey_cohort in animal_list:
            # Calculate the mass to be consumed from this cohort
            consumed_mass = self.calculate_consumed_mass_predation(
                animal_list, prey_cohort
            )

            if consumed_mass is None:
                raise ValueError(
                    f"calculate_consumed_mass_predation() returned None for"
                    f"{prey_cohort}."
                )

            # Call get_eaten on the prey cohort to update its mass and individuals
            actual_consumed_cnp = prey_cohort.get_eaten(
                consumed_mass, self, carcass_pools
            )

            if actual_consumed_cnp is None:
                raise ValueError(f"get_eaten() returned None for {prey_cohort}.")

            # Update total consumed mass for each nutrient
            for element in total_consumed_mass:
                total_consumed_mass[element] += actual_consumed_cnp[element]

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
        herbivory_waste_pools: dict[int, HerbivoryWaste],
    ) -> dict[str, float]:
        """Handles mass assimilation from herbivory.

        TODO: At present this just takes a single herbivory waste pool (for leaves),
        this probably should change to be a list of waste pools once herbivory for other
        plant tissues is added.
        TODO: update name.

        Args:
            plant_list: A list of plant resources available for herbivory.
            herbivory_waste_pools: Waste pools for plant biomass (at this point just
                leaves) that gets removed as part of herbivory but not consumed.

        Returns:
            A dictionary of total plant mass (C, N, P) consumed by the animal cohort.

        Raises:
            ValueError: If `plant_list` or `herbivory_waste_pools` is None.
            ValueError: If `calculate_consumed_mass_herbivory` returns None.
            ValueError: If `get_eaten` returns None.
            KeyError: If `plant.cell_id` is missing from `herbivory_waste_pools`.
        """

        # Validate inputs
        if plant_list is None:
            raise ValueError("plant_list cannot be None.")
        if herbivory_waste_pools is None:
            raise ValueError("herbivory_waste_pools cannot be None.")

        # If no plants are available, return zero change
        if not plant_list:
            return {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}

        # Initialize total consumed stoichiometric masses
        total_consumed_cnp = {
            element: 0.0 for element in ["carbon", "nitrogen", "phosphorus"]
        }

        for plant in plant_list:
            # Calculate the mass to be consumed from this plant
            consumed_mass = self.calculate_consumed_mass_herbivory(plant_list, plant)

            if consumed_mass is None:
                raise ValueError(
                    f"calculate_consumed_mass_herbivory() returned None for {plant}."
                )

            # Update the plant resource's state based on consumed mass
            herbivore_gain_cnp, plant_litter_cnp = plant.get_eaten(consumed_mass, self)

            if herbivore_gain_cnp is None or plant_litter_cnp is None:
                raise ValueError(f"get_eaten() returned None for {plant}.")

            # Update total mass gained by the herbivore
            for element in total_consumed_cnp:
                total_consumed_cnp[element] += herbivore_gain_cnp[element]

            # Ensure plant.cell_id exists in waste pools before adding waste
            if plant.cell_id not in herbivory_waste_pools:
                raise KeyError(
                    f"herbivory_waste_pools is missing cell_id {plant.cell_id}."
                )

            # Add the litter to the appropriate herbivory waste pool
            herbivory_waste_pools[plant.cell_id].add_waste(plant_litter_cnp)

        return total_consumed_cnp

    def forage_cohort(
        self,
        plant_list: list[Resource],
        animal_list: list[AnimalCohort],
        excrement_pools: list[ExcrementPool],
        carcass_pools: dict[int, list[CarcassPool]],
        herbivory_waste_pools: dict[int, HerbivoryWaste],
    ) -> None:
        """This function handles selection of resources from a list for consumption.

        TODO: Update with stoichiometry

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
                plant_list, herbivory_waste_pools
            )  # Directly modifies the plant mass
            self.eat(
                consumed_mass, excrement_pools
            )  # Accumulate net mass gain from each plant

        # Carnivore diet
        elif self.functional_group.diet == DietType.CARNIVORE and animal_list:
            # Calculate the mass gained from predation
            consumed_mass = self.delta_mass_predation(animal_list, carcass_pools)
            # Update the predator's mass with the total gained mass
            self.eat(consumed_mass, excrement_pools)

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

    def eat(
        self, mass_consumed: dict[str, float], excrement_pools: list[ExcrementPool]
    ) -> None:
        """Handles the mass gain from consuming food and processes waste.

        This method updates the consumer's mass based on the amount of food consumed
        in stoichiometric terms. It also handles waste by calling `defecate` with any
        excess nutrients after growth.

        Args:
            mass_consumed: A dictionary representing the mass of each nutrient consumed
                by this consumer: {"carbon": value, "nitrogen": value,
                "phosphorus": value}.
            excrement_pools: The ExcrementPool objects in the cohort's territory in
                which waste is deposited.

        Raises:
            ValueError: If `mass_consumed` contains negative values or missing keys.
            ValueError: If no excrement pools are provided.
        """
        if self.individuals == 0:
            return

        # Validate mass_consumed input
        required_keys = {"carbon", "nitrogen", "phosphorus"}
        if not required_keys.issubset(mass_consumed.keys()):
            raise ValueError(
                f"mass_consumed must contain all required keys {required_keys}. "
                f"Provided keys: {mass_consumed.keys()}"
            )
        if any(value < 0 for value in mass_consumed.values()):
            raise ValueError(
                f"Values in mass_consumed must be non-negative: {mass_consumed}"
            )

        # Ensure at least one excrement pool is provided
        if not excrement_pools:
            raise ValueError("At least one excrement pool must be provided.")

        # Apply growth and calculate waste
        waste_mass = self.grow(mass_consumed)

        # Pass the waste to the defecate method for processing
        self.defecate(excrement_pools, waste_mass)

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

    def can_prey_on(self, prey_cohort: AnimalCohort) -> bool:
        """Check if the cohort can prey upon another cohort.

        Determines if another animal cohort is suitable prey based on the predator's
        defined prey groups, prey body mass, and vertical occupancy.

        Args:
            prey_cohort: An animal cohort potentially being preyed upon.

        Returns:
            True if the prey cohort meets size, identity, and vertical occupancy
              criteria, False otherwise.
        """
        if prey_cohort.functional_group.name not in self.prey_groups:
            return False

        min_size, max_size = self.prey_groups[prey_cohort.functional_group.name]

        return (
            min_size <= prey_cohort.mass_current <= max_size
            and prey_cohort.individuals > 0
            and prey_cohort is not self
            and self.match_vertical(prey_cohort.functional_group.vertical_occupancy)
        )

    def get_prey(
        self,
        communities: dict[int, list[AnimalCohort]],
    ) -> list[AnimalCohort]:
        """Collect suitable prey cohorts within the cohort's territory.

        Args:
            communities: Dictionary mapping cell IDs to lists of animal cohorts.

        Returns:
            List of animal cohorts that can be preyed upon.
        """
        prey_list: list[AnimalCohort] = []

        for cell_id in self.territory:
            for prey_cohort in communities[cell_id]:
                if self.can_prey_on(prey_cohort):
                    prey_list.append(prey_cohort)

        return prey_list

    def can_forage_on(self, resource: Resource) -> bool:
        """Check if the cohort can forage on a given non-cohort resource pool.

        This will soon be expanded to include more suitability checks.

        Args:
            resource: A non-cohort resource pool object implementing the Resource
              protocol.

        Returns:
            True if the cohort and resource share overlapping vertical occupancy,
            False otherwise.
        """
        return self.match_vertical(resource.vertical_occupancy)

    def get_plant_resources(
        self, plant_resources: dict[int, list[Resource]]
    ) -> list[Resource]:
        """Return plant resources accessible within this cohort's territory.

        Args:
            plant_resources: Dictionary of plant resources keyed by grid cell IDs.

        Returns:
            List of accessible Resource objects within the territory.
        """
        plant_resources_in_territory: list[Resource] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.territory:
            # Check if the cell_id is within the provided plant resources
            if cell_id in plant_resources:
                for resource in plant_resources[cell_id]:
                    if self.can_forage_on(resource):
                        plant_resources_in_territory.append(resource)

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

    def is_migration_season(self) -> bool:
        """Handles determination of whether it is time to migrate.

        Temporary probabilistic migration.

        TODO: update when we have seasonality

        Returns: A bool of whether it is time to migrate.


        Notes:
            This method uses Python's built-in :func:`random.random` function.

        """

        return random.random() <= self.constants.seasonal_migration_probability

    def match_vertical(self, resource_occupancy: VerticalOccupancy) -> bool:
        """Check whether cohort vertical occupancy overlaps with a resource or prey.

        This method determines whether the vertical occupancy of the consumer cohort
        overlaps with the vertical occupancy of a resource (pool or cohort). Animals
        can only forage resources that share at least one overlapping vertical space.

        Args:
            resource_occupancy: The vertical occupancy trait of the potential resource
                or prey.

        Returns:
            True if the vertical occupancy overlaps; False otherwise.

        """
        return bool(resource_occupancy & self.functional_group.vertical_occupancy)
