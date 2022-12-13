"""The `soil.carbon` module.

This module simulates the radiation soil carbon cycle for the Virtual Rainforest. At the
moment only two pools are modelled, these are low molecular weight carbon (LMWC) and
mineral associated organic matter (MAOM). More pools and their interactions will be
added at a later date.
"""

import numpy as np
from numpy.typing import NDArray


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
        # TODO - MINERAL DISASSOCIATION
        # TODO - SUM ALL CHANGES
        # TODO - UPDATE POOLS
