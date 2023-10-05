"""Collection of fixtures to assist the animal model testing scripts."""

import numpy as np
import pytest
import xarray


@pytest.fixture
def plant_data_instance():
    """Fixture returning a simple data instance containing plant resource data."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Populate data with a layers x cell id layer_leaf_mass array
    data = Data(grid=Grid(cell_nx=3, cell_ny=3))
    leaf_mass = np.full((15, 9), fill_value=np.nan)
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    return data


@pytest.fixture
def functional_group_list_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list


@pytest.fixture
def animal_model_instance(data_instance, functional_group_list_instance):
    """Fixture for an animal model object used in tests."""
    from pint import Quantity

    from virtual_rainforest.models.animals.animal_model import AnimalModel

    return AnimalModel(data_instance, Quantity("1 day"), functional_group_list_instance)


@pytest.fixture
def animal_community_instance(
    functional_group_list_instance, animal_model_instance, plant_data_instance
):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_groups=functional_group_list_instance,
        data=plant_data_instance,
        community_key=4,
        neighbouring_keys=[1, 3, 5, 7],
        get_destination=animal_model_instance.get_community_by_key,
    )


@pytest.fixture
def herbivore_functional_group_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list[3]


@pytest.fixture
def herbivore_cohort_instance(herbivore_functional_group_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(herbivore_functional_group_instance, 10000.0, 1)


@pytest.fixture
def excrement_instance():
    """Fixture for a soil pool used in tests."""
    from virtual_rainforest.models.animals.decay import ExcrementPool

    return ExcrementPool(100000.0, 0.0)


@pytest.fixture
def plant_instance(plant_data_instance):
    """Fixture for a plant community used in tests."""
    from virtual_rainforest.models.animals.plant_resources import PlantResources

    return PlantResources(data=plant_data_instance, cell_id=4)
