"""The ``models.soil.carbon`` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment five pools are modelled, these are low molecular weight carbon
(LMWC), mineral associated organic matter (MAOM), microbial biomass, particulate organic
matter (POM), and POM degrading enzymes.
"""  # noqa: D205, D415

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.soil.constants import SoilConsts
from virtual_rainforest.models.soil.env_factors import (
    calculate_clay_impact_on_enzyme_saturation,
    calculate_clay_impact_on_necromass_decay,
    calculate_pH_suitability,
    calculate_temperature_effect_on_microbes,
    calculate_water_potential_impact_on_microbes,
    convert_moisture_to_scalar,
)


@dataclass
class MicrobialBiomassLoss:
    """A data class to store the various biomass losses from microbial biomass."""

    maintenance_synthesis: NDArray[np.float32]
    """Rate at which biomass must be synthesised to balance losses [kg C m^-3 day^-1].
    """
    pom_enzyme_production: NDArray[np.float32]
    """Rate at which POM degrading enzymes are produced [kg C m^-3 day^-1]."""
    maom_enzyme_production: NDArray[np.float32]
    """Rate at which MAOM degrading enzymes are produced [kg C m^-3 day^-1]."""
    necromass_decay_to_lmwc: NDArray[np.float32]
    """Rate at which biomass is lost to the LMWC pool [kg C m^-3 day^-1]."""
    necromass_decay_to_pom: NDArray[np.float32]
    """Rate at which biomass is lost to the POMM pool [kg C m^-3 day^-1]."""


