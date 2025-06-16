"""Tests for the Stochiometry class."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest


@pytest.mark.parametrize(
    "expected_exception",
    [
        (does_not_raise()),
    ],
)
def test_FoliageTissue__init__(fxt_plants_model, expected_exception):
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

        with expected_exception:
            if expected_exception is does_not_raise():
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


def test_Stochiometry__init__(fxt_plants_model):
    """Fixture for the Stochiometry class."""

    from virtual_ecosystem.models.plants.stochiometry import (
        FoliageTissue,
        ReproductiveTissue,
        RootTissue,
        StemStochiometry,
        WoodTissue,
    )

    plant_consts = fxt_plants_model.model_constants
    for cell_id in fxt_plants_model.communities.keys():
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
        assert n_stochiometry is not None
