"""The `abiotic.radiation` module.

The radiation module calculates the radiation balance of the Virtual Rainforest.
The top of canopy net shortwave radiation at a given location depends on
    1. extra-terrestrial radiation (affected by the earth's orbit, time of year and
        day, and location on the earth),
    2. terrestrial radiation (affected by atmospheric composition and clouds),
    3. topography (elevation, slope and aspect),
    4. surface albedo (vegetation type and fraction of vegetation/bare soil), and
    5. emitted longwave radiation.

The preprocessing module takes extra-terrestrial radiation as an input and adjusts for
the effects of topography (slope and aspect). Here, the effects of atmospheric
filtering (elevation dependend) and cloud cover are added to calculate photosynthetic
photon flux density (PPFD) at the top of the canopy which is a crucial input to the
plant module. The implementation is based on David et al. (2017): Simple process-led
algorithms for simulating habitats (SPLASH v.1.0): robust indices of radiation, evapo-
transpiration and plant-available moisture, Geosci. Model Dev., 10, 689-708.

Cloud cover and surface albedo also determine how much of the shortwave radiation that
reaches the top of the canopy is reflected and how much remains to be absorbed via
photosynthesis and re-emitted as longwave radiation by vegetation and forest floor.

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
CLOUDY_TRANSMISSIVITY = 0.25  # cloudy transmittivity (Linacre, 1968)
TRANSMISSIVITY_COEFFICIENT = (
    0.50  # angular coefficient of transmittivity (Linacre, 1968)
)
FLUX_TO_ENERGY = 2.04  # from flux to energy conversion, umol/J (Meek et al., 1984)
BOLZMAN_CONSTANT = 5.67 * 10 ** (-8)  # Stephan Bolzman constant W m-2 K-4
SOIL_EMISSIVITY = 0.95  # default for tropical rainforest
CANOPY_EMISSIVITY = 0.95  # default for tropical rainforest
BEER_REGRESSION = 2.67e-5  # parameter in equation for atmospheric transmissivity based
# on regression of Beer’s radiation extinction function (Allen 1996)
ALBEDO_VIS = np.array(0.03, dtype=float)
ALBEDO_SHORTWAVE = np.array(0.17, dtype=float)
CELCIUS_TO_KELVIN = 273.15  # calculate absolute temperature in Kelvin
SECOND_TO_DAY = 86400  # factor to convert between days and seconds


class Radiation:
    """Radiation balance.

    Attributes:
        elevation: NDArray[np.float32], elevation [m]
        topofcanopy_radiation: NDArray[np.float32], daily top of canopy downward
        shortwave radiation, [J m-2]
        ppfd: NDArray[np.float32], daily top of canopy photosynthetic photon flux
        density, [mol m-2]
        longwave_canopy: NDArray[np.float32], daily longwave radiation from n individual
            canopy layers [J m-2]
        longwave_soil: NDArray[np.float32], daily longwave radiation from soil [J m-2]
        netradiation_surface: NDArray[np.float32], daily net shortwave radiation at the
            surface (=forest floor) [J m-2]
    """

    def __init__(self, elevation: NDArray[np.float32]) -> None:
        """Initializes point-based radiation method."""
        self.elevation = elevation

    def calc_ppfd(
        self,
        shortwave_in: NDArray[np.float32],
        sunshine_hours: NDArray[np.float32] = np.array(1.0, dtype=float),
        albedo_vis: NDArray[np.float32] = ALBEDO_VIS,
    ) -> NDArray[np.float32]:
        """Calculates photosynthetic photon flux density at the top of the canopy.

        Args:
            shortwave_in: NDArray[np.float32], daily downward shortwave radiation[J m-2]
            sunshine_hours: NDArray[np.float32], fraction of sunshine hours, between 0
                (100% cloud cover) and 1 (cloud free sky)
            albedo_vis: NDArray[np.float32], visible light albedo, default = 0.03

        Returns:
            tau: NDArray[np.float32], transmissivity
            self.ppfd: NDArray[np.float32], daily top of canopy photosynthetic photon
            flux density, [mol m-2]

        Reference:
            Davis et al. (2017): Simple process-led algorithms for simulating habitats
            (SPLASH v.1.0): robust indices of radiation, evapotranspiration and plant-
            available moisture, Geosci. Model Dev., 10, 689-708
        """
        # calculate transmissivity (tau), unitless
        tau_o = CLOUDY_TRANSMISSIVITY + TRANSMISSIVITY_COEFFICIENT * sunshine_hours
        tau = tau_o * (1.0 + BEER_REGRESSION * self.elevation)

        # Calculate daily photosynth. photon flux density (ppfd_d), mol/m^2
        self.ppfd = (1.0e-6) * FLUX_TO_ENERGY * (1.0 - albedo_vis) * tau * shortwave_in
        return tau

    def calc_topofcanopy_radiation(
        self,
        tau: NDArray[np.float32],
        shortwave_in: NDArray[np.float32],
        sunshine_hours: NDArray[np.float32] = np.array(1.0, dtype=float),
        albedo_shortwave: NDArray[np.float32] = ALBEDO_SHORTWAVE,
    ) -> None:
        """Calculate top of canopy shortwave radiation.

        Args:
            shortwave_in: NDArray[np.float32], daily downward shortwave radiation[J m-2]
            sunshine_hours: NDArray[np.float32], fraction of sunshine hours, between 0
                (100% cloud cover) and 1 (cloud free sky)
            albedo_shortwave: NDArray[np.float32], shortwave albedo, default = 0.17

        Returns:
            self.topofcanopy_radiation: NDArray[np.float32], top of canopy downward
                shortwave radiation, [J m-2]
        """
        self.topofcanopy_radiation = (1.0 - albedo_shortwave) * tau * shortwave_in

    def calc_longwave_radiation(
        self,
        canopy_temperature: NDArray[np.float32],
        surface_temperature: NDArray[np.float32],
    ) -> None:
        """Calculates longwave emission from canopy and forest floor.

        Args:
            canopy_temperature: NDArray[np.float32], canopy temperature of n layers [C];
                the array size is set to max number of layers (n_max) and filled with
                NaN where n < n_max
            surface_temperature: NDArray[np.float32], surface soil temperature [C]

        Returns:
            self.longwave_canopy: NDArray[np.float32], longwave radiation from n
                individual canopy layers [J m-2]
            self.longwave_soil: NDArray[np.float32],longwave radiation from soil [J m-2]
        """
        # longwave emission canopy
        self.longwave_canopy = (
            CANOPY_EMISSIVITY
            * BOLZMAN_CONSTANT
            * (CELCIUS_TO_KELVIN + canopy_temperature**4)
        )

        # longwave emission surface
        self.longwave_soil = (
            SOIL_EMISSIVITY
            * BOLZMAN_CONSTANT
            * (CELCIUS_TO_KELVIN + surface_temperature**4)
        )

    def calc_netradiation_surface(
        self,
        canopy_absorption: NDArray[np.float32],
    ) -> None:
        """Calculates daily net radiation at the forest floor.

        Args:
            canopy_absorption: NDArray[np.float32]: absorption by canopy layers [J m-2]

        Returns:
            self.netradiation_surface: NDArray[np.float32], net shortwave radiation at
                the forest floor [J m-2]
        """
        self.netradiation_surface = (
            self.topofcanopy_radiation
            - np.sum(canopy_absorption, axis=1)  # what axis is level? select by name?
            - np.sum(self.longwave_canopy, axis=1)  #
            - self.longwave_soil
        )

    def radiation_balance(
        self,
        elevation: NDArray[np.float32],
        shortwave_in: NDArray[np.float32],
        sunshine_hours: NDArray[np.float32],
        albedo_vis: NDArray[np.float32],
        albedo_shortwave: NDArray[np.float32],
        canopy_temperature: NDArray[np.float32],
        surface_temperature: NDArray[np.float32],
        canopy_absorption: NDArray[np.float32],
    ) -> None:
        """Calculate radiation balance.

        Args:
            elevation: NDArray[np.float32], elevation [m]
            shortwave_in: NDArray[np.float32], daily downward shortwave radiation[J m-2]
            sunshine_hours: NDArray[np.float32], fraction of sunshine hours, between 0
                (100% cloud cover) and 1 (cloud free sky)
            albedo_vis: NDArray[np.float32], visible light albedo, default = 0.03
            albedo_shortwave: NDArray[np.float32], shortwave albedo, default = 0.17
            canopy_temperature: NDArray[np.float32], canopy temperature of n layers [C]
            surface_temperature: NDArray[np.float32], surface soil temperature [C]
            canopy_absorption: NDArray[np.float32]: absorption by canopy [J m-2]

        Returns:
            elevation: NDArray[np.float32], evelation [m]
            topofcanopy_radiation: NDArray[np.float32], top of canopy downward shortwave
                radiation, [J m-2]
            ppfd: NDArray[np.float32], top of canopy photosynthetic photon flux density,
                [mol m-2]
            longwave_canopy: NDArray[np.float32], longwave radiation from n individual
                canopy layers [J m-2]
            longwave_soil: NDArray[np.float32], longwave radiation from soil [J m-2]
            netradiation_surface: NDArray[np.float32], net shortwave radiation at
                the surface (=forest floor)[J m-2]
        """

        tau = self.calc_ppfd(shortwave_in, sunshine_hours, albedo_vis)
        self.calc_topofcanopy_radiation(
            tau, shortwave_in, sunshine_hours, albedo_shortwave
        )
        self.calc_longwave_radiation(canopy_temperature, surface_temperature)
        self.calc_netradiation_surface(canopy_absorption)
        del tau
