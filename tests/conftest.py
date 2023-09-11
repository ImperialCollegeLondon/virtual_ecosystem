"""Collection of fixtures to assist the testing scripts."""
from logging import DEBUG
from typing import Any

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray

# An import of LOGGER is required for INFO logging events to be visible to tests
# This can be removed as soon as a script that imports logger is imported
from virtual_rainforest.core.logger import LOGGER

# Class uses DEBUG
LOGGER.setLevel(DEBUG)


def log_check(caplog: pytest.LogCaptureFixture, expected_log: tuple[tuple]) -> None:
    """Helper function to check that the captured log is as expected.

    Arguments:
        caplog: An instance of the caplog fixture
        expected_log: An iterable of 2-tuples containing the log level and message.
    """

    assert len(expected_log) == len(caplog.records)

    assert all(
        [exp[0] == rec.levelno for exp, rec in zip(expected_log, caplog.records)]
    )
    assert all(
        [exp[1] in rec.message for exp, rec in zip(expected_log, caplog.records)]
    )


# Shared fixtures


@pytest.fixture
def fixture_square_grid():
    """Create a square grid fixture.

    A 10 x 10 grid of 1 hectare cells, with non-zero origin.
    """

    from virtual_rainforest.core.grid import Grid

    grid = Grid(
        grid_type="square",
        cell_area=10000,
        cell_nx=10,
        cell_ny=10,
        xoff=500000,
        yoff=200000,
    )

    return grid


@pytest.fixture
def fixture_square_grid_simple():
    """Create a square grid fixture.

    A 2 x 2 grid centred on x=1,1,2,2 y=1,2,1,2
    """

    from virtual_rainforest.core.grid import Grid

    grid = Grid(
        grid_type="square",
        cell_area=1,
        cell_nx=2,
        cell_ny=2,
        xoff=0.5,
        yoff=0.5,
    )

    return grid


@pytest.fixture
def fixture_data(fixture_square_grid_simple):
    """A Data instance fixture for use in testing."""

    from virtual_rainforest.core.data import Data

    data = Data(fixture_square_grid_simple)

    # Create an existing variable to test replacement
    data["existing_var"] = DataArray([1, 2, 3, 4], dims=("cell_id",))

    return data


