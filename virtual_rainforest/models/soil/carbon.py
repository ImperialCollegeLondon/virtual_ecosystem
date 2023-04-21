"""The ``models.soil.carbon`` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment only two pools are modelled, these are low molecular weight
carbon (LMWC) and mineral associated organic matter (MAOM). More pools and their
interactions will be added at a later date.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.soil.constants import (
    CARBON_INPUT_TO_POM,
    HALF_SAT_MICROBIAL_ACTIVITY,
    LEACHING_RATE_LABILE_CARBON,
    LITTER_INPUT_RATE,
    MAX_UPTAKE_RATE_LABILE_C,
    MICROBIAL_TURNOVER_RATE,
    NECROMASS_ADSORPTION_RATE,
    BindingWithPH,
    CarbonUseEfficiency,
    MaxSorptionWithClay,
    MoistureScalar,
    TempScalar,
)

# TODO - I'm basically certain that the paper I've taken this model structure from has
# not used units consistently (in particular the BINDING_WITH_PH). Down the line I need
# to track down a reliable parameterisation for this section.


def calculate_soil_carbon_updates(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    pH: NDArray[np.float32],
    bulk_density: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
    delta_pools_ordered: dict[str, NDArray[np.float32]],
) -> NDArray[np.float32]:
    """Calculate net change for each carbon pool.

    This function calls lower level functions which calculate the transfers between
    pools. When all transfers have been calculated the net transfer is used to
    calculate the net change for each pool.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_c_pool_maom: Mineral associated organic matter pool [kg C m^-3]
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        pH: pH values for each soil grid cell
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        soil_moisture: relative water content for each soil grid cell [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        percent_clay: Percentage clay for each soil grid cell
        delta_pools_ordered: Dictionary to store pool changes in the order that pools
            are stored in the initial condition vector.

    Returns:
        A vector containing net changes to each pool. Order [lmwc, maom].
    """
    # TODO - Add interactions which involve the three missing carbon pools

    # Find scalar factors that multiple rates
    temp_scalar = convert_temperature_to_scalar(soil_temp)
    moist_scalar = convert_moisture_to_scalar(soil_moisture)
    moist_temp_scalar = moist_scalar * temp_scalar

    # Calculate transfers between pools
    lmwc_to_maom = calculate_mineral_association(
        soil_c_pool_lmwc,
        soil_c_pool_maom,
        pH,
        bulk_density,
        moist_temp_scalar,
        percent_clay,
    )
    microbial_uptake = calculate_microbial_carbon_uptake(
        soil_c_pool_lmwc, soil_c_pool_microbe, moist_temp_scalar, soil_temp
    )
    microbial_respiration = calculate_maintenance_respiration(
        soil_c_pool_microbe, moist_temp_scalar
    )
    necromass_adsorption = calculate_necromass_adsorption(
        soil_c_pool_microbe, moist_temp_scalar
    )
    labile_carbon_leaching = calculate_labile_carbon_leaching(
        soil_c_pool_lmwc, moist_temp_scalar
    )
    litter_input_to_lmwc = calculate_direct_litter_input_to_lmwc()

    # Determine net changes to the pools
    delta_pools_ordered["soil_c_pool_lmwc"] = (
        litter_input_to_lmwc - lmwc_to_maom - microbial_uptake - labile_carbon_leaching
    )
    delta_pools_ordered["soil_c_pool_maom"] = lmwc_to_maom + necromass_adsorption
    delta_pools_ordered["soil_c_pool_microbe"] = (
        microbial_uptake - microbial_respiration - necromass_adsorption
    )

    # Create output array of pools in desired order
    return np.concatenate(list(delta_pools_ordered.values()))


def calculate_mineral_association(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_maom: NDArray[np.float32],
    pH: NDArray[np.float32],
    bulk_density: NDArray[np.float32],
    moist_temp_scalar: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
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
        moist_temp_scalar: A scalar capturing the combined impact of soil moisture and
            temperature on process rates
        percent_clay: Percentage clay for each soil grid cell

    Returns:
        The net flux from LMWC to MAOM [kg C m^-3 day^-1]
    """

    # Calculate
    Q_max = calculate_max_sorption_capacity(bulk_density, percent_clay)
    equib_maom = calculate_equilibrium_maom(pH, Q_max, soil_c_pool_lmwc)

    return (
        moist_temp_scalar * soil_c_pool_lmwc * (equib_maom - soil_c_pool_maom) / Q_max
    )


def calculate_max_sorption_capacity(
    bulk_density: NDArray[np.float32],
    percent_clay: NDArray[np.float32],
    coef: MaxSorptionWithClay = MaxSorptionWithClay(),
) -> NDArray[np.float32]:
    """Calculate maximum sorption capacity based on bulk density and clay content.

    The maximum sorption capacity is the maximum amount of mineral associated organic
    matter that can exist per unit volume. This expression and its parameters are also
    drawn from :cite:t:`mayes_relation_2012`. In that paper max sorption also depends on
    Fe content, but we are ignoring this for now.

    Args:
        bulk_density: bulk density values for each soil grid cell [kg m^-3]
        percent_clay: Percentage clay for each soil grid cell

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

    Q_max = bulk_density * 10 ** (coef.slope * np.log10(percent_clay) + coef.intercept)
    return Q_max


def calculate_equilibrium_maom(
    pH: NDArray[np.float32],
    Q_max: NDArray[np.float32],
    lmwc: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate equilibrium MAOM concentration based on Langmuir coefficients.

    Equilibrium concentration of mineral associated organic matter (MAOM) is calculated
    by this function under the assumption that the concentration of low molecular weight
    carbon (LMWC) is fixed.

    Args:
        pH: pH values for each soil grid cell
        Q_max: Maximum sorption capacities [kg C m^-3]
        lmwc: Low molecular weight carbon pool [kg C m^-3]

    Returns:
        Equilibrium concentration of MAOM [kg C m^-3]
    """

    binding_coefficient = calculate_binding_coefficient(pH)
    return (binding_coefficient * Q_max * lmwc) / (1 + lmwc * binding_coefficient)


def calculate_binding_coefficient(
    pH: NDArray[np.float32], coef: BindingWithPH = BindingWithPH()
) -> NDArray[np.float32]:
    """Calculate Langmuir binding coefficient based on pH.

    This specific expression and its parameters are drawn from
    :cite:t:`mayes_relation_2012`.

    Args:
        pH: pH values for each soil grid cell

    Returns:
        Langmuir binding coefficients for mineral association of labile carbon [m^3
        kg^-1]
    """

    return 10.0 ** (coef.slope * pH + coef.intercept)


def convert_temperature_to_scalar(
    soil_temp: NDArray[np.float32], coef: TempScalar = TempScalar()
) -> NDArray[np.float32]:
    """Convert soil temperature into a factor to multiply rates by.

    This form is used in :cite:t:`abramoff_millennial_2018` to minimise differences with
    the CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
       soil_temp: soil temperature for each soil grid cell [degrees C]

    Returns:
        A scalar that captures the impact of soil temperature on process rates
    """

    # This expression is drawn from Abramoff et al. (2018)
    numerator = coef.t_2 + (coef.t_3 / np.pi) * np.arctan(
        np.pi * (soil_temp - coef.t_1)
    )
    denominator = coef.t_2 + (coef.t_3 / np.pi) * np.arctan(
        np.pi * coef.t_4 * (coef.ref_temp - coef.t_1)
    )

    return np.divide(numerator, denominator)


def convert_moisture_to_scalar(
    soil_moisture: NDArray[np.float32],
    coef: MoistureScalar = MoistureScalar(),
) -> NDArray[np.float32]:
    """Convert soil moisture into a factor to multiply rates by.

    This form is used in :cite:t:`abramoff_millennial_2018` to minimise differences with
    the CENTURY model. We very likely want to define our own functional form here. I'm
    also a bit unsure how this form was even obtained, so further work here is very
    needed.

    Args:
        soil_moisture: relative water content for each soil grid cell (unitless)

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
    return 1 / (1 + coef.coefficient * np.exp(-coef.exponent * soil_moisture))


def calculate_maintenance_respiration(
    soil_c_pool_microbe: NDArray[np.float32],
    moist_temp_scalar: NDArray[np.float32],
    microbial_turnover_rate: float = MICROBIAL_TURNOVER_RATE,
) -> NDArray[np.float32]:
    """Calculate the maintenance respiration of the microbial pool.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moist_scalar: A scalar capturing the combined impact of soil moisture and
            temperature on process rates
        microbial_turnover_rate: Rate of microbial biomass turnover [day^-1]

    Returns:
        Total respiration for all microbial biomass
    """

    return microbial_turnover_rate * moist_temp_scalar * soil_c_pool_microbe


def calculate_necromass_adsorption(
    soil_c_pool_microbe: NDArray[np.float32],
    moist_temp_scalar: NDArray[np.float32],
    necromass_adsorption_rate: float = NECROMASS_ADSORPTION_RATE,
) -> NDArray[np.float32]:
    """Calculate adsorption of microbial necromass to soil minerals.

    Args:
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moist_temp_scalar: A scalar capturing the combined impact of soil moisture and
            temperature on process rates
        necromass_adsorption_rate: Rate at which necromass is adsorbed by soil minerals

    Returns:
        Adsorption of microbial biomass to mineral associated organic matter (MAOM)
    """

    return necromass_adsorption_rate * moist_temp_scalar * soil_c_pool_microbe


def calculate_carbon_use_efficiency(
    soil_temp: NDArray[np.float32], paras: CarbonUseEfficiency = CarbonUseEfficiency()
) -> NDArray[np.float32]:
    """Calculate the (temperature dependant) carbon use efficiency.

    Args:
       soil_temp: soil temperature for each soil grid cell [degrees C]

    Returns:
        The carbon use efficiency (CUE) of the microbial community
    """

    return paras.reference_cue - paras.cue_with_temperature * (
        soil_temp - paras.reference_temp
    )


def calculate_microbial_saturation(
    soil_c_pool_microbe: NDArray[np.float32],
    half_sat_microbial_activity: float = HALF_SAT_MICROBIAL_ACTIVITY,
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


def calculate_microbial_carbon_uptake(
    soil_c_pool_lmwc: NDArray[np.float32],
    soil_c_pool_microbe: NDArray[np.float32],
    moist_temp_scalar: NDArray[np.float32],
    soil_temp: NDArray[np.float32],
    max_uptake_rate: float = MAX_UPTAKE_RATE_LABILE_C,
) -> NDArray[np.float32]:
    """Calculate amount of labile carbon taken up by microbes.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_c_pool_microbe: Microbial biomass (carbon) pool [kg C m^-3]
        moist_temp_scalar: A scalar capturing the combined impact of soil moisture and
            temperature on process rates
        soil_temp: soil temperature for each soil grid cell [degrees C]
        max_uptake_rate: Maximum rate at which microbes can uptake labile carbon
            [TODO - Add units]

    Returns:
        Uptake of low molecular weight carbon (LMWC) by the soil microbial biomass.
    """

    # Calculate carbon use efficiency and microbial saturation
    carbon_use_efficency = calculate_carbon_use_efficiency(soil_temp)
    microbial_saturation = calculate_microbial_saturation(soil_c_pool_microbe)

    # TODO - the quantities calculated above can be used to calculate the carbon
    # respired instead of being uptaken. This isn't currently of interest, but will be
    # in future

    return (
        max_uptake_rate
        * moist_temp_scalar
        * soil_c_pool_lmwc
        * microbial_saturation
        * carbon_use_efficency
    )


def calculate_labile_carbon_leaching(
    soil_c_pool_lmwc: NDArray[np.float32],
    moist_temp_scalar: NDArray[np.float32],
    leaching_rate: float = LEACHING_RATE_LABILE_CARBON,
) -> NDArray[np.float32]:
    """Calculate rate at which labile carbon is leached.

    This is adopted from Abramoff et al. We definitely need to give more thought to how
    we model leaching.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        moist_temp_scalar: A scalar capturing the combined impact of soil moisture and
            temperature on process rates
        leaching_rate: The rate at which labile carbon leaches from the soil [day^-1]

    Returns:
        The amount of labile carbon leached
    """

    return leaching_rate * moist_temp_scalar * soil_c_pool_lmwc


def calculate_direct_litter_input_to_lmwc(
    carbon_input_to_pom: float = CARBON_INPUT_TO_POM,
    litter_input_rate: float = LITTER_INPUT_RATE,
) -> float:
    """Calculate direct input from litter to LMWC pool.

    This process is very much specific to :cite:t:`abramoff_millennial_2018`, and I
    don't think we want to preserve it long term.

    Args:
        carbon_input_to_pom: Proportion of litter carbon input that goes to POM (rather
            than LMWC) [unitless].
        litter_input_rate: Rate at which carbon moves from litter "pool" to soil carbon
            pools [kg C m^-2 day^-1].

    Returns:
        Amount of carbon directly added to LMWC pool from litter.
    """

    return (1 - carbon_input_to_pom) * litter_input_rate
