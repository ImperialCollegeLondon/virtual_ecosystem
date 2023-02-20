"""Test module for wind.py."""

# from contextlib import nullcontext as does_not_raise

import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["canopy_height"] = DataArray([10, 50], dims=["cell_id"])
    data["leaf_area_index"] = DataArray(
        [
            [1, 2, 3],
            [1, 2, 3],
        ],
        dims=["cell_id", "canopy_layers"],
    )
    data["temperature_2m"] = DataArray([10, 20], dims=["cell_id"])
    data["atmospheric_pressure"] = DataArray([101, 101], dims=["cell_id"])
    data["sensible_heat_flux_top"] = DataArray([50, 10], dims=["cell_id"])
    data["friction_velocity"] = DataArray([12, 2], dims=["cell_id"])

    return data


def test_calculate_zero_plane_displacement(dummy_data):
    """Test zero plane displacement."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_zero_plane_displacement(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
    )

    xr.testing.assert_allclose(
        result, DataArray([8.51110796, 42.55553979], dims=["cell_id"])
    )


def test_calculate_roughness_length_momentum(dummy_data):
    """Test roughness length governing momentum transfer.

    TODO test different cases
    """

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_roughness_length_momentum(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
        zero_plane_displacement=DataArray([10, 20], dims="cell_id"),
    )

    xr.testing.assert_allclose(result, DataArray([0.0, 16.236493], dims=["cell_id"]))


def test_calculate_mixing_length(dummy_data):
    """Test."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_mixing_length(
        canopy_height=dummy_data.data["canopy_height"],
        zero_plane_displacement=DataArray([10, 20], dims="cell_id"),
        roughness_length_momentum=1,
    )

    xr.testing.assert_allclose(result, DataArray([0, 2.822535], dims=["cell_id"]))


def test_calculate_wind_attenuation_coefficient(dummy_data):
    """Test calculate wind attenuation coefficient."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_attenuation_coefficient(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
        mixing_length=DataArray([5, 10], dims=["cell_id"]),
    )

    xr.testing.assert_allclose(result, DataArray([1.549193, 2.44949], dims=["cell_id"]))


def test_calc_molar_density_air(dummy_data):
    """Test."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calc_molar_density_air(
        temperature=dummy_data.data["temperature_2m"],
        atmospheric_pressure=dummy_data.data["atmospheric_pressure"],
    )
    xr.testing.assert_allclose(
        result, DataArray([120.618713, 120.618713], dims=["cell_id"])
    )


def test_calc_specific_heat_air(dummy_data):
    """Test."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calc_specific_heat_air(temperature=dummy_data.data["temperature_2m"])

    xr.testing.assert_allclose(result, DataArray([29.194, 29.202], dims=["cell_id"]))


def test_calculate_wind_above_canopy():
    """Test wind above canopy."""
    pass


def test_calculate_wind_below_canopy():
    """Test wind below canopy."""
    pass


def test_calculate_wind_profile():
    """Test wind profile."""
    pass
