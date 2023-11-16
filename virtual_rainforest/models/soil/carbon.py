"""The ``models.soil.carbon`` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment five pools are modelled, these are low molecular weight carbon
(LMWC), mineral associated organic matter (MAOM), microbial biomass, particulate organic
matter (POM), and POM degrading enzymes.
"""  # noqa: D205, D415

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.models.soil.constants import SoilConsts
from virtual_rainforest.models.soil.env_factors import (
    calculate_clay_impact_on_enzyme_saturation,
    calculate_clay_impact_on_necromass_decay,
    calculate_leaching_rate,
    calculate_pH_suitability,
    calculate_temperature_effect_on_microbes,
    calculate_water_potential_impact_on_microbes,
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
    """Rate at which biomass is lost to the POM pool [kg C m^-3 day^-1]."""


# TODO - This function should probably be shortened
def calculate_soil_carbon_updates(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    soil_c_pool_pom: NDArray[np.float32],
    soil_enzyme_pom: NDArray[np.float32],
    soil_enzyme_maom: NDArray[np.float32],
    pH: NDArray[np.float32],
    bulk_density: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    soil_water_potential: NDArray[np.float32],
    vertical_flow_rate: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    clay_fraction: NDArray[np.float32],
    mineralisation_rate: NDArray[np.float32],
    delta_pools_ordered: dict[str, NDArray[np.float32]],
    core_constants: CoreConsts,
    model_constants: SoilConsts,
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
        soil_enzyme_maom: Amount of enzyme class which breaks down mineral associated
            organic matter [kg C m^-3]
        pH: pH values for each soil grid cell [unitless]
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        soil_moisture: relative water content for each soil grid cell [unitless]
        soil_water_potential: Soil water potential for each grid cell [kPa]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        clay_fraction: The clay fraction for each soil grid cell [unitless]
        mineralisation_rate: Amount of litter mineralised into POM pool [kg C m^-3
            day^-1]
        delta_pools_ordered: Dictionary to store pool changes in the order that pools
            are stored in the initial condition vector.
        core_constants: Set of constants shared between models.
        model_constants: Set of constants for the soil model.

    Returns:
        A vector containing net changes to each pool. Order [lmwc, maom].
    """

    # Find the impact of soil water potential on the biochemical soil processes
    water_factor = calculate_water_potential_impact_on_microbes(
        water_potential=soil_water_potential,
        water_potential_halt=model_constants.soil_microbe_water_potential_halt,
        water_potential_opt=model_constants.soil_microbe_water_potential_optimum,
        moisture_response_curvature=model_constants.moisture_response_curvature,
    )
    # Find the impact of soil pH on microbial rates
    pH_factor = calculate_pH_suitability(
        soil_pH=pH,
        maximum_pH=model_constants.max_pH_microbes,
        minimum_pH=model_constants.min_pH_microbes,
        lower_optimum_pH=model_constants.lowest_optimal_pH_microbes,
        upper_optimum_pH=model_constants.highest_optimal_pH_microbes,
    )
    clay_factor_saturation = calculate_clay_impact_on_enzyme_saturation(
        clay_fraction=clay_fraction,
        base_protection=model_constants.base_soil_protection,
        protection_with_clay=model_constants.soil_protection_with_clay,
    )
    clay_factor_decay = calculate_clay_impact_on_necromass_decay(
        clay_fraction=clay_fraction,
        decay_exponent=model_constants.clay_necromass_decay_exponent,
    )
    microbial_uptake, microbial_assimilation = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        soil_c_pool_microbe=soil_c_pool_microbe,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        constants=model_constants,
    )
    biomass_losses = determine_microbial_biomass_losses(
        soil_c_pool_microbe=soil_c_pool_microbe,
        soil_temp=soil_temp,
        clay_factor_decay=clay_factor_decay,
        constants=model_constants,
    )
    pom_enzyme_turnover = calculate_enzyme_turnover(
        enzyme_pool=soil_enzyme_pom,
        turnover_rate=model_constants.pom_enzyme_turnover_rate,
    )
    maom_enzyme_turnover = calculate_enzyme_turnover(
        enzyme_pool=soil_enzyme_maom,
        turnover_rate=model_constants.maom_enzyme_turnover_rate,
    )
    labile_carbon_leaching = calculate_leaching_rate(
        solute_density=soil_c_pool_lmwc,
        vertical_flow_rate=vertical_flow_rate,
        soil_moisture=soil_moisture,
        solubility_coefficient=model_constants.solubility_coefficient_lmwc,
        soil_layer_thickness=core_constants.depth_of_active_soil_layer,
    )
    pom_decomposition_rate = calculate_enzyme_mediated_decomposition(
        soil_c_pool=soil_c_pool_pom,
        soil_enzyme=soil_enzyme_pom,
        water_factor=water_factor,
        pH_factor=pH_factor,
        clay_factor_saturation=clay_factor_saturation,
        soil_temp=soil_temp,
        constants=model_constants,
    )

    pom_decomposition_to_lmwc = (
        pom_decomposition_rate * model_constants.pom_decomposition_fraction_lmwc
    )
    pom_decomposition_to_maom = pom_decomposition_rate * (
        1 - model_constants.pom_decomposition_fraction_lmwc
    )
    # TODO - Use enzyme decomp equation to calculate lmwc to maom transfer

    # Determine net changes to the pools
    delta_pools_ordered["soil_c_pool_lmwc"] = (
        pom_decomposition_to_lmwc
        + biomass_losses.necromass_decay_to_lmwc
        + pom_enzyme_turnover
        - microbial_uptake
        - labile_carbon_leaching
    )
    delta_pools_ordered["soil_c_pool_maom"] = pom_decomposition_to_maom
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
    delta_pools_ordered["soil_enzyme_maom"] = (
        biomass_losses.maom_enzyme_production - maom_enzyme_turnover
    )

    # Create output array of pools in desired order
    return np.concatenate(list(delta_pools_ordered.values()))


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


def calculate_enzyme_mediated_decomposition(
    soil_c_pool: NDArray[np.float32],
    soil_enzyme: NDArray[np.float32],
    water_factor: NDArray[np.float32],
    pH_factor: NDArray[np.float32],
    clay_factor_saturation: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    constants: SoilConsts,
) -> NDArray[np.float32]:
    """Calculate rate of a enzyme mediated decomposition process.

    This function calculates various environmental factors that effect enzyme activity,
    then uses these to find environmental adjusted rate and saturation constants. These
    are then used to find the decomposition rate of the pool in question.

    Args:
        soil_c_pool: Size of organic matter pool [kg C m^-3]
        soil_enzyme: Amount of enzyme class which breaks down the organic matter pool in
            question [kg C m^-3]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        clay_factor_saturation: A factor capturing the impact of soil clay fraction on
            enzyme saturation constants [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.

    Returns:
        The rate of decomposition of the organic matter pool in question [kg C m^-3
        day^-1]
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
        rate_constant * soil_enzyme * soil_c_pool / (saturation_constant + soil_c_pool)
    )