def calculate_soil_carbon_updates(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    soil_c_pool_pom: NDArray[np.float32],
    soil_enzyme_pom: NDArray[np.float32],
    pH: NDArray[np.float32],
    bulk_density: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    soil_water_potential: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
    clay_fraction: NDArray[np.float32],
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
        soil_enzyme_pom: Amount of enzyme class which breaks down particulate organic
            matter [kg C m^-3]
        pH: pH values for each soil grid cell [unitless]
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        soil_moisture: relative water content for each soil grid cell [unitless]
        soil_water_potential: Soil water potential for each grid cell [kPa]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        percent_clay: Percentage clay for each soil grid cell
        clay_fraction: The clay fraction for each soil grid cell [unitless]
        mineralisation_rate: Amount of litter mineralised into POM pool [kg C m^-3
            day^-1]
        delta_pools_ordered: Dictionary to store pool changes in the order that pools
            are stored in the initial condition vector.
        constants: Set of constants for the soil model.

    Returns:
        A vector containing net changes to each pool. Order [lmwc, maom].
    """

    # TODO - At present we have two different factors that capture the impact of soil
    # water. water_factor is based on soil water potential and applies to the microbial
    # processes, whereas moist_scalar is based on soil water content and applies to the
    # chemical processes. In future, all processes will be microbially mediated, meaning
    # that moist_scalar can be removed.

    # Find the impact of soil water content on chemical soil processes
    moist_scalar = convert_moisture_to_scalar(
        soil_moisture,
        constants.moisture_scalar_coefficient,
        constants.moisture_scalar_exponent,
    )
    # Find the impact of soil water potential on the biochemical soil processes
    water_factor = calculate_water_potential_impact_on_microbes(
        water_potential=soil_water_potential,
        water_potential_halt=constants.soil_microbe_water_potential_halt,
        water_potential_opt=constants.soil_microbe_water_potential_optimum,
        moisture_response_curvature=constants.moisture_response_curvature,
    )
    # Find the impact of soil pH on microbial rates
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
    clay_factor_decay = calculate_clay_impact_on_necromass_decay(
        clay_fraction=clay_fraction,
        decay_exponent=constants.clay_necromass_decay_exponent,
    )
    # Calculate transfers between pools
    lmwc_to_maom = calculate_mineral_association(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        soil_c_pool_maom=soil_c_pool_maom,
        pH=pH,
        bulk_density=bulk_density,
        moisture_scalar=moist_scalar,
        percent_clay=percent_clay,
        constants=constants,
    )
    microbial_uptake, microbial_assimilation = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        soil_c_pool_microbe=soil_c_pool_microbe,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        constants=constants,
    )
    biomass_losses = determine_microbial_biomass_losses(
        soil_c_pool_microbe=soil_c_pool_microbe,
        soil_temp=soil_temp,
        clay_factor_decay=clay_factor_decay,
        constants=constants,
    )
    pom_enzyme_turnover = calculate_enzyme_turnover(
        enzyme_pool=soil_enzyme_pom, turnover_rate=constants.pom_enzyme_turnover_rate
    )
    labile_carbon_leaching = calculate_labile_carbon_leaching(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        moisture_scalar=moist_scalar,
        leaching_rate=constants.leaching_rate_labile_carbon,
    )
    pom_decomposition_rate = calculate_pom_decomposition(
        soil_c_pool_pom=soil_c_pool_pom,
        soil_enzyme_pom=soil_enzyme_pom,
        water_factor=water_factor,
        pH_factor=pH_factor,
        clay_factor_saturation=clay_factor_saturation,
        soil_temp=soil_temp,
        constants=constants,
    )

    pom_decomposition_to_lmwc = (
        pom_decomposition_rate * constants.pom_decomposition_fraction_lmwc
    )
    pom_decomposition_to_maom = pom_decomposition_rate * (
        1 - constants.pom_decomposition_fraction_lmwc
    )

    # Determine net changes to the pools
    delta_pools_ordered["soil_c_pool_lmwc"] = (
        pom_decomposition_to_lmwc
        + biomass_losses.necromass_decay_to_lmwc
        + pom_enzyme_turnover
        - lmwc_to_maom
        - microbial_uptake
        - labile_carbon_leaching
    )
    delta_pools_ordered["soil_c_pool_maom"] = pom_decomposition_to_maom + lmwc_to_maom
    delta_pools_ordered["soil_c_pool_microbe"] = (
        microbial_assimilation - biomass_losses.maintenance_synthesis
    )
    delta_pools_ordered["soil_c_pool_pom"] = (
        mineralisation_rate
        + biomass_losses.necromass_decay_to_pom
        - pom_decomposition_rate
    )
    delta_pools_ordered["soil_enzyme_pom"] = (
        biomass_losses.pom_enzyme_production - pom_enzyme_turnover
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


def determine_microbial_biomass_losses(
    soil_c_pool_microbe: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    clay_factor_decay: NDArray[np.float32],
    constants: SoilConsts,
) -> MicrobialBiomassLoss:
    """Calculate all of the losses from the microbial biomass pool.

    Microbes need to synthesis new biomass at a certain rate just to maintain their
    current biomass. This function calculates this overall rate and the various losses
    that contribute to this rate. The main sources of this loss are the external
    excretion of enzymes, cell death, and protein degradation.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        clay_factor_decay: A factor capturing the impact of soil clay fraction on
            necromass decay destination [unitless]
        constants: Set of constants for the soil model.

    Returns:
        A dataclass containing all the losses from the microbial biomass pool.
    """

    # Calculate the rate of maintenance synthesis
    maintenance_synthesis = calculate_maintenance_biomass_synthesis(
        soil_c_pool_microbe=soil_c_pool_microbe,
        soil_temp=soil_temp,
        constants=constants,
    )

    # Calculation the production of each enzyme class
    pom_enzyme_production = constants.maintenance_pom_enzyme * maintenance_synthesis
    maom_enzyme_production = constants.maintenance_maom_enzyme * maintenance_synthesis

    # Remaining maintenance synthesis is used to replace degraded proteins and cells
    replacement_synthesis = (
        1 - constants.maintenance_pom_enzyme - constants.maintenance_maom_enzyme
    ) * maintenance_synthesis

    # TODO - This split will change when a necromass pool is introduced
    # Calculate fraction of necromass that decays to LMWC
    necromass_proportion_to_lmwc = constants.necromass_to_lmwc * clay_factor_decay
    # These proteins and cells that are replaced decay into either the POM or LMWC pool
    necromass_to_lmwc = necromass_proportion_to_lmwc * replacement_synthesis
    necromass_to_pom = (1 - necromass_proportion_to_lmwc) * replacement_synthesis

    return MicrobialBiomassLoss(
        maintenance_synthesis=maintenance_synthesis,
        pom_enzyme_production=pom_enzyme_production,
        maom_enzyme_production=maom_enzyme_production,
        necromass_decay_to_lmwc=necromass_to_lmwc,
        necromass_decay_to_pom=necromass_to_pom,
    )


def calculate_maintenance_biomass_synthesis(
    soil_c_pool_microbe: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate microbial biomass synthesis rate required to offset losses.

    In order for a microbial population to not decline it must synthesise enough new
    biomass to offset losses. These losses mostly come from cell death and protein
    decay, but also include loses due to extracellular enzyme excretion.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.

    Returns:
        The rate of microbial biomass loss that must be matched to maintain a steady
        population [kg C m^-3 day^-1]
    """

    temp_factor = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_microbial_turnover,
        reference_temperature=constants.arrhenius_reference_temp,
    )

    return constants.microbial_turnover_rate * temp_factor * soil_c_pool_microbe


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


