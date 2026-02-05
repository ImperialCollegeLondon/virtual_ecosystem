"""The ``models.soil.uptake`` module contains functions that are used to
capture the uptake competition for the various microbial groups in the simulation.
"""  # noqa: D205

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.models.soil.env_factors import (
    calculate_carbon_use_efficiency,
    calculate_temperature_effect_on_microbes,
)
from virtual_ecosystem.models.soil.microbial_groups import MicrobialGroupConstants
from virtual_ecosystem.models.soil.model_config import SoilConstants


@dataclass
class NetNutrientConsumption:
    """Net consumption of each labile due to microbial activity.

    The labile inorganic pools can have negative consumptions because microbes can
    mineralise inorganic nutrients from nutrients in organic form.
    """

    carbon: NDArray[np.floating]
    """Uptake of low molecular weight carbon [kg C m^-3 day^-1]."""

    organic_nitrogen: NDArray[np.floating]
    """Uptake of dissolved organic nitrogen [kg N m^-3 day^-1]."""

    ammonium: NDArray[np.floating]
    """Uptake of ammonium [kg N m^-3 day^-1]."""

    nitrate: NDArray[np.floating]
    """Uptake of nitrate [kg N m^-3 day^-1]."""

    organic_phosphorus: NDArray[np.floating]
    """Uptake of dissolved organic phosphorus [kg P m^-3 day^-1]."""

    inorganic_phosphorus: NDArray[np.floating]
    """Uptake of labile inorganic phosphorus [kg P m^-3 day^-1]."""


@dataclass
class MaxUptakeRates:
    """Maximum rate at which each nutrient can be taken up by the microbial group."""

    carbon: NDArray[np.floating]
    """Maximum uptake of low molecular weight carbon [kg C m^-3 day^-1]."""

    organic_nitrogen: NDArray[np.floating]
    """Maximum uptake rate of organic nitrogen [kg N m^-3 day^-1].
    
    This nitrogen is taken up along with the :term:`LMWC` uptake.
    """

    organic_phosphorus: NDArray[np.floating]
    """Maximum uptake rate of organic phosphorus [kg P m^-3 day^-1].
    
    This phosphorus is taken up along with the :term:`LMWC` uptake.
    """

    ammonium: NDArray[np.floating]
    """Maximum uptake rate of ammonium [kg N m^-3 day^-1]."""

    nitrate: NDArray[np.floating]
    """Maximum uptake rate of nitrate [kg N m^-3 day^-1]."""

    inorganic_phosphorus: NDArray[np.floating]
    """Maximum uptake rate of labile inorganic phosphorus [kg P m^-3 day^-1]."""


