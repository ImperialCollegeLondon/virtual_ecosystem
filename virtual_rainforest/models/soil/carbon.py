"""The `models.soil.carbon` module.

This module simulates the soil carbon cycle for the Virtual Rainforest. At the moment
only two pools are modelled, these are low molecular weight carbon (LMWC) and mineral
associated organic matter (MAOM). More pools and their interactions will be added at a
later date.
"""

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.logger import log_and_raise
from virtual_rainforest.core.model import InitialisationError

# TODO - I'm basically certain that the paper I've taken this model structure from has
# not used units consistently (in particular the BINDING_WITH_PH). Down the line I need
# to track down a reliable parameterisation for this section.

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
        """Mineral associated organic matter pool (kg C m^-3)"""
        self.lmwc = lmwc
        """Low molecular weight carbon pool (kg C m^-3)"""

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
            bulk_density: bulk density values for each soil grid cell (kg m^-3)
            soil_moisture: relative water content for each soil grid cell (unitless)
            soil_temp: soil temperature for each soil grid cell (degrees C)
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
            bulk_density: bulk density values for each soil grid cell (kg m^-3)
            soil_moisture: relative water content for each soil grid cell (unitless)
            soil_temp: soil temperature for each soil grid cell (degrees C)
            percent_clay: Percentage clay for each soil grid cell

        Returns:
            The net flux from LMWC to MAOM (kg C m^-3 day^-1)
        """

        # Calculate
        Q_max = calculate_max_sorption_capacity(bulk_density, percent_clay)
        equib_maom = calculate_equilibrium_maom(pH, Q_max, self.lmwc)

        # Find scalar factors that multiple rates
        temp_scalar = convert_temperature_to_scalar(soil_temp)
        moist_scalar = convert_moisture_to_scalar(soil_moisture)

        return temp_scalar * moist_scalar * self.lmwc * (equib_maom - self.maom) / Q_max


def calculate_max_sorption_capacity(
    bulk_density: NDArray[np.float32], percent_clay: NDArray[np.float32]
) -> NDArray[np.float32]:
    """Calculate maximum sorption capacity based on bulk density and clay content.

    The maximum sorption capacity is the maximum amount of mineral associated organic
    matter that can exist per unit volume. This expression and its parameters are also
    drawn from Mayes et al. (2012). In that paper max sorption also depends on Fe
    content, but we are ignoring this for now.

    Args:
        bulk_density: bulk density values for each soil grid cell (kg m^-3)
        percent_clay: Percentage clay for each soil grid cell

    Returns:
        Maximum sorption capacity (kg m^-3)
    """

    if np.any(percent_clay > 100.0) or np.any(percent_clay < 0.0):
        log_and_raise(
            "Relative clay content must be expressed as a percentage!", ValueError
        )

    Q_max = bulk_density * 10 ** (
        MAX_SORPTION_WITH_CLAY["slope"] * np.log10(percent_clay)
        + MAX_SORPTION_WITH_CLAY["intercept"]
    )
    return Q_max


def calculate_equilibrium_maom(
    pH: NDArray[np.float32],
    Q_max: NDArray[np.float32],
    lmwc: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate equilibrium MAOM concentration based on Langmuir coefficients.

    Equilibrium concentration of mineral associated organic matter (MAOM) is calculated
    by this function under the assumption that the concentration of low molecular weight
    carbon (LMWC) is fixed.

    Args:
        pH: pH values for each soil grid cell Q_max: Maximum sorption capacities (kg
        m^-3)
        lmwc: Low molecular weight carbon pool (kg C m^-3)

    Returns:
        Equilibrium concentration of MAOM (kg C m^-3)
    """

    binding_coefficient = calculate_binding_coefficient(pH)
    return (binding_coefficient * Q_max * lmwc) / (1 + lmwc * binding_coefficient)


def calculate_binding_coefficient(pH: NDArray[np.float32]) -> NDArray[np.float32]:
    """Calculate Langmuir binding coefficient based on pH.

    This specific expression and its parameters are drawn from (Mayes et al. (2012)).

    Args:
        pH: pH values for each soil grid cell

    Returns:
        Langmuir binding coefficients for mineral association of labile carbon (m^3
        kg^-1)
    """

    return 10.0 ** (BINDING_WITH_PH["slope"] * pH + BINDING_WITH_PH["intercept"])


def convert_temperature_to_scalar(
    soil_temp: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Convert soil temperature into a factor to multiply rates by.

    This form is used in Abramoff et al. (2018) to minimise differences with the
    CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
       soil_temp: soil temperature for each soil grid cell (degrees C)

    Returns:
        A scalar that captures the impact of soil temperature on process rates
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
        soil_moisture: relative water content for each soil grid cell (unitless)

    Returns:
        A scalar that captures the impact of soil moisture on process rates
    """

    if np.any(soil_moisture > 1.0) or np.any(soil_moisture < 0.0):
        log_and_raise(
            "Relative water content cannot go below zero or above one!", ValueError
        )

    # This expression is drawn from Abramoff et al. (2018)
    return 1 / (
        1
        + MOISTURE_SCALAR["coefficient"]
        * np.exp(-MOISTURE_SCALAR["exponent"] * soil_moisture)
    )
