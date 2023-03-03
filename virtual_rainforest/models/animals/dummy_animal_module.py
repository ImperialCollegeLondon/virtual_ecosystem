"""The ''dummy animal'' module provides toy animal module functionality as well 
as self-contained dummy versions of the abiotic, soil, and plant modules that 
are required for setting up and testing the early stages of the animal module.

Todo:
- food intake, needs to be modified by number of indiv in cohort
- rework dispersal
- send portion of dead to carcass pool

Current simplifications:
- only herbivory (want: carnivory and omnivory)
- only endothermy (want: ectothermy)
- only iteroparity (want: semelparity)
- no development

Notes to self:
- assume each grid = 1 km2
- assume each tick = 1 day (28800s)
- damuth ~ 4.23*mass**(-3/4) indiv / km2
- waste_energy pool likely unnecessary, better to excrete directly to external pools
"""  # noqa: #D205, D415

from dataclasses import dataclass
from math import ceil

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.animals.constants import (
    ConversionEfficiency,
    DamuthsLaw,
    FatMass,
    IntakeRate,
    MeatEnergy,
    MetabolicRate,
    MuscleMass,
    PlantEnergyDensity,
)


class PlantCommunity:
    """This is a dummy class of plant cohorts for testing the animal module."""

    def __init__(self, mass: float, position: int) -> None:
        """The constructor for Plant class."""
        self.mass = mass
        """The mass of the plant cohort [kg]."""
        self.energy_density: float = PlantEnergyDensity.value
        """The energy (J) in a kg of plant [currently set to toy value of Alfalfa]."""
        self.energy_max: float = self.mass * self.energy_density
        """The maximum amount of energy that the cohort can have [J] [Alfalfa]."""
        self.energy = self.energy_max
        """The initial amount of energy in the plant cohort [J] [toy]."""
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
            LOGGER.warning("A Plant Community has died")
        elif not self.is_alive:
            LOGGER.warning("A Plant Community which is dead cannot die.")


@dataclass
class PalatableSoil:
    """This is a dummy class of soil pools for testing the animal module."""

    energy: float
    """The amount of energy in the soil pool [J]."""
    position: int
    """The grid position of the soil pool."""


class AnimalCohort:
    """This is a class of animal cohorts."""

    def __init__(self, name: str, mass: float, age: float, position: int) -> None:
        """The constructor for the Animal class."""
        self.name = name
        """The functional type name of the animal cohort."""
        self.mass = mass
        """The average mass of an individual in the animal cohort [kg]."""
        self.age = age
        """The age of the animal cohort [days]."""
        self.position = position
        """The grid position of the animal cohort."""
        self.individuals: int = ceil(
            DamuthsLaw.coefficient * self.mass ** (DamuthsLaw.exponent)
        )
        """The number of individuals in the cohort."""
        self.is_alive: bool = True
        """Whether the cohort is alive [True] or dead [False]."""
        self.metabolic_rate: float = (
            MetabolicRate.coefficient * (self.mass * 1000) ** MetabolicRate.exponent
        ) * 86400
        """The per-gram rate at which energy is expended modified
        to kg rate in [J/day]."""
        self.stored_energy: float = (
            (MuscleMass.coefficient * (self.mass * 1000) ** MuscleMass.exponent)
            + (FatMass.coefficient * (self.mass * 1000) * FatMass.exponent)
        ) * MeatEnergy.value
        """The initialized individual energetic reserve [J] as the sum of muscle
        mass [g] and fat mass [g] multiplied by its average energetic value."""
        self.intake_rate: float = (IntakeRate.coefficient) * self.mass ** (
            IntakeRate.exponent
        )
        """The rate of plant mass consumption over an 8hr foraging day [kg/day]."""

    def metabolize(self) -> None:
        """The function to reduce stored_energy through basal metabolism."""
        energy_burned = self.metabolic_rate
        """ J/day metabolic rate."""
        if self.stored_energy >= energy_burned:
            self.stored_energy -= energy_burned
        elif self.stored_energy < energy_burned:
            self.stored_energy = 0.0

    def eat(self, food: PlantCommunity) -> float:
        """The function to transfer energy from a food source to the animal cohort.

        Args:
            food: The targeted PlantCommunity instance from which energy is
                            transferred.

        Returns:
            A float containing the amount of energy consumed in the foraging bout.
        """
        consumed_energy = min(food.energy, self.intake_rate * food.energy_density)
        """Minimum of the energy available and amount that can be consumed in an 8 hour
        foraging window ."""
        food.energy -= consumed_energy
        self.stored_energy += (
            consumed_energy * ConversionEfficiency.value
        ) / self.individuals
        """The energy [J] extracted from the PlantCommunity adjusted for energetic
        conversion efficiency and divided by the number of individuals in the cohort."""
        return consumed_energy

    def excrete(self, soil: PalatableSoil, consumed_energy: float) -> None:
        """The function to transfer waste energy from an animal cohort to the soil.

        Args:
            soil: The local PalatableSoil pool in which waste is deposited.
            consumed_energy: The amount of energy flowing through cohort digestion.

        """
        waste_energy = consumed_energy * ConversionEfficiency.value
        soil.energy += waste_energy

    def forage(self, food: PlantCommunity, soil: PalatableSoil) -> None:
        """The function to enact multi-step foraging behaviors.

        Currently, this wraps the acts of consuming plants and excreting wastes. It will
        later wrap additional functions for selecting a food choice and navigating
        predation interactions.

        Args:
            food: The targeted PlantCommunity instance from which energy is
                            transferred.
            soil: The local PalatableSoil pool in which waste is deposited.

        """
        consumed_energy = self.eat(food)
        self.excrete(soil, consumed_energy)