def calculate_nutrient_uptake_rates(
    soil_c_pool_lmwc: NDArray[np.floating],
    soil_n_pool_don: NDArray[np.floating],
    soil_n_pool_ammonium: NDArray[np.floating],
    soil_n_pool_nitrate: NDArray[np.floating],
    soil_p_pool_dop: NDArray[np.floating],
    soil_p_pool_labile: NDArray[np.floating],
    microbial_pool_size: NDArray[np.floating],
    external_carbon_supply: NDArray[np.floating] | None,
    water_factor: NDArray[np.floating],
    pH_factor: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    constants: SoilConstants,
    functional_group: MicrobialGroupConstants,
) -> tuple[NDArray[np.floating], NetNutrientConsumption]:
    """Calculate the rate at which microbes uptake each nutrient.

    These rates are found based on the assumption that microbial stoichiometry is
    inflexible, i.e. assuming that the rate of uptake of all nutrients (carbon, nitrogen
    and phosphorus) needed for growth will be set by the least available nutrient. The
    carbon case is more complex as carbon gets used both for biomass synthesis and
    respiration. In this case, we calculate the carbon use efficiency and use this to
    find the maximum amount of carbon available for biomass synthesis. Once the most
    limiting nutrient uptake stream is found it is straightforward to find the demand
    for other nutrients. This is because the microbial biomass stoichiometry can only
    remain the same if nutrients are taken up following the same stoichiometry (with an
    adjustment made for carbon use efficiency).

    Biomass synthesis is split between the synthesis of new cellular biomass and the
    production of extracellular enzymes. We assume that extracellular enzymes are always
    produced in fixed proportion to the rate at which new biomass is synthesised. As
    such, we calculate the nutrient costs of synthesising new biomass based on a
    weighted (by relative investment in production) average of the stoichiometry of the
    different enzymes and the microbial group itself.

    The balance of mineralisation and immobilisation rates of inorganic nitrogen and
    phosphorus are also calculated in this function. This is done by calculating the
    difference between the demand for nitrogen and phosphorus and their uptake due to
    organic matter uptake. If more is taken up as a component of organic matter than is
    needed then nutrients are mineralised, i.e. mass is added to the relevant inorganic
    nutrient pool. Conversely, if more is required to meet demand uptake occurs from the
    relevant inorganic nutrient pool (this is termed immobilisation). Two forms
    inorganic nitrogen can be taken up by microbes, ammonium and nitrate. The rate at
    which these are taken up is determined by the ratio of their uptake rates. When
    inorganic nitrogen is mineralised the ratio of ammonium to nitrate mineralised is
    determined by a fixed ratio defined in the model constants.

    Symbiotic microbes depend on their symbiotic plant partners for their carbon
    requirements. They uptake the nitrogen and phosphorus they need to grow from the
    soil, preferentially taking inorganic nutrients. A fixed (but configurable) fraction
    of their uptake is supplied to their symbiotic partners. If more carbon is supplied
    than the microbes can use the surplus is added to the soil as :term:`LMWC`.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_n_pool_don: Dissolved organic nitrogen pool [kg N m^-3]
        soil_n_pool_ammonium: Soil ammonium pool [kg N m^-3]
        soil_n_pool_nitrate: Soil nitrate pool [kg N m^-3]
        soil_p_pool_dop: Dissolved organic phosphorus pool [kg P m^-3]
        soil_p_pool_labile: Labile inorganic phosphorus pool [kg P m^-3]
        microbial_pool_size: Amount of biomass for functional of interest [kg C m^-3]
        external_carbon_supply: Additional supply of carbon to the microbial group from
            external sources (i.e. partner plants) [kg C m^-3 day^-1]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.
        functional_group: A data class containing the parameters defining the microbial
            functional group

    Returns:
        A tuple containing the rate at which microbial (cellular) biomass is generated
        due to nutrient uptake, as well as a dataclass containing the rate at which
        carbon, nitrogen and phosphorus get taken up.

    Raises:
        ValueError: If an external carbon supply is provided without a corresponding
            demand for nitrogen and phosphorus exchange
    """

    # Calculate carbon use efficiency as it is used in multiple subsequent functions
    carbon_use_efficiency = calculate_carbon_use_efficiency(
        soil_temp=soil_temp,
        reference_cue_logit=constants.reference_cue_logit,
        cue_reference_temp=constants.cue_reference_temp,
        logit_cue_with_temp=constants.logit_cue_with_temperature,
    )

    max_uptake_rates = calculate_maximum_uptake_rates(
        soil_c_pool_lmwc=soil_c_pool_lmwc,
        soil_n_pool_don=soil_n_pool_don,
        soil_n_pool_ammonium=soil_n_pool_ammonium,
        soil_n_pool_nitrate=soil_n_pool_nitrate,
        soil_p_pool_dop=soil_p_pool_dop,
        soil_p_pool_labile=soil_p_pool_labile,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        functional_group=functional_group,
    )

    actual_carbon_gain = calculate_actual_carbon_gain(
        max_uptake_rates=max_uptake_rates,
        external_carbon_supply=external_carbon_supply,
        carbon_use_efficiency=carbon_use_efficiency,
        functional_group=functional_group,
    )

    if external_carbon_supply is not None:
        consumption_rates = find_net_nutrient_consumptions_symbiotic(
            max_uptake_rates=max_uptake_rates,
            actual_carbon_gain=actual_carbon_gain,
            external_carbon_supply=external_carbon_supply,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_group,
        )
    else:
        consumption_rates = find_net_nutrient_consumptions_free_living(
            max_uptake_rates=max_uptake_rates,
            actual_carbon_gain=actual_carbon_gain,
            carbon_use_efficiency=carbon_use_efficiency,
            functional_group=functional_group,
            ammonium_mineralisation_proportion=constants.ammonium_mineralisation_proportion,
        )

    # TODO - the quantities calculated above can be used to calculate the carbon
    # respired instead of being uptaken. This isn't currently of interest, but will be
    # in future

    # Carbon gain needs to be divided by the proportional enzyme production as it
    # represents biomass gain and enzyme production.
    return (
        actual_carbon_gain
        / (
            1
            + sum(functional_group.enzyme_production.values())
            + functional_group.reproductive_allocation
        ),
        consumption_rates,
    )


