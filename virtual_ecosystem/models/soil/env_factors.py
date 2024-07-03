"""The ``models.soil.env_factors`` module contains functions that are used to
capture the impact that environmental factors have on microbial rates. These include
temperature, soil water potential, pH and soil texture.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.constants import convert_temperature, gas_constant

from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.soil.constants import SoilConsts


@dataclass
class EnvironmentalEffectFactors:
    """The various factors through which the environment effects soil cycling rates."""

    water: NDArray[np.float32]
    """Impact of soil water potential on enzymatic rates [unitless]."""
    pH: NDArray[np.float32]
    """Impact of soil pH on enzymatic rates [unitless]."""
    clay_saturation: NDArray[np.float32]
    """Impact of soil clay fraction on enzyme saturation constants [unitless]."""


def calculate_environmental_effect_factors(
    soil_water_potential: NDArray[np.float32],
    pH: NDArray[np.float32],
    clay_fraction: NDArray[np.float32],
    constants: SoilConsts,
) -> EnvironmentalEffectFactors:
    """Calculate the effects that the environment has on relevant biogeochemical rates.

    For each environmental effect a multiplicative factor is calculated, and all of them
    are returned in a single object for use elsewhere in the soil model.

    Args:
        soil_water_potential: Soil water potential for each grid cell [kPa]
        pH: pH values for each soil grid cell [unitless]
        clay_fraction: The clay fraction for each soil grid cell [unitless]
        constants: Set of constants for the soil model

    Returns:
        An object containing four environmental factors, one for the effect of water
        potential on enzyme rates, one for the effect of pH on enzyme rates, one for the
        effect of clay fraction on enzyme saturation, and one for the effect of clay on
        necromass decay destination.
    """

    # Calculate the impact that each environment variable has on the relevant
    # biogeochemical soil processes
    water_factor = calculate_water_potential_impact_on_microbes(
        water_potential=soil_water_potential,
        water_potential_halt=constants.soil_microbe_water_potential_halt,
        water_potential_opt=constants.soil_microbe_water_potential_optimum,
        response_curvature=constants.microbial_water_response_curvature,
    )
    pH_factor = calculate_pH_suitability(
        soil_pH=pH,
        maximum_pH=constants.max_pH_microbes,
        minimum_pH=constants.min_pH_microbes,
        lower_optimum_pH=constants.lowest_optimal_pH_microbes,
        upper_optimum_pH=constants.highest_optimal_pH_microbes,
    )
    clay_factor_saturation = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=clay_fraction,
        base_protection=constants.base_soil_protection,
        protection_with_clay=constants.soil_protection_with_clay,
    )

    # Combine all factors into a single EnvironmentalFactors object
    return EnvironmentalEffectFactors(
        water=water_factor,
        pH=pH_factor,
        clay_saturation=clay_factor_saturation,
    )


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
        reference_temperature: The reference temperature of the Arrhenius equation [C]

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
    response_curvature: float,
) -> NDArray[np.float32]:
    """Calculate the effect that soil water potential has on microbial rates.

    This function only returns valid output for soil water potentials that are less than
    the optimal water potential.

    Args:
        water_potential: Soil water potential [kPa]
        water_potential_halt: Water potential at which all microbial activity stops
            [kPa]
        water_potential_opt: Optimal water potential for microbial activity [kPa]
        response_curvature: Parameter controlling the curvature of function that
            captures the response of microbial rates to water potential [unitless]

    Returns:
        A multiplicative factor capturing the impact of moisture on soil microbe rates
        decomposition [unitless]
    """

    # If the water potential is greater than the optimal then the function produces NaNs
    # so the simulation should be interrupted
    if np.any(water_potential > water_potential_opt):
        err = ValueError("Water potential greater than minimum value")
        LOGGER.critical(err)
        raise err

    # Calculate how much moisture suppresses microbial activity
    supression = (
        (np.log10(-water_potential) - np.log10(-water_potential_opt))
        / (np.log10(-water_potential_halt) - np.log10(-water_potential_opt))
    ) ** response_curvature

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


def calculate_leaching_rate(
    solute_density: NDArray[np.float32],
    vertical_flow_rate: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    solubility_coefficient: float,
) -> NDArray[np.float32]:
    """Calculate leaching rate for a given solute based on flow rate.

    This functional form is adapted from :cite:t:`porporato_hydrologic_2003`. The amount
    of solute that is expected to be found in dissolved form is calculated by
    multiplying the solute density by its solubility coefficient. This is then
    multiplied by the frequency with which the water column is completely replaced, i.e.
    the ratio of vertical flow rate to soil moisture in mm.

    Args:
        solute_density: The density of the solute in the soil [kg solute m^-3]
        vertical_flow_rate: Rate of flow downwards through the soil [mm day^-1]
        soil_moisture: Volume of water contained in topsoil layer [mm]
        solubility_coefficient: The solubility coefficient of the solute in question
            [unitless]

    Returns:
        The rate at which the solute in question is leached [kg solute m^-3 day^-1]
    """

    return solubility_coefficient * solute_density * vertical_flow_rate / soil_moisture
