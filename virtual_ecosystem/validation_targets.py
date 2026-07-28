"""Validation targets for the Virtual Ecosystem.

Defines two tiers of validation targets used to assess how well the
Virtual Ecosystem model reproduces observed ecosystem properties.

**Tier 1 — Primary targets (10 headline benchmarks)**
    Ecosystem-level quantities that should match observations from reference
    sites or published compilations.  These are the primary pass/fail criteria
    used when benchmarking a simulation.  Some primary targets are also
    *emergent* (i.e. they are aggregated or derived from multiple model
    output variables rather than appearing as a single directly written
    variable) — these are identified by :attr:`ValidationTarget.is_emergent`
    being ``True``.

**Tier 2 — Secondary emergent targets**
    Derived or emergent properties that can be computed post-hoc from the
    model output files.  They focus on energy fluxes, plant assimilation,
    animal consumption and assimilation flows, and Madingley-style
    life-history allometrics (Harfoot et al. 2014,
    doi:10.1371/journal.pbio.1001841).  All secondary targets are emergent.

Using the module
----------------
The target definitions are available through :data:`PRIMARY_TARGETS`,
:data:`SECONDARY_TARGETS`, :data:`EMERGENT_TARGETS` (all targets with
``is_emergent=True``, spanning both tiers), and the combined
:data:`ALL_TARGETS` list.

Each entry is a :class:`ValidationTarget` instance that records what
ecological property the target represents, whether it is primary or
secondary, whether it is emergent, which output files and variables are
used, and the supporting reference.

Helper functions are provided to derive emergent metrics directly from
the CSV files produced by the animal and plant exporters.
"""  # noqa: D205

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Target tier enum
# ---------------------------------------------------------------------------


class TargetTier(str, Enum):
    """Tier classification for a validation target.

    Attributes:
        PRIMARY: One of the 10 main headline benchmarks.
        SECONDARY: A derived or emergent property used as a supporting check.
    """

    PRIMARY = "primary"
    SECONDARY = "secondary"


# ---------------------------------------------------------------------------
# ValidationTarget dataclass
# ---------------------------------------------------------------------------


@dataclass
class ValidationTarget:
    """Metadata for a single validation target.

    Attributes:
        target_id: Short unique identifier (e.g. ``"P01"`` or ``"E03"``).
        name: Human-readable name for the target.
        tier: Whether this is a :attr:`TargetTier.PRIMARY` or
            :attr:`TargetTier.SECONDARY` target.
        is_emergent: ``True`` when the quantity is derived or aggregated
            from multiple model output variables rather than being written
            as a single variable by the model.  All :attr:`TargetTier.SECONDARY`
            targets are emergent.  Some :attr:`TargetTier.PRIMARY` targets
            are *also* emergent — they remain headline benchmarks but require
            post-processing to compute (e.g. totalling soil carbon pools or
            aggregating cohort-level animal biomass).
        ecological_property: Brief statement of the ecological quantity
            being assessed.
        description: Longer explanation of the target, including how it is
            computed and why it is ecologically meaningful.
        output_variables: Names of variables in ``data_variables.toml`` or
            column names in exported CSV files that are used to compute this
            target.
        output_files: Which output sources supply the required variables.
            Typical values are ``"Data object (xarray)"`` for variables
            written to the central :class:`~virtual_ecosystem.core.data.Data`
            store, ``"animal_cohort_data.csv"`` or
            ``"animal_trophic_interactions.csv"`` for the animal exporter
            outputs, and ``"plants_cohort_data.csv"`` for the plant exporter.
        reference: Citation key (matching ``docs/source/refs.bib``) or a
            short description of the external reference that motivates or
            supplies observed values for this target.
        units: Physical units of the quantity.
    """

    target_id: str
    name: str
    tier: TargetTier
    is_emergent: bool
    ecological_property: str
    description: str
    output_variables: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    reference: str = ""
    units: str = ""


# ---------------------------------------------------------------------------
# Primary targets — 10 headline benchmarks
# ---------------------------------------------------------------------------

