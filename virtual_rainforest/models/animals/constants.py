"""The `models.animals.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class DamuthsLaw:
    """From (Damuth 1987)."""

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
