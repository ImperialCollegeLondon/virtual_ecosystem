"""The `abiotic.radiation` module.

The radiation module calculates the radiation balance of the Virtual Rainforest.
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

The radiation balance is calculated with the radiation_balance() function. At the
moment, this happens at a daily timestep.

# the following structural components are not implemented yet
TODO include time dimension
TODO logging, raise errors
"""

# from typing import Optional
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
BOLZMAN_CONSTANT = 5.67e-8
"""Stephan Bolzman constant W m-2 K-4"""
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


class Radiation:
    """Radiation balance."""

    def __init__(self, elevation: NDArray[np.float32]) -> None:
        """Initializes point-based radiation method."""

        self.elevation = elevation
        """Elevation above sea level, [m]"""

        # populated later
        self.ppfd = NDArray[np.float32]
        """Daily top of canopy photosynthetic photon flux density, [mol m-2]"""
        self.topofcanopy_radiation = NDArray[np.float32]
        """Daily top of canopy downward shortwave radiation, [J m-2]"""
        self.longwave_canopy = NDArray[np.float32]
        """Daily longwave radiation from n individual canopy layers, [J m-2]"""
        self.longwave_soil = NDArray[np.float32]
        """Daily longwave radiation from soil, [J m-2]"""
        self.netradiation_surface = NDArray[np.float32]
        """Daily net shortwave radiation at the surface (= forest floor), [J m-2]"""

    def calc_ppfd(
        self,
        shortwave_in: NDArray[np.float32],
        sunshine_fraction: NDArray[np.float32] = np.array(1.0, dtype=np.float32),
        albedo_vis: NDArray[np.float32] = np.array(0.03, dtype=np.float32),
    ) -> NDArray[np.float32]:
        """Calculates top of canopy photosynthetic photon flux density [mol m-2].

        Args:
            shortwave_in: daily downward shortwave radiation [J m-2]
            sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
                and 1 (cloud free sky)
            albedo_vis: visible light albedo, default = 0.03

        Returns:
            tau: atmospheric transmissivity, unitless

        Reference: :cite:t:`Davis2017`
        """
        # calculate transmissivity (tau), unitless
        tau_o = CLOUDY_TRANSMISSIVITY + TRANSMISSIVITY_COEFFICIENT * sunshine_fraction
        tau = tau_o * (1.0 + BEER_REGRESSION * self.elevation)

        # Calculate daily photosynth. photon flux density (ppfd_d), mol/m^2
        self.ppfd = (1.0e-6) * FLUX_TO_ENERGY * (1.0 - albedo_vis) * tau * shortwave_in
        return tau

    def calc_topofcanopy_radiation(
        self,
        tau: NDArray[np.float32],
        shortwave_in: NDArray[np.float32],
        sunshine_fraction: NDArray[np.float32] = np.array(1.0, dtype=np.float32),
        albedo_shortwave: NDArray[np.float32] = np.array(0.17, dtype=np.float32),
    ) -> None:
        """Calculate top of canopy shortwave radiation [J m-2].

        Args:
            tau: atmospheric transmissivity, unitless
            shortwave_in: daily downward shortwave radiation [J m-2]
            sunshine_fraction: fraction of sunshine hours, between 0 (100% cloud cover)
                and 1 (cloud free sky)
            albedo_shortwave: shortwave albedo, default = 0.17
        """
        self.topofcanopy_radiation = (1.0 - albedo_shortwave) * tau * shortwave_in

    def calc_longwave_radiation(
        self,
        canopy_temperature: NDArray[np.float32],
        surface_temperature: NDArray[np.float32],
    ) -> None:
        """Calculates longwave emission from canopy and forest floor [J m-2].

        Args:
            canopy_temperature: canopy temperature of n layers [C]; the array size is
                set to max number of layers (n_max) and filled with NaN where n < n_max
            surface_temperature: surface soil temperature [C]
        """
        # longwave emission canopy
        self.longwave_canopy = (
            CANOPY_EMISSIVITY
            * BOLZMAN_CONSTANT
            * (CELSIUS_TO_KELVIN + canopy_temperature) ** 4
        )

        # longwave emission surface
        self.longwave_soil = (
            SOIL_EMISSIVITY
            * BOLZMAN_CONSTANT
            * (CELSIUS_TO_KELVIN + surface_temperature) ** 4
        )

    def calc_netradiation_surface(
        self,
        canopy_absorption: NDArray[np.float32],
    ) -> None:
        """Calculates daily net radiation at the forest floor [J m-2].

        Args:
            canopy_absorption: absorption by canopy layers, [J m-2]
        """
        self.netradiation_surface = (
            self.topofcanopy_radiation
            - canopy_absorption  # np.sum(canopy_absorption, axis=1)  # what axis?
            - self.longwave_soil
            - self.longwave_canopy  # np.sum(self.longwave_canopy, axis=1)
        )

    def radiation_balance(
        self,
        shortwave_in: NDArray[np.float32],
        sunshine_fraction: NDArray[np.float32],
        albedo_vis: NDArray[np.float32],
        albedo_shortwave: NDArray[np.float32],
        canopy_temperature: NDArray[np.float32],
        surface_temperature: NDArray[np.float32],
        canopy_absorption: NDArray[np.float32],
    ) -> None:
        """Calculate radiation balance.

        The function runs the full radiation balance and populates the following
        attributes:
            * elevation [m]
            * top of canopy downward shortwave radiation, [J m-2]
            * top of canopy photosynthetic photon flux density,[mol m-2]
            * longwave radiation from n individual canopy layers [J m-2]
            * longwave radiation from soil [J m-2]
            * net shortwave radiation at the surface (=forest floor)[J m-2]

        Args:
            elevation: elevation [m]
            shortwave_in: daily downward shortwave radiation[J m-2]
            sunshine_fraction: fraction of sunshine hours, between 0
                (100% cloud cover) and 1 (cloud free sky)
            albedo_vis: visible light albedo, default = 0.03
            albedo_shortwave: shortwave albedo, default = 0.17
            canopy_temperature: canopy temperature of n layers [C]
            surface_temperature: surface soil temperature [C]
            canopy_absorption: absorption by canopy [J m-2]
        """

        tau = self.calc_ppfd(shortwave_in, sunshine_fraction, albedo_vis)
        self.calc_topofcanopy_radiation(
            tau, shortwave_in, sunshine_fraction, albedo_shortwave
        )
        self.calc_longwave_radiation(canopy_temperature, surface_temperature)
        self.calc_netradiation_surface(canopy_absorption)
