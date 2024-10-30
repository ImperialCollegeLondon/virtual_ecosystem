"""The ``models.litter.carbon`` module  tracks the carbon content of the litter pools
for the Virtual Ecosystem. Pools are divided into above and below ground pools, with
below ground pools affected by both soil moisture and temperature, and above ground
pools just affected by soil surface temperatures. The pools are also divided based on
the recalcitrance of their inputs, dead wood is given a separate pool, and all other
inputs are divided between metabolic and structural pools. Recalcitrant litter contains
hard to break down compounds, principally lignin. The metabolic litter pool contains the
non-recalcitrant litter and so breaks down quickly. Whereas, the structural litter
contains the recalcitrant litter.

We consider 5 pools rather than 6, as it's not really possible to parametrise the below
ground dead wood pool. So, all dead wood gets included in the above ground woody litter
pool.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.models.litter.chemistry import calculate_litter_chemistry_factor
from virtual_ecosystem.models.litter.constants import LitterConsts
from virtual_ecosystem.models.litter.env_factors import (
    calculate_environmental_factors,
)
from virtual_ecosystem.models.litter.inputs import LitterInputs


def calculate_post_consumption_pools(
    above_metabolic: NDArray[np.float32],
    above_structural: NDArray[np.float32],
    woody: NDArray[np.float32],
    below_metabolic: NDArray[np.float32],
    below_structural: NDArray[np.float32],
    consumption_above_metabolic: NDArray[np.float32],
    consumption_above_structural: NDArray[np.float32],
    consumption_woody: NDArray[np.float32],
    consumption_below_metabolic: NDArray[np.float32],
    consumption_below_structural: NDArray[np.float32],
) -> dict[str, NDArray[np.float32]]:
    """Calculates the size of the five litter pools after animal consumption.

    At present the Virtual Ecosystem gives animals priority for consumption of litter.
    And so only the litter not consumed by animals has a chance to decay. This is a
    major assumption that we may have to revisit in future.

    Args:
        above_metabolic: Above ground metabolic litter pool [kg C m^-2]
        above_structural: Above ground structural litter pool [kg C m^-2]
        woody: The woody litter pool [kg C m^-2]
        below_metabolic: Below ground metabolic litter pool [kg C m^-2]
        below_structural: Below ground structural litter pool [kg C m^-2]
        consumption_above_metabolic: Amount of above-ground metabolic litter that has
            been consumed by animals [kg C m^-2]
        consumption_above_structural: Amount of above-ground structural litter that has
            been consumed by animals [kg C m^-2]
        consumption_woody: Amount of woody litter that has been consumed by animals [kg
            C m^-2]
        consumption_below_metabolic: Amount of below-ground metabolic litter that has
            been consumed by animals [kg C m^-2]
        consumption_below_structural: Amount of below-ground structural litter that has
            been consumed by animals [kg C m^-2]

    Returns:
        A dictionary containing the size of each litter pool after the mass consumed by
        animals has been removed [kg C m^-2].
    """

    return {
        "above_metabolic": above_metabolic - consumption_above_metabolic,
        "above_structural": above_structural - consumption_above_structural,
        "woody": woody - consumption_woody,
        "below_metabolic": below_metabolic - consumption_below_metabolic,
        "below_structural": below_structural - consumption_below_structural,
    }


def calculate_decay_rates(
    post_consumption_pools: dict[str, NDArray[np.float32]],
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
        post_consumption_pools: The five litter pools after animal consumption has been
            subtracted [kg C m^-2]
        lignin_above_structural: Proportion of above ground structural pool which is
            lignin [unitless]
        lignin_woody: Proportion of dead wood pool which is lignin [unitless]
        lignin_below_structural: Proportion of below ground structural pool which is
            lignin [unitless]
        air_temperatures: Air temperatures, for all above ground layers [C]
        soil_temperatures: Soil temperatures, for all soil layers [C]
        water_potentials: Water potentials, for all soil layers [kPa]
        layer_structure: The LayerStructure instance for the simulation.
        constants: Set of constants for the litter model

    Decay rates depend on lignin proportions as well as a range of environmental
    factors. These environmental factors are calculated as part of this function.

    Returns:
        A dictionary containing the decay rate for each of the five litter pools.
    """

    # Calculate environmental factors
    env_factors = calculate_environmental_factors(
        air_temperatures=air_temperatures,
        soil_temperatures=soil_temperatures,
        water_potentials=water_potentials,
        layer_structure=layer_structure,
        constants=constants,
    )

    # Calculate decay rate for each pool
    metabolic_above_decay = calculate_litter_decay_metabolic_above(
        temperature_factor=env_factors["temp_above"],
        litter_pool_above_metabolic=post_consumption_pools["above_metabolic"],
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_above,
    )
    structural_above_decay = calculate_litter_decay_structural_above(
        temperature_factor=env_factors["temp_above"],
        litter_pool_above_structural=post_consumption_pools["above_structural"],
        lignin_proportion=lignin_above_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_above,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    woody_decay = calculate_litter_decay_woody(
        temperature_factor=env_factors["temp_above"],
        litter_pool_woody=post_consumption_pools["woody"],
        lignin_proportion=lignin_woody,
        litter_decay_coefficient=constants.litter_decay_constant_woody,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    metabolic_below_decay = calculate_litter_decay_metabolic_below(
        temperature_factor=env_factors["temp_below"],
        moisture_factor=env_factors["water"],
        litter_pool_below_metabolic=post_consumption_pools["below_metabolic"],
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_below,
    )
    structural_below_decay = calculate_litter_decay_structural_below(
        temperature_factor=env_factors["temp_below"],
        moisture_factor=env_factors["water"],
        litter_pool_below_structural=post_consumption_pools["below_structural"],
        lignin_proportion=lignin_below_structural,
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
    post_consumption_pools: dict[str, NDArray[np.float32]],
    decay_rates: dict[str, NDArray[np.float32]],
    litter_inputs: LitterInputs,
    update_interval: float,
) -> dict[str, NDArray[np.float32]]:
    """Calculate the updated mass of each litter pool.

    This function is not intended to be used continuously, and returns the new value for
    each pool after the update interval, rather than a rate of change to be integrated.

    Args:
        post_consumption_pools: The five litter pools after animal consumption has been
            subtracted [kg C m^-2]
        decay_rates: Dictionary containing the rates of decay for all 5 litter pools
            [kg C m^-2 day^-1]
        litter_inputs: An LitterInputs instance containing the total input of each plant
            biomass type, the proportion of the input that goes to the relevant
            metabolic pool for each input type (expect deadwood) and the total input
            into each litter pool.
        update_interval: Interval that the litter pools are being updated for [days]
        constants: Set of constants for the litter model

    Returns:
        Dictionary containing the updated pool densities for all 5 litter pools (above
        ground metabolic, above ground structural, dead wood, below ground metabolic,
        and below ground structural) [kg C m^-2]
    """

    # Net pool changes are found by combining input and decay rates, and then
    # multiplying by the update time step.
    change_in_metabolic_above = litter_inputs.input_above_metabolic - (
        decay_rates["metabolic_above"] * update_interval
    )
    change_in_structural_above = litter_inputs.input_above_structural - (
        decay_rates["structural_above"] * update_interval
    )
    change_in_woody = litter_inputs.input_woody - (
        decay_rates["woody"] * update_interval
    )
    change_in_metabolic_below = litter_inputs.input_below_metabolic - (
        decay_rates["metabolic_below"] * update_interval
    )
    change_in_structural_below = litter_inputs.input_below_structural - (
        decay_rates["structural_below"] * update_interval
    )

    # New value for each pool is found and returned in a dictionary
    return {
        "above_metabolic": post_consumption_pools["above_metabolic"]
        + change_in_metabolic_above,
        "above_structural": post_consumption_pools["above_structural"]
        + change_in_structural_above,
        "woody": post_consumption_pools["woody"] + change_in_woody,
        "below_metabolic": post_consumption_pools["below_metabolic"]
        + change_in_metabolic_below,
        "below_structural": post_consumption_pools["below_structural"]
        + change_in_structural_below,
    }


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