PRIMARY_TARGETS: list[ValidationTarget] = [
    ValidationTarget(
        target_id="P01",
        name="Gross Primary Productivity",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Rate of photosynthetic carbon fixation by the plant canopy",
        description=(
            "Gross Primary Productivity (GPP) is the total rate at which the plant "
            "community fixes atmospheric CO2 through photosynthesis, integrated across "
            "all canopy layers and plant functional types.  In the Virtual Ecosystem the "
            "per-stem GPP is computed by the P Model and summed to give cell-level GPP "
            "(``per_stem_gpp`` in kg C stem⁻¹ update⁻¹, accessible via the plant "
            "exporter).  Spatial and temporal averages should be compared against "
            "eddy-covariance or satellite-derived GPP products for the target biome.  "
            "This target is emergent because it is aggregated from per-stem, per-layer "
            "photosynthesis estimates computed by the P Model."
        ),
        output_variables=["plant_net_co2_assimilation"],
        output_files=["Data object (xarray)", "plants_cohort_data.csv"],
        reference="harfoot_madingley_2014",
        units="kg C m⁻² yr⁻¹",
    ),
    ValidationTarget(
        target_id="P02",
        name="Evapotranspiration",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Total water vapour loss from vegetation and soil to atmosphere",
        description=(
            "Evapotranspiration (ET) is the combined flux of water from the soil, "
            "canopy interception, and plant transpiration.  It is computed as the sum "
            "of ``transpiration``, ``soil_evaporation``, and ``canopy_evaporation`` "
            "across the spatial grid using :func:`compute_evapotranspiration`.  "
            "Comparisons should target long-term site-level ET observations or "
            "water-balance estimates.  This target is emergent because it must be "
            "aggregated from three separate flux variables."
        ),
        output_variables=["transpiration", "soil_evaporation", "canopy_evaporation"],
        output_files=["Data object (xarray)"],
        reference="",
        units="mm yr⁻¹",
    ),
    ValidationTarget(
        target_id="P03",
        name="Above-ground vegetation biomass",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Carbon stored in stems and foliage above the soil surface",
        description=(
            "Above-ground biomass (AGB) captures the carbon in plant stems and leaves "
            "across all plant functional types.  It is derived from the plant exporter "
            "CSV by summing ``biomass_foliage_carbon_mass`` and "
            "``biomass_stem_carbon_mass`` for all cohorts within a cell using "
            ":func:`compute_above_ground_biomass`.  Reference values for tropical and "
            "temperate forests are widely available from inventory surveys and "
            "remote-sensing products.  This target is emergent because it requires "
            "aggregation across cohorts from the plant exporter CSV."
        ),
        output_variables=["biomass_foliage_carbon_mass", "biomass_stem_carbon_mass"],
        output_files=["plants_cohort_data.csv"],
        reference="",
        units="kg C m⁻²",
    ),
    ValidationTarget(
        target_id="P04",
        name="Below-ground vegetation biomass",
        tier=TargetTier.PRIMARY,
        is_emergent=False,
        ecological_property="Carbon stored in plant fine roots below the soil surface",
        description=(
            "Below-ground biomass (BGB) is the fine-root carbon mass summed across all "
            "plant cohorts in a cell.  It is read from the plant exporter CSV column "
            "``biomass_root_carbon_mass``.  The ratio of BGB to AGB provides an "
            "additional diagnostic (see secondary target E04).  Unlike the other "
            "biomass targets, root mass is tracked as a single tissue per cohort so "
            "this target does not require cross-pool aggregation."
        ),
        output_variables=["biomass_root_carbon_mass"],
        output_files=["plants_cohort_data.csv"],
        reference="",
        units="kg C m⁻²",
    ),
    ValidationTarget(
        target_id="P05",
        name="Total soil organic carbon",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Organic carbon stored across all soil carbon pools",
        description=(
            "Total soil organic carbon (SOC) is the sum of the carbon components of "
            "all soil pools tracked by the Virtual Ecosystem: low molecular weight "
            "organic carbon (``soil_cnp_pool_lmwc``), mineral-associated organic "
            "matter (``soil_cnp_pool_maom``), particulate organic matter "
            "(``soil_cnp_pool_pom``), and necromass (``soil_cnp_pool_necromass``). "
            "Each variable stores the full CNP array so the carbon component must be "
            "selected via the ``element`` coordinate before summing.  This target is "
            "emergent because it aggregates four separate soil carbon pools."
        ),
        output_variables=[
            "soil_cnp_pool_lmwc",
            "soil_cnp_pool_maom",
            "soil_cnp_pool_pom",
            "soil_cnp_pool_necromass",
        ],
        output_files=["Data object (xarray)"],
        reference="",
        units="kg C m⁻²",
    ),
    ValidationTarget(
        target_id="P06",
        name="Total litter carbon",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Carbon stored in all above- and below-ground litter pools",
        description=(
            "Total litter carbon is the sum of the carbon components of the five "
            "litter pools: above-ground metabolic "
            "(``litter_pool_above_metabolic_cnp``), above-ground structural "
            "(``litter_pool_above_structural_cnp``), woody "
            "(``litter_pool_woody_cnp``), below-ground metabolic "
            "(``litter_pool_below_metabolic_cnp``), and below-ground structural "
            "(``litter_pool_below_structural_cnp``).  Reference values are available "
            "from forest inventory and litter-trap studies.  This target is emergent "
            "because it aggregates five separate litter pools."
        ),
        output_variables=[
            "litter_pool_above_metabolic_cnp",
            "litter_pool_above_structural_cnp",
            "litter_pool_woody_cnp",
            "litter_pool_below_metabolic_cnp",
            "litter_pool_below_structural_cnp",
        ],
        output_files=["Data object (xarray)"],
        reference="",
        units="kg C m⁻²",
    ),
    ValidationTarget(
        target_id="P07",
        name="Soil respiration",
        tier=TargetTier.PRIMARY,
        is_emergent=False,
        ecological_property="CO2 efflux from soil microbial decomposition",
        description=(
            "Soil respiration is the CO2 produced by microbial decomposition of "
            "organic matter in the soil.  It is stored directly in the "
            "``soil_respiration`` variable in the data object and requires no further "
            "aggregation.  Site-level comparisons should use automated chamber or "
            "gradient measurements averaged over the same time period as the model "
            "output."
        ),
        output_variables=["soil_respiration"],
        output_files=["Data object (xarray)"],
        reference="",
        units="ppm (model-native)",
    ),
    ValidationTarget(
        target_id="P08",
        name="Net radiation",
        tier=TargetTier.PRIMARY,
        is_emergent=False,
        ecological_property="Radiative energy balance at the land surface",
        description=(
            "Net radiation (Rn) is the difference between incoming and outgoing "
            "short- and long-wave radiation at the top of the canopy.  It is stored "
            "directly in the ``net_radiation`` variable and requires no further "
            "aggregation.  Comparisons should target radiation measurements from flux "
            "tower sites within the same biome."
        ),
        output_variables=["net_radiation"],
        output_files=["Data object (xarray)"],
        reference="",
        units="W m⁻²",
    ),
    ValidationTarget(
        target_id="P09",
        name="Animal biomass density",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Total heterotroph carbon mass per unit area",
        description=(
            "Animal biomass density is the aggregate carbon mass of all animal cohorts "
            "per grid cell area.  It is computed from ``animal_cohort_data.csv`` by "
            "multiplying ``mass_carbon`` by ``individuals`` for each cohort and summing "
            "within each time step using :func:`compute_animal_biomass_density`.  "
            "Reference values can be drawn from Madingley model outputs "
            "(Harfoot et al. 2014) or empirical compilations of heterotroph biomass "
            "density for the target biome.  This target is emergent because it must be "
            "aggregated from cohort-level data."
        ),
        output_variables=["mass_carbon", "individuals"],
        output_files=["animal_cohort_data.csv"],
        reference="harfoot_madingley_2014",
        units="kg C m⁻²",
    ),
    ValidationTarget(
        target_id="P10",
        name="Total heterotrophic respiration",
        tier=TargetTier.PRIMARY,
        is_emergent=True,
        ecological_property="Combined CO2 efflux from soil microbes and animals",
        description=(
            "Total heterotrophic respiration is the sum of ``soil_respiration`` and "
            "``total_animal_respiration`` averaged over the simulation domain.  It "
            "provides a check on the total carbon cycling rate through the heterotroph "
            "compartment and should be compared against eddy-covariance partitioned "
            "ecosystem respiration measurements.  This target is emergent because it "
            "aggregates two separate respiration variables from different model "
            "components."
        ),
        output_variables=["soil_respiration", "total_animal_respiration"],
        output_files=["Data object (xarray)"],
        reference="",
        units="ppm (model-native)",
    ),
]


