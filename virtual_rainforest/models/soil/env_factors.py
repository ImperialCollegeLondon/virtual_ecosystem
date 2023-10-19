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


def calculate_pH_suitability(
    soil_pH: NDArray[np.float32],
    maximum_pH: float,
    minimum_pH: float,
    upper_optimum_pH: float,
    lower_optimum_pH: float,
) -> NDArray[np.float32]:
    """Calculate the suitability of the soil pH for microbial activity.

    This function is taken from :cite:t:`orwin_organic_2011`. pH values within the
    optimal range are assumed to cause no microbial inhibition, and pH values above a
    certain value or below a certain value are assumed to cause total inhibition. Linear
    declines then occur between the edges of the optimal range and the zone of total
    inhibition.

    Args:
        soil_pH: The pH of the soil [unitless]
        maximum_pH: pH above which microbial rates are completely inhibited [unitless]
        minimum_pH: pH below which microbial rates are completely inhibited [unitless]
        upper_optimum_pH: pH above which suitability declines [unitless]
        lower_optimum_pH: pH below which suitability declines [unitless]

    Returns:
        A multiplicative factor capturing the effect of pH on microbial rates
    """

    # TODO - This check is necessary to prevent nonsensical output being generated,
    # however it could be done when constants are loaded, rather than for every function
    # call
    if (
        maximum_pH <= upper_optimum_pH
        or upper_optimum_pH <= lower_optimum_pH
        or lower_optimum_pH <= minimum_pH
    ):
        to_raise = ValueError("At least one pH threshold has an invalid value!")
        LOGGER.error(to_raise)
        raise to_raise

    pH_factors = np.full(len(soil_pH), np.nan)

    # zero below minimum or above maximum pH
    pH_factors[soil_pH < minimum_pH] = 0
    pH_factors[soil_pH > maximum_pH] = 0
    # and one between the two thresholds
    pH_factors[(lower_optimum_pH <= soil_pH) & (soil_pH <= upper_optimum_pH)] = 1

    # Find points that lie between optimal region and maximum/minimum
    between_opt_and_min = (minimum_pH <= soil_pH) & (soil_pH < lower_optimum_pH)
    between_opt_and_max = (upper_optimum_pH < soil_pH) & (soil_pH <= maximum_pH)

    # Linear increase from minimum pH value to lower threshold
    pH_factors[between_opt_and_min] = (soil_pH[between_opt_and_min] - minimum_pH) / (
        lower_optimum_pH - minimum_pH
    )
    # Linear decrease from the upper threshold to maximum pH
    pH_factors[between_opt_and_max] = (
        soil_pH[between_opt_and_max] - upper_optimum_pH
    ) / (maximum_pH - upper_optimum_pH)

    return pH_factors


def calculate_clay_impact_on_enzyme_saturation(
    clay_fraction: NDArray[np.float32],
    base_protection: float,
    protection_with_clay: float,
) -> NDArray[np.float32]:
    """Calculate the impact that the soil clay fraction has on enzyme saturation.

    This factor impacts enzyme saturation constants, based on the assumption that finely
    textured soils will restrict enzyme access to available C substrates (which protects
    them). Its form is taken from :cite:t:`fatichi_mechanistic_2019`.

    Args:
        clay_fraction: The fraction of the soil which is clay [unitless]
        base_protection: The protection that a soil with no clay provides [unitless]
        protection_with_clay: The rate at which protection increases with increasing
           clay [unitless]

    Returns:
        A multiplicative factor capturing how much the protection due to soil structure
        changes the effective saturation constant by [unitless]
    """

    return base_protection + protection_with_clay * clay_fraction


def calculate_clay_impact_on_necromass_decay(
    clay_fraction: NDArray[np.float32], decay_exponent: float
) -> NDArray[np.float32]:
    """Calculate the impact that soil clay has on necromass decay to LMWC.

    Necromass which doesn't breakdown fully gets added to the POM pool instead.

    Args:
        clay_fraction: The fraction of the soil which is clay [unitless]
        sorption_exponent: Controls the impact that differences in soil clay content
            have on the proportion of necromass that decays to LMWC [unitless]

    Returns:
        A multiplicative factor capturing the impact that soil clay has on the
        proportion of necromass decay which sorbs to form POM [unitless]
    """

    return np.exp(decay_exponent * clay_fraction)


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
