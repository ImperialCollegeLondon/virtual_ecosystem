"""Tests for virtual_ecosystem.validation_targets.

Covers:
* Structural integrity of PRIMARY_TARGETS and SECONDARY_TARGETS
* Correct classification of emergent vs non-emergent targets
* EMERGENT_TARGETS and get_emergent_targets() filter helper
* All metric helper functions (energy, plant biomass, animal assimilation,
  Madingley allometrics)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from virtual_ecosystem.validation_targets import (
    ALL_TARGETS,
    EMERGENT_TARGETS,
    PRIMARY_TARGETS,
    SECONDARY_TARGETS,
    TargetTier,
    ValidationTarget,
    body_mass_vs_abundance,
    body_mass_vs_maturity_rate,
    body_mass_vs_time_to_maturity,
    compute_above_ground_biomass,
    compute_animal_biomass_density,
    compute_below_ground_biomass,
    compute_bowen_ratio,
    compute_evapotranspiration,
    compute_herbivore_assimilation_rate,
    compute_predator_assimilation_rate,
    compute_root_to_shoot_ratio,
    compute_total_animal_assimilation_rate,
    compute_trophic_efficiency,
    get_emergent_targets,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_trophic_df() -> pd.DataFrame:
    """Minimal trophic interactions DataFrame with two time steps.

    One row per time step of herbivory (resource_kind != 'cohort')
    and one row of predation (resource_kind == 'cohort').
    """
    return pd.DataFrame(
        {
            "time_index": [0, 0, 1, 1],
            "resource_kind": ["plant", "cohort", "litter", "cohort"],
            "C": [10.0, 2.0, 8.0, 3.0],
            "N": [1.0, 0.2, 0.8, 0.3],
            "P": [0.1, 0.02, 0.08, 0.03],
        }
    )


@pytest.fixture()
def minimal_cohort_df() -> pd.DataFrame:
    """Minimal animal cohort DataFrame with mature and immature cohorts."""
    return pd.DataFrame(
        {
            "time_index": [0, 0, 0, 0],
            "centroid_key": [0, 0, 1, 1],
            "is_mature": [True, True, False, True],
            "largest_mass_achieved": [10.0, 50.0, 5.0, 100.0],
            "time_to_maturity": [365.0, 730.0, 0.0, 1460.0],
            "individuals": [100, 20, 500, 5],
            "mass_carbon": [5.0, 25.0, 2.5, 50.0],
        }
    )


@pytest.fixture()
def minimal_plant_df() -> pd.DataFrame:
    """Minimal plant cohort DataFrame for two cells across two time steps."""
    return pd.DataFrame(
        {
            "cell_id": [0, 0, 1, 1, 0, 0, 1, 1],
            "time": [
                "2000-01-01", "2000-01-01",
                "2000-01-01", "2000-01-01",
                "2000-02-01", "2000-02-01",
                "2000-02-01", "2000-02-01",
            ],
            "biomass_foliage_carbon_mass": [2.0, 1.5, 3.0, 2.5, 2.1, 1.6, 3.1, 2.6],
            "biomass_stem_carbon_mass": [8.0, 6.0, 10.0, 9.0, 8.2, 6.2, 10.2, 9.2],
            "biomass_root_carbon_mass": [1.0, 0.8, 1.5, 1.2, 1.1, 0.9, 1.6, 1.3],
        }
    )


# ---------------------------------------------------------------------------
# Target list structural tests
# ---------------------------------------------------------------------------


class TestPrimaryTargets:
    """Tests for the PRIMARY_TARGETS list."""

    def test_count_is_ten(self):
        """There must be exactly 10 primary targets."""
        assert len(PRIMARY_TARGETS) == 10

    def test_all_are_primary_tier(self):
        """Every entry must have tier == PRIMARY."""
        for t in PRIMARY_TARGETS:
            assert t.tier is TargetTier.PRIMARY, (
                f"Target {t.target_id} has tier {t.tier!r}, expected PRIMARY"
            )

    def test_ids_are_unique(self):
        """All target IDs must be unique."""
        ids = [t.target_id for t in PRIMARY_TARGETS]
        assert len(ids) == len(set(ids))

    def test_ids_start_with_p(self):
        """Primary target IDs must start with 'P'."""
        for t in PRIMARY_TARGETS:
            assert t.target_id.startswith("P"), (
                f"Primary target ID {t.target_id!r} does not start with 'P'"
            )

    def test_required_fields_populated(self):
        """Every target must have a non-empty name, ecological_property, and description."""
        for t in PRIMARY_TARGETS:
            assert t.name, f"Target {t.target_id} has empty name"
            assert t.ecological_property, (
                f"Target {t.target_id} has empty ecological_property"
            )
            assert t.description, f"Target {t.target_id} has empty description"
            assert t.output_variables, (
                f"Target {t.target_id} has no output_variables"
            )
            assert t.output_files, f"Target {t.target_id} has no output_files"
            assert t.units, f"Target {t.target_id} has empty units"

    def test_emergent_flag_values(self):
        """P04, P07, P08 must be non-emergent; others must be emergent."""
        non_emergent_ids = {"P04", "P07", "P08"}
        emergent_ids = {"P01", "P02", "P03", "P05", "P06", "P09", "P10"}
        for t in PRIMARY_TARGETS:
            if t.target_id in non_emergent_ids:
                assert not t.is_emergent, (
                    f"Target {t.target_id} should not be emergent"
                )
            elif t.target_id in emergent_ids:
                assert t.is_emergent, (
                    f"Target {t.target_id} should be emergent"
                )

    def test_emergent_descriptions_mention_aggregation(self):
        """Emergent primary targets should explain why they require aggregation."""
        keywords = ("aggregat", "sum", "comput", "deriv")
        for t in PRIMARY_TARGETS:
            if t.is_emergent:
                lower_desc = t.description.lower()
                assert any(kw in lower_desc for kw in keywords), (
                    f"Emergent target {t.target_id} description does not explain "
                    f"why it is emergent"
                )


class TestSecondaryTargets:
    """Tests for the SECONDARY_TARGETS list."""

    def test_all_are_secondary_tier(self):
        """Every entry must have tier == SECONDARY."""
        for t in SECONDARY_TARGETS:
            assert t.tier is TargetTier.SECONDARY, (
                f"Target {t.target_id} has tier {t.tier!r}, expected SECONDARY"
            )

    def test_all_are_emergent(self):
        """All secondary targets must have is_emergent == True."""
        for t in SECONDARY_TARGETS:
            assert t.is_emergent, (
                f"Secondary target {t.target_id} has is_emergent=False"
            )

    def test_ids_are_unique(self):
        """All secondary target IDs must be unique."""
        ids = [t.target_id for t in SECONDARY_TARGETS]
        assert len(ids) == len(set(ids))

    def test_ids_match_group_prefix(self):
        """Secondary IDs must start with 'E', 'A', or 'M'."""
        for t in SECONDARY_TARGETS:
            assert t.target_id[0] in {"E", "A", "M"}, (
                f"Secondary target ID {t.target_id!r} has unexpected prefix"
            )

    def test_madingley_targets_cite_harfoot(self):
        """M-group targets must reference harfoot_madingley_2014."""
        for t in SECONDARY_TARGETS:
            if t.target_id.startswith("M"):
                assert "harfoot_madingley_2014" in t.reference, (
                    f"Target {t.target_id} does not cite harfoot_madingley_2014"
                )


class TestAllAndEmergentLists:
    """Tests for ALL_TARGETS, EMERGENT_TARGETS, and get_emergent_targets()."""

    def test_all_targets_count(self):
        """ALL_TARGETS must equal PRIMARY + SECONDARY."""
        assert len(ALL_TARGETS) == len(PRIMARY_TARGETS) + len(SECONDARY_TARGETS)

    def test_all_targets_uniqueness(self):
        """No duplicate IDs across all targets."""
        ids = [t.target_id for t in ALL_TARGETS]
        assert len(ids) == len(set(ids))

    def test_emergent_targets_are_subset_of_all(self):
        """EMERGENT_TARGETS must be a subset of ALL_TARGETS."""
        emergent_ids = {t.target_id for t in EMERGENT_TARGETS}
        all_ids = {t.target_id for t in ALL_TARGETS}
        assert emergent_ids <= all_ids

    def test_emergent_targets_all_flagged(self):
        """Every entry in EMERGENT_TARGETS must have is_emergent == True."""
        for t in EMERGENT_TARGETS:
            assert t.is_emergent

    def test_non_emergent_primary_not_in_emergent_list(self):
        """P04, P07, P08 must not appear in EMERGENT_TARGETS."""
        non_emergent_ids = {"P04", "P07", "P08"}
        emergent_ids = {t.target_id for t in EMERGENT_TARGETS}
        overlap = non_emergent_ids & emergent_ids
        assert not overlap, (
            f"Non-emergent primary targets found in EMERGENT_TARGETS: {overlap}"
        )

    def test_get_emergent_targets_no_filter(self):
        """get_emergent_targets() with no arguments must equal EMERGENT_TARGETS."""
        assert get_emergent_targets() == EMERGENT_TARGETS

    def test_get_emergent_targets_primary_filter(self):
        """get_emergent_targets(tier=PRIMARY) must return only emergent primary targets."""
        result = get_emergent_targets(tier=TargetTier.PRIMARY)
        for t in result:
            assert t.tier is TargetTier.PRIMARY
            assert t.is_emergent

    def test_get_emergent_targets_secondary_filter(self):
        """get_emergent_targets(tier=SECONDARY) must equal SECONDARY_TARGETS."""
        result = get_emergent_targets(tier=TargetTier.SECONDARY)
        assert result == SECONDARY_TARGETS

    def test_emergent_primary_count(self):
        """Exactly 7 of the 10 primary targets must be emergent."""
        emergent_primary = get_emergent_targets(tier=TargetTier.PRIMARY)
        assert len(emergent_primary) == 7


# ---------------------------------------------------------------------------
# Energy flux helper function tests
# ---------------------------------------------------------------------------


class TestComputeBowenRatio:
    """Tests for compute_bowen_ratio."""

    def test_basic_ratio(self):
        """Ratio should equal H / LE for positive inputs."""
        result = compute_bowen_ratio(
            sensible_heat=np.array([100.0, 50.0]),
            latent_heat=np.array([200.0, 100.0]),
        )
        np.testing.assert_allclose(result, [0.5, 0.5])

    def test_zero_latent_heat_gives_nan(self):
        """Zero latent heat must return NaN."""
        result = compute_bowen_ratio(
            sensible_heat=np.array([100.0]),
            latent_heat=np.array([0.0]),
        )
        assert np.isnan(result[0])

    def test_negative_latent_heat_gives_nan(self):
        """Negative latent heat must return NaN."""
        result = compute_bowen_ratio(
            sensible_heat=np.array([50.0]),
            latent_heat=np.array([-10.0]),
        )
        assert np.isnan(result[0])

    def test_series_input(self):
        """Accepts pandas Series."""
        result = compute_bowen_ratio(
            sensible_heat=pd.Series([100.0]),
            latent_heat=pd.Series([400.0]),
        )
        np.testing.assert_allclose(result, [0.25])

    def test_scalar_arrays_preserved(self):
        """Single-element arrays return single-element result."""
        result = compute_bowen_ratio(
            sensible_heat=np.array([30.0]),
            latent_heat=np.array([120.0]),
        )
        assert result.shape == (1,)


class TestComputeEvapotranspiration:
    """Tests for compute_evapotranspiration."""

    def test_sums_components(self):
        """ET must equal transpiration + soil_evap + canopy_evap."""
        result = compute_evapotranspiration(
            transpiration=np.array([5.0, 3.0]),
            soil_evaporation=np.array([1.0, 0.5]),
            canopy_evaporation=np.array([0.5, 0.2]),
        )
        np.testing.assert_allclose(result, [6.5, 3.7])

    def test_zeros(self):
        """All-zero inputs must return zero."""
        result = compute_evapotranspiration(
            transpiration=np.zeros(3),
            soil_evaporation=np.zeros(3),
            canopy_evaporation=np.zeros(3),
        )
        np.testing.assert_allclose(result, np.zeros(3))

    def test_series_input(self):
        """Accepts pandas Series."""
        result = compute_evapotranspiration(
            transpiration=pd.Series([2.0]),
            soil_evaporation=pd.Series([1.0]),
            canopy_evaporation=pd.Series([0.5]),
        )
        np.testing.assert_allclose(result, [3.5])


# ---------------------------------------------------------------------------
# Plant biomass helper function tests
# ---------------------------------------------------------------------------


class TestComputeAboveGroundBiomass:
    """Tests for compute_above_ground_biomass."""

    def test_sums_foliage_and_stem(self, minimal_plant_df):
        """AGB must equal foliage + stem mass per (cell_id, time) group."""
        result = compute_above_ground_biomass(minimal_plant_df)
        # cell 0, time 2000-01-01: (2+1.5) + (8+6) = 17.5
        assert result.loc[(0, "2000-01-01")] == pytest.approx(17.5)
        # cell 1, time 2000-01-01: (3+2.5) + (10+9) = 24.5
        assert result.loc[(1, "2000-01-01")] == pytest.approx(24.5)

    def test_missing_column_raises(self, minimal_plant_df):
        """Missing required column must raise KeyError."""
        df = minimal_plant_df.drop(columns=["biomass_foliage_carbon_mass"])
        with pytest.raises(KeyError, match="biomass_foliage_carbon_mass"):
            compute_above_ground_biomass(df)


class TestComputeBelowGroundBiomass:
    """Tests for compute_below_ground_biomass."""

    def test_sums_root_mass(self, minimal_plant_df):
        """BGB must equal the sum of root masses per group."""
        result = compute_below_ground_biomass(minimal_plant_df)
        # cell 0, time 2000-01-01: 1.0 + 0.8 = 1.8
        assert result.loc[(0, "2000-01-01")] == pytest.approx(1.8)

    def test_missing_column_raises(self, minimal_plant_df):
        """Missing column must raise KeyError."""
        df = minimal_plant_df.drop(columns=["biomass_root_carbon_mass"])
        with pytest.raises(KeyError, match="biomass_root_carbon_mass"):
            compute_below_ground_biomass(df)


class TestComputeRootToShootRatio:
    """Tests for compute_root_to_shoot_ratio."""

    def test_ratio_value(self, minimal_plant_df):
        """RSR must equal BGB / AGB."""
        agb = compute_above_ground_biomass(minimal_plant_df)
        bgb = compute_below_ground_biomass(minimal_plant_df)
        rsr = compute_root_to_shoot_ratio(minimal_plant_df)
        # All values should be positive
        assert (rsr > 0).all()
        # Verify numerical equivalence
        for idx in rsr.index:
            expected = bgb.loc[idx] / agb.loc[idx]
            assert rsr.loc[idx] == pytest.approx(expected)

    def test_zero_agb_gives_nan(self):
        """Zero AGB must give NaN RSR."""
        df = pd.DataFrame(
            {
                "cell_id": [0],
                "time": ["2000-01-01"],
                "biomass_foliage_carbon_mass": [0.0],
                "biomass_stem_carbon_mass": [0.0],
                "biomass_root_carbon_mass": [1.0],
            }
        )
        rsr = compute_root_to_shoot_ratio(df)
        assert rsr.isna().all()


# ---------------------------------------------------------------------------
# Animal assimilation helper function tests
# ---------------------------------------------------------------------------


class TestComputeTotalAnimalAssimilationRate:
    """Tests for compute_total_animal_assimilation_rate."""

    def test_sums_all_c_per_time_step(self, minimal_trophic_df):
        """Total C must equal the sum of all C values per time_index."""
        result = compute_total_animal_assimilation_rate(minimal_trophic_df)
        # time 0: 10 + 2 = 12; time 1: 8 + 3 = 11
        assert result.loc[0] == pytest.approx(12.0)
        assert result.loc[1] == pytest.approx(11.0)

    def test_missing_column_raises(self, minimal_trophic_df):
        """Missing 'C' column must raise KeyError."""
        df = minimal_trophic_df.drop(columns=["C"])
        with pytest.raises(KeyError, match="'C'"):
            compute_total_animal_assimilation_rate(df)


class TestComputeHerbivoreAssimilationRate:
    """Tests for compute_herbivore_assimilation_rate."""

    def test_excludes_cohort_rows(self, minimal_trophic_df):
        """Must sum only rows where resource_kind != 'cohort'."""
        result = compute_herbivore_assimilation_rate(minimal_trophic_df)
        # time 0: 10.0 (plant); time 1: 8.0 (litter)
        assert result.loc[0] == pytest.approx(10.0)
        assert result.loc[1] == pytest.approx(8.0)

    def test_empty_after_filter_returns_empty(self):
        """All-predation trophic DataFrame must return empty Series."""
        df = pd.DataFrame(
            {
                "time_index": [0, 0],
                "resource_kind": ["cohort", "cohort"],
                "C": [5.0, 3.0],
            }
        )
        result = compute_herbivore_assimilation_rate(df)
        assert result.empty


class TestComputePredatorAssimilationRate:
    """Tests for compute_predator_assimilation_rate."""

    def test_includes_only_cohort_rows(self, minimal_trophic_df):
        """Must sum only rows where resource_kind == 'cohort'."""
        result = compute_predator_assimilation_rate(minimal_trophic_df)
        # time 0: 2.0; time 1: 3.0
        assert result.loc[0] == pytest.approx(2.0)
        assert result.loc[1] == pytest.approx(3.0)

    def test_no_predation_returns_empty(self):
        """All-herbivory DataFrame must return empty Series."""
        df = pd.DataFrame(
            {
                "time_index": [0],
                "resource_kind": ["plant"],
                "C": [5.0],
            }
        )
        result = compute_predator_assimilation_rate(df)
        assert result.empty


class TestComputeTrophicEfficiency:
    """Tests for compute_trophic_efficiency."""

    def test_ratio_value(self, minimal_trophic_df):
        """Efficiency must equal predator / herbivore assimilation."""
        result = compute_trophic_efficiency(minimal_trophic_df)
        assert result.loc[0] == pytest.approx(2.0 / 10.0)
        assert result.loc[1] == pytest.approx(3.0 / 8.0)

    def test_zero_herbivory_gives_nan(self):
        """Zero herbivory must produce NaN efficiency."""
        df = pd.DataFrame(
            {
                "time_index": [0],
                "resource_kind": ["cohort"],
                "C": [5.0],
            }
        )
        result = compute_trophic_efficiency(df)
        # herbivory is 0, so efficiency should be NaN
        assert result.loc[0] is np.nan or (
            0 not in result.index or np.isnan(result.loc[0])
        )


# ---------------------------------------------------------------------------
# Madingley-style allometric helper function tests
# ---------------------------------------------------------------------------


class TestBodyMassVsTimeToMaturity:
    """Tests for body_mass_vs_time_to_maturity."""

    def test_returns_only_mature_rows(self, minimal_cohort_df):
        """Must include only rows where is_mature == True."""
        mass, ttm = body_mass_vs_time_to_maturity(minimal_cohort_df)
        # 3 rows are mature (is_mature=True) but one has time_to_maturity=0
        # (shouldn't happen in a real run but we only keep positive ttm)
        assert len(mass) == len(ttm)
        assert all(m > 0 for m in mass)
        assert all(t > 0 for t in ttm)

    def test_excludes_immature_cohorts(self, minimal_cohort_df):
        """Cohorts with is_mature=False must not appear in output."""
        mass, ttm = body_mass_vs_time_to_maturity(minimal_cohort_df)
        # immature cohort has mass 5.0, should not appear
        assert 5.0 not in mass

    def test_missing_column_raises(self, minimal_cohort_df):
        """Missing 'is_mature' column must raise KeyError."""
        df = minimal_cohort_df.drop(columns=["is_mature"])
        with pytest.raises(KeyError, match="is_mature"):
            body_mass_vs_time_to_maturity(df)

    def test_no_mature_cohorts_returns_empty_arrays(self):
        """All-immature DataFrame must return empty arrays."""
        df = pd.DataFrame(
            {
                "is_mature": [False, False],
                "largest_mass_achieved": [10.0, 20.0],
                "time_to_maturity": [0.0, 0.0],
            }
        )
        mass, ttm = body_mass_vs_time_to_maturity(df)
        assert len(mass) == 0
        assert len(ttm) == 0


class TestBodyMassVsMaturityRate:
    """Tests for body_mass_vs_maturity_rate."""

    def test_maturity_rate_is_inverse_of_ttm(self, minimal_cohort_df):
        """Maturity rate must equal 1 / time_to_maturity."""
        mass, rate = body_mass_vs_maturity_rate(minimal_cohort_df)
        _, ttm = body_mass_vs_time_to_maturity(minimal_cohort_df)
        np.testing.assert_allclose(rate, 1.0 / ttm)

    def test_larger_mass_tends_lower_rate(self, minimal_cohort_df):
        """In a simple dataset, heavier cohorts should have lower maturity rates."""
        mass, rate = body_mass_vs_maturity_rate(minimal_cohort_df)
        # Sort by mass and confirm rates are decreasing
        sort_idx = np.argsort(mass)
        sorted_rate = rate[sort_idx]
        assert sorted_rate[0] >= sorted_rate[-1]


class TestBodyMassVsAbundance:
    """Tests for body_mass_vs_abundance."""

    def test_returns_positive_values(self, minimal_cohort_df):
        """All returned mass and individual values must be positive."""
        mass, abund = body_mass_vs_abundance(minimal_cohort_df)
        assert all(m > 0 for m in mass)
        assert all(a > 0 for a in abund)

    def test_cell_id_filter(self, minimal_cohort_df):
        """cell_id filter must restrict to centroid_key == cell_id."""
        mass_all, _ = body_mass_vs_abundance(minimal_cohort_df)
        mass_cell0, _ = body_mass_vs_abundance(minimal_cohort_df, cell_id=0)
        # Cell 0 has 2 cohorts in the fixture
        assert len(mass_cell0) == 2
        assert len(mass_all) > len(mass_cell0)

    def test_time_index_filter(self, minimal_cohort_df):
        """time_index filter must restrict to the given time step."""
        mass, abund = body_mass_vs_abundance(minimal_cohort_df, time_index=0)
        assert len(mass) == len(abund)
        # The fixture only has time_index=0, so all rows should be returned
        mass_all, _ = body_mass_vs_abundance(minimal_cohort_df)
        assert len(mass) == len(mass_all)

    def test_missing_centroid_key_raises_with_cell_id_filter(self, minimal_cohort_df):
        """Passing cell_id without centroid_key column must raise KeyError."""
        df = minimal_cohort_df.drop(columns=["centroid_key"])
        with pytest.raises(KeyError, match="centroid_key"):
            body_mass_vs_abundance(df, cell_id=0)


class TestComputeAnimalBiomassDensity:
    """Tests for compute_animal_biomass_density."""

    def test_mass_times_individuals(self, minimal_cohort_df):
        """Total biomass must equal sum of mass_carbon * individuals per time_index."""
        result = compute_animal_biomass_density(minimal_cohort_df)
        # time 0: (5*100) + (25*20) + (2.5*500) + (50*5)
        #       = 500 + 500 + 1250 + 250 = 2500
        assert result.loc[0] == pytest.approx(2500.0)

    def test_missing_column_raises(self, minimal_cohort_df):
        """Missing 'mass_carbon' must raise KeyError."""
        df = minimal_cohort_df.drop(columns=["mass_carbon"])
        with pytest.raises(KeyError, match="mass_carbon"):
            compute_animal_biomass_density(df)
