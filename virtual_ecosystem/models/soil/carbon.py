"""The ``models.soil.carbon`` module  simulates the soil carbon cycle for the Virtual
Ecosystem. At the moment five pools are modelled, these are low molecular weight carbon
(LMWC), mineral associated organic matter (MAOM), microbial biomass, particulate organic
matter (POM), and POM degrading enzymes.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.models.soil.constants import SoilConsts
from virtual_ecosystem.models.soil.env_factors import (
    calculate_environmental_effect_factors,
    calculate_leaching_rate,
    calculate_temperature_effect_on_microbes,
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
    necromass_formation: NDArray[np.float32]
    """Rate at which living biomass enters the necromass pool [kg C m^-3 day^-1]."""


# TODO - This function should probably be shortened, leaving as is for the moment as a
# sensible split will probably be more obvious once more is added to this function.
# TODO - Some level of cleanup is needed before I submit this PR, because it's actually
# hard to read at this point. I don't need to fix it completely, but need to do
# something to improve the readability
def calculate_soil_carbon_updates(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    soil_c_pool_pom: NDArray[np.float32],
    soil_c_pool_necromass: NDArray[np.float32],
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
        soil_c_pool_necromass: Microbial necromass pool [kg C m^-3]
        soil_enzyme_pom: Amount of enzyme class which breaks down particulate organic
            matter [kg C m^-3]
        soil_enzyme_maom: Amount of enzyme class which breaks down mineral associated
            organic matter [kg C m^-3]
        pH: pH values for each soil grid cell [unitless]
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        soil_moisture: amount of water contained by each soil layer [mm]
        soil_water_potential: Soil water potential for each grid cell [kPa]
        vertical_flow_rate: The vertical flow rate [TODO]
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

    # Find environmental factors which impact biogeochemical soil processes
    env_factors = calculate_environmental_effect_factors(
        soil_water_potential=soil_water_potential,
        pH=pH,
        clay_fraction=clay_fraction,
        constants=model_constants,
    )

    microbial_uptake, microbial_assimilation = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        soil_c_pool_microbe=soil_c_pool_microbe,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        soil_temp=soil_temp,
        constants=model_constants,
    )
    biomass_losses = determine_microbial_biomass_losses(
        soil_c_pool_microbe=soil_c_pool_microbe,
        soil_temp=soil_temp,
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
    )
    pom_decomposition_to_lmwc = calculate_enzyme_mediated_decomposition(
        soil_c_pool=soil_c_pool_pom,
        soil_enzyme=soil_enzyme_pom,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        clay_factor_saturation=env_factors.clay_saturation,
        soil_temp=soil_temp,
        reference_temp=model_constants.arrhenius_reference_temp,
        max_decomp_rate=model_constants.max_decomp_rate_pom,
        activation_energy_rate=model_constants.activation_energy_pom_decomp_rate,
        half_saturation=model_constants.half_sat_pom_decomposition,
        activation_energy_sat=model_constants.activation_energy_pom_decomp_saturation,
    )
    maom_decomposition_to_lmwc = calculate_enzyme_mediated_decomposition(
        soil_c_pool=soil_c_pool_maom,
        soil_enzyme=soil_enzyme_maom,
        water_factor=env_factors.water,
        pH_factor=env_factors.pH,
        clay_factor_saturation=env_factors.clay_saturation,
        soil_temp=soil_temp,
        reference_temp=model_constants.arrhenius_reference_temp,
        max_decomp_rate=model_constants.max_decomp_rate_maom,
        activation_energy_rate=model_constants.activation_energy_maom_decomp_rate,
        half_saturation=model_constants.half_sat_maom_decomposition,
        activation_energy_sat=model_constants.activation_energy_maom_decomp_saturation,
    )
    maom_desorption_to_lmwc = calculate_maom_desorption(
        soil_c_pool_maom=soil_c_pool_maom,
        desorption_rate_constant=model_constants.maom_desorption_rate,
    )
    # Calculate necromass decay to lmwc and sorption to maom
    necromass_decay_to_lmwc = calculate_necromass_breakdown(
        soil_c_pool_necromass=soil_c_pool_necromass,
        necromass_decay_rate=model_constants.necromass_decay_rate,
    )

    # Determine net changes to the pools
    delta_pools_ordered["soil_c_pool_lmwc"] = (
        pom_decomposition_to_lmwc
        + maom_decomposition_to_lmwc
        + maom_desorption_to_lmwc
        + necromass_decay_to_lmwc
        - microbial_uptake
        - labile_carbon_leaching
    )
    delta_pools_ordered["soil_c_pool_maom"] = (
        -maom_decomposition_to_lmwc - maom_desorption_to_lmwc
    )
    delta_pools_ordered["soil_c_pool_microbe"] = (
        microbial_assimilation - biomass_losses.maintenance_synthesis
    )
    delta_pools_ordered["soil_c_pool_pom"] = (
        mineralisation_rate - pom_decomposition_to_lmwc
    )
    delta_pools_ordered["soil_c_pool_necromass"] = (
        biomass_losses.necromass_formation
        + pom_enzyme_turnover
        + maom_enzyme_turnover
        - necromass_decay_to_lmwc
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
    # (i.e. forms necromass)
    necromass_formation = (
        1 - constants.maintenance_pom_enzyme - constants.maintenance_maom_enzyme
    ) * maintenance_synthesis

    return MicrobialBiomassLoss(
        maintenance_synthesis=maintenance_synthesis,
        pom_enzyme_production=pom_enzyme_production,
        maom_enzyme_production=maom_enzyme_production,
        necromass_formation=necromass_formation,
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
    reference_temp: float,
    max_decomp_rate: float,
    activation_energy_rate: float,
    half_saturation: float,
    activation_energy_sat: float,
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
        reference_temp: The reference temperature that enzyme rates were determined
            relative to [degrees C]
        max_decomp_rate: The maximum rate of substrate decomposition (at the reference
            temperature) [day^-1]
        activation_energy_rate: Activation energy for maximum decomposition rate
            [J K^-1]
        half_saturation: Half saturation constant for decomposition (at the reference
            temperature) [kg C m^-3]
        activation_energy_sat: Activation energy for decomposition saturation [J K^-1]

    Returns:
        The rate of decomposition of the organic matter pool in question [kg C m^-3
        day^-1]
    """

    # Calculate the factors which impact the rate and saturation constants
    temp_factor_rate = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=activation_energy_rate,
        reference_temperature=reference_temp,
    )
    temp_factor_saturation = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=activation_energy_sat,
        reference_temperature=reference_temp,
    )

    # Calculate the adjusted rate and saturation constants
    rate_constant = max_decomp_rate * temp_factor_rate * water_factor * pH_factor
    saturation_constant = (
        half_saturation * temp_factor_saturation * clay_factor_saturation
    )

    return (
        rate_constant * soil_enzyme * soil_c_pool / (saturation_constant + soil_c_pool)
    )