# ---------------------------------------------------------------------------
# Secondary emergent targets
# ---------------------------------------------------------------------------

SECONDARY_TARGETS: list[ValidationTarget] = [
    # ---- Energy flux group ------------------------------------------------
    ValidationTarget(
        target_id="E01",
        name="Latent heat flux",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Energy flux associated with evapotranspiration",
        description=(
            "The latent heat flux (LE) profile is stored in ``latent_heat_flux`` "
            "(W m⁻²) across canopy layers.  The canopy top value is the surface "
            "flux that should be compared against eddy-covariance measurements.  "
            "Together with the sensible heat flux it determines how Rn is partitioned "
            "between turbulent fluxes."
        ),
        output_variables=["latent_heat_flux"],
        output_files=["Data object (xarray)"],
        reference="",
        units="W m⁻²",
    ),
    ValidationTarget(
        target_id="E02",
        name="Sensible heat flux",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Convective energy flux from land surface to atmosphere",
        description=(
            "The sensible heat flux (H) profile is stored in ``sensible_heat_flux`` "
            "(W m⁻²) across canopy layers.  The canopy top value is the observable "
            "flux.  Comparisons should use the same time-averaging as the model "
            "output."
        ),
        output_variables=["sensible_heat_flux"],
        output_files=["Data object (xarray)"],
        reference="",
        units="W m⁻²",
    ),
    ValidationTarget(
        target_id="E03",
        name="Bowen ratio",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property=(
            "Partitioning of net radiation between sensible and latent heat"
        ),
        description=(
            "The Bowen ratio (β = H / LE) is an emergent metric of the surface energy "
            "balance that indicates how wet or dry the surface energy budget is.  It is "
            "computed from the top-of-canopy values of ``sensible_heat_flux`` and "
            "``latent_heat_flux`` using :func:`compute_bowen_ratio`.  Tropical "
            "rainforests typically have β < 0.5."
        ),
        output_variables=["sensible_heat_flux", "latent_heat_flux"],
        output_files=["Data object (xarray)"],
        reference="",
        units="dimensionless",
    ),
    ValidationTarget(
        target_id="E04",
        name="Root-to-shoot ratio",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Allocation of carbon between above- and below-ground plant tissues",
        description=(
            "The root-to-shoot ratio (RSR = BGB / AGB) is an emergent allometric "
            "property of the plant community.  It is computed from "
            "``biomass_root_carbon_mass``, ``biomass_foliage_carbon_mass`` and "
            "``biomass_stem_carbon_mass`` in the plant exporter CSV using "
            ":func:`compute_root_to_shoot_ratio`.  Observed values for tropical forests "
            "are typically in the range 0.2–0.4."
        ),
        output_variables=[
            "biomass_root_carbon_mass",
            "biomass_foliage_carbon_mass",
            "biomass_stem_carbon_mass",
        ],
        output_files=["plants_cohort_data.csv"],
        reference="",
        units="dimensionless",
    ),
    # ---- Animal assimilation group ----------------------------------------
    ValidationTarget(
        target_id="A01",
        name="Total animal assimilation rate",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Carbon consumed and assimilated across all animal cohorts",
        description=(
            "The total animal assimilation rate is the sum of the carbon column (``C``) "
            "in ``animal_trophic_interactions.csv`` across all cohorts, resource kinds, "
            "and grid cells for a given time step.  It captures the aggregate flow of "
            "carbon through all animal consumers and can be compared against "
            "carbon-budget estimates of secondary production."
        ),
        output_variables=["C"],
        output_files=["animal_trophic_interactions.csv"],
        reference="harfoot_madingley_2014",
        units="kg C m⁻² update⁻¹",
    ),
    ValidationTarget(
        target_id="A02",
        name="Herbivore assimilation rate",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Carbon consumed from plant or litter resources by herbivores",
        description=(
            "The herbivore assimilation rate is computed from "
            "``animal_trophic_interactions.csv`` by filtering rows where "
            "``resource_kind != 'cohort'`` (i.e. the resource is a plant or litter "
            "pool, not another animal) and summing the ``C`` column.  Use "
            ":func:`compute_herbivore_assimilation_rate` to derive this quantity.  "
            "Reference values can be obtained from Madingley model runs "
            "(Harfoot et al. 2014)."
        ),
        output_variables=["C", "resource_kind"],
        output_files=["animal_trophic_interactions.csv"],
        reference="harfoot_madingley_2014",
        units="kg C m⁻² update⁻¹",
    ),
    ValidationTarget(
        target_id="A03",
        name="Predator assimilation rate",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Carbon consumed from prey cohorts by predators",
        description=(
            "The predator assimilation rate is computed from "
            "``animal_trophic_interactions.csv`` by filtering rows where "
            "``resource_kind == 'cohort'`` (predation events) and summing the "
            "``C`` column.  Use :func:`compute_predator_assimilation_rate` to "
            "derive this quantity."
        ),
        output_variables=["C", "resource_kind"],
        output_files=["animal_trophic_interactions.csv"],
        reference="harfoot_madingley_2014",
        units="kg C m⁻² update⁻¹",
    ),
    ValidationTarget(
        target_id="A04",
        name="Trophic efficiency",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property="Fraction of consumed carbon passed to the next trophic level",
        description=(
            "Trophic efficiency is the ratio of predator assimilation (target A03) to "
            "herbivore assimilation (target A02).  It measures how efficiently carbon "
            "is transferred up the food web.  Values are typically 5–20 % in empirical "
            "systems.  Use :func:`compute_trophic_efficiency` to derive this quantity."
        ),
        output_variables=["C", "resource_kind"],
        output_files=["animal_trophic_interactions.csv"],
        reference="harfoot_madingley_2014",
        units="dimensionless (fraction)",
    ),
    # ---- Madingley-style allometric group ---------------------------------
    ValidationTarget(
        target_id="M01",
        name="Body mass vs time to maturity",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property=(
            "Allometric relationship between adult body mass and development time"
        ),
        description=(
            "The Madingley model predicts that time to maturity scales positively "
            "with adult body mass across functional groups (Harfoot et al. 2014, "
            "Fig. 2).  This emergent relationship is extracted from "
            "``animal_cohort_data.csv`` by taking the ``largest_mass_achieved`` "
            "and ``time_to_maturity`` fields for all mature cohorts "
            "(``is_mature == True``) and fitting or plotting the relationship.  "
            "Use :func:`body_mass_vs_time_to_maturity` to extract the paired arrays."
        ),
        output_variables=["largest_mass_achieved", "time_to_maturity", "is_mature"],
        output_files=["animal_cohort_data.csv"],
        reference="harfoot_madingley_2014",
        units="kg vs days",
    ),
    ValidationTarget(
        target_id="M02",
        name="Body mass vs maturity rate",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property=(
            "Allometric relationship between adult body mass and rate of attaining maturity"
        ),
        description=(
            "The maturity rate (1 / time_to_maturity) should scale negatively with "
            "adult body mass: larger animals take proportionally longer to mature.  "
            "This mirrors Figure 2 in Harfoot et al. (2014), where body mass and "
            "maturity rate exhibit a clear allometric relationship across functional "
            "groups.  Use :func:`body_mass_vs_maturity_rate` to extract the paired "
            "arrays from ``animal_cohort_data.csv``."
        ),
        output_variables=["largest_mass_achieved", "time_to_maturity", "is_mature"],
        output_files=["animal_cohort_data.csv"],
        reference="harfoot_madingley_2014",
        units="kg vs day⁻¹",
    ),
    ValidationTarget(
        target_id="M03",
        name="Body mass vs abundance (Damuth's Law)",
        tier=TargetTier.SECONDARY,
        is_emergent=True,
        ecological_property=(
            "Negative allometric scaling of population density with body mass"
        ),
        description=(
            "Damuth's Law states that population density scales approximately as "
            "mass⁻⁰·⁷⁵ across species.  This emergent relationship can be checked "
            "by plotting the ``individuals`` count against ``largest_mass_achieved`` "
            "for all cohorts within a single cell at a given time step.  The expected "
            "log-log slope is approximately −0.75.  Use "
            ":func:`body_mass_vs_abundance` to extract the paired arrays."
        ),
        output_variables=["largest_mass_achieved", "individuals"],
        output_files=["animal_cohort_data.csv"],
        reference="harfoot_madingley_2014",
        units="kg vs individuals",
    ),
]


