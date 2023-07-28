"""The ``models.litter.litter_pools`` module  simulates the litter pools for the Virtual
Rainforest. At the moment only two pools are modelled, above ground metabolic and above
ground structural, but a wider variety of pools will be simulated in future.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.models.litter.constants import LitterConsts


def calculate_litter_pool_updates(
    data: Data, constants: LitterConsts
) -> dict[str, DataArray]:
    """TODO - add a proper docstring here."""

    # TODO - Work out actual content here

    # TODO - only returning this to shut mypy up, this needs to change down the line
    return {"litter_pool_above_metabolic": data["litter_pool_above_metabolic"]}


# TODO - Functions for input to each compartment


def calculate_temperature_effect_on_litter_decomp(
    temperature: NDArray[np.float32],
    reference_temp: float,
    offset_temp: float,
    temp_response: float,
) -> NDArray[np.float32]:
    """Calculate the effect that temperature has on litter decomposition rates.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature: The temperature of the litter layer [C]
        reference_temp: The reference temperature for changes in litter decomposition
            rates with temperature [C]
        offset_temp: Temperature offset [C]
        temp_response: Factor controlling response strength to changing temperature
            [unitless]

    Returns:
        A multiplicative factor capturing the impact of temperature
    """

    return np.exp(
        temp_response * (temperature - reference_temp) / (temperature + offset_temp)
    )
