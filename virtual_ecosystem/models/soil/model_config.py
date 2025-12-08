"""Configuration classes for the soil model."""

from __future__ import annotations

from itertools import product
from typing import ClassVar, Literal, get_args

import numpy as np
from pydantic import Field, field_validator, model_validator

from virtual_ecosystem.core.configuration import Configuration, ModelConfigurationRoot

REQUIRED_MICROBIAL_GROUPS = Literal[
    "saprotrophic_fungi",
    "ectomycorrhiza",
    "arbuscular_mycorrhiza",
    "bacteria",
]
"""Required taxonomic groups in the soil model"""

HIGHER_TAXONOMIC_GROUPS = Literal["fungi", "bacteria"]
"""Permitted higher taxonomic group names in the soil model."""

SUBSTRATES = Literal["pom", "maom"]
"""Permitted substrate types in the soil model"""


REQUIRED_ENZYMES: set[tuple[HIGHER_TAXONOMIC_GROUPS, SUBSTRATES]] = set(
    product(get_args(HIGHER_TAXONOMIC_GROUPS), get_args(SUBSTRATES))
)
"""Required enzyme classes as all pairs of higher taxon source and substrate."""


class SoilConstants(Configuration):
    """Dataclass to store all constants for the `soil` model."""

    reference_cue_logit: float = 0.094
    """Logit of carbon use efficiency of microbial community at reference temperature
    [unitless]. Parameter estimated from a beta-logit GLMM using the data from
    :cite:t:`Qiao2019`."""

    cue_reference_temp: float = 20.0
    """Reference temperature for carbon use efficiency [°C]. Default value taken from
    :cite:t:`Qiao2019`."""

    logit_cue_with_temperature: float = -0.039
    """Change in the logit of carbon use efficiency with unit increase in temperature
    [°C^-1]. Parameter estimated from a beta-logit GLMM using the data from 
    :cite:t:`Qiao2019`."""

    soil_microbe_water_potential_optimum: float = -3.0
    """The water potential at which soil microbial rates are maximised [kPa]. Value is
    taken from :cite:t:`moyano_responses_2013`."""

    soil_microbe_water_potential_halt: float = -15800.0
    """The water potential at which soil microbial activity stops entirely [kPa]. Value
    is taken from :cite:t:`moyano_responses_2013`."""

    microbial_water_response_curvature: float = 1.47
    """Curvature of function for response of soil microbial rates to water potential
    [unitless]. Value is taken from :cite:t:`moyano_responses_2013`."""

    # TODO - At some point, need to allow microbial and fungal environmental factors to
    # vary
    min_pH_microbes: float = 2.5
    """Soil pH below which microbial activity is completely inhibited [unitless]. This
    value cannot be larger than :attr:`SoilConstants.lowest_optimal_pH_microbes`. The
    default value was obtained by averaging the fungi and bacteria specific values given
    in :cite:t:`orwin_organic_2011`."""

    lowest_optimal_pH_microbes: float = 4.5
    """Soil pH above which microbial activity is not inhibited at all [unitless]. This
    value cannot be smaller than :attr:`SoilConstants.min_pH_microbes` or larger than
    :attr:`SoilConstants.highest_optimal_pH_microbes`. The default value was obtained by
    averaging the fungi and bacteria specific values given in
    :cite:t:`orwin_organic_2011`."""

    highest_optimal_pH_microbes: float = 7.5
    """Soil pH below which microbial activity is not inhibited at all [unitless]. This
    value cannot be smaller than :attr:`SoilConstants.lowest_optimal_pH_microbes` or
    larger than :attr:`SoilConstants.max_pH_microbes`. The default value was obtained by
    averaging the fungi and bacteria specific values given in
    :cite:t:`orwin_organic_2011`."""

    max_pH_microbes: float = 11.0
    """Soil pH above which microbial activity is completely inhibited [unitless]. This
    value cannot be smaller than :attr:`SoilConstants.highest_optimal_pH_microbes`. The
    default value was obtained by averaging the fungi and bacteria specific values given
    in :cite:t:`orwin_organic_2011`."""

    base_soil_protection: float = 0.694
    """Basal change in saturation constants due to soil structure [unitless]. This value
    is multiplicative and is taken from :cite:t:`fatichi_mechanistic_2019`."""

    soil_protection_with_clay: float = 1.36
    """Rate at which soil protection of carbon increases with clay content [unitless].
    This protection contributes multiplicatively to the effective saturation constant. 
    The value of this constant is taken from :cite:t:`fatichi_mechanistic_2019`.
    """

    solubility_coefficient_lmwc: float = 0.05
    """Solubility coefficient for low molecular weight organic carbon [unitless]. Value
    taken from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite a
    loose manner. 
    """

    solubility_coefficient_ammonium: float = 0.05
    """Solubility coefficient for ammonium in soil [unitless]. Value taken from
    :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite a loose manner.
    """

    solubility_coefficient_nitrate: float = 1.0
    """Solubility coefficient for nitrate in soil [unitless]. Value taken from
    :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite a loose manner.
    """

    solubility_coefficient_labile_p: float = 0.005
    """Solubility coefficient for labile inorganic phosphorus [unitless]. Value taken
    from :cite:t:`fatichi_mechanistic_2019`, where it is estimated in quite a loose
    manner."""

    necromass_decay_rate: float = (1 / 3) * np.log(2)
    """Rate at which microbial necromass decays to low molecular weight carbon [day^-1].
    I have not been able to track down any data on this, so for now choosing a rate that
    corresponds to halving every three days. This parameter is a key target for tracking
    down data for and for sensitivity analysis."""

    maom_desorption_rate: float = 1e-5
    """Rate constant for mineral associated organic matter desorption [day^-1]. The
    default value of this rate is not based on data. It was instead chosen to be 
    small relative to the rate at which microbes breakdown LMWC. This is another key
    target for sensitivity analysis."""

    lmwc_sorption_rate: float = 1e-3
    """Rate constant for low molecular weight carbon sorption to minerals [day^-1]. The
    default value of this rate is not based on data. It was instead chosen so that 
    the ratio of :term:`LMWC` to :term:`MAOM` would tend to 1/100, in the absence of
    microbes. This is another key target for sensitivity analysis."""

    necromass_sorption_rate: float = 1.0 * np.log(2)
    """Rate constant for necromass sorption to minerals [day^-1]. The default value was
    chosen to be three times the value of :attr:`SoilConstants.necromass_decay_rate`,
    this means that 75% of necromass becomes MAOM with the remainder becoming LMWC.
    Replacing this with a function that depends on environmental conditions is a post
    release goal."""

    litter_leaching_fraction_carbon: float = 0.0015
    """Fraction of carbon mineralisation from litter that occurs by leaching [unitless].
    The remainder of the mineralisation consists of particulates. Value is an order of
    magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`."""

    litter_leaching_fraction_nitrogen: float = 0.0015
    """Fraction of nitrogen mineralisation from litter that occurs by leaching.
    [unitless]. The remainder of the mineralisation consists of particulates. Value is
    an order of magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`."""

    litter_leaching_fraction_phosphorus: float = 0.0001
    """Fraction of phosphorus mineralisation from litter that occurs by leaching.
    [unitless]. The remainder of the mineralisation consists of particulates. Value is
    an order of magnitude estimate taken from :cite:t:`fatichi_mechanistic_2019`."""

    organic_proportion_litter_nitrogen_leaching: float = 1.0
    """Fraction of leached nitrogen from litter mineralisation that is organic form.
    [unitless]. The remainder of the leaching consists of ammonium. Value is taken from
    :cite:t:`fatichi_mechanistic_2019`, where it is assumed that nitrogen leaches from
    litter solely in organic form."""

    organic_proportion_litter_phosphorus_leaching: float = 1.0
    """Fraction of leached phosphorus from litter mineralisation that is organic form.
    [unitless]. The remainder of the leaching consists of inorganic phosphorus. Value is
    taken from :cite:t:`fatichi_mechanistic_2019`, where it is assumed that phosphorus
    leaches from litter solely in organic form."""

    ammonium_mineralisation_proportion: float = 0.9
    """Proportion of microbially mineralised nitrogen that takes the form of ammonium.
    [unitless]. The remainder gets mineralised as nitrate. Estimate taken from
    :cite:t:`fatichi_mechanistic_2019`, but the way it was obtained wasn't made
    particularly clear."""

    tectonic_uplift_rate_phosphorus: float = 0.0
    """Rate at which tectonic uplift exposes new primary phosphorus [kg P m^-3 day^-1].
    This rate is essentially zero for decadal simulations. We have only included to
    give the flexibility to run longer term test scenarios."""

    ammonia_volatilisation_rate_constant: float = 1e-9 * (24 * 60 * 60)
    """Rate constant for ammonia volatilisation from ammonium [day^-1]. Following
    :cite:t:`dickinson_nitrogen_2002`, linear kinetics are assumed. We also take our
    default value from there."""

    nitrification_rate_constant: float = 1e-6 * (24 * 60 * 60)
    """Rate constant for nitrification from ammonium [day^-1]. Following
    :cite:t:`dickinson_nitrogen_2002`, linear kinetics are assumed. We also take our
    default value from there."""

    denitrification_rate_constant: float = 2.5e-6 * (24 * 60 * 60)
    """Rate constant for denitrification from nitrate [day^-1]. Following
    :cite:t:`dickinson_nitrogen_2002`, linear kinetics are assumed. We also take our
    default value from there."""

    nitrification_optimum_temperature: float = 311.15
    """Soil temperature at which nitrification is maximised [K]. Value taken from
    :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied independently of
    :attr:`SoilConstants.nitrification_maximum_temperature` and
    :attr:`SoilConstants.nitrification_thermal_sensitivity`!"""

    nitrification_maximum_temperature: float = 343.15
    """Temperature at which our empirical nitrification model stops working [K].
    This is well outside field values so this should be too much of a problem. Value
    taken from :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied
    independently of :attr:`SoilConstants.nitrification_optimum_temperature` and
    :attr:`SoilConstants.nitrification_thermal_sensitivity`!"""

    nitrification_thermal_sensitivity: int = 12
    """Sensitivity of nitrification rate to changes in temperature [unitless]. Value
    taken from :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied 
    independently of :attr:`SoilConstants.nitrification_optimum_temperature` and
    :attr:`SoilConstants.nitrification_maximum_temperature`!"""

    denitrification_infinite_temperature_factor: float = 93.34598
    """Denitrification temperature factor at infinite temperature [unitless]. Value is
    obtained from :cite:t:`xu-ri_terrestrial_2008`, by taking the exponential of the
    constant part of the expression. This value should not be varied independently of
    :attr:`SoilConstants.denitrification_minimum_temperature` and
    :attr:`SoilConstants.denitrification_thermal_sensitivity`!"""

    denitrification_minimum_temperature: float = 273.15 - 46.02
    """Temperature at which denitrification stops entirely [K]. Value is obtained from
    :cite:t:`xu-ri_terrestrial_2008`, and converted to Kelvin. The expression we are
    using does not function below this temperature, but this is not a major problem as
    it is a very low temperature. This value should not be varied independently of
    :attr:`SoilConstants.denitrification_infinite_temperature_factor` and
    :attr:`SoilConstants.denitrification_thermal_sensitivity`!"""

    denitrification_thermal_sensitivity: float = 308.56
    """Sensitivity of denitrification rate to changes in temperature [K]. Value is
    obtained from :cite:t:`xu-ri_terrestrial_2008`. This value should not be varied
    independently of :attr:`SoilConstants.denitrification_infinite_temperature_factor`
    and :attr:`SoilConstants.denitrification_minimum_temperature`!"""

    nitrogen_fixation_cost_zero_celcius: float = 59.19651970522086
    """Cost (in carbon) that plants pay to their symbiotic partners at zero Celsius [kg
    C kg N^-1]. This is cost per unit of nitrogen received, and will be higher than the
    symbiotic partners actually spend to fix the nitrogen. Value is obtained from
    :cite:t:`brzostek_modeling_2014`. 
    """

    nitrogen_fixation_cost_infinite_temp_offset: float = -0.8034802947791453
    """Difference in nitrogen fixation cost between zero Celsius and infinite limit.
    Units of [kg C kg N^-1]. This limit of infinite temperature is not biologically
    meaningful and is instead just a way of characterising the form of the empirical
    function. A negative value means that the cost in the infinite temperature limit is
    higher than at zero Celsius. Value is obtained from
    :cite:t:`brzostek_modeling_2014`."""

    nitrogen_fixation_cost_thermal_sensitivity: float = 0.27
    """Sensitivity of symbiotic nitrogen fixation cost to changes in temperature
    [°C^-1]. Value is obtained from :cite:t:`brzostek_modeling_2014`."""

    nitrogen_fixation_cost_equality_temperature: float = 50.28
    """Positive temperature at which nitrogen fixation cost is the same at zero Celsius.
    [°C]. Value is obtained from :cite:t:`brzostek_modeling_2014`."""

    free_living_N_fixation_reference_rate: float = 15.0 * 1e-4 / 365.25
    """Rate at which free living microbes fix nitrogen (at the reference temperature).
    Units of [kg N m^-2 day^-1]. Value specific to tropical forests, and is taken from
    :cite:t:`lin_modelling_2000` (with the units adjusted). Should not be changed
    independently from :attr:`SoilConstants.free_living_N_fixation_reference_temp`."""

    free_living_N_fixation_reference_temp: float = 293.15
    """Temperature reference rate of free-living nitrogen fixation was measured at [K].
    Value taken from :cite:t:`lin_modelling_2000`. Should not be changed independently
    from :attr:`SoilConstants.free_living_N_fixation_reference_rate`.
    """

    free_living_N_fixation_q10_coefficent: float = 3.0
    """Q10 coefficient for free-living fixation of nitrogen [unitless]. Value taken from
    :cite:t:`lin_modelling_2000`. """

    primary_phosphorus_breakdown_rate: float = 1.0 / 4.38e6
    """Rate constant for breakdown of primary phosphorus to labile phosphorus [day^-1].
    Default value taken from :cite:t:`parton_dynamics_1988`."""

    secondary_phosphorus_breakdown_rate: float = 1.0 / 13500
    """Rate constant for breakdown of secondary mineral to labile phosphorus [day^-1].
    Default value taken from :cite:t:`parton_dynamics_1988`."""

    labile_phosphorus_sorption_rate: float = 1.0 / 600
    """Rate constant for sorption of labile phosphorus to secondary mineral phosphorus
    [day^-1]. Default value taken from :cite:t:`parton_dynamics_1988`. """

    ammonium_deposition_rate: float = 1.5e-4 / 365.25
    """Rate at which ammonium is deposited into the system [kg N m^-2 day^-1]. We are
    assuming that deposition rates won't vary substantially over the area the 
    simulation encompasses. Value taken from :cite:t:`vet_global_2014`."""

    phosphorus_deposition_rate: float = 5e-6 / 365.25
    """Rate at which phosphorus is deposited into the system [kg P m^-2 day^-1].
    We are assuming that deposition rates won't vary substantially over the area the
    simulation encompasses. Value taken from :cite:t:`Mahowald2008`."""

    nitrogen_fixer_supply_fraction: float = 0.3
    """Fraction of carbon supplied by plants to symbiotes that goes to nitrogen fixers.
    [unitless]. The remainder goes to mycorrhizal fungi."""

    ectomycorrhiza_supply_fraction: float = 0.25
    """Fraction of plant carbon supply to mycorrhizal fungi that goes to ectomycorrhiza.
    [unitless]. The remainder goes to arbuscular mycorrhizal fungi."""

    @model_validator(mode="after")
    def _check_pH_sequence(self) -> SoilConstants:
        """Checks that the microbe pH thresholds are in the correct order."""
        if not (
            self.min_pH_microbes
            < self.lowest_optimal_pH_microbes
            < self.highest_optimal_pH_microbes
            < self.max_pH_microbes
        ):
            raise ValueError("Microbe pH thresholds not in increasing sequence")

        return self