def find_net_nutrient_consumptions_free_living(
    max_uptake_rates: MaxUptakeRates,
    actual_carbon_gain: NDArray[np.floating],
    carbon_use_efficiency: NDArray[np.floating],
    functional_group: MicrobialGroupConstants,
    ammonium_mineralisation_proportion: float,
) -> NetNutrientConsumption:
    """Find net consumption of each nutrient class for a free-living microbial group.

    These net consumptions can be negative as microbes can mineralise nutrients from
    organic matter.

    We assume that organic matter is always taken up at the maximum possible rate. This
    is because organic matter contains carbon, nitrogen and phosphorus and one of these
    will always be limiting growth. Any excess uptake through organic matter gets
    returned (this represents overflow metabolism). If the microbial group is heavily
    carbon limited nutrients will be returned to the soil in an inorganic form,
    conversely if it is less carbon limited the excess nutrients will be returned in an
    organic form. If the demand for nitrogen or phosphorus exceeds the amount provided
    through organic matter uptake, inorganic nutrients are uptaken.

    Args:
        max_uptake_rates: Maximum uptake rates for each nutrient class [kg m^-3 day^-1]
        actual_carbon_gain: The rate at which carbon is assimilated to biomass [kg C
            m^-3 day^-1]
        carbon_use_efficiency: Carbon use efficiency of the microbial group (varies with
            temperature) [unitless]
        functional_group: A data class containing the parameters defining the microbial
            functional group.
        ammonium_mineralisation_proportion: Proportion of microbially mineralised
            nitrogen that takes the form of ammonium [unitless]

    Returns:
        The net consumption/production of each nutrient class [kg m^-3 day^-1].
    """

    # Determine how limiting carbon is (as a proportion). The zero carbon uptake case is
    # handled by assuming that carbon limitation is total in this case.
    carbon_limitation = np.divide(
        actual_carbon_gain,
        max_uptake_rates.carbon * carbon_use_efficiency,
        out=np.ones_like(max_uptake_rates.carbon, dtype=float),
        where=(max_uptake_rates.carbon > 0),
    )

    # Calculate biomass demands for nitrogen and phosphorus
    nitrogen_demand = (
        actual_carbon_gain / functional_group.synthesis_nutrient_ratios["nitrogen"]
    )
    phosphorus_demand = (
        actual_carbon_gain / functional_group.synthesis_nutrient_ratios["phosphorus"]
    )
    # Next find if organic uptake satisfies demands for phosphorus and nitrogen
    nitrogen_inorganic_demand = nitrogen_demand - max_uptake_rates.organic_nitrogen
    phosphorus_inorganic_demand = (
        phosphorus_demand - max_uptake_rates.organic_phosphorus
    )

    # Calculate how much of the organic nitrogen and phosphorus should be returned in an
    # organic form
    organic_nitrogen_return = np.where(
        nitrogen_inorganic_demand < 0,
        -nitrogen_inorganic_demand * (1 - carbon_limitation),
        0.0,
    )
    organic_phosphorus_return = np.where(
        phosphorus_inorganic_demand < 0,
        -phosphorus_inorganic_demand * (1 - carbon_limitation),
        0.0,
    )

    # Find how much inorganic nitrogen and phosphorus is taken up or released
    inorganic_nitrogen_change = np.where(
        nitrogen_inorganic_demand >= 0,
        nitrogen_inorganic_demand,
        nitrogen_inorganic_demand * carbon_limitation,
    )
    inorganic_phosphorus_change = np.where(
        phosphorus_inorganic_demand >= 0,
        phosphorus_inorganic_demand,
        phosphorus_inorganic_demand * carbon_limitation,
    )

    # For immobilisation of nitrogen, the proportion of ammonium and nitrate taken up
    # follows the proportion of the maximum uptake rates (if either is above zero)
    ammonium_uptake_proportion = np.divide(
        max_uptake_rates.ammonium,
        max_uptake_rates.ammonium + max_uptake_rates.nitrate,
        out=np.zeros_like(max_uptake_rates.ammonium, dtype=float),
        where=(max_uptake_rates.ammonium > 0) | (max_uptake_rates.nitrate > 0),
    )

    # Whether the uptake proportion or the mineralisation proportion is relevant depends
    # whether inorganic nitrogen is being taken up or not
    ammonium_to_nitrate_proportion = np.where(
        inorganic_nitrogen_change > 0,
        ammonium_uptake_proportion,
        ammonium_mineralisation_proportion,
    )
    ammonium_change = inorganic_nitrogen_change * ammonium_to_nitrate_proportion
    nitrate_change = inorganic_nitrogen_change * (1 - ammonium_to_nitrate_proportion)

    return NetNutrientConsumption(
        organic_nitrogen=max_uptake_rates.organic_nitrogen - organic_nitrogen_return,
        organic_phosphorus=(
            max_uptake_rates.organic_phosphorus - organic_phosphorus_return
        ),
        carbon=actual_carbon_gain / carbon_use_efficiency,
        ammonium=ammonium_change,
        nitrate=nitrate_change,
        inorganic_phosphorus=inorganic_phosphorus_change,
    )


