"""The ``models.soil.constants`` module contains a set of dataclasses containing
constants (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_ecosystem.models.soil` module
"""  # noqa: D205, D415

from dataclasses import dataclass

import numpy as np

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class SoilConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `soil` model."""

    reference_cue: float = 0.6
    """Carbon use efficiency of community at the reference temperature [no units].

    Default value taken from :cite:t:`abramoff_millennial_2018`.
    """

    cue_reference_temp: float = 15.0
    """Reference temperature for carbon use efficiency [degrees C].

    Default value taken from :cite:t:`abramoff_millennial_2018`.
    """

    cue_with_temperature: float = 0.012
    """Change in carbon use efficiency with increasing temperature [degree C^-1].

    Default value taken from :cite:t:`abramoff_millennial_2018`.
    """

    soil_microbe_water_potential_optimum: float = -3.0
    """The water potential at which soil microbial rates are maximised [kPa].

    Value is taken from :cite:t:`moyano_responses_2013`.
    """

    soil_microbe_water_potential_halt: float = -15800.0
    """The water potential at which soil microbial activity stops entirely [kPa].

    Value is taken from :cite:t:`moyano_responses_2013`.
    """

    microbial_water_response_curvature: float = 1.47
    """Curvature of function for response of soil microbial rates to water potential.

    [unitless]. Value is taken from :cite:t:`moyano_responses_2013`.
    """

    arrhenius_reference_temp: float = 12.0
    """Reference temperature for the Arrhenius equation [C].

    This is the reference temperature used in :cite:t:`wang_development_2013`, which is
    the source of the activation energies and corresponding rates.
    """

    max_bacterial_uptake_rate_labile_C: float = 0.04
    """Maximum rate at the reference temperature of labile carbon uptake [day^-1].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - Source of this constant is not completely clear, investigate this further
    once fungi are added.
    """

    max_fungal_uptake_rate_labile_C: float = 0.04
    """Maximum rate at the reference temperature of labile carbon uptake [day^-1].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - Source of this constant is not completely clear, investigate this further
    once fungi are added.
    """

    activation_energy_microbial_uptake: float = 47000
    """Activation energy for bacterial nutrient uptake [J K^-1].

    Value taken from :cite:t:`wang_development_2013`. The maximum labile carbon uptake
    rate that this activation energy corresponds to is given by
    :attr:`max_bacterial_uptake_rate_labile_C`. This activation energy is assumed to be
    the same for the uptake of other nutrients as for carbon.
    """

    half_sat_bacterial_labile_C_uptake: float = 0.364
    """Half saturation constant for bacterial uptake of labile carbon (LMWC).

    [kg C m^-3]. This was calculated from the value provided in
    :cite:t:`wang_development_2013` assuming an average bulk density of 1400 [kg m^-3].
    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.
    """

    half_sat_fungal_labile_C_uptake: float = 0.364
    """Half saturation constant for fungal uptake of labile carbon (LMWC).

    [kg C m^-3]. This was calculated from the value provided in
    :cite:t:`wang_development_2013` assuming an average bulk density of 1400 [kg m^-3].
    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.
    """

    activation_energy_uptake_saturation: float = 30000
    """Activation energy for nutrient uptake saturation constants [J K^-1].

    Taken from :cite:t:`wang_development_2013`. This is assumed to be the same across
    all nutrients.
    """

    half_sat_pom_decomposition: float = 70.0
    """Half saturation constant for POM decomposition to LMWC [kg C m^-3].

    This was calculated from the value provided in :cite:t:`wang_development_2013`
    assuming an average bulk density of 1400 [kg m^-3]. The reference temperature is
    given by :attr:`arrhenius_reference_temp`, and the corresponding activation energy
    is given by :attr:`activation_energy_pom_decomp_saturation`.
    """

    activation_energy_pom_decomp_saturation: float = 30000
    """Activation energy for POM decomposition saturation constant [J K^-1].

    Taken from :cite:t:`wang_development_2013`.
    """

    max_decomp_rate_pom: float = 60.0
    """Maximum rate for particulate organic matter break down (at reference temp).

    Units of [day^-1]. The reference temperature is given by
    :attr:`arrhenius_reference_temp`, and the corresponding activation energy is given
    by :attr:`activation_energy_pom_decomp_rate`.

    TODO - Source of this constant is not completely clear, investigate this further
    once lignin chemistry is added.
    """

    activation_energy_pom_decomp_rate: float = 37000
    """Activation energy for decomposition of particulate organic matter [J K^-1].

    Taken from :cite:t:`wang_development_2013`.
    """

    half_sat_maom_decomposition: float = 350.0
    """Half saturation constant for MAOM decomposition to LMWC [kg C m^-3].

    This was calculated from the value provided in :cite:t:`wang_development_2013`
    assuming an average bulk density of 1400 [kg m^-3]. The reference temperature is
    given by :attr:`arrhenius_reference_temp`, and the corresponding activation energy
    is given by :attr:`activation_energy_maom_decomp_saturation`.
    """

    activation_energy_maom_decomp_saturation: float = 30000
    """Activation energy for MAOM decomposition saturation constant [J K^-1].

    Taken from :cite:t:`wang_development_2013`.
    """

    max_decomp_rate_maom: float = 24.0
    """Maximum rate for mineral associated organic matter decomposition enzyme.

    Units of [day^-1]. The rate is for a reference temperature which is given by
    :attr:`arrhenius_reference_temp`, and the corresponding activation energy is given
    by :attr:`activation_energy_maom_decomp_rate`. The value is taken from
    :cite:t:`wang_development_2013`.
    """

    activation_energy_maom_decomp_rate: float = 47000
    """Activation energy for decomposition of mineral associated organic matter.

    Units of [J K^-1]. Taken from :cite:t:`wang_development_2013`.
    """

    bacterial_turnover_rate: float = 0.005
    """Bacterial turnover rate at reference temperature [day^-1].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_microbial_turnover`.

    TODO - Source of this constant is not completely clear, investigate this further
    once fungi are added.
    """

    activation_energy_microbial_turnover = 20000
    """Activation energy for microbial maintenance turnover rate [J K^-1].

    Value taken from :cite:t:`wang_development_2013`. The bacterial turnover rate that
    this activation energy corresponds to is given by :attr:`bacterial_turnover_rate`.
    """

    fungal_turnover_rate: float = 0.005
    """Fungal turnover rate at reference temperature [day^-1].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_microbial_turnover`.

    TODO - Source of this constant is not completely clear, investigate this further
    once fungi are added.
    """

    # TODO - At some point I need to split these enzyme constants into fungi and
    # bacteria specific constants
    pom_enzyme_turnover_rate: float = 2.4e-2
    """Turnover rate for POM degrading enzymes [day^-1].

    Value taken from :cite:t:`wang_development_2013`.
    """

    maom_enzyme_turnover_rate: float = 2.4e-2
    """Turnover rate for MAOM degrading enzymes [day^-1].

    Value taken from :cite:t:`wang_development_2013`.
    """

    bacterial_maintenance_pom_enzyme: float = 1e-2
    """Fraction of bacterial maintenance used to produce POM degrading enzymes.

    [unitless]. Value taken from :cite:t:`wang_development_2013`.
    """

    fungal_maintenance_pom_enzyme: float = 1e-2
    """Fraction of fungal maintenance used to produce POM degrading enzymes.

    [unitless]. Value taken from :cite:t:`wang_development_2013`.
    """

    bacterial_maintenance_maom_enzyme: float = 1e-2
    """Fraction of bacterial maintenance used to produce MAOM degrading enzymes.

    [unitless]. Value taken from :cite:t:`wang_development_2013`.
    """

    fungal_maintenance_maom_enzyme: float = 1e-2
    """Fraction of bacterial maintenance used to produce MAOM degrading enzymes.

    [unitless]. Value taken from :cite:t:`wang_development_2013`.
    """

    # TODO - At some point, need to allow microbial and fungal environmental factors to
    # vary
    min_pH_microbes: float = 2.5
    """Soil pH below which microbial activity is completely inhibited [unitless].

    This value cannot be larger than :attr:`lowest_optimal_pH_microbes`. The default
    value was obtained by averaging the fungi and bacteria specific values given in
    :cite:t:`orwin_organic_2011`.
    """

    lowest_optimal_pH_microbes: float = 4.5
    """Soil pH above which microbial activity is not inhibited at all [unitless].

    This value cannot be smaller than :attr:`min_pH_microbes` or larger than
    :attr:`highest_optimal_pH_microbes`. The default value was obtained by averaging the
    fungi and bacteria specific values given in :cite:t:`orwin_organic_2011`.
    """

    highest_optimal_pH_microbes: float = 7.5
    """Soil pH below which microbial activity is not inhibited at all [unitless].

    This value cannot be smaller than :attr:`lowest_optimal_pH_microbes` or larger than
    :attr:`max_pH_microbes`. The default value was obtained by averaging the fungi
    and bacteria specific values given in :cite:t:`orwin_organic_2011`.
    """

    max_pH_microbes: float = 11.0
    """Soil pH above which microbial activity is completely inhibited [unitless].

    This value cannot be smaller than :attr:`highest_optimal_pH_microbes`. The default
    value was obtained by averaging the fungi and bacteria specific values given in
    :cite:t:`orwin_organic_2011`.
    """

    base_soil_protection: float = 0.694
    """Basal change in saturation constants due to soil structure [unitless]

    This value is multiplicative and is taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    soil_protection_with_clay: float = 1.36
    """Rate at which soil protection of carbon increases with clay content [unitless].

    This protection contributes multiplicatively to the effective saturation constant.
    The value of this constant is taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    solubility_coefficient_lmwc: float = 0.05
    """Solubility coefficient for low molecular weight organic carbon [unitless].

    Value taken from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite
    a loose manner.
    """

    solubility_coefficient_ammonium: float = 0.05
    """Solubility coefficient for ammonium in soil [unitless].

    Value taken from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite
    a loose manner.
    """

    solubility_coefficient_nitrate: float = 1.0
    """Solubility coefficient for nitrate in soil [unitless].

    Value taken from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite
    a loose manner.
    """

    solubility_coefficient_labile_p: float = 0.005
    """Solubility coefficient for labile inorganic phosphorus [unitless].

    Value taken from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite
    a loose manner.
    """

    necromass_decay_rate: float = (1 / 3) * np.log(2)
    """Rate at which microbial necromass decays to low molecular weight carbon [day^-1]

    I have not been able to track down any data on this, so for now choosing a rate that
    corresponds to halving every three days. This parameter is a key target for tracking
    down data for and for sensitivity analysis.
    """

    maom_desorption_rate: float = 1e-5
    """Rate constant for mineral associated organic matter desorption [day^-1]
    
    The default value of this rate is not based on data. It was instead chosen to be
    small relative to the rate at which microbes breakdown LMWC. This is another key
    target for sensitivity analysis.
    """

    lmwc_sorption_rate: float = 1e-3
    """Rate constant for low molecular weight carbon sorption to minerals [day^-1]
    
    The default value of this rate is not based on data. It was instead chosen so that
    the ratio of :term:`LMWC` to :term:`MAOM` would tend to 1/100, in the absence of
    microbes. This is another key target for sensitivity analysis.
    """

    necromass_sorption_rate: float = 1.0 * np.log(2)
    """Rate constant for necromass sorption to minerals [day^-1]
    
    The default value was chosen to be three times the value of
    :attr:`necromass_decay_rate`, this means that 75% of necromass becomes MAOM with the
    remainder becoming LMWC. Replacing this with a function that depends on
    environmental conditions is a post release goal.
    """

    litter_leaching_fraction_carbon: float = 0.0015
    """Fraction of carbon mineralisation from litter that occurs by leaching [unitless].
    
    The remainder of the mineralisation consists of particulates. Value is an order of
    magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    litter_leaching_fraction_nitrogen: float = 0.0015
    """Fraction of nitrogen mineralisation from litter that occurs by leaching.
    
    [unitless]. The remainder of the mineralisation consists of particulates. Value is
    an order of magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    litter_leaching_fraction_phosphorus: float = 0.0001
    """Fraction of phosphorus mineralisation from litter that occurs by leaching.
    
    [unitless]. The remainder of the mineralisation consists of particulates. Value is
    an order of magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    organic_proportion_litter_nitrogen_leaching: float = 1.0
    """Fraction of leached nitrogen from litter mineralisation that is organic form.
    
    [unitless]. The remainder of the leaching consists of ammonium. Value is taken from
    :cite:t:`fatichi_mechanistic_2019`, where it is assumed that nitrogen leaches from
    litter solely in organic form.
    """

    organic_proportion_litter_phosphorus_leaching: float = 1.0
    """Fraction of leached phosphorus from litter mineralisation that is organic form.
    
    [unitless]. The remainder of the leaching consists of inorganic phosphorus. Value is
    taken from :cite:t:`fatichi_mechanistic_2019`, where it is assumed that phosphorus
    leaches from litter solely in organic form.
    """

    bacterial_c_n_ratio: float = 5.2
    """Ratio of carbon to nitrogen in bacterial biomass [unitless].
    
    Estimate taken from :cite:t:`fatichi_mechanistic_2019`, which estimates this based
    on previous literature.
    """

    bacterial_c_p_ratio: float = 16
    """Ratio of carbon to phosphorus in bacterial biomass [unitless].
    
    Estimate taken from :cite:t:`fatichi_mechanistic_2019`, which estimates this based
    on previous literature.
    """

    fungal_c_n_ratio: float = 6.5
    """Ratio of carbon to nitrogen in fungal biomass [unitless].
    
    Estimate taken from :cite:t:`fatichi_mechanistic_2019`, which estimates this based
    on previous literature.
    """

    fungal_c_p_ratio: float = 40.0
    """Ratio of carbon to phosphorus in fungal biomass [unitless].
    
    Estimate taken from :cite:t:`fatichi_mechanistic_2019`, which estimates this based
    on previous literature.
    """

    ammonium_mineralisation_proportion: float = 0.9
    """Proportion of microbially mineralised nitrogen that takes the form of ammonium.
    
    [unitless]. The remainder gets mineralised as nitrate. Estimate taken from
    :cite:t:`fatichi_mechanistic_2019`, but the way it was obtained wasn't made
    particularly clear.
    """

    max_bacterial_uptake_rate_ammonium: float = 5e-3
    """Maximum possible rate for bacterial ammonium uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_bacterial_ammonium_uptake: float = 0.02275
    """Half saturation constant for bacterial uptake of ammonium [kg N m^-3].
    
    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_bacterial_uptake_rate_nitrate: float = 5e-4
    """Maximum possible rate for bacterial nitrate uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_bacterial_nitrate_uptake: float = 0.02275
    """Half saturation constant for bacterial uptake of nitrate [kg N m^-3].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_bacterial_uptake_rate_labile_p: float = 0.0025
    """Maximum possible rate for bacterial labile inorganic phosphorus uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_bacterial_labile_p_uptake: float = 0.02275
    """Half saturation constant for bacterial uptake of labile inorganic phosphorus.

    [kg P m^-3]. The reference temperature is given by :attr:`arrhenius_reference_temp`,
    and the corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_fungal_uptake_rate_ammonium = 5e-3
    """Maximum possible rate for fungal ammonium uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_fungal_ammonium_uptake: float = 0.02275
    """Half saturation constant for fungal uptake of ammonium [kg N m^-3].
    
    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_fungal_uptake_rate_nitrate = 5e-4
    """Maximum possible rate for fungal nitrate uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_fungal_nitrate_uptake: float = 0.02275
    """Half saturation constant for fungal uptake of nitrate [kg N m^-3].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_fungal_uptake_rate_labile_p: float = 0.0025
    """Maximum possible rate for fungal labile inorganic phosphorus uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_fungal_labile_p_uptake: float = 0.02275
    """Half saturation constant for fungal uptake of labile inorganic phosphorus.

    [kg P m^-3]. The reference temperature is given by :attr:`arrhenius_reference_temp`,
    and the corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    tectonic_uplift_rate_phosphorus: float = 0.0
    """Rate at which tectonic uplift exposes new primary phosphorus [kg P m^-3 day^-1].

    This rate is essentially zero for decadal simulations. We have only included to
    give the flexibility to run longer term test scenarios.
    """

    ammonia_volatilisation_rate_constant: float = 1e-9 * (24 * 60 * 60)
    """Rate constant for ammonia volatilisation from ammonium [day^-1].
    
    Following :cite:t:`dickinson_nitrogen_2002`, linear kinetics are assumed. We also
    take our default value from there.
    """

    nitrification_rate_constant: float = 1e-6 * (24 * 60 * 60)
    """Rate constant for nitrification from ammonium [day^-1].
    
    Following :cite:t:`dickinson_nitrogen_2002`, linear kinetics are assumed. We also
    take our default value from there.
    """

    denitrification_rate_constant: float = 2.5e-6 * (24 * 60 * 60)
    """Rate constant for denitrification from nitrate [day^-1].
    
    Following :cite:t:`dickinson_nitrogen_2002`, linear kinetics are assumed. We also
    take our default value from there.
    """

    nitrification_optimum_temperature: float = 311.15
    """Soil temperature at which nitrification is maximised [K].
    
    Value taken from :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied
    independently of :attr:`nitrification_maximum_temperature` and
    :attr:`nitrification_thermal_sensitivity`!
    """

    nitrification_maximum_temperature: float = 343.15
    """Temperature at which our empirical nitrification model stops working [K].
    
    This is well outside field values so this should be too much of a problem. Value
    taken from :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied
    independently of :attr:`nitrification_optimum_temperature` and
    :attr:`nitrification_thermal_sensitivity`!
    """

    nitrification_thermal_sensitivity: int = 12
    """Sensitivity of nitrification rate to changes in temperature [unitless].
    
    Value taken from :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied
    independently of :attr:`nitrification_optimum_temperature` and
    :attr:`nitrification_maximum_temperature`!
    """

    denitrification_infinite_temperature_factor: float = 93.34598
    """Denitrification temperature factor at infinite temperature.
    
    [unitless]. Value is obtained from :cite:t:`xu-ri_terrestrial_2008`, by taking the
    exponential of the constant part of the expression. This value should not be varied
    independently of :attr:`denitrification_minimum_temperature` and
    :attr:`denitrification_thermal_sensitivity`!
    """

    denitrification_minimum_temperature: float = 273.15 - 46.02
    """Temperature at which denitrification stops entirely [K].
    
    Value is obtained from :cite:t:`xu-ri_terrestrial_2008`, and converted to Kelvin.
    The expression we are using does not function below this temperature, but this is
    not a major problem as it is a very low temperature. This value should not be varied
    independently of :attr:`denitrification_infinite_temperature_factor` and
    :attr:`denitrification_thermal_sensitivity`!
    """

    denitrification_thermal_sensitivity: float = 308.56
    """Sensitivity of denitrification rate to changes in temperature [K].
    
    Value is obtained from :cite:t:`xu-ri_terrestrial_2008`. This value should not be
    varied independently of :attr:`denitrification_infinite_temperature_factor` and
    :attr:`denitrification_minimum_temperature`!
    """

    nitrogen_fixation_cost_zero_celcius: float = 59.19651970522086
    """Cost (in carbon) that plants pay to their symbiotic partners at zero Celsius.
    
    Units of [kg C kg N^-1]. This is cost per unit of nitrogen received, and will be
    higher than the symbiotic partners actually spend to fix the nitrogen. Value is
    obtained from :cite:t:`brzostek_modeling_2014`.
    """

    nitrogen_fixation_cost_infinite_temp_offset: float = -0.8034802947791453
    """Difference in nitrogen fixation cost between zero Celsius and infinite limit.
    
    Units of [kg C kg N^-1]. This limit of infinite temperature is not biologically
    meaningful and is instead just a way of characterising the form of the empirical
    function. A negative value means that the cost in the infinite temperature limit is
    higher than at zero Celsius. Value is obtained from
    :cite:t:`brzostek_modeling_2014`.
    """

    nitrogen_fixation_cost_thermal_sensitivity: float = 0.27
    """Sensitivity of symbiotic nitrogen fixation cost to changes in temperature.
    
    Units of [C^-1]. Value is obtained from :cite:t:`brzostek_modeling_2014`.
    """

    nitrogen_fixation_cost_equality_temperature: float = 50.28
    """Positive temperature at which nitrogen fixation cost is the same at zero Celsius.
    
    Units of [C]. Value is obtained from :cite:t:`brzostek_modeling_2014`.
    """

    free_living_N_fixation_reference_rate: float = 15.0 * 1e-4 / 365.25
    """Rate at which free living microbes fix nitrogen (at the reference temperature).
    
    Units of [kg N m^-2 day^-1]. Value specific to tropical forests, and is taken from
    :cite:t:`lin_modelling_2000` (with the units adjusted). Should not be changed
    independently from :attr:`free_living_N_fixation_reference_temp`.
    """

    free_living_N_fixation_reference_temp: float = 293.15
    """Temperature reference rate of free-living nitrogen fixation was measured at.

    Units of [K]. Value taken from :cite:t:`lin_modelling_2000`. Should not be changed
    independently from :attr:`free_living_N_fixation_reference_rate`.
    """

    free_living_N_fixation_q10_coefficent: float = 3.0
    """Q10 coefficient for free-living fixation of nitrogen [unitless].

    Value taken from :cite:t:`lin_modelling_2000`.
    """

    primary_phosphorus_breakdown_rate: float = 1.0 / 4.38e6
    """Rate constant for breakdown of primary phosphorus to labile phosphorus [day^-1].
    
    Default value taken from :cite:t:`parton_dynamics_1988`.
    """

    secondary_phosphorus_breakdown_rate: float = 1.0 / 13500
    """Rate constant for breakdown of secondary mineral to labile phosphorus [day^-1].
    
    Default value taken from :cite:t:`parton_dynamics_1988`.
    """

    labile_phosphorus_sorption_rate: float = 1.0 / 600
    """Rate constant for sorption of labile phosphorus to secondary mineral phosphorus.
    
    Units of [day^-1]. Default value taken from :cite:t:`parton_dynamics_1988`.
    """

    ammonium_deposition_rate: float = 1.5e-4 / 365.25
    """Rate at which ammonium is deposited into the system [kg N m^-2 day^-1].
    
    We are assuming that deposition rates won't vary substantially over the area the
    simulation encompasses. Value taken from :cite:t:`vet_global_2014`.
    """

    phosphorus_deposition_rate: float = 5e-6 / 365.25
    """Rate at which phosphorus is deposited into the system [kg P m^-2 day^-1].
    
    We are assuming that deposition rates won't vary substantially over the area the
    simulation encompasses. Value taken from :cite:t:`Mahowald2008`.
    """
