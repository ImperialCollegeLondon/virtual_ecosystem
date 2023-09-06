"""Tests for the model.plants.plants_model submodule."""

import numpy as np

# TODO: A lot of duplication in these tests, work out how to share code to make it DRYer


def test_PlantsModel__init__(plants_data, flora):
    """Test the PlantsModel.__init__ method."""
    from pint import Quantity

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel(
        data=plants_data,
        update_interval=Quantity("1 month"),
        flora=flora,
        canopy_layers=10,
        soil_layers=3,
    )

    # Test the flora and community are as expected
    assert len(plants_model.flora) == len(flora)
    assert len(plants_model.communities) == plants_data.grid.n_cells

    # Check the canopy has been initialised and updated with some simple test sums
    expected_layers = [
        ("layer_heights", (30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),
    ]

    for layer_name, layer_sum in expected_layers:
        assert layer_name in plants_data
        assert plants_data[layer_name].sum() == layer_sum


def test_PlantsModel_from_config(plants_data, plants_config):
    """Test the PlantsModel.from_config factory method."""
    from pint import Quantity

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel.from_config(
        data=plants_data, config=plants_config, update_interval=Quantity("1 month")
    )

    # Currently trivial test.
    assert isinstance(plants_model, PlantsModel)
    assert len(plants_model.communities) == plants_data.grid.n_cells

    # Check the canopy has been initialised and updated with some simple test sums
    expected_layers = [
        ("layer_heights", (30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),
    ]

    for layer_name, layer_sum in expected_layers:
        assert layer_name in plants_data
        assert plants_data[layer_name].sum() == layer_sum


def test_PlantsModel_update_canopy_layers(fxt_plants_model):
    """Simple test that update canopy layers restores overwritten data."""

    expected_layers = [
        ("layer_heights", (30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 0),  # Note that this layer should not be updated
    ]

    # Overwrite the existing data in each layer
    for layer, _ in expected_layers:
        fxt_plants_model.data[layer][:] = np.full_like(
            fxt_plants_model.data[layer].data, fill_value=np.nan
        )

    # Check that calling the method resets to the expected values
    fxt_plants_model.update_canopy_layers()

    for layer, value in expected_layers:
        assert fxt_plants_model.data[layer].sum() == value


def test_PlantsModel_set_absorbed_irradiance(fxt_plants_model):
    """Simple test that update canopy layers restores overwritten data."""

    expected_layers = [
        ("layer_heights", (30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),  # Is restored by additional call.
    ]
    # Overwrite the existing data in each layer
    for layer, _ in expected_layers:
        fxt_plants_model.data[layer][:] = np.full_like(
            fxt_plants_model.data[layer].data, fill_value=np.nan
        )

    # Check that calling the method after update resets to the expected values
    fxt_plants_model.update_canopy_layers()
    fxt_plants_model.set_absorbed_irradiance(time_index=0)

    for layer, value in expected_layers:
        assert fxt_plants_model.data[layer].sum() == value


def test_PlantsModel_update(fxt_plants_model):
    """Test the update method."""

    # The update method runs both update_canopy_layers and set_absorbed_irradiance so
    # should restore all of the layers below.
    expected_layers = [
        ("layer_heights", (30 + 20 + 10) * 4),
        ("leaf_area_index", 3 * 4),
        ("layer_fapar", (0.4 + 0.2 + 0.1) * 4),
        ("layer_absorbed_irradiation", 1000 * 4),
    ]

    # Overwrite the existing data in each layer
    for layer, _ in expected_layers:
        fxt_plants_model.data[layer][:] = np.full_like(
            fxt_plants_model.data[layer].data, fill_value=np.nan
        )

    # Check reset
    fxt_plants_model.update(time_index=0)

    # Check the canopy has been initialised and updated with some simple test sums
    for layer, value in expected_layers:
        assert fxt_plants_model.data[layer].sum() == value
