"""This submodule contains dataclasses containing core constants used across
the Virtual Rainforest. This includes universal constants but also constants that may be
shared across model.

Note that true universal constants are defined as class variables of dataclasses. This
prevents them being changed by user specified configuration.
"""  # noqa: D205, D415

from dataclasses import dataclass
from typing import ClassVar

from scipy import constants

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class CoreConsts(ConstantsDataclass):
    """Core constants for use across the :mod:`virtual_rainforest` modules."""

    zero_Celsius: ClassVar[float] = constants.zero_Celsius
    """Conversion constant from Kelvin to Celsius (°)."""
