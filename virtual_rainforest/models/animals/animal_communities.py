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

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort
from virtual_rainforest.models.animals.carcasses import CarcassPool
from virtual_rainforest.models.animals.dummy_plants_and_soil import (
    PalatableSoil,
    PlantCommunity,
)

# from virtual_rainforest.models.animals.animal_model import AnimalModel
from virtual_rainforest.models.animals.functional_group import FunctionalGroup


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

    def immigrate(self, immigrant: AnimalCohort, destination: AnimalCommunity) -> None:
        """Function to move an AnimalCohort between AnimalCommunity objects.

        This function should take a cohort and a destination community and then pop the
        cohort from this community to the destination.

        Args:
            immigrant: The AnimalCohort moving between AnimalCommunities.
            destination: The AnimalCommunity the cohort is moving to.

        """

        destination.animal_cohorts[immigrant.name].append(
            self.animal_cohorts[immigrant.name].pop(
                self.animal_cohorts[immigrant.name].index(immigrant)
            )
        )

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

    def birth(self, cohort: AnimalCohort) -> AnimalCohort:
        """The function to produce a new AnimalCohort through reproduction.

        Currently, the birth function returns an identical cohort of adults with age
        0. In the future, the offspring will be modified to have appropriate juvenile
        traits based on parental type.

        Args:
            cohort: The AnimalCohort instance which is producing a new AnimalCohort.

        Returns:
            A new age 0 AnimalCohort.

        """
        self.animal_cohorts[cohort.name].append(
            AnimalCohort(cohort.functional_group, cohort.mass, 0.0)
        )
        return self.animal_cohorts[cohort.name][-1]

    def forage_community(self) -> None:
        """This function needs to handle the foraging of animal cohorts.

        It should loop over every animal cohort in the community and call either
        herbivory or predation functions. This will sooner be expanded to include
        functions for handling scavenging and soil consumption behaviors specifically.


        """
        plant_list = [self.plant_community]
        carcass_pool = self.carcass_pool
        soil_pool = self.soil_pool

        for functional_group, cohorts in self.animal_cohorts.items():
            # Create a separate list of prey for each functional group
            prey = []
            cohort = None  # Initialize 'cohort' before the loop
            for cohort in cohorts:
                if functional_group not in cohort.prey_groups:
                    continue

                min_size, max_size = cohort.prey_groups[functional_group]
                right_sized = [c for c in cohorts if min_size <= c.mass <= max_size]
                prey.extend(right_sized)

            # Skip to the next iteration if 'cohort' is None
            if cohort is None:
                continue

            # Now, the 'prey' list contains all AnimalCohort objects that match the
            # prey_groups criteria
            # Use this 'prey' list in the forage_cohort method for each cohort
            cohort.forage_cohort(
                plant_list=plant_list,
                animal_list=prey,
                carcass_pool=carcass_pool,
                soil_pool=soil_pool,
            )
