"""This submodule contains a set of dataclasses containing core constants used across
the Virtual Rainforest.
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class CoreConsts(ConstantsDataclass):
    """Core constants for use across the :mod:`virtual_rainforest` modules."""

    k_to_c: float = 273.15
    """Conversion constant from Kelvin to Celsius (°)."""
