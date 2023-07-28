"""The ''animals'' module provides animal module functionality.

Todo:
- send portion of dead to carcass pool
- work out a big picture logic for what a month of foraging means and how to capture
it in functions

Current simplifications:
- only iteroparity (want: semelparity)
- no development

Notes to self:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
- waste_energy pool likely unnecessary, better to excrete directly to external pools
"""  # noqa: #D205, D415

from __future__ import annotations

from random import choice

from numpy import timedelta64

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_traits import DietType
from virtual_rainforest.models.animals.carcasses import CarcassPool
from virtual_rainforest.models.animals.constants import ENERGY_DENSITY, TEMPERATURE
from virtual_rainforest.models.animals.dummy_plants_and_soil import (
    PalatableSoil,
    PlantCommunity,
)
from virtual_rainforest.models.animals.functional_group import FunctionalGroup
from virtual_rainforest.models.animals.scaling_functions import (
    damuths_law,
    energetic_reserve_scaling,
    intake_rate_scaling,
    metabolic_rate,
    prey_group_selection,
)


class AnimalCohort:
    """This is a class of animal cohorts."""

    def __init__(
        self,
        functional_group: FunctionalGroup,
        mass: float,
        age: float,
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
            self.mass,
            TEMPERATURE,
            self.functional_group.metabolic_rate_terms,
            self.functional_group.metabolic_type,
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
        self.prey_groups: dict[str, tuple[float, float]] = prey_group_selection(
            self.functional_group.diet.value,
            self.mass,
            self.functional_group.prey_scaling,
        )

    def metabolize(self, dt: timedelta64) -> None:
        """The function to reduce stored_energy through basal metabolism.

        Args:
            dt: Number of days over which the metabolic costs should be calculated.

        """

        if dt < timedelta64(0, "D"):
            raise ValueError("dt cannot be negative.")

        if self.stored_energy < 0:
            raise ValueError("stored_energy cannot be negative.")

        # Number of seconds in a day * J/s metabolic rate, consider daily rate.
        energy_needed = self.metabolic_rate * float((dt / timedelta64(1, "s")))
        self.stored_energy -= min(self.stored_energy, energy_needed)

    def consumer_plants(self, plant_food: PlantCommunity, soil: PalatableSoil) -> float:
        """The function to transfer energy from a food source to the animal cohort.

        The flow to soil here will need to be replaced with a flow to a plant litter
        pool.

        Args:
            plant_food: The targeted PlantCommunity instance from which energy is
                transferred.
            soil: The soil community to which plant waste from consumption (leftovers)
                is deposited for decomposition.

        Returns:
            A float containing the amount of energy consumed in the herbivory bout.
        """
        consumed_energy = min(
            plant_food.energy,
            self.intake_rate * plant_food.energy_density * self.individuals,
        )
        # Minimum of the energy available and amount that can be consumed in an 8 hour
        # foraging window .
        plant_food.energy -= consumed_energy
        # The energy [J] extracted from the PlantCommunity adjusted for energetic
        # conversion efficiency and divided by the number of individuals in the cohort.
        soil.energy += consumed_energy * (
            1 - self.functional_group.mechanical_efficiency
        )

        return (
            consumed_energy
            * self.functional_group.conversion_efficiency
            * self.functional_group.mechanical_efficiency
        )

    def consume_prey(self, prey: AnimalCohort, carcass_pool: CarcassPool) -> float:
        """A predation event where this cohort preys on the given prey cohort.

        Removing both individuals and prey energy is a temporary implementation.

        Args:
            prey: The AnimalCohort instance being preyed upon.
            carcass_pool: The resident pool of animal carcasses to which the remains of
              dead individuals are delivered.

        Returns:
            A float containing the amount of energy consumed in the herbivory bout.

        """
        # Calculate the number of individuals that can be eaten based on intake rate
        # Here we assume predator can consume prey mass equivalent to its daily intake
        number_eaten = int(min(self.intake_rate // prey.mass, prey.individuals))

        # Calculate the energy gain from eating prey
        # Here we assume all eaten mass is converted to energy
        consumed_energy = min(
            (
                number_eaten
                * prey.mass
                * ENERGY_DENSITY["meat"]
                * self.functional_group.mechanical_efficiency
            ),
            prey.stored_energy,
        )

        # Reduce the number of individuals in the prey cohort and add energy to predator
        prey.individuals -= number_eaten
        # Excess from deficits of efficiency flow to the carcass pool
        carcass_pool.energy += consumed_energy * (
            1 - self.functional_group.mechanical_efficiency
        )

        prey.stored_energy -= consumed_energy

        return consumed_energy * self.functional_group.conversion_efficiency

    def excrete(self, soil: PalatableSoil, consumed_energy: float) -> None:
        """The function to transfer waste energy from an animal cohort to the soil.

        Args:
            soil: The local PalatableSoil pool in which waste is deposited.
            consumed_energy: The amount of energy flowing through cohort digestion.

        """
        waste_energy = consumed_energy * self.functional_group.conversion_efficiency
        soil.energy += waste_energy * self.individuals
        # The amount of waste by the average cohort member * number individuals.

    def increase_age(self, dt: timedelta64) -> None:
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

    def forage_cohort(
        self,
        plant_list: list[PlantCommunity],
        animal_list: list[AnimalCohort],
        carcass_pool: CarcassPool,
        soil_pool: PalatableSoil,
    ) -> None:
        """Forage the environment for food depending on diet type.

        Current version expected to search a single grid square and uses AnimalModel
        dummy implementations of plants (PlantCommunity).
        Direct interactions with food pools are handled with helper functions predation
        and herbivory. Combining those individual trophic events and adding energy
        gained to storage pools is handled here.

        Args:
            plant_list: A list of plant cohorts available for herbivory.
            animal_list: A list of animal cohorts available for predation.
            carcass_pool: A CarcassPool object representing available carcasses.
            soil_pool: A PalatableSoil object representing soil nutrients.

        """
        found_food = False
        print(self.name)
        print("Starting energy:")
        print(self.stored_energy)
        if self.functional_group.diet == DietType.HERBIVORE:
            if plant_list:
                plant_prey = choice(plant_list)
                print("I found plants!")
                energy = self.consumer_plants(plant_prey, soil_pool)
                found_food = True
        elif self.functional_group.diet == DietType.CARNIVORE:
            if animal_list:
                animal_prey = choice(animal_list)
                print("I found prey!")
                print(animal_prey.name)  # debugging
                energy = self.consume_prey(animal_prey, carcass_pool)
                found_food = True
        else:
            raise ValueError("Invalid diet type")

        if not found_food:
            print("didn't find food")  # debugging
            # debugging info - I expect these to be rare occurances
            if self.functional_group.diet.value == "herbivore":
                LOGGER.info("No plant available for herbivory.")
            elif self.functional_group.diet.value == "carnivore":
                LOGGER.info("No animal available for predation.")

        if found_food:
            # Increase consumer's stored energy with the energy gained from eating
            self.stored_energy += energy
            print("I gained energy:")
            print(energy)
        print("Final Energy:")
        print(self.stored_energy)
