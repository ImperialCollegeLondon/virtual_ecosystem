"""The 'dummy_animal_module.

This file provides toy animal module functionality as well as self-contained
dummy versions of the abiotic, soil, and plant modules that are required for
setting up and testing the early stages of the animal module.
"""

# experimental file for figuring out how to make an animal module

# to do
# - in dispersal, move cohort between grid square lists
# - in birth, add cohort to grid square list
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


import random
from typing import List

# plant and soil classes are dummies for testing functionality w/in the animal module


class Plant:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, name: str, mass: float, position: str) -> None:
        """The constructor for Plant class.

        Args:
            name (str): The functional type name of the plant cohort.
            mass (str): The mass of the plant cohort [g].
            position (str): The grid position of the plant cohort [g0-g8].
            energy (flt): The amount of energy in the plant cohort [j] [toy].
            alive (bool): Whether the cohort is alive [True] or dead [False].
            energy_max (flt): The maximum amount of energy that the cohort
                                can have [j] [toy].

        """
        self.name = name
        self.energy = mass * 100
        self.alive = True
        self.energy_max = mass * 100
        self.position = position

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
        self.alive = False
        return f"""A {self.name} cohort died"""


class SoilPool:
    """This is a dummy class of soil pools for testing the animal module.

    Attributes:
        energy (flt): The amount of energy in the soil pool [j].
        position (str): The grid position of the soil pool [g0-g8].
    """

    def __init__(self, energy: float, position: str) -> None:
        """The constructor for Soil class.

        Args:
            energy (flt): The amount of energy in the soil pool [j].
            position (str): The grid position of the soil pool [g0-g8].
        """
        self.energy = energy
        self.position = position


class Animal:
    """This is a class of animal cohorts."""

    def __init__(self, name: str, mass: float, age: int, position: str):
        """The constructor for the Animal class.

        Args:
            name (str): The functional type name of the animal cohort.
            mass (flt): The average mass of an individual in the animal cohort [g].
            age (int): The age of the animal cohort [yrs].
            position (str): The grid position of the plant cohort [g0-g8].
            individuals (int): The number of individuals in the cohort [toy].
            alive (bool): Whether the cohort is alive [True] or dead [False].
            age_max (int): The maximum lifespan of the cohort [yrs].
            intake_rate (flt): The rate of energy gain while foraging [j/s] [toy].
            reproductive_threshold (flt): Thresh mass of a reproductive event [g].
            metabolic_rate (flt): The rate at which energy is expended to [j/s] [toy].
            stored_energy (flt): The current indiv energetic reserve [j] [toy].
            waste_energy (flt): The  energetic content of an indivs excreta [j] [toy].
        """
        self.name = name
        self.mass = mass
        self.individuals = 4.23 * self.mass ** (-3 / 4)
        self.alive = True
        self.age = age
        self.age_max = 30
        self.position = position
        # derived allometric parameters
        self.intake_rate = (10**-4) * self.mass ** (3 / 4)
        self.reproductive_threshold = self.mass * 20
        self.metabolic_rate = (10**-5) * self.mass ** (3 / 4)
        # storage pool
        self.stored_energy = self.mass * 10.0
        # internal waste pools
        self.waste_energy = 0.0

    def details(self) -> str:
        """The function to provide a written description of current animal cohort state.

        Parameters:
            None: Relies only on current internal states

        Returns:
            An description (str) of cohort: name, aliveness, age, stored energy,
                and waste energy.
        """
        return f"""This {self.name} cohort is alive? {self.alive},
                    is {self.age} years old, has {self.stored_energy}  stored energy,
                    and has: {self.waste_energy} waste energy"""

    def metabolism(self, time: float) -> None:
        """The function to change reduce stored_energy through metabolism.

        Args:
            time (flt): The amount of time over which the energy expenditure
                        occurs [s].

        Returns:
            Reduces self.stored_energy by the product of time and the metabolic_rate.
        """
        self.stored_energy -= time * self.metabolic_rate

    def eat(self, food: Plant) -> None:
        """The function to transfer energy from a food source to the animal cohort.

        Args:
            food (Plant): The targeted food instance from which energy is
                            transferred.

        Returns:
            Removes energy from the food by the minimum of available
                food energy and intake_rate. Adds 1/3 of that energy to waste_energy
                and 2/3 to stored_energy [j] [toy]
        """
        consumed_energy = min(food.energy, self.intake_rate)
        food.energy -= consumed_energy
        self.stored_energy += consumed_energy * (2 / 3)
        self.waste_energy += consumed_energy * (1 / 3)

    def excrete(self, soil: SoilPool) -> None:
        """The function to transfer energy from a the internal waste pool to the soil.

        Args:
            soil (Soil): The targeted soil pool instance to which waste energy is
                            transferred.

        Returns:
            Removes energy from the waste pool and adds it to the soil pool [j] [toy].
        """
        self.waste_energy -= self.waste_energy * 0.1
        soil.energy += self.waste_energy * 0.1

    def aging(self, time: int) -> None:
        """The function to increase the age of an animal cohort.

        Args:
            time (int): The number by which to increment the age attribute [yrs].

        Returns:
            Removes energy from the waste pool and adds it to the soil pool [j] [toy].
        """
        self.age += time

    def animal_individual_death(self, deaths: int) -> None:
        """The function to decrease the self.individuals attribute as cohort indivs die.

        Args:
            deaths (int): The number of individuals that have died

        Returns:
            Modified value of self.individuals.
        """
        self.individuals -= deaths

    def animal_cohort_death(self) -> str:
        """The function to change the self.alive state from True to False.

        Args:
            None: Toy implementation of death is only a function of the
                    current aliveness state.

        Returns:
            Modified value of self.alive.
            An alert (str) informing you the cohort has died.
        """
        self.alive = False
        return f"""A {self.name} cohort died"""

    # @classmethod
    def birth(self) -> object:
        """The function to create a new animal cohort.

        Args:
            None: Toy implementation of death is only a function of the
                    parent cohorts attributes.

        Returns:
            Creates an adult-sized animal cohort of the parental type and age 0.
        """
        return Animal(name=self.name, mass=self.mass, age=0, position=self.position)

    def disperse(self) -> None:
        """The function to move an animal cohort between grid positions.

            0 1 2
            3 4 5
            6 7 8

        Args:
            None: Toy implementation of dispersal is only a function of the
                    cohort's current position.

        Returns:
            Modifies the cohort's position by 1 random king-step.
        """
        adjacency = {
            "g0": ["g1", "g3"],
            "g1": ["g0", "g2", "g4"],
            "g2": ["g1", "g5"],
            "g3": ["g0", "g4", "g6"],
            "g4": ["g1", "g3", "g5", "g7"],
            "g5": ["g2", "g4", "g8"],
            "g6": ["g3", "g7"],
            "g7": ["g4", "g6", "g8"],
            "g8": ["g5", "g7"],
        }
        new_position = random.choice(adjacency[self.position])
        self.position = new_position
        # need to update this so that the lists like 'elephants' are auto referenced
        # index_position = grid.grid_squares[self.position].elephants.index(self)
        # grid.grid_squares[new_position].elephants.append(
        #    grid.grid_squares[self.position].elephants.pop(index_position)


