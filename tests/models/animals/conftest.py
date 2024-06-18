"""Collection of fixtures to assist the animal model testing scripts."""

import numpy as np
import pytest
import xarray
from xarray import DataArray


@pytest.fixture
def plant_data_instance():
    """Fixture returning a simple data instance containing plant resource data."""
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Populate data with a layers x cell id layer_leaf_mass array
    data = Data(grid=Grid(cell_nx=3, cell_ny=3))
    leaf_mass = np.full((15, 9), fill_value=np.nan)
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    return data


@pytest.fixture
def animal_data_for_model_instance(fixture_core_components):
    """Fixture returning a combination of plant and air temperature data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(
        grid_type="square",
        cell_nx=3,
        cell_ny=3,
    )
    data = Data(grid)

    leaf_mass = np.full(
        (fixture_core_components.layer_structure.n_layers, grid.n_cells),
        fill_value=np.nan,
    )
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    # grid.cell_id gives the spatial dimension, and we want a single "time" or "layer"
    air_temperature_values = np.full(
        (1, grid.n_cells), 25.0
    )  # All cells at 25.0 for one time step or layer
    air_temperature = DataArray(
        air_temperature_values,
        dims=[
            "time_or_layer",
            "cell_id",
        ],  # Adjust dimension names as appropriate for your model
        coords={
            "time_or_layer": [0],  # Assuming a single time step or layer for simplicity
            "cell_id": grid.cell_id,
        },
    )
    data["air_temperature"] = air_temperature

    return data


@pytest.fixture
def animal_data_for_community_instance(fixture_core_components):
    """Fixture returning a combination of plant and air temperature data."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(
        grid_type="square",
        cell_nx=3,
        cell_ny=3,
    )
    data = Data(grid)

    leaf_mass = np.full(
        (fixture_core_components.layer_structure.n_layers, grid.n_cells),
        fill_value=np.nan,
    )
    leaf_mass[1:4, :] = 10000
    data["layer_leaf_mass"] = xarray.DataArray(
        data=leaf_mass, dims=["layers", "cell_id"]
    )

    # grid.cell_id gives the spatial dimension, and we want a single "time" or "layer"
    air_temperature_values = np.full(
        (1, grid.n_cells), 25.0
    )  # All cells at 25.0 for one time step or layer
    air_temperature = DataArray(
        air_temperature_values,
        dims=[
            "time_or_layer",
            "cell_id",
        ],  # Adjust dimension names as appropriate for your model
        coords={
            "time_or_layer": [0],  # Assuming a single time step or layer for simplicity
            "cell_id": grid.cell_id,
        },
    )
    data["air_temperature"] = air_temperature

    # Initialize total_animal_respiration with zeros for each cell
    total_animal_respiration = np.zeros(len(grid.cell_id))
    data["total_animal_respiration"] = DataArray(
        total_animal_respiration, dims=["cell_id"], coords={"cell_id": grid.cell_id}
    )

    return data


@pytest.fixture
def constants_instance():
    """Fixture for an instance of animal constants."""
    from virtual_ecosystem.models.animal.constants import AnimalConsts

    return AnimalConsts()


@pytest.fixture
def functional_group_list_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list


@pytest.fixture
def animal_model_instance(
    data_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Fixture for an animal model object used in tests."""

    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    return AnimalModel(
        data=data_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )


@pytest.fixture
def animal_community_instance(
    functional_group_list_instance,
    animal_model_instance,
    animal_data_for_community_instance,
    constants_instance,
):
    """Fixture for an animal community used in tests."""
    from virtual_ecosystem.models.animal.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_groups=functional_group_list_instance,
        data=animal_data_for_community_instance,
        community_key=4,
        neighbouring_keys=[1, 3, 5, 7],
        get_destination=animal_model_instance.get_community_by_key,
        constants=constants_instance,
    )


@pytest.fixture
def herbivore_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[3]


@pytest.fixture
def herbivore_cohort_instance(herbivore_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        herbivore_functional_group_instance, 10000.0, 1, 10, constants_instance
    )


@pytest.fixture
def excrement_pool_instance():
    """Fixture for a soil pool used in tests."""
    from virtual_ecosystem.models.animal.decay import ExcrementPool

    return ExcrementPool(100000.0, 0.0)


@pytest.fixture
def plant_instance(plant_data_instance, constants_instance):
    """Fixture for a plant community used in tests."""
    from virtual_ecosystem.models.animal.plant_resources import PlantResources

    return PlantResources(
        data=plant_data_instance, cell_id=4, constants=constants_instance
    )


@pytest.fixture
def plant_list_instance(plant_data_instance, constants_instance):
    """Fixture providing a list of plant resources."""
    from virtual_ecosystem.models.animal.plant_resources import PlantResources

    return [
        PlantResources(
            data=plant_data_instance, cell_id=4, constants=constants_instance
        )
        for idx in range(3)
    ]


@pytest.fixture
def animal_list_instance(herbivore_functional_group_instance, constants_instance):
    """Fixture providing a list of animal cohorts."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return [
        AnimalCohort(
            herbivore_functional_group_instance, 10000.0, 1, 10, constants_instance
        )
        for idx in range(3)
    ]
