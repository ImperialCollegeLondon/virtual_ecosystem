"""Tests for the model.plants.plants_model submodule."""

import numpy as np
import xarray

# TODO: A lot of duplication in these tests, work out how to share code to make it DRYer


def test_PlantsModel__init__(
    plants_data, flora, fixture_core_components, fixture_canopy_layer_data
):
    """Test the PlantsModel.__init__ method."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=flora,
    )

    # Test the flora and community are as expected
    n_cells = fixture_core_components.grid.n_cells
    assert plants_model.flora == flora
    assert len(plants_model.communities) == n_cells

    # Check the canopy has been initialised and updated, using the full layer heights
    # data
    # TODO - amend this as and when layer heights gets centralised
    del fixture_canopy_layer_data["layer_heights_canopy"]
    del fixture_canopy_layer_data["layer_leaf_mass"]

    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        assert layer_name in plants_data
        expected = fixture_core_components.layer_structure.from_template()
        expected[layer_indices] = layer_vals
        xarray.testing.assert_allclose(plants_data[layer_name], expected)


def test_PlantsModel_from_config(
    plants_data, fixture_config, fixture_core_components, fixture_canopy_layer_data
):
    """Test the PlantsModel.from_config factory method."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel.from_config(
        data=plants_data, config=fixture_config, core_components=fixture_core_components
    )

    # Currently trivial test.
    n_cells = fixture_core_components.grid.n_cells
    assert isinstance(plants_model, PlantsModel)
    assert len(plants_model.communities) == n_cells

    # Check the canopy has been initialised and updated, using the full layer heights
    # data
    # TODO - amend this as and when layer heights gets centralised
    del fixture_canopy_layer_data["layer_heights_canopy"]
    del fixture_canopy_layer_data["layer_leaf_mass"]

    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        assert layer_name in plants_data
        expected = fixture_core_components.layer_structure.from_template()
        expected[layer_indices] = layer_vals
        xarray.testing.assert_allclose(plants_data[layer_name], expected)


def test_PlantsModel_update_canopy_layers(
    fixture_core_components, fxt_plants_model, fixture_canopy_layer_data
):
    """Simple test that update canopy layers restores overwritten data."""

    from_template = fixture_core_components.layer_structure.from_template

    # Overwrite the existing canopy derived data in each layer - this also nukes the
    # soil and surface depths _which_ are not correctly regenerated in this test, so the
    # test makes use of the canopy only layer heights in the fixture_canopy_layer_data
    #
    # TODO - amend this as and when layer heights gets centralised
    del fixture_canopy_layer_data["layer_heights_full"]
    del fixture_canopy_layer_data["layer_leaf_mass"]

    for layer, _, _ in fixture_canopy_layer_data.values():
        fxt_plants_model.data[layer] = from_template()

    # Calling the method resets to the expected values
    fxt_plants_model.update_canopy_layers()

    # Check the resulting repopulated canopy data, but omitting the
    # shortwave_absorption, which should not have been regenerated yet
    del fixture_canopy_layer_data["shortwave_absorption"]
    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        expected = from_template()
        expected[layer_indices] = layer_vals
        xarray.testing.assert_allclose(fxt_plants_model.data[layer_name], expected)


def test_PlantsModel_set_shortwave_absorption(
    fxt_plants_model, fixture_core_components, fixture_canopy_layer_data
):
    """Simple test that update canopy layers restores overwritten data."""

    from_template = fixture_core_components.layer_structure.from_template

    # Overwrite the existing canopy derived data in each layer - this also nukes the
    # soil and surface depths _which_ are not correctly regenerated in this test, so the
    # test makes use of the canopy only layer heights in the fixture_canopy_layer_data
    #
    # TODO - amend this as and when layer heights gets centralised
    del fixture_canopy_layer_data["layer_heights_full"]
    del fixture_canopy_layer_data["layer_leaf_mass"]

    for layer, _, _ in fixture_canopy_layer_data.values():
        fxt_plants_model.data[layer] = from_template()

    # Check that calling the method after update resets to the expected values
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.set_shortwave_absorption(time_index=0)

    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        expected = from_template()
        expected[layer_indices] = layer_vals
        xarray.testing.assert_allclose(fxt_plants_model.data[layer_name], expected)