def find_net_nutrient_consumptions_symbiotic(
    max_uptake_rates: MaxUptakeRates,
    actual_carbon_gain: NDArray[np.floating],
    external_carbon_supply: NDArray[np.floating],
    carbon_use_efficiency: NDArray[np.floating],
    functional_group: MicrobialGroupConstants,
) -> NetNutrientConsumption:
    """Find net consumption of each nutrient class for a symbiotic microbial group.

    We assume that inorganic nutrients are preferentially taken up, as the symbiotic
    microbes are reliant on their hosts for carbon. If the demand for nitrogen or
    phosphorus exceeds the amount provided through inorganic matter uptake, organic
    nutrients are uptaken. Though this implies a corresponding uptake of carbon, we do
    not track it as we are assuming that the symbiotic partners cannot make use of this
    carbon at all, and so immediately release it. If more carbon is supplied (by
    symbiotic plant partners) than the microbes make use of the surplus carbon is added
    to the soil as :term:`LMWC`.

    Args:
        max_uptake_rates: Maximum uptake rates for each nutrient class [kg m^-3 day^-1]
        actual_carbon_gain: The rate at which carbon is assimilated to biomass [kg C
            m^-3 day^-1]
        external_carbon_supply: Additional supply of carbon to the microbial group from
            symbiotic partner plants [kg C m^-3 day^-1]
        carbon_use_efficiency: Carbon use efficiency of the microbial group (varies with
            temperature) [unitless]
        functional_group: A data class containing the parameters defining the microbial
            functional group.

    Returns:
        The net consumption/production of each nutrient class [kg m^-3 day^-1].
    """

    # Calculate total demands for nitrogen and phosphorus by dividing amount uptaken for
    # assimilation by the fraction of the total uptake that this represents
    nitrogen_demand = (
        actual_carbon_gain / functional_group.synthesis_nutrient_ratios["nitrogen"]
    ) / (1 - functional_group.symbiote_nitrogen_uptake_fraction)

    phosphorus_demand = (
        actual_carbon_gain / functional_group.synthesis_nutrient_ratios["phosphorus"]
    ) / (1 - functional_group.symbiote_phosphorus_uptake_fraction)

    # Inorganic nutrients are preferentially taken up, so calculate how much of each of
    # these are taken up
    inorganic_nitrogen_demand = np.where(
        nitrogen_demand >= max_uptake_rates.ammonium + max_uptake_rates.nitrate,
        max_uptake_rates.ammonium + max_uptake_rates.nitrate,
        nitrogen_demand,
    )
    inorganic_phosphorus_demand = np.where(
        phosphorus_demand >= max_uptake_rates.inorganic_phosphorus,
        max_uptake_rates.inorganic_phosphorus,
        phosphorus_demand,
    )

    # Organic nutrients are then taken up if the demand can't be satisfied by inorganic
    # uptake alone.
    organic_nitrogen_demand = nitrogen_demand - inorganic_nitrogen_demand
    organic_phosphorus_demand = phosphorus_demand - inorganic_phosphorus_demand

    # For inorganic nitrogen uptake, the proportion of ammonium and nitrate taken up
    # follows the proportion of the maximum uptake rates (if either is above zero)
    ammonium_uptake_proportion = np.divide(
        max_uptake_rates.ammonium,
        max_uptake_rates.ammonium + max_uptake_rates.nitrate,
        out=np.zeros_like(max_uptake_rates.ammonium, dtype=float),
        where=(max_uptake_rates.ammonium > 0) | (max_uptake_rates.nitrate > 0),
    )

    ammonium_uptake = inorganic_nitrogen_demand * ammonium_uptake_proportion
    nitrate_uptake = inorganic_nitrogen_demand * (1 - ammonium_uptake_proportion)

    # Finally need to find how much additional carbon has been provided
    surplus_carbon_supply = external_carbon_supply - (
        actual_carbon_gain / carbon_use_efficiency
    )

    return NetNutrientConsumption(
        organic_nitrogen=organic_nitrogen_demand,
        organic_phosphorus=organic_phosphorus_demand,
        carbon=-surplus_carbon_supply,
        ammonium=ammonium_uptake,
        nitrate=nitrate_uptake,
        inorganic_phosphorus=inorganic_phosphorus_demand,
    )


