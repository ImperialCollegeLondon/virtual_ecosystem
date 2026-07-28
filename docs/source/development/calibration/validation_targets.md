---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.4
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Validation targets

This page describes the validation targets used to assess how well the Virtual
Ecosystem reproduces observed ecosystem properties.  The targets are organised
into two tiers.

**Tier 1 — Primary targets (10 headline benchmarks)**
:   Ecosystem-level quantities that can be compared directly against site
    observations or published data compilations.  These are the headline
    pass/fail benchmarks for a simulation.

**Tier 2 — Secondary emergent targets**
:   Derived or emergent properties computed post-hoc from the model output
    files.  They provide a richer picture of model behaviour and are
    particularly useful for diagnosing whether the *dynamics* of the ecosystem
    (not just its mean state) are realistic.

Within the primary tier, some targets are also **emergent** — they must be
aggregated from multiple model output variables or cohort-level CSV exports
rather than being written as a single variable by the model.  These targets
carry an *Emergent* badge in the table below and are also listed in the
secondary emergent tier section for convenience.

---

## Primary targets (Tier 1)

The ten primary targets are implemented as
{class}`~virtual_ecosystem.validation_targets.ValidationTarget` instances in
{mod}`virtual_ecosystem.validation_targets`.  The three targets that are **not**
emergent (P04, P07, P08) are single model variables and require no
post-processing to read.  The seven **emergent** primary targets (P01–P03,
P05, P06, P09, P10) must be aggregated from multiple output variables or
CSV exports using the helper functions described below.

| ID | Name | Emergent? | Units | Output source | Reference |
|----|------|:---------:|-------|---------------|-----------|
| P01 | Gross Primary Productivity | ✓ | kg C m⁻² yr⁻¹ | `plant_net_co2_assimilation`; `plants_cohort_data.csv` | {cite:t}`harfoot_madingley_2014` |
| P02 | Evapotranspiration | ✓ | mm yr⁻¹ | `transpiration`, `soil_evaporation`, `canopy_evaporation` | — |
| P03 | Above-ground vegetation biomass | ✓ | kg C m⁻² | `plants_cohort_data.csv` | — |
| P04 | Below-ground vegetation biomass | | kg C m⁻² | `plants_cohort_data.csv` | — |
| P05 | Total soil organic carbon | ✓ | kg C m⁻² | `soil_cnp_pool_*` variables | — |
| P06 | Total litter carbon | ✓ | kg C m⁻² | `litter_pool_*_cnp` variables | — |
| P07 | Soil respiration | | ppm | `soil_respiration` | — |
| P08 | Net radiation | | W m⁻² | `net_radiation` | — |
| P09 | Animal biomass density | ✓ | kg C m⁻² | `animal_cohort_data.csv` | {cite:t}`harfoot_madingley_2014` |
| P10 | Total heterotrophic respiration | ✓ | ppm | `soil_respiration`, `total_animal_respiration` | — |

### P01 — Gross Primary Productivity

**Ecological property**: Rate of photosynthetic carbon fixation by the plant canopy.

**Why it is emergent**: GPP is computed by the P Model at the per-stem, per-layer
level and must be summed across all cohorts within a grid cell.

**Output**: Per-stem GPP is available in the `plants_cohort_data.csv` exporter
output.  The cell-level aggregate is also held in `plant_net_co2_assimilation`
in the data object.

**Reference**: Comparisons can be made against eddy-covariance GPP or
satellite-derived products (e.g. MODIS MOD17).

---

### P02 — Evapotranspiration

**Ecological property**: Total water vapour loss from vegetation and soil to the
atmosphere.

**Why it is emergent**: ET must be aggregated from three separate flux variables
(`transpiration`, `soil_evaporation`, `canopy_evaporation`) using
{func}`~virtual_ecosystem.validation_targets.compute_evapotranspiration`.

**Output**: All three components are in the data object (xarray).

---

### P03 — Above-ground vegetation biomass

**Ecological property**: Carbon in stems and foliage above the soil surface.

**Why it is emergent**: AGB is the per-cell sum of `biomass_foliage_carbon_mass`
and `biomass_stem_carbon_mass` across all plant cohorts.  Use
{func}`~virtual_ecosystem.validation_targets.compute_above_ground_biomass`.

**Output**: `plants_cohort_data.csv`.

---

### P04 — Below-ground vegetation biomass

**Ecological property**: Carbon in plant fine roots.

**Output**: `biomass_root_carbon_mass` column in `plants_cohort_data.csv`.

