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

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.litter.chemistry import calculate_litter_chemistry_factor
from virtual_ecosystem.models.litter.env_factors import (
    calculate_environmental_factors,
)
from virtual_ecosystem.models.litter.inputs import LitterInputs
from virtual_ecosystem.models.litter.losses import LitterLosses
from virtual_ecosystem.models.litter.model_config import LitterConstants


def calculate_post_consumption_pools(
    above_metabolic: NDArray[np.floating],
    above_structural: NDArray[np.floating],
    woody: NDArray[np.floating],
    below_metabolic: NDArray[np.floating],
    below_structural: NDArray[np.floating],
    consumption_above_metabolic: NDArray[np.floating],
    consumption_above_structural: NDArray[np.floating],
    consumption_woody: NDArray[np.floating],
    consumption_below_metabolic: NDArray[np.floating],
    consumption_below_structural: NDArray[np.floating],
) -> dict[str, NDArray[np.floating]]:
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
    lignin_above_structural: NDArray[np.floating],
    lignin_woody: NDArray[np.floating],
    lignin_below_structural: NDArray[np.floating],
    air_temperatures: DataArray,
    soil_temperatures: DataArray,
    water_potentials: DataArray,
    layer_structure: LayerStructure,
    constants: LitterConstants,
) -> dict[str, NDArray[np.floating]]:
    """Calculate the decay rate for all five of the litter pools.

    Args:
        lignin_above_structural: Proportion of above ground structural pool which is
            lignin [kg lignin C (kg C)^-1]
        lignin_woody: Proportion of dead wood pool which is lignin
            [kg lignin C (kg C)^-1]
        lignin_below_structural: Proportion of below ground structural pool which is
            lignin [kg lignin C (kg C)^-1]
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
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_above,
    )
    structural_above_decay = calculate_litter_decay_structural_above(
        temperature_factor=env_factors["temp_above"],
        lignin_proportion=lignin_above_structural,
        litter_decay_coefficient=constants.litter_decay_constant_structural_above,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    woody_decay = calculate_litter_decay_woody(
        temperature_factor=env_factors["temp_above"],
        lignin_proportion=lignin_woody,
        litter_decay_coefficient=constants.litter_decay_constant_woody,
        lignin_inhibition_factor=constants.lignin_inhibition_factor,
    )
    metabolic_below_decay = calculate_litter_decay_metabolic_below(
        temperature_factor=env_factors["temp_below"],
        moisture_factor=env_factors["water"],
        litter_decay_coefficient=constants.litter_decay_constant_metabolic_below,
    )
    structural_below_decay = calculate_litter_decay_structural_below(
        temperature_factor=env_factors["temp_below"],
        moisture_factor=env_factors["water"],
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
    litter_losses: LitterLosses,
    model_constants: LitterConstants,
    core_constants: CoreConstants,
    update_interval: float,
) -> NDArray[np.floating]:
    """Calculate the total carbon mineralisation rate from all five litter pools.

    Args:
        litter_losses: Dataclass containing the total nutrient loss from each litter
            pool
        model_constants: Set of constants for the litter model
        core_constants: Set of core constants shared between all models
        update_interval: Interval that the litter pools are being updated for [days]

    Returns:
        Rate of carbon mineralisation from litter into soil [kg C m^-3 day^-1].
    """

    # Calculate mineralisation from each pool
    metabolic_above_mineral = calculate_carbon_mineralised(
        carbon_loss=litter_losses.above_metabolic_carbon,
        carbon_use_efficiency=model_constants.cue_metabolic,
    )
    structural_above_mineral = calculate_carbon_mineralised(
        carbon_loss=litter_losses.above_structural_carbon,
        carbon_use_efficiency=model_constants.cue_structural_above_ground,
    )
    woody_mineral = calculate_carbon_mineralised(
        carbon_loss=litter_losses.woody_carbon,
        carbon_use_efficiency=model_constants.cue_woody,
    )
    metabolic_below_mineral = calculate_carbon_mineralised(
        carbon_loss=litter_losses.below_metabolic_carbon,
        carbon_use_efficiency=model_constants.cue_metabolic,
    )
    structural_below_mineral = calculate_carbon_mineralised(
        carbon_loss=litter_losses.below_structural_carbon,
        carbon_use_efficiency=model_constants.cue_structural_below_ground,
    )

    # Calculate mineralisation rate
    total_C_mineralised = (
        metabolic_above_mineral
        + structural_above_mineral
        + woody_mineral
        + metabolic_below_mineral
        + structural_below_mineral
    )

    # Convert total mineralisation rate into kg m^-3 day^-1 units (from kg m^-2)
    return total_C_mineralised / (
        core_constants.max_depth_of_microbial_activity * update_interval
    )


def calculate_updated_pools(
    post_consumption_pools: dict[str, NDArray[np.floating]],
    decay_rates: dict[str, NDArray[np.floating]],
    litter_inputs: LitterInputs,
    update_interval: float,
) -> dict[str, NDArray[np.floating]]:
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

    return {
        "above_metabolic": calculate_final_pool_size(
            input_rate=litter_inputs.above_metabolic,
            decay_rate=decay_rates["metabolic_above"],
            initial_pool=post_consumption_pools["above_metabolic"],
            update_interval=update_interval,
        ),
        "above_structural": calculate_final_pool_size(
            input_rate=litter_inputs.above_structural,
            decay_rate=decay_rates["structural_above"],
            initial_pool=post_consumption_pools["above_structural"],
            update_interval=update_interval,
        ),
        "woody": calculate_final_pool_size(
            input_rate=litter_inputs.woody,
            decay_rate=decay_rates["woody"],
            initial_pool=post_consumption_pools["woody"],
            update_interval=update_interval,
        ),
        "below_metabolic": calculate_final_pool_size(
            input_rate=litter_inputs.below_metabolic,
            decay_rate=decay_rates["metabolic_below"],
            initial_pool=post_consumption_pools["below_metabolic"],
            update_interval=update_interval,
        ),
        "below_structural": calculate_final_pool_size(
            input_rate=litter_inputs.below_structural,
            decay_rate=decay_rates["structural_below"],
            initial_pool=post_consumption_pools["below_structural"],
            update_interval=update_interval,
        ),
    }


def calculate_final_pool_size(
    input_rate: NDArray[np.floating],
    decay_rate: NDArray[np.floating],
    initial_pool: NDArray[np.floating],
    update_interval: float,
):
    """Calculate the final size of a litter pool based on input and decay rates.

    This function use an exact solution to the litter input and decay dynamics to find
    the pool size at the end of the update interval. This involves finding the
    equilibrium pool size based on the ratio of the input rate to the decay rate. The
    actual pool size exponentially decays from its initial size towards this equilibrium
    size with at the litter decay rate.

    Args:
        input_rate: The rate of input of carbon to the new pool [kg C m^-2 day^-1]
        decay_rate: The rate at which the pool decays (in carbon terms) [kg C m^-2
            day^-1]
        initial_pool: The size of the pool at the start of the update interval [kg C
            m^-2]
        update_interval: Interval that the litter pools are being updated for [days]

    Returns:
        The size of the pool at the end of the time step [kg C m^-2]
    """

    equilibrium_pool = input_rate / decay_rate

    return equilibrium_pool - (equilibrium_pool - initial_pool) * np.exp(
        -decay_rate * update_interval
    )


def calculate_litter_decay_metabolic_above(
    temperature_factor: NDArray[np.floating],
    litter_decay_coefficient: float,
) -> NDArray[np.floating]:
    """Calculate decay of above ground metabolic litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        litter_decay_coefficient: The decay coefficient for the above ground metabolic
            litter pool [day^-1]

    Returns:
        Rate of decay of the above ground metabolic litter pool [kg C m^-2 day^-1]
    """

    return litter_decay_coefficient * temperature_factor


def calculate_litter_decay_structural_above(
    temperature_factor: NDArray[np.floating],
    lignin_proportion: NDArray[np.floating],
    litter_decay_coefficient: float,
    lignin_inhibition_factor: float,
) -> NDArray[np.floating]:
    """Calculate decay of above ground structural litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        lignin_proportion: The proportion of the above ground structural pool which is
            lignin [kg lignin C (kg C)^-1]
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

    return litter_decay_coefficient * temperature_factor * litter_chemistry_factor


