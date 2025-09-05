"""Tests for the Stoichiometry class."""

import numpy as np
import pytest


def test_FoliageTissue__init__(fxt_plants_model, extra_pft_traits):
    """Test the foliage stoichiometry."""
    from virtual_ecosystem.models.plants.stoichiometry import FoliageTissue

    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]
        ideal_ratio = np.array(
            [
                extra_pft_traits.traits[name]["foliage_c_n_ratio"]
                for name in community.cohorts.pft_names
            ]
        )
        tissue_model = FoliageTissue(
            community=community,
            ideal_ratio=ideal_ratio,
            actual_element_mass=community.stem_allometry.foliage_mass * ideal_ratio,
            reclaim_ratio=np.array(
                [
                    extra_pft_traits.traits[name]["leaf_turnover_c_n_ratio"]
                    for name in community.cohorts.pft_names
                ]
            ),
        )

        assert isinstance(tissue_model, FoliageTissue)


def test_from_pft_default_ratios(fxt_plants_model):
    """Test the default ratios in FoliageTissue from PFT."""
    from virtual_ecosystem.models.plants.stoichiometry import FoliageTissue

    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        tissue_model = FoliageTissue.from_pft_default_ratios(
            community=community,
            extra_pft_traits=fxt_plants_model.extra_pft_traits,
            element_name="n",
        )

        assert isinstance(tissue_model, FoliageTissue)


def test_stoichiometry_from_defaults(fxt_plants_model):
    """Test the stoichiometry from defaults."""
    from virtual_ecosystem.models.plants.stoichiometry import StemStoichiometry

    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        stoichiometry = StemStoichiometry.default_init(
            community,
            extra_pft_traits=fxt_plants_model.extra_pft_traits,
            element="N",
        )
        assert isinstance(stoichiometry, StemStoichiometry)


@pytest.mark.parametrize(
    argnames=(
        "classname, carbon_mass, deficit, element_needed_for_growth, "
        "element_turnover, Cx_ratio"
    ),
    argvalues=[
        pytest.param(
            "FoliageTissue",
            [1.00834120e01, 3.27620602e-01, 3.85363977e-03],
            [0, 0, 0],
            [0.01381296, 0.17212982, 0.97911226],
            [-1.44656201e00, -4.70003125e-02, -5.52841526e-04],
            [0.06666667, 0.06666667, 0.06666667],
        ),
    ],
)
def test_Tissue_class_functions(
    fxt_plants_model,
    classname,
    carbon_mass,
    deficit,
    element_needed_for_growth,
    element_turnover,
    Cx_ratio,
    extra_pft_traits,
):
    """Test the carbon mass calculation in FoliageTissue."""
    from pyrealm.demography.tmodel import StemAllocation

    from virtual_ecosystem.models.plants.stoichiometry import FoliageTissue

    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    cell_id = 0
    community = fxt_plants_model.communities[cell_id]
    ideal_ratio = np.array(
        [
            extra_pft_traits.traits[name]["foliage_c_n_ratio"]
            for name in community.cohorts.pft_names
        ]
    )
    tissue_model = FoliageTissue(
        community=community,
        ideal_ratio=ideal_ratio,
        actual_element_mass=community.stem_allometry.foliage_mass * ideal_ratio,
        reclaim_ratio=np.array(
            [
                extra_pft_traits.traits[name]["leaf_turnover_c_n_ratio"]
                for name in community.cohorts.pft_names
            ]
        ),
    )

    stem_allocation = StemAllocation(
        stem_traits=community.stem_traits,
        stem_allometry=community.stem_allometry,
        whole_crown_gpp=fxt_plants_model.per_stem_gpp[cell_id],
    )

    # Assert that the calculated carbon mass matches the expected value
    assert np.allclose(
        tissue_model.carbon_mass,
        carbon_mass,
    )

    assert np.allclose(
        tissue_model.deficit,
        deficit,
    )

    assert np.allclose(
        tissue_model.element_needed_for_growth(stem_allocation),
        element_needed_for_growth,
    )

    assert np.allclose(
        tissue_model.element_turnover(stem_allocation),
        element_turnover,
    )

    assert np.allclose(
        tissue_model.Cx_ratio,
        Cx_ratio,
    )


