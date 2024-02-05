"""Tests for the model.plants.plants_model submodule."""

import numpy as np

# TODO: A lot of duplication in these tests, work out how to share code to make it DRYer


def test_PlantsModel__init__(plants_data, flora, fixture_core_components):
    """Test the PlantsModel.__init__ method."""

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=flora,
    )

    # Test the flora and community are as expected
    assert len(plants_model.flora) == len(flora)
    assert len(plants_model.communities) == plants_data.grid.n_cells

    # Check the canopy has been initialised and updated with some simple test sums
    expected_layers = [
        ("layer_heights", (32 + 30 + 20 + 10 + 1.5 + 0.1 - 0.25 - 1) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),
    ]

    for layer_name, layer_sum in expected_layers:
        assert layer_name in plants_data
        assert np.allclose(plants_data[layer_name].sum(), layer_sum)


def test_PlantsModel_from_config(plants_data, fixture_config, fixture_core_components):
    """Test the PlantsModel.from_config factory method."""

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel.from_config(
        data=plants_data, config=fixture_config, core_components=fixture_core_components
    )

    # Currently trivial test.
    assert isinstance(plants_model, PlantsModel)
    assert len(plants_model.communities) == plants_data.grid.n_cells

    # Check the canopy has been initialised and updated with some simple test sums
    expected_layers = (
        ("layer_heights", (32 + 30 + 20 + 10 + 1.5 + 0.1 - 0.25 - 1) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),
    )

    for layer_name, layer_sum in expected_layers:
        assert layer_name in plants_data
        assert np.allclose(plants_data[layer_name].sum(), layer_sum)


def test_PlantsModel_update_canopy_layers(fxt_plants_model):
    """Simple test that update canopy layers restores overwritten data."""

    expected_layers = (
        ("layer_heights", (32 + 30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 0),  # Note that this layer should not be updated
    )

    # Overwrite the existing data in each layer
    for layer, _ in expected_layers:
        fxt_plants_model.data[layer][:] = np.full_like(
            fxt_plants_model.data[layer].data, fill_value=np.nan
        )

    # Check that calling the method resets to the expected values
    fxt_plants_model.update_canopy_layers()

    for layer, value in expected_layers:
        assert np.allclose(fxt_plants_model.data[layer].sum(), value)


def test_PlantsModel_set_absorbed_irradiance(fxt_plants_model):
    """Simple test that update canopy layers restores overwritten data."""

    expected_layers = (
        ("layer_heights", (32 + 30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),  # Is restored by additional call.
    )
    # Overwrite the existing data in each layer
    for layer, _ in expected_layers:
        fxt_plants_model.data[layer][:] = np.full_like(
            fxt_plants_model.data[layer].data, fill_value=np.nan
        )

    # Check that calling the method after update resets to the expected values
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.set_absorbed_irradiance(time_index=0)

    for layer, value in expected_layers:
        assert np.allclose(fxt_plants_model.data[layer].sum(), value)


def test_PlantsModel_estimate_gpp(fxt_plants_model):
    """Test the estimate_gpp method."""

    # Set the canopy and absorbed irradiance
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.set_absorbed_irradiance(time_index=0)

    # Calculate GPP
    fxt_plants_model.estimate_gpp(time_index=0)

    # Check calculate quantities - this is currently very basic.

    # - Light use efficiency: currently asserted fixed value
    exp_lue = np.full((15, 4), fill_value=np.nan)
    exp_lue[1:4, :] = 0.3
    assert np.allclose(
        fxt_plants_model.data["layer_light_use_efficiency"].to_numpy(),
        exp_lue,
        equal_nan=True,
    )

    # Same for evapotranspiration
    exp_evapo = np.full((15, 4), fill_value=np.nan)
    exp_evapo[1:4, :] = 20
    assert np.allclose(
        fxt_plants_model.data["evapotranspiration"].to_numpy(),
        exp_evapo,
        equal_nan=True,
    )

    # - Canopy fapar to expected gpp per m2
    exp_fapar = np.full((15, 1), fill_value=np.nan)
    exp_fapar[[1, 2, 3, 12]] = [[0.4], [0.2], [0.1], [0.3]]
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


def test_PlantsModel_update(fxt_plants_model):
    """Test the update method."""

    # The update method runs both update_canopy_layers and set_absorbed_irradiance so
    # should restore all of the layers below.
    expected_layers = (
        ("layer_heights", (32 + 30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_leaf_mass", 30000 * 4),
        ("layer_absorbed_irradiation", 1000 * 4),
    )

    # Overwrite the existing data in each layer
    for layer, _ in expected_layers:
        fxt_plants_model.data[layer][:] = np.full_like(
            fxt_plants_model.data[layer].data, fill_value=np.nan
        )

    # Check reset
    fxt_plants_model.update(time_index=0)

    # Check the canopy has been initialised and updated with some simple test sums
    for layer, value in expected_layers:
        assert np.allclose(fxt_plants_model.data[layer].sum(), value)

    # Check the growth of the cohorts
    for community in fxt_plants_model.communities.values():
        for cohort in community:
            # Original 0.1 + 0.03 cm from current arbitrary increment
            assert np.allclose(cohort.dbh, 0.13)
