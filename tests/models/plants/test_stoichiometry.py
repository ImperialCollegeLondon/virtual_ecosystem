"""Tests for the plant stoichiometry module."""

from types import SimpleNamespace

import numpy as np
import pytest

from virtual_ecosystem.models.plants.stoichiometry import (
    FoliageTissue,
    ReproductiveTissue,
    RootTissue,
    StemStoichiometry,
    WoodTissue,
)


class DummyCommunity:
    """Mock class for a plant community with two cohorts for testing."""

    def __init__(self):
        self.stem_allometry = SimpleNamespace(
            foliage_mass=np.array([50.0, 80.0]),
            stem_mass=np.array([100.0, 150.0]),
            reproductive_tissue_mass=np.array([20.0, 40.0]),
        )
        self.stem_traits = SimpleNamespace(
            zeta=0.1, sla=2.0, p_foliage_for_reproductive_tissue=0.5
        )

        self.n_cohorts = 2
        self.cohorts = type("Cohorts", (), {"pft_names": ["pft1", "pft2"]})


class DummyAllocation:
    """Mock class for allocation with predefined values for testing."""

    def __init__(self):
        self.delta_foliage_mass = np.array([20.0, 10.0])
        self.delta_stem_mass = np.array([10.0, 5.0])
        self.foliage_turnover = np.array([30.0, 15.0])
        self.reproductive_tissue_turnover = np.array([5.0, 2.0])
        self.fine_root_turnover = np.array([3.0, 1.5])


DUMMY_COMMUNITY = DummyCommunity()
DUMMY_ALLOC = DummyAllocation()


@pytest.fixture
def stem_stoichiometry():
    """Helper function to create a StemStoichiometry instance with all tissues."""

    """"""

    foliage = FoliageTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([5.0, 6.0]),
        actual_element_mass=np.array([5.0, 20.0]),
        turnover_ratio=np.array([10.0, 12.0]),
    )
    root = RootTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([5.0, 7.0]),
        actual_element_mass=np.array([10.0, 25.0]),
    )
    wood = WoodTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([10.0, 8.0]),
        actual_element_mass=np.array([5.0, 30.0]),
    )
    repro = ReproductiveTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([4.0, 5.0]),
        actual_element_mass=np.array([8.0, 12.0]),
    )
    return StemStoichiometry(
        "N", [foliage, repro, wood, root], DUMMY_COMMUNITY, SimpleNamespace()
    )


def test_foliage_tissue_functions():
    """Test the FoliageTissue class functions."""

    tissue = FoliageTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([5.0, 6.0]),
        actual_element_mass=np.array([5.0, 20.0]),
        turnover_ratio=np.array([10.0, 12.0]),
    )

    # carbon mass = foliage mass
    assert np.allclose(tissue.carbon_mass, [50.0, 80.0])

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            (50.0 / 5.0) - 5.0,
            (80.0 / 6.0) - 20.0,
        ]
    )
    assert np.allclose(tissue.deficit, expected_deficit)

    # Cx ratio = C / element
    expected_cx = np.array([50.0 / 5.0, 80.0 / 20.0])
    assert np.allclose(tissue.Cx_ratio, expected_cx)

    # growth = ΔC / CN
    expected_growth = np.array([20.0 / 5.0, 10.0 / 6.0])
    assert np.allclose(tissue.element_needed_for_growth(DUMMY_ALLOC), expected_growth)

    # turnover = turnover * (1 / turnover Cx)
    expected_turnover = np.array(
        [
            30.0 * (1 / 10.0),
            15.0 * (1 / 12.0),
        ]
    )
    assert np.allclose(tissue.element_turnover(DUMMY_ALLOC), expected_turnover)


def test_root_tissue_functions():
    """Test the RootTissue class functions."""

    tissue = RootTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([5.0, 7.0]),
        actual_element_mass=np.array([10.0, 25.0]),
    )

    # carbon mass = foliage_mass * zeta * SLA
    expected_carbon = np.array(
        [
            50.0 * 0.1 * 2.0,
            80.0 * 0.1 * 2.0,
        ]
    )
    assert np.allclose(tissue.carbon_mass, expected_carbon)

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            (expected_carbon[0] / 5.0) - 10.0,
            (expected_carbon[1] / 7.0) - 25.0,
        ]
    )
    assert np.allclose(tissue.deficit, expected_deficit)

    # Cx ratio = C / element
    expected_cx = expected_carbon / np.array([10.0, 25.0])
    assert np.allclose(tissue.Cx_ratio, expected_cx)

    # growth = Δ foliage * zeta * SLA / CN
    expected_growth = np.array(
        [
            (20.0 * 0.1 * 2.0) / 5.0,
            (10.0 * 0.1 * 2.0) / 7.0,
        ]
    )
    assert np.allclose(tissue.element_needed_for_growth(DUMMY_ALLOC), expected_growth)

    # turnover = turnover * (1 / Cx)
    expected_turnover = np.array(
        [
            3.0 * (1 / expected_cx[0]),
            1.5 * (1 / expected_cx[1]),
        ]
    )
    assert np.allclose(tissue.element_turnover(DUMMY_ALLOC), expected_turnover)


