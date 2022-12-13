"""The `soil.carbon` module.

This module simulates the radiation soil carbon cycle for the Virtual Rainforest. At the
moment only two pools are modelled, these are low molecular weight carbon (LMWC) and
mineral associated organic matter (MAOM). More pools and their interactions will be
added at a later date.
"""

import numpy as np
from numpy.typing import NDArray

# OKAY FOR ME IT MAKES SENSE TO HAVE A CLASS CALLED CARBON
# AN ATTRIBUTE FOR EVERY POOL, THESE ATTRIBUTES ARE ONLY MODIFIED BY SPECIFIC FUNCTIONS


class SoilCarbon:
    """Class containing the full set of soil carbon pools.

    TODO - Explain current contents + limitations
    TODO - List attributes
    """

    def __init__(self, MAOM: NDArray[np.float32], LMWC: NDArray[np.float32]) -> None:
        """Initialise set of carbon pools."""

        self.MAOM = MAOM
        self.LMWC = LMWC
        pass