class SoilEnzymeClass(Configuration):
    """Soil enzyme constants."""

    source: HIGHER_TAXONOMIC_GROUPS = Field(default="bacteria")
    """The higher microbial group which produces the enzyme."""
    substrate: SUBSTRATES = Field(default="pom")
    """The substrate which the enzyme acts upon."""
    maximum_rate: float = Field(default=60.0)
    """The maximum rate of the enzyme at the reference temperature [day^-1]."""
    half_saturation_constant: float = Field(default=70.0)
    """The half saturation constant for the enzyme at the reference temperature. Units
    of [kg C m^-3]."""
    activation_energy_rate: float = Field(default=37000)
    """Activation energy for enzyme rate with temperature [J K^-1]."""
    activation_energy_saturation: float = Field(default=30000)
    """Activation energy for enzyme saturation with temperature [J K^-1]."""
    # TODO - This should change to Kelvin when we change the default units to Kelvin
    reference_temperature: float = Field(default=12.0)
    """The temperature that enzyme rate and saturation were measured at [°C]."""
    turnover_rate: float = Field(default=0.024)
    """The turnover rate of the enzyme [day^-1]."""
    c_n_ratio: float = Field(default=5.2)
    """Ratio of carbon to nitrogen for the enzyme [unitless]."""
    c_p_ratio: float = Field(default=16)
    """Ratio of carbon to phosphorus for the enzyme [unitless]."""


