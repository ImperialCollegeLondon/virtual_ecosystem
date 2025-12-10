"""Configuration for the plants model."""

from typing import Literal

from virtual_ecosystem.core.configuration import (
    FILEPATH_PLACEHOLDER,
    Configuration,
    ModelConfigurationRoot,
)


class PlantsConstants(Configuration):
    """Constants for the :mod:`~virtual_ecosystem.models.plants` model.

    .. TODO::
        The subcanopy seedbank and vegetation constants have the same structure. This is
        probably worth bringing together into a dataclass and external file,
        particularly as and when we add shrub or liana layers, which likely mirror this.

    """

    per_stem_annual_mortality_probability: float = 0.1
    """Basic annual mortality rate for plants."""

    per_propagule_annual_recruitment_probability: float = 0.2
    """Basic annual recruitment rate from plant propagules."""

    dsr_to_ppfd: float = 2.04
    """Convert from downward shortwave radiation to photosynthetic photon flux density.

    Converting DSR in W m-2 to PPFD in µmol m-2 s-1. 1 W m-2 of sunlight is roughly 4.57
    µmol m-2 s-1 of full spectrum sunlight, of which about 4.57 * 46% = 2.04  µmol m-2
    s-1 is PPFD.
    """

    stem_lignin: float = 0.545
    """Fraction of stem biomass that is lignin."""

    senesced_leaf_lignin: float = 0.05
    """Fraction of senesced leaf biomass that is lignin."""

    leaf_lignin: float = 0.10
    """Fraction of leaf biomass that is lignin."""

    plant_reproductive_tissue_lignin: float = 0.01
    """Fraction of plant reproductive tissue biomass that is lignin."""

    root_lignin: float = 0.20
    """Fraction of root biomass that is lignin."""

    subcanopy_extinction_coef: float = 0.5
    """The extinction coefficient of subcanopy vegetation (unitless)."""

    subcanopy_specific_leaf_area: float = 14
    """The specific leaf area of subcanopy vegetation (m2 kg-1)."""

    subcanopy_respiration_fraction: float = 0.1
    """The fraction of gross primary productivity used in respiration (unitless)."""

    subcanopy_yield: float = 0.6
    """The yield fraction of net primary productivity in subcanopy vegetation
    (unitless). """

    subcanopy_reproductive_allocation: float = 0.1
    """The fraction of subcanopy net primary productivity that is allocated to subcanopy
    seedbank mass (unitless)."""

    subcanopy_sprout_rate: float = 0.1
    """The rate at which new subcanopy biomass sprouts from the subcanopy seedbank mass
    (kg kg-1 m-2 y-1)."""

    subcanopy_sprout_yield: float = 0.5
    """The fraction of subcanopy seedbank mass that is realised as subcanopy vegetation
    mass (kg kg-1)."""

    subcanopy_vegetation_turnover: float = 1.0
    """The annual fraaction of subcanopy vegetative biomass turnover (kg kg-1 m-2
    y-1)."""

    subcanopy_seedbank_turnover: float = 0.25
    """The annual fraction of subcanopy seedbank biomass turnover (kg kg-1 m-2 y-1)."""

    subcanopy_seedbank_c_n_ratio: float = 20
    """The ideal mass ratio of nitrogen in subcanopy seedbank biomass (-)."""

    subcanopy_seedbank_c_p_ratio: float = 50
    """The ideal mass ratio of phosphorous in subcanopy seedbank biomass (-)."""

    subcanopy_vegetation_c_n_ratio: float = 20
    """The ideal mass ratio of nitrogen in subcanopy vegetation biomass (-)."""

    subcanopy_vegetation_c_p_ratio: float = 50
    """The ideal mass ratio of phosphorous in subcanopy vegetation biomass (-)."""

    subcanopy_vegetation_lignin: float = 0.2
    """The proportion of lignin in subcanopy vegetation."""

    subcanopy_seedbank_lignin: float = 0.2
    """The proportion of lignin in subcanopy seedbank."""

    root_exudates: float = 0.5
    """Fraction of GPP topslice allocated to root exudates."""

    propagule_mass_portion: float = 0.5
    """Fraction of reprodutive tissue allocated to propagules."""

    carbon_mass_per_propagule: float = 1
    """Mass of carbon per propagule in g."""


class PlantsExportConfig(Configuration):
    """Configuration class for plant export options.

    The plants model only writes a relatively small amount of data to the central data
    store. These variables are typically about the light environment within vertical
    layers and plant biomasses and stoichiometry within grid cells.

    However, the model also contains a great deal of demographic and allometric data
    about the plant communities within grid cells. If you want to look in detail at the
    plant communities in a simulation, then you can use this configuration section to
    output a wider range of plant model data at each model update.

    There are three possible output files:

    * Cohort data: details about the stems in each cohort, including the stem allometry
      and the GPP allocation of the stem. The stem GPP allocation is not defined during
      the model setup, so these attributes are set to ``np.nan`` for the initial output.
      This data is exported to the file ``plants_cohort_data.csv``.

    * Community canopy data: community wide data on the canopy structure, such as the
      heights of the canopy layers and the light transmission profile. This data is
      exported to the file ``plants_community_canopy_data.csv``.

    * Stem canopy data: details of contribution in leaf area and fAPAR from each stem to
      the community canopy model. This data is exported to the file
      ``plants_stem_canopy_data.csv``.

    By default, the exporter does not export any data, but you can configure which of
    these files to export. You can also configure which attributes to export for each
    data file. For each of the three files, the default is to not specify a subset of
    attributes, but you may not require all of this data and so can set specific
    attribute names to include in the file..
    """

    required_data: tuple[
        Literal["cohorts", "community_canopy", "stem_canopy"], ...
    ] = ()
    """A list of the strings giving the required plant data types to be exported. The 
    accepted values are "cohorts", "community_canopy" and "stem_canopy"."""
    cohort_attributes: tuple[str, ...] = ()
    """A list of the cohort attributes that should be exported."""
    community_canopy_attributes: tuple[str, ...] = ()
    """The community canopy attributes that should be exported."""
    stem_canopy_attributes: tuple[str, ...] = ()
    """The stem canopy attributes that should be exported."""
    float_format: str = "%0.5f"
    """A float format string to control data precision in export files."""


class PlantsConfiguration(ModelConfigurationRoot):
    """Root configuration class for the plants model."""

    pft_definitions_path: FILEPATH_PLACEHOLDER
    "A file path to a data file of plant functional type definitions"
    cohort_data_path: FILEPATH_PLACEHOLDER
    """A file path to a file of initial cohort data"""
    community_data_export: PlantsExportConfig = PlantsExportConfig()
    """Configuration of plant community data export"""
    constants: PlantsConstants = PlantsConstants()
    """Constants for the plants model"""
