"""The ''animals'' module provides animal module functionality.

Notes:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
"""  # noqa: #D205, D415

from __future__ import annotations

from math import ceil
from random import choice
from typing import Optional, Sequence

from numpy import random, timedelta64

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.animal_traits import DietType
from virtual_rainforest.models.animals.constants import (
    DECAY_FRACTION_CARCASSES,
    DECAY_FRACTION_EXCREMENT,
    FLOW_TO_REPRODUCTIVE_MASS_THRESHOLD,
)
from virtual_rainforest.models.animals.decay import CarcassPool
from virtual_rainforest.models.animals.functional_group import FunctionalGroup
from virtual_rainforest.models.animals.protocols import Consumer, DecayPool, Resource
from virtual_rainforest.models.animals.scaling_functions import (
    damuths_law,
    intake_rate_scaling,
    metabolic_rate,
    natural_mortality_scaling,
    prey_group_selection,
)


class AnimalCohort:
    """This is a class of animal cohorts."""

    def __init__(
        self,
        functional_group: FunctionalGroup,
        mass: float,
        age: float,
        individuals: int,
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
        """The average mass of an individual in the animal cohort [kg]."""
        self.mass_current = mass
        """The current average body mass of an individual [kg]."""
        self.age = age
        """The age of the animal cohort [days]."""
        self.individuals = individuals
        """The number of individuals in this cohort."""
        self.damuth_density: int = damuths_law(
            self.functional_group.adult_mass, self.functional_group.damuths_law_terms
        )
        """The number of individuals in an average cohort of this type."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.reproductive_mass: float = 0.0
        """The pool of biomass from which the material of reproduction is drawn."""

        self.intake_rate: float = intake_rate_scaling(
            self.functional_group.adult_mass, self.functional_group.intake_rate_terms
        )
        """The individual rate of plant mass consumption over an 8hr foraging day
        [kg/day]."""
        self.prey_groups = prey_group_selection(
            self.functional_group.diet,
            self.functional_group.adult_mass,
            self.functional_group.prey_scaling,
        )
        """The identification of useable food resources."""

        self.adult_natural_mortality_prob = natural_mortality_scaling(
            self.functional_group.adult_mass, self.functional_group.longevity_scaling
        )
        # TODO: Distinguish between background, senesence, and starvation mortalities.
        """The per-day probability of an individual dying to natural causes."""

        # TODO - In future this should be parameterised using a constants dataclass, but
        # this hasn't yet been implemented for the animal model
        self.decay_fraction_excrement: float = DECAY_FRACTION_EXCREMENT
        """The fraction of excrement which decays before it gets consumed."""
        self.decay_fraction_carcasses: float = DECAY_FRACTION_CARCASSES
        """The fraction of carcass biomass which decays before it gets consumed."""

    def metabolize(self, temperature: float, dt: timedelta64) -> None:
        """The function to reduce mass_current through basal metabolism.

        TODO: Implement distinction between field and basal rates.
        TODO: Implement proportion of day active.
        TODO: clean up units

        Args:
            temperature: Current air temperature (K)
            dt: Number of days over which the metabolic costs should be calculated.

        """

        if dt < timedelta64(0, "D"):
            raise ValueError("dt cannot be negative.")

        if self.mass_current < 0:
            raise ValueError("mass_current cannot be negative.")

        #  kg/day metabolic rate * number of days
        mass_metabolized = metabolic_rate(
            self.mass_current,
            temperature,
            self.functional_group.metabolic_rate_terms,
            self.functional_group.metabolic_type,
        ) * float((dt / timedelta64(1, "D")))

        self.mass_current -= min(self.mass_current, mass_metabolized)

    def excrete(
        self,
        excrement_pool: DecayPool,
        mass_consumed: float,
    ) -> None:
        """Transfer waste mass from an animal cohort to the excrement pool.

        Currently, this function is in an inbetween state where mass is removed from
        the animal cohort but it is recieved by the litter pool as energy. This will be
        fixed once the litter pools are updated for mass.

        TODO: Rework after update litter pools for mass

        Args:
            excrement_pool: The local ExcrementSoil pool in which waste is deposited.
            mass_consumed: The amount of mass flowing through cohort digestion.
        """
        # Find total waste mass, the total amount of waste is then found by the
        # average cohort member * number individuals.
        waste_energy = mass_consumed * self.functional_group.conversion_efficiency

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

        Currently, this function is in an inbetween state where mass is removed from
        the animal cohort but it is recieved by the litter pool as energy. This will be
        fixed once the litter pools are updated for mass.

        TODO: Rework after update litter pools for mass

        Args:
            number_dead: The number of individuals by which to decrease the population
                count.
            carcass_pool: The resident pool of animal carcasses to which the dead
                individuals are delivered.

        """
        self.individuals -= number_dead

        # Find total mass contained in the carcasses
        carcass_mass = number_dead * self.mass_current

        # Split this mass between carcass decay, and scavengeable carcasses
        carcass_pool.scavengeable_energy += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass
        carcass_pool.decomposed_energy += self.decay_fraction_carcasses * carcass_mass

    def get_eaten(self, predator: Consumer, carcass_pool: DecayPool) -> float:
        """This function handles AnimalCohorts being subject to predation.

        Note: AnimalCohort mass_current is mean per individual mass within the
            cohort. Mass is not lost from mass_current from a predation event but the
            number of individuals in the cohort is reduced.

        Currently, this function is in an inbetween state where mass is removed from
        the animal cohort but it is recieved by the litter pool as energy. This will be
        fixed once the litter pools are updated for mass.

        TODO: Rework after update litter pools for mass

        Args:
            predator: The AnimalCohort preying on the eaten cohort.
            carcass_pool: The resident pool of animal carcasses to which the remains of
              dead individuals are delivered.

        Returns:
            A float of the mass value of the lost individuals after digestive
                efficiencies are accounted for.

        """
        # Calculate the number of individuals that can be eaten based on intake rate
        # Here we assume predators can consume prey mass equivalent to daily intake
        number_eaten = min(
            ceil((predator.intake_rate * predator.individuals) / self.mass_current),
            self.individuals,
        )

        # Calculate the mass gain from eating prey
        # Here we assume all eaten mass is converted to consumer mass
        prey_mass = min(
            (
                number_eaten
                * self.mass_current
                * self.functional_group.mechanical_efficiency
            ),
            self.mass_current,
        )

        # Reduce the number of individuals in the prey cohort
        self.individuals -= number_eaten
        # Calculate excess from deficits of efficiency, which flows to the carcass pool
        carcass_mass = prey_mass * (1 - self.functional_group.mechanical_efficiency)

        # Split this mass between carcass decay, and scavengeable carcasses
        carcass_pool.scavengeable_energy += (
            1 - self.decay_fraction_carcasses
        ) * carcass_mass
        carcass_pool.decomposed_energy += self.decay_fraction_carcasses * carcass_mass

        # return the net mass gain of predation
        return prey_mass * predator.functional_group.conversion_efficiency

    def forage_cohort(
        self,
        plant_list: Sequence[Resource],
        animal_list: Sequence[Resource],
        carcass_pool: DecayPool,
        excrement_pool: DecayPool,
    ) -> Optional[Resource]:  # Note the optional here, temporary
        """This function handles selection of resources from a list of options.

        Currently, this function is passed a list of plant or animal resources from
        AnimalCommunity.forage_community and performs a simple random uniform selection.
        After this, excrete is called to pass excess waste to the excrement pool.
        Later this function will involve more complex weightings of prey options.

        TODO: Fix the occasional division by zero bug in eat and then remove Optional

        Args:
            plant_list: A list of plant cohorts available for herbivory.
            animal_list: A list of animal cohorts available for predation.
            carcass_pool: A CarcassPool object representing available carcasses.
            excrement_pool: A pool representing the excrement in the grid cell

        """

        if self.individuals == 0:
            LOGGER.warning("No individuals in cohort to forage.")
            return None  # Early return with no food choice

        mass_consumed = 0.0  # Initialize to 0.0

        try:
            if self.functional_group.diet == DietType.HERBIVORE and plant_list:
                food_choice = choice(plant_list)
                mass_consumed = self.eat(food_choice, excrement_pool)
            elif self.functional_group.diet == DietType.CARNIVORE and animal_list:
                food_choice = choice(animal_list)
                mass_consumed = self.eat(food_choice, carcass_pool)
            else:
                LOGGER.info("No food available.")
                food_choice = None  # No food available

        except ValueError as e:
            raise e

        # excrete excess digestive wastes
        self.excrete(excrement_pool, mass_consumed)

        return food_choice

    def eat(self, food: Resource, pool: DecayPool) -> float:
        """This function handles the mass transfer of a trophic interaction.

        Currently, all this does is call the food's get_eaten method and pass the
        returned mass value to the consumer.

        Args:
            food: An object of a Resource class (currently: AnimalCohort, Plant
                  Community)
            pool: An object of a DecayPool class, which could represent depositional
                  pools like soil or carcass pools.

        Returns:
            The amount of consumed mass so it can be used to determine waste output.

        """
        # Check if self.individuals is greater than zero
        if self.individuals == 0:
            return 0.0

        if self is food:
            raise ValueError("The food and the consumer are the same object.")

        # get the per-individual energetic gain from the bulk value
        mass_consumed = food.get_eaten(self, pool) / self.individuals

        if self.is_below_mass_threshold(FLOW_TO_REPRODUCTIVE_MASS_THRESHOLD):
            # if current mass equals or exceeds standard adult mass, gains to repro mass
            self.mass_current += mass_consumed
        else:
            # otherwise, gains flow to non-reproductive body mass.
            self.reproductive_mass += mass_consumed
        return mass_consumed  # for passing to excrete

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

    def inflict_natural_mortality(
        self, carcass_pool: CarcassPool, number_days: float
    ) -> None:
        """The function to cause natural mortality in a cohort.

        TODO Find a more efficient structure so we aren't recalculating the
        time_step_mortality. Probably pass through the initialized timestep size to the
        scaling function

        Args:
            carcass_pool: The grid-local carcass pool to which the dead matter is
                transferred.
            number_days: Number of days over which the metabolic costs should be
                calculated.

        """

        # Calculate the mortality probability for the entire time step
        time_step_mortality_prob = (
            1 - (1 - self.adult_natural_mortality_prob) ** number_days
        )
        # Draw the number of deaths from a binomial distribution
        number_of_deaths = random.binomial(
            n=self.individuals, p=time_step_mortality_prob
        )

        self.die_individual(number_of_deaths, carcass_pool)
