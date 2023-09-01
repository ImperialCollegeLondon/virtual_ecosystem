"""The ``models.litter.litter_pools`` module  simulates the litter pools for the Virtual
Rainforest. Pools are divided into above and below ground pools, with below ground pools
affected by both soil moisture and temperature, and above ground pools just affected by
soil surface temperatures. The pools are also divided based on the recalcitrance of
their inputs, dead wood is given a separate pool, and all other inputs are divided
between metabolic and structural pools. Recalcitrant litter contains hard to break down
compounds, principally lignin. The metabolic litter pool contains the non-recalcitrant
litter and so breaks down quickly. Whereas, the structural litter contains the
recalcitrant litter.

We consider 5 pools rather than 6, as it's not really possible to parametrise the below
ground dead wood pool. So, all dead wood gets included in the above ground woody litter
pool.

At present, litter chemistry is not explicitly considered so the three recalcitrant
pools (woody, above_ground_structural, and below_ground_structural) are all assumed to
be 50% lignin. In the near future the model will be explicitly consider litter
chemistry.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.models.litter.constants import LitterConsts

# TODO - At the moment this module does not use litter chemistry (relative lignin
# content) at all. We need to decide how we handle this and adjust the below functions
# to use this at some point.


def calculate_litter_pool_updates(
    surface_temp: NDArray[np.float32],
    topsoil_temp: NDArray[np.float32],
    water_potential: NDArray[np.float32],
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    decomposed_excrement: NDArray[np.float32],
    decomposed_carcasses: NDArray[np.float32],
    update_interval: float,
    constants: LitterConsts,
) -> dict[str, DataArray]:
    """Calculate updates for all litter pools.

    Args:
        surface_temp: Temperature of soil surface, which is assumed to be the same
            temperature as the above ground litter [C]
        topsoil_temp: Temperature of topsoil layer, which is assumed to be the same
            temperature as the below ground litter [C]
        water_potential: Water potential of the topsoil layer [kPa]
        above_metabolic: Above ground metabolic litter pool [kg C m^-2]
        above_structural: Above ground structural litter pool [kg C m^-2]
        woody: The woody litter pool [kg C m^-2]
        below_metabolic: Below ground metabolic litter pool [kg C m^-2]
        below_structural: Below ground structural litter pool [kg C m^-2]
        decomposed_excrement: Input rate of excrement from the animal model [kg C m^-2
            day^-1]
        decomposed_carcasses: Input rate of (partially) decomposed carcass biomass from
            the animal model [kg C m^-2 day^-1]
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
    # Calculate temperature factor for the below ground litter layers
    temperature_factor_below = calculate_temperature_effect_on_litter_decomp(
        temperature=topsoil_temp,
        reference_temp=constants.litter_decomp_reference_temp,
        offset_temp=constants.litter_decomp_offset_temp,
        temp_response=constants.litter_decomp_temp_response,
    )
    # Calculate the water factor (relevant for below ground layers)
    water_factor = calculate_moisture_effect_on_litter_decomp(
        water_potential=water_potential,
        water_potential_halt=constants.litter_decay_water_potential_halt,
        water_potential_opt=constants.litter_decay_water_potential_optimum,
        moisture_response_curvature=constants.moisture_response_curvature,
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
    woody_decay = calculate_litter_decay_woody(
        temperature_factor_above,
        woody,
        litter_decay_coefficient=constants.litter_decay_constant_woody,
    )
    metabolic_below_decay = calculate_litter_decay_metabolic_below(
        temperature_factor_below,
        water_factor,
        below_metabolic,
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_below,
    )
    structural_below_decay = calculate_litter_decay_structural_below(
        temperature_factor_below,
        water_factor,
        below_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_below,
    )

    # Calculate mineralisation from each pool
    metabolic_above_mineral = calculate_carbon_mineralised(
        metabolic_above_decay, carbon_use_efficiency=constants.cue_metabolic
    )
    structural_above_mineral = calculate_carbon_mineralised(
        structural_above_decay,
        carbon_use_efficiency=constants.cue_structural_above_ground,
    )
    woody_mineral = calculate_carbon_mineralised(
        woody_decay,
        carbon_use_efficiency=constants.cue_woody,
    )
    metabolic_below_mineral = calculate_carbon_mineralised(
        metabolic_below_decay, carbon_use_efficiency=constants.cue_metabolic
    )
    structural_below_mineral = calculate_carbon_mineralised(
        structural_below_decay,
        carbon_use_efficiency=constants.cue_structural_below_ground,
    )

    # Calculate how the decomposed carcasses biomass is split between the metabolic and
    # structural litter pools
    carcass_to_metabolic, carcass_to_structural = calculate_carcass_split(
        decomposed_carcasses,
        fraction_to_metabolic=constants.carcass_decay_metabolic_fraction,
    )

    # Combine with input rates and multiple by update time to find overall changes
    change_in_metabolic_above = (
        constants.litter_input_to_metabolic_above
        + decomposed_excrement
        + carcass_to_metabolic
        - metabolic_above_decay
    ) * update_interval

    change_in_structural_above = (
        constants.litter_input_to_structural_above
        + carcass_to_structural
        - structural_above_decay
    ) * update_interval
    change_in_woody = (constants.litter_input_to_woody - woody_decay) * update_interval
    change_in_metabolic_below = (
        constants.litter_input_to_metabolic_below - metabolic_below_decay
    ) * update_interval
    change_in_structural_below = (
        constants.litter_input_to_structural_below - structural_below_decay
    ) * update_interval

    # Calculate mineralisation rate
    total_C_mineralisation_rate = (
        metabolic_above_mineral
        + structural_above_mineral
        + woody_mineral
        + metabolic_below_mineral
        + structural_below_mineral
    )
    # Convert mineralisation rate into kg m^-3 units (from kg m^-2)
    total_C_mineralisation_rate /= constants.depth_of_active_layer

    # Construct dictionary of data arrays to return
    new_litter_pools = {
        "litter_pool_above_metabolic": DataArray(
            above_metabolic + change_in_metabolic_above, dims="cell_id"
        ),
        "litter_pool_above_structural": DataArray(
            above_structural + change_in_structural_above, dims="cell_id"
        ),
        "litter_pool_woody": DataArray(woody + change_in_woody, dims="cell_id"),
        "litter_pool_below_metabolic": DataArray(
            below_metabolic + change_in_metabolic_below, dims="cell_id"
        ),
        "litter_pool_below_structural": DataArray(
            below_structural + change_in_structural_below, dims="cell_id"
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


def calculate_moisture_effect_on_litter_decomp(
    water_potential: NDArray[np.float32],
    water_potential_halt: float,
    water_potential_opt: float,
    moisture_response_curvature: float,
) -> NDArray[np.float32]:
    """Calculate the effect that soil moisture has on litter decomposition rates.

    This function is only relevant for the below ground litter pools. Its functional
    form is taken from :cite:t:`moyano_responses_2013`.

    Args:
        water_potential: Soil water potential [kPa]
        water_potential_halt: Water potential at which all microbial activity stops
            [kPa]
        water_potential_opt: Optimal water potential for microbial activity [kPa]
        moisture_response_curvature: Parameter controlling the curvature of the moisture
            response function [unitless]

    Returns:
        A multiplicative factor capturing the impact of moisture on below ground litter
        decomposition [unitless]
    """

    # Calculate how much moisture suppresses microbial activity
    supression = (
        (np.log10(np.abs(water_potential)) - np.log10(abs(water_potential_opt)))
        / (np.log10(abs(water_potential_halt)) - np.log10(abs(water_potential_opt)))
    ) ** moisture_response_curvature

    return 1 - supression


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


def calculate_litter_decay_woody(
    temperature_factor: NDArray[np.float32],
    litter_pool_woody: NDArray[np.float32],
    litter_decay_coefficient: float,
) -> NDArray[np.float32]:
    """Calculate decay of the woody litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        litter_pool_woody: The size of the woody litter pool [kg C m^-2]
        litter_decay_coefficient: The decay coefficient for the woody litter pool
            [day^-1]

    Returns:
        Rate of decay of the woody litter pool [kg C m^-2 day^-1]
    """

    # Factor capturing the impact of litter chemistry on decomposition, calculated based
    # on formula in Kirschbaum and Paul (2002) with the assumption that dead wood is 50%
    # lignin. Keeping as a hard coded constant for now, as how litter chemistry is dealt
    # with is going to be revised in the near future.
    litter_chemistry_factor = 0.082085

    return (
        litter_decay_coefficient
        * temperature_factor
        * litter_pool_woody
        * litter_chemistry_factor
    )


def calculate_litter_decay_metabolic_below(
    temperature_factor: NDArray[np.float32],
    moisture_factor: NDArray[np.float32],
    litter_pool_below_metabolic: NDArray[np.float32],
    litter_decay_coefficient: float,
) -> NDArray[np.float32]:
    """Calculate decay of below ground metabolic litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        moisture_factor: A multiplicative factor capturing the impact of soil moisture
            on litter decomposition [unitless]
        litter_pool_below_metabolic: The size of the below ground metabolic litter pool
            [kg C m^-2]
        litter_decay_coefficient: The decay coefficient for the below ground metabolic
            litter pool [day^-1]

    Returns:
        Rate of decay of the below ground metabolic litter pool [kg C m^-2 day^-1]
    """

    return (
        litter_decay_coefficient
        * temperature_factor
        * moisture_factor
        * litter_pool_below_metabolic
    )


def calculate_litter_decay_structural_below(
    temperature_factor: NDArray[np.float32],
    moisture_factor: NDArray[np.float32],
    litter_pool_below_structural: NDArray[np.float32],
    litter_decay_coefficient: float,
) -> NDArray[np.float32]:
    """Calculate decay of below ground structural litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        moisture_factor: A multiplicative factor capturing the impact of soil moisture
            on litter decomposition [unitless]
        litter_pool_below_structural: The size of the below ground structural litter
            pool [kg C m^-2]
        litter_decay_coefficient: The decay coefficient for the below ground structural
            litter pool [day^-1]

    Returns:
        Rate of decay of the below ground structural litter pool [kg C m^-2 day^-1]
    """

    # Factor capturing the impact of litter chemistry on decomposition, calculated based
    # on formula in Kirschbaum and Paul (2002) with the assumption that structural
    # litter is 50% lignin. Keeping as a hard coded constant for now, as how litter
    # chemistry is dealt with is going to be revised in the near future.
    litter_chemistry_factor = 0.082085

    return (
        litter_decay_coefficient
        * temperature_factor
        * moisture_factor
        * litter_chemistry_factor
        * litter_pool_below_structural
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


def calculate_carcass_split(
    decomposed_carcasses: NDArray[np.float32], fraction_to_metabolic: float
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Calculate the amount of carcass biomass for metabolic and structural litter.

    TODO - In future this function probably should depend on factors like animal tissue
    chemistry, but for now the split is assumed to be constant.

    Args:
        decomposed_carcasses: Input rate of (partially) decomposed carcass biomass from
            the animal model [kg C m^-2 day^-1]
        fraction_to_metabolic: Fraction of decomposed carcass biomass that belongs in
            the metabolic litter pool [unitless]

    Returns:
        A tuple containing the rate carcass biomass flow into to the metabolic litter
        pool [kg C m^-2 day^-1], and the rate of flow into the structural pool [kg C
        m^-2 day^-1].
    """

    carcass_to_metabolic = fraction_to_metabolic * decomposed_carcasses
    carcass_to_structural = (1 - fraction_to_metabolic) * decomposed_carcasses

    return (carcass_to_metabolic, carcass_to_structural)
