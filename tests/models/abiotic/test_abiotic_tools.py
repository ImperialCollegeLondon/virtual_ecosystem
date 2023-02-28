"""Test abiotic_tools.py."""

import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in wind tests.

    One grid cell has no vegetation, two grid cells represent a range of values.
    """

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=3, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["temperature_2m"] = DataArray([30, 20, 30], dims=["cell_id"])
    data["atmospheric_pressure"] = DataArray([101, 102, 103], dims=["cell_id"])

    return data


def test_calc_molar_density_air(dummy_data):
    """Test calculate molar desity of air."""

    from virtual_rainforest.models.abiotic import abiotic_tools

    result = abiotic_tools.calc_molar_density_air(
        temperature=dummy_data.data["temperature_2m"],
        atmospheric_pressure=dummy_data.data["atmospheric_pressure"],
    )
    xr.testing.assert_allclose(
        result, DataArray([120.618713, 119.436176, 118.276602], dims=["cell_id"])
    )


def test_calc_specific_heat_air(dummy_data):
    """Test canclualte specific heat of air."""

    from virtual_rainforest.models.abiotic import abiotic_tools

    result = abiotic_tools.calc_specific_heat_air(
        temperature=dummy_data.data["temperature_2m"]
    )

    xr.testing.assert_allclose(
        result, DataArray([29.214, 29.202, 29.214], dims=["cell_id"])
    )