def calculate_maom_desorption(
    soil_c_pool_maom: NDArray[np.float32], desorption_rate_constant: float
):
    """Calculate the rate of mineral associated organic matter (MAOM) desorption.

    This function is independent of soil temperature, moisture, pH, clay fraction and
    bulk density. All of these things are known to effect real world desorption rates.
    However, to simplify the parameterisation we only include these effects on microbial
    rates. This may be something we want to alter in future.

    Args:
        soil_c_pool_maom: Size of the mineral associated organic matter pool [kg C m^-3]
        desorption_rate_constant: Rate constant for MAOM desorption [day^-1]

    Returns:
        The rate of MAOM desorption to LMWC [kg C m^-3 day^-1]
    """

    return desorption_rate_constant * soil_c_pool_maom


def calculate_sorption_to_maom(
    soil_c_pool: NDArray[np.float32], sorption_rate_constant: float
):
    """Calculate that a carbon pool sorbs to become mineral associated organic matter.

    Carbon from both the low molecular weight carbon pool and the necromass pool can
    sorb to minerals to form MAOM, so this function can be used for either pool.

    This function is independent of soil temperature, moisture, pH, clay fraction and
    bulk density. All of these things are known to effect real world desorption rates.
    However, to simplify the parameterisation we only include these effects on microbial
    rates. This may be something we want to alter in future.

    Args:
        soil_c_pool: Size of carbon pool [kg C m^-3]
        sorption_rate_constant: Rate constant for sorption to MAOM [day^-1]

    Returns:
        The rate of sorption to MAOM [kg C m^-3 day^-1]
    """

    return sorption_rate_constant * soil_c_pool


def calculate_necromass_breakdown(
    soil_c_pool_necromass: NDArray[np.float32], necromass_decay_rate: float
) -> NDArray[np.float32]:
    """Calculate breakdown rate of necromass into low molecular weight carbon (LMWC).

    This function calculate necromass breakdown to LMWC as a simple exponential decay.
    This decay is not effected by temperature or any other environmental factor. The
    idea is to keep this function as simple as possible, because it will be hard to
    parametrise even without additional complications. However, this is a simplification
    to bear in mind when planning future model improvements.

    Args:
        soil_c_pool_necromass: Size of the microbial necromass pool [kg C m^-3]
        necromass_decay_rate: Rate at which necromass decays into LMWC [day^-1]

    Returns:
        The amount of necromass that breakdown to LMWC [kg C m^-3 day^-1]
    """

    return necromass_decay_rate * soil_c_pool_necromass
