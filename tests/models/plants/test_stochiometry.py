"""Tests for the Stochiometry class."""

import numpy as np


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
            tissues=[
                FoliageTissue(
                    element_name="Nitrogen",
                    community=community,
                    ideal_ratio=np.full(
                        community.number_of_cohorts, plant_consts.foliage_c_n_ratio
                    ),
                    actual_element_mass=community.stem_allometry.foliage_mass
                    * plant_consts.foliage_c_n_ratio,
                    reclaim_ratio=plant_consts.leaf_turnover_c_n_ratio,
                ),
                RootTissue(
                    element_name="Nitrogen",
                    community=community,
                    ideal_ratio=np.full(
                        community.number_of_cohorts,
                        plant_consts.root_turnover_c_n_ratio,
                    ),
                    actual_element_mass=plant_consts.root_turnover_c_n_ratio
                    * community.stem_traits.zeta
                    * community.stem_allometry.foliage_mass,
                ),
                WoodTissue(
                    element_name="Nitrogen",
                    community=community,
                    ideal_ratio=np.full(
                        community.number_of_cohorts, plant_consts.deadwood_c_n_ratio
                    ),
                    actual_element_mass=plant_consts.deadwood_c_n_ratio
                    * community.stem_allometry.stem_mass,
                ),
                ReproductiveTissue(
                    element_name="Nitrogen",
                    community=community,
                    ideal_ratio=np.full(
                        community.number_of_cohorts,
                        plant_consts.plant_reproductive_tissue_turnover_c_n_ratio,
                    ),
                    actual_element_mass=community.stem_allometry.reproductive_tissue_mass
                    * plant_consts.plant_reproductive_tissue_turnover_c_n_ratio,
                ),
            ],
            n_cohorts=community.number_of_cohorts,
            community=community,
        )
        assert n_stochiometry is not None


def test_Stochiometry_FoliageTissue(fxt_plants_model):
    """Test the foliage stochiometry."""
    from virtual_ecosystem.models.plants.stochiometry import FoliageTissue

    plant_consts = fxt_plants_model.model_constants
    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        foliage_tissue = FoliageTissue(
            element_name="Nitrogen",
            community=community,
            ideal_ratio=np.full(
                community.number_of_cohorts, plant_consts.foliage_c_n_ratio
            ),
            actual_element_mass=community.stem_allometry.foliage_mass
            * plant_consts.foliage_c_n_ratio,
            reclaim_ratio=plant_consts.leaf_turnover_c_n_ratio,
        )
        assert foliage_tissue is not None


def test_Stochiometry_ReproductiveTissue(fxt_plants_model):
    """Test the reproductive tissue stochiometry."""
    from virtual_ecosystem.models.plants.stochiometry import ReproductiveTissue

    plant_consts = fxt_plants_model.model_constants
    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        reproductive_tissue = ReproductiveTissue(
            element_name="Nitrogen",
            community=community,
            ideal_ratio=np.full(
                community.number_of_cohorts,
                plant_consts.plant_reproductive_tissue_turnover_c_n_ratio,
            ),
            actual_element_mass=community.stem_allometry.reproductive_tissue_mass
            * plant_consts.plant_reproductive_tissue_turnover_c_n_ratio,
        )
        assert reproductive_tissue is not None


def test_Stochiometry_RootTissue(fxt_plants_model):
    """Test the reproductive tissue stochiometry."""
    from virtual_ecosystem.models.plants.stochiometry import RootTissue

    plant_consts = fxt_plants_model.model_constants
    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        root_tissue = RootTissue(
            element_name="Nitrogen",
            community=community,
            ideal_ratio=np.full(
                community.number_of_cohorts, plant_consts.root_turnover_c_n_ratio
            ),
            actual_element_mass=plant_consts.root_turnover_c_n_ratio
            * community.stem_traits.zeta
            * community.stem_allometry.foliage_mass,
        )

        assert root_tissue is not None


def test_Stochiometry_WoodTissue(fxt_plants_model):
    """Test the reproductive tissue stochiometry."""
    from virtual_ecosystem.models.plants.stochiometry import WoodTissue

    plant_consts = fxt_plants_model.model_constants
    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        wood_tissue = WoodTissue(
            element_name="Nitrogen",
            community=community,
            ideal_ratio=np.full(
                community.number_of_cohorts, plant_consts.deadwood_c_n_ratio
            ),
            actual_element_mass=plant_consts.deadwood_c_n_ratio
            * community.stem_allometry.stem_mass,
        )
        assert wood_tissue is not None
