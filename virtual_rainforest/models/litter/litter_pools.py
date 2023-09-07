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

The amount of lignin in both the structural pools and the dead wood pool is tracked.
This is tracked because litter chemistry is a major determinant of litter decay rates.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.models.litter.constants import LitterConsts


def calculate_change_in_litter_variables(
    surface_temp: NDArray[np.float32],
    topsoil_temp: NDArray[np.float32],
    water_potential: NDArray[np.float32],
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    lignin_above_structural: NDArray[np.float32],
    lignin_woody: NDArray[np.float32],
    lignin_below_structural: NDArray[np.float32],
    decomposed_excrement: NDArray[np.float32],
    decomposed_carcasses: NDArray[np.float32],
    update_interval: float,
    constants: LitterConsts,
) -> dict[str, DataArray]:
    """Calculate changes for all the litter variables (pool sizes and chemistries).

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
        lignin_above_structural: Proportion of above ground structural pool which is
            lignin [unitless]
        lignin_woody: Proportion of dead wood pool which is lignin [unitless]
        lignin_below_structural: Proportion of below ground structural pool which is
            lignin [unitless]
        decomposed_excrement: Input rate of excrement from the animal model [kg C m^-2
            day^-1]
        decomposed_carcasses: Input rate of (partially) decomposed carcass biomass from
            the animal model [kg C m^-2 day^-1]
        update_interval: Interval that the litter pools are being updated for [days]
        constants: Set of constants for the litter model

    Returns:
        The new value for each of the litter pools, and the total mineralisation rate.
    """

    # Calculate the factors which capture the impact that temperature and soil water
    # content have on litter decay rates
    environmental_factors = calculate_environmental_factors(
        surface_temp=surface_temp,
        topsoil_temp=topsoil_temp,
        water_potential=water_potential,
        constants=constants,
    )

    # Calculate the litter pool decay rates
    decay_rates = calculate_decay_rates(
        above_metabolic=above_metabolic,
        above_structural=above_structural,
        woody=woody,
        below_metabolic=below_metabolic,
        below_structural=below_structural,
        lignin_above_structural=lignin_above_structural,
        lignin_woody=lignin_woody,
        lignin_below_structural=lignin_below_structural,
        environmental_factors=environmental_factors,
        constants=constants,
    )

    # Calculate the total mineralisation of carbon from the litter
    total_C_mineralisation_rate = calculate_total_C_mineralised(decay_rates, constants)

    # Calculate the updated pool masses
    updated_pools = calculate_updated_pools(
        above_metabolic=above_metabolic,
        above_structural=above_structural,
        woody=woody,
        below_metabolic=below_metabolic,
        below_structural=below_structural,
        decomposed_excrement=decomposed_excrement,
        decomposed_carcasses=decomposed_carcasses,
        decay_rates=decay_rates,
        update_interval=update_interval,
        constants=constants,
    )

    # TODO - Work out a sensible function structure for the below
    # Find the changes in the lignin concentrations of the 3 relevant pools
    input_carbon_above_structural = np.full(
        (len(lignin_above_structural),),
        constants.litter_input_to_structural_above * update_interval,
    )
    input_carbon_woody = np.full(
        (len(lignin_woody),), constants.litter_input_to_woody * update_interval
    )
    input_carbon_below_structural = np.full(
        (len(lignin_below_structural),),
        constants.litter_input_to_structural_below * update_interval,
    )
    change_in_lignin_above_structural = calculate_change_in_lignin(
        input_carbon=input_carbon_above_structural,
        updated_pool_carbon=updated_pools["above_structural"],
        input_lignin=np.full(
            (len(lignin_above_structural),),
            constants.lignin_proportion_above_structural_input,
        ),
        old_pool_lignin=lignin_above_structural,
    )
    change_in_lignin_woody = calculate_change_in_lignin(
        input_carbon=input_carbon_woody,
        updated_pool_carbon=updated_pools["woody"],
        input_lignin=np.full(
            (len(lignin_woody),), constants.lignin_proportion_wood_input
        ),
        old_pool_lignin=lignin_woody,
    )
    change_in_lignin_below_structural = calculate_change_in_lignin(
        input_carbon=input_carbon_below_structural,
        updated_pool_carbon=updated_pools["below_structural"],
        input_lignin=np.full(
            (len(lignin_below_structural),),
            constants.lignin_proportion_below_structural_input,
        ),
        old_pool_lignin=lignin_below_structural,
    )

    # Construct dictionary of data arrays to return
    new_litter_pools = {
        "litter_pool_above_metabolic": DataArray(
            updated_pools["above_metabolic"], dims="cell_id"
        ),
        "litter_pool_above_structural": DataArray(
            updated_pools["above_structural"], dims="cell_id"
        ),
        "litter_pool_woody": DataArray(updated_pools["woody"], dims="cell_id"),
        "litter_pool_below_metabolic": DataArray(
            updated_pools["below_metabolic"], dims="cell_id"
        ),
        "litter_pool_below_structural": DataArray(
            updated_pools["below_structural"], dims="cell_id"
        ),
        "lignin_above_structural": DataArray(
            lignin_above_structural + change_in_lignin_above_structural, dims="cell_id"
        ),
        "lignin_woody": DataArray(
            lignin_woody + change_in_lignin_woody, dims="cell_id"
        ),
        "lignin_below_structural": DataArray(
            lignin_below_structural + change_in_lignin_below_structural, dims="cell_id"
        ),
        "litter_C_mineralisation_rate": DataArray(
            total_C_mineralisation_rate, dims="cell_id"
        ),
    }

    return new_litter_pools


