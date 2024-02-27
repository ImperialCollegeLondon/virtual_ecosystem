"""The ''animals'' module provides animal module functionality.

Notes:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
"""  # noqa: #D205, D415

from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import chain
from random import choice

from numpy import timedelta64

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort
from virtual_rainforest.models.animals.constants import AnimalConsts
from virtual_rainforest.models.animals.decay import CarcassPool, ExcrementPool
from virtual_rainforest.models.animals.functional_group import FunctionalGroup
from virtual_rainforest.models.animals.plant_resources import PlantResources
from virtual_rainforest.models.animals.scaling_functions import damuths_law


class AnimalCommunity:
    """This is a class for the animal community of a grid cell.

    Args:
        functional_groups: A list of FunctionalGroup objects
        data: The core data object
        community_key: The integer key of the cell id for this community
        neighbouring_keys: A list of cell id keys for neighbouring communities
        get_destination: A function to return a destination AnimalCommunity for
            migration.
    """

    def __init__(
        self,
        functional_groups: list[FunctionalGroup],
        data: Data,
        community_key: int,
        neighbouring_keys: list[int],
        get_destination: Callable[[int], AnimalCommunity],
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
        self.get_destination = get_destination
        """Callable get_destination from AnimalModel."""
        self.constants = constants
        """Animal constants."""

        self.animal_cohorts: dict[str, list[AnimalCohort]] = {
            k.name: [] for k in self.functional_groups
        }
        """A dictionary of lists of animal cohort keyed by functional group."""
        self.carcass_pool: CarcassPool = CarcassPool(10000.0, 0.0)
        """A pool for animal carcasses within the community."""
        self.excrement_pool: ExcrementPool = ExcrementPool(10000.0, 0.0)
        """A pool for excrement within the community."""

    @property
    def all_animal_cohorts(self) -> Iterable[AnimalCohort]:
        """Get an iterable of all animal cohorts in the community.

        This property provides access to all the animal cohorts contained
        within this community class.

        Returns:
            Iterable[AnimalCohort]: An iterable of AnimalCohort objects.
        """
        return chain.from_iterable(self.animal_cohorts.values())

    def populate_community(self) -> None:
        """This function creates an instance of each functional group.

        Currently, this is the simplest implementation of populating the animal model.
        In each AnimalCommunity one AnimalCohort of each FunctionalGroup type is
        generated. So the more functional groups that are made, the denser the animal
        community will be. This function will need to be reworked dramatically later on.

        """
        for functional_group in self.functional_groups:
            individuals = damuths_law(
                functional_group.adult_mass, functional_group.damuths_law_terms
            )

            cohort = AnimalCohort(
                functional_group,
                functional_group.adult_mass,
                0.0,
                individuals,
                self.constants,
            )
            self.animal_cohorts[functional_group.name].append(cohort)

    def migrate(self, migrant: AnimalCohort, destination: AnimalCommunity) -> None:
        """Function to move an AnimalCohort between AnimalCommunity objects.

        This function should take a cohort and a destination community and then pop the
        cohort from this community to the destination.

        TODO: Implement juvenile dispersal.
        TODO: Implement low-density trigger.

        Args:
            migrant: The AnimalCohort moving between AnimalCommunities.
            destination: The AnimalCommunity the cohort is moving to.

        """

        self.animal_cohorts[migrant.name].remove(migrant)
        destination.animal_cohorts[migrant.name].append(migrant)

    def migrate_community(self) -> None:
        """This handles migrating all cohorts in a community."""
        for cohort in self.all_animal_cohorts:
            if cohort.is_below_mass_threshold(self.constants.dispersal_mass_threshold):
                # Random walk destination from the neighbouring keys
                destination_key = choice(self.neighbouring_keys)
                destination = self.get_destination(destination_key)
                self.migrate(cohort, destination)

    def die_cohort(self, cohort: AnimalCohort) -> None:
        """The function to change the cohort status from alive to dead.

        Args:
            cohort: The AnimalCohort instance that has lost all individuals.

        """

        if cohort.is_alive:
            cohort.is_alive = False
            # LOGGER.debug("An animal cohort has died")
            self.animal_cohorts[cohort.name].remove(cohort)
        elif not cohort.is_alive:
            LOGGER.exception("An animal cohort which is dead cannot die.")

    def die_cohort_community(self) -> None:
        """This handles die_cohort for all cohorts in a community."""
        for cohort in chain.from_iterable(self.animal_cohorts.values()):
            self.die_cohort(cohort)

    def birth(self, parent_cohort: AnimalCohort) -> None:
        """Produce a new AnimalCohort through reproduction.

        A cohort can only reproduce if it has an excess of reproductive mass above a
        certain threshold. The offspring will be an identical cohort of adults
        with age 0 and mass=birth_mass.

        TODO: Implement juvenile dispersal.
        TODO: Check whether madingley discards excess reproductive mass

        Args:
            parent_cohort: The AnimalCohort instance which is producing a new
            AnimalCohort.

        """
        number_offspring = int(
            (parent_cohort.reproductive_mass * parent_cohort.individuals)
            / parent_cohort.functional_group.birth_mass
        )

        # reduce reproductive mass by amount used to generate offspring
        parent_cohort.reproductive_mass = 0.0

        # add a new cohort of the parental type to the community
        self.animal_cohorts[parent_cohort.name].append(
            AnimalCohort(
                parent_cohort.functional_group,
                parent_cohort.functional_group.birth_mass,
                0.0,
                number_offspring,
                self.constants,
            )
        )

    def birth_community(self) -> None:
        """This handles birth for all cohorts in a community."""

        # reproduction occurs for cohorts with sufficient reproductive mass
        for cohort in self.all_animal_cohorts:
            if not cohort.is_below_mass_threshold(self.constants.birth_mass_threshold):
                self.birth(cohort)

    def forage_community(self) -> None:
        """This function needs to organize the foraging of animal cohorts.

        It should loop over every animal cohort in the community and call the
        collect_prey and forage_cohort functions. This will create a list of suitable
        trophic resources and then action foraging on those resources. Details of
        mass transfer are handled inside forage_cohort and its helper functions.
        This will sooner be expanded to include functions for handling scavenging
        and soil consumption behaviors specifically.

        TODO Remove excess die_cohort related checks

        """
        # Generate the plant resources for foraging.
        plant_community: PlantResources = PlantResources(
            data=self.data,
            cell_id=self.community_key,
            constants=self.constants,
        )

        plant_list = [plant_community]

        for consumer_cohort in self.all_animal_cohorts:
            if (
                consumer_cohort.individuals == 0
            ):  # temporary while finalizing die_cohort placements
                continue

            prey_list = self.collect_prey(consumer_cohort)
            food_choice = consumer_cohort.forage_cohort(
                plant_list=plant_list,
                animal_list=prey_list,
                carcass_pool=self.carcass_pool,
                excrement_pool=self.excrement_pool,
            )
            if isinstance(food_choice, AnimalCohort) and food_choice.individuals == 0:
                self.die_cohort(food_choice)

    def collect_prey(self, consumer_cohort: AnimalCohort) -> list[AnimalCohort]:
        """Collect suitable prey for a given consumer cohort.

        This is a helper function for forage_community to isolate the prey selection
        functionality. It was already getting confusing and it will get much more so
        as the Animal Module develops.

        Args:
            consumer_cohort: The AnimalCohort for which a prey list is being collected

        Returns:
            A list of AnimalCohorts that can be preyed upon.

        """
        prey: list = []
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

        Args:
            temperature: Current air temperature (K).
            dt: Number of days over which the metabolic costs should be calculated.

        """
        for cohort in self.all_animal_cohorts:
            cohort.metabolize(temperature, dt)

    def increase_age_community(self, dt: timedelta64) -> None:
        """This handles age for all cohorts in a community.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        for cohort in self.all_animal_cohorts:
            cohort.increase_age(dt)

    def inflict_natural_mortality_community(self, dt: timedelta64) -> None:
        """This handles natural mortality for all cohorts in a community.

        TODO Replace the number_of_days format with a passthrough of the initialized
        dt straight to the scaling function that sets the cohort rates.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        number_of_days = float(dt / timedelta64(1, "D"))
        for cohort in self.all_animal_cohorts:
            cohort.inflict_natural_mortality(self.carcass_pool, number_of_days)
            if cohort.individuals <= 0:
                self.die_cohort(cohort)
