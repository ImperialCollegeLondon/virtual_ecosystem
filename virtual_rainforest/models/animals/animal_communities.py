"""The ''animals'' module provides animal module functionality.

Todo:
- send portion of dead to carcass pool

Current simplifications:
- only herbivory (want: carnivory and omnivory)
- only iteroparity (want: semelparity)
- no development

Notes to self:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
"""  # noqa: #D205, D415


from __future__ import annotations

from itertools import chain

from numpy import timedelta64

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort
from virtual_rainforest.models.animals.carcasses import CarcassPool
from virtual_rainforest.models.animals.dummy_plants_and_soil import (
    PalatableSoil,
    PlantCommunity,
)

# from virtual_rainforest.models.animals.animal_model import AnimalModel
from virtual_rainforest.models.animals.functional_group import FunctionalGroup

# from virtual_rainforest.models.animals.protocols import Consumer, Resource


class AnimalCommunity:
    """This is a class for the animal community of a grid cell."""

    def __init__(
        self,
        functional_groups: list[FunctionalGroup],
    ) -> None:
        """The constructor of the AnimalCommunity class."""
        self.functional_groups = tuple(functional_groups)
        """A list of all FunctionalGroup types in the model."""

        self.animal_cohorts: dict[str, list[AnimalCohort]] = {
            k.name: [] for k in self.functional_groups
        }
        """Generate a dictionary of functional groups within the community."""
        self.plant_community: PlantCommunity = PlantCommunity(10000.0, 1)
        self.carcass_pool: CarcassPool = CarcassPool(10000.0, 1)
        self.soil_pool: PalatableSoil = PalatableSoil(10000.0, 1)

    def populate_community(self) -> None:
        """This function creates an instance of each functional group."""
        for functional_group in self.functional_groups:
            cohort = AnimalCohort(functional_group, functional_group.adult_mass, 0.0)
            self.animal_cohorts[functional_group.name].append(cohort)

    def migrate(self, migrant: AnimalCohort, destination: AnimalCommunity) -> None:
        """Function to move an AnimalCohort between AnimalCommunity objects.

        This function should take a cohort and a destination community and then pop the
        cohort from this community to the destination.

        Args:
            migrant: The AnimalCohort moving between AnimalCommunities.
            destination: The AnimalCommunity the cohort is moving to.

        """

        self.animal_cohorts[migrant.name].remove(migrant)
        destination.animal_cohorts[migrant.name].append(migrant)

    def die_cohort(self, cohort: AnimalCohort) -> None:
        """The function to change the cohort status from alive to dead.

        Args:
            cohort: The AnimalCohort instance that has lost all individuals.

        """

        if cohort.is_alive:
            cohort.is_alive = False
            LOGGER.debug("An animal cohort has died")
            self.animal_cohorts[cohort.name].remove(cohort)
        elif not cohort.is_alive:
            LOGGER.exception("An animal cohort which is dead cannot die.")

    def birth(self, cohort: AnimalCohort) -> None:
        """The function to produce a new AnimalCohort through reproduction.

        Currently, the birth function returns an identical cohort of adults with age
        0. In the future, the offspring will be modified to have appropriate juvenile
        traits based on parental type.

        Args:
            cohort: The AnimalCohort instance which is producing a new AnimalCohort.


        """
        self.animal_cohorts[cohort.name].append(
            AnimalCohort(
                cohort.functional_group, cohort.functional_group.birth_mass, 0.0
            )
        )

    def birth_community(self) -> None:
        """This handles birth for all cohorts in a community."""
        # Create a snapshot list of the current cohorts
        current_cohorts = list(chain.from_iterable(self.animal_cohorts.values()))
        for cohort in current_cohorts:
            # insert check for reproductive mass
            self.birth(cohort)

    def forage_community(self) -> None:
        """This function needs to organize the foraging of animal cohorts.

        It should loop over every animal cohort in the community and call the
        collect_prey and forage_cohort functions. This will create a list of suitable
        trophic resources and then action foraging on those resources. Details of
        energy transfer are handled inside forage_cohort and its helper functions.
        This will sooner be expanded to include functions for handling scavenging
        and soil consumption behaviors specifically.


        """
        plant_list = [self.plant_community]
        carcass_pool = self.carcass_pool
        soil_pool = self.soil_pool

        for consumer_cohort in chain.from_iterable(self.animal_cohorts.values()):
            prey = self.collect_prey(consumer_cohort)
            consumer_cohort.forage_cohort(
                plant_list=plant_list,
                animal_list=prey,
                carcass_pool=carcass_pool,
                soil_pool=soil_pool,
            )

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
            right_sized_prey = (
                c for c in potential_prey_cohorts if min_size <= c.mass <= max_size
            )
            prey.extend(right_sized_prey)

        return prey

    def migrate_community(self) -> None:
        """This handles migrating all cohorts in a community."""
        for cohort in chain.from_iterable(self.animal_cohorts.values()):
            # insert check for migration
            # insert random walk destination
            destination = self
            self.migrate(cohort, destination)

    def metabolize_community(self, dt: timedelta64) -> None:
        """This handles metabolize for all cohorts in a community.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """
        for cohort in chain.from_iterable(self.animal_cohorts.values()):
            cohort.metabolize(dt)

    def increase_age_community(self, dt: timedelta64) -> None:
        """This handles age for all cohorts in a community."""
        for cohort in chain.from_iterable(self.animal_cohorts.values()):
            cohort.increase_age(dt)

    def mortality_community(self) -> None:
        """This handles natural mortality for all cohorts in a community."""
        for cohort in chain.from_iterable(self.animal_cohorts.values()):
            # insert check for whether natural death occurs
            # determine how many deaths occur
            cohort.die_individual(0, self.carcass_pool)
