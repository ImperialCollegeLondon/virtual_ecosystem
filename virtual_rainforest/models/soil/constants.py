"""The ``models.soil.constants`` module contains a set of dataclasses containing
constants (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.soil` module
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass

# TODO - Need to figure out a sensible area to volume conversion


@dataclass(frozen=True)
class SoilConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `soil` model.

    All constants are taken from :cite:t:`abramoff_millennial_2018` unless otherwise
    stated.
    """

    binding_with_ph_slope: float = -0.186
    """Change in the binding affinity of soil mineral with pH.

    Units of [pH^-1]. From linear regression :cite:p:`mayes_relation_2012`."""

    binding_with_ph_intercept: float = -0.216 + 3.0
    """Binding affinity of soil minerals at zero pH.

    Unit of [log(m^3 kg^-1)]. n.b. +3 converts from mg^-1 to kg^-1 and L to m^3. From
    linear regression :cite:p:`mayes_relation_2012`.
    """

    max_sorption_with_clay_slope: float = 0.483
    """Change in the maximum size of the MAOM pool with increasing clay content.

    Units of [(% clay)^-1]. From linear regression :cite:p:`mayes_relation_2012`.
    """

    max_sorption_with_clay_intercept: float = 2.328 - 6.0
    """Maximum size of the MAOM pool at zero clay content.

    Unit of [log(kg C kg soil ^-1)]. n.b. -6 converts from mg to kg. From linear
    regression :cite:p:`mayes_relation_2012`.
    """

    moisture_scalar_coefficient: float = 30.0
    """Used in :cite:t:`abramoff_millennial_2018`, can't find original source.

    Value at zero relative water content (RWC) [unit less].
    """

    moisture_scalar_exponent: float = 9.0
    """Used in :cite:t:`abramoff_millennial_2018`, can't find original source.

    Units of [(RWC)^-1]
    """

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

    necromass_adsorption_rate: float = 0.025
    """Rate at which necromass is adsorbed by soil minerals [day^-1].

    Taken from :cite:t:`abramoff_millennial_2018`, where it was obtained by calibration.
    """

    half_sat_microbial_activity: float = 0.0072
    """Half saturation constant for microbial activity (with increasing biomass).

    Units of [kg C m^-2].
    """

    leaching_rate_labile_carbon: float = 1.5e-3
    """Leaching rate for labile carbon (lmwc) [day^-1]."""

    soil_microbe_water_potential_optimum: float = -3.0
    """The water potential at which soil microbial rates are maximised [kPa].

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    soil_microbe_water_potential_halt: float = -15800.0
    """The water potential at which soil microbial activity stops entirely [kPa].

    Value is taken from :cite:t`moyano_responses_2013`.
    """

    moisture_response_curvature: float = 1.47
    """Curvature of the soil microbial moisture response function [unitless].

    Value is taken from :cite:t`moyano_responses_2013`.
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

    # TODO - Add another set of constants once we start tracking lignin
    half_sat_pom_decomposition: float = 70.0
    """Half saturation constant for POM decomposition to LMWC [kg C m^-2].

    This was calculated from the value provided in :cite:t:`wang_development_2013`
    assuming an average bulk density of 1400 [kg m^-3]. The reference temperature is
    given by :attr:`arrhenius_reference_temp`, and the corresponding activation energy
    is given by :attr:`activation_energy_pom_decomp_saturation`.
    """

    activation_energy_pom_decomp_saturation: float = 30000
    """Activation energy for decomposition of particulate organic matter [J K^-1].

    Taken from :cite:t:`wang_development_2013`.
    """

    # TODO - Add another set of constants once we start tracking lignin
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

    necromass_to_pom: float = 0.5
    """Proportion of necromass that flows to POM rather than LMWC [unitless].

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
