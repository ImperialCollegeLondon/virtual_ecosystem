"""Tests for the model.plants.plants_model submodule."""


def test_PlantsModel__init__(plants_data, flora):
    """Test the PlantsModel.__init__ method."""
    from pint import Quantity

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel(
        data=plants_data, update_interval=Quantity("1 month"), flora=flora
    )

    # Currently trivial test.
    assert len(plants_model.flora) == len(flora)


def test_PlantsModel_from_config(plants_data, plants_config):
    """Test the PlantsModel.from_config factory method."""
    from pint import Quantity

    from virtual_rainforest.models.plants.plants_model import PlantsModel

    plants_model = PlantsModel.from_config(
        data=plants_data, config=plants_config, update_interval=Quantity("1 month")
    )

    # Currently trivial test.
    assert isinstance(plants_model, PlantsModel)
