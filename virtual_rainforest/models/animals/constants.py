"""The `models.soil.carbon` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment only two pools are modelled, these are low molecular weight
carbon (LMWC) and mineral associated organic matter (MAOM). More pools and their
interactions will be added at a later date.
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class DamuthsLaw:
    """Toy values."""

    slope: float = -0.75
    """"""
    intercept: float = 4.23
    """"""


@dataclass
class IntakeRate:
    """Toy values."""

    slope: float = 0.75
    """"""
    intercept: float = 10**-4
    """"""


@dataclass
class ReproductiveThreshold:
    """Toy values."""

    slope: float = 0.75
    """"""
    intercept: float = 10**-4
    """"""


@dataclass
class MetabolicRate:
    """Toy values."""

    slope: float = 0.75
    """"""
    intercept: float = 10**-5
    """"""


@dataclass
class StoredEnergy:
    """Toy values."""

    slope: float = 0.75
    """"""
    intercept: float = 10
    """"""


@dataclass
class ConversionEfficiency:
    """Toy values."""

    value: float = 0.1
    """Unitless."""


@dataclass
class ExcretaProportion:
    """Toy values."""

    value: float = 0.01
    """Unitless."""