def test_wood_tissue_functions():
    """Test the WoodTissue class functions."""

    tissue = WoodTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([10.0, 8.0]),
        actual_element_mass=np.array([5.0, 30.0]),
    )

    # carbon mass = stem mass
    assert np.allclose(tissue.carbon_mass, [100.0, 150.0])

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            (100.0 / 10.0) - 5.0,
            (150.0 / 8.0) - 30.0,
        ]
    )
    assert np.allclose(tissue.deficit, expected_deficit)

    # growth = Δ stem / CN
    expected_growth = np.array(
        [
            10.0 / 10.0,
            5.0 / 8.0,
        ]
    )
    assert np.allclose(tissue.element_needed_for_growth(DUMMY_ALLOC), expected_growth)

    # turnover = always 0
    assert np.allclose(tissue.element_turnover(DUMMY_ALLOC), [0.0, 0.0])


def test_reproductive_tissue_functions():
    """Test the ReproductiveTissue class functions."""

    tissue = ReproductiveTissue(
        community=DUMMY_COMMUNITY,
        ideal_ratio=np.array([4.0, 5.0]),
        actual_element_mass=np.array([8.0, 12.0]),
    )

    # carbon mass = reproductive tissue mass
    assert np.allclose(tissue.carbon_mass, [20.0, 40.0])

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            (20.0 / 4.0) - 8.0,
            (40.0 / 5.0) - 12.0,
        ]
    )
    assert np.allclose(tissue.deficit, expected_deficit)

    # Cx ratio = C / element
    expected_cx = np.array([20.0 / 8.0, 40.0 / 12.0])
    assert np.allclose(tissue.Cx_ratio, expected_cx)

    # growth = Δ foliage * p_foliage_for_rep / CN
    expected_growth = np.array(
        [
            (20.0 * 0.5) / 4.0,
            (10.0 * 0.5) / 5.0,
        ]
    )
    assert np.allclose(tissue.element_needed_for_growth(DUMMY_ALLOC), expected_growth)

    # turnover = turnover * (1 / Cx)
    expected_turnover = np.array(
        [
            5.0 * (1 / expected_cx[0]),
            2.0 * (1 / expected_cx[1]),
        ]
    )
    assert np.allclose(tissue.element_turnover(DUMMY_ALLOC), expected_turnover)


def test_total_element_mass_and_deficit(stem_stoichiometry: StemStoichiometry):
    """Test the total element mass and deficit calculations in StemStoichiometry."""

    # total element = sum across tissues
    expected_total = (
        stem_stoichiometry.tissues[0].actual_element_mass
        + stem_stoichiometry.tissues[1].actual_element_mass
        + stem_stoichiometry.tissues[2].actual_element_mass
        + stem_stoichiometry.tissues[3].actual_element_mass
    )
    assert np.allclose(stem_stoichiometry.total_element_mass, expected_total)

    # total deficit = sum across tissues
    expected_deficit = (
        stem_stoichiometry.tissues[0].deficit
        + stem_stoichiometry.tissues[1].deficit
        + stem_stoichiometry.tissues[2].deficit
        + stem_stoichiometry.tissues[3].deficit
    )
    assert np.allclose(stem_stoichiometry.tissue_deficit, expected_deficit)


def test_account_for_growth_updates_element_masses_and_surplus(
    stem_stoichiometry: StemStoichiometry,
):
    """Test that accounting for growth updates element masses and surplus correctly."""

    before = [t.actual_element_mass.copy() for t in stem_stoichiometry.tissues]
    stem_stoichiometry.account_for_growth(DUMMY_ALLOC)
    after = [t.actual_element_mass for t in stem_stoichiometry.tissues]

    # Each tissue should increase by element_needed_for_growth
    for b, a, t in zip(before, after, stem_stoichiometry.tissues):
        expected = b + t.element_needed_for_growth(DUMMY_ALLOC)
        assert np.allclose(a, expected)

    # Surplus should decrease accordingly
    expected_surplus = np.zeros(DUMMY_COMMUNITY.n_cohorts)
    for t in stem_stoichiometry.tissues:
        expected_surplus -= t.element_needed_for_growth(DUMMY_ALLOC)
    assert np.allclose(stem_stoichiometry.element_surplus, expected_surplus)


def test_account_for_element_loss_turnover(stem_stoichiometry: StemStoichiometry):
    """Test account for element loss function in StemStoichiometry."""

    stem_stoichiometry.account_for_element_loss_turnover(DUMMY_ALLOC)

    expected = np.zeros(DUMMY_COMMUNITY.n_cohorts)
    for t in stem_stoichiometry.tissues:
        expected -= t.element_turnover(DUMMY_ALLOC)

    assert np.allclose(stem_stoichiometry.element_surplus, expected)


