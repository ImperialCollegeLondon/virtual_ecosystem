"""The ``models.litter.litter_pools`` module  simulates the litter pools for the Virtual
Rainforest. At the moment only two pools are modelled, above ground metabolic and above
ground structural, but a wider variety of pools will be simulated in future.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.models.litter.constants import LitterConsts

# TODO - At the moment this module does not use litter chemistry (relative lignin
# content) at all. We need to decide how we handle this and adjust the below functions
# to use this at some point.

# TODO - Then need to add this to a litter decay pool, which the soil model can use


def calculate_litter_pool_updates(
    surface_temp: NDArray[np.float32],
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    update_interval: float,
    constants: LitterConsts,
) -> dict[str, DataArray]:
    """Calculate updates for all litter pools.

    Args:
        surface_temp: Temperature of soil surface, which is assumed to be the same
            temperature of the above ground litter [C]
        above_metabolic: Above ground metabolic litter pool [kg C m^-2]
        above_structural: Above ground structural litter pool [kg C m^-2]
        update_interval: Interval that the litter pools are being updated for [days]
        constants: Set of constants for the litter model

    Returns:
        The new value for each of the litter pools, and the total mineralisation rate.
    """

    # Calculate temperature factor for the above ground litter layers
    temperature_factor_above = calculate_temperature_effect_on_litter_decomp(
        temperature=surface_temp,
        reference_temp=constants.litter_decomp_reference_temp,
        offset_temp=constants.litter_decomp_offset_temp,
        temp_response=constants.litter_decomp_temp_response,
    )

    # Calculate the pool decay rates
    metabolic_above_decay = calculate_litter_decay_metabolic_above(
        temperature_factor_above,
        above_metabolic,
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_above,
    )
    structural_above_decay = calculate_litter_decay_structural_above(
        temperature_factor_above,
        above_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_above,
    )

    # Calculate mineralisation from each pool
    metabolic_above_mineral = calculate_carbon_mineralised(
        metabolic_above_decay, carbon_use_efficiency=constants.cue_metabolic
    )
    structural_above_mineral = calculate_carbon_mineralised(
        structural_above_decay,
        carbon_use_efficiency=constants.cue_structural_above_ground,
    )

    # Combine with input rates and multiple by update time to find overall changes
    change_in_metabolic_above = (
        constants.litter_input_to_metabolic_above - metabolic_above_decay
    ) * update_interval
    change_in_structural_above = (
        constants.litter_input_to_structural_above - structural_above_decay
    ) * update_interval

    # Calculate mineralisation rate
    total_C_mineralisation_rate = metabolic_above_mineral + structural_above_mineral

    # Construct dictionary of data arrays to return
    new_litter_pools = {
        "litter_pool_above_metabolic": DataArray(
            above_metabolic + change_in_metabolic_above, dims="cell_id"
        ),
        "litter_pool_above_structural": DataArray(
            above_structural + change_in_structural_above, dims="cell_id"
        ),
        "litter_C_mineralisation_rate": DataArray(
            total_C_mineralisation_rate, dims="cell_id"
        ),
    }

    return new_litter_pools


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
        A multiplicative factor capturing the impact of temperature on litter
        decomposition [unitless]
    """

    return np.exp(
        temp_response * (temperature - reference_temp) / (temperature + offset_temp)
    )


def calculate_litter_decay_metabolic_above(
    temperature_factor: NDArray[np.float32],
    litter_pool_above_metabolic: NDArray[np.float32],
    litter_decay_coefficient: float,
) -> NDArray[np.float32]:
    """Calculate decay of above ground metabolic litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        litter_pool_above_metabolic: The size of the above ground metabolic litter pool
            [kg C m^-2]
        litter_decay_coefficient: The decay coefficient for the above ground metabolic
            litter pool [day^-1]

    Returns:
        Rate of decay of the above ground metabolic litter pool [kg C m^-2 day^-1]
    """

    return litter_decay_coefficient * temperature_factor * litter_pool_above_metabolic


def calculate_litter_decay_structural_above(
    temperature_factor: NDArray[np.float32],
    litter_pool_above_structural: NDArray[np.float32],
    litter_decay_coefficient: float,
) -> NDArray[np.float32]:
    """Calculate decay of above ground structural litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        litter_pool_above_structural: The size of the above ground structural litter
            pool [kg C m^-2]
        litter_decay_coefficient: The decay coefficient for the above ground structural
            litter pool [day^-1]

    Returns:
        Rate of decay of the above ground structural litter pool [kg C m^-2 day^-1]
    """

    # Factor capturing the impact of litter chemistry on decomposition, calculated based
    # on formula in Kirschbaum and Paul (2002) with the assumption that structural
    # litter is 50% lignin. Keeping as a hard coded constant for now, as how litter
    # chemistry is dealt with is going to be revised in the near future.
    litter_chemistry_factor = 0.082085

    return (
        litter_decay_coefficient
        * temperature_factor
        * litter_pool_above_structural
        * litter_chemistry_factor
    )


def calculate_carbon_mineralised(
    litter_decay_rate: NDArray[np.float32], carbon_use_efficiency: float
) -> NDArray[np.float32]:
    """Calculate fraction of litter decay that gets mineralised.

    TODO - This function could also be used to track carbon respired, if/when we decide
    to track that.

    Args:
        litter_decay_rate: Rate at which litter pool is decaying [kg C m^-2 day^-1]
        carbon_use_efficiency: Carbon use efficiency of litter pool [unitless]

    Returns:
        Rate at which carbon is mineralised from the litter pool [kg C m^-2 day^-1]
    """

    return carbon_use_efficiency * litter_decay_rate