def calculate_actual_carbon_gain(
    max_uptake_rates: MaxUptakeRates,
    external_carbon_supply: NDArray[np.floating] | None,
    carbon_use_efficiency: NDArray[np.floating],
    functional_group: MicrobialGroupConstants,
) -> NDArray[np.floating]:
    """Calculate the rate at which carbon is assimilated by microbes.

    The limitation that each nutrient places on carbon assimilation is determined. For
    carbon this is based on carbon use efficiency, but in the case of nitrogen and
    phosphorus this is determined based on biomass stoichiometry (i.e. you can't add
    more carbon to biomass if you are deficient in nitrogen). This is used to calculate
    the actual rate at which carbon is assimilated to biomass.

    In the symbiotic case, microbes can only use the carbon is supplied by their plant
    partners to grow. In return for this, symbiotic microbes must provide a fraction of
    the nutrients they uptake back to the plants. This means that they can only
    assimilate a fraction of the nutrients that they uptake as biomass, which generally
    reduces maximum carbon assimilation rates.

    Args:
        max_uptake_rates: Maximum uptake rates for each nutrient class [kg m^-3 day^-1]
        external_carbon_supply: Additional supply of carbon to the microbial group from
            external sources (i.e. partner plants) [kg C m^-3 day^-1]
        carbon_use_efficiency: Carbon use efficiency of the microbial group (varies with
            temperature) [unitless]
        functional_group: A data class containing the parameters defining the microbial
            functional group.

    Returns:
        The rate at which carbon is assimilated to biomass [kg m^-3 day^-1].
    """

    # In symbiotic cases only external carbon is used, and in free-living cases there is
    # no external carbon supplied
    if external_carbon_supply is not None:
        carbon_gain_max = external_carbon_supply * carbon_use_efficiency
    else:
        carbon_gain_max = max_uptake_rates.carbon * carbon_use_efficiency

    nitrogen_gain_max = (
        max_uptake_rates.organic_nitrogen
        + max_uptake_rates.ammonium
        + max_uptake_rates.nitrate
    ) * (1 - functional_group.symbiote_nitrogen_uptake_fraction)
    phosphorus_gain_max = (
        max_uptake_rates.organic_phosphorus + max_uptake_rates.inorganic_phosphorus
    ) * (1 - functional_group.symbiote_phosphorus_uptake_fraction)

    # Find the maximum rate of carbon assimilation based on nitrogen and phosphorus
    # uptake rates, and biomass stoichiometric ratios
    nitrogen_limit = (
        functional_group.synthesis_nutrient_ratios["nitrogen"] * nitrogen_gain_max
    )
    phosphorus_limit = (
        functional_group.synthesis_nutrient_ratios["phosphorus"] * phosphorus_gain_max
    )

    # Find actual rate of carbon gain based on most limiting uptake rate, then find
    # nutrient gain and total carbon consumption based on this
    return np.minimum.reduce([carbon_gain_max, nitrogen_limit, phosphorus_limit])


