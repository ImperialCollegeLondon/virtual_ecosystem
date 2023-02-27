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
    """"""


@dataclass
class MetabolicRate:
    """Toy values."""

    exponent: float = 0.75
    """"""
    coefficienct: float = 10**-5
    """"""


@dataclass
class StoredEnergy:
    """Toy values."""

    exponent: float = 0.75
    """"""
    coefficienct: float = 10
    """"""
    """ fat mass scaling = 0.02 * M ** 1.19 g"""
    """ muscle mass scaling = 0.38 * M ** 1.0 g"""
    """ Energy in unit mass = 7000 J/g"""


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
