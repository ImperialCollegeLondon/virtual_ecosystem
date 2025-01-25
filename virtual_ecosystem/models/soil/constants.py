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

    # TODO - Split this and the following into 2 constants once fungi are introduced
    max_uptake_rate_labile_C: float = 0.04
    """Maximum rate at the reference temperature of labile carbon uptake [day^-1].

    The reference temperature is given
    by :attr:`arrhenius_reference_temp`, and the corresponding activation energy is
    given by :attr:`activation_energy_microbial_uptake`.

    TODO - Source of this constant is not completely clear, investigate this further
    once fungi are added.
    """

    activation_energy_microbial_uptake: float = 47000
    """Activation energy for microbial nutrient uptake [J K^-1].

    Value taken from :cite:t:`wang_development_2013`. The maximum labile carbon uptake
    rate that this activation energy corresponds to is given by
    :attr:`max_uptake_rate_labile_C`. This activation energy is assumed to be the same
    for the uptake of other nutrients as for carbon.
    """

    half_sat_labile_C_uptake: float = 0.364
    """Half saturation constant for microbial uptake of labile carbon (LMWC).

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

    # TODO - Split this and the following into 2 constants once fungi are introduced
    microbial_turnover_rate: float = 0.005
    """Microbial turnover rate at reference temperature [day^-1].

    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_microbial_turnover`.

    TODO - Source of this constant is not completely clear, investigate this further
    once fungi are added.
    """

    activation_energy_microbial_turnover = 20000
    """Activation energy for microbial maintenance turnover rate [J K^-1].

    Value taken from :cite:t:`wang_development_2013`. The microbial turnover rate that
    this activation energy corresponds to is given by :attr:`microbial_turnover_rate`.
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

    maintenance_pom_enzyme: float = 1e-2
    """Fraction of maintenance synthesis used to produce POM degrading enzymes.

    [unitless]. Value taken from :cite:t:`wang_development_2013`.
    """

    maintenance_maom_enzyme: float = 1e-2
    """Fraction of maintenance synthesis used to produce MAOM degrading enzymes.

    [unitless]. Value taken from :cite:t:`wang_development_2013`.
    """

    # TODO - The 4 constants below should take different values for fungi and bacteria,
    # once that separation is implemented.
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
    the ratio of LWMC to mineral associated organic matter would tend to 1/100, in the
    absence of microbes. This is another key target for sensitivity analysis.
    """

    necromass_sorption_rate: float = 1.0 * np.log(2)
    """Rate constant for necromass sorption to minerals [day^-1]
    
    The default value was chosen to be three times the value of
    :attr:`necromass_decay_rate`, this means that 75% of necromass becomes MAOM with the
    remainder becoming LMWC. Replacing this with a function that depends on
    environmental conditions is a post release goal.
    """

    litter_leaching_fraction_carbon = 0.0015
    """Fraction of carbon mineralisation from litter that occurs by leaching [unitless].
    
    The remainder of the mineralisation consists of particulates. Value is an order of
    magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    litter_leaching_fraction_nitrogen = 0.0015
    """Fraction of nitrogen mineralisation from litter that occurs by leaching.
    
    [unitless]. The remainder of the mineralisation consists of particulates. Value is
    an order of magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    litter_leaching_fraction_phosphorus = 0.0001
    """Fraction of phosphorus mineralisation from litter that occurs by leaching.
    
    [unitless]. The remainder of the mineralisation consists of particulates. Value is
    an order of magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    organic_proportion_litter_phosphorus_leaching = 1.0
    """Fraction of leached phosphrous from litter mineralisation that is organic form.
    
    [unitless]. The remainder of the leaching consists of inorganic phosphorus. Value is
    taken from :cite:t:`fatichi_mechanistic_2019`, where it is assumed that phosphorus
    leaches from litter solely in organic form.
    """

    microbial_c_n_ratio = 5.2
    """Ratio of carbon to nitrogen in microbial biomass [unitless].
    
    Estimate taken from :cite:t:`fatichi_mechanistic_2019`, which estimates this based
    on previous literature. Here using specifically the bacterial value, once fungi are 
    added this constant needs to be split.
    """

    microbial_c_p_ratio = 16
    """Ratio of carbon to phosphorus in microbial biomass [unitless].
    
    Estimate taken from :cite:t:`fatichi_mechanistic_2019`, which estimates this based
    on previous literature. Here using specifically the bacterial value, once fungi are 
    added this constant needs to be split.
    """

    max_uptake_rate_don = 0.0077
    """Maximum possible rate for dissolved organic nitrogen uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_don_uptake: float = 0.07
    """Half saturation constant for uptake of dissolved organic nitrogen (DON).

    [kg N m^-3]. The reference temperature is given by :attr:`arrhenius_reference_temp`,
    and the corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_uptake_rate_dop = 0.0025
    """Maximum possible rate for dissolved organic phosphorus uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_dop_uptake: float = 0.02275
    """Half saturation constant for uptake of dissolved organic phosphorus (DOP).

    [kg P m^-3]. The reference temperature is given by :attr:`arrhenius_reference_temp`,
    and the corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    max_uptake_rate_labile_p = 0.0025
    """Maximum possible rate for labile inorganic phosphorus uptake [day^-1].

    This rate corresponds to the reference temperature given by
    :attr:`arrhenius_reference_temp`, with the corresponding activation energy given by
    :attr:`activation_energy_microbial_uptake`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    half_sat_labile_p_uptake: float = 0.02275
    """Half saturation constant for uptake of labile inorganic phosphorus.

    [kg P m^-3]. The reference temperature is given by :attr:`arrhenius_reference_temp`,
    and the corresponding activation energy is given by
    :attr:`activation_energy_uptake_saturation`.

    TODO - At present I've invented the value for this constant, so it really needs to
    be better pinned down.
    """

    tectonic_uplift_rate_phosphorus: float = 0.0
    """Rate at which tectonic uplift exposes new primary phosphorus [kg P m^-3 day^-1].

    This rate is essientially zero for decadal simulations. We have only included to
    give the flexibility to run longer term test scenarios.
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

    phosphorus_deposition_rate: float = 5e-6 / 365.25
    """Rate at which phosphorus is deposited into the system [kg P m^-2 day^-1].
    
    We are assuming that deposistion rates won't vary substantially over the area the
    simulation encompasses. Value taken from :cite:t:`Mahowald2008`.
    """