@pytest.fixture
def fxt_stoichiometry_model(fxt_plants_model):
    """Fixture for the Stoichiometry class."""

    from virtual_ecosystem.models.plants.stoichiometry import StemStoichiometry

    cell_id = 0  # Assuming we are testing for the first cell
    community = fxt_plants_model.communities[cell_id]

    community = fxt_plants_model.communities[cell_id]

    n_stoichiometry = StemStoichiometry.default_init(
        community,
        extra_pft_traits=fxt_plants_model.extra_pft_traits,
        element="N",
    )
    return n_stoichiometry


def test_Stoichiometry__init__(fxt_stoichiometry_model):
    """Test the Stoichiometry class initialization."""

    from virtual_ecosystem.models.plants.stoichiometry import StemStoichiometry

    assert isinstance(fxt_stoichiometry_model, StemStoichiometry)


def test_Stoichiometry_total_element_mass(fxt_stoichiometry_model):
    """Test the total_element_mass method of the Stoichiometry class."""

    # Calculate the total element mass
    total_mass = fxt_stoichiometry_model.total_element_mass

    assert np.allclose(total_mass, [1.42690028e05, 5.00222397e02, 1.01898381e00])


def test_Stoichiometry_tissue_deficit(fxt_stoichiometry_model):
    """Test the tissue_deficit method of the Stoichiometry class."""

    # Calculate the tissue deficit
    tissue_deficit = fxt_stoichiometry_model.tissue_deficit

    expected_deficit = np.array([-3.48223990e04, -1.02544990e02, 4.02427444e-03])
    assert np.allclose(tissue_deficit, expected_deficit)


@pytest.mark.skip(
    reason="Negative growth problem. Return to this test when that problem is fixed."
)
def test_Stoichiometry_account_for_growth(fxt_plants_model, fxt_stoichiometry_model):
    """Test the account_for_growth method of the Stoichiometry class."""

    from virtual_ecosystem.models.plants.stoichiometry import StemAllocation

    # Create a StemAllocation object
    cell_id = 0  # Assuming we are testing for the first cell
    community = fxt_plants_model.communities[cell_id]
    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    stem_allocation = StemAllocation(
        stem_traits=community.stem_traits,
        stem_allometry=community.stem_allometry,
        whole_crown_gpp=fxt_plants_model.per_stem_gpp[cell_id],
    )

    assert np.allclose(
        fxt_stoichiometry_model.total_element_mass,
        [1.31887368e05, 4.35408760e02, 5.93227761e-01],
    )

    # Account for growth
    fxt_stoichiometry_model.account_for_growth(stem_allocation)

    assert np.all(
        fxt_stoichiometry_model.total_element_mass
        >= [1.31887368e05, 4.35408760e02, 5.93227761e-01]
    )


def test_Stoichiometry_account_for_element_loss_turnover(
    fxt_plants_model, fxt_stoichiometry_model
):
    """Test the account_for_element_loss_turnover method of the Stoichiometry class."""

    from virtual_ecosystem.models.plants.stoichiometry import StemAllocation

    # Create a StemAllocation object
    cell_id = 0  # Assuming we are testing for the first cell
    community = fxt_plants_model.communities[cell_id]
    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    stem_allocation = StemAllocation(
        stem_traits=community.stem_traits,
        stem_allometry=community.stem_allometry,
        whole_crown_gpp=fxt_plants_model.per_stem_gpp[cell_id],
    )

    assert np.allclose(fxt_stoichiometry_model.element_surplus, [0.0, 0.0, 0.0])
    fxt_stoichiometry_model.account_for_element_loss_turnover(stem_allocation)

    # The surplus should always be negative after accounting for turnover
    assert np.all(fxt_stoichiometry_model.element_surplus <= [0.0, 0.0, 0.0])


def test_Stoichiometry_distribute_deficit(fxt_stoichiometry_model):
    """Test the distribute_deficit method of the Stoichiometry class.

    NOTE: This method should have a more robust test with a more deliberate test value.
    This will be easier to implement once growth is functioning.
    """

    # Distribute the deficit
    fxt_stoichiometry_model.distribute_deficit(0)

    assert np.allclose(fxt_stoichiometry_model.element_surplus[0], [0])


def test_Stoichiometry_distrubte_surplus(fxt_stoichiometry_model):
    """Test the distribute_surplus method of the Stoichiometry class.

    NOTE: This method should have a more robust test with a more deliberate test value.
    This will be easier to implement once growth is functioning.
    """

    fxt_stoichiometry_model.distribute_surplus(0)

    assert fxt_stoichiometry_model.element_surplus[0] >= 0
