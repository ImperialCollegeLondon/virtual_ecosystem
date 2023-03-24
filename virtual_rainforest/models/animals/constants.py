"""The `models.animals.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class Term:
    """Dataclass for handling the terms of scaling equations."""

    exponent: float
    """Handles the exponent on body-mass for scaling equations."""
    coefficient: float
    """Handles the coefficient of scaling equations"""


"""From (Damuth 1987)."""
DamuthsLaw = Term(-0.75, 4.23)

"""Toy values."""
MetabolicRate = Term(0.75, 10**-5)

"""Toy values."""
StoredEnergy = Term(0.75, 10)
