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
    assert len(plants_model.flora) == len(flora)
    assert len(plants_model.communities) == n_cells

    # Check the canopy has been initialised and updated, using the full layer heights
    # data
    # TODO - amend this as and when layer heights gets centralised
    del fixture_canopy_layer_data["layer_heights_canopy"]
    del fixture_canopy_layer_data["layer_leaf_mass"]

    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        assert layer_name in plants_data
        expected = fixture_core_components.layer_structure.from_template()
        expected[layer_indices] = layer_vals[:, None]
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
        expected[layer_indices] = layer_vals[:, None]
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
    # canopy_absorption, which should not have been regenerated yet
    del fixture_canopy_layer_data["canopy_absorption"]
    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        expected = from_template()
        expected[layer_indices] = layer_vals[:, None]
        xarray.testing.assert_allclose(fxt_plants_model.data[layer_name], expected)

    # Check canopy_absorption is indeed still empty
    xarray.testing.assert_allclose(
        fxt_plants_model.data["canopy_absorption"], from_template()
    )


def test_PlantsModel_set_canopy_absorption(
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
    fxt_plants_model.set_canopy_absorption(time_index=0)

    for layer_name, layer_vals, layer_indices in fixture_canopy_layer_data.values():
        expected = from_template()
        expected[layer_indices] = layer_vals[:, None]
        xarray.testing.assert_allclose(fxt_plants_model.data[layer_name], expected)


def test_PlantsModel_estimate_gpp(fxt_plants_model, fixture_core_components):
    """Test the estimate_gpp method."""

    lyr_str = fixture_core_components.layer_structure

    # Set the canopy and absorbed irradiance
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.set_canopy_absorption(time_index=0)

    # Calculate GPP
    fxt_plants_model.estimate_gpp(time_index=0)

    # Check calculated quantities - this is currently very basic.

    # - Light use efficiency: currently asserted fixed value
    exp_lue = lyr_str.from_template()
    exp_lue[lyr_str.index_filled_canopy] = 0.3
    xarray.testing.assert_allclose(
        fxt_plants_model.data["layer_light_use_efficiency"],
        exp_lue,
    )

    # Same for evapotranspiration
    exp_evapo = lyr_str.from_template()
    exp_evapo[lyr_str.index_filled_canopy] = 20
    xarray.testing.assert_allclose(
        fxt_plants_model.data["evapotranspiration"],
        exp_evapo,
    )

    # - Canopy fapar to expected gpp per m2
    exp_fapar = lyr_str.from_template()
    exp_fapar[lyr_str.index_flux_layers] = [[0.4], [0.2], [0.1], [0.3]]
    exp_gpp_per_m2 = exp_lue * 1000 * exp_fapar

    assert np.allclose(
        fxt_plants_model.data["layer_gpp_per_m2"].data, exp_gpp_per_m2, equal_nan=True
    )

    # - GPP calculated correctly
    for cell_id, community in fxt_plants_model.communities.items():
        cell_gpp_per_m2 = exp_gpp_per_m2[np.arange(1, 11), cell_id]
        for cohort in community:
            assert np.allclose(
                cohort.gpp,
                np.nansum(cell_gpp_per_m2 * cohort.canopy_area * 30 * 24 * 60 * 60),
            )


def test_PlantsModel_update(
    fxt_plants_model, fixture_core_components, fixture_canopy_layer_data
):
    """Test the update method."""

    # The update method runs both update_canopy_layers and set_canopy_absorption so
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
        expected[layer_indices] = layer_vals[:, None]
        xarray.testing.assert_allclose(fxt_plants_model.data[layer_name], expected)

    # Check the growth of the cohorts
    for community in fxt_plants_model.communities.values():
        for cohort in community:
            # Original 0.1 + 0.03 cm from current arbitrary increment
            assert np.allclose(cohort.dbh, 0.13)


def test_PlantsModel_calculate_turnover(fxt_plants_model, fixture_core_components):
    """Test the calculate_turnover method of the plants model."""

    # Check reset
    fxt_plants_model.calculate_turnover()

    # Check that all expected variables are generated and have the correct value
    assert np.allclose(fxt_plants_model.data["deadwood_production"], 0.075)
    assert np.allclose(fxt_plants_model.data["leaf_turnover"], 0.027)
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover"], 0.003
    )
    assert np.allclose(fxt_plants_model.data["root_turnover"], 0.027)
    assert np.allclose(fxt_plants_model.data["deadwood_lignin"], 0.545)
    assert np.allclose(fxt_plants_model.data["leaf_turnover_lignin"], 0.05)
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover_lignin"], 0.01
    )
    assert np.allclose(fxt_plants_model.data["root_turnover_lignin"], 0.2)
    assert np.allclose(fxt_plants_model.data["leaf_turnover_c_n_ratio"], 25.5)
    assert np.allclose(
        fxt_plants_model.data["plant_reproductive_tissue_turnover_c_n_ratio"], 12.5
    )
    assert np.allclose(fxt_plants_model.data["root_turnover_c_n_ratio"], 45.6)
