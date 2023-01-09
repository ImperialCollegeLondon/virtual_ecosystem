"""The `soil.carbon` module.

This module simulates the radiation soil carbon cycle for the Virtual Rainforest. At the
moment only two pools are modelled, these are low molecular weight carbon (LMWC) and
mineral associated organic matter (MAOM). More pools and their interactions will be
added at a later date.
"""

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.logger import log_and_raise
from virtual_rainforest.core.model import InitialisationError

# from core.constants import CONSTANTS as C
# but for meanwhile define all the constants needed here
BINDING_WITH_PH = {
    "slope": -0.186,  # unitless
    "intercept": -0.216,  # unitless
}
"""From linear regression (Mayes et al. (2012))."""
MAX_SORPTION_WITH_CLAY = {
    "slope": 0.483,  # unitless
    "intercept": 2.328,  # unitless
}
"""From linear regression (Mayes et al. (2012))."""
MOISTURE_SCALAR = {
    "coefficient": 30.0,  # unitless
    "exponent": 9.0,  # unitless
}
"""Used in Abramoff et al. (2018), but can't trace it back to anything more concrete."""
TEMP_SCALAR = np.array([15.4, 11.75, 29.7, 0.031, 30.0])
"""Used in Abramoff et al. (2018), but can't trace it back to anything more concrete.

Values:
    t_1: (degrees C)
    t_2: (unit unclear)
    t_3: (unit unclear)
    t_4: (unit unclear)
    ref_temp: (degrees C)
"""


class SoilCarbonPools:
    """Class containing the full set of soil carbon pools.

    At the moment, only two pools are included. Functions exist for the transfer of
    carbon between these pools, but not with either the yet to be implemented soil
    carbon pools, other pools in the soil module, or other modules.
    """

    def __init__(self, maom: NDArray[np.float32], lmwc: NDArray[np.float32]) -> None:
        """Initialise set of carbon pools."""

        # Check that arrays are of equal size and shape
        if maom.shape != lmwc.shape:
            log_and_raise(
                "Dimension mismatch for initial carbon pools!",
                InitialisationError,
            )

        # Check that negative initial values are not given
        if np.any(maom < 0) or np.any(lmwc < 0):
            log_and_raise(
                "Initial carbon pools contain at least one negative value!",
                InitialisationError,
            )

        self.maom = maom
        """Mineral associated organic matter pool"""
        self.lmwc = lmwc
        """Low molecular weight carbon pool"""

    def update_pools(
        self,
        pH: NDArray[np.float32],
        bulk_density: NDArray[np.float32],
        soil_moisture: NDArray[np.float32],
        soil_temp: NDArray[np.float32],
        percent_clay: NDArray[np.float32],
        dt: float,
    ) -> None:
        """Update all soil carbon pools.

        This function calls lower level functions which calculate the transfers between
        pools. When all transfers have been calculated the net transfer is used to
        update the soil pools.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell
            soil_moisture: soil moisture for each soil grid cell
            soil_temp: soil temperature for each soil grid cell
            percent_clay: Percentage clay for each soil grid cell
            dt: time step (days)
        """
        # TODO - Add interactions which involve the three missing carbon pools

        lmwc_to_maom = self.mineral_association(
            pH, bulk_density, soil_moisture, soil_temp, percent_clay
        )

        # Once changes are determined update all pools
        self.lmwc -= lmwc_to_maom * dt
        self.maom += lmwc_to_maom * dt

    def mineral_association(
        self,
        pH: NDArray[np.float32],
        bulk_density: NDArray[np.float32],
        soil_moisture: NDArray[np.float32],
        soil_temp: NDArray[np.float32],
        percent_clay: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """Calculates net rate of LMWC association with soil minerals.

        Following Abramoff et al. (2018), mineral adsorption of carbon is controlled by
        a Langmuir saturation function. At present, binding affinity and Q_max are
        recalculated on every function called based on pH, bulk density and clay
        content. Once a decision has been reached as to how fast pH and bulk density
        will change (if at all), this calculation may need to be moved elsewhere.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell
            soil_moisture: soil moisture for each soil grid cell
            soil_temp: soil temperature for each soil grid cell
            percent_clay: Percentage clay for each soil grid cell

        Returns:
            lmwc_to_maom: The net flux from LMWC to MAOM
        """

        # This expression is drawn from (Mayes et al. (2012))
        binding_affinity = 10.0 ** (
            BINDING_WITH_PH["slope"] * pH + BINDING_WITH_PH["intercept"]
        )

        # This expression is also drawn from Mayes et al. (2012)
        # Original paper also depends on Fe concentration, but we are ignoring this for
        # now
        Q_max = bulk_density * 10 ** (
            MAX_SORPTION_WITH_CLAY["slope"] * np.log10(percent_clay)
            + MAX_SORPTION_WITH_CLAY["intercept"]
        )

        # Using the above calculate the equilibrium MAOM pool
        equib_maom = (binding_affinity * Q_max * self.lmwc) / (
            1 + self.lmwc * binding_affinity
        )

        # Find scalar factors that multiple rates
        temp_scalar = convert_temperature_to_scalar(soil_temp)
        moist_scalar = convert_moisture_to_scalar(soil_moisture)

        return temp_scalar * moist_scalar * self.lmwc * (equib_maom - self.maom) / Q_max


def convert_temperature_to_scalar(
    soil_temp: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Convert soil temperature into a factor to multiply rates by.

    This form is used in Abramoff et al. (2018) to minimise differences with the
    CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
       soil_temp: soil temperature for each soil grid cell
    """

    t_1, t_2, t_3, t_4, ref_temp = TEMP_SCALAR

    # This expression is drawn from Abramoff et al. (2018)
    numerator = t_2 + (t_3 / np.pi) * np.arctan(np.pi * (soil_temp - t_1))
    denominator = t_2 + (t_3 / np.pi) * np.arctan(np.pi * t_4 * (ref_temp - t_1))

    return np.divide(numerator, denominator)


def convert_moisture_to_scalar(
    soil_moisture: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Convert soil moisture into a factor to multiply rates by.

    This form is used in Abramoff et al. (2018) to minimise differences with the
    CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
        soil_moisture: soil moisture for each soil grid cell
    """

    # This expression is drawn from Abramoff et al. (2018)
    return 1 / (
        1
        + MOISTURE_SCALAR["coefficient"]
        * np.exp(-MOISTURE_SCALAR["exponent"] * soil_moisture)
    )
