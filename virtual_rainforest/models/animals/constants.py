"""The `models.animals.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class DamuthsLaw:
    """Mammalian herbivore population density, observed allometry (Damuth 1987)."""

    exponent: float = -0.75
    """"""
    coefficienct: float = 4.23
    """indiv/(km2*kg)"""


@dataclass
class MetabolicRate:
    """Temporary basal metabolic rate values for mammals (citation from Rallings)."""

    exponent: float = 0.75
    """"""
    coefficienct: float = 0.047
    """ 0.047 J/sg"""


@dataclass
class FatMass:
    """Scaling of mammalian herbivore fat mass (citation from Rallings)."""

    exponent: float = 1.19
    """"""
    coefficient: float = 0.02
    """[g/g]"""


@dataclass
class MuscleMass:
    """Scaling of mammalian herbivore muscle mass (citation from Rallings)."""

    exponent: float = 1.0
    """"""
    coefficient: float = 0.38
    """[g/g]"""


@dataclass
class MeatEnergy:
    """The energy of a unit mass of mammal meat (check citation from Rallings)."""

    value: float = 7000.0
    """[J/g] """


@dataclass
class IntakeRate:
    """Mammalian maximum intake rate (kg/day) from (Shipley 1994)."""

    exponent: float = 0.71
    """"""
    coefficienct: float = (0.63 * 480) * (1 / 1000)
    """ Converts original g/min rate to kg/day where 'day' is an 8hr foraging window."""


@dataclass
class ConversionEfficiency:
    """Toy values."""

    value: float = 0.1
    """Unitless."""


@dataclass
class PlantEnergyDensity:
    """Alfalfa ¬ 18,200,000 J/kg DM."""

    value: float = 18200000.0
    """"""
