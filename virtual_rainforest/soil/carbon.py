"""The `soil.carbon` module.

This module simulates the radiation soil carbon cycle for the Virtual Rainforest. At the
moment only two pools are modelled, these are low molecular weight carbon (LMWC) and
mineral associated organic matter (MAOM). More pools and their interactions will be
added at a later date.
"""

from math import e

import numpy as np
from numpy.typing import NDArray

# from core.constants import CONSTANTS as C
# but for meanwhile define all the constants needed here
BINDING_WITH_PH = {
    "slope": -0.186,
    "intercept": -0.216,
}  # From linear regression (Mayes et al. (2012))
MAX_SORPTION_WITH_CLAY = {
    "slope": 0.483,
    "intercept": 2.328,
}  # From linear regression (Mayes et al. (2012))
MOISTURE_SCALAR = {
    "coefficient": 30.0,
    "exponent": 9.0,
}  # Used in Abramoff et al. (2018), but can't trace it back to anything more concrete


class SoilCarbon:
    """Class containing the full set of soil carbon pools.

    At the moment, only two pools are included. Functions exist for the transfer of
    carbon between these pools, but not with either the yet to be implemented soil
    carbon pools, other pools in the soil module, or other modules.

    Attributes:
        maom: Mineral associated organic matter pool
        lmwc: Low molecular weight carbon pool
    """

    def __init__(self, maom: NDArray[np.float32], lmwc: NDArray[np.float32]) -> None:
        """Initialise set of carbon pools."""

        self.maom = maom
        self.lmwc = lmwc

    def update_pools(
        self,
        pH: NDArray[np.float32],
        bulk_density: NDArray[np.float32],
        soil_moisture: NDArray[np.float32],
    ) -> None:
        """Update all soil carbon pools.

        This function calls lower level functions which calculate the transfers between
        pools. When all transfers have been calculated the net transfer is used to
        update the soil pools.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell
            soil_moisture: soil moisture for each soil grid cell
        """
        # TODO - Add interactions which involve the three missing carbon pools

        lmwc_from_maom, maom_from_lmwc = self.mineral_association(
            pH, bulk_density, soil_moisture
        )

        # Once changes are determined update all pools
        self.lmwc += lmwc_from_maom
        self.lmwc += maom_from_lmwc

    def mineral_association(
        self,
        pH: NDArray[np.float32],
        bulk_density: NDArray[np.float32],
        soil_moisture: NDArray[np.float32],
    ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Calculates net rate of LMWC association with soil minerals.

        Following Abramoff et al. (2018), mineral adsorption of carbon is controlled by
        a Langmuir saturation function. At present, binding affinity and Q_max are
        recalculated on every function called based on pH and bulk density. Once a
        decision has been reached as to how fast pH and bulk density will change (if at
        all), this calculation may need to be moved elsewhere.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell
            soil_moisture: soil moisture for each soil grid cell
        """

        # This expression is drawn from (Mayes et al. (2012))
        binding_affinity = 10.0 ** (
            BINDING_WITH_PH["slope"] * pH + BINDING_WITH_PH["intercept"]
        )

        # This expression is also drawn from Mayes et al. (2012)
        # Original paper also depends on Fe concentration, but we are ignoring this for
        # now
        Q_max = bulk_density * 10 ** (
            MAX_SORPTION_WITH_CLAY["slope"] * bulk_density
            + MAX_SORPTION_WITH_CLAY["intercept"]
        )

        # Using the above calculate the equilibrium MAOM pool
        equib_maom = (binding_affinity * Q_max * self.lmwc) / (
            1 + self.lmwc * binding_affinity
        )

        # Find scalar factors that multiple rates
        temp_scaler = scaler_temperature()
        moist_scaler = scaler_moisture(soil_moisture)

        flux = temp_scaler * moist_scaler * self.lmwc * (equib_maom - self.maom) / Q_max

        return -flux, flux

    # FIRST TASK FIND OUT WHAT THE HELL THIS SCALER IS


def scaler_temperature() -> NDArray[np.float32]:
    """Convert soil temperature into a factor to multiply rates by."""


def scaler_moisture(soil_moisture: NDArray[np.float32]) -> NDArray[np.float32]:
    """Convert soil moisture into a factor to multiply rates by.

    This form is used in Abramoff et al. (2018) to minimise differences with the
    CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
        soil_moisture: soil moisture for each soil grid cell
    """

    # This expression is drawn from Abramoff et al. (2018)
    scaler = 1 / (
        1
        + MOISTURE_SCALAR["coefficient"]
        * e ** (-MOISTURE_SCALAR["exponent"] * soil_moisture)
    )

    return scaler
