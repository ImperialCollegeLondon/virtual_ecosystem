"""The ``models.soil.carbon`` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment four pools are modelled, these are low molecular weight carbon
(LMWC), mineral associated organic matter (MAOM), microbial biomass, and particulate
organic matter (POM).
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.soil.constants import SoilConsts

# TODO - Once enzymes are added, temperature dependence of saturation constants should
# be added.


def calculate_soil_carbon_updates(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    soil_c_pool_pom: NDArray[np.float32],
    pH: NDArray[np.float32],
    bulk_density: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
    mineralisation_rate: NDArray[np.float32],
    delta_pools_ordered: dict[str, NDArray[np.float32]],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate net change for each carbon pool.

    This function calls lower level functions which calculate the transfers between
    pools. When all transfers have been calculated the net transfer is used to
    calculate the net change for each pool.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_c_pool_maom: Mineral associated organic matter pool [kg C m^-3]
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        soil_c_pool_pom: Particulate organic matter pool [kg C m^-3]
        pH: pH values for each soil grid cell
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        soil_moisture: relative water content for each soil grid cell [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        percent_clay: Percentage clay for each soil grid cell
        mineralisation_rate: Amount of litter mineralised into POM pool [kg C m^-3
            day^-1]
        delta_pools_ordered: Dictionary to store pool changes in the order that pools
            are stored in the initial condition vector.
        constants: Set of constants for the soil model.

    Returns:
        A vector containing net changes to each pool. Order [lmwc, maom].
    """

    # TODO - Work out if I can use my new water factor in place of moist_scalar
    # TODO - Get rid of these scalars, and then reparametrise the functions that call
    # them appropriately
    # Find scalar factors that multiple rates
    moist_scalar = convert_moisture_to_scalar(
        soil_moisture,
        constants.moisture_scalar_coefficient,
        constants.moisture_scalar_exponent,
    )
    # Calculate transfers between pools
    lmwc_to_maom = calculate_mineral_association(
        soil_c_pool_lmwc,
        soil_c_pool_maom,
        pH,
        bulk_density,
        moist_scalar,
        percent_clay,
        constants,
    )
    microbial_uptake = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc, soil_c_pool_microbe, moist_scalar, soil_temp, constants
    )
    microbial_respiration = calculate_maintenance_respiration(
        soil_c_pool_microbe=soil_c_pool_microbe,
        moisture_scalar=moist_scalar,
        soil_temp=soil_temp,
        constants=constants,
    )
    necromass_adsorption = calculate_necromass_adsorption(
        soil_c_pool_microbe=soil_c_pool_microbe,
        moisture_scalar=moist_scalar,
        necromass_adsorption_rate=constants.necromass_adsorption_rate,
    )
    labile_carbon_leaching = calculate_labile_carbon_leaching(
        soil_c_pool_lmwc, moist_scalar, constants.leaching_rate_labile_carbon
    )
    pom_decomposition_to_lmwc = calculate_pom_decomposition(
        soil_c_pool_pom, soil_c_pool_microbe, moist_scalar, constants
    )

    # Determine net changes to the pools
    delta_pools_ordered["soil_c_pool_lmwc"] = (
        pom_decomposition_to_lmwc
        - lmwc_to_maom
        - microbial_uptake
        - labile_carbon_leaching
    )
    delta_pools_ordered["soil_c_pool_maom"] = lmwc_to_maom + necromass_adsorption
    delta_pools_ordered["soil_c_pool_microbe"] = (
        microbial_uptake - microbial_respiration - necromass_adsorption
    )
    delta_pools_ordered["soil_c_pool_pom"] = (
        mineralisation_rate - pom_decomposition_to_lmwc
    )

    # Create output array of pools in desired order
    return np.concatenate(list(delta_pools_ordered.values()))