def test_PlantsModel_estimate_gpp(fxt_plants_model, fixture_core_components):
    """Test the estimate_gpp method."""

    # Set the canopy and absorbed irradiance
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.set_shortwave_absorption(time_index=0)

    # Calculate GPP
    fxt_plants_model.estimate_gpp(time_index=0)

    # TODO - currently no actual validation of values, only of structure
    #      - maybe mock lue and iwue to get easier values rather than current obscure
    #        ones

    # Check stem_gpp and stem_transpiration structure
    exp_stem_struct = {
        cid: cmty.number_of_cohorts
        for cid, cmty in fxt_plants_model.communities.items()
    }

    # Are the stem properties dictionaries of arrays with the right length
    assert exp_stem_struct == {
        cid: len(vals) for cid, vals in fxt_plants_model.per_stem_gpp.items()
    }

    assert exp_stem_struct == {
        cid: len(vals) for cid, vals in fxt_plants_model.per_stem_transpiration.items()
    }

    # Check the evapotranspiration shape

    assert fxt_plants_model.data["evapotranspiration"].shape == (
        fxt_plants_model.layer_structure.n_layers,
        fxt_plants_model.grid.n_cells,
    )


def test_PlantsModel_allocate_gpp(fxt_plants_model, fixture_core_components):
    """Test the allocate_gpp method."""

    # Provide GPP values
    fxt_plants_model.per_stem_gpp = {
        cell_id: np.array([55]) for cell_id in fxt_plants_model.communities.keys()
    }
    # Store previous dbh values
    prev_dbh_values = {
        cell_id: fxt_plants_model.communities[cell_id].cohorts.dbh_values.copy()
        for cell_id in fxt_plants_model.communities.keys()
    }

    # Allocate GPP
    fxt_plants_model.allocate_gpp()

    for cell_id in fxt_plants_model.communities.keys():
        # TODO: eventually have tests with more meaningful values
        # Check that dbh is >= previous dbh (plants should not shrink!)
        assert (
            fxt_plants_model.communities[cell_id].cohorts.dbh_values
            >= prev_dbh_values[cell_id]
        ).all()
        # Ensure that leaf and root turnover exist and are > 0
        assert fxt_plants_model.data["leaf_turnover"][cell_id] > 0
        assert fxt_plants_model.data["root_turnover"][cell_id] > 0
        assert fxt_plants_model.data["fallen_n_propagules"][cell_id] >= 0
        assert fxt_plants_model.data["fallen_non_propagule_c_mass"][cell_id] > 0
        assert fxt_plants_model.data["canopy_n_propagules"][cell_id] >= 0
        assert fxt_plants_model.data["canopy_non_propagule_c_mass"][cell_id] > 0
        assert fxt_plants_model.data["root_carbohydrate_exudation"][cell_id] > 0
        assert fxt_plants_model.data["plant_symbiote_carbon_supply"][cell_id] > 0


def test_PlantsModel_update(
    fxt_plants_model, fixture_core_components, fixture_canopy_layer_data
):
    """Test the update method."""

    # The update method runs both update_canopy_layers and set_shortwave_absorption so
    # should restore all of the layers below.
    # TODO - amend this as and when layer heights gets centralised
    del fixture_canopy_layer_data["layer_heights_full"]

    from_template = fixture_core_components.layer_structure.from_template

    for layer, _, _ in fixture_canopy_layer_data.values():
        fxt_plants_model.data[layer] = from_template()

    # Check reset
    fxt_plants_model.update(time_index=0)

    # Check the canopy has been initialised and updated
    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        expected = from_template()
        expected[layer_indices] = layer_vals
        xarray.testing.assert_allclose(fxt_plants_model.data[layer_name], expected)

    # # Check the growth of the cohorts
    # for community in fxt_plants_model.communities.values():
    #     for cohort in community:
    #         # Original 0.1 + 0.03 cm from current arbitrary increment
    #         assert np.allclose(cohort.dbh, 0.13)


