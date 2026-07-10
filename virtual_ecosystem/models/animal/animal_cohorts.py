"""The ''animal'' module provides animal module functionality."""

from __future__ import annotations

import random
import uuid
from _collections_abc import Callable, Mapping
from math import ceil, exp, log, sqrt
from typing import Literal, TypeVar, cast

from numpy import mean, timedelta64
from numpy.random import binomial
from numpy.typing import NDArray

import virtual_ecosystem.models.animal.scaling_functions as sf
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.animal.animal_traits import DietType, VerticalOccupancy
from virtual_ecosystem.models.animal.array_resources import CellResource, ResourcePool
from virtual_ecosystem.models.animal.cnp import CNP
from virtual_ecosystem.models.animal.decay import (
    CarcassPool,
    ExcrementPool,
    FungalFruitPool,
    HerbivoryWaste,
    SoilPool,
    find_decay_consumed_split,
)
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup
from virtual_ecosystem.models.animal.model_config import AnimalConstants
from virtual_ecosystem.models.animal.protocols import Resource

_T = TypeVar("_T")


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
        constants: AnimalConstants = AnimalConstants(),
        core_constants: CoreConstants = CoreConstants(),
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
        self.core_constants = core_constants
        """Core constants."""
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
        self.prey_groups: dict[str, tuple[float, float]] = {}
        """The identification of usable food resources."""
        self.territory_size = sf.territory_size(
            self.functional_group.adult_mass,
            self.constants.territory_size_terms[self.functional_group.metabolic_type][
                self.functional_group.taxa
            ],
        )
        """The size in m2 of the animal cohort's territory."""
        self.territory_cells = ceil(self.territory_size / grid.cell_area)
        """The number of grid cells the cohort occupies."""
        self.occupancy_proportion: float = 1.0 / self.territory_cells
        """The proportion of the cohort that is within a grid cell of territory."""
        self._initialize_territory(centroid_key)
        """Initialize the territory using the centroid grid key."""
        self.territory: list[int]
        """The list of grid cells currently occupied by the cohort."""
        self.sigma_f_t: float = 1.0
        """The Activity window fraction in [0, 1]."""
        self.reference_temp: float = self.functional_group.reference_annual_mean_temp
        """The mean reference temp of the functional group over vertical strata."""
        self.current_temperature: float = (
            self.functional_group.reference_annual_mean_temp
        )
        """Mean territory temperature [°C] last recorded by
        :meth:`update_activity_window`. Seeded to the functional group's reference
        annual mean so that endotherms and any cohort that calls :meth:`metabolize`
        before its first activity-window update receive a physically reasonable
        value."""
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
            C=mass * self.cnp_proportions["C"],
            N=mass * self.cnp_proportions["N"],
            P=mass * self.cnp_proportions["P"],
        )
        """The mass of C, N, and P in the cohort, from total mass and proportions."""

        self.reproductive_mass_cnp = CNP(0.0, 0.0, 0.0)
        """The reproductive mass of each stoichiometric element found in the animal
          cohort, {"C": value, "N": value, "P": value}."""
        self.largest_mass_achieved: float = mass
        """The largest body-mass ever achieved by this cohort [kg]."""
        self.diet_category_count: int = (
            self.functional_group.diet.count_dietary_categories()
        )
        """The number of different diet categories consumed by the cohort."""
        self.trophic_record: dict[tuple[str, str], dict[str, float]] = {}
        """A record of the mass transfer from resource to consumer during the
        timestep. tuple["kind", "id"] where kind is a str resource category and
        id is a uuid or a cell_id. 
        Value example: {"C": 1.2, "N": 0.08, "P": 0.01}"""

    @property
    def mass_current(self) -> float:
        """Dynamically calculate the current total body mass from CNP object."""
        return self.mass_cnp.total

    @property
    def reproductive_mass(self) -> float:
        """Dynamically calculate the current reproductive mass from CNP object."""
        return self.reproductive_mass_cnp.total

    def update_largest_mass(self) -> None:
        """Update the record of the largest body-mass achieved by this cohort.

        This provides a rough approximation of the development process. Once maturity
        is achieved, adult mass becomes the reference for starvation as normal.

        """

        if self.mass_current > self.largest_mass_achieved:
            self.largest_mass_achieved = min(
                self.mass_current, self.functional_group.adult_mass
            )

    def get_territory_cells(self, centroid_key: int) -> list[int]:
        """This calls bfs_territory to determine the scope of the territory.

        Args:
            centroid_key: The central grid cell key of the territory.

        """

        # Perform BFS to determine the territory cells
        territory_cells = sf.bfs_territory(
            centroid_key,
            self.territory_cells,
            self.grid.cell_nx,
            self.grid.cell_ny,
        )

        return territory_cells

    def _initialize_territory(
        self,
        centroid_key: int,
    ) -> None:
        """This initializes the territory occupied by the cohort.

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

    def _clamp_cnp_noise(self, cnp: dict[str, float]) -> dict[str, float]:
        """Clamp sub-tolerance negative CNP values to zero.

        Floating point arithmetic in elemental mass ratio calculations can produce
        tiny negative values (order 1e-17) that are noise rather than genuine errors.
        Values more negative than _ELEMENTAL_MASS_NOISE_TOLERANCE are left unchanged
        and will be caught by downstream validation.

        Args:
            cnp: A dictionary of elemental masses keyed by "C", "N", "P".

        Returns:
            The CNP dictionary with noise-level negatives clamped to zero.
        """
        return {
            k: 0.0 if -self.constants._ELEMENTAL_MASS_NOISE_TOLERANCE < v < 0.0 else v
            for k, v in cnp.items()
        }

    def reset_trophic_record(self) -> None:
        """Reset the trophic transfer record for a new timestep."""
        self.trophic_record.clear()

    def record_trophic_transfer(
        self, resource_key: tuple[str, str], delta: CNP
    ) -> None:
        """Accumulate a trophic mass transfer for the current timestep.

        Values are stored as a simple dict of floats for easy export.
        This records the total CNP mass removed from a given resource by this cohort
        during the current timestep.

        Args:
            resource_key: A tuple of (resource_kind, resource_id), where both elements
                are strings.
            delta: The CNP mass removed from the resource in a single feeding event.

        Raises:
            ValueError: If any element of `delta` is negative.
        """
        if delta.total == 0.0:
            return

        if delta.C < 0.0 or delta.N < 0.0 or delta.P < 0.0:
            raise ValueError(
                "Trophic transfer masses must be non-negative. "
                f"Received carbon={delta.C}, N={delta.N}, "
                f"P={delta.P}."
            )

        if resource_key not in self.trophic_record:
            self.trophic_record[resource_key] = {
                "C": 0.0,
                "N": 0.0,
                "P": 0.0,
            }

        entry = self.trophic_record[resource_key]
        entry["C"] += delta.C
        entry["N"] += delta.N
        entry["P"] += delta.P

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
        used_carbon = max_growth * self.cnp_proportions["C"]
        used_nitrogen = max_growth * self.cnp_proportions["N"]
        used_phosphorus = max_growth * self.cnp_proportions["P"]

        # Update the mass_cnp object using the new add method
        self.mass_cnp.update(C=used_carbon, N=used_nitrogen, P=used_phosphorus)

        # Subtract the used mass from the resource intake to get waste
        resource_intake["C"] -= used_carbon
        resource_intake["N"] -= used_nitrogen
        resource_intake["P"] -= used_phosphorus

        # Numerical safety: clamp tiny negatives to zero, but catch real bugs.
        eps = 1e-12
        for element in ("C", "N", "P"):
            value = resource_intake[element]
            if value < 0.0:
                if value > -eps:
                    resource_intake[element] = 0.0
                else:
                    raise ValueError(
                        f"grow produced negative waste for {element}: {value}"
                    )

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

        if self.mass_cnp.C < 0:
            raise ValueError("Carbon mass (C) cannot be negative.")

        # Calculate potential carbon metabolized (kg/day * number of days)
        potential_carbon_metabolized = sf.metabolic_rate(
            mass=self.mass_current,
            temperature=temperature,
            terms=self.functional_group.metabolic_rate_terms,
            metabolic_type=self.functional_group.metabolic_type,
            sigma_f_t=self.sigma_f_t,
            metabolic_scaling_coefficients=self.constants.metabolic_scaling_coefficients,
            boltzmann_constant=self.core_constants.boltzmann_constant,
        ) * float(dt / timedelta64(1, "D"))

        # Ensure metabolized carbon does not exceed available carbon
        actual_carbon_metabolized = min(self.mass_cnp.C, potential_carbon_metabolized)

        # Subtract metabolized carbon directly from mass_cnp
        self.mass_cnp.update(C=-actual_carbon_metabolized)

        # Return the total metabolized carbon mass for the entire cohort
        return {
            "C": actual_carbon_metabolized * self.individuals,
            "N": 0.0,
            "P": 0.0,
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
        required_keys = {"C", "N", "P"}
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
                C=scavengeable_mass["C"],
                N=scavengeable_mass["N"],
                P=scavengeable_mass["P"],
            )
            excrement_pool.decomposed_cnp.update(
                C=decomposed_mass["C"],
                N=decomposed_mass["N"],
                P=decomposed_mass["P"],
            )

    def respire(self, excreta_mass: dict[str, float]) -> float:
        """Transfers carbonaceous metabolic wastes to the atmosphere.

        This method processes the metabolic waste for carbon and returns the total
        mass respired to the atmosphere as a float. Currently, only carbon is affected.

        TODO: This method needs to be properly fleshed out or it will produce a small
        error in carbon totals.

        Args:
            excreta_mass: A dictionary representing the mass of each nutrient excreted
                by the cohort: {"C": value, "N": value,
                "P": value}.

        Returns:
            A float representing the total carbon mass respired to the atmosphere.
        """

        # Validate the input dictionary
        if "C" not in excreta_mass:
            raise ValueError("excreta_mass must contain the key 'C' for carbon.")
        if excreta_mass["C"] < 0:
            raise ValueError("Carbon mass in excreta_mass cannot be negative.")

        # Calculate the carbonaceous waste for respiration
        respired_mass = excreta_mass["C"] * self.constants.carbon_excreta_proportion

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
        required_keys = {"C", "N", "P"}
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

        # Zero deaths: nothing to do
        if number_of_deaths == 0:
            return

        # Negative deaths are invalid
        if number_of_deaths < 0:
            raise ValueError(
                f"Number of deaths must be non-negative, got {number_of_deaths}."
            )

        # Can't kill more individuals than exist
        if number_of_deaths > self.individuals:
            raise ValueError(
                f"Number of deaths ({number_of_deaths}) exceeds cohort size "
                f"({self.individuals})."
            )

        # Calculate total mass lost per element
        carbon_lost = self.mass_cnp.C * number_of_deaths
        nitrogen_lost = self.mass_cnp.N * number_of_deaths
        phosphorus_lost = self.mass_cnp.P * number_of_deaths

        # Reduce the cohort size
        self.individuals -= number_of_deaths

        # Transfer the lost mass to carcass pools
        self.update_carcass_pool(
            carbon_lost, nitrogen_lost, phosphorus_lost, carcass_pools
        )

    def update_carcass_pool(
        self,
        C: float,
        N: float,
        P: float,
        carcass_pools: list[CarcassPool],
    ) -> None:
        """Updates the carcass pools after deaths.

        Distributes carcass mass among pools, dividing it into scavengeable and
        decomposed fractions.

        Args:
            C (float): The total carbon mass to be distributed.
            N (float): The total nitrogen mass to be distributed.
            P (float): The total phosphorus mass to be distributed.
            carcass_pools (list[CarcassPool]): The carcass pools receiving the biomass.

        Raises:
            ValueError: If any input mass is negative or no carcass pools are provided.
        """
        if C < 0 or N < 0 or P < 0:
            raise ValueError(
                f"Carcass mass values must be non-negative. Provided: "
                f"C={C}, N={N}, P={P}"
            )

        number_carcass_pools = len(carcass_pools)
        if number_carcass_pools == 0:
            raise ValueError("No carcass pools provided for waste distribution.")

        # Distribute mass across pools
        carbon_per_pool = C / number_carcass_pools
        nitrogen_per_pool = N / number_carcass_pools
        phosphorus_per_pool = P / number_carcass_pools

        scavengeable_factor = 1 - self.decay_fraction_carcasses
        decomposed_factor = self.decay_fraction_carcasses

        for carcass_pool in carcass_pools:
            carcass_pool.scavengeable_cnp.update(
                C=carbon_per_pool * scavengeable_factor,
                N=nitrogen_per_pool * scavengeable_factor,
                P=phosphorus_per_pool * scavengeable_factor,
            )
            carcass_pool.decomposed_cnp.update(
                C=carbon_per_pool * decomposed_factor,
                N=nitrogen_per_pool * decomposed_factor,
                P=phosphorus_per_pool * decomposed_factor,
            )

    def get_eaten(
        self,
        potential_consumed_mass: float,
        predator: AnimalCohort,
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> dict[str, float]:
        """Handles predation, removing individuals and distributing biomass.

        TODO: does mechanical efficiency need to be moved? not sure

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
            self.mass_cnp.C / individual_mass
        ) * consumed_mass_after_efficiency
        consumed_nitrogen = (
            self.mass_cnp.N / individual_mass
        ) * consumed_mass_after_efficiency
        consumed_phosphorus = (
            self.mass_cnp.P / individual_mass
        ) * consumed_mass_after_efficiency

        # Convert carcass mass to stoichiometric proportions
        carcass_carbon = (self.mass_cnp.C / individual_mass) * carcass_mass_total
        carcass_nitrogen = (self.mass_cnp.N / individual_mass) * carcass_mass_total
        carcass_phosphorus = (self.mass_cnp.P / individual_mass) * carcass_mass_total

        # Remove individuals from the prey cohort
        self.individuals -= actual_individuals_killed

        # If no individuals remain, mark the cohort as dead
        if self.individuals <= 0:
            self.is_alive = False

        # Find the intersection of prey and predator territories
        intersection_carcass_pools = self.find_intersecting_carcass_pools(
            predator, carcass_pools
        )

        # Update the carcass pool with the carcass mass
        self.update_carcass_pool(
            carcass_carbon,
            carcass_nitrogen,
            carcass_phosphorus,
            intersection_carcass_pools,
        )

        return {
            "C": consumed_carbon,
            "N": consumed_nitrogen,
            "P": consumed_phosphorus,
        }

    def calculate_alpha(self) -> float:
        """Calculate search efficiency.

        This utilizes the alpha_i_k scaling function to determine the effective rate at
        which an individual herbivore searches its environment, factoring in the
        herbivore's current mass.

        TODO: update name

        Returns:
            A float representing the search efficiency rate in [ha/day].
        """

        return sf.alpha_i_k(self.constants.alpha_0_herb, self.mass_current)

    def calculate_total_handling_time_for_herbivory(
        self, plant_list: list[Resource] | list[CellResource], alpha: float
    ) -> float:
        """Calculate total handling time across all plant resources.

        Computes the denominator sum Σ K_i,l · H_i,l from the Holling Type III
        functional response,

        Args:
            plant_list: A list of plant resources available for consumption by the
                cohort.
            alpha: The search efficiency rate of the herbivore cohort.

        Returns:
            Dimensionless sum of handling time across all plant resources (days of
            handling per day of searching).
        """

        A_cell = self.grid.cell_area

        handling_time_per_gram = sf.H_i_k(
            self.constants.h_herb_0,
            self.constants.M_herb_ref,
            self.mass_current,
            self.constants.b_herb,
        )
        return handling_time_per_gram * sum(
            sf.k_i_k(alpha, plant.mass_current, A_cell) for plant in plant_list
        )

    def F_i_k(
        self,
        resource: Resource | CellResource,
        potential_biomass_consumed: float,
        total_handling_t: float,
    ) -> float:
        """Calculate the instantaneous consumption rate on a plant resource.

        Implements the Holling Type III functional response for herbivory.

        The potential biomass numerator arrives in g/day from ``k_i_k`` (native
        Madingley units), so the resource biomass divisor is converted kg -> g here
        to match; this leaves F as a clean per-day rate.

        Args:
            resource: The target plant resource being consumed.
            potential_biomass_consumed: Potential biomass eaten from the target
                resource in a day [g/day].
            total_handling_t: Pre-computed dimensionless handling time sum across
                all available resources, built once per foraging bout in
                forage_resource_list.

        Returns:
            The instantaneous consumption rate [1/day] of the target resource.
        """

        return (
            self.individuals
            * (potential_biomass_consumed / (1.0 + total_handling_t))
            / (resource.mass_current * 1000.0)  # kg -> g, matches k_i_k
        )

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

    def _mass_bin(self, prey_mass: float, theta_opt: float) -> int:
        """Calculate the predator-specific mass bin index for a prey cohort.

        Implements Equation 39 of Harfoot et al. (2014). Assigns a prey cohort
        to a discrete bin based on its log mass ratio to the predator, normalised
        by the prey preference width, offset to ensure non-negative bin indices.

        Args:
            prey_mass: Current body mass of the prey cohort in kg.
            theta_opt: This predator's optimal prey-predator mass ratio for this
                foraging encounter, drawn once per encounter in delta_mass_predation.

        Returns:
            Integer bin index for the prey cohort.

        Raises:
            ValueError: If prey_mass or self.mass_current is zero or negative, which
                would make the log ratio undefined.
        """
        if prey_mass <= 0.0:
            raise ValueError(f"prey_mass must be positive, got {prey_mass}.")
        if self.mass_current <= 0.0:
            raise ValueError(
                f"Predator mass_current must be positive, got {self.mass_current}."
            )

        return round(
            (log(prey_mass / self.mass_current) - theta_opt)
            / (0.5 * self.constants.sigma_opt_pred_prey)
            + 2 * self.constants.N_sigma_opt_pred_prey
        )

    def _build_prey_bin_densities(
        self,
        animal_list: list[AnimalCohort],
        theta_opt: float,
    ) -> dict[int, float]:
        """Build a mapping of mass bin index to cumulative prey density.

        Pre-computes the per-bin prey density (Madingley Theta_i,j) for all bins
        represented in animal_list in a single pass. The density is returned in
        native Madingley units (individuals/ha): cell area is converted from m^2 to
        hectares here, at the point the density is formed, so that k_i_j can combine
        it with an ha/day search rate and an ha territory intersection consistently.

        Args:
            animal_list: Prey cohorts available to this predator.
            theta_opt: This predator's optimal prey-predator mass ratio for this
                foraging encounter, drawn once per encounter in delta_mass_predation.

        Returns:
            Dict mapping each occupied bin index to the cumulative prey density
            (sum of individuals / cell_area, in individuals/ha) for all prey cohorts
            assigned to that bin.
        """
        A_cell_ha = self.grid.cell_area / 10000.0  # m^2 -> ha, native theta unit
        bin_densities: dict[int, float] = {}

        for cohort in animal_list:
            b = self._mass_bin(cohort.mass_current, theta_opt)
            bin_densities[b] = (
                bin_densities.get(b, 0.0) + cohort.individuals / A_cell_ha
            )

        return bin_densities

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
        self, alpha: float, n_prey: float, theta_i_j: float, intersection_area: float
    ) -> float:
        """Calculate the potential number of prey consumed.

        Args:
            alpha: The predation search rate in ha/day.
            n_prey: The number of prey individuals.
            theta_i_j: The cumulative density of organisms with a mass lying within the
                same predator specific mass bin.
            intersection_area: The overlapping area between predator and prey
              territories in m2.

        Returns:
            The potential number of prey items consumed.
        """
        return sf.k_i_j(alpha, n_prey, intersection_area, theta_i_j)

    def calculate_total_handling_time_for_predation(
        self,
        animal_list: list[AnimalCohort],
        theta_opt: float,
        bin_densities: dict[int, float],
        intersection_areas: dict[int, float],
    ) -> float:
        """Calculate the total handling time term for the predation functional response.

        Computes the denominator sum ∑(K_i,m · H_i,m) from Equations 28/29 of
        Harfoot et al. (2014), which represents the total time in days, per day
        spent searching, that would be taken to handle all potential prey items
        across all prey cohorts. This is dimensionless (days of handling per day
        of searching) and forms the saturation term in the Holling Type III
        denominator: 1 + ∑(K_i,m · H_i,m).

        Args:
            animal_list: All prey cohorts available to the predator.
            theta_opt: The predator's optimum prey-predator mass ratio for this
                encounter, drawn once per encounter in delta_mass_predation.
            bin_densities: Pre-computed mapping of mass bin index to cumulative
                prey density, built once per encounter by _build_prey_bin_densities.
            intersection_areas: Pre-computed mapping of prey cohort id to territory
                intersection area in m², built once per encounter in
                delta_mass_predation.

        Returns:
            Dimensionless sum of handling time across all prey cohorts (days of
            handling per day of searching).
        """
        return sum(
            sf.H_i_j(
                self.constants.h_pred_0,
                self.constants.M_pred_ref,
                self.mass_current,
                self.constants.b_pred,
                prey.mass_current,
            )
            * sf.k_i_j(
                sf.alpha_i_j(
                    self.constants.alpha_0_pred,
                    self.mass_current,
                    sf.w_bar_i_j(
                        self.mass_current,
                        prey.mass_current,
                        theta_opt,
                        self.constants.sigma_opt_pred_prey,
                    ),
                ),
                prey.individuals,
                intersection_areas[id(prey)],
                bin_densities.get(self._mass_bin(prey.mass_current, theta_opt), 0.0),
            )
            for prey in animal_list
        )

    def F_i_j_individual(
        self,
        target_cohort: AnimalCohort,
        intersection_area: float,
        theta_opt: float,
        bin_densities: dict[int, float],
        total_handling_time: float,
    ) -> float:
        """Method to determine instantaneous predation rate on cohort j.

        Implements the Holling type III functional response for predation. All
        encounter-level quantities (theta_opt, bin_densities, total_handling_time)
        are pre-computed once per encounter in delta_mass_predation and passed in
        to avoid redundant recomputation across prey.

        Args:
            target_cohort: The prey cohort from which mass will be consumed.
            intersection_area: Pre-computed overlap area between predator and target
                territories in m2.
            theta_opt: This predator's optimal prey-predator mass ratio, drawn once
                per encounter in delta_mass_predation.
            bin_densities: Pre-computed mapping of mass bin index to cumulative prey
                density, built once per encounter by _build_prey_bin_densities.
            total_handling_time: Pre-computed Holling type III denominator sum
                ∑(K_i,m · H_i,m), built once per encounter in delta_mass_predation.

        Returns:
            Float fraction of target cohort consumed per day.
        """
        N_target = target_cohort.individuals
        if N_target <= 0:
            return 0.0

        w_bar = sf.w_bar_i_j(
            self.mass_current,
            target_cohort.mass_current,
            theta_opt,
            self.constants.sigma_opt_pred_prey,
        )
        alpha = self.calculate_predation_search_rate(w_bar)
        target_bin = self._mass_bin(target_cohort.mass_current, theta_opt)
        theta = bin_densities.get(target_bin, 0.0)
        k_target = self.calculate_potential_prey_consumed(
            alpha, N_target, theta, intersection_area
        )
        return (
            self.individuals * (k_target / (1 + total_handling_time)) * (1 / N_target)
        )

    def calculate_consumed_mass_predation(
        self,
        target_cohort: AnimalCohort,
        adjusted_dt: timedelta64,
        intersection_area: float,
        theta_opt: float,
        bin_densities: dict[int, float],
        total_handling_time: float,
    ) -> float:
        """Calculates the mass to be consumed from a prey cohort by the predator.

        This method utilizes the F_i_j_individual method to determine the rate at
        which the target cohort is consumed, and then calculates the actual mass to
        be consumed based on this rate and other model parameters.

        Args:
            target_cohort: The prey cohort from which mass will be consumed.
            adjusted_dt: The amount of time (D) in the time-step available for foraging.
            intersection_area: Pre-computed overlap area between predator and target
                territories in m2.
            theta_opt: This predator's optimal prey-predator mass ratio, drawn once
                per encounter in delta_mass_predation.
            bin_densities: Pre-computed mapping of mass bin index to cumulative prey
                density, built once per encounter by _build_prey_bin_densities.
            total_handling_time: Pre-computed Holling type III denominator sum
                ∑(K_i,m · H_i,m), built once per encounter in delta_mass_predation.

        Returns:
            The mass to be consumed from the target cohort by the predator (in kg).
        """
        F = self.F_i_j_individual(
            target_cohort,
            intersection_area,
            theta_opt,
            bin_densities,
            total_handling_time,
        )
        return (
            target_cohort.mass_current
            * target_cohort.individuals
            * (1 - exp(-(F * float(adjusted_dt / timedelta64(1, "D")))))
        )

    def delta_mass_predation(
        self,
        animal_list: list[AnimalCohort],
        carcass_pools: dict[int, list[CarcassPool]],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handles mass assimilation from predation.

        This is Madingley's delta_assimilation_mass_predation.

        Pre-computes territory intersections, draws theta_opt once, and builds
        the prey bin density dict.

        Args:
            animal_list: A list of animal cohorts that can be consumed by the predator.
            carcass_pools: The pools to which animal carcasses are delivered.
            adjusted_dt: The amount of time (D) in the time-step available for foraging.

        Returns:
            A dictionary representing the total change in mass (C, N, P) experienced by
            the predator: {"C": value, "N": value, "P": value}.

        Raises:
            ValueError: If `animal_list` or `carcass_pools` is None.
            ValueError: If `prey_cohort.get_eaten()` returns None.
            ValueError: If `self.calculate_consumed_mass_predation()` returns None.
        """
        if animal_list is None:
            raise ValueError("animal_list cannot be None.")
        if carcass_pools is None:
            raise ValueError("carcass_pools cannot be None.")

        if not animal_list:
            return {"C": 0.0, "N": 0.0, "P": 0.0}

        # Pre-compute once per encounter
        theta_opt = self.calculate_theta_opt_i()
        intersection_areas = {
            id(prey): self.get_territory_intersection(prey)[1] for prey in animal_list
        }
        bin_densities = self._build_prey_bin_densities(animal_list, theta_opt)
        total_handling_time = self.calculate_total_handling_time_for_predation(
            animal_list, theta_opt, bin_densities, intersection_areas
        )

        total_consumed_mass = {"C": 0.0, "N": 0.0, "P": 0.0}

        for prey_cohort in animal_list:
            intersection_area = intersection_areas[id(prey_cohort)]

            if intersection_area == 0.0:
                continue

            consumed_mass = self.calculate_consumed_mass_predation(
                prey_cohort,
                adjusted_dt,
                intersection_area,
                theta_opt,
                bin_densities,
                total_handling_time,
            )

            if consumed_mass is None:
                raise ValueError(
                    f"calculate_consumed_mass_predation() returned None for"
                    f"{prey_cohort}."
                )

            actual_consumed_cnp = prey_cohort.get_eaten(
                consumed_mass, self, carcass_pools
            )

            if actual_consumed_cnp is None:
                raise ValueError(f"get_eaten() returned None for {prey_cohort}.")

            self.record_trophic_transfer(
                ("cohort", str(prey_cohort.id)),
                CNP.from_dict(actual_consumed_cnp),
            )

            for element in total_consumed_mass:
                total_consumed_mass[element] += actual_consumed_cnp[element]

        return total_consumed_mass

    def forage_resource_list(
        self,
        resources: list[Resource] | list[CellResource],
        adjusted_dt: timedelta64,
        resource_kind: str,
        herbivory_waste_pools: dict[int, HerbivoryWaste] | None = None,
    ) -> dict[str, float]:
        """Generic foraging function for all non-predation resources.

        Implements a Holling Type III functional response over a list of resources.
        Cohort-level quantities (search efficiency and total handling time) are
        precomputed once per foraging bout before the resource loop.

        Elemental mass values returned by ``get_eaten`` are clamped to remove
        floating point noise before being passed to downstream validators. Values
        more negative than ``_ELEMENTAL_MASS_NOISE_TOLERANCE`` are left unchanged
        and will raise in ``record_trophic_transfer`` or ``add_waste``.

        Args:
            resources: List of foragable resources.
            adjusted_dt: Time available for foraging.
            resource_kind: A string label of the resource type, used as a key in
                trophic transfer records.
            herbivory_waste_pools: Optional mapping of cell_id to waste pool for
                unassimilated biomass. If None, mechanical losses are discarded.

        Returns:
            Stoichiometric mass gained by the cohort (kg of C, N, P).
        """
        total_gain = {"C": 0.0, "N": 0.0, "P": 0.0}

        if not resources:
            return total_gain

        # Precompute cohort-level quantities — invariant across the resource loop.
        alpha = self.calculate_alpha()
        total_handling_t = self.calculate_total_handling_time_for_herbivory(
            resources, alpha
        )
        A_cell = self.grid.cell_area
        dt_days = float(adjusted_dt / timedelta64(1, "D"))
        conv_eff = self.functional_group.conversion_efficiency

        for resource in resources:
            # Holling Type III: potential biomass eaten from this resource per day.
            potential_biomass_consumed = sf.k_i_k(alpha, resource.mass_current, A_cell)
            # Instantaneous consumption rate [1/day] for this resource.
            F = self.F_i_k(resource, potential_biomass_consumed, total_handling_t)
            # Exponential depletion integral: total biomass consumed over dt days when
            # consuming a fraction F of remaining stock per day. Approaches F*B*dt for
            # small F*dt (linear regime) and B for large F*dt (full depletion).
            requested = resource.mass_current * (1.0 - exp(-F * dt_days))

            gain_cnp, litter_cnp = resource.get_eaten(requested, self)

            # Clamp floating point noise before passing to downstream validators.
            gain_cnp = self._clamp_cnp_noise(gain_cnp)
            litter_cnp = self._clamp_cnp_noise(litter_cnp)

            self.record_trophic_transfer(
                (resource_kind, str(resource.cell_id)),
                CNP.from_dict(gain_cnp),
            )

            for elem in total_gain:
                total_gain[elem] += gain_cnp[elem] * conv_eff

            if herbivory_waste_pools and litter_cnp:
                herbivory_waste_pools[resource.cell_id].add_waste(litter_cnp)

        return total_gain

    def delta_mass_herbivory(
        self,
        plant_list: list[CellResource],
        adjusted_dt: timedelta64,
        herbivory_waste_pools: dict[int, HerbivoryWaste],
    ) -> dict[str, float]:
        """Handle mass assimilation from live plant herbivory.

        Args:
            plant_list: List of live plant resources.
            adjusted_dt: Time available for foraging.
            herbivory_waste_pools: Waste pools for unassimilated plant matter.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=plant_list,
            adjusted_dt=adjusted_dt,
            herbivory_waste_pools=herbivory_waste_pools,
            resource_kind="plant_resource",
        )

    def delta_mass_detritivory(
        self,
        litter_pools: list[CellResource],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handle mass assimilation from litter (detritivory).

        Args:
            litter_pools: List of litter pools available to the cohort.
            adjusted_dt: Time available for foraging.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=litter_pools,
            adjusted_dt=adjusted_dt,
            resource_kind="litter_pool",
        )

    def delta_mass_carcass_scavenging(
        self,
        carcass_pools: list[Resource],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handle mass assimilation from carcass scavenging.

        Args:
            carcass_pools: List of carcass pools available to the cohort.
            adjusted_dt: Time available for foraging.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=carcass_pools,
            adjusted_dt=adjusted_dt,
            resource_kind="carcass_pool",
        )

    def delta_mass_excrement_scavenging(
        self,
        excrement_pools: list[Resource],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handle mass assimilation from excrement (coprophagy).

        Args:
            excrement_pools: List of excrement pools available to the cohort.
            adjusted_dt: Time available for foraging.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=excrement_pools,
            adjusted_dt=adjusted_dt,
            resource_kind="excrement_pool",
        )

    def delta_mass_fruiting_fungivory(
        self,
        fungal_fruit_list: list[Resource],
        adjusted_dt: timedelta64,
        herbivory_waste_pools: dict[int, HerbivoryWaste],
    ) -> dict[str, float]:
        """Handle mass assimilation from fruiting body (mushroom) fungivory.

        Args:
            fungal_fruit_list: List of fungal fruiting resources.
            adjusted_dt: Time available for foraging.
            herbivory_waste_pools: Waste pools for unassimilated fungal matter.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=fungal_fruit_list,
            adjusted_dt=adjusted_dt,
            herbivory_waste_pools=herbivory_waste_pools,
            resource_kind="fungal_fruit_pool",
        )

    def delta_mass_soil_fungivory(
        self,
        soil_fungi_list: list[Resource],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handle mass assimilation from soil fungi foraging.

        Args:
            soil_fungi_list: List of soil fungi resources (distinct from fruiting
                bodies).
            adjusted_dt: Time available for foraging.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=soil_fungi_list,
            adjusted_dt=adjusted_dt,
            resource_kind="soil_fungi_pool",
        )

    def delta_mass_pomivory(
        self,
        pom_list: list[Resource],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handle mass assimilation from POM (particulate organic matter) foraging.

        Args:
            pom_list: List of particulate organic matter soil resources.
            adjusted_dt: Time available for foraging.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=pom_list,
            adjusted_dt=adjusted_dt,
            resource_kind="pom_pool",
        )

    def delta_mass_bacteriophagy(
        self,
        bacteria_list: list[Resource],
        adjusted_dt: timedelta64,
    ) -> dict[str, float]:
        """Handle mass assimilation from soil bacteria.

        Args:
            bacteria_list: List of soil bacteria resources.
            adjusted_dt: Time available for foraging.

        Returns:
            Stoichiometric mass gained by the cohort.
        """
        return self.forage_resource_list(
            resources=bacteria_list,
            adjusted_dt=adjusted_dt,
            resource_kind="bacteria_pool",
        )

    def forage_cohort(
        self,
        array_resource_list: list[CellResource],
        animal_list: list[AnimalCohort],
        fungal_fruit_list: list[Resource],
        soil_fungi_list: list[Resource],
        pom_list: list[Resource],
        bacteria_list: list[Resource],
        excrement_pools: list[ExcrementPool],
        carcass_pool_map: dict[int, list[CarcassPool]],
        scavenge_carcass_pools: list[Resource],
        scavenge_excrement_pools: list[Resource],
        herbivory_waste_pools: dict[int, HerbivoryWaste],
        dt: timedelta64,
    ) -> None:
        """Coordinate all resource consumption for a single cohort.

        This wrapper collects every resource class the cohort can exploit
        (plants, prey, litter, carcasses, excrement) and calls the
        specialised *delta_mass_* helpers.  It also passes the full
        deposition pools (`excrement_pools`, `carcass_pool_map`) so that
        waste and carcass remains are always routed correctly, even if the
        cohort is not actively scavenging.

        Args:
            array_resource_list: Full set of resources available through the array
                resources interface, at present this consists of the living plants and
                dead plant detritus (litter).
            animal_list: Live prey cohorts available for predation.
            fungal_fruit_list: Live fungal fruiting bodies available for consumption.
            soil_fungi_list: Soil fungi pools (not fruiting bodies).
            pom_list: Soil particulate organic matter pools (POM).
            bacteria_list: Soil bacteria pools.
            excrement_pools: ExcrementPool objects used for defecation
                deposition.
            carcass_pool_map: Mapping ``cell_id → list[CarcassPool]`` that
                receives carcass remains created during predation.
            scavenge_carcass_pools: Subset of `CarcassPool` objects in the
                territory from which the cohort will attempt to scavenge.
            scavenge_excrement_pools: Subset of `ExcrementPool` objects in
                the territory that the cohort will consume via coprophagy.
            herbivory_waste_pools: Mapping ``cell_id → HerbivoryWaste`` for
                litter generated by partial plant consumption.
            dt: Time (D) in the time step.


        """
        if self.individuals == 0:
            LOGGER.warning("No individuals in cohort to forage.")
            return

        if self.mass_current == 0:
            LOGGER.warning("No mass left in cohort to forage.")
            return

        # TODO - TEMPORARY SOLUTION THAT TARAN SHOULD IMPROVE UPON
        # Split array resources between herbivory and detritivory
        herbivore_diets = [
            DietType.ALGAE,
            DietType.FLOWERS,
            DietType.FOLIAGE,
            DietType.FRUIT,
            DietType.SEEDS,
            DietType.NECTAR,
            DietType.WOOD,
        ]
        plant_list = [
            resource
            for resource in array_resource_list
            if resource.resource.diet_type in herbivore_diets
        ]
        litter_pools = [
            resource
            for resource in array_resource_list
            if resource.resource.diet_type == DietType.DETRITUS
        ]

        # Compute foraging time proportionally across diet types
        time_available_per_diet = (
            dt * self.constants.tau_f * self.sigma_f_t / self.diet_category_count
        )

        total_gain = {"C": 0.0, "N": 0.0, "P": 0.0}

        # live plant herbivory
        if plant_list:
            gain = self.delta_mass_herbivory(
                plant_list=plant_list,
                adjusted_dt=time_available_per_diet,
                herbivory_waste_pools=herbivory_waste_pools,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # live prey predation (adds carcasses to map)
        if animal_list:
            gain = self.delta_mass_predation(
                animal_list=animal_list,
                carcass_pools=carcass_pool_map,
                adjusted_dt=time_available_per_diet,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # live mushroom fungivory
        if fungal_fruit_list:
            gain = self.delta_mass_fruiting_fungivory(
                fungal_fruit_list=fungal_fruit_list,
                adjusted_dt=time_available_per_diet,
                herbivory_waste_pools=herbivory_waste_pools,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # soil fungi fungivory
        if soil_fungi_list:
            gain = self.delta_mass_soil_fungivory(
                soil_fungi_list=soil_fungi_list,
                adjusted_dt=time_available_per_diet,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # particulate organic matter consumption
        if pom_list:
            gain = self.delta_mass_pomivory(
                pom_list=pom_list,
                adjusted_dt=time_available_per_diet,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # bacteria foraging
        if bacteria_list:
            gain = self.delta_mass_bacteriophagy(
                bacteria_list=bacteria_list,
                adjusted_dt=time_available_per_diet,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # litter detritivory
        if litter_pools:
            gain = self.delta_mass_detritivory(
                litter_pools=litter_pools,
                adjusted_dt=time_available_per_diet,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # carcass scavenging
        if scavenge_carcass_pools or scavenge_excrement_pools:
            gain = self.delta_mass_carcass_scavenging(
                carcass_pools=scavenge_carcass_pools,
                adjusted_dt=time_available_per_diet,
            )

            for k in total_gain:
                total_gain[k] += gain[k]

        # waste scavenging
        if scavenge_carcass_pools or scavenge_excrement_pools:
            gain = self.delta_mass_excrement_scavenging(
                excrement_pools=scavenge_excrement_pools,
                adjusted_dt=time_available_per_diet,
            )
            for k in total_gain:
                total_gain[k] += gain[k]

        # -- assimilate & deposit wastes
        if any(v > 0 for v in total_gain.values()):
            self.eat(total_gain, excrement_pools)

    def eat(
        self, mass_consumed: dict[str, float], excrement_pools: list[ExcrementPool]
    ) -> None:
        """Handles the mass gain from consuming food and processes waste.

        This method updates the consumer's mass based on the amount of food consumed
        in stoichiometric terms. It also handles waste by calling `defecate` with any
        excess nutrients after growth.

        Args:
            mass_consumed: A dictionary representing the mass of each nutrient consumed
                by this consumer: {"C": value, "N": value,
                "P": value}.
            excrement_pools: The ExcrementPool objects in the cohort's territory in
                which waste is deposited.

        Raises:
            ValueError: If `mass_consumed` contains negative values or missing keys.
            ValueError: If no excrement pools are provided.
        """
        if self.individuals == 0:
            return

        # Validate mass_consumed input
        required_keys = {"C", "N", "P"}
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

        Following Madingley's assumption that the probability of juvenile dispersal is
        equal to the proportion of the cohort individuals that would arrive in the
        neighboring cell after one full timestep's movement.

        Assuming cohort individuals are homogeneously distributed within a grid cell and
        that the move is non-diagonal, the probability is then equal to the ratio of
        dispersal speed to the side-length of a grid cell.

        A homogeneously distributed cohort with a partial presence in a grid cell will
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

        A_cell = self.grid.cell_area
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

        The number of deaths is drawn from a binomial distribution with trial size
        ``pop_size`` and per-individual death probability ``1 - exp(-u_t * dt)`` where
        ``u_t`` is the sum of background, senescence, and starvation mortality rates.

        Args:
            dt: The time passed in the timestep (days).
            carcass_pools: The local carcass pool to which dead individuals go.

        """

        pop_size = self.individuals
        mass_current = self.mass_current

        t_to_maturity = self.time_to_maturity
        t_since_maturity = self.time_since_maturity
        mass_max = self.largest_mass_achieved  # growth to adult_mass

        u_bg = sf.background_mortality(
            self.constants.u_bg
        )  # constant background mortality

        u_se = 0.0
        if self.is_mature:
            u_se = sf.senescence_mortality(
                self.constants.lambda_se, t_to_maturity, t_since_maturity
            )  # senescence mortality only experienced by mature adults

        u_st = sf.starvation_mortality(
            self.constants.lambda_max,
            self.constants.J_st,
            self.constants.zeta_st,
            mass_current,
            mass_max,
        )  # starvation mortality
        u_t = u_bg + u_se + u_st

        # Calculate the total number of dead individuals w/ binomial draw
        number_dead = binomial(n=pop_size, p=1 - exp(-u_t * dt))

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
        prey_diet: DietType,
    ) -> list[AnimalCohort]:
        """Collect suitable prey cohorts within the cohort's territory.

        This method filters candidate prey by:
        1) Spatial overlap (cohort territory),
        2) Predation feasibility (`can_prey_on`),
        3) Taxonomic category requested by `prey_diet` flags

        Args:
            communities: Dictionary mapping cell IDs to lists of animal cohorts.
            prey_diet: Diet flags specifying which prey categories are allowed, e.g.
                `DietType.VERTEBRATES`, `DietType.INVERTEBRATES`, or both.

        Returns:
            List of animal cohorts that can be preyed upon.
        """
        allows_invertebrates = bool(prey_diet & DietType.INVERTEBRATES)
        allows_vertebrates = bool(prey_diet & DietType.VERTEBRATES)

        prey_set: set[AnimalCohort] = set()
        for cell_id in self.territory:
            for prey_cohort in communities[cell_id]:
                if not self.can_prey_on(prey_cohort):
                    continue

                prey_group = prey_cohort.functional_group
                if (allows_invertebrates and prey_group.is_invertebrate) or (
                    allows_vertebrates and prey_group.is_vertebrate
                ):
                    prey_set.add(prey_cohort)

        return list(prey_set)

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

    def _get_resources_in_territory(
        self,
        resource_map: Mapping[int, _T | list[_T]],
        filter_fn: Callable[[_T], bool] | None = None,
    ) -> list[_T]:
        """Return resources from territory; accepts singleton or list per cell.

        This normalizes each per-cell entry to a list, applies an optional filter,
        and flattens the result.

        Args:
            resource_map: Mapping from cell_id to a single resource or a list.
            filter_fn: Optional predicate to retain resources (True keeps item).

        Returns:
            A flat list of resources located within the cohort's territory.
        """
        # Collect results from all territory cells
        result: list[_T] = []

        for cell_id in self.territory:
            entry = resource_map.get(cell_id)
            if entry is None:
                continue

            # Normalize to a list
            items = entry if isinstance(entry, list) else [entry]

            # Apply optional filter
            if filter_fn is not None:
                items = [r for r in items if filter_fn(r)]

            result.extend(items)

        return result

    def get_array_resources(
        self, array_resources: list[ResourcePool]
    ) -> list[CellResource]:
        """Return array resources accessible within this cohort's territory.

        This method filters the array resources by territory and the cohort's
        foraging capability (via `can_forage_on`).

        Args:
            array_resources: A list of ResourcePool instances.

        Returns:
            A list of CellResource objects that the cohort can forage on.
        """

        available_cell_array_resources: list[CellResource] = []

        # Loop over the array resources
        for resource in array_resources:
            # If the resource is forage-able, extend the list of resources with the
            # resource for every cell in the territory.
            if resource.is_forageable(
                diet=self.functional_group.diet,
                vertical_occupancy=self.functional_group.vertical_occupancy,
            ):
                available_cell_array_resources.extend(
                    [resource[cell_id] for cell_id in self.territory]
                )

        return available_cell_array_resources

    def get_plant_resources(
        self, plant_resources: dict[int, list[Resource]]
    ) -> list[Resource]:
        """Return plant resources accessible within this cohort's territory.

        This method filters the plant resources by territory and the cohort's
        foraging capability (via `can_forage_on`).

        Args:
            plant_resources: A dictionary mapping cell IDs to lists of plant
                resource objects.

        Returns:
            A list of plant Resource objects that the cohort can forage on.
        """
        return self._get_resources_in_territory(plant_resources, self.can_forage_on)

    def get_excrement_pools(
        self, excrement_pools: dict[int, list[ExcrementPool]]
    ) -> list[ExcrementPool]:
        """Return excrement pools within the cohort's territory.

        This method returns all ExcrementPool objects that are located in grid
        cells occupied by the cohort.

        Args:
            excrement_pools: A dictionary mapping cell IDs to lists of ExcrementPool
                objects.

        Returns:
            A list of ExcrementPool objects in the cohort's territory.
        """
        return self._get_resources_in_territory(excrement_pools)

    def get_carcass_pools(
        self, carcass_pools: dict[int, list[CarcassPool]]
    ) -> list[CarcassPool]:
        """Return carcass pools within the cohort's territory.

        This method returns all CarcassPool objects located in grid cells
        that the cohort occupies.

        Args:
            carcass_pools: A dictionary mapping cell IDs to lists of CarcassPool
                objects.

        Returns:
            A list of CarcassPool objects in the cohort's territory.
        """
        return self._get_resources_in_territory(carcass_pools)

    def get_fungal_fruit_pools(
        self, fungal_fruiting_bodies: dict[int, FungalFruitPool]
    ) -> list[Resource]:
        """Return fungal fruiting-body pools within the cohort's territory.

        Args:
            fungal_fruiting_bodies: The fungal fruiting pools the model.

        Returns:
            A list of fungal fruiting-body Resource objects available in
            the cohort's territory.
        """

        fungal_fruits = self._get_resources_in_territory(
            fungal_fruiting_bodies, self.can_forage_on
        )
        return cast(list[Resource], fungal_fruits)

    def get_soil_fungi_pools(
        self, soil_pools: dict[int, dict[str, SoilPool]]
    ) -> list[Resource]:
        """Return soil fungi pools within the cohort's territory.

        Args:
            soil_pools: Mapping from cell_id to SoilPool objects keyed by 'fungi',
                'pom', and 'bacteria'.

        Returns:
            List of soil-fungi Resource objects within the territory.
        """
        fungi_by_cell: dict[int, SoilPool] = {
            cid: pools["fungi"] for cid, pools in soil_pools.items() if "fungi" in pools
        }
        pools_list = self._get_resources_in_territory(fungi_by_cell, self.can_forage_on)
        return cast(list[Resource], pools_list)

    def get_pom_pools(
        self, soil_pools: dict[int, dict[str, SoilPool]]
    ) -> list[Resource]:
        """Return soil POM pools within the cohort's territory.

        Args:
            soil_pools: Mapping from cell_id to SoilPool objects keyed by 'fungi',
                'pom', and 'bacteria'.

        Returns:
            List of POM Resource objects within the territory.
        """
        pom_by_cell: dict[int, SoilPool] = {
            cid: pools["pom"] for cid, pools in soil_pools.items() if "pom" in pools
        }
        pools_list = self._get_resources_in_territory(pom_by_cell, self.can_forage_on)
        return cast(list[Resource], pools_list)

    def get_bacteria_pools(
        self, soil_pools: dict[int, dict[str, SoilPool]]
    ) -> list[Resource]:
        """Return soil bacteria pools within the cohort's territory.

        Args:
            soil_pools: Mapping from cell_id to SoilPool objects keyed by 'fungi',
                'pom', and 'bacteria'.

        Returns:
            List of bacterial Resource objects within the territory.
        """
        bacteria_by_cell: dict[int, SoilPool] = {
            cid: pools["bacteria"]
            for cid, pools in soil_pools.items()
            if "bacteria" in pools
        }
        pools_list = self._get_resources_in_territory(
            bacteria_by_cell, self.can_forage_on
        )
        return cast(list[Resource], pools_list)

    def get_territory_intersection(
        self, other_cohort: AnimalCohort
    ) -> tuple[set[int], float]:
        """Find the overlapping cells and area between this cohort and another cohort.

        Args:
            other_cohort: The prey cohort to find the territorial overlap with.

        Returns:
            A tuple of the set of overlapping cell IDs and the total intersection
            area in m2.
        """
        intersection_cells = set(self.territory) & set(other_cohort.territory)
        intersection_area = len(intersection_cells) * self.grid.cell_area
        return intersection_cells, intersection_area

    def find_intersecting_carcass_pools(
        self,
        other_cohort: AnimalCohort,
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> list[CarcassPool]:
        """Find the carcass pools in the territorial overlap with another cohort.

        Args:
            other_cohort: The other cohort to find the territorial intersection with.
            carcass_pools: A dictionary mapping cell IDs to CarcassPool objects.

        Returns:
            A list of CarcassPools in the intersecting grid cells.
        """
        intersection_cells, _ = self.get_territory_intersection(other_cohort)
        return [
            pool for cell_id in intersection_cells for pool in carcass_pools[cell_id]
        ]

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

    def update_activity_window(
        self,
        temperature: float,
        diurnal_temp_range: float,
        annual_mean_temp: float,
        annual_temp_sd: float,
    ) -> None:
        """Update the activity window fraction and current temperature.

        Delegates to
        :func:`~virtual_ecosystem.models.animal.scaling_functions.activity_window`
        and stores the result in :attr:`sigma_f_t`. Should be called once per
        timestep, before both :meth:`forage_cohort` and :meth:`metabolize`.

        If the cohort's functional group has ``t_opt``, ``t_max_crit``, and
        ``t_min_crit`` set from CSV input, those values are used directly.
        Otherwise the toy climate parameters from
        :attr:`~virtual_ecosystem.models.animal.model_config.AnimalConstants`
        are used to derive thermal tolerances.

        Args:
            temperature: Monthly mean ambient temperature [°C].
            diurnal_temp_range: Monthly mean diurnal temperature range [°C].
            annual_mean_temp: Annual mean ambient temperature [°C].
            annual_temp_sd: Standard deviation of monthly temperatures across the
                climatological year [°C].
        """
        self.current_temperature = temperature
        self.sigma_f_t = sf.activity_window(
            metabolic_type=self.functional_group.metabolic_type,
            temperature=temperature,
            diurnal_temp_range=diurnal_temp_range,
            annual_mean_temp=annual_mean_temp,
            annual_temp_sd=annual_temp_sd,
            t_opt=self.functional_group.t_opt,
            t_max_crit=self.functional_group.t_max_crit,
            t_min_crit=self.functional_group.t_min_crit,
            constants=self.constants,
        )

    def get_stratum_climate(
        self,
        cell_id: int,
        canopy_temperature: NDArray,
        ground_temperature: NDArray,
        soil_temperature: NDArray,
        canopy_diurnal_range: NDArray,
        ground_diurnal_range: NDArray,
        soil_diurnal_range: NDArray,
    ) -> tuple[float, float]:
        """Mean temperature and diurnal range experienced by this cohort in a cell.

        Averages both climate variables across all occupied vertical strata. The
        arrays should be pre-computed per-cell means for each stratum before calling
        — see
        :meth:`~virtual_ecosystem.models.animal.animal_model.AnimalModel.update_activity_windows_community`.

        The stratum-to-array mapping is:

        * ``CANOPY`` — mean of filled canopy layer values, one value per cell.
        * ``GROUND`` — surface layer value, one value per cell.
        * ``SOIL``   — topsoil layer value, one value per cell.

        Args:
            cell_id: Index of the grid cell to evaluate.
            canopy_temperature: 1-D array of per-cell mean filled canopy
                temperatures [°C], shape ``(n_cells,)``.
            ground_temperature: 1-D array of surface air temperatures [°C],
                shape ``(n_cells,)``.
            soil_temperature: 1-D array of topsoil temperatures [°C],
                shape ``(n_cells,)``.
            canopy_diurnal_range: 1-D array of per-cell mean filled canopy diurnal
                temperature ranges [°C], shape ``(n_cells,)``.
            ground_diurnal_range: 1-D array of surface diurnal temperature ranges
                [°C], shape ``(n_cells,)``.
            soil_diurnal_range: 1-D array of topsoil diurnal temperature ranges
                [°C], shape ``(n_cells,)``.

        Returns:
            A tuple of (temperature, diurnal_range), each the mean across all
            occupied strata for the given cell [°C].

        Raises:
            ValueError: If the cohort's vertical occupancy contains no recognised
                flags.
        """
        stratum_temps: list[float] = []
        stratum_diurnal: list[float] = []

        if self.functional_group.vertical_occupancy & VerticalOccupancy.CANOPY:
            stratum_temps.append(float(canopy_temperature[cell_id]))
            stratum_diurnal.append(float(canopy_diurnal_range[cell_id]))

        if self.functional_group.vertical_occupancy & VerticalOccupancy.GROUND:
            stratum_temps.append(float(ground_temperature[cell_id]))
            stratum_diurnal.append(float(ground_diurnal_range[cell_id]))

        if self.functional_group.vertical_occupancy & VerticalOccupancy.SOIL:
            stratum_temps.append(float(soil_temperature[cell_id]))
            stratum_diurnal.append(float(soil_diurnal_range[cell_id]))

        if not stratum_temps:
            raise ValueError(
                f"No recognised vertical occupancy flags in: "
                f"{self.functional_group.vertical_occupancy}"
            )

        return float(mean(stratum_temps)), float(mean(stratum_diurnal))

    def get_mean_territory_climate(
        self,
        canopy_temperature: NDArray,
        ground_temperature: NDArray,
        soil_temperature: NDArray,
        canopy_diurnal_range: NDArray,
        ground_diurnal_range: NDArray,
        soil_diurnal_range: NDArray,
    ) -> tuple[float, float]:
        """Mean temperature and diurnal range across this cohort's full territory.

        Calls :meth:`get_stratum_climate` for each cell in the cohort's territory
        and returns the unweighted mean of both climate variables. Arrays should be
        pre-computed per-cell stratum means before calling — see
        :meth:`~virtual_ecosystem.models.animal.animal_model.AnimalModel.update_activity_windows_community`.

        Args:
            canopy_temperature: 1-D array of per-cell mean filled canopy
                temperatures [°C], shape ``(n_cells,)``.
            ground_temperature: 1-D array of surface air temperatures [°C],
                shape ``(n_cells,)``.
            soil_temperature: 1-D array of topsoil temperatures [°C],
                shape ``(n_cells,)``.
            canopy_diurnal_range: 1-D array of per-cell mean filled canopy diurnal
                temperature ranges [°C], shape ``(n_cells,)``.
            ground_diurnal_range: 1-D array of surface diurnal temperature ranges
                [°C], shape ``(n_cells,)``.
            soil_diurnal_range: 1-D array of topsoil diurnal temperature ranges
                [°C], shape ``(n_cells,)``.

        Returns:
            A tuple of (temperature, diurnal_range), each the mean across all
            territory cells and occupied strata [°C].
        """
        cell_climates = [
            self.get_stratum_climate(
                c,
                canopy_temperature,
                ground_temperature,
                soil_temperature,
                canopy_diurnal_range,
                ground_diurnal_range,
                soil_diurnal_range,
            )
            for c in self.territory
        ]

        mean_temperature = float(mean([t for t, _ in cell_climates]))
        mean_diurnal_range = float(mean([d for _, d in cell_climates]))

        return mean_temperature, mean_diurnal_range
