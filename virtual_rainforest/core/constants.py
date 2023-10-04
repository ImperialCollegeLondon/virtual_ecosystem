"""This submodule contains dataclasses containing core constants used across
the Virtual Rainforest. This includes universal constants but also constants that may be
shared across model.
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class CoreConsts(ConstantsDataclass):
    """Core constants for use across the :mod:`virtual_rainforest` modules."""

    k_to_c: float = 273.15
    """Conversion constant from Kelvin to Celsius (°)."""