class SoilMicrobialGroup(Configuration):
    """Microbial functional group definitions."""

    name: REQUIRED_MICROBIAL_GROUPS = Field(default="bacteria")
    """The name of the microbial group functional type."""
    taxonomic_group: HIGHER_TAXONOMIC_GROUPS = Field(default="bacteria")
    """The high level taxonomic group that the microbial group belongs to."""
    max_uptake_rate_labile_C: float = Field(default=0.04)
    """Maximum rate at the reference temperature of labile carbon uptake [day^-1]."""
    activation_energy_uptake_rate: float = Field(default=47000)
    """Activation energy for nutrient uptake [J K^-1]."""
    half_sat_labile_C_uptake: float = Field(default=0.364)
    """Half saturation constant for uptake of labile carbon (LMWC) [kg C m^-3]."""
    activation_energy_uptake_saturation: float = Field(default=30000)
    """Activation energy for nutrient uptake saturation constants [J K^-1]."""
    max_uptake_rate_ammonium: float = Field(default=0.005)
    """Maximum possible rate for ammonium uptake [day^-1]."""
    half_sat_ammonium_uptake: float = Field(default=0.02275)
    """Half saturation constant for uptake of ammonium [kg N m^-3]."""
    max_uptake_rate_nitrate: float = Field(default=0.0005)
    """Maximum possible rate for nitrate uptake [day^-1]."""
    half_sat_nitrate_uptake: float = Field(default=0.02275)
    """Half saturation constant for uptake of nitrate [kg N m^-3]."""
    max_uptake_rate_labile_p: float = Field(default=0.0025)
    """Maximum possible rate for labile inorganic phosphorus uptake [day^-1]."""
    half_sat_labile_p_uptake: float = Field(default=0.02275)
    """Half saturation constant for uptake of labile inorganic phosphorus [kg P m^-3].
    """
    turnover_rate: float = Field(default=0.005)
    """Microbial maintenance turnover rate at reference temperature [day^-1]."""
    activation_energy_turnover: float = Field(default=20000)
    """Activation energy for microbial maintenance turnover rate [J K^-1]."""
    reference_temperature: float = Field(default=12.0)
    """The temperature that turnover and uptake rates were measured at [°C]."""
    c_n_ratio: float = Field(default=5.2)
    """Ratio of carbon to nitrogen in biomass [unitless]."""
    c_p_ratio: float = Field(default=16)
    """Ratio of carbon to phosphorus in biomass [unitless]."""
    enzyme_production: dict[str, float] = Field(default={"pom": 0.005, "maom": 0.005})
    """Details of the enzymes produced by the microbial group. The keys are the
    substrates for which enzymes are produced, and the values are the allocation to
    enzyme production. This allocation is expressed as a fraction of the (gross)
    cellular biomass growth.
    """
    reproductive_allocation: float = Field(default=0.0)
    """Reproductive allocation as fraction of (gross) cellular biomass growth [unitless]
    Only fungi generate separate reproductive bodies, so this value **must** be set to
    zero for bacterial functional groups. Providing a non-zero value for a bacterial
    functional group will prevent the soil model from configuring.
    """

    @model_validator(mode="after")
    def _only_fungi_fruit(self) -> SoilMicrobialGroup:
        if self.taxonomic_group != "fungi" and self.reproductive_allocation > 0:
            raise ValueError(
                "Reproductive allocation for non fungal groups must be zero."
            )

        return self