def test_PlantsModel_calculate_turnover(fxt_plants_model, fixture_config):
    """Test the calculate_turnover method of the plants model."""

    # Check reset
    fxt_plants_model.calculate_turnover()
    consts = fxt_plants_model.model_constants

    # Check that all expected variables are generated and have the correct value
    assert np.allclose(fxt_plants_model.data["stem_lignin"], consts.stem_lignin)
    assert np.allclose(
        fxt_plants_model.data["senesced_leaf_lignin"], consts.senesced_leaf_lignin
    )
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_lignin"],
        consts.plant_reproductive_tissue_lignin,
    )
    assert np.allclose(fxt_plants_model.data["root_lignin"], consts.root_lignin)
    assert np.allclose(fxt_plants_model.data["leaf_lignin"], consts.leaf_lignin)
    assert np.allclose(
        fxt_plants_model.data["deadwood_c_n_ratio"], consts.deadwood_c_n_ratio
    )
    assert np.allclose(
        fxt_plants_model.data["leaf_turnover_c_n_ratio"], consts.leaf_turnover_c_n_ratio
    )
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover_c_n_ratio"],
        consts.plant_reproductive_tissue_turnover_c_n_ratio,
    )
    assert np.allclose(
        fxt_plants_model.data["root_turnover_c_n_ratio"], consts.root_turnover_c_n_ratio
    )
    assert np.allclose(
        fxt_plants_model.data["deadwood_c_p_ratio"], consts.deadwood_c_p_ratio
    )
    assert np.allclose(
        fxt_plants_model.data["leaf_turnover_c_p_ratio"], consts.leaf_turnover_c_p_ratio
    )
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover_c_p_ratio"],
        consts.plant_reproductive_tissue_turnover_c_p_ratio,
    )
    assert np.allclose(
        fxt_plants_model.data["root_turnover_c_p_ratio"], consts.root_turnover_c_p_ratio
    )


def test_PlantsModel_calculate_turnover_constant_override(
    plants_data, fixture_config, fixture_core_components
):
    """Test that the turnover constants can be overridden by values in config."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    fixture_config["plants"]["constants"] = {"PlantsConsts": {"leaf_lignin": 100.0}}
    plants_model = PlantsModel.from_config(
        data=plants_data, config=fixture_config, core_components=fixture_core_components
    )
    plants_model.calculate_turnover()

    assert np.allclose(plants_model.data["leaf_lignin"], 100.0)


def test_PlantsModel_calculate_nutrient_uptake(fxt_plants_model):
    """Test the calculate_nutrient_uptake method of the plants model."""

    # Check reset
    fxt_plants_model.calculate_nutrient_uptake()

    # Check that all expected variables are generated and have the correct value
    assert np.allclose(fxt_plants_model.data["plant_ammonium_uptake"], 5.0e-4)
    assert np.allclose(fxt_plants_model.data["plant_nitrate_uptake"], 7.5e-3)
    assert np.allclose(fxt_plants_model.data["plant_phosphorus_uptake"], 3.0e-5)


def test_PlantsModel_apply_mortality(fxt_plants_model):
    """Test the apply_mortality method of the plants model."""

    original_population = {
        cell_id: fxt_plants_model.communities[cell_id].cohorts.n_individuals.copy()
        for cell_id in fxt_plants_model.communities.keys()
    }

    # Check reset
    fxt_plants_model.apply_mortality()

    for cell_id in fxt_plants_model.communities.keys():
        community = fxt_plants_model.communities[cell_id]

        mortality = (
            original_population[cell_id]
            - fxt_plants_model.communities[cell_id].cohorts.n_individuals
        )
        deadwood_mass = np.sum(mortality * community.stem_allometry.stem_mass)

        assert np.all(
            original_population[cell_id]
            >= fxt_plants_model.communities[cell_id].cohorts.n_individuals
        )
        assert fxt_plants_model.data["deadwood_production"][cell_id] == deadwood_mass


def test_partition_reproductive_tissue(fxt_plants_model):
    """Tests the partition reproductive tissue function."""

    n_propagules, mass_non_propagules = fxt_plants_model.partition_reproductive_tissue(
        reproductive_tissue_mass=10.5
    )

    assert n_propagules == 5
    assert mass_non_propagules == 5.5
    assert (
        n_propagules * fxt_plants_model.model_constants.carbon_mass_per_propagule
        + mass_non_propagules
    )