@pytest.fixture
def data_instance():
    """Creates an empty data instance."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    grid = Grid()
    return Data(grid)


@pytest.fixture
def dummy_carbon_data(layer_roles_fixture):
    """Creates a dummy carbon data object for use in tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(cell_nx=4, cell_ny=1)
    data = Data(grid)

    # The required data is now added. This includes the four carbon pools: mineral
    # associated organic matter, low molecular weight carbon, microbial carbon and
    # particulate organic matter. It also includes various factors of the physical
    # environment: pH, bulk density, soil moisture, soil temperature, percentage clay in
    # soil.
    data["soil_c_pool_lmwc"] = DataArray([0.05, 0.02, 0.1, 0.005], dims=["cell_id"])
    """Low molecular weight carbon pool (kg C m^-3)"""
    data["soil_c_pool_maom"] = DataArray([2.5, 1.7, 4.5, 0.5], dims=["cell_id"])
    """Mineral associated organic matter pool (kg C m^-3)"""
    data["soil_c_pool_microbe"] = DataArray([5.8, 2.3, 11.3, 1.0], dims=["cell_id"])
    """Microbial biomass (carbon) pool (kg C m^-3)"""
    data["soil_c_pool_pom"] = DataArray([0.1, 1.0, 0.7, 0.35], dims=["cell_id"])
    """Particulate organic matter pool (kg C m^-3)"""
    data["pH"] = DataArray([3.0, 7.5, 9.0, 5.7], dims=["cell_id"])
    data["bulk_density"] = DataArray([1350.0, 1800.0, 1000.0, 1500.0], dims=["cell_id"])
    data["percent_clay"] = DataArray([80.0, 30.0, 10.0, 90.0], dims=["cell_id"])
    data["litter_C_mineralisation_rate"] = DataArray(
        [0.00212106, 0.00106053, 0.00049000, 0.0055], dims=["cell_id"]
    )

    # The layer dependant data has to be handled separately
    data["soil_moisture"] = xr.concat(
        [
            DataArray(np.full((13, 4), np.nan), dims=["layers", "cell_id"]),
            # At present the soil model only uses the top soil layer, so this is the
            # only one with real test values in
            DataArray([[0.5, 0.7, 0.6, 0.2]], dims=["layers", "cell_id"]),
            DataArray(np.full((1, 4), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    data["soil_moisture"] = data["soil_moisture"].assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": data.grid.cell_id,
        }
    )
    data["soil_temperature"] = xr.concat(
        [
            DataArray(np.full((13, 4), np.nan), dims=["dim_0", "cell_id"]),
            # At present the soil model only uses the top soil layer, so this is the
            # only one with real test values in
            DataArray([[35.0, 37.5, 40.0, 25.0]], dims=["dim_0", "cell_id"]),
            DataArray(np.full((1, 4), 22.5), dims=["dim_0", "cell_id"]),
        ],
        dim="dim_0",
    )
    data["soil_temperature"] = (
        data["soil_temperature"]
        .rename({"dim_0": "layers"})
        .assign_coords(
            {
                "layers": np.arange(0, 15),
                "layer_roles": ("layers", layer_roles_fixture),
                "cell_id": data.grid.cell_id,
            }
        )
    )

    return data


@pytest.fixture
def top_soil_layer_index(layer_roles_fixture):
    """The index of the top soil layer in the data fixtures."""
    return next(i for i, v in enumerate(layer_roles_fixture) if v == "soil")


@pytest.fixture
def surface_layer_index(layer_roles_fixture):
    """The index of the top soil layer in the data fixtures."""
    return next(i for i, v in enumerate(layer_roles_fixture) if v == "surface")


@pytest.fixture
def new_axis_validators():
    """Create new axis validators to test methods and registration."""
    from virtual_rainforest.core.axes import AxisValidator
    from virtual_rainforest.core.grid import Grid

    # Create a new subclass.
    class TestAxis(AxisValidator):
        core_axis = "testing"
        dim_names = {"test"}

        def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
            return True if value.sum() > 10 else False

        def run_validation(
            self, value: DataArray, grid: Grid, **kwargs: Any
        ) -> DataArray:
            return value * 2

    # Create a new duplicate subclass to check mutual exclusivity test
    class TestAxis2(AxisValidator):
        core_axis = "testing"
        dim_names = {"test"}

        def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
            return True if value.sum() > 10 else False

        def run_validation(
            self, value: DataArray, grid: Grid, **kwargs: Any
        ) -> DataArray:
            return value * 2


@pytest.fixture
def layer_roles_fixture():
    """Create list of layer roles for 10 canopy layers and 2 soil layers."""
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        set_layer_roles,
    )

    return set_layer_roles(10, 2)


@pytest.fixture
def dummy_climate_data(layer_roles_fixture):
    """Creates a dummy climate data object for use in tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with four cells.
    grid = Grid(
        grid_type="square",
        cell_nx=3,
        cell_ny=1,
        cell_area=3,
        xoff=0,
        yoff=0,
    )
    data = Data(grid)

    data["air_temperature_ref"] = DataArray(
        np.full((3, 3), 30),
        dims=["cell_id", "time_index"],
    )
    data["mean_annual_temperature"] = DataArray(
        np.full((3), 20),
        dims=["cell_id"],
    )
    data["relative_humidity_ref"] = DataArray(
        np.full((3, 3), 90),
        dims=["cell_id", "time_index"],
    )
    data["vapour_pressure_deficit_ref"] = DataArray(
        np.full((3, 3), 0.14),
        dims=["cell_id", "time_index"],
    )
    data["atmospheric_pressure_ref"] = DataArray(
        np.full((3, 3), 96),
        dims=["cell_id", "time_index"],
    )
    data["atmospheric_co2_ref"] = DataArray(
        np.full((3, 3), 400),
        dims=["cell_id", "time_index"],
    )
    evapotranspiration = np.repeat(a=[np.nan, 20.0, np.nan], repeats=[1, 3, 11])
    data["evapotranspiration"] = DataArray(
        np.broadcast_to(evapotranspiration, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": data.grid.cell_id,
        },
        name="evapotranspiration",
    )
    leaf_area_index = np.repeat(a=[np.nan, 1.0, np.nan], repeats=[1, 3, 11])
    data["leaf_area_index"] = DataArray(
        np.broadcast_to(leaf_area_index, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": data.grid.cell_id,
        },
        name="leaf_area_index",
    )

    layer_heights = np.repeat(
        a=[32.0, 30.0, 20.0, 10.0, np.nan, 1.5, 0.1, -0.1, -1.0],
        repeats=[1, 1, 1, 1, 7, 1, 1, 1, 1],
    )
    data["layer_heights"] = DataArray(
        np.broadcast_to(layer_heights, (3, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles_fixture),
            "cell_id": data.grid.cell_id,
        },
        name="layer_heights",
    )

    data["precipitation"] = DataArray(
        [[200, 200, 200], [200, 200, 200], [200, 200, 200]],
        dims=["time_index", "cell_id"],
    )
    data["elevation"] = DataArray([200, 100, 10], dims="cell_id")
    data["surface_runoff"] = DataArray([10, 50, 100], dims="cell_id")
    data["soil_moisture"] = xr.concat(
        [
            DataArray(np.full((13, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(np.full((2, 3), 0.20), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    data["soil_temperature"] = xr.concat(
        [DataArray(np.full((13, 3), np.nan)), DataArray(np.full((2, 3), 20))],
        dim="dim_0",
    )
    data["soil_temperature"] = (
        data["soil_temperature"]
        .rename({"dim_0": "layers", "dim_1": "cell_id"})
        .assign_coords(
            {
                "layers": np.arange(0, 15),
                "layer_roles": ("layers", layer_roles_fixture),
                "cell_id": data.grid.cell_id,
            }
        )
    )

    data["air_temperature"] = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.844995, 29.844995, 29.844995],
                    [28.87117, 28.87117, 28.87117],
                    [27.206405, 27.206405, 27.206405],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [16.145945, 16.145945, 16.145945],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture[0:15]),
            "cell_id": data.grid.cell_id,
        }
    )

    data["relative_humidity"] = xr.concat(
        [
            DataArray(
                [
                    [90.0, 90.0, 90.0],
                    [90.341644, 90.341644, 90.341644],
                    [92.488034, 92.488034, 92.488034],
                    [96.157312, 96.157312, 96.157312],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [100, 100, 100],
                    [100, 100, 100],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    ).assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture[0:15]),
            "cell_id": data.grid.cell_id,
        }
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
def animal_community_instance(functional_group_list_instance, animal_model_instance):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_group_list_instance,
        0,
        [0, 1, 3],
        animal_model_instance.get_community_by_key,
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
def plant_instance():
    """Fixture for a plant community used in tests."""
    from virtual_rainforest.models.animals.dummy_plants import PlantCommunity

    return PlantCommunity(10000.0)
