"""The `abiotic.radiation` module.

The radiation module calculates the radiation balance of the Virtual Rainforest. This
includes the shortwave radiation that reaches the top of the canopy, the shortwave
radiation that reaches the forest floor after penetrating through the canopy, and the
longwave radiation that is emitted by the canopy and the forest floor.

The top of canopy net shortwave radiation at a given location depends on

1. extra-terrestrial radiation (affected by the earth's orbit, date, and location),

2. terrestrial radiation (affected by atmospheric composition and clouds),

3. topography (elevation, slope and aspect),

4. surface albedo (vegetation type and fraction of vegetation/bare soil), and

5. emitted longwave radiation.

The preprocessing module takes extra-terrestrial radiation as an input and adjusts for
the effects of topography (slope and aspect). Here, the effects of atmospheric
filtering (elevation-dependent) and cloud cover are added to calculate photosynthetic
photon flux density (PPFD) at the top of the canopy which is a crucial input to the
plant module. The implementation is based on :cite:t:`Davis2017`.

Cloud cover and surface albedo also determine how much of the shortwave radiation that
reaches the top of the canopy is reflected and how much remains to be absorbed via
photosynthesis and re-emitted as longwave radiation by vegetation and forest floor.
Scattering and re-absorption of longwave radiation are not considered at this stage.

# the following structural components are not implemented yet
TODO include time dimension
TODO logging, raise errors
TODO sanity checks
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

import numpy as np
from numpy.typing import NDArray

# from core.constants import CONSTANTS as C
# this doesn't exist yet; optional scipy
CLOUDY_TRANSMISSIVITY = 0.25
"""Cloudy transmittivity :cite:p:`Linacre1968`"""
TRANSMISSIVITY_COEFFICIENT = 0.50
"""Angular coefficient of transmittivity :cite:p:`Linacre1968`"""
FLUX_TO_ENERGY = 2.04
"""From flux to energy conversion, umol/J :cite:p:`Meek1984`"""
STEFAN_BOLTZMANN_CONSTANT = 5.67e-8
"""Stefan-Boltzmann constant W m-2 K-4"""
SOIL_EMISSIVITY = 0.95
"""Soil emissivity, default for tropical rainforest"""
CANOPY_EMISSIVITY = 0.95
"""Canopy emissivity, default for tropical rainforest"""
BEER_REGRESSION = 2.67e-5
"""Parameter in equation for atmospheric transmissivity based on regression of Beer’s
radiation extinction function :cite:p:`Allen1996`"""
CELSIUS_TO_KELVIN = 273.15
"""Factor to convert temperature in Celsius to absolute temperature in Kelvin"""
SECOND_TO_DAY = 86400
"""Factor to convert between days and seconds."""

# dummy data object
data: Dict[str, Any] = {
    "elevation": 100,
    "shortwave_in": 30000000,
    "canopy_temperature": NDArray([25, 22, 20], dtype=np.float32),
    "surface_temperature": 20,
    "canopy_absorption": NDArray([300, 200, 100], dtype=np.float32),
}


@dataclass
class Radiation:
    """Radiation balance dataclass.

    The class stores the following attributes:
    * Elevation, [m]
    * Daily top of canopy downward shortwave radiation, [J m-2]
    * Daily top of canopy photosynthetic photon flux density,[mol m-2]
    * Daily longwave radiation from n individual canopy layers [J m-2]
    * Daily longwave radiation from soil [J m-2]
    * Daily net shortwave radiation at the surface (= forest floor)[J m-2]

    Args:
        shortwave_in: daily downward shortwave radiation[J m-2] # from data
        canopy_temperature: canopy temperature of n layers [C] # from data
        surface_temperature: surface soil temperature [C] # from data
        sunshine_fraction: fraction of sunshine hours, between 0
            (100% cloud cover) and 1 (cloud free sky)
        canopy_absorption: absorption by canopy [J m-2] # from data
        albedo_vis: visible light albedo, default = 0.03
        albedo_shortwave: shortwave albedo, default = 0.17
    """

    elevation: NDArray[np.float32] = data["elevation"]
    """Elevation above sea level, [m]"""
    ppfd: NDArray[np.float32] = field(init=False)
    """Daily top of canopy photosynthetic photon flux density, [mol m-2]"""
    topofcanopy_radiation: NDArray[np.float32] = field(init=False)
    """Daily top of canopy downward shortwave radiation, [J m-2]"""
    longwave_canopy: NDArray[np.float32] = field(init=False)
    """Daily longwave radiation from n individual canopy layers, [J m-2]"""
    longwave_soil: NDArray[np.float32] = field(init=False)
    """Daily longwave radiation from soil, [J m-2]"""
    netradiation_surface: NDArray[np.float32] = field(init=False)
    """Daily net shortwave radiation at the surface (= forest floor), [J m-2]"""

    def __post_init__(self) -> None:
        """Post init method populates radiation balance attributes."""

        self.ppfd = calculate_ppfd(data["shortwave_in"], data["elevation"])
        self.topofcanopy_radiation = calculate_topofcanopy_radiation(
            data["shortwave_in"], data["elevation"]
        )
        self.longwave_canopy, self.longwave_soil = calculate_longwave_radiation(
            data["canopy_temperature"], data["surface_temperature"]
        )
        self.netradiation_surface = calculate_netradiation_surface(
            self.topofcanopy_radiation,
            data["canopy_absorption"],
            self.longwave_canopy,
            self.longwave_soil,
        )


# helper functions
def calculate_atmospheric_transmissivity(
    elevation: NDArray[np.float32],
    sunshine_fraction: NDArray[np.float32] = np.array(1.0, dtype=np.float32),
    cloudy_transmissivity: float = CLOUDY_TRANSMISSIVITY,
    transmissivity_coefficient: float = TRANSMISSIVITY_COEFFICIENT,
    beer_regression: float = BEER_REGRESSION,
) -> NDArray[np.float32]:
    """Calculate atmospheric transmissivity (tau).

    Args:
        elevation: elevation, [m]
        sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
            and 1 (cloud free sky)
        cloudy_transmissivity, default = CLOUDY_TRANSMISSIVITY,
        transmissivity_coefficient, default = TRANSMISSIVITY_COEFFICIENT,
        beer_regression, default = BEER_REGRESSION,

    Returns:
        atmospheric transmissivity (tau), unitless
    """

    # check sunshine fraction between 0 and 1
    if 0 >= sunshine_fraction >= 1:
        raise ValueError("The fraction of sunshine hours needs to be between 0 and 1!")

    # calculate transmissivity (tau), unitless
    tau_o = cloudy_transmissivity + transmissivity_coefficient * sunshine_fraction
    return tau_o * (1.0 + beer_regression * elevation)


def calculate_ppfd(
    shortwave_in: NDArray[np.float32],
    elevation: NDArray[np.float32],
    sunshine_fraction: NDArray[np.float32] = np.array(1.0, dtype=np.float32),
    albedo_vis: NDArray[np.float32] = np.array(0.03, dtype=np.float32),
    flux_to_energy: float = FLUX_TO_ENERGY,
) -> NDArray[np.float32]:
    """Calculate top of canopy photosynthetic photon flux density [mol m-2].

    Args:
        shortwave_in: daily downward shortwave radiation [J m-2]
        elevation: elevation [m]
        sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
            and 1 (cloud free sky)
        albedo_vis: visible light albedo, default = 0.03
        flux_to_energy = FLUX_TO_ENERGY,

    Returns:
        ppfd: photosynthetic photon flux density [mol m-2]

    Reference: :cite:t:`Davis2017`
    """

    # Calculate daily photosynth. photon flux density (ppfd_d), mol/m^2
    tau = calculate_atmospheric_transmissivity(elevation, sunshine_fraction)
    return (1.0e-6) * flux_to_energy * (1.0 - albedo_vis) * tau * shortwave_in


def calculate_topofcanopy_radiation(
    shortwave_in: NDArray[np.float32],
    elevation: NDArray[np.float32],
    sunshine_fraction: NDArray[np.float32] = np.array(1.0, dtype=np.float32),
    albedo_shortwave: NDArray[np.float32] = np.array(0.17, dtype=np.float32),
) -> NDArray[np.float32]:
    """Calculate top of canopy shortwave radiation [J m-2].

    Args:
        shortwave_in: daily downward shortwave radiation [J m-2]
        elevation: elevation [m]
        sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
            and 1 (cloud free sky)
        albedo_shortwave: shortwave albedo, default = 0.17

    Returns:
        top of canopy radiation shortwave radiation [J m-2]
    """
    tau = calculate_atmospheric_transmissivity(elevation, sunshine_fraction)
    return (1.0 - albedo_shortwave) * tau * shortwave_in


def calculate_longwave_radiation(
    canopy_temperature: NDArray[np.float32],
    surface_temperature: NDArray[np.float32],
    canopy_emissivity: float = CANOPY_EMISSIVITY,
    soil_emissivity: float = SOIL_EMISSIVITY,
    stefan_boltzmann_constant: float = STEFAN_BOLTZMANN_CONSTANT,
    celsius_to_kelvin: float = CELSIUS_TO_KELVIN,
) -> Tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Calculates longwave emission from canopy and forest floor [J m-2].

    Args:
        canopy_temperature: canopy temperature of n layers [C]; the array size is
            set to max number of layers (n_max) and filled with NaN where n < n_max
        surface_temperature: surface soil temperature [C]
        canopy_emissivity: CANOPY_EMISSIVITY,
        soil_emissivity: SOIL_EMISSIVITY
        stefan_boltzmann_constant: STEFAN_BOLTZMANN_CONSTANT,
        celsius_to_kelvin: CELSIUS_TO_KELVIN,

    Returns:
        longwave_canopy: longwave radiation from n individual canopy layers, [J m-2]
        longwave_soil: longwave radiation from soil, [J m-2]

    """
    # longwave emission canopy
    longwave_canopy = (
        canopy_emissivity
        * stefan_boltzmann_constant
        * (celsius_to_kelvin + canopy_temperature) ** 4
    )

    # longwave emission surface
    longwave_soil = (
        soil_emissivity
        * stefan_boltzmann_constant
        * (celsius_to_kelvin + surface_temperature) ** 4
    )

    return longwave_canopy, longwave_soil


def calculate_netradiation_surface(
    topofcanopy_radiation: NDArray[np.float32],
    canopy_absorption: NDArray[np.float32],
    longwave_canopy: NDArray[np.float32],
    longwave_soil: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculates daily net radiation at the forest floor [J m-2].

    Args:
        topofcanopy_radiation: [J m-2]
        canopy_absorption: absorption by canopy layers, [J m-2]
        longwave_canopy: [J m-2]
        longwave_soil: [J m-2]

    Returns:
        netradiation_surface
    """
    return (
        topofcanopy_radiation
        - canopy_absorption
        - longwave_soil
        - np.sum(longwave_canopy)
    )
