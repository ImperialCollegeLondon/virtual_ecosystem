"""The ``models.litter.env_factors`` module contains functions that are used to
capture the impact that environmental factors have on litter decay rates. These include
temperature and soil water potential.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.models.litter.model_config import LitterConstants
from virtual_ecosystem.models.soil.env_factors import (
    calculate_water_potential_impact_on_microbes,
)


def calculate_environmental_factors(
    air_temperatures: DataArray,
    soil_temperatures: DataArray,
    water_potentials: DataArray,
    layer_structure: LayerStructure,
    constants: LitterConstants,
):
    """Calculate the impact of the environment has on litter decay across litter layers.

    For the above ground layer the impact of temperature is calculated, and for the
    below ground layer the effect of temperature and soil water potential are both
    calculated.

    The relevant above ground temperature is the surface temperature, which can be
    easily extracted from the temperature data. It's more complex for the below ground
    temperature and the water potential as the relevant values are averages across the
    microbially active depth. These are calculated by averaging across the soil layers
    with each layer weighted by the proportion of the total microbially active depth it
    represents.

    If a shallow microbially active depth is used then below ground litter decomposition
    will be exposed to a high degree of environmental variability. This is
    representative of the real world, but needs to be kept in mind when comparing to
    other models.

    Args:
        air_temperatures: Air temperatures, for all above ground layers [Celsius]
        soil_temperatures: Soil temperatures, for all soil layers [Celsius]
        water_potentials: Water potentials, for all soil layers [kPa]
        layer_structure: The LayerStructure instance for the simulation.
        constants: Set of constants for the litter model

    Returns:
        A dictionary containing three environmental factors, one for the effect of
        temperature on above ground litter decay, one for the effect of temperature on
        below ground litter decay, and one for the effect of soil water potential on
        below ground litter decay.
    """

    temperatures = {
        "surface": air_temperatures[layer_structure.index_surface_scalar].to_numpy(),
        "below_ground": average_abiotic_environment_over_microbially_active_layers(
            environmental_variable=soil_temperatures,
            layer_structure=layer_structure,
        ),
    }
    water_potential = average_abiotic_environment_over_microbially_active_layers(
        environmental_variable=water_potentials, layer_structure=layer_structure
    )

    temperature_factors = {
        level: calculate_temperature_effect_on_litter_decomp(
            temperature=temp,
            reference_temp=constants.litter_decomp_reference_temp,
            offset_temp=constants.litter_decomp_offset_temp,
            temp_response=constants.litter_decomp_temp_response,
        )
        for (level, temp) in temperatures.items()
    }

    # Calculate the water factor (relevant for below ground layers)
    water_factor = calculate_water_potential_impact_on_microbes(
        water_potential=water_potential,
        water_potential_halt=constants.litter_decay_water_potential_halt,
        water_potential_opt=constants.litter_decay_water_potential_optimum,
        response_curvature=constants.moisture_response_curvature,
    )

    return {
        "temp_above": temperature_factors["surface"],
        "temp_below": temperature_factors["below_ground"],
        "water": water_factor,
    }


def calculate_temperature_effect_on_litter_decomp(
    temperature: NDArray[np.floating],
    reference_temp: float,
    offset_temp: float,
    temp_response: float,
) -> NDArray[np.floating]:
    """Calculate the effect that temperature has on litter decomposition rates.

    This function is taken from :cite:t:`kirschbaum_modelling_2002`.

    Args:
        temperature: The temperature of the litter layer [Celsius]
        reference_temp: The reference temperature for changes in litter decomposition
            rates with temperature [Celsius]
        offset_temp: Temperature offset [Celsius]
        temp_response: Factor controlling response strength to changing temperature
            [unitless]

    Returns:
        A multiplicative factor capturing the impact of temperature on litter
        decomposition [unitless]
    """

    return np.exp(
        temp_response * (temperature - reference_temp) / (temperature + offset_temp)
    )


def average_abiotic_environment_over_microbially_active_layers(
    environmental_variable: DataArray,
    layer_structure: LayerStructure,
) -> NDArray[np.floating]:
    """Average abiotic environmental variables over the microbially active layers.

    This function calculated an average across the microbially active depth (biotic
    topsoil) which is weighted by how much of the microbially active depth lies within
    each layer.

    Args:
        environmental_variable: The environmental variable to be averaged.
        layer_structure: The LayerStructure instance for the simulation.

    Returns:
        The average of the environmental variable of interest across the soil depth
        considered to be microbially active.
    """

    # Find weighting for each layer in the average by dividing the microbially active
    # depth in each layer by the total depth of microbial activity
    layer_weights = (
        layer_structure.soil_layer_active_thickness
        / layer_structure.microbial_simulation_depth
    )

    return np.dot(layer_weights, environmental_variable[layer_structure.index_all_soil])
