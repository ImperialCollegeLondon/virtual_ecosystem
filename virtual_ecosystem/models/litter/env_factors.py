"""The ``models.litter.env_factors`` module contains functions that are used to
capture the impact that environmental factors have on litter decay rates. These include
temperature and soil water potential.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure


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


def average_over_microbially_active_layers(
    environmental_variable: DataArray, layer_structure: LayerStructure
) -> NDArray[np.float32]:
    """Average an environmental variable over the microbially active layers.

    This average is weighted by how much of the microbially active depth lies within
    each layer.

    Args:
        environmental_variable: The environmental variable to be averaged
        layer_structure: The LayerStructure instance for the simulation.

    Returns:
        The average of the environmental variable across the soil depth considered to be
        microbially active.
    """

    # Find weighting for each layer in the average by dividing the microbially active
    # depth in each layer by the total depth of microbial activity
    layer_weights = (
        layer_structure.soil_layer_active_thickness
        / layer_structure.max_depth_of_microbial_activity
    )

    return np.dot(
        layer_weights,
        environmental_variable[layer_structure.index_all_soil].to_numpy(),
    )
