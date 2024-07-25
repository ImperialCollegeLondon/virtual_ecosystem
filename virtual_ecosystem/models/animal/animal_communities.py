"""The ''animal'' module provides animal module functionality."""

from __future__ import annotations

import importlib
import random
from collections.abc import Callable, Iterable, MutableSequence, Sequence
from itertools import chain
from math import ceil

from numpy import timedelta64

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
from virtual_ecosystem.models.animal.animal_traits import DevelopmentType
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.decay import CarcassPool, ExcrementPool
from virtual_ecosystem.models.animal.functional_group import (
    FunctionalGroup,
    get_functional_group_by_name,
)
from virtual_ecosystem.models.animal.plant_resources import PlantResources
from virtual_ecosystem.models.animal.protocols import (
    Consumer,
    DecayPool,
    Resource,
    Territory,
)
from virtual_ecosystem.models.animal.scaling_functions import damuths_law


class AnimalCommunity:
    """This is a class for the animal community of a grid cell.

    This class manages the animal cohorts present in a grid cell and provides methods
    that need to loop over all cohorts, move cohorts to new grids, or manage an
    interaction between two cohorts.

    Args:
        functional_groups: A list of FunctionalGroup objects
        data: The core data object
        community_key: The integer key of the cell id for this community
        neighbouring_keys: A list of cell id keys for neighbouring communities
        get_community_by_key: A function to return a designated AnimalCommunity by
        integer key.
    """

    def __init__(
        self,
        functional_groups: list[FunctionalGroup],
        data: Data,
        community_key: int,
        neighbouring_keys: list[int],
        get_community_by_key: Callable[[int], AnimalCommunity],
        constants: AnimalConsts = AnimalConsts(),
    ) -> None:
        # The constructor of the AnimalCommunity class.
        self.data = data
        """A reference to the core data object."""
        self.functional_groups = tuple(functional_groups)
        """A list of all FunctionalGroup types in the model."""
        self.community_key = community_key
        """Integer designation of the community in the model grid."""
        self.neighbouring_keys = neighbouring_keys
        """List of integer keys of neighbouring communities."""
        self.get_community_by_key = get_community_by_key
        """Callable get_community_by_key from AnimalModel."""
        self.constants = constants
        """Animal constants."""
        self.animal_cohorts: dict[str, list[AnimalCohort]] = {
            k.name: [] for k in self.functional_groups
        }
        """A dictionary of lists of animal cohorts keyed by functional group, containing
        only those cohorts having their territory centroid in this community."""
        self.occupancy: dict[str, dict[AnimalCohort, float]] = {
            k.name: {} for k in self.functional_groups
        }
        """A dictionary of dictionaries of animal cohorts keyed by functional group and 
        cohort, with the value being the occupancy percentage."""
        self.carcass_pool: CarcassPool = CarcassPool(10000.0, 0.0)
        """A pool for animal carcasses within the community."""
        self.excrement_pool: ExcrementPool = ExcrementPool(10000.0, 0.0)
        """A pool for excrement within the community."""
        self.plant_community: PlantResources = PlantResources(
            data=self.data,
            cell_id=self.community_key,
            constants=self.constants,
        )

    @property
    def all_animal_cohorts(self) -> Iterable[AnimalCohort]:
        """Get an iterable of all animal cohorts w/ proportion in the community.

        This property provides access to all the animal cohorts contained
        within this community class.

        Returns:
            Iterable[AnimalCohort]: An iterable of AnimalCohort objects.
        """
        return chain.from_iterable(self.animal_cohorts.values())

    @property
    def all_occupying_cohorts(self) -> Iterable[AnimalCohort]:
        """Get an iterable of all occupying cohorts w/ proportion in the community.

        This property provides access to all the animal cohorts contained
        within this community class.

        Returns:
            Iterable[AnimalCohort]: An iterable of AnimalCohort objects.
        """
        return chain.from_iterable(
            cohort_dict.keys() for cohort_dict in self.occupancy.values()
        )

    def initialize_territory(
        self,
        cohort: AnimalCohort,
        centroid_key: int,
        get_community_by_key: Callable[[int], AnimalCommunity],
    ) -> None:
        """This initializes the territory occupied by the cohort.

        TODO: update the territory size to cell number conversion using grid size
        TODO: needs test

        Args:
            cohort: The animal cohort occupying the territory.
            centroid_key: The community key anchoring the territory.
            get_community_by_key: The method for accessing animal communities by key.
        """
        AnimalTerritory = importlib.import_module(
            "virtual_ecosystem.models.animal.animal_territories"
        ).AnimalTerritory

        bfs_territory = importlib.import_module(
            "virtual_ecosystem.models.animal.animal_territories"
        ).bfs_territory

        # Each grid cell is 1 hectare, territory size in grids is the same as hectares
        target_cell_number = int(cohort.territory_size)

        # Perform BFS to determine the territory cells
        territory_cells = bfs_territory(
            centroid_key,
            target_cell_number,
            self.data.grid.cell_nx,
            self.data.grid.cell_ny,
        )

        # Generate the territory
        territory = AnimalTerritory(centroid_key, territory_cells, get_community_by_key)
        # Add the territory to the cohort's attributes
        cohort.territory = territory

        # Update the occupancy of the cohort in each community within the territory
        occupancy_percentage = 1.0 / len(territory_cells)
        for cell_key in territory_cells:
            community = get_community_by_key(cell_key)
            community.occupancy[cohort.functional_group.name][cohort] = (
                occupancy_percentage
            )

        territory.update_territory()

    def reinitialize_territory(
        self,
        cohort: AnimalCohort,
        centroid_key: int,
        get_community_by_key: Callable[[int], AnimalCommunity],
    ) -> None:
        """This initializes the territory occupied by the cohort.

        TODO: update the territory size to cell number conversion using grid size
        TODO: needs test

        Args:
            cohort: The animal cohort occupying the territory.
            centroid_key: The community key anchoring the territory.
            get_community_by_key: The method for accessing animal communities by key.
        """
        # remove existing occupancies
        cohort.territory.abandon_communities(cohort)
        # reinitialize the territory
        self.initialize_territory(cohort, centroid_key, get_community_by_key)

    def populate_community(self) -> None:
        """This function creates an instance of each functional group.

        Currently, this is the simplest implementation of populating the animal model.
        In each AnimalCommunity one AnimalCohort of each FunctionalGroup type is
        generated. So the more functional groups that are made, the denser the animal
        community will be. This function will need to be reworked dramatically later on.

        Currently, the number of individuals in a cohort is handled using Damuth's Law,
        which only holds for mammals.

        TODO: Move populate_community to following Madingley instead of damuth

        """
        for functional_group in self.functional_groups:
            individuals = damuths_law(
                functional_group.adult_mass, functional_group.damuths_law_terms
            )

            # create a cohort of the functional group
            cohort = AnimalCohort(
                functional_group,
                functional_group.adult_mass,
                0.0,
                individuals,
                DefaultTerritory(),
                self.constants,
            )
            # add the cohort to the community's list of animal cohorts @ centroid
            self.animal_cohorts[functional_group.name].append(cohort)

            # add the cohort to the community with 100% occupancy initially
            self.occupancy[functional_group.name][cohort] = 1.0

            # generate a territory for the cohort
            self.initialize_territory(
                cohort,
                self.community_key,
                self.get_community_by_key,
            )

    def migrate(self, migrant: AnimalCohort, destination: AnimalCommunity) -> None:
        """Function to move an AnimalCohort between AnimalCommunity objects.

        This function takes a cohort and a destination community, changes the
        centroid of the cohort's territory to be the new community, and then
        reinitializes the territory around the new centroid.

        TODO: travel distance should be a function of body-size or locomotion once
              multi-grid occupancy is integrated.

        Args:
            migrant: The AnimalCohort moving between AnimalCommunities.
            destination: The AnimalCommunity the cohort is moving to.

        """

        self.animal_cohorts[migrant.name].remove(migrant)
        destination.animal_cohorts[migrant.name].append(migrant)

        # Regenerate a territory for the cohort at the destination community
        destination.reinitialize_territory(
            migrant,
            destination.community_key,
            destination.get_community_by_key,
        )

    def migrate_community(self) -> None:
        """This handles migrating all cohorts with a centroid in the community.

        This migration method initiates migration for two reasons:
        1) The cohort is starving and needs to move for a chance at resource access
        2) An initial migration event immediately after birth.

        TODO: MGO - migrate distance mod for larger territories?


        """
        for cohort in self.all_animal_cohorts:
            is_starving = cohort.is_below_mass_threshold(
                self.constants.dispersal_mass_threshold
            )
            is_juvenile_and_migrate = (
                cohort.age == 0.0
                and random.random() <= cohort.migrate_juvenile_probability()
            )
            migrate = is_starving or is_juvenile_and_migrate

            if not migrate:
                continue

            destination_key = random.choice(self.neighbouring_keys)
            destination = self.get_community_by_key(destination_key)
            self.migrate(cohort, destination)

    def remove_dead_cohort(self, cohort: AnimalCohort) -> None:
        """Remove a dead cohort from a community.

        Args:
            cohort: The AnimalCohort instance that has lost all individuals.

        """

        if not cohort.is_alive:
            self.animal_cohorts[cohort.name].remove(cohort)
        elif cohort.is_alive:
            LOGGER.exception("An animal cohort which is alive cannot be removed.")

    def remove_dead_cohort_community(self) -> None:
        """This handles remove_dead_cohort for all cohorts in a community."""
        for cohort in chain.from_iterable(self.animal_cohorts.values()):
            if cohort.individuals <= 0:
                cohort.is_alive = False
                self.remove_dead_cohort(cohort)

    def birth(self, parent_cohort: AnimalCohort) -> None:
        """Produce a new AnimalCohort through reproduction.

        A cohort can only reproduce if it has an excess of reproductive mass above a
        certain threshold. The offspring will be an identical cohort of adults
        with age 0 and mass=birth_mass. A new territory, likely smaller b/c allometry,
        is generated for the newborn cohort.

        The science here follows Madingley.

        TODO: Check whether Madingley discards excess reproductive mass.
        TODO: Rework birth mass for indirect developers.

        Args:
            parent_cohort: The AnimalCohort instance which is producing a new cohort.
        """
        # semelparous organisms use a portion of their non-reproductive mass to make
        # offspring and then they die
        non_reproductive_mass_loss = 0.0
        if parent_cohort.functional_group.reproductive_type == "semelparous":
            non_reproductive_mass_loss = (
                parent_cohort.mass_current
                * parent_cohort.constants.semelparity_mass_loss
            )
            parent_cohort.mass_current -= non_reproductive_mass_loss
            # kill the semelparous parent cohort
            parent_cohort.is_alive = False

        number_offspring = (
            int(
                (parent_cohort.reproductive_mass + non_reproductive_mass_loss)
                / parent_cohort.functional_group.birth_mass
            )
            * parent_cohort.individuals
        )

        # reduce reproductive mass by amount used to generate offspring
        parent_cohort.reproductive_mass = 0.0

        offspring_cohort = AnimalCohort(
            get_functional_group_by_name(
                self.functional_groups,
                parent_cohort.functional_group.offspring_functional_group,
            ),
            parent_cohort.functional_group.birth_mass,
            0.0,
            number_offspring,
            DefaultTerritory(),
            self.constants,
        )

        # generate a territory for the offspring cohort
        self.initialize_territory(
            offspring_cohort,
            self.community_key,
            self.get_community_by_key,
        )

        # add a new cohort of the parental type to the community
        self.animal_cohorts[parent_cohort.name].append(offspring_cohort)

        if parent_cohort.functional_group.reproductive_type == "semelparous":
            self.remove_dead_cohort(parent_cohort)

    def birth_community(self) -> None:
        """This handles birth for all cohorts in a community."""

        # reproduction occurs for cohorts with sufficient reproductive mass
        for cohort in self.all_animal_cohorts:
            if (
                not cohort.is_below_mass_threshold(self.constants.birth_mass_threshold)
                and cohort.functional_group.reproductive_type != "nonreproductive"
            ):
                self.birth(cohort)

    def forage_community(self) -> None:
        """This function organizes the foraging of animal cohorts.

        It loops over every animal cohort in the community and calls the
        forage_cohort function with a list of suitable trophic resources. This action
        initiates foraging for those resources, with mass transfer details handled
        internally by forage_cohort and its helper functions. Future expansions may
        include functions for handling scavenging and soil consumption behaviors.

        Cohorts with no remaining individuals post-foraging are marked for death.

        TODO: find a more elegant way to remove dead cohorts between foraging bouts

        """
        # Generate the plant resources for foraging.

        plant_list: Sequence = [self.plant_community]

        for consumer_cohort in self.all_animal_cohorts:
            # Prepare the prey list for the consumer cohort
            if consumer_cohort.territory is None:
                raise ValueError("The cohort's territory hasn't been defined.")
            prey_list = consumer_cohort.territory.get_prey(consumer_cohort)
            plant_list = consumer_cohort.territory.get_plant_resources()
            excrement_list = consumer_cohort.territory.get_excrement_pools()

            # Initiate foraging for the consumer cohort with the prepared resources
            consumer_cohort.forage_cohort(
                plant_list=plant_list,
                animal_list=prey_list,
                excrement_pools=excrement_list,
            )

            # temporary solution
            self.remove_dead_cohort_community()

    def collect_prey(
        self, consumer_cohort: AnimalCohort
    ) -> MutableSequence[AnimalCohort]:
        """Collect suitable prey for a given consumer cohort.

        This is a helper function for territory.get_prey, it filters suitable prey from
        the total list of animal cohorts across the territory.

        TODO: possibly moved to be a territory method

        Args:
            consumer_cohort: The AnimalCohort for which a prey list is being collected

        Returns:
            A sequence of AnimalCohorts that can be preyed upon.

        """
        prey: MutableSequence = []
        for (
            prey_functional_group,
            potential_prey_cohorts,
        ) in self.animal_cohorts.items():
            # Skip if this functional group is not a prey of current predator
            if prey_functional_group not in consumer_cohort.prey_groups:
                continue

            # Get the size range of the prey this predator eats
            min_size, max_size = consumer_cohort.prey_groups[prey_functional_group]

            # Filter the potential prey cohorts based on their size
            for cohort in potential_prey_cohorts:
                if (
                    min_size <= cohort.mass_current <= max_size
                    and cohort.individuals != 0
                    and cohort is not consumer_cohort
                ):
                    prey.append(cohort)

        return prey

    def metabolize_community(self, temperature: float, dt: timedelta64) -> None:
        """This handles metabolize for all cohorts in a community.

        This method generates a total amount of metabolic waste per cohort and passes
        that waste to handler methods for distinguishing between nitrogenous and
        carbonaceous wastes as they need depositing in different pools. This will not
        be fully implemented until the stoichiometric rework.

        Respiration wastes are totaled because they are CO2 and not tracked spatially.
        Excretion wastes are handled cohort by cohort because they will need to be
        spatially explicit with multi-grid occupancy.

        TODO: Rework with stoichiometry

        Args:
            temperature: Current air temperature (K).
            dt: Number of days over which the metabolic costs should be calculated.

        """
        total_carbonaceous_waste = 0.0

        for cohort in self.all_animal_cohorts:
            metabolic_waste_mass = cohort.metabolize(temperature, dt)
            total_carbonaceous_waste += cohort.respire(metabolic_waste_mass)
            cohort.excrete(
                metabolic_waste_mass,
                cohort.territory.territory_excrement,
            )

        # Update the total_animal_respiration for this community using community_key.

        self.data["total_animal_respiration"].loc[{"cell_id": self.community_key}] += (
            total_carbonaceous_waste
        )

    def increase_age_community(self, dt: timedelta64) -> None:
        """This handles age for all cohorts in a community.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        for cohort in self.all_animal_cohorts:
            cohort.increase_age(dt)

    def inflict_non_predation_mortality_community(self, dt: timedelta64) -> None:
        """This handles natural mortality for all cohorts in a community.

        This includes background mortality, starvation, and, for mature cohorts,
        senescence.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        number_of_days = float(dt / timedelta64(1, "D"))
        for cohort in self.all_animal_cohorts:
            cohort.inflict_non_predation_mortality(
                number_of_days, cohort.territory.territory_carcasses
            )
            if cohort.individuals <= 0:
                cohort.is_alive = False
                self.remove_dead_cohort(cohort)

    def metamorphose(self, larval_cohort: AnimalCohort) -> None:
        """This transforms a larval status cohort into an adult status cohort.

        This method takes an indirect developing cohort in its larval form,
        inflicts a mortality rate, and creates an adult cohort of the correct type.

        TODO: Build in a relationship between larval_cohort mass and adult cohort mass.
        TODO: Is adult_mass the correct mass threshold?
        TODO: If the time step drops below a month, this needs an intermediary stage.

        Args:
            larval_cohort: The cohort in its larval stage to be transformed.
        """

        # inflict a mortality
        number_dead = ceil(
            larval_cohort.individuals * larval_cohort.constants.metamorph_mortality
        )
        larval_cohort.die_individual(
            number_dead, larval_cohort.territory.territory_carcasses
        )
        # collect the adult functional group
        adult_functional_group = get_functional_group_by_name(
            self.functional_groups,
            larval_cohort.functional_group.offspring_functional_group,
        )
        # create the adult cohort
        adult_cohort = AnimalCohort(
            adult_functional_group,
            adult_functional_group.birth_mass,
            0.0,
            larval_cohort.individuals,
            larval_cohort.territory,
            self.constants,
        )

        # generate a territory for the adult cohort
        self.initialize_territory(
            adult_cohort,
            self.community_key,
            self.get_community_by_key,
        )

        # add a new cohort of the parental type to the community
        self.animal_cohorts[adult_cohort.name].append(adult_cohort)

        # remove the larval cohort
        larval_cohort.is_alive = False
        self.remove_dead_cohort(larval_cohort)

    def metamorphose_community(self) -> None:
        """Handle metamorphosis for all applicable cohorts in the community."""

        for cohort in self.all_animal_cohorts:
            if (
                cohort.functional_group.development_type == DevelopmentType.INDIRECT
                and (cohort.mass_current >= cohort.functional_group.adult_mass)
            ):
                self.metamorphose(cohort)