def calculate_enzyme_turnover(
    enzyme_pool: NDArray[np.float32], turnover_rate: float
) -> NDArray[np.float32]:
    """Calculate the turnover rate of a specific enzyme class.

    Args:
        enzyme_pool: The pool size for the enzyme class in question [kg C m^-3]
        turnover_rate: The rate at which enzymes in the pool turnover [day^-1]

    Returns:
        The rate at which enzymes are lost from the pool [kg C m^-3 day^-1]
    """

    return turnover_rate * enzyme_pool


def calculate_microbial_carbon_uptake(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    water_factor: NDArray[np.float32],
    pH_factor: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """Calculate uptake and assimilation of labile carbon by microbes.

    This function starts by calculating the impact that environmental factors have on
    the rate and saturation constants for microbial uptake. These constants are then
    used to calculate the rate of uptake of labile carbon. Carbon use efficiency is then
    calculated and used to find how much of this carbon ends up assimilated as biomass
    (rather than respired).

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.

    Returns:
        A tuple containing the uptake rate of low molecular weight carbon (LMWC) by the
        soil microbial biomass, and the rate at which this causes microbial biomass to
        increase.
    """

    # Calculate carbon use efficiency
    carbon_use_efficency = calculate_carbon_use_efficiency(
        soil_temp,
        constants.reference_cue,
        constants.cue_reference_temp,
        constants.cue_with_temperature,
    )
    # Calculate impact of temperature on the rate and saturation constants
    temp_factor_rate = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_microbial_uptake,
        reference_temperature=constants.arrhenius_reference_temp,
    )
    temp_factor_saturation = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_labile_C_saturation,
        reference_temperature=constants.arrhenius_reference_temp,
    )
    # Then use to calculate rate constant and saturation constant (which also change
    # with other environmental conditions)
    rate_constant = (
        constants.max_uptake_rate_labile_C * temp_factor_rate * water_factor * pH_factor
    )
    saturation_constant = constants.half_sat_labile_C_uptake * temp_factor_saturation

    # Calculate both the rate of carbon uptake, and the rate at which this carbon is
    # assimilated into microbial biomass.
    uptake_rate = rate_constant * np.divide(
        (soil_c_pool_lmwc * soil_c_pool_microbe),
        (soil_c_pool_lmwc + saturation_constant),
    )
    assimilation_rate = uptake_rate * carbon_use_efficency

    # TODO - the quantities calculated above can be used to calculate the carbon
    # respired instead of being uptaken. This isn't currently of interest, but will be
    # in future

    return uptake_rate, assimilation_rate


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


# TODO - Should consider making this a generic function, i.e. not POM specific
def calculate_pom_decomposition(
    soil_c_pool_pom: NDArray[np.float32],
    soil_enzyme_pom: NDArray[np.float32],
    water_factor: NDArray[np.float32],
    pH_factor: NDArray[np.float32],
    clay_factor_saturation: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate rate of particulate organic matter decomposition.

    This function calculates various environmental factors that effect enzyme activity,
    then uses these to find environmental adjusted rate and saturation constants. These
    are then used to find the POM decomposition rate.

    Args:
        soil_c_pool_pom: Particulate organic matter pool [kg C m^-3]
        soil_enzyme_pom: Amount of enzyme class which breaks down particulate organic
            matter [kg C m^-3]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        clay_factor_saturation: A factor capturing the impact of soil clay fraction on
            enzyme saturation constants [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.

    Returns:
        The amount of particulate organic matter (POM) decomposed into both labile
        carbon (LMWC) and mineral associated organic matter (MAOM) [kg C m^-3 day^-1]
    """

    # Calculate the factors which impact the rate and saturation constants
    temp_factor_rate = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_pom_decomp_rate,
        reference_temperature=constants.arrhenius_reference_temp,
    )
    temp_factor_saturation = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=constants.activation_energy_pom_decomp_saturation,
        reference_temperature=constants.arrhenius_reference_temp,
    )

    # Calculate the adjusted rate and saturation constants
    rate_constant = (
        constants.max_decomp_rate_pom * temp_factor_rate * water_factor * pH_factor
    )
    saturation_constant = (
        constants.half_sat_pom_decomposition
        * temp_factor_saturation
        * clay_factor_saturation
    )

    return (
        rate_constant
        * soil_enzyme_pom
        * soil_c_pool_pom
        / (saturation_constant + soil_c_pool_pom)
    )
