"""This submodule contains dataclasses containing core constants used across
the Virtual Ecosystem. This includes universal constants but also constants that may be
shared across model.

Note that true universal constants are defined as class variables of dataclasses. This
prevents them being changed by user specified configuration.
"""  # noqa: D205, D415

from dataclasses import dataclass
from typing import ClassVar

from scipy import constants
from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class CoreConsts(ConstantsDataclass):
    """Core constants for use across the Virtual Ecosystem modules."""

    zero_Celsius: ClassVar[float] = constants.zero_Celsius
    """Conversion constant from Kelvin to Celsius (°)."""

    depth_of_active_soil_layer: float = 0.25
    """Depth of the biogeochemically active soil layer [m].

    The soil model considered a homogenous layer in which all significant nutrient
    processes take place. This is a major assumption of the model. The value is taken
    from :cite:t:`fatichi_mechanistic_2019`. No empirical source is provided for this
    value.
    """
