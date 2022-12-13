"""The `soil.carbon` module.

This module simulates the radiation soil carbon cycle for the Virtual Rainforest. At the
moment only two pools are modelled, these are low molecular weight carbon (LMWC) and
mineral associated organic matter (MAOM). More pools and their interactions will be
added at a later date.
"""

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

    def update_pools(self) -> None:
        """Update all soil carbon pools.

        This function calls lower level functions which calculate the transfers between
        pools. When all transfers have been calculated the net transfer is used to
        update the soil pools.
        """
        # TODO - Add interactions which involve the three missing carbon pools

        # TODO - MINERAL ASSOCIATION
        # TODO - SUM ALL CHANGES
        # TODO - UPDATE POOLS

    # TEMP SCALER AND MOIST SCALER DEFINITELY SHOULD BE CALCULATED IN A SUB FUNCTION
    def mineral_association(
        self, pH: NDArray[np.float32], bulk_density: NDArray[np.float32]
    ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Calculates net rate of LMWC association with soil minerals.

        Following Abramoff et al. (2018), mineral adsorption of carbon is controlled by
        a Langmuir saturation function.

        Args:
            pH: pH values for each soil grid cell
            bulk_density: bulk density values for each soil grid cell
        """

        # This expression is drawn from (Mayes et al. (2012))
        binding_affinity = 10.0 ^ (
            BINDING_WITH_PH["slope"] * pH + BINDING_WITH_PH["intercept"]
        )

        # This expression is also drawn from (Mayes et al. (2012))
        # Original paper also depends on Fe concentration, but we are ignoring this for
        # now
        Q_max = bulk_density * 10 ^ (
            MAX_SORPTION_WITH_CLAY["slope"] * bulk_density
            + MAX_SORPTION_WITH_CLAY["intercept"]
        )

        # Using the above calculate the equilibrium MAOM pool
        equib_maom = (binding_affinity * Q_max * self.lmwc) / (
            1 + self.lmwc * binding_affinity
        )

        # TEMP - DELETE THESE SOON, AND REPLACE WITH EQUATIONS
        temp_scaler = 1.0
        moist_scaler = 1.0

        flux = temp_scaler * moist_scaler * self.lmwc * (equib_maom - self.maom) / Q_max

        return -flux, flux