class SoilConfiguration(ModelConfigurationRoot):
    """Root configuration class for the soil model."""

    enzyme_class_definition_path: str = ""
    """Path to a CSV file of microbial enzyme class definitions. Not yet implemented."""

    microbial_group_definition_path: str = ""
    """Path to a CSV file of microbial functional group definitions. Not yet
    implemented."""

    constants: SoilConstants = SoilConstants()
    """Constants values for soil model."""

    enzyme_class_definition: list[SoilEnzymeClass] = Field(
        default=[
            SoilEnzymeClass(source="fungi", substrate="pom"),
            SoilEnzymeClass(source="fungi", substrate="maom"),
            SoilEnzymeClass(source="bacteria", substrate="pom"),
            SoilEnzymeClass(source="bacteria", substrate="maom"),
        ]
    )
    """Definition of enzyme classes for soil model."""

    microbial_group_definition: list[SoilMicrobialGroup] = Field(
        default=[
            SoilMicrobialGroup(name="saprotrophic_fungi"),
            SoilMicrobialGroup(name="ectomycorrhiza"),
            SoilMicrobialGroup(name="arbuscular_mycorrhiza"),
            SoilMicrobialGroup(name="bacteria"),
        ]
    )
    """Definition of microbial groups for soil model."""

    _required_enzymes: ClassVar[set[tuple[HIGHER_TAXONOMIC_GROUPS, SUBSTRATES]]] = (
        REQUIRED_ENZYMES
    )
    """Required enzyme classes, provided as all pairs of higher taxon source and
    substrates."""

    _required_microbial_groups: ClassVar[set[REQUIRED_MICROBIAL_GROUPS]] = {
        *get_args(REQUIRED_MICROBIAL_GROUPS)
    }
    """Required named microbial groups."""

    @field_validator("enzyme_class_definition")
    def _enforce_required_enzymes(
        cls, enzymes: list[SoilEnzymeClass]
    ) -> list[SoilEnzymeClass]:
        """Validates the provided sets of enzyme classes."""
        provided_enzymes = {(e.source, e.substrate) for e in enzymes}

        if not provided_enzymes == cls._required_enzymes:
            raise ValueError(
                f"The source/substrate pairs provided in enzyme class definitions "
                f"({provided_enzymes!r}) do not match the required set of pairs "
                f"({cls._required_enzymes!r})"
            )

        return enzymes

    @field_validator("microbial_group_definition")
    def _enforce_required_microbial_groups(
        cls, microbial_groups: list[SoilMicrobialGroup]
    ) -> list[SoilMicrobialGroup]:
        """Validates the provided sets of enzyme classes."""
        provided_groups = {g.name for g in microbial_groups}

        if not provided_groups == cls._required_microbial_groups:
            raise ValueError(
                f"The microbial group definitions ({provided_groups!r}) does not match "
                f"the required set ({cls._required_microbial_groups!r})"
            )

        return microbial_groups
