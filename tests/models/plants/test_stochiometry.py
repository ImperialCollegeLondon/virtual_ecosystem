"""Tests for the Stochiometry class."""

import numpy as np
import pytest


def test_FoliageTissue__init__(fxt_plants_model):
    """Test the foliage stochiometry."""
    from virtual_ecosystem.models.plants.stochiometry import FoliageTissue

    plant_consts = fxt_plants_model.model_constants
    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        tissue_model = FoliageTissue(
            community=community,
            ideal_ratio=np.full(community.n_cohorts, plant_consts.foliage_c_n_ratio),
            actual_element_mass=community.stem_allometry.foliage_mass
            * plant_consts.foliage_c_n_ratio,
            reclaim_ratio=plant_consts.leaf_turnover_c_n_ratio,
        )

        assert isinstance(tissue_model, FoliageTissue)


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
            [-0.35486191, 0.02330898, 0.87583064],
            [-9.83256242e02, -3.19470237e01, -3.75777103e-01],
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
):
    """Test the carbon mass calculation in FoliageTissue."""
    from pyrealm.demography.tmodel import StemAllocation

    from virtual_ecosystem.models.plants.stochiometry import FoliageTissue

    plant_consts = fxt_plants_model.model_constants
    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    cell_id = 0
    community = fxt_plants_model.communities[cell_id]
    tissue_model = FoliageTissue(
        community=community,
        ideal_ratio=np.full(community.n_cohorts, plant_consts.foliage_c_n_ratio),
        actual_element_mass=community.stem_allometry.foliage_mass
        * plant_consts.foliage_c_n_ratio,
        reclaim_ratio=plant_consts.leaf_turnover_c_n_ratio,
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
def fxt_stochiometry_model(fxt_plants_model):
    """Fixture for the Stochiometry class."""

    from virtual_ecosystem.models.plants.stochiometry import (
        FoliageTissue,
        ReproductiveTissue,
        RootTissue,
        StemStochiometry,
        WoodTissue,
    )

    plant_consts = fxt_plants_model.model_constants
    cell_id = 0  # Assuming we are testing for the first cell
    community = fxt_plants_model.communities[cell_id]

    n_stochiometry = StemStochiometry(
        element="N",
        tissues=[
            FoliageTissue(
                community=community,
                ideal_ratio=np.full(
                    community.n_cohorts,
                    plant_consts.foliage_c_n_ratio,
                ),
                actual_element_mass=community.stem_allometry.foliage_mass
                * plant_consts.foliage_c_n_ratio,
                reclaim_ratio=plant_consts.leaf_turnover_c_n_ratio,
            ),
            RootTissue(
                community=community,
                ideal_ratio=np.full(
                    community.n_cohorts,
                    plant_consts.root_turnover_c_n_ratio,
                ),
                actual_element_mass=plant_consts.root_turnover_c_n_ratio
                * community.stem_traits.zeta
                * community.stem_allometry.foliage_mass,
            ),
            WoodTissue(
                community=community,
                ideal_ratio=np.full(
                    community.n_cohorts,
                    plant_consts.deadwood_c_n_ratio,
                ),
                actual_element_mass=plant_consts.deadwood_c_n_ratio
                * community.stem_allometry.stem_mass,
            ),
            ReproductiveTissue(
                community=community,
                ideal_ratio=np.full(
                    community.n_cohorts,
                    plant_consts.plant_reproductive_tissue_turnover_c_n_ratio,
                ),
                actual_element_mass=community.stem_allometry.reproductive_tissue_mass
                * plant_consts.plant_reproductive_tissue_turnover_c_n_ratio,
            ),
        ],
        community=community,
    )
    return n_stochiometry


def test_Stochiometry__init__(fxt_stochiometry_model):
    """Test the Stochiometry class initialization."""

    from virtual_ecosystem.models.plants.stochiometry import StemStochiometry

    assert isinstance(fxt_stochiometry_model, StemStochiometry)


def test_Stochiometry_total_element_mass(fxt_stochiometry_model):
    """Test the total_element_mass method of the Stochiometry class."""

    # Calculate the total element mass
    total_mass = fxt_stochiometry_model.total_element_mass

    assert np.allclose(total_mass, [1.31887368e05, 4.35408760e02, 5.93227761e-01])


def test_Stochiometry_tissue_deficit(fxt_stochiometry_model):
    """Test the tissue_deficit method of the Stochiometry class."""

    # Calculate the tissue deficit
    tissue_deficit = fxt_stochiometry_model.tissue_deficit

    expected_deficit = np.array([1.01616593e03, 3.30162938e01, 3.88354401e-01])
    assert np.allclose(tissue_deficit, expected_deficit)


@pytest.mark.skip(
    reason="Negative growth problem. Return to this test when that problem is fixed."
)
def test_Stochiometry_account_for_growth(fxt_plants_model, fxt_stochiometry_model):
    """Test the account_for_growth method of the Stochiometry class."""

    from virtual_ecosystem.models.plants.stochiometry import StemAllocation

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
        fxt_stochiometry_model.total_element_mass,
        [1.31887368e05, 4.35408760e02, 5.93227761e-01],
    )

    # Account for growth
    fxt_stochiometry_model.account_for_growth(stem_allocation)

    print("new mass")

    assert np.all(
        fxt_stochiometry_model.total_element_mass
        >= [1.31887368e05, 4.35408760e02, 5.93227761e-01]
    )


def test_Stochiometry_account_for_element_loss_turnover(
    fxt_plants_model, fxt_stochiometry_model
):
    """Test the account_for_element_loss_turnover method of the Stochiometry class."""

    from virtual_ecosystem.models.plants.stochiometry import StemAllocation

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

    assert np.allclose(fxt_stochiometry_model.element_surplus, [0.0, 0.0, 0.0])
    fxt_stochiometry_model.account_for_element_loss_turnover(stem_allocation)

    # The surplus should always be negative after accounting for turnover
    assert np.all(fxt_stochiometry_model.element_surplus <= [0.0, 0.0, 0.0])


def test_Stochiometry_distribute_deficit(fxt_stochiometry_model):
    """Test the distribute_deficit method of the Stochiometry class.

    NOTE: This method should have a more robust test with a more deliberate test value.
    This will be easier to implement once growth is functioning.
    """

    # Distribute the deficit
    fxt_stochiometry_model.distribute_deficit(0)

    assert np.allclose(fxt_stochiometry_model.element_surplus[0], [0])


def test_Stochiometry_distrubte_surplus(fxt_stochiometry_model):
    """Test the distribute_surplus method of the Stochiometry class.

    NOTE: This method should have a more robust test with a more deliberate test value.
    This will be easier to implement once growth is functioning.
    """

    fxt_stochiometry_model.distribute_surplus(0)

    assert fxt_stochiometry_model.element_surplus[0] >= 0