def calculate_mineral_association(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    pH: NDArray[np.float32],
    bulk_density: NDArray[np.float32],
    moisture_scalar: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculates net rate of LMWC association with soil minerals.

    Following :cite:t:`abramoff_millennial_2018`, mineral adsorption of carbon is
    controlled by a Langmuir saturation function. At present, binding affinity and
    Q_max are recalculated on every function called based on pH, bulk density and
    clay content. Once a decision has been reached as to how fast pH and bulk
    density will change (if at all), this calculation may need to be moved
    elsewhere.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_c_pool_maom: Mineral associated organic matter pool [kg C m^-3]
        pH: pH values for each soil grid cell
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        moisture_scalar: A scalar capturing the impact of soil moisture and on process
            rates [unitless]
        percent_clay: Percentage clay for each soil grid cell
        constants: Set of constants for the soil model.

    Returns:
        The net flux from LMWC to MAOM [kg C m^-3 day^-1]
    """

    # Calculate maximum sorption
    Q_max = calculate_max_sorption_capacity(
        bulk_density,
        percent_clay,
        constants.max_sorption_with_clay_slope,
        constants.max_sorption_with_clay_intercept,
    )
    equib_maom = calculate_equilibrium_maom(pH, Q_max, soil_c_pool_lmwc, constants)

    return moisture_scalar * soil_c_pool_lmwc * (equib_maom - soil_c_pool_maom) / Q_max


def calculate_max_sorption_capacity(
    bulk_density: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
    max_sorption_with_clay_slope: float,
    max_sorption_with_clay_intercept: float,
) -> NDArray[np.float32]:
    """Calculate maximum sorption capacity based on bulk density and clay content.

    The maximum sorption capacity is the maximum amount of mineral associated organic
    matter that can exist per unit volume. This expression and its parameters are also
    drawn from :cite:t:`mayes_relation_2012`. In that paper max sorption also depends on
    Fe content, but we are ignoring this for now.

    Args:
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        percent_clay: Percentage clay for each soil grid cell
        max_sorption_with_clay_slope: Slope of relationship between clay content and
            maximum organic matter sorption [(% clay)^-1]
        max_sorption_with_clay_intercept: Intercept of relationship between clay content
            and maximum organic matter sorption [log(kg C kg soil ^-1)]

    Returns:
        Maximum sorption capacity [kg C m^-3]
    """

    # Check that negative initial values are not given
    if np.any(percent_clay > 100.0) or np.any(percent_clay < 0.0):
        to_raise = ValueError(
            "Relative clay content must be expressed as a percentage!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    Q_max = bulk_density * 10 ** (
        max_sorption_with_clay_slope * np.log10(percent_clay)
        + max_sorption_with_clay_intercept
    )
    return Q_max


def calculate_equilibrium_maom(
    pH: NDArray[np.float32],
    Q_max: NDArray[np.float32],
    lmwc: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate equilibrium MAOM concentration based on Langmuir coefficients.

    Equilibrium concentration of mineral associated organic matter (MAOM) is calculated
    by this function under the assumption that the concentration of low molecular weight
    carbon (LMWC) is fixed.

    Args:
        pH: pH values for each soil grid cell
        Q_max: Maximum sorption capacities [kg C m^-3]
        lmwc: Low molecular weight carbon pool [kg C m^-3]
        constants: Set of constants for the soil model.

    Returns:
        Equilibrium concentration of MAOM [kg C m^-3]
    """

    binding_coefficient = calculate_binding_coefficient(
        pH, constants.binding_with_ph_slope, constants.binding_with_ph_intercept
    )
    return (binding_coefficient * Q_max * lmwc) / (1 + lmwc * binding_coefficient)


def calculate_binding_coefficient(
    pH: NDArray[np.float32],
    binding_with_ph_slope: float,
    binding_with_ph_intercept: float,
) -> NDArray[np.float32]:
    """Calculate Langmuir binding coefficient based on pH.

    This specific expression and its parameters are drawn from
    :cite:t:`mayes_relation_2012`.

    Args:
        pH: pH values for each soil grid cell
        binding_with_ph_slope: Slope of relationship between pH and binding coefficient
            [pH^-1]
        binding_with_ph_intercept: Intercept of relationship between pH and binding
            coefficient [log(m^3 kg^-1)]

    Returns:
        Langmuir binding coefficients for mineral association of labile carbon [m^3
        kg^-1]
    """

    return 10.0 ** (binding_with_ph_slope * pH + binding_with_ph_intercept)


def calculate_temperature_effect_on_microbes(
    soil_temperature: NDArray[np.float32],
    activation_energy: float,
    reference_temperature: float,
    gas_constant: float,
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
        gas_constant: The molar gas constant [J mol^-1 K^-1]

    Returns:
        A multiplicative factor capturing the effect of temperature on microbial rates
    """

    return np.exp(
        (-activation_energy / gas_constant)
        * ((1 / (soil_temperature + 273.15)) - (1 / (reference_temperature + 273.15)))
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

    # Calculate how much moisture suppresses microbial activity
    supression = (
        (np.log10(np.abs(water_potential)) - np.log10(abs(water_potential_opt)))
        / (np.log10(abs(water_potential_halt)) - np.log10(abs(water_potential_opt)))
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


def calculate_maintenance_respiration(
    soil_c_pool_microbe: NDArray[np.float32],
    moisture_scalar: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate the maintenance respiration of the microbial pool.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moisture_scalar: A scalar capturing the impact of soil moisture on process rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.

    Returns:
        Total maintenance respiration for all microbial biomass
    """

    temp_factor = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_microbial_turnover,
        reference_temperature=constants.arrhenius_reference_temp,
        gas_constant=constants.universal_gas_constant,
    )

    return (
        constants.microbial_turnover_rate
        * temp_factor
        * moisture_scalar
        * soil_c_pool_microbe
    )


def calculate_necromass_adsorption(
    soil_c_pool_microbe: NDArray[np.float32],
    moisture_scalar: NDArray[np.float32],
    necromass_adsorption_rate: float,
) -> NDArray[np.float32]:
    """Calculate adsorption of microbial necromass to soil minerals.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moisture_scalar: A scalar capturing the impact of soil moisture on process rates
            [unitless]
        necromass_adsorption_rate: Rate at which necromass is adsorbed by soil minerals
            [day^-1]

    Returns:
        Adsorption of microbial biomass to mineral associated organic matter (MAOM)
    """

    return necromass_adsorption_rate * moisture_scalar * soil_c_pool_microbe


def calculate_carbon_use_efficiency(
    soil_temp: NDArray[np.float32],
    reference_cue: float,
    cue_reference_temp: float,
    cue_with_temperature: float,
) -> NDArray[np.float32]:
    """Calculate the (temperature dependant) carbon use efficiency.

    TODO - This should be adapted to use an Arrhenius function at some point.

    Args:
        soil_temp: soil temperature for each soil grid cell [degrees C]
        reference_cue: Carbon use efficiency at reference temp [unitless]
        cue_reference_temp: Reference temperature [degrees C]
        cue_with_temperature: Rate of change in carbon use efficiency with increasing
            temperature [degree C^-1]

    Returns:
        The carbon use efficiency (CUE) of the microbial community
    """

    return reference_cue - cue_with_temperature * (soil_temp - cue_reference_temp)


def calculate_microbial_saturation(
    soil_c_pool_microbe: NDArray[np.float32],
    half_sat_microbial_activity: float,
) -> NDArray[np.float32]:
    """Calculate microbial activity saturation.

    This ensures that microbial activity (per unit biomass) drops as biomass density
    increases. This is adopted from Abramoff et al. It feels like an assumption that
    should be revised as the Virtual Rainforest develops.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        half_sat_microbial_activity: Half saturation constant for microbial activity

    Returns:
        A rescaling of microbial biomass that takes into account activity saturation
        with increasing biomass density
    """

    return soil_c_pool_microbe / (soil_c_pool_microbe + half_sat_microbial_activity)


def calculate_microbial_pom_mineralisation_saturation(
    soil_c_pool_microbe: NDArray[np.float32],
    half_sat_microbial_mineralisation: float,
) -> NDArray[np.float32]:
    """Calculate microbial POM mineralisation saturation (with increasing biomass).

    This ensures that microbial mineralisation of POM (per unit biomass) drops as
    biomass density increases. This is adopted from Abramoff et al. This function is
    very similar to the
    :func:`~virtual_rainforest.models.soil.carbon.calculate_microbial_saturation`
    function. They could in theory be reworked into a single function, but it doesn't
    seem worth the effort as we do not anticipate using biomass saturation functions
    beyond the first model draft.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        half_sat_microbial_mineralisation: Half saturation constant for microbial
            mineralisation of POM

    Returns:
        A rescaling of microbial biomass that takes into account POM mineralisation rate
        saturation with increasing biomass density
    """

    return soil_c_pool_microbe / (
        soil_c_pool_microbe + half_sat_microbial_mineralisation
    )


def calculate_pom_decomposition_saturation(
    soil_c_pool_pom: NDArray[np.float32],
    half_sat_pom_decomposition: float,
) -> NDArray[np.float32]:
    """Calculate particulate organic matter (POM) decomposition saturation.

    This ensures that decomposition of POM to low molecular weight carbon (LMWC)
    saturates with increasing POM. This effect arises from the saturation of enzymes
    with increasing substrate.

    Args:
        soil_c_pool_pom: Particulate organic matter (carbon) pool [kg C m^-3]
        half_sat_pom_decomposition: Half saturation constant for POM decomposition

    Returns:
        The saturation of the decomposition process
    """

    return soil_c_pool_pom / (soil_c_pool_pom + half_sat_pom_decomposition)


def calculate_microbial_carbon_uptake(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    moisture_scalar: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate amount of labile carbon taken up by microbes.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moisture_scalar: A scalar capturing the impact of soil moisture on process rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.

    Returns:
        Uptake of low molecular weight carbon (LMWC) by the soil microbial biomass.
    """

    # Calculate carbon use efficiency and microbial saturation
    carbon_use_efficency = calculate_carbon_use_efficiency(
        soil_temp,
        constants.reference_cue,
        constants.cue_reference_temp,
        constants.cue_with_temperature,
    )
    microbial_saturation = calculate_microbial_saturation(
        soil_c_pool_microbe, constants.half_sat_microbial_activity
    )
    temp_factor = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_microbial_uptake,
        reference_temperature=constants.arrhenius_reference_temp,
        gas_constant=constants.universal_gas_constant,
    )

    # TODO - the quantities calculated above can be used to calculate the carbon
    # respired instead of being uptaken. This isn't currently of interest, but will be
    # in future

    return (
        constants.max_uptake_rate_labile_C
        * moisture_scalar
        * temp_factor
        * soil_c_pool_lmwc
        * microbial_saturation
        * carbon_use_efficency
    )


def calculate_labile_carbon_leaching(
    soil_c_pool_lmwc: NDArray[np.float32],
    moisture_scalar: NDArray[np.float32],
    leaching_rate: float,
) -> NDArray[np.float32]:
    """Calculate rate at which labile carbon is leached.

    This is adopted from Abramoff et al. We definitely need to give more thought to how
    we model leaching.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        moisture_scalar: A scalar capturing the impact of soil moisture on process rates
            [unitless]
        leaching_rate: The rate at which labile carbon leaches from the soil [day^-1]

    Returns:
        The amount of labile carbon leached
    """

    return leaching_rate * moisture_scalar * soil_c_pool_lmwc


def calculate_pom_decomposition(
    soil_c_pool_pom: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    moisture_scalar: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate decomposition of particulate organic matter into labile carbon (LMWC).

    This is adopted from Abramoff et al. We definitely want to change this down the line
    to something that uses enzymes explicitly.

    Args:
        soil_c_pool_pom: Particulate organic matter pool [kg C m^-3]
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moisture_scalar: A scalar capturing the impact of soil moisture on process rates
            [unitless]
        constants: Set of constants for the soil model.

    Returns:
        The amount of particulate organic matter (POM) decomposed into labile carbon
            (LMWC)
    """

    # Calculate the two relevant saturations
    saturation_with_biomass = calculate_microbial_pom_mineralisation_saturation(
        soil_c_pool_microbe, constants.half_sat_microbial_pom_mineralisation
    )
    saturation_with_pom = calculate_pom_decomposition_saturation(
        soil_c_pool_pom, constants.half_sat_pom_decomposition
    )

    return (
        constants.max_decomp_rate_pom
        * saturation_with_pom
        * saturation_with_biomass
        * moisture_scalar
    )
