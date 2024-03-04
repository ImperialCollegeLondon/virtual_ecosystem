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
    """Core constants for use across the Virtual Rainforest modules."""

    placeholder: float = 123.4
    """A placeholder configurable constant."""

    zero_Celsius: ClassVar[float] = constants.zero_Celsius
    """Conversion constant from Kelvin to Celsius (°)."""

    standard_pressure: float = constants.atmosphere / 1000
    """Standard atmospheric pressure, [kPa]"""

    standard_mole: float = 44.642
    """Moles of ideal gas in 1 m^3 air at standard atmosphere."""

    molar_heat_capacity_air: float = 29.19
    """Molar heat capacity of air, [J mol-1 K-1]."""

    gravity: float = constants.gravitational_constant
    """Newtonian constant of gravitation, [m s-1]."""

    stefan_boltzmann_constant: float = constants.Stefan_Boltzmann
    """Stefan-Boltzmann constant, [W m-2 K-4].

    The Stefan-Boltzmann constant relates the energy radiated by a black body to its
    temperature."""

    von_karmans_constant: float = 0.4
    """Von Karman's constant, [unitless].

    The von Karman's constant describes the logarithmic velocity profile of a turbulent
    fluid near a no-slip boundary."""

    depth_of_active_soil_layer: float = 0.25
    """Depth of the biogeochemically active soil layer [m].

    The soil model considered a homogenous layer in which all significant nutrient
    processes take place. This is a major assumption of the model. The value is taken
    from :cite:t:`fatichi_mechanistic_2019`. No empirical source is provided for this
    value.
    """

    meters_to_mm: float = 1000.0
    """Factor to convert variable unit from meters to millimeters."""

    molecular_weight_air: float = 28.96
    """Molecular weight of air, [g mol-1]."""

    gas_constant_water_vapour: float = 461.51
    """Gas constant for water vapour, [J kg-1 K-1]"""

    seconds_to_day: float = 86400.0
    """Factor to convert variable unit from seconds to day."""

    characteristic_dimension_leaf: float = 0.01
    """Characteristic dimension of leaf, typically around 0.7 * leaf width, [m]."""
