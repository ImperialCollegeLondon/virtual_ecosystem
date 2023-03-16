"""Test atmospheric_co2.py."""

import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def dummy_data():
    """Creates a dummy data object with input data for use in atmospheric CO2 tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["atmosperic_co2"] = DataArray([390, 395], dims=["cell_id"])
    data["plant_net_co2_assimilation"] = DataArray(
        [[30, 30], [20, 20], [10, 10]], dims=["canopy_layers", "cell_id"]
    )
    data["soil_respiration"] = DataArray([30, 35], dims=["cell_id"])
    data["animal_respiration"] = DataArray([30, 35], dims=["cell_id"])

    return data


@pytest.fixture
def dummy_data_empty():
    """Creates an empty dummy data object."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data_empty = Data(grid)

    return data_empty


def test_calculate_co2_profile(dummy_data, dummy_data_empty):
    """Test default values."""

    from virtual_rainforest.models.abiotic import atmospheric_co2

    data = dummy_data
    result = atmospheric_co2.calculate_co2_profile(data, 5)

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[400, 370, 380, 390, 460], [400, 370, 380, 390, 470]],
            dims=["cell_id", "atmosphere_layers"],
        ),
    )

    data1 = dummy_data_empty
    result1 = atmospheric_co2.calculate_co2_profile(data1, 5)

    xr.testing.assert_allclose(
        result1,
        DataArray(
            [[400, 400, 400, 400, 400], [400, 400, 400, 400, 400]],
            dims=["cell_id", "atmosphere_layers"],
        ),
    )
