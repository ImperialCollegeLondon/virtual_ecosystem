"""The ``models.soil.env_factors`` module contains functions that are used to
capture the impact that environmental factors have on microbial rates. These include
temperature, soil water potential, pH and soil texture.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.constants import convert_temperature, gas_constant
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
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
    pH_factors[between_opt_and_max] = (maximum_pH - soil_pH[between_opt_and_max]) / (
        maximum_pH - upper_optimum_pH
    )

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


def calculate_nitrification_temperature_factor(
    soil_temp: NDArray[np.float32],
    optimum_temp: float,
    max_temp: float,
    thermal_sensitivity: int,
) -> NDArray[np.float32]:
    """Calculate factor that captures the effect of temperature on nitrification rate.

    Form of this function is taken from :cite:t:`xu-ri_terrestrial_2008`.

    Args:
        soil_temp: Temperature of the relevant segment of soil [C]
        optimum_temp: Temperature at which nitrification is maximised [K]
        max_temp: Maximum temperature for which this expression still gives a meaningful
            result [K]
        thermal_sensitivity: Sensitivity of the factor to changes in temperature
            [unitless]

    Returns:
        A factor capturing the impact of soil temperature on the nitrification rate
        [unitless].
    """

    # TODO - This will be removed once temperatures start being supplied in Kelvin
    # Convert the temperatures to Kelvin
    soil_temp_in_kelvin = convert_temperature(
        soil_temp, old_scale="Celsius", new_scale="Kelvin"
    )

    return (
        ((max_temp - soil_temp_in_kelvin) / (max_temp - optimum_temp))
        ** thermal_sensitivity
    ) * np.exp(
        thermal_sensitivity
        * ((soil_temp_in_kelvin - optimum_temp) / (max_temp - optimum_temp))
    )


def calculate_nitrification_moisture_factor(effective_saturation: NDArray[np.float32]):
    """Calculate factor that captures the effect of soil moisture on nitrification rate.

    Form of this function is taken from :cite:t:`fatichi_mechanistic_2019`, where it is
    provided with basically no justification.

    Args:
        effective_saturation: Effective saturation of the soil with water [unitless]

    Returns:
        A factor capturing the impact of soil moisture on the nitrification rate
        [unitless].
    """

    return effective_saturation * (1 - effective_saturation) / 0.25


def calculate_denitrification_temperature_factor(
    soil_temp: NDArray[np.float32],
    factor_at_infinity: float,
    minimum_temp: float,
    thermal_sensitivity: float,
):
    """Calculate factor that captures the effect of temperature on denitrification rate.

    Form of this function is a slight rearranged of one provided in
    :cite:t:`xu-ri_terrestrial_2008`.

    Args:
        soil_temp: Temperature of the relevant segment of soil [C]
        factor_at_infinity: Value of temperature factor at infinite temperature
            [unitless]
        minimum_temp: Minimum temperature at which denitrification can still happen [K]
        thermal_sensitivity: Sensitivity of the factor to changes in temperature [K]

    Returns:
        A factor capturing the impact of soil temperature on the denitrification rate
        [unitless].
    """

    # TODO - This will be removed once temperatures start being supplied in Kelvin
    # Convert the temperatures to Kelvin
    soil_temp_in_kelvin = convert_temperature(
        soil_temp, old_scale="Celsius", new_scale="Kelvin"
    )

    return np.where(
        soil_temp_in_kelvin <= minimum_temp,
        0,
        factor_at_infinity
        * np.exp(-thermal_sensitivity / (soil_temp_in_kelvin - minimum_temp)),
    )


def calculate_symbiotic_nitrogen_fixation_carbon_cost(
    soil_temp: NDArray[np.float32],
    cost_at_zero_celsius: float,
    infinite_temp_cost_offset: float,
    thermal_sensitivity: float,
    cost_equality_temp: float,
):
    """Calculate the cost of symbiotic nitrogen fixation in carbon terms.

    The function used here is adapted from an empirical function provided in
    :cite:t:`brzostek_modeling_2014`. As the function is not defined below zero degrees
    celsius if a negative temperature is input an infinite cost is returned.

    I could not sensibly convert this empirically derived function from Celsius to
    Kelvin units so this is the only function in the soil model to use Celsius units.

    Args:
        soil_temp: Temperature of the relevant soil zone [C]
        cost_at_zero_celsius: The cost nitrogen fixation at zero Celsius [kg C kg N^-1]
        infinite_temp_cost_offset: The difference between the nitrogen fixation cost at
            zero Celsius and the cost that it tends towards at very high temperatures
            [kg C kg N^-1]
        thermal_sensitivity: Sensitivity of nitrogen fixation cost to changes in
            temperature [C^-1]
        cost_equality_temp: Temperature (positive) at which the nitrogen fixation cost
            is the same as it is at zero Celsius [C]

    Returns:
        The carbon cost that plants have to pay their microbial symbionts to fix per
        unit of nitrogen fixed [kg C kg N^-1]
    """

    return np.where(
        soil_temp < 0.0,
        np.inf,
        cost_at_zero_celsius
        + infinite_temp_cost_offset
        * (
            np.exp(
                thermal_sensitivity * soil_temp * (1 - (soil_temp / cost_equality_temp))
            )
            - 1
        ),
    )


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


def find_total_soil_moisture_for_microbially_active_depth(
    soil_moistures: DataArray,
    layer_structure: LayerStructure,
) -> NDArray[np.float32]:
    """Find total soil moisture for the microbially active depth.

    The proportion of each soil layer that lies within the microbially active zone is
    first found. The soil moisture for each layer is then multiplied by this proportion
    and summed, to find the total soil moisture in the microbially active zone.

    Args:
        soil_moistures: Soil moistures across all soil layers [mm]
        layer_structure: The LayerStructure instance for the simulation. From this we
           use the thickness of each layer, as well as `soil_layer_active_thickness`
           which is how much of each layer lies within the microbially active zone

    Returns:
        The total soil moisture in the microbially active depth [mm]
    """

    # Find the fraction of each layer that lies within the microbially active zone
    layer_weights = (
        layer_structure.soil_layer_active_thickness
        / layer_structure.soil_layer_thickness
    )

    return np.dot(layer_weights, soil_moistures[layer_structure.index_all_soil])