---

### P05 — Total soil organic carbon

**Ecological property**: Organic carbon stored across all soil carbon pools.

**Why it is emergent**: Must sum the carbon component of four soil variables:
`soil_cnp_pool_lmwc`, `soil_cnp_pool_maom`, `soil_cnp_pool_pom`,
`soil_cnp_pool_necromass`.

**Output**: Data object (xarray).  Each variable has an `element` coordinate;
select `element == "C"` before summing.

---

### P06 — Total litter carbon

**Ecological property**: Carbon stored in all above- and below-ground litter pools.

**Why it is emergent**: Must sum the carbon components of five litter variables:
`litter_pool_above_metabolic_cnp`, `litter_pool_above_structural_cnp`,
`litter_pool_woody_cnp`, `litter_pool_below_metabolic_cnp`,
`litter_pool_below_structural_cnp`.

**Output**: Data object (xarray).

---

### P07 — Soil respiration

**Ecological property**: CO₂ efflux from soil microbial decomposition.

**Output**: `soil_respiration` in the data object (xarray); no aggregation needed.

---

### P08 — Net radiation

**Ecological property**: Radiative energy balance at the land surface.

**Output**: `net_radiation` in the data object (xarray); no aggregation needed.

---

### P09 — Animal biomass density

**Ecological property**: Total heterotroph carbon mass per unit area.

**Why it is emergent**: Must multiply `mass_carbon` by `individuals` for each
cohort and sum across all cohorts per time step.  Use
{func}`~virtual_ecosystem.validation_targets.compute_animal_biomass_density`.

**Output**: `animal_cohort_data.csv`.

**Reference**: {cite:t}`harfoot_madingley_2014`.

---

### P10 — Total heterotrophic respiration

**Ecological property**: Combined CO₂ efflux from soil microbes and animals.

**Why it is emergent**: Must sum `soil_respiration` and
`total_animal_respiration`.

**Output**: Data object (xarray).

---

## Secondary emergent targets (Tier 2)

The secondary targets are all emergent.  They are grouped into three
sub-categories: energy flux, animal assimilation, and Madingley-style
allometrics.

