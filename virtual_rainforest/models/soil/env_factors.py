"""The ``models.soil.env_factors`` module contains functions that are used to
capture the impact that environmental factors have on microbial rates. These include
temperature, soil water potential, pH and soil texture.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from scipy.constants import convert_temperature, gas_constant

from virtual_rainforest.core.logger import LOGGER


def calculate_temperature_effect_on_microbes(
    soil_temperature: NDArray[np.float32],
    activation_energy: float,
    reference_temperature: float,
) -> NDArray[np.float32]:
    """Calculate the effect that temperature has on microbial metabolic rates.

    This uses a standard Arrhenius equation to calculate the impact of temperature.

    This function takes temperatures in Celsius as inputs and converts them into Kelvin
    for use in the Arrhenius equation. TODO - review this after we have decided how to
    handle these conversions in general.

    Args:
        soil_temperature: The temperature of the soil [C]
        activation_energy: Energy of activation [J mol^-1]
        soil_temperature: The reference temperature of the Arrhenius equation [C]

    Returns:
        A multiplicative factor capturing the effect of temperature on microbial rates
    """

    # Convert the temperatures to Kelvin
    soil_temp_in_kelvin = convert_temperature(
        soil_temperature, old_scale="Celsius", new_scale="Kelvin"
    )
    ref_temp_in_kelvin = convert_temperature(
        reference_temperature, old_scale="Celsius", new_scale="Kelvin"
    )

    return np.exp(
        (-activation_energy / gas_constant)
        * ((1 / (soil_temp_in_kelvin)) - (1 / (ref_temp_in_kelvin)))
    )


def calculate_water_potential_impact_on_microbes(
    water_potential: NDArray[np.float32],
    water_potential_halt: float,
    water_potential_opt: float,
    moisture_response_curvature: float,
) -> NDArray[np.float32]:
    """Calculate the effect that soil water potential has on microbial rates.

    This function only returns valid output for soil water potentials that are less than
    the optimal water potential.

    Args:
        water_potential: Soil water potential [kPa]
        water_potential_halt: Water potential at which all microbial activity stops
            [kPa]
        water_potential_opt: Optimal water potential for microbial activity [kPa]
        moisture_response_curvature: Parameter controlling the curvature of the moisture
            response function [unitless]

    Returns:
        A multiplicative factor capturing the impact of moisture on soil microbe rates
        decomposition [unitless]
    """

    # If the water potential is greater than the optimal then the function produces NaNs
    # so the simulation should be interrupted
    if any(water_potential > water_potential_opt):
        err = ValueError("Water potential greater than minimum value")
        LOGGER.critical(err)
        raise err

    # Calculate how much moisture suppresses microbial activity
    supression = (
        (np.log10(-water_potential) - np.log10(-water_potential_opt))
        / (np.log10(-water_potential_halt) - np.log10(-water_potential_opt))
    ) ** moisture_response_curvature

    return 1 - supression


def convert_moisture_to_scalar(
    soil_moisture: NDArray[np.float32],
    moisture_scalar_coefficient: float,
    moisture_scalar_exponent: float,
) -> NDArray[np.float32]:
    """Convert soil moisture into a factor to multiply rates by.

    This form is used in :cite:t:`abramoff_millennial_2018` to minimise differences with
    the CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
        soil_moisture: relative water content for each soil grid cell [unitless]
        moisture_scalar_coefficient: [unit less]
        moisture_scalar_exponent: [(Relative water content)^-1]

    Returns:
        A scalar that captures the impact of soil moisture on process rates
    """

    if np.any(soil_moisture > 1.0) or np.any(soil_moisture < 0.0):
        to_raise = ValueError(
            "Relative water content cannot go below zero or above one!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    # This expression is drawn from Abramoff et al. (2018)
    return 1 / (
        1
        + moisture_scalar_coefficient
        * np.exp(-moisture_scalar_exponent * soil_moisture)
    )