def calculate_maximum_uptake_rates(
    soil_c_pool_lmwc: NDArray[np.floating],
    soil_n_pool_don: NDArray[np.floating],
    soil_n_pool_ammonium: NDArray[np.floating],
    soil_n_pool_nitrate: NDArray[np.floating],
    soil_p_pool_dop: NDArray[np.floating],
    soil_p_pool_labile: NDArray[np.floating],
    microbial_pool_size: NDArray[np.floating],
    water_factor: NDArray[np.floating],
    pH_factor: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    functional_group: MicrobialGroupConstants,
) -> MaxUptakeRates:
    """Calculate the maximum uptake rate for each category of nutrient.

    Categories are, carbon, organic nitrogen and phosphorus, inorganic nitrogen
    (ammonium and nitrate), and inorganic phosphorus.

    Args:
        soil_c_pool_lmwc: Low molecular weight carbon pool [kg C m^-3]
        soil_n_pool_don: Dissolved organic nitrogen pool [kg N m^-3]
        soil_n_pool_ammonium: Soil ammonium pool [kg N m^-3]
        soil_n_pool_nitrate: Soil nitrate pool [kg N m^-3]
        soil_p_pool_dop: Dissolved organic phosphorus pool [kg P m^-3]
        soil_p_pool_labile: Labile inorganic phosphorus pool [kg P m^-3]
        microbial_pool_size: Amount of biomass for functional of interest [kg C m^-3]
        lmwc_c_n_ratio: Carbon to nitrogen ratio of the low molecular weight carbon pool
            [unitless]
        lmwc_c_p_ratio: Carbon to phosphorus ratio of the low molecular weight carbon
            pool [unitless]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        constants: Set of constants for the soil model.
        functional_group: A data class containing the parameters defining the microbial
            functional group

    Returns:
        The maximum rate at which each category of nutrient can be taken up by the
        microbial group of interest.
    """

    # Calculate highest possible microbial uptake rates for organic matter and inorganic
    # forms of nitrogen and phosphorus
    carbon_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_c_pool_lmwc,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_labile_C,
        half_saturation_constant=functional_group.half_sat_labile_C_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )
    ammonium_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_n_pool_ammonium,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_ammonium,
        half_saturation_constant=functional_group.half_sat_ammonium_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )
    nitrate_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_n_pool_nitrate,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_nitrate,
        half_saturation_constant=functional_group.half_sat_nitrate_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )
    inorganic_phosphorus_uptake_rate_max = calculate_highest_achievable_nutrient_uptake(
        labile_nutrient_pool=soil_p_pool_labile,
        microbial_pool_size=microbial_pool_size,
        water_factor=water_factor,
        pH_factor=pH_factor,
        soil_temp=soil_temp,
        max_uptake_rate=functional_group.max_uptake_rate_labile_p,
        half_saturation_constant=functional_group.half_sat_labile_p_uptake,
        activation_energy_uptake=functional_group.activation_energy_uptake_rate,
        activation_energy_uptake_saturation=functional_group.activation_energy_uptake_saturation,
        reference_temperature=functional_group.reference_temperature,
    )

    # Find maximum possible uptake rates for organic nitrogen and phosphorus, based on
    # LMWC pool stoichiometry
    lmwc_c_n_ratio = soil_c_pool_lmwc / soil_n_pool_don
    lmwc_c_p_ratio = soil_c_pool_lmwc / soil_p_pool_dop
    organic_nitrogen_uptake_rate_max = carbon_uptake_rate_max / lmwc_c_n_ratio
    organic_phosphorus_uptake_rate_max = carbon_uptake_rate_max / lmwc_c_p_ratio

    return MaxUptakeRates(
        carbon=carbon_uptake_rate_max,
        organic_nitrogen=organic_nitrogen_uptake_rate_max,
        organic_phosphorus=organic_phosphorus_uptake_rate_max,
        ammonium=ammonium_uptake_rate_max,
        nitrate=nitrate_uptake_rate_max,
        inorganic_phosphorus=inorganic_phosphorus_uptake_rate_max,
    )