# ---------------------------------------------------------------------------
# Combined lists
# ---------------------------------------------------------------------------

ALL_TARGETS: list[ValidationTarget] = PRIMARY_TARGETS + SECONDARY_TARGETS
"""All validation targets, primary (10) followed by secondary."""

EMERGENT_TARGETS: list[ValidationTarget] = [t for t in ALL_TARGETS if t.is_emergent]
"""All targets that require post-processing to compute (``is_emergent=True``).

This spans both tiers: the seven primary targets that are aggregated from
multiple model output variables (P01–P03, P05, P06, P09, P10) and all
secondary targets (E01–E04, A01–A04, M01–M03).
"""


def get_emergent_targets(
    *,
    tier: TargetTier | None = None,
) -> list[ValidationTarget]:
    """Return all emergent validation targets, optionally filtered by tier.

    Args:
        tier: If provided, restrict results to targets in the given
            :class:`TargetTier`.  Pass ``TargetTier.PRIMARY`` to retrieve
            only the primary targets that are also emergent, or
            ``TargetTier.SECONDARY`` to retrieve only secondary targets.
            Defaults to ``None`` (return all emergent targets).

    Returns:
        List of :class:`ValidationTarget` instances with ``is_emergent=True``,
        filtered by *tier* if provided.
    """
    targets = EMERGENT_TARGETS
    if tier is not None:
        targets = [t for t in targets if t.tier == tier]
    return targets


