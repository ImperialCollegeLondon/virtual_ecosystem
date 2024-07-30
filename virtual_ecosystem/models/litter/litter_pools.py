"""The ``models.litter.litter_pools`` module  simulates the litter pools for the Virtual
Ecosystem. Pools are divided into above and below ground pools, with below ground pools
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
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.models.litter.constants import LitterConsts
from virtual_ecosystem.models.litter.env_factors import (
    calculate_soil_water_effect_on_litter_decomp,
    calculate_temperature_effect_on_litter_decomp,
)


# TODO - Work out if it makes sense to make the env_factor calculation a separate
# function
def calculate_decay_rates(
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    lignin_above_structural: NDArray[np.float32],
    lignin_woody: NDArray[np.float32],
    lignin_below_structural: NDArray[np.float32],
    air_temperatures: DataArray,
    soil_temperatures: DataArray,
    water_potentials: DataArray,
    layer_structure: LayerStructure,
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
        air_temperatures: Air temperatures, for all above ground layers [C]
        soil_temperatures: Soil temperatures, for all soil layers [C]
        water_potentials: Water potentials, for all soil layers []
        layer_structure: The LayerStructure instance for the simulation.
        constants: Set of constants for the litter model

    TODO - Fill out this to explain the logic of the function, or alternatively that it
    calls another function that chooses the appropriate layers for environmental
    variables

    Returns:
        A dictionary containing the decay rate for each of the five litter pools.
    """

    # Find the temperature for each of the relevant layers, and the water potential for
    # the topsoil layer
    surface_temp = air_temperatures[layer_structure.index_surface_scalar].to_numpy()
    # TODO - Write a function to average and return these results
    topsoil_temp = soil_temperatures[layer_structure.index_topsoil_scalar].to_numpy()
    water_potential = water_potentials[layer_structure.index_topsoil_scalar].to_numpy()
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
    water_factor = calculate_soil_water_effect_on_litter_decomp(
        water_potential=water_potential,
        water_potential_halt=constants.litter_decay_water_potential_halt,
        water_potential_opt=constants.litter_decay_water_potential_optimum,
        moisture_response_curvature=constants.moisture_response_curvature,
    )

    # Calculate decay rate for each pool
    metabolic_above_decay = calculate_litter_decay_metabolic_above(
        temperature_factor_above,
        above_metabolic,
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_above,
    )
    structural_above_decay = calculate_litter_decay_structural_above(
        temperature_factor_above,
        above_structural,
        lignin_above_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_above,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    woody_decay = calculate_litter_decay_woody(
        temperature_factor_above,
        woody,
        lignin_woody,
        litter_decay_coefficient=constants.litter_decay_constant_woody,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
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
    decay_rates: dict[str, NDArray[np.float32]],
    model_constants: LitterConsts,
    core_constants: CoreConsts,
) -> NDArray[np.float32]:
    """Calculate the total carbon mineralisation rate from all five litter pools.

    Args:
        decay_rates: Dictionary containing the rates of decay for all 5 litter pools
            [kg C m^-2 day^-1]
        model_constants: Set of constants for the litter model
        core_constants: Set of core constants shared between all models

    Returns:
        Rate of carbon mineralisation from litter into soil [kg C m^-3 day^-1].
    """

    # Calculate mineralisation from each pool
    metabolic_above_mineral = calculate_carbon_mineralised(
        decay_rates["metabolic_above"],
        carbon_use_efficiency=model_constants.cue_metabolic,
    )
    structural_above_mineral = calculate_carbon_mineralised(
        decay_rates["structural_above"],
        carbon_use_efficiency=model_constants.cue_structural_above_ground,
    )
    woody_mineral = calculate_carbon_mineralised(
        decay_rates["woody"],
        carbon_use_efficiency=model_constants.cue_woody,
    )
    metabolic_below_mineral = calculate_carbon_mineralised(
        decay_rates["metabolic_below"],
        carbon_use_efficiency=model_constants.cue_metabolic,
    )
    structural_below_mineral = calculate_carbon_mineralised(
        decay_rates["structural_below"],
        carbon_use_efficiency=model_constants.cue_structural_below_ground,
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
    return total_C_mineralisation_rate / core_constants.max_depth_of_microbial_activity


def calculate_updated_pools(
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    decomposed_excrement: NDArray[np.float32],
    decomposed_carcasses: NDArray[np.float32],
    decay_rates: dict[str, NDArray[np.float32]],
    plant_inputs: dict[str, NDArray[np.float32]],
    update_interval: float,
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
            [kg C m^-2 day^-1]
        plant_inputs: Dictionary containing the amount of each litter type that is added
            from the plant model in this time step [kg C m^-2]
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
        plant_inputs["above_ground_metabolic"]
        + (decomposed_excrement + decomposed_carcasses - decay_rates["metabolic_above"])
        * update_interval
    )
    change_in_structural_above = plant_inputs["above_ground_structural"] - (
        decay_rates["structural_above"] * update_interval
    )
    change_in_woody = plant_inputs["woody"] - (decay_rates["woody"] * update_interval)
    change_in_metabolic_below = plant_inputs["below_ground_metabolic"] - (
        decay_rates["metabolic_below"] * update_interval
    )
    change_in_structural_below = plant_inputs["below_ground_structural"] - (
        decay_rates["structural_below"] * update_interval
    )

    # New value for each pool is found and returned in a dictionary
    return {
        "above_metabolic": above_metabolic + change_in_metabolic_above,
        "above_structural": above_structural + change_in_structural_above,
        "woody": woody + change_in_woody,
        "below_metabolic": below_metabolic + change_in_metabolic_below,
        "below_structural": below_structural + change_in_structural_below,
    }


def calculate_lignin_updates(
    lignin_above_structural: NDArray[np.float32],
    lignin_woody: NDArray[np.float32],
    lignin_below_structural: NDArray[np.float32],
    plant_inputs: dict[str, NDArray[np.float32]],
    input_lignin: dict[str, NDArray[np.float32]],
    updated_pools: dict[str, NDArray[np.float32]],
) -> dict[str, NDArray[np.float32]]:
    """Calculate the changes in lignin proportion for the relevant litter pools.

    The relevant pools are the two structural pools, and the dead wood pool. This
    function calculates the total change over the entire time step, so cannot be used in
    an integration process.

    Args:
        lignin_above_structural: Proportion of above ground structural pool which is
            lignin [unitless]
        lignin_woody: Proportion of dead wood pool which is lignin [unitless]
        lignin_below_structural: Proportion of below ground structural pool which is
            lignin [unitless]
        plant_inputs: Dictionary containing the amount of each litter type that is added
            from the plant model in this time step [kg C m^-2]
        input_lignin: Dictionary containing the lignin concentration of the input to
            each of the three lignin containing litter pools [kg lignin kg C^-1]
        updated_pools: Dictionary containing the updated pool densities for all 5 litter
            pools [kg C m^-2]

    Returns:
        Dictionary containing the updated lignin proportions for the 3 relevant litter
        pools (above ground structural, dead wood, and below ground structural) [kg C
        m^-2]
    """

    change_in_lignin_above_structural = calculate_change_in_lignin(
        input_carbon=plant_inputs["above_ground_structural"],
        updated_pool_carbon=updated_pools["above_structural"],
        input_lignin=input_lignin["above_structural"],
        old_pool_lignin=lignin_above_structural,
    )
    change_in_lignin_woody = calculate_change_in_lignin(
        input_carbon=plant_inputs["woody"],
        updated_pool_carbon=updated_pools["woody"],
        input_lignin=input_lignin["woody"],
        old_pool_lignin=lignin_woody,
    )
    change_in_lignin_below_structural = calculate_change_in_lignin(
        input_carbon=plant_inputs["below_ground_structural"],
        updated_pool_carbon=updated_pools["below_structural"],
        input_lignin=input_lignin["below_structural"],
        old_pool_lignin=lignin_below_structural,
    )

    return {
        "above_structural": change_in_lignin_above_structural,
        "woody": change_in_lignin_woody,
        "below_structural": change_in_lignin_below_structural,
    }


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
    input_carbon: float | NDArray[np.float32],
    updated_pool_carbon: NDArray[np.float32],
    input_lignin: float | NDArray[np.float32],
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
