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


class Plant:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, name: str, mass: float, position: int) -> None:
        """The constructor for Plant class."""
        self.name = name
        """The functional-type name of the plant cohort."""
        self.mass = mass
        """The mass of the plant cohort [g]."""
        self.energy = mass * 100
        """The amount of energy in the plant cohort [j] [toy]."""
        self.alive = "alive"
        """Whether the cohort is alive [True] or dead [False]."""
        self.energy_max = mass * 100
        """The maximum amount of energy that the cohort can have [j] [toy]."""
        self.position = position
        """The grid location of the cohort [0-8]."""

    def plant_growth(self) -> None:
        """The function to logistically modify cohort energy to the energy_max value.

        Args:
            None: Toy implementation of growth is only a function of the
                  current energy state.

        Returns:
            Modified value of self.energy
        """
        self.energy += 1 * self.energy * (1 - self.energy / self.energy_max)

    def plant_death(self) -> str:
        """The function to change the self.alive state from True to False.

        Parameters:
            None: Toy implementation of death is only a function of the
                    current aliveness state.

        Returns:
            Modified value of self.alive.
            An alert (str) informing you the cohort has died.
        """
        self.alive = "dead"
        return f"""A {self.name} cohort died"""


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
