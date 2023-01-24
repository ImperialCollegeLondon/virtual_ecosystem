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
# problems with circular type definitions between grid, gridsquare, and animal

from __future__ import annotations

from math import ceil
from typing import Any, List

# import random
import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER  # , log_and_raise
from virtual_rainforest.core.model import BaseModel, InitialisationError

# plant and soil classes are dummies for testing functionality w/in the animal module


class AnimalModel(BaseModel, model_name="animal"):
    """A class describing the animal model.

    Describes the specific functions and attributes that the animal module should
    possess.

    Args:
        update_interval: Time to wait between updates of the model state.


    Attributes:
        name: Names the model that is described.
        grid: The spatial grid over which the model is run, currently fixed 3x3.
        #     0 1 2
        #     3 4 5
        #     6 7 8
    """

    name = "animal"

    def __init__(
        self,
        update_interval: timedelta64,
        start_time: datetime64,
        # no_layers: int,
        **kwargs: Any,
    ):

        self.animal_list: List[Animal] = []
        self.plant_list: List[Plant] = []
        self.soil_list: List[SoilPool] = []
        self.carcass_list: List[CarcassPool] = []
        self.grid = Grid(grid_type="square", cell_area=9, cell_nx=3, cell_ny=3)

        super().__init__(update_interval, start_time, **kwargs)
        # self.no_layers = int(no_layers)
        # Save variables names to be used by the __repr__
        # self._repr.append("no_layers")

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> BaseModel:
        """Factory function to initialise the animal model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            config: The complete (and validated) virtual rainforest configuration.

        Raises:
            InitialisationError: If configuration data can't be properly converted
        """

        # Assume input is valid until we learn otherwise
        valid_input = True
        try:
            raw_interval = pint.Quantity(config["soil"]["model_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")
            start_time = datetime64(config["core"]["timing"]["start_time"])
        except (
            ValueError,
            pint.errors.DimensionalityError,
            pint.errors.UndefinedUnitError,
        ) as e:
            valid_input = False
            LOGGER.error(
                "Configuration types appear not to have been properly validated. This "
                "problem prevents initialisation of the soil model. The first instance"
                " of this problem is as follows: %s" % str(e)
            )

        if valid_input:
            LOGGER.info(
                "Information required to initialise the soil model successfully "
                "extracted."
            )
            return cls(update_interval, start_time)
        else:
            raise InitialisationError()

    # THIS IS BASICALLY JUST A PLACEHOLDER TO DEMONSTRATE HOW THE FUNCTION OVERWRITING
    # SHOULD WORK
    # AT THIS STEP COMMUNICATION BETWEEN MODELS CAN OCCUR IN ORDER TO DEFINE INITIAL
    # STATE
    def setup(self) -> None:
        """Function to set up the soil model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def update(self) -> None:
        """Placeholder function to solve the soil model."""

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""

    def populate_pool_lists(self) -> None:
        """The function to add one of each of the toy pools to the pool lists.

        Args:
            None: Toy implementation  is only a function of the
                  hardcoded pools and cohorts.

        Returns:
             Pool and cohort list attributes containing an instance.
        """
        for grid in range(9):
            self.animal_list.append(Animal("elephant", 10**6, 5, grid))
            self.soil_list.append(SoilPool(1000, grid))
            self.carcass_list.append(CarcassPool(1000, grid))
            self.animal_list.append(Animal("beetle", 50, 0, grid))
            self.plant_list.append(Plant("tree", 10.0**5, grid))


class Plant:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, name: str, mass: float, position: int) -> None:
        """The constructor for Plant class.

        Args:
            name (str): The functional type name of the plant cohort.
            mass (str): The mass of the plant cohort [g].
            position (int): The grid position of the plant cohort [0-8].
            energy (flt): The amount of energy in the plant cohort [j] [toy].
            alive (bool): Whether the cohort is alive [True] or dead [False].
            energy_max (flt): The maximum amount of energy that the cohort
                                can have [j] [toy].

        """
        self.name = name
        self.energy = mass * 100
        self.alive = "alive"
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
        self.alive = "dead"
        return f"""A {self.name} cohort died"""


class SoilPool:
    """This is a dummy class of soil pools for testing the animal module.

    Attributes:
        energy (flt): The amount of energy in the soil pool [j].
        position (int): The grid position of the soil pool [g0-g8].
    """

    def __init__(self, energy: float, position: int) -> None:
        """The constructor for Soil class.

        Args:
            energy (flt): The amount of energy in the soil pool [j].
            position (int): The grid position of the soil pool [0-8].
        """
        self.energy = energy
        self.position = position


class Animal:
    """This is a class of animal cohorts."""

    def __init__(self, name: str, mass: float, age: int, position: int):
        """The constructor for the Animal class.

        Args:
            name (str): The functional type name of the animal cohort.
            mass (flt): The average mass of an individual in the animal cohort [g].
            age (int): The age of the animal cohort [yrs].
            position (int): The grid position of the plant cohort [0-8].
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
        self.individuals = ceil(4.23 * self.mass ** (-3 / 4) * 1000000)
        self.alive = "alive"
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
        return f"""This {self.name} cohort is {self.alive},
                   is {self.age} years old, has {self.stored_energy}  stored energy,
                   and has: {self.waste_energy} waste energy."""

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
        excreted_energy = self.stored_energy * 0.01
        self.stored_energy -= excreted_energy
        soil.energy += excreted_energy

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
        self.alive = "dead"
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

    def disperse(self, grid: Grid) -> None:
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
        # the following is commented out until disersal is reworked for Grid
        # adjacency = {
        #     "g0": ["g1", "g3"],
        #     "g1": ["g0", "g2", "g4"],
        #     "g2": ["g1", "g5"],
        #     "g3": ["g0", "g4", "g6"],
        #     "g4": ["g1", "g3", "g5", "g7"],
        #     "g5": ["g2", "g4", "g8"],
        #     "g6": ["g3", "g7"],
        #     "g7": ["g4", "g6", "g8"],
        #     "g8": ["g5", "g7"],
        # }
        # old_position = self.position
        # new_position = random.choice(adjacency[self.position])
        # self.position = new_position
        # old_animal_list = grid.grid_squares[old_position].elephants
        # index = old_animal_list.index(self)
        # new_animal_list = grid.grid_squares[new_position].elephants
        # new_animal_list.append(old_animal_list.pop(index))

        # need to update this so that the lists like 'elephants' are auto referenced
        # index_position = grid.grid_squares[self.position].elephants.index(self)
        # grid.grid_squares[new_position].elephants.append(
        #    grid.grid_squares[self.position].elephants.pop(index_position)


class CarcassPool:
    """This is a class of carcass pools."""

    def __init__(self, energy: float, position: int) -> None:
        """The constructor for Carcass class.

        Args:
            energy (flt): The amount of energy in the carcass pool [j].
            position (int): The grid position of carcass pool pool [0-8].
        """
        self.energy = energy
        self.position = position
