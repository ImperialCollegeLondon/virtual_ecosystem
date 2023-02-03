"""The 'dummy_animal_module.

This file provides toy animal module functionality as well as self-contained
dummy versions of the abiotic, soil, and plant modules that are required for
setting up and testing the early stages of the animal module.
"""

# experimental file for figuring out how to make an animal module

# to do
# - rework dispersal
# - send portion of dead to carcass pool

# current simplifications
# - only herbivory (want: carnivory and omnivory)
# - only endothermy (want: ectothermy)
# - only iteroparity (want: semelparity)
# - no development

# notes to self
# assume each grid = 1 km2
# assume each tick = 1 day (28800s)
# damuth ~ 4.23*mass**(-3/4) indiv / km2
# waste_energy pool likely unnecessary
#   better to excrete directly to external pools
# only elephants disperse atm


from virtual_rainforest.core.logger import LOGGER


class PlantCommunity:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, mass: float, position: int) -> None:
        """The constructor for Plant class."""
        self.mass = mass
        """The mass of the plant cohort [kg]."""
        self.energy_density: float = 1000.0
        """The energy (J) in a kg of plant. [small toy J/kg value for convenience.]"""
        self.energy_max: float = self.mass * self.energy_density
        """The maximum amount of energy that the cohort can have [J] [toy]."""
        self.energy = self.energy_max
        """The amount of energy in the plant cohort [J] [toy]."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.position = position
        """The grid location of the cohort [0-8]."""

    def grow(self) -> None:
        """The function to logistically modify cohort energy to the energy_max value.

        Args:
            None: Toy implementation of growth is only a function of the
                  current energy state.

        """
        self.energy += 1 * self.energy * (1 - self.energy / self.energy_max)

    def die(self) -> None:
        """The function to kill a plant cohort.

        Parameters:
            None: Toy implementation of death is only a function of the
                    current aliveness state.

        """
        self.is_alive = False
        LOGGER.debug("A Plant Community has died")


class SoilPool:
    """This is a dummy class of soil pools for testing the animal module."""

    def __init__(self, energy: float, position: int) -> None:
        """The constructor for Soil class."""
        self.energy = energy
        """The amount of energy in the soil pool [j]."""
        self.position = position
        """The grid position of the soil pool [0-8]."""


class CarcassPool:
    """This is a class of carcass pools."""

    def __init__(self, energy: float, position: int) -> None:
        """The constructor for Carcass class."""
        self.energy = energy
        """The amount of energy in the carcass pool [j]."""
        self.position = position
        """The grid position of carcass pool pool [0-8]."""
