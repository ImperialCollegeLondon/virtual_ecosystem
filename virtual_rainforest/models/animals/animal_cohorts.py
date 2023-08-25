"""The ''animals'' module provides animal module functionality.

Notes:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
"""  # noqa: #D205, D415

from __future__ import annotations

from random import choice
from typing import Sequence

from numpy import timedelta64

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_traits import DietType
from virtual_rainforest.models.animals.constants import (
    DECAY_FRACTION_EXCREMENT,
    ENERGY_DENSITY,
    REPRODUCTION_ENERGY_COST_MULTIPLIER,
    REPRODUCTION_ENERGY_MULTIPLIER,
    TEMPERATURE,
)
from virtual_rainforest.models.animals.decay import CarcassPool
from virtual_rainforest.models.animals.functional_group import FunctionalGroup
from virtual_rainforest.models.animals.protocols import Consumer, DecayPool, Resource
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
        self.reproduction_energy_threshold: float = (
            energetic_reserve_scaling(
                mass,
                self.functional_group.muscle_mass_terms,
                self.functional_group.fat_mass_terms,
            )
            * REPRODUCTION_ENERGY_MULTIPLIER
        )
        """The energetic reserve threshold at which the cohort can reproduce."""
        self.reproduction_cost: float = (
            energetic_reserve_scaling(
                mass,
                self.functional_group.muscle_mass_terms,
                self.functional_group.fat_mass_terms,
            )
            * REPRODUCTION_ENERGY_COST_MULTIPLIER
        )
        """The energetic reserve of reproduction."""
        self.intake_rate: float = intake_rate_scaling(
            self.mass, self.functional_group.intake_rate_terms
        )
        """The individual rate of plant mass consumption over an 8hr foraging day
        [kg/day]."""
        self.prey_groups = prey_group_selection(
            self.functional_group.diet.value,
            self.mass,
            self.functional_group.prey_scaling,
        )
        # TODO - In future this should be parameterised using a constants dataclass, but
        # this hasn't yet been implemented for the animal model
        self.decay_fraction_excrement: float = DECAY_FRACTION_EXCREMENT
        """The fraction of excrement which decays before it gets consumed."""

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

    def excrete(
        self,
        excrement_pool: DecayPool,
        consumed_energy: float,
    ) -> None:
        """Transfer waste energy from an animal cohort to the excrement pool.

        Args:
            excrement_pool: The local ExcrementSoil pool in which waste is deposited.
            consumed_energy: The amount of energy flowing through cohort digestion.
        """
        # Find total waste energy, the total amount of waste is then found by the
        # average cohort member * number individuals.
        waste_energy = consumed_energy * self.functional_group.conversion_efficiency

        # This total waste is then split between decay and scavengeable excrement
        excrement_pool.scavengeable_energy += (
            (1 - self.decay_fraction_excrement) * waste_energy * self.individuals
        )
        excrement_pool.decomposed_energy += (
            self.decay_fraction_excrement * waste_energy * self.individuals
        )

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

        carcass_pool.scavengeable_energy += (
            number_dead * self.mass * ENERGY_DENSITY["meat"]
        )

    def get_eaten(self, predator: Consumer, carcass_pool: DecayPool) -> float:
        """This function handles AnimalCohorts being subject to predation.

        Note: AnimalCohort stored_energy is mean per individual energy within the
            cohort. Energy is not lost from stored_energy from a predation event but the
            number of individuals in the cohort is reduced.

        Args:
            predator: The AnimalCohort preying on the eaten cohort.
            carcass_pool: The resident pool of animal carcasses to which the remains of
              dead individuals are delivered.

        Returns:
            A float of the energy value of the lost individuals after digestive
                efficiencies are accounted for.

        """
        # Calculate the number of individuals that can be eaten based on intake rate
        # Here we assume predators can consume prey mass equivalent to daily intake
        number_eaten = min(
            int((predator.intake_rate * predator.individuals) // self.mass),
            self.individuals,
        )

        # Calculate the energy gain from eating prey
        # Here we assume all eaten mass is converted to energy
        prey_energy = min(
            (
                number_eaten
                * self.mass
                * ENERGY_DENSITY["meat"]
                * self.functional_group.mechanical_efficiency
            ),
            self.stored_energy,
        )

        # Reduce the number of individuals in the prey cohort
        self.individuals -= number_eaten
        # Excess from deficits of efficiency flow to the carcass pool
        carcass_pool.scavengeable_energy += prey_energy * (
            1 - self.functional_group.mechanical_efficiency
        )

        # return the net energetic gain of predation
        return prey_energy * predator.functional_group.conversion_efficiency

    def forage_cohort(
        self,
        plant_list: Sequence[Resource],
        animal_list: Sequence[Resource],
        carcass_pool: DecayPool,
        excrement_pool: DecayPool,
    ) -> None:
        """This function handles selection of resources from a list of options.

        Currently, this function is passed a list of plant or animal resources from
        AnimalCommunity.forage_community and performs a simple random uniform selection.
        After this, excrete is called to pass excess waste to the excrement pool.
        Later this function will involve more complex weightings of prey options.

        Args:
            plant_list: A list of plant cohorts available for herbivory.
            animal_list: A list of animal cohorts available for predation.
            carcass_pool: A CarcassPool object representing available carcasses.
            excrement_pool: A pool representing the excrement in the grid cell

        """

        if self.functional_group.diet == DietType.HERBIVORE and plant_list:
            consumed_energy = self.eat(choice(plant_list), excrement_pool)
        elif self.functional_group.diet == DietType.CARNIVORE and animal_list:
            consumed_energy = self.eat(choice(animal_list), carcass_pool)
        else:
            LOGGER.info("No food available.")
        # excrete excess digestive wastes
        self.excrete(excrement_pool, consumed_energy)

    def eat(self, food: Resource, pool: DecayPool) -> float:
        """This function handles the energy transfer of a trophic interaction.

        Currently, all this does is call the food's get_eaten method and pass the
        returned energy value to the consumer.

        Args:
            food: An object of a Resource class (currently: AnimalCohort, Plant
                  Community)
            pool: An object of a DecayPool class, which could represent depositional
                  pools like soil or carcass pools.

        Returns:
            The amount of consumed energy so it can be used to determine waste output.

        """
        # Check if self.individuals is greater than zero
        if self.individuals == 0:
            raise ValueError("Individuals cannot be 0.")

        # get the per-individual energetic gain from the bulk value
        energy = food.get_eaten(self, pool) / self.individuals
        self.stored_energy += energy
        return energy  # for passing to excrete

    def can_reproduce(self) -> bool:
        """Checks if a cohort has sufficient energy to reproduce.

        Currently this keys off an excess of stored_energy, later in development this
        reproduction system will work around a specific pool of reproductive mass.

        Return:
            Boolean of whether or not the cohort exceeds the reproduction threshold and
            can reproduce.

        """
        return self.stored_energy >= self.reproduction_energy_threshold