class DefaultCommunity(AnimalCommunity):
    """A default community that represents an empty or non-functional state."""

    def __init__(self) -> None:
        self.functional_groups: tuple[FunctionalGroup, ...] = ()
        self.data: Data = self.data
        self.community_key: int = -1
        self.neighbouring_keys: list[int] = []
        self.constants: AnimalConsts = AnimalConsts()
        self.carcass_pool: CarcassPool = CarcassPool(10000.0, 0.0)
        """A pool for animal carcasses within the community."""
        self.excrement_pool: ExcrementPool = ExcrementPool(10000.0, 0.0)
        """A pool for excrement within the community."""
        self.plant_community: PlantResources = PlantResources(
            data=self.data,
            cell_id=self.community_key,
            constants=self.constants,
        )

    def collect_prey(
        self, consumer_cohort: AnimalCohort
    ) -> MutableSequence[AnimalCohort]:
        """Default method."""
        return []

    def get_community_by_key(self, key: int) -> AnimalCommunity:
        """Default method."""
        return self


class DefaultTerritory(Territory):
    """A default territory that represents an empty or non-functional state."""

    def __init__(self) -> None:
        """Default method."""
        self.grid_cell_keys: list[int] = []
        self._get_community_by_key = lambda key: DefaultCommunity()
        self.territory_carcasses: Sequence[DecayPool] = []
        self.territory_excrement: Sequence[DecayPool] = []

    def update_territory(self, consumer_cohort: Consumer) -> None:
        """Default method."""
        pass

    def get_prey(self, consumer_cohort: Consumer) -> MutableSequence[Consumer]:
        """Default method."""
        return []

    def get_plant_resources(self) -> MutableSequence[Resource]:
        """Default method."""
        return []

    def get_excrement_pools(self) -> MutableSequence[DecayPool]:
        """Default method."""
        return []

    def get_carcass_pools(self) -> MutableSequence[DecayPool]:
        """Default method."""
        return []

    def find_intersecting_carcass_pools(
        self, animal_territory: Territory
    ) -> MutableSequence[DecayPool]:
        """Default method."""
        return []

    def abandon_communities(self, consumer_cohort: Consumer) -> None:
        """Default method."""
        pass