def calculate_decay_rates(
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    lignin_above_structural: NDArray[np.float32],
    lignin_woody: NDArray[np.float32],
    lignin_below_structural: NDArray[np.float32],
    environmental_factors: dict[str, NDArray[np.float32]],
    constants: LitterConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate the decay rate for all five of the litter pools.

    Args:
        above_metabolic: Above ground metabolic litter pool [kg C m^-2]
        above_structural: Above ground structural litter pool [kg C m^-2]
        woody: The woody litter pool [kg C m^-2]
        below_metabolic: Below ground metabolic litter pool [kg C m^-2]
        below_structural: Below ground structural litter pool [kg C m^-2]
        lignin_above_structural: Proportion of above ground structural pool which is
            lignin [unitless]
        lignin_woody: Proportion of dead wood pool which is lignin [unitless]
        lignin_below_structural: Proportion of below ground structural pool which is
            lignin [unitless]
        environmental_factors: Factors capturing the effect that the physical
           environment (soil water + temperature) has on litter decay rates [unitless].
        constants: Set of constants for the litter model

    Returns:
        A dictionary containing the decay rate for each of the five litter pools.
    """

    # Calculate decay rate for each pool
    metabolic_above_decay = calculate_litter_decay_metabolic_above(
        environmental_factors["temp_above"],
        above_metabolic,
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_above,
    )
    structural_above_decay = calculate_litter_decay_structural_above(
        environmental_factors["temp_above"],
        above_structural,
        lignin_above_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_above,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    woody_decay = calculate_litter_decay_woody(
        environmental_factors["temp_above"],
        woody,
        lignin_woody,
        litter_decay_coefficient=constants.litter_decay_constant_woody,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    metabolic_below_decay = calculate_litter_decay_metabolic_below(
        environmental_factors["temp_below"],
        environmental_factors["water"],
        below_metabolic,
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_below,
    )
    structural_below_decay = calculate_litter_decay_structural_below(
        environmental_factors["temp_below"],
        environmental_factors["water"],
        below_structural,
        lignin_below_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_below,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )

    # Then return all the decay rates in a dictionary
    return {
        "metabolic_above": metabolic_above_decay,
        "structural_above": structural_above_decay,
        "woody": woody_decay,
        "metabolic_below": metabolic_below_decay,
        "structural_below": structural_below_decay,
    }


def calculate_total_C_mineralised(
    decay_rates: dict[str, NDArray[np.float32]], constants: LitterConsts
) -> NDArray[np.float32]:
    """Calculate the total carbon mineralisation rate from all five litter pools.

    Args:
        decay_rates: Dictionary containing the rates of decay for all 5 litter pools:
            above ground metabolic, above ground structural, dead wood, below ground
            metabolic, and below ground structural [kg C m^-2 day^-1]
        constants: Set of constants for the litter model

    Returns:
        Rate of carbon mineralisation from litter into soil [kg C m^-3 day^-1].
    """

    # Calculate mineralisation from each pool
    metabolic_above_mineral = calculate_carbon_mineralised(
        decay_rates["metabolic_above"], carbon_use_efficiency=constants.cue_metabolic
    )
    structural_above_mineral = calculate_carbon_mineralised(
        decay_rates["structural_above"],
        carbon_use_efficiency=constants.cue_structural_above_ground,
    )
    woody_mineral = calculate_carbon_mineralised(
        decay_rates["woody"],
        carbon_use_efficiency=constants.cue_woody,
    )
    metabolic_below_mineral = calculate_carbon_mineralised(
        decay_rates["metabolic_below"], carbon_use_efficiency=constants.cue_metabolic
    )
    structural_below_mineral = calculate_carbon_mineralised(
        decay_rates["structural_below"],
        carbon_use_efficiency=constants.cue_structural_below_ground,
    )

    # Calculate mineralisation rate
    total_C_mineralisation_rate = (
        metabolic_above_mineral
        + structural_above_mineral
        + woody_mineral
        + metabolic_below_mineral
        + structural_below_mineral
    )

    # Convert mineralisation rate into kg m^-3 units (from kg m^-2)
    return total_C_mineralisation_rate / constants.depth_of_active_layer


def calculate_updated_pools(
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    decomposed_excrement: NDArray[np.float32],
    decomposed_carcasses: NDArray[np.float32],
    decay_rates: dict[str, NDArray[np.float32]],
    update_interval: float,
    constants: LitterConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate the updated mass of each litter pool.

    This function is not intended to be used continuously, and returns the new value for
    each pool after the update interval, rather than a rate of change to be integrated.

    Args:
        above_metabolic: Above ground metabolic litter pool [kg C m^-2]
        above_structural: Above ground structural litter pool [kg C m^-2]
        woody: The woody litter pool [kg C m^-2]
        below_metabolic: Below ground metabolic litter pool [kg C m^-2]
        below_structural: Below ground structural litter pool [kg C m^-2]
        decomposed_excrement: Input rate of excrement from the animal model [kg C m^-2
            day^-1]
        decomposed_carcasses: Input rate of (partially) decomposed carcass biomass from
            the animal model [kg C m^-2 day^-1]
        decay_rates: Dictionary containing the rates of decay for all 5 litter pools
            (above ground metabolic, above ground structural, dead wood, below ground
            metabolic, and below ground structural) [kg C m^-2 day^-1]
        update_interval: Interval that the litter pools are being updated for [days]
        constants: Set of constants for the litter model

    Returns:
        Dictionary containing the updated pool densities for all 5 litter pools (above
        ground metabolic, above ground structural, dead wood, below ground metabolic,
        and below ground structural) [kg C m^-2]
    """

    # Net pool changes are found by combining input and decay rates, and then
    # multiplying by the update time step.
    change_in_metabolic_above = (
        constants.litter_input_to_metabolic_above
        + decomposed_excrement
        + decomposed_carcasses
        - decay_rates["metabolic_above"]
    ) * update_interval
    change_in_structural_above = (
        constants.litter_input_to_structural_above - decay_rates["structural_above"]
    ) * update_interval
    change_in_woody = (
        constants.litter_input_to_woody - decay_rates["woody"]
    ) * update_interval
    change_in_metabolic_below = (
        constants.litter_input_to_metabolic_below - decay_rates["metabolic_below"]
    ) * update_interval
    change_in_structural_below = (
        constants.litter_input_to_structural_below - decay_rates["structural_below"]
    ) * update_interval

    # New value for each pool is found and returned in a dictionary
    return {
        "above_metabolic": above_metabolic + change_in_metabolic_above,
        "above_structural": above_structural + change_in_structural_above,
        "woody": woody + change_in_woody,
        "below_metabolic": below_metabolic + change_in_metabolic_below,
        "below_structural": below_structural + change_in_structural_below,
    }


def calculate_environmental_factors(
    surface_temp: NDArray[np.float32],
    topsoil_temp: NDArray[np.float32],
    water_potential: NDArray[np.float32],
    constants: LitterConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate the impact of the environment has on litter decay across litter layers.

    For the above ground layer the impact of temperature is calculated, and for the
    below ground layer the effect of temperature and soil water potential are
    considered.

    Args:
        surface_temp: Temperature of soil surface, which is assumed to be the same
            temperature as the above ground litter [C]
        topsoil_temp: Temperature of topsoil layer, which is assumed to be the same
            temperature as the below ground litter [C]
        water_potential: Water potential of the topsoil layer [kPa]
        constants: Set of constants for the litter model

    Returns:
        A dictionary containing three environmental factors, one for the effect of
        temperature on above ground litter decay, one for the effect of temperature on
        below ground litter decay, and one for the effect of soil water potential on
        below ground litter decay.
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

    # Return all three factors in a single dictionary
    return {
        "temp_above": temperature_factor_above,
        "temp_below": temperature_factor_below,
        "water": water_factor,
    }


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


def calculate_litter_chemistry_factor(
    lignin_proportion: NDArray[np.float32], lignin_inhibition_factor: float
) -> NDArray[np.float32]:
    """Calculate the effect that litter chemistry has on litter decomposition rates.

    This expression is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        lignin_proportion: The proportion of the polymers in the litter pool that are
            lignin (or similar) [unitless]
        lignin_inhibition_factor: An exponential factor expressing the extent to which
            lignin inhibits the breakdown of litter [unitless]

    Returns:
        A factor that captures the impact of litter chemistry on litter decay rates
    """

    return np.exp(lignin_inhibition_factor * lignin_proportion)


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
    lignin_proportion: NDArray[np.float32],
    litter_decay_coefficient: float,
    lignin_inhibition_factor: float,
) -> NDArray[np.float32]:
    """Calculate decay of above ground structural litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        litter_pool_above_structural: The size of the above ground structural litter
            pool [kg C m^-2]
        lignin_proportion: The proportion of the above ground structural pool which is
            lignin [unitless]
        litter_decay_coefficient: The decay coefficient for the above ground structural
            litter pool [day^-1]
        lignin_inhibition_factor: An exponential factor expressing the extent to which
            lignin inhibits the breakdown of litter [unitless]

    Returns:
        Rate of decay of the above ground structural litter pool [kg C m^-2 day^-1]
    """

    litter_chemistry_factor = calculate_litter_chemistry_factor(
        lignin_proportion, lignin_inhibition_factor=lignin_inhibition_factor
    )

    return (
        litter_decay_coefficient
        * temperature_factor
        * litter_pool_above_structural
        * litter_chemistry_factor
    )


def calculate_litter_decay_woody(
    temperature_factor: NDArray[np.float32],
    litter_pool_woody: NDArray[np.float32],
    lignin_proportion: NDArray[np.float32],
    litter_decay_coefficient: float,
    lignin_inhibition_factor: float,
) -> NDArray[np.float32]:
    """Calculate decay of the woody litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        litter_pool_woody: The size of the woody litter pool [kg C m^-2]
        lignin_proportion: The proportion of the woody litter pool which is lignin
            [unitless]
        litter_decay_coefficient: The decay coefficient for the woody litter pool
            [day^-1]
        lignin_inhibition_factor: An exponential factor expressing the extent to which
            lignin inhibits the breakdown of litter [unitless]

    Returns:
        Rate of decay of the woody litter pool [kg C m^-2 day^-1]
    """

    litter_chemistry_factor = calculate_litter_chemistry_factor(
        lignin_proportion, lignin_inhibition_factor=lignin_inhibition_factor
    )

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
    lignin_proportion: NDArray[np.float32],
    litter_decay_coefficient: float,
    lignin_inhibition_factor: float,
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
        lignin_proportion: The proportion of the below ground structural pool which is
            lignin [unitless]
        litter_decay_coefficient: The decay coefficient for the below ground structural
            litter pool [day^-1]
        lignin_inhibition_factor: An exponential factor expressing the extent to which
            lignin inhibits the breakdown of litter [unitless]

    Returns:
        Rate of decay of the below ground structural litter pool [kg C m^-2 day^-1]
    """

    litter_chemistry_factor = calculate_litter_chemistry_factor(
        lignin_proportion, lignin_inhibition_factor=lignin_inhibition_factor
    )

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


def calculate_change_in_lignin(
    input_carbon: NDArray[np.float32],
    updated_pool_carbon: NDArray[np.float32],
    input_lignin: NDArray[np.float32],
    old_pool_lignin: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate the change in the lignin concentration of a particular litter pool.

    This change is found by calculating the difference between the previous lignin
    concentration of the pool and the lignin concentration of the inputs. This
    difference is then multiplied by the ratio of the mass of carbon added to pool and
    the final (carbon) mass of the pool.

    Args:
        input_carbon: The total carbon mass of inputs to the litter pool [kg C m^-2]
        updated_pool_carbon: The total carbon mass of the litter pool after inputs and
            decay [kg C m^-2]
        input_lignin: The proportion of the input carbon that is lignin [unitless]
        old_pool_lignin: The proportion of the carbon mass of the original litter pool
            that was lignin [unitless]

    Returns:
        The total change in the lignin concentration of the pool over the full time step
        [unitless]
    """

    return (input_carbon / (updated_pool_carbon)) * (input_lignin - old_pool_lignin)