def calculate_highest_achievable_nutrient_uptake(
    labile_nutrient_pool: NDArray[np.floating],
    microbial_pool_size: NDArray[np.floating],
    water_factor: NDArray[np.floating],
    pH_factor: NDArray[np.floating],
    soil_temp: NDArray[np.floating],
    max_uptake_rate: float,
    activation_energy_uptake: float,
    half_saturation_constant: float,
    activation_energy_uptake_saturation: float,
    reference_temperature: float,
) -> NDArray[np.floating]:
    """Calculate highest achievable uptake rate for a specific nutrient.

    This function starts by calculating the impact that environmental factors have on
    the rate and saturation constants for microbial uptake. These constants are then
    used to calculate the maximum possible uptake rate for the specific nutrient and
    microbial group in question.

    Args:
        labile_nutrient_pool: Mass of nutrient that is in a readily uptakeable (labile)
            form [kg nut m^-3]
        microbial_pool_size: Size of microbial biomass (carbon) pool of interest [kg C
            m^-3]
        water_factor: A factor capturing the impact of soil water potential on microbial
            rates [unitless]
        pH_factor: A factor capturing the impact of soil pH on microbial rates
            [unitless]
        soil_temp: soil temperature for each soil grid cell [degrees C]
        max_uptake_rate: Maximum possible uptake rate of the nutrient (at reference
            temperature) [day^-1]
        activation_energy_uptake: Activation energy for nutrient uptake for the
            microbial group in question [J K^-1].
        half_saturation_constant: Half saturation constant for nutrient uptake (at
            reference temperature) [kg nut m^-3]
        activation_energy_uptake_saturation: Activation energy for nutrient uptake
            saturation for the microbial group in question [J K^-1].
        reference_temperature: The reference temperature of the Arrhenius equation [C]

    Returns:
        The maximum uptake rate by the soil microbial biomass for the nutrient in
        question.
    """

    # Calculate impact of temperature on the rate and saturation constants
    temp_factor_rate = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=activation_energy_uptake,
        reference_temperature=reference_temperature,
    )
    temp_factor_saturation = calculate_temperature_effect_on_microbes(
        soil_temperature=soil_temp,
        activation_energy=activation_energy_uptake_saturation,
        reference_temperature=reference_temperature,
    )
    # Rate and saturation constants are then adjusted based on these environmental
    # conditions
    rate_constant = max_uptake_rate * temp_factor_rate * water_factor * pH_factor
    saturation_constant = half_saturation_constant * temp_factor_saturation

    # Calculate both the rate of carbon uptake, and the rate at which this carbon is
    # assimilated into microbial biomass.
    uptake_rate = rate_constant * (
        (labile_nutrient_pool * microbial_pool_size)
        / (labile_nutrient_pool + saturation_constant)
    )

    return np.where(uptake_rate >= 0.0, uptake_rate, 0.0)
