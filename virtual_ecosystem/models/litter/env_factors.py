"""The ``models.litter.env_factors`` module contains functions that are used to
capture the impact that environmental factors have on litter decay rates. These include
temperature and soil water potential.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.models.litter.constants import LitterConsts


def calculate_environmental_factors(
    air_temperatures: DataArray,
    soil_temperatures: DataArray,
    water_potentials: DataArray,
    layer_structure: LayerStructure,
    constants: LitterConsts,
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
        air_temperatures: Air temperatures, for all above ground layers [C]
        soil_temperatures: Soil temperatures, for all soil layers [C]
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
        # TODO - This currently takes uses the surface temperature for the first layer.
        # Once we start change the default to use a thin topsoil layer that should be
        # used here instead
        "below_ground": average_temperature_over_microbially_active_layers(
            soil_temperatures=soil_temperatures,
            surface_temperature=air_temperatures[
                layer_structure.index_surface_scalar
            ].to_numpy(),
            layer_structure=layer_structure,
        ),
    }
    water_potential = average_water_potential_over_microbially_active_layers(
        water_potentials=water_potentials, layer_structure=layer_structure
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
    water_factor = calculate_soil_water_effect_on_litter_decomp(
        water_potential=water_potential,
        water_potential_halt=constants.litter_decay_water_potential_halt,
        water_potential_opt=constants.litter_decay_water_potential_optimum,
        moisture_response_curvature=constants.moisture_response_curvature,
    )

    return {
        "temp_above": temperature_factors["surface"],
        "temp_below": temperature_factors["below_ground"],
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


def calculate_soil_water_effect_on_litter_decomp(
    water_potential: NDArray[np.float32],
    water_potential_halt: float,
    water_potential_opt: float,
    moisture_response_curvature: float,
) -> NDArray[np.float32]:
    """Calculate the effect that soil water potential has on litter decomposition rates.

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

    # TODO - Need to make sure that this function is properly defined for a plausible
    # range of matric potentials.

    # Calculate how much moisture suppresses microbial activity
    supression = (
        (np.log10(-water_potential) - np.log10(-water_potential_opt))
        / (np.log10(-water_potential_halt) - np.log10(-water_potential_opt))
    ) ** moisture_response_curvature

    return 1 - supression


def average_temperature_over_microbially_active_layers(
    soil_temperatures: DataArray,
    surface_temperature: NDArray[np.float32],
    layer_structure: LayerStructure,
) -> NDArray[np.float32]:
    """Average soil temperatures over the microbially active layers.

    First the average temperature is found for each layer. Then an average across the
    microbially active depth is taken, weighting by how much of the microbially active
    depth lies within each layer.

    Args:
        soil_temperatures: Soil temperatures to be averaged [C]
        surface_temperature: Air temperature just above the soil surface [C]
        layer_structure: The LayerStructure instance for the simulation.

    Returns:
        The average temperature across the soil depth considered to be microbially
        active [C]
    """

    # Find weighting for each layer in the average by dividing the microbially active
    # depth in each layer by the total depth of microbial activity
    layer_weights = (
        layer_structure.soil_layer_active_thickness
        / layer_structure.max_depth_of_microbial_activity
    )

    # Find the average for each layer
    layer_averages = np.empty((layer_weights.shape[0], soil_temperatures.shape[1]))
    layer_averages[0, :] = (
        surface_temperature + soil_temperatures[layer_structure.index_topsoil]
    ) / 2.0

    for index in range(1, len(layer_structure.soil_layer_active_thickness)):
        layer_averages[index, :] = (
            soil_temperatures[layer_structure.index_topsoil_scalar + index - 1]
            + soil_temperatures[layer_structure.index_topsoil_scalar + index]
        ) / 2.0

    return np.dot(layer_weights, layer_averages)


def average_water_potential_over_microbially_active_layers(
    water_potentials: DataArray,
    layer_structure: LayerStructure,
) -> NDArray[np.float32]:
    """Average water potentials over the microbially active layers.

    The average water potential is found for each layer apart from the top layer. This
    is because for the top layer a sensible average can't be taken as water potential is
    not defined for the surface layer. In this case, the water potential at the maximum
    layer height is just treated as the average of the layer. This is a reasonable
    assumption if the first soil layer is shallow.

    These water potentials are then averaged across the microbially active depth,
    weighting by how much of the microbially active depth lies within each layer.

    Args:
        water_potentials: Soil water potentials to be averaged [kPa]
        layer_structure: The LayerStructure instance for the simulation.

    Returns:
        The average water potential across the soil depth considered to be microbially
        active [kPa]
    """

    # Find weighting for each layer in the average by dividing the microbially active
    # depth in each layer by the total depth of microbial activity
    layer_weights = (
        layer_structure.soil_layer_active_thickness
        / layer_structure.max_depth_of_microbial_activity
    )

    # Find the average for each layer
    layer_averages = np.empty((layer_weights.shape[0], water_potentials.shape[1]))
    # Top layer cannot be averaged
    layer_averages[0, :] = water_potentials[layer_structure.index_topsoil]

    for index in range(1, len(layer_structure.soil_layer_active_thickness)):
        layer_averages[index, :] = (
            water_potentials[layer_structure.index_topsoil_scalar + index - 1]
            + water_potentials[layer_structure.index_topsoil_scalar + index]
        ) / 2.0

    return np.dot(layer_weights, layer_averages)