# ---------------------------------------------------------------------------
# Helper functions — energy flux metrics
# ---------------------------------------------------------------------------


def compute_bowen_ratio(
    sensible_heat: NDArray[np.floating] | pd.Series,
    latent_heat: NDArray[np.floating] | pd.Series,
) -> NDArray[np.floating]:
    """Compute the Bowen ratio (H / LE) from heat flux arrays.

    The Bowen ratio characterises the partitioning of net radiation between
    sensible and latent heat.  Cells or time steps where ``latent_heat`` is
    zero or negative are returned as ``np.nan`` to avoid division errors.

    This function supports validation target :data:`E03`.

    Args:
        sensible_heat: Array of sensible heat flux values [W m⁻²].
        latent_heat: Array of latent heat flux values [W m⁻²].

    Returns:
        Array of Bowen ratio values (dimensionless).  Entries where
        ``latent_heat <= 0`` are set to ``np.nan``.
    """
    sh = np.asarray(sensible_heat, dtype=float)
    lh = np.asarray(latent_heat, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(lh > 0, sh / lh, np.nan)
    return ratio


def compute_evapotranspiration(
    transpiration: NDArray[np.floating] | pd.Series,
    soil_evaporation: NDArray[np.floating] | pd.Series,
    canopy_evaporation: NDArray[np.floating] | pd.Series,
) -> NDArray[np.floating]:
    """Compute total evapotranspiration from its component fluxes.

    Sums plant transpiration, soil evaporation, and canopy evaporation into
    the total ET flux for each grid cell and time step.

    This function supports validation target :data:`P02`.

    Args:
        transpiration: Transpiration from canopy and sub-canopy [mm].
        soil_evaporation: Soil evaporation [mm].
        canopy_evaporation: Canopy interception evaporation [mm].

    Returns:
        Total evapotranspiration [mm].
    """
    return (
        np.asarray(transpiration, dtype=float)
        + np.asarray(soil_evaporation, dtype=float)
        + np.asarray(canopy_evaporation, dtype=float)
    )


# ---------------------------------------------------------------------------
# Helper functions — plant biomass metrics
# ---------------------------------------------------------------------------


def compute_above_ground_biomass(
    plant_cohort_df: pd.DataFrame,
) -> pd.Series:
    """Compute total above-ground plant carbon per cell per time step.

    Sums ``biomass_foliage_carbon_mass`` and ``biomass_stem_carbon_mass``
    for all cohorts within each (``cell_id``, ``time``) combination.

    This function supports validation target :data:`P03`.

    Args:
        plant_cohort_df: DataFrame loaded from ``plants_cohort_data.csv``.

    Returns:
        Series indexed by ``(cell_id, time)`` with values in kg C.

    Raises:
        KeyError: If required columns are absent from ``plant_cohort_df``.
    """
    required = {"cell_id", "time", "biomass_foliage_carbon_mass", "biomass_stem_carbon_mass"}
    _check_columns(plant_cohort_df, required, "plant_cohort_df")

    agb = plant_cohort_df["biomass_foliage_carbon_mass"] + plant_cohort_df["biomass_stem_carbon_mass"]
    return agb.groupby([plant_cohort_df["cell_id"], plant_cohort_df["time"]]).sum()


def compute_below_ground_biomass(
    plant_cohort_df: pd.DataFrame,
) -> pd.Series:
    """Compute total below-ground plant carbon per cell per time step.

    Sums ``biomass_root_carbon_mass`` for all cohorts within each
    (``cell_id``, ``time``) combination.

    This function supports validation target :data:`P04`.

    Args:
        plant_cohort_df: DataFrame loaded from ``plants_cohort_data.csv``.

    Returns:
        Series indexed by ``(cell_id, time)`` with values in kg C.

    Raises:
        KeyError: If required columns are absent from ``plant_cohort_df``.
    """
    required = {"cell_id", "time", "biomass_root_carbon_mass"}
    _check_columns(plant_cohort_df, required, "plant_cohort_df")

    return plant_cohort_df["biomass_root_carbon_mass"].groupby(
        [plant_cohort_df["cell_id"], plant_cohort_df["time"]]
    ).sum()


def compute_root_to_shoot_ratio(
    plant_cohort_df: pd.DataFrame,
) -> pd.Series:
    """Compute the root-to-shoot ratio per cell per time step.

    The root-to-shoot ratio (RSR) is BGB / AGB where BGB is the total fine
    root carbon and AGB is the total foliar + stem carbon.  Cells where AGB
    is zero are returned as ``np.nan``.

    This function supports validation target :data:`E04`.

    Args:
        plant_cohort_df: DataFrame loaded from ``plants_cohort_data.csv``.

    Returns:
        Series indexed by ``(cell_id, time)`` of dimensionless RSR values.

    Raises:
        KeyError: If required columns are absent from ``plant_cohort_df``.
    """
    agb = compute_above_ground_biomass(plant_cohort_df)
    bgb = compute_below_ground_biomass(plant_cohort_df)
    with np.errstate(invalid="ignore", divide="ignore"):
        rsr = bgb.where(agb > 0).div(agb.where(agb > 0))
    return rsr


# ---------------------------------------------------------------------------
# Helper functions — animal assimilation metrics
# ---------------------------------------------------------------------------


def compute_total_animal_assimilation_rate(
    trophic_df: pd.DataFrame,
) -> pd.Series:
    """Compute total animal carbon assimilation per time step.

    Sums the ``C`` column of ``animal_trophic_interactions.csv`` over all
    cohorts, resource kinds, and cells for each time step.

    This function supports validation target :data:`A01`.

    Args:
        trophic_df: DataFrame loaded from ``animal_trophic_interactions.csv``.

    Returns:
        Series indexed by ``time_index`` with total carbon assimilated [kg C].

    Raises:
        KeyError: If required columns are absent from ``trophic_df``.
    """
    required = {"time_index", "C"}
    _check_columns(trophic_df, required, "trophic_df")
    return trophic_df.groupby("time_index")["C"].sum()


def compute_herbivore_assimilation_rate(
    trophic_df: pd.DataFrame,
) -> pd.Series:
    """Compute herbivore carbon assimilation per time step.

    Filters ``animal_trophic_interactions.csv`` to rows where
    ``resource_kind != 'cohort'`` (i.e. the resource is a plant, litter, or
    soil pool rather than another animal cohort) and sums the ``C`` column
    per time step.

    This function supports validation target :data:`A02`.

    Args:
        trophic_df: DataFrame loaded from ``animal_trophic_interactions.csv``.

    Returns:
        Series indexed by ``time_index`` with herbivore-pathway carbon [kg C].

    Raises:
        KeyError: If required columns are absent from ``trophic_df``.
    """
    required = {"time_index", "C", "resource_kind"}
    _check_columns(trophic_df, required, "trophic_df")
    mask = trophic_df["resource_kind"] != "cohort"
    return trophic_df.loc[mask].groupby("time_index")["C"].sum()


def compute_predator_assimilation_rate(
    trophic_df: pd.DataFrame,
) -> pd.Series:
    """Compute predator carbon assimilation per time step.

    Filters ``animal_trophic_interactions.csv`` to rows where
    ``resource_kind == 'cohort'`` (predation events) and sums the ``C``
    column per time step.

    This function supports validation target :data:`A03`.

    Args:
        trophic_df: DataFrame loaded from ``animal_trophic_interactions.csv``.

    Returns:
        Series indexed by ``time_index`` with predation-pathway carbon [kg C].

    Raises:
        KeyError: If required columns are absent from ``trophic_df``.
    """
    required = {"time_index", "C", "resource_kind"}
    _check_columns(trophic_df, required, "trophic_df")
    mask = trophic_df["resource_kind"] == "cohort"
    return trophic_df.loc[mask].groupby("time_index")["C"].sum()


def compute_trophic_efficiency(
    trophic_df: pd.DataFrame,
) -> pd.Series:
    """Compute trophic efficiency (predator / herbivore assimilation) per time step.

    Trophic efficiency is the ratio of carbon consumed via predation to carbon
    consumed via herbivory.  Time steps where herbivore assimilation is zero
    are returned as ``np.nan``.

    This function supports validation target :data:`A04`.

    Args:
        trophic_df: DataFrame loaded from ``animal_trophic_interactions.csv``.

    Returns:
        Series indexed by ``time_index`` of dimensionless trophic efficiency
        values.

    Raises:
        KeyError: If required columns are absent from ``trophic_df``.
    """
    herb = compute_herbivore_assimilation_rate(trophic_df)
    pred = compute_predator_assimilation_rate(trophic_df)
    # Align on index, filling missing time steps with 0
    herb, pred = herb.align(pred, fill_value=0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        efficiency = pred.where(herb > 0).div(herb.where(herb > 0))
    return efficiency


# ---------------------------------------------------------------------------
# Helper functions — Madingley-style allometric metrics
# ---------------------------------------------------------------------------


def body_mass_vs_time_to_maturity(
    cohort_df: pd.DataFrame,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Extract body mass and time-to-maturity pairs for mature cohorts.

    Filters ``animal_cohort_data.csv`` to rows where ``is_mature`` is
    ``True`` and returns arrays of ``largest_mass_achieved`` and
    ``time_to_maturity`` ready for scatter-plot or regression analysis.

    This function supports validation target :data:`M01`.

    Args:
        cohort_df: DataFrame loaded from ``animal_cohort_data.csv``.

    Returns:
        Tuple of ``(mass_array, time_to_maturity_array)`` where both arrays
        contain only finite positive values for mature cohorts.

    Raises:
        KeyError: If required columns are absent from ``cohort_df``.
    """
    required = {"is_mature", "largest_mass_achieved", "time_to_maturity"}
    _check_columns(cohort_df, required, "cohort_df")

    mature = cohort_df[cohort_df["is_mature"].astype(bool)].copy()
    # Keep only rows with valid, positive time-to-maturity
    valid = (mature["time_to_maturity"] > 0) & (mature["largest_mass_achieved"] > 0)
    mass = mature.loc[valid, "largest_mass_achieved"].to_numpy(dtype=float)
    ttm = mature.loc[valid, "time_to_maturity"].to_numpy(dtype=float)
    return mass, ttm


def body_mass_vs_maturity_rate(
    cohort_df: pd.DataFrame,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Extract body mass and maturity rate pairs for mature cohorts.

    Maturity rate is defined as 1 / time_to_maturity [day⁻¹].  Larger
    animals are expected to have lower maturity rates, mirroring the
    allometric relationship shown in Harfoot et al. (2014), Fig. 2.

    This function supports validation target :data:`M02`.

    Args:
        cohort_df: DataFrame loaded from ``animal_cohort_data.csv``.

    Returns:
        Tuple of ``(mass_array, maturity_rate_array)`` for all valid mature
        cohorts.

    Raises:
        KeyError: If required columns are absent from ``cohort_df``.
    """
    mass, ttm = body_mass_vs_time_to_maturity(cohort_df)
    maturity_rate = 1.0 / ttm
    return mass, maturity_rate


def body_mass_vs_abundance(
    cohort_df: pd.DataFrame,
    cell_id: int | None = None,
    time_index: int | None = None,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Extract body mass and individual count pairs for a Damuth's Law check.

    Optionally filters to a single grid cell and/or time step before
    returning the paired arrays.

    This function supports validation target :data:`M03`.

    Args:
        cohort_df: DataFrame loaded from ``animal_cohort_data.csv``.
        cell_id: If provided, restrict to cohorts whose territory centroid is
            in this cell (``centroid_key == cell_id``).
        time_index: If provided, restrict to this time step.

    Returns:
        Tuple of ``(mass_array, individuals_array)`` for all matching cohorts
        with positive mass and individual count.

    Raises:
        KeyError: If required columns are absent from ``cohort_df``.
    """
    required = {"largest_mass_achieved", "individuals"}
    _check_columns(cohort_df, required, "cohort_df")

    df = cohort_df.copy()
    if cell_id is not None:
        if "centroid_key" not in df.columns:
            raise KeyError("'centroid_key' column required when cell_id is provided.")
        df = df[df["centroid_key"] == cell_id]
    if time_index is not None:
        if "time_index" not in df.columns:
            raise KeyError("'time_index' column required when time_index is provided.")
        df = df[df["time_index"] == time_index]

    valid = (df["largest_mass_achieved"] > 0) & (df["individuals"] > 0)
    mass = df.loc[valid, "largest_mass_achieved"].to_numpy(dtype=float)
    abundance = df.loc[valid, "individuals"].to_numpy(dtype=float)
    return mass, abundance


def compute_animal_biomass_density(
    cohort_df: pd.DataFrame,
) -> pd.Series:
    """Compute total animal carbon biomass density per time step.

    Multiplies ``mass_carbon`` by ``individuals`` for each cohort and sums
    over all cohorts within each time step.

    This function supports validation target :data:`P09`.

    Args:
        cohort_df: DataFrame loaded from ``animal_cohort_data.csv``.

    Returns:
        Series indexed by ``time_index`` with total animal carbon [kg C].

    Raises:
        KeyError: If required columns are absent from ``cohort_df``.
    """
    required = {"time_index", "mass_carbon", "individuals"}
    _check_columns(cohort_df, required, "cohort_df")

    total_c = cohort_df["mass_carbon"] * cohort_df["individuals"]
    return total_c.groupby(cohort_df["time_index"]).sum()


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _check_columns(df: pd.DataFrame, required: set[str], arg_name: str) -> None:
    """Raise KeyError if any required columns are absent from *df*.

    Args:
        df: DataFrame to check.
        required: Set of required column names.
        arg_name: Name of the argument (used in the error message).

    Raises:
        KeyError: If any of *required* are missing from ``df.columns``.
    """
    missing = required - set(df.columns)
    if missing:
        raise KeyError(
            f"The DataFrame '{arg_name}' is missing required columns: "
            f"{sorted(missing)}"
        )
