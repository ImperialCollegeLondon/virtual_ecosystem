"""The ''dummy_plants'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: #D205, D415

from __future__ import annotations

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.protocols import Consumer, DecayPool


class PlantCommunity:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, mass_max: float) -> None:
        """The constructor for Plant class."""
        self.mass_max = mass_max
        """The mass of the plant cohort [kg]."""
        self.mass_current = self.mass_max
        """The amount of energy in the plant cohort [J] [toy]."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""

    def grow(self) -> None:
        """The function to logistically modify cohort mass to the mass_max value."""
        self.mass_current += self.mass_current * (1 - self.mass_current / self.mass_max)

    def die(self) -> None:
        """The function to kill a plant cohort."""
        if self.is_alive:
            self.is_alive = False
            LOGGER.info("A Plant Community has died")
        elif not self.is_alive:
            LOGGER.warning("A Plant Community which is dead cannot die.")

    def get_eaten(self, herbivore: Consumer, excrement_pool: DecayPool) -> float:
        """This function removes energy from a PlantCommunity and through herbivory.

        Args:
            herbivore: The AnimalCohort preying on the PlantCommunity
            excrement_pool: The resident pool of detritus to which the remains of excess
                plant material is lost.

        Returns:
            A float of the energy value of the consumed plants after mechanical and
            digestive efficiencies are accounted for.

        """

        # Minimum of the energy available and amount that can be consumed in an 8 hour
        # foraging window .
        mass_consumed = min(
            self.mass_current,
            herbivore.intake_rate * herbivore.individuals,
        )

        self.mass_current -= mass_consumed

        # TODO - All plant matter that animals fail to eat currently goes into the
        # excrement pool. This isn't ideal, but will do for now. This herbivore
        # contribution to litter fall should be handled by the plant model in future.
        excrement_pool.decomposed_energy += mass_consumed * (
            1 - herbivore.functional_group.mechanical_efficiency
        )

        # Return the net mass gain of herbivory
        return (
            mass_consumed
            * herbivore.functional_group.conversion_efficiency
            * herbivore.functional_group.mechanical_efficiency
        )
