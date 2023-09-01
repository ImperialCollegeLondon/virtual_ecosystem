"""Tests for the model.plants.plants_model submodule."""

import numpy as np


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

    # Check the canopy has been initialised and updated
    assert "layer_heights" in plants_data
    assert "leaf_area_index" in plants_data
    assert plants_data["layer_heights"].sum() == (30 + 20 + 10) * 4
    assert plants_data["leaf_area_index"].sum() == 3 * 4


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

    # Check the canopy has been initialised and updated
    assert "layer_heights" in plants_data
    assert "leaf_area_index" in plants_data
    assert plants_data["layer_heights"].sum() == (30 + 20 + 10) * 4
    assert plants_data["leaf_area_index"].sum() == 3 * 4


def test_PlantsModel_update_canopy_layers(fxt_plants_model):
    """Simple test that update canopy layers restores overwritten data."""

    # Overwrite the existing data
    fxt_plants_model.data["layer_heights"][:] = np.full_like(
        fxt_plants_model.data["layer_heights"].data, fill_value=np.nan
    )
    fxt_plants_model.data["leaf_area_index"][:] = np.full_like(
        fxt_plants_model.data["leaf_area_index"].data, fill_value=np.nan
    )

    # Check reset
    fxt_plants_model.update_canopy_layers()

    assert fxt_plants_model.data["layer_heights"].sum() == (30 + 20 + 10) * 4
    assert fxt_plants_model.data["leaf_area_index"].sum() == 3 * 4


def test_PlantsModel_update(fxt_plants_model):
    """Test the update method."""

    # TODO - this currently just duplicates update_canopy_layers because that is all the
    #        functionality currently in update().

    # Overwrite the existing data
    fxt_plants_model.data["layer_heights"][:] = np.full_like(
        fxt_plants_model.data["layer_heights"].data, fill_value=np.nan
    )
    fxt_plants_model.data["leaf_area_index"][:] = np.full_like(
        fxt_plants_model.data["leaf_area_index"].data, fill_value=np.nan
    )

    # Check reset
    fxt_plants_model.update(time_index=0)

    assert fxt_plants_model.data["layer_heights"].sum() == (30 + 20 + 10) * 4
    assert fxt_plants_model.data["leaf_area_index"].sum() == 3 * 4