def calculate_litter_decay_woody(
    temperature_factor: NDArray[np.floating],
    lignin_proportion: NDArray[np.floating],
    litter_decay_coefficient: float,
    lignin_inhibition_factor: float,
) -> NDArray[np.floating]:
    """Calculate decay of the woody litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        lignin_proportion: The proportion of the woody litter pool which is lignin
            [kg lignin C (kg C)^-1]
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

    return litter_decay_coefficient * temperature_factor * litter_chemistry_factor


def calculate_litter_decay_metabolic_below(
    temperature_factor: NDArray[np.floating],
    moisture_factor: NDArray[np.floating],
    litter_decay_coefficient: float,
) -> NDArray[np.floating]:
    """Calculate decay of below ground metabolic litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        moisture_factor: A multiplicative factor capturing the impact of soil moisture
            on litter decomposition [unitless]
        litter_decay_coefficient: The decay coefficient for the below ground metabolic
            litter pool [day^-1]

    Returns:
        Rate of decay of the below ground metabolic litter pool [kg C m^-2 day^-1]
    """

    return litter_decay_coefficient * temperature_factor * moisture_factor


def calculate_litter_decay_structural_below(
    temperature_factor: NDArray[np.floating],
    moisture_factor: NDArray[np.floating],
    lignin_proportion: NDArray[np.floating],
    litter_decay_coefficient: float,
    lignin_inhibition_factor: float,
) -> NDArray[np.floating]:
    """Calculate decay of below ground structural litter pool.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature_factor: A multiplicative factor capturing the impact of temperature
            on litter decomposition [unitless]
        moisture_factor: A multiplicative factor capturing the impact of soil moisture
            on litter decomposition [unitless]
        lignin_proportion: The proportion of the below ground structural pool which is
            lignin [kg lignin C (kg C)^-1]
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
    )


def calculate_carbon_mineralised(
    carbon_loss: NDArray[np.floating], carbon_use_efficiency: float
) -> NDArray[np.floating]:
    """Calculate fraction of carbon loss that gets mineralised.

    TODO - This function could also be used to track carbon respired, if/when we decide
    to track that.

    Args:
        carbon_loss: Total amount of carbon lost from the litter pool [kg C m^-2]
        carbon_use_efficiency: Carbon use efficiency of litter pool [unitless]

    Returns:
        Rate at which carbon is mineralised from the litter pool [kg C m^-2 day^-1]
    """

    return carbon_use_efficiency * carbon_loss
