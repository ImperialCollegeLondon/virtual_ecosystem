"""The ''dummy animal'' module provides toy animal module functionality as well 
as self-contained dummy versions of the abiotic, soil, and plant modules that 
are required for setting up and testing the early stages of the animal module.

Todo:
- rework dispersal
- send portion of dead to carcass pool

Current simplifications:
- only herbivory (want: carnivory and omnivory)
- only endothermy (want: ectothermy)
- only iteroparity (want: semelparity)
- no development

Notes to self:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
- waste_energy pool likely unnecessary, better to excrete directly to external pools
"""  # noqa: #D205, D415

from __future__ import annotations

from dataclasses import dataclass

from numpy import timedelta64

from virtual_rainforest.core.logger import LOGGER

# from virtual_rainforest.models.animals.animal_model import AnimalModel
from virtual_rainforest.models.animals.carcasses import CarcassPool
from virtual_rainforest.models.animals.constants import ENERGY_DENSITY
from virtual_rainforest.models.animals.functional_group import FunctionalGroup
from virtual_rainforest.models.animals.scaling_functions import (
    damuths_law,
    energetic_reserve_scaling,
    intake_rate_scaling,
    metabolic_rate,
)

# from random import choice


class PlantCommunity:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, mass: float, position: int) -> None:
        """The constructor for Plant class."""
        self.mass = mass
        """The mass of the plant cohort [kg]."""
        self.energy_density: float = ENERGY_DENSITY["plant"]
        """The energy (J) in a kg of plant [currently set to toy value of Alfalfa]."""
        self.energy_max: float = self.mass * self.energy_density
        """The maximum amount of energy that the cohort can have [J] [Alfalfa]."""
        self.energy = self.energy_max
        """The amount of energy in the plant cohort [J] [toy]."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.position = position
        """The grid location of the cohort."""

    def grow(self) -> None:
        """The function to logistically modify cohort energy to the energy_max value."""
        self.energy += self.energy * (1 - self.energy / self.energy_max)

    def die(self) -> None:
        """The function to kill a plant cohort."""
        if self.is_alive:
            self.is_alive = False
            LOGGER.info("A Plant Community has died")
        elif not self.is_alive:
            LOGGER.warning("A Plant Community which is dead cannot die.")


@dataclass
class PalatableSoil:
    """This is a dummy class of soil pools for testing the animal module."""

    energy: float
    """The amount of energy in the soil pool [J]."""
    position: int
    """The grid position of the soil pool."""


class AnimalCommunity:
    """This is a class for the animal community of a grid cell."""

    def __init__(
        self,
        functional_groups: list[FunctionalGroup],
    ) -> None:
        """The constructor of the AnimalCommunity class."""
        self.functional_groups = tuple(functional_groups)
        """A list of all FunctionalGroup types in the model."""

        self.cohorts: dict[str, list[AnimalCohort]] = {
            k.name: [] for k in self.functional_groups
        }
        """Generate a dictionary of functional groups within the community."""

    def immigrate(self, immigrant: AnimalCohort, destination: AnimalCommunity) -> None:
        """Function to move an AnimalCohort between AnimalCommunity objects.

        This function should take a cohort and a destination community and then pop the
        cohort from this community to the destination.

        Args:
            immigrant: The AnimalCohort moving between AnimalCommunities.
            destination: The AnimalCommunity the cohort is moving to.

        """

        destination.cohorts[immigrant.name].append(
            self.cohorts[immigrant.name].pop(
                self.cohorts[immigrant.name].index(immigrant)
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
            self.cohorts[cohort.name].remove(cohort)
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
        self.cohorts[cohort.name].append(
            AnimalCohort(cohort.functional_group, cohort.mass, 0.0)
        )
        return self.cohorts[cohort.name][-1]


class AnimalCohort:
    """This is a class of animal cohorts."""

    def __init__(
        self,
        functional_group: FunctionalGroup,
        mass: float,
        age: float,
    ) -> None:
        """The constructor for the AnimalCohort class."""
        self.functional_group = functional_group
        """The functional group of the animal cohort which holds constants."""
        self.name = functional_group.name
        """The functional type name of the animal cohort."""
        self.mass = mass
        """The average mass of an individual in the animal cohort [kg]."""
        self.age = age
        """The age of the animal cohort [days]."""
        self.individuals: int = damuths_law(
            self.mass, self.functional_group.damuths_law_terms
        )
        """The number of individuals in the cohort."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.metabolic_rate: float = metabolic_rate(
            self.mass, self.functional_group.metabolic_rate_terms
        )
        """The rate at which energy is expended in [J/s]."""
        self.stored_energy: float = energetic_reserve_scaling(
            mass,
            self.functional_group.muscle_mass_terms,
            self.functional_group.fat_mass_terms,
        )
        """The individual energetic reserve [J] as the sum of muscle"
        mass [g] and fat mass [g] multiplied by its average energetic value."""
        self.intake_rate: float = intake_rate_scaling(
            self.mass, self.functional_group.intake_rate_terms
        )
        """The individual rate of plant mass consumption over an 8hr foraging day
        [kg/day]."""

    def metabolize(self, dt: timedelta64) -> None:
        """The function to reduce stored_energy through basal metabolism.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """

        energy_burned = float(dt / timedelta64(1, "s")) * self.metabolic_rate
        # Number of seconds in a day * J/s metabolic rate, consider daily rate.
        if self.stored_energy >= energy_burned:
            self.stored_energy -= energy_burned
        elif self.stored_energy < energy_burned:
            self.stored_energy = 0.0

    def eat(self, food: PlantCommunity) -> float:
        """The function to transfer energy from a food source to the animal cohort.

        Args:
            food: The targeted PlantCommunity instance from which energy is
                transferred.

        Returns:
            A float containing the amount of energy consumed in the foraging bout.
        """
        consumed_energy = min(food.energy, self.intake_rate * food.energy_density)
        # Minimum of the energy available and amount that can be consumed in an 8 hour
        # foraging window .
        food.energy -= consumed_energy * self.individuals
        # The amount of energy consumed by the average member * number of individuals.
        self.stored_energy += (
            consumed_energy * self.functional_group.conversion_efficiency
        )
        # The energy [J] extracted from the PlantCommunity adjusted for energetic
        # conversion efficiency and divided by the number of individuals in the cohort.
        return consumed_energy

    def excrete(self, soil: PalatableSoil, consumed_energy: float) -> None:
        """The function to transfer waste energy from an animal cohort to the soil.

        Args:
            soil: The local PalatableSoil pool in which waste is deposited.
            consumed_energy: The amount of energy flowing through cohort digestion.

        """
        waste_energy = consumed_energy * self.functional_group.conversion_efficiency
        soil.energy += waste_energy * self.individuals
        # The amount of waste by the average cohort member * number individuals.

    def forage(self, food: PlantCommunity, soil: PalatableSoil) -> None:
        """The function to enact multi-step foraging behaviors.

        Currently, this wraps the acts of consuming plants and excreting wastes. It will
        later wrap additional functions for selecting a food choice and navigating
        predation interactions.

        Args:
            food: The targeted PlantCommunity instance from which energy is
                transferred.
            soil: The local PalatableSoil pool in which waste is deposited.

        """
        consumed_energy = self.eat(food)
        self.excrete(soil, consumed_energy)

    def aging(self, dt: timedelta64) -> None:
        """The function to modify cohort age as time passes.

        Args:
            dt: The amount of time that should be added to cohort age.

        """
        self.age += float(dt / timedelta64(1, "D"))

    def die_individual(self, number_dead: int, carcass_pool: CarcassPool) -> None:
        """The function to reduce the number of individuals in the cohort through death.

        Currently, all cohorts are crafted as single km2 grid cohorts. This means that
        very large animals will have one or fewer cohort members per grid. As changes
        are made to capture large body size and multi-grid occupancy, this will be
        updated.

        Args:
            number_dead: The number of individuals by which to decrease the population
                count.
            carcass_pool: The resident pool of animal carcasses to which the dead
                individuals are delivered.

        """
        self.individuals -= number_dead
        carcass_pool.energy += number_dead * self.mass * ENERGY_DENSITY["meat"]