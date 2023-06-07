"""The ''dummy_plands_and_soil'' classes provides toy plant and soil module functionality 
that  are required for setting up and testing the early stages of the animal module.

"""  # noqa: #D205, D415

from __future__ import annotations

from dataclasses import dataclass

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.constants import ENERGY_DENSITY


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
