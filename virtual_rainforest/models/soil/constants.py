"""The ``models.soil.constants`` module contains a set of dataclasses containing
constants (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_ecosystem.models.soil` module
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass

# TODO - Once lignin is tracked a large number of constants will have to be duplicated


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

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    soil_microbe_water_potential_halt: float = -15800.0
    """The water potential at which soil microbial activity stops entirely [kPa].

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    microbial_water_response_curvature: float = 1.47
    """Curvature of function for response of soil microbial rates to water potential.

    [unitless]. Value is taken from :cite:t`moyano_responses_2013`.
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
    """Activation energy for microbial uptake of low molecular weight carbon [J K^-1].

    Value taken from :cite:t:`wang_development_2013`. The maximum labile carbon uptake
    rate that this activation energy corresponds to is given by
    :attr:`max_uptake_rate_labile_C`.
    """

    half_sat_labile_C_uptake: float = 0.364
    """Half saturation constant for microbial uptake of labile carbon (LMWC).

    [kg C m^-3]. This was calculated from the value provided in
    :cite:t:`wang_development_2013` assuming an average bulk density of 1400 [kg m^-3].
    The reference temperature is given by :attr:`arrhenius_reference_temp`, and the
    corresponding activation energy is given by
    :attr:`activation_energy_labile_C_saturation`.
    """

    activation_energy_labile_C_saturation: float = 30000
    """Activation energy for labile C uptake saturation constant [J K^-1].

    Taken from :cite:t:`wang_development_2013`.
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

    necromass_to_lmwc: float = 0.25
    """Proportion of necromass that flows to LMWC rather than POM [unitless].

    Value taken from :cite:t:`wang_development_2013`.
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

    clay_necromass_decay_exponent: float = -0.8
    """Change in proportion of necromass which decays with increasing soil clay content.

    [unitless]. The function this is used in is an exponential, and the sign should be
    negative so increases in clay leads to a lower proportion of necromass decaying to
    LMWC. The value of this constant is taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    pom_decomposition_fraction_lmwc: float = 0.5
    """Fraction of decomposed POM that becomes LMWC rather than MAOM [unitless].

    Value taken from :cite:t:`wang_development_2013`.
    """

    solubility_coefficient_lmwc: float = 0.05
    """Solubility coefficient for low molecular weight organic carbon [unitless].

    Value taken from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite
    a loose manner.
    """