class CarcassPool:
    """This is a class of carcass pools."""

    def __init__(self, energy: float, position: str) -> None:
        """The constructor for Carcass class.

        Args:
            energy (flt): The amount of energy in the carcass pool [j].
            position (str): The grid position of carcass pool pool [g0-g8].
        """
        self.energy = energy
        self.position = position


class GridSquare:
    """This is a dummy class for collecting lists of pools sharing a grid."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.soil: List[SoilPool] = []
        self.trees: List[Plant] = []
        self.carcasses: List[CarcassPool] = []
        self.beetles: List[Animal] = []
        self.elephants: List[Animal] = []

    def populate_grid_square(self) -> None:
        """The function to add one of each of the toy pools to the grid square.

        Args:
            None: Toy implementation  is only a function of the
                  hardcoded pools and cohorts.

        Returns:
            Pool and cohort list attributes containing an instance.
        """
        self.elephants.append(Animal("elephant", 10**6, 5, self.name))
        self.soil.append(SoilPool(1000, self.name))
        self.carcasses.append(CarcassPool(1000, self.name))
        self.beetles.append(Animal("beetle", 50, 0, self.name))
        self.trees.append(Plant("tree", 10.0**5, self.name))


class Grid:
    """This is a dummy class for collecting the spatial relationships of pools.

    0 1 2
    3 4 5
    6 7 8
    """

    def __init__(self) -> None:
        """The constructor for Grid class.

        Args:
            grid_squares (list): a list (str) of the grid squares present on the grid.

        """
        self.grid_squares = {
            "g0": GridSquare("g0"),
            "g1": GridSquare("g1"),
            "g2": GridSquare("g2"),
            "g3": GridSquare("g3"),
            "g4": GridSquare("g4"),
            "g5": GridSquare("g5"),
            "g6": GridSquare("g6"),
            "g7": GridSquare("g7"),
            "g8": GridSquare("g8"),
        }

    def populate_grid_squares(self) -> None:
        """The function to add one of each toy pool to each grid square in the grid.

        Args:
            None: Toy implementation  is only a function of the
                  hardcoded pools and cohorts.

        Returns:
            Pool and cohort list attributes in each square
             are populated with an containing an instance.
        """
        for square in self.grid_squares:
            self.grid_squares[square].populate_grid_square()
