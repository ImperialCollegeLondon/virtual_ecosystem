"""This submodule contains dataclasses containing core constants used across
the Virtual Ecosystem. This includes universal constants but also constants that may be
shared across model.

Note that true universal constants are defined as class variables of dataclasses. This
prevents them being changed by user specified configuration.
"""  # noqa: D205

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from scipy import constants

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class CoreConsts(ConstantsDataclass):
    """Core constants for use across the Virtual Ecosystem modules.

    An instance of the CoreConsts dataclass provides definitions of the core constants
    used across an entire simulation. The core constants can be changed, as shown below,
    although for many this would likely generate nonsensical results.

    Example:
        >>> consts = CoreConsts()
        >>> consts.max_depth_of_microbial_activity
        0.25
        >>> consts = CoreConsts(max_depth_of_microbial_activity=0.75)
        >>> consts.max_depth_of_microbial_activity
        0.75
    """

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

    max_depth_of_microbial_activity: float = 0.25
    """Maximum depth of microbial activity in the soil layers [m].

    The soil model needs to identify which of the configured soil layers are
    sufficiently close to the surface to contain significant microbial activity that
    drives nutrient processes. The default value is taken from
    :cite:t:`fatichi_mechanistic_2019`. No empirical source is provided for this value.
    """

    meters_to_mm: float = 1000.0
    """Factor to convert variable unit from meters to millimeters."""

    molecular_weight_air: float = 28.96
    """Molecular weight of air, [g mol-1]."""

    gas_constant_water_vapour: float = 461.51
    """Gas constant for water vapour, [J kg-1 K-1]"""

    seconds_to_day: float = 86400.0
    """Factor to convert variable unit from seconds to day."""

    seconds_to_hour: float = 3600.0
    """Factor to convert variable unit from seconds to hours."""

    characteristic_dimension_leaf: float = 0.01
    """Characteristic dimension of leaf, typically around 0.7 * leaf width, [m]."""

    specific_gas_constant_dry_air: float = 287.05
    """Specific gas constant for dry air, [J kg-1 K-1]."""

    molecular_weight_ratio_water_to_dry_air: float = 0.622
    """The molecular weight ratio of water to dry air.
    
    The ratio of the molar mass of water vapour (18.015 g/mol) to the molar mass of dry
    air (28.964 g/mol), which is approximately 0.622. This ratio is used in atmospheric
    calculations, particularly in determining the mixing ratio of water vapour to dry
    air."""

    conductance_to_resistance_conversion_factor: float = 40.9
    """Conductance to resistance conversion factor.
    
    This factor is used to convert between stomatal conductance in mmol m-2 s-1 and
    stomatal resistance in s m-1."""

    density_water: float = 1000.0
    """Density of water, [kg m-3]."""

    fungal_fruiting_bodies_c_n_ratio: float = 10.0
    """Carbon to nitrogen ratio of fungal fruiting bodies, [unitless].
    
    This constant is stored in the CoreConsts as it is used by both the animal model
    (to work out consumption flows) and the soil model (to work out production rates).
    The current default value is very much a guess.
    """

    fungal_fruiting_bodies_c_p_ratio: float = 75.0
    """Carbon to phosphorus ratio of fungal fruiting bodies, [unitless].
    
    This constant is stored in the CoreConsts as it is used by both the animal model (to
    work out consumption flows) and the soil model (to work out production rates). The
    current default value is very much a guess.
    """

    fungal_fruiting_bodies_decay_rate: float = np.log(2) / 50.0
    """Rate constant for the decay of fungal fruiting bodies, [day^-1].
    
    This is calculated based on the assumption that fungal fruiting bodies decay with a
    half-life of 50 days. This estimate should be improved based on empirical data.
    """
