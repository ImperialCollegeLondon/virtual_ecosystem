"""The ''dummy_plands_and_soil'' classes provides toy plant and soil module functionality 
that  are required for setting up and testing the early stages of the animal module.

"""  # noqa: #D205, D415

from __future__ import annotations

from dataclasses import dataclass

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.constants import ENERGY_DENSITY
from virtual_rainforest.models.animals.protocols import Consumer, Pool


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
        self.stored_energy = self.energy_max
        """The amount of energy in the plant cohort [J] [toy]."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.position = position
        """The grid location of the cohort."""

    def grow(self) -> None:
        """The function to logistically modify cohort energy to the energy_max value."""
        self.stored_energy += self.stored_energy * (
            1 - self.stored_energy / self.energy_max
        )

    def die(self) -> None:
        """The function to kill a plant cohort."""
        if self.is_alive:
            self.is_alive = False
            LOGGER.info("A Plant Community has died")
        elif not self.is_alive:
            LOGGER.warning("A Plant Community which is dead cannot die.")

    def get_eaten(self, herbivore: Consumer, soil_pool: Pool) -> float:
        """This function removes energy from a PlantCommunity and through herbivory.

        Args:
            herbivore: The AnimalCohort preying on the PlantCommunity
            soil_pool: The resident pool of detritus to which the remains of excess
                plant material is lost.

        Returns:
            A float of the energy value of the consumed plants after mechanical and
            digestive efficiencies are accounted for.

        """

        # Minimum of the energy available and amount that can be consumed in an 8 hour
        # foraging window .
        consumed_energy = min(
            self.stored_energy,
            herbivore.intake_rate * self.energy_density * herbivore.individuals,
        )

        self.stored_energy -= consumed_energy

        soil_pool.stored_energy += consumed_energy * (
            1 - herbivore.functional_group.mechanical_efficiency
        )

        # Return the net energetic gain of herbivory
        return (
            consumed_energy
            * herbivore.functional_group.conversion_efficiency
            * herbivore.functional_group.mechanical_efficiency
        )


@dataclass
class PalatableSoil:
    """This is a dummy class of soil pools for testing the animal module."""

    stored_energy: float
    """The amount of energy in the soil pool [J]."""
    position: int
    """The grid position of the soil pool."""
