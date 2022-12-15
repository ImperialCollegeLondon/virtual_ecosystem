"""The `abiotic.radiation` module.

The radiation module calculates the radiation balance of the Virtual Rainforest.
The top of canopy net shortwave radiation at a given location depends on
    1. extra-terrestrial radiation (affected by the earth's orbit, time of year and
        day, and location on the earth),
    2. terrestrial radiation (affected by atmospheric composition and clouds),
    3. topography (elevantion, slope and aspect), and
    4. surface albedo (vegetation type and fraction of vegetation/bare soil).

The preprocessing module takes extra-terrestrial radiation as an input and adjusts for
the effects of topography (slope and aspect). Here, the effects of atmospheric
filtering (elevation dependend) and cloud cover are added to calculate photosynthetic
photon flux density (PPFD) at the top of the canopy which is a crucial input to the
plant module. The implementation is based on David et al. (2017): Simple process-led
algorithms for simulating habitats (SPLASH v.1.0): robust indices of radiation, evapo-
transpiration and plant-available moisture, Geosci. Model Dev., 10, 689-708.

The effects of cloud cover and surface albedo also determine how much of the shortwave
radiation that reaches the top of the canopy is refleceted, absorbed, and re-emitted as
longwave radiation by vegetation and forest floor. The canopy structure determines the
vertical profile of net shortwave radiation below the canopy which is available for
sensible and latent heat flux and ground heat flux (see Energy_balance).

The radiation balance can be calculated with the radiation_balance() function. At the
moment, this happens at a daily timestep.

# the following structural components are not implemented yet
TODO include time dimension
TODO logging, raise errors
TODO all tests
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


class Radiation:
    """Radiation balance.

    Attributes:
        elevation: NDArray[np.float32], evelation [m]
        topofcanopy_radiation: NDArray[np.float32], top of canopy downward shortwave
         radiation, [W m-2]
        ppfd: NDArray[np.float32], photosynthetic photon flux density, [mol m-2]
        netradiation_profile: NDArray[np.float32], net shortwave radiation below canopy
         [W m-2]
    """

    def __init__(self, elevation: NDArray[np.float32]) -> None:
        """Initializes point-based radiation method."""
        self.elevation = elevation

    def calc_ppfd(
        self,
        shortwave_in: NDArray[np.float32],
        sunshine_hours: NDArray[np.float32],
        albedo_vis: NDArray[np.float32] = np.array(0.03, dtype=float),
    ) -> NDArray[np.float32]:
        """Calculates photosynthetic photon flux density at the top of the canopy.

        Args:
            shortwave_in: NDArray[np.float32], daily downward shortwave radiation[W m-2]
            sunshine_hours: NDArray[np.float32], fraction of sunshine hours
            albedo_vis: NDArray[np.float32], visible light albedo, default = 0.03

        Returns:
            tau: NDArray[np.float32], transmissivity, unitless
            self.ppfd: NDArray[np.float32], photosynthetic photon flux density [mol m-2]

        Reference:
            Davis et al. (2017): Simple process-led algorithms for simulating habitats
            (SPLASH v.1.0): robust indices of radiation, evapotranspiration and plant-
            available moisture, Geosci. Model Dev., 10, 689-708
        """
        # calculate transmissivity (tau), unitless
        tau_o = CLOUDY_TRANSMISSIVITY + TRANSMISSIVITY_COEFFICIENT * sunshine_hours
        tau = tau_o * (1.0 + BEER_REGRESSION * self.elevation)

        # Calculate daily photosynth. photon flux density (ppfd_d), mol/m^2
        self.ppfd_d = (
            (1.0e-6) * FLUX_TO_ENERGY * (1.0 - albedo_vis) * tau * shortwave_in
        )
        return tau

    def calc_topofcanopy_radiation(
        self,
        tau: NDArray[np.float32],
        shortwave_in: NDArray[np.float32],
        sunshine_hours: NDArray[np.float32],
        albedo_shortwave: NDArray[np.float32] = np.array(0.17, dtype=float),
    ) -> None:
        """Calculate top of canopy shortwave radiation.

        Args:
            shortwave_in: NDArray[np.float32], daily downward shortwave radiation[W m-2]
            sunshine_hours: NDArray[np.float32], fraction of sunshine hours
            albedo_shortwave: NDArray[np.float32], shortwave albedo, default = 0.17

        Returns:
            self.topofcanopy_radiation: NDArray[np.float32], shortwave radiation [W m-2]
        """
        self.topofcanopy_radiation = (1.0 - albedo_shortwave) * tau * shortwave_in

    def calc_longwave_radiation(
        self,
        canopy_temperature: NDArray[np.float32],
        surface_temperature: NDArray[np.float32],
    ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Calculates longwave emission from canopy and forest floor.

        Args:
            canopy_temperature: NDArray[np.float32], canopy temperature of n layers [C]
            surface_temperature: NDArray[np.float32], surface soil temperature [C]

        Returns:
            longwave_canopy: NDArray[np.float32], longwave radiation from n individual
                canopy layers [W m-2]
            longwave_soil: NDArray[np.float32], longwave radiation from soil [W m-2]
            self.longwave_out: NDArray[np.float32], total longwave radiation [W m-2]
        """
        raise NotImplementedError("Implementation of this feature is missing")

        # longwave emission canopy
        # TODO define the longwave_canopy array to match grid+vertical structure
        # which is not uniform (different number of layers in each grid cell)
        longwave_canopy = np.full_like(canopy_temperature, 0)
        for id in canopy_temperature["cell_id"]:
            for n in canopy_temperature["layer"]:
                longwave_canopy[id][n] = (
                    CANOPY_EMISSIVITY
                    * BOLZMAN_CONSTANT
                    * canopy_temperature[id][n] ** 4
                )

        # longwave emission surface
        longwave_soil = SOIL_EMISSIVITY * BOLZMAN_CONSTANT * surface_temperature**4

        return longwave_canopy, longwave_soil

    def calc_netradiation_profile(
        self,
        longwave_canopy: NDArray[np.float32],
        longwave_soil: NDArray[np.float32],
        canopy_absorption: NDArray[np.float32],
    ) -> None:
        """Calculates daily net radiation profile within the canopy.

        The output is a vector of net shortwave radiation, the first entry is the top
        of the canopy, the last entry is the net radiation that reaches the surface. The
        length of the vector varies in response to the number of canopy layers indicated
        by length of canopy_absorption.

        Args:
            longwave_canopy: NDArray[np.float32], longwave radiation from n individual
                canopy layers [W m-2]
            longwave_soil: NDArray[np.float32], longwave radiation from soil [W m-2]
            canopy_absorption: NDArray[np.float32]: absorption by canopy [W m-2]

        Returns:
            self.netradiation_profile: NDArray[np.float32],vertical profile net short-
                wave radiation [W m-2]
        """
        raise NotImplementedError("Implementation of this feature is missing")
        # this needs to loop over all layers and stepwise reduce topofcanopy_radiation
        # number of layers can differ between grid cells
        # netrad = self.topofcanopy_radiation
        # for i in len(canopy_absorption):
        #   self.netradiation_profile[i] = (
        #    netrad - self.longwave_out[i] - canopy_absorption[i]
        #    netrad = self.netradiation_profile[i]
        # )

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
    ) -> NDArray[np.float32]:
        """Calculate radiation balance.

        Args:
            elevation: NDArray[np.float32], elevation [m]
            shortwave_in: NDArray[np.float32], daily downward shortwave radiation[W m-2]
            sunshine_hours: NDArray[np.float32], fraction of sunshine hours
            albedo_vis: NDArray[np.float32], visible light albedo, default = 0.03
            albedo_shortwave: NDArray[np.float32], shortwave albedo, defaul = 0.17
            canopy_temperature: NDArray[np.float32], canopy temperature of n layers [C]
            surface_temperature: NDArray[np.float32], surface soil temperature [C]
            canopy_absorption: NDArray[np.float32]: absorption by canopy [W m-2]

        Returns:
            elevation: NDArray[np.float32], evelation [m]
            topofcanopy_radiation: NDArray[np.float32], top of canopy downward shortwave
                radiation, [W m-2]
            ppfd: NDArray[np.float32], photosynthetic photon flux density, [mol m-2]
            netradiation_profile: NDArray[np.float32], net shortwave radiation below
            canopy [W m-2]
        """
        raise NotImplementedError("Implementation of this feature is missing")

        tau = self.calc_ppfd(self, shortwave_in, sunshine_hours, albedo_vis)
        self.calc_topofcanopy_radiation(
            self, tau, shortwave_in, sunshine_hours, albedo_shortwave
        )
        longwave_canopy, longwave_soil = self.calc_longwave_radiation(
            self, canopy_temperature, surface_temperature
        )
        self.calc_netradiation_profile(
            self, longwave_canopy, longwave_soil, canopy_absorption
        )
        del tau, longwave_canopy, longwave_soil