| ID | Name | Units | Output source | Reference |
|----|------|-------|---------------|-----------|
| E01 | Latent heat flux | W m⁻² | `latent_heat_flux` | — |
| E02 | Sensible heat flux | W m⁻² | `sensible_heat_flux` | — |
| E03 | Bowen ratio | dimensionless | `sensible_heat_flux`, `latent_heat_flux` | — |
| E04 | Root-to-shoot ratio | dimensionless | `plants_cohort_data.csv` | — |
| A01 | Total animal assimilation rate | kg C m⁻² update⁻¹ | `animal_trophic_interactions.csv` | {cite:t}`harfoot_madingley_2014` |
| A02 | Herbivore assimilation rate | kg C m⁻² update⁻¹ | `animal_trophic_interactions.csv` | {cite:t}`harfoot_madingley_2014` |
| A03 | Predator assimilation rate | kg C m⁻² update⁻¹ | `animal_trophic_interactions.csv` | {cite:t}`harfoot_madingley_2014` |
| A04 | Trophic efficiency | dimensionless | `animal_trophic_interactions.csv` | {cite:t}`harfoot_madingley_2014` |
| M01 | Body mass vs time to maturity | kg vs days | `animal_cohort_data.csv` | {cite:t}`harfoot_madingley_2014` |
| M02 | Body mass vs maturity rate | kg vs day⁻¹ | `animal_cohort_data.csv` | {cite:t}`harfoot_madingley_2014` |
| M03 | Body mass vs abundance (Damuth's Law) | kg vs individuals | `animal_cohort_data.csv` | {cite:t}`harfoot_madingley_2014` |

### Energy flux group

**E01 — Latent heat flux**

The latent heat flux (LE) profile across canopy layers is stored in
`latent_heat_flux` [W m⁻²].  The value at the top canopy layer is the
surface flux that should be compared against eddy-covariance measurements.

**E02 — Sensible heat flux**

The sensible heat flux (H) profile is stored in `sensible_heat_flux` [W m⁻²].

**E03 — Bowen ratio**

The Bowen ratio β = H / LE characterises how net radiation is partitioned
between turbulent fluxes.  Tropical rainforests typically have β < 0.5.
Compute using
{func}`~virtual_ecosystem.validation_targets.compute_bowen_ratio`.

**E04 — Root-to-shoot ratio**

The root-to-shoot ratio (RSR = BGB / AGB) is an emergent allometric property
of the plant community that reflects carbon allocation strategy.  Typical
values for tropical forests are 0.2–0.4.  Compute using
{func}`~virtual_ecosystem.validation_targets.compute_root_to_shoot_ratio`.

---

### Animal assimilation group

These targets are derived from `animal_trophic_interactions.csv`, which records
the carbon, nitrogen, and phosphorus consumed from every resource by every
cohort at each time step.

**A01 — Total animal assimilation rate**

Sum of all C consumed across all cohorts, resource kinds, and cells per time
step.  Compute using
{func}`~virtual_ecosystem.validation_targets.compute_total_animal_assimilation_rate`.

**A02 — Herbivore assimilation rate**

Carbon consumed from non-animal resources (plant tissue, litter, soil pools)
per time step.  Rows in `animal_trophic_interactions.csv` with
`resource_kind != 'cohort'` are summed.  Compute using
{func}`~virtual_ecosystem.validation_targets.compute_herbivore_assimilation_rate`.

**A03 — Predator assimilation rate**

Carbon consumed from prey cohorts (rows with `resource_kind == 'cohort'`) per
time step.  Compute using
{func}`~virtual_ecosystem.validation_targets.compute_predator_assimilation_rate`.

**A04 — Trophic efficiency**

Ratio of predator to herbivore assimilation per time step.  Values are
typically 5–20 % in empirical food webs.  Compute using
{func}`~virtual_ecosystem.validation_targets.compute_trophic_efficiency`.

---

### Madingley-style allometric group

The following three targets mirror validation relationships used by
{cite:t}`harfoot_madingley_2014` to demonstrate that the Madingley model
produces realistic life-history and population-density scaling across
functional groups.

**M01 — Body mass vs time to maturity**

For all mature cohorts (`is_mature == True`), the time taken to reach adult
body mass (`time_to_maturity`) should scale positively with
`largest_mass_achieved`.  Larger animals take longer to mature.  Extract
paired arrays with
{func}`~virtual_ecosystem.validation_targets.body_mass_vs_time_to_maturity`.

**M02 — Body mass vs maturity rate**

The maturity rate (1 / `time_to_maturity`) should scale negatively with body
mass.  This mirrors Figure 2 in {cite:t}`harfoot_madingley_2014`.  Extract
paired arrays with
{func}`~virtual_ecosystem.validation_targets.body_mass_vs_maturity_rate`.

**M03 — Body mass vs abundance (Damuth's Law)**

Damuth's Law predicts that population density ∝ mass⁻⁰·⁷⁵.  Plot
`individuals` against `largest_mass_achieved` on a log–log scale and
check that the slope is approximately −0.75.  Extract paired arrays with
{func}`~virtual_ecosystem.validation_targets.body_mass_vs_abundance`.

---

## Using the Python module

All target definitions and helper functions are in
{mod}`virtual_ecosystem.validation_targets`.

```python
from virtual_ecosystem.validation_targets import (
    PRIMARY_TARGETS,
    SECONDARY_TARGETS,
    EMERGENT_TARGETS,
    ALL_TARGETS,
    get_emergent_targets,
    TargetTier,
)

# List the 7 emergent primary targets
emergent_primary = get_emergent_targets(tier=TargetTier.PRIMARY)
for t in emergent_primary:
    print(t.target_id, t.name)
```

```python
import pandas as pd
from virtual_ecosystem.validation_targets import (
    compute_bowen_ratio,
    compute_evapotranspiration,
    compute_above_ground_biomass,
    compute_animal_biomass_density,
    compute_trophic_efficiency,
    body_mass_vs_time_to_maturity,
    body_mass_vs_maturity_rate,
    body_mass_vs_abundance,
)

# Energy flux example
# (assuming xr_data is an xarray Dataset loaded from the model output)
import numpy as np
bowen = compute_bowen_ratio(
    sensible_heat=xr_data["sensible_heat_flux"].values,
    latent_heat=xr_data["latent_heat_flux"].values,
)

# Animal allometrics example
cohort_df = pd.read_csv("output/animal_cohort_data.csv")
mass, ttm = body_mass_vs_time_to_maturity(cohort_df)
mass, rate = body_mass_vs_maturity_rate(cohort_df)
mass, abund = body_mass_vs_abundance(cohort_df, cell_id=0, time_index=10)

# Trophic efficiency
trophic_df = pd.read_csv("output/animal_trophic_interactions.csv")
efficiency = compute_trophic_efficiency(trophic_df)
```