def test_distribute_deficit(stem_stoichiometry: StemStoichiometry):
    """Test the distribution of a negative element surplus (deficit) across tissues."""

    cohort = 0

    # Set actual element masses to full ideal values
    for tissue in stem_stoichiometry.tissues:
        tissue.actual_element_mass[cohort] = (
            tissue.carbon_mass[cohort] / tissue.ideal_ratio[cohort]
        )

    # Introduce a deficit in element surplus (negative value)
    deficit_to_distribute = (
        -0.4 * stem_stoichiometry.total_element_mass[cohort]
    )  # 40% deficit
    stem_stoichiometry.element_surplus[cohort] = deficit_to_distribute

    # Record actual masses before distribution
    before = np.array(
        [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
    )

    # Compute shares based on initial actual masses
    initial_masses = before.copy()
    total_mass = initial_masses.sum()
    expected_losses = initial_masses / total_mass * -deficit_to_distribute

    # Distribute the deficit
    stem_stoichiometry.distribute_deficit(cohort)

    # Record actual masses after distribution
    after = np.array(
        [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
    )
    total_loss = before.sum() - after.sum()

    # Assertions
    assert np.all(after < before), "Each tissue should have decreased"
    assert stem_stoichiometry.element_surplus[cohort] == 0.0, (
        "Deficit should be fully distributed"
    )
    assert np.allclose(before - after, expected_losses, rtol=1e-12, atol=1e-12), (
        "Losses should match expected proportional distribution"
    )
    assert np.isclose(total_loss, -deficit_to_distribute, rtol=1e-12, atol=1e-12), (
        "Total loss should match the distributed deficit"
    )


def test_distribute_partial_surplus(stem_stoichiometry: StemStoichiometry):
    """Test distribution of a partial surplus across tissues with deficits."""

    cohort = 0

    # Set actual element masses to 50% of ideal to guarantee a positive deficit
    for tissue in stem_stoichiometry.tissues:
        ideal_mass = tissue.carbon_mass[cohort] / tissue.ideal_ratio[cohort]
        tissue.actual_element_mass[cohort] = 0.5 * ideal_mass

    # Compute total deficit and partial surplus
    total_deficit = stem_stoichiometry.tissue_deficit[cohort]
    partial_surplus = total_deficit * 0.4
    stem_stoichiometry.element_surplus[cohort] = partial_surplus

    # Record actual masses before distribution
    before = np.array(
        [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
    )
    ideals = np.array(
        [
            t.carbon_mass[cohort] / t.ideal_ratio[cohort]
            for t in stem_stoichiometry.tissues
        ]
    )

    # Distribute the partial surplus
    stem_stoichiometry.distribute_surplus(cohort)

    # Record actual masses after distribution
    after = np.array(
        [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
    )
    total_gain = after.sum() - before.sum()

    # Assertions
    assert np.all(after > before), "Each tissue should have increased"
    assert np.all(after <= ideals + 1e-12), "No tissue should exceed its ideal mass"
    assert stem_stoichiometry.element_surplus[cohort] == 0.0, (
        "Surplus should be fully consumed"
    )
    assert np.isclose(total_gain, partial_surplus, rtol=1e-12, atol=1e-12), (
        "Total gain should match partial surplus"
    )


def test_distribute_surplus_full(stem_stoichiometry: StemStoichiometry):
    """Test distribution of a full surplus that exceeds all deficits."""

    # lower actuals so there is a deficit
    for t in stem_stoichiometry.tissues:
        t.actual_element_mass[:] *= 0.1

    cohort = 1
    initial_deficits = np.array([t.deficit[cohort] for t in stem_stoichiometry.tissues])
    total_deficit = initial_deficits.sum()

    # give more than enough surplus to cover all deficits
    stem_stoichiometry.element_surplus[cohort] = total_deficit * 2.0

    stem_stoichiometry.distribute_surplus(cohort)

    # all tissues should now be at their ideal ratios
    for t in stem_stoichiometry.tissues:
        expected = t.carbon_mass[cohort] / t.ideal_ratio[cohort]
        assert np.isclose(t.actual_element_mass[cohort], expected)

    # surplus should remain
    assert stem_stoichiometry.element_surplus[cohort] > 0.0


@pytest.mark.parametrize(
    "method,surplus",
    [
        ("distribute_deficit", 5.0),
        ("distribute_surplus", -5.0),
    ],
)
def test_error_triggers(method, surplus, stem_stoichiometry):
    """Test that errors are raised when surplus/deficit conditions are violated."""

    stem_stoichiometry.element_surplus[0] = surplus
    with pytest.raises(ValueError):
        getattr(stem_stoichiometry, method)(0)
