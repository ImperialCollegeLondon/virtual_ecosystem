import numpy as np  # noqa: D100

from virtual_ecosystem.models.plants.stochiometry import (
    FoliageTissue,
    ReproductiveTissue,
    RootTissue,
    WoodTissue,
)


class DummyStemAllometry:
    """Mock class for stem allometry with predefined masses for testing."""

    foliage_mass = np.array([50.0, 80.0])
    stem_mass = np.array([100.0, 150.0])
    reproductive_tissue_mass = np.array([20.0, 40.0])


class DummyStemTraits:
    """Mock class for stem traits with predefined stoichiometric ratios for testing."""

    zeta = 0.1
    sla = 2.0
    p_foliage_for_reproductive_tissue = 0.5


class DummyCommunity:
    """Mock class for a plant community with two cohorts for testing."""

    def __init__(self):
        self.stem_allometry = DummyStemAllometry()
        self.stem_traits = DummyStemTraits()
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


dummy_community = DummyCommunity()
dummy_alloc = DummyAllocation()


def test_foliage_tissue_functions():
    """Test the FoliageTissue class functions."""

    tissue = FoliageTissue(
        community=dummy_community,
        ideal_ratio=np.array([5.0, 6.0]),
        actual_element_mass=np.array([5.0, 20.0]),
        reclaim_ratio=np.array([10.0, 12.0]),
    )

    # carbon mass = foliage mass
    assert np.allclose(tissue.carbon_mass, [50.0, 80.0])

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            5.0 - (50.0 / 5.0),
            20.0 - (80.0 / 6.0),
        ]
    )
    assert np.allclose(tissue.deficit, expected_deficit)

    # Cx ratio = C / element
    expected_cx = np.array([50.0 / 5.0, 80.0 / 20.0])
    assert np.allclose(tissue.Cx_ratio, expected_cx)

    # growth = ΔC / CN
    expected_growth = np.array([20.0 / 5.0, 10.0 / 6.0])
    assert np.allclose(tissue.element_needed_for_growth(dummy_alloc), expected_growth)

    # turnover = turnover * (1/reclaim - 1/Cx)
    expected_turnover = np.array(
        [
            30.0 * ((1 / 10.0) - (1 / (50.0 / 5.0))),
            15.0 * ((1 / 12.0) - (1 / (80.0 / 20.0))),
        ]
    )
    assert np.allclose(tissue.element_turnover(dummy_alloc), expected_turnover)


def test_root_tissue_functions():
    """Test the RootTissue class functions."""

    tissue = RootTissue(
        community=dummy_community,
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
            10.0 - (expected_carbon[0] / 5.0),
            25.0 - (expected_carbon[1] / 7.0),
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
    assert np.allclose(tissue.element_needed_for_growth(dummy_alloc), expected_growth)

    # turnover = turnover * (1 / Cx)
    expected_turnover = np.array(
        [
            3.0 * (1 / expected_cx[0]),
            1.5 * (1 / expected_cx[1]),
        ]
    )
    assert np.allclose(tissue.element_turnover(dummy_alloc), expected_turnover)


def test_wood_tissue_functions():
    """Test the WoodTissue class functions."""

    tissue = WoodTissue(
        community=dummy_community,
        ideal_ratio=np.array([10.0, 8.0]),
        actual_element_mass=np.array([5.0, 30.0]),
    )

    # carbon mass = stem mass
    assert np.allclose(tissue.carbon_mass, [100.0, 150.0])

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            5.0 - (100.0 / 10.0),
            30.0 - (150.0 / 8.0),
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
    assert np.allclose(tissue.element_needed_for_growth(dummy_alloc), expected_growth)

    # turnover = always 0
    assert np.allclose(tissue.element_turnover(dummy_alloc), [0.0, 0.0])


def test_reproductive_tissue_functions():
    """Test the ReproductiveTissue class functions."""

    tissue = ReproductiveTissue(
        community=dummy_community,
        ideal_ratio=np.array([4.0, 5.0]),
        actual_element_mass=np.array([8.0, 12.0]),
    )

    # carbon mass = reproductive tissue mass
    assert np.allclose(tissue.carbon_mass, [20.0, 40.0])

    # deficit = element - (C / CN)
    expected_deficit = np.array(
        [
            8.0 - (20.0 / 4.0),
            12.0 - (40.0 / 5.0),
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
    assert np.allclose(tissue.element_needed_for_growth(dummy_alloc), expected_growth)

    # turnover = turnover * (1 / Cx)
    expected_turnover = np.array(
        [
            5.0 * (1 / expected_cx[0]),
            2.0 * (1 / expected_cx[1]),
        ]
    )
    assert np.allclose(tissue.element_turnover(dummy_alloc), expected_turnover)
