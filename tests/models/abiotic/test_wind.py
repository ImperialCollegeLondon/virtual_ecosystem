"""Test module for wind.py."""


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
    data["canopy_height"] = DataArray([0, 10, 50], dims=["cell_id"])
    data["canopy_node_heights"] = DataArray(
        [[0, 5, 15], [0, 15, 25], [0, 25, 35]], dims=["cell_id", "canopy_layers"]
    )
    data["leaf_area_index"] = DataArray(
        [
            [0, 1, 5],
            [0, 2, 5],
            [0, 3, 5],
        ],
        dims=["cell_id", "canopy_layers"],
    )
    data["temperature_2m"] = DataArray([30, 20, 30], dims=["cell_id"])
    data["atmospheric_pressure"] = DataArray([101, 102, 103], dims=["cell_id"])
    data["sensible_heat_flux"] = DataArray([100, 50, 10], dims=["cell_id"])
    data["friction_velocity"] = DataArray([12, 5, 2], dims=["cell_id"])

    return data


def test_calculate_zero_plane_displacement(dummy_data):
    """Test if calculated correctly and set to zero without vegetation."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_zero_plane_displacement(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
    )

    xr.testing.assert_allclose(
        result, DataArray([0.0, 8.620853, 43.547819], dims=["cell_id"])
    )


def test_calculate_roughness_length_momentum(dummy_data):
    """Test roughness length governing momentum transfer."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_roughness_length_momentum(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
        zero_plane_displacement=DataArray([0, 8, 43], dims="cell_id"),
    )

    xr.testing.assert_allclose(
        result, DataArray([0.003, 0.434662, 1.521318], dims=["cell_id"])
    )


def test_calculate_mixing_length(dummy_data):
    """Test mixing length with and withour vegetation."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_mixing_length(
        canopy_height=dummy_data.data["canopy_height"],
        zero_plane_displacement=DataArray([0, 10, 20], dims="cell_id"),
        roughness_length_momentum=DataArray([0, 1, 1], dims="cell_id"),
    )

    xr.testing.assert_allclose(result, DataArray([0, 0, 2.822535], dims=["cell_id"]))


def test_calculate_wind_attenuation_coefficient(dummy_data):
    """Test wind attenuation coefficient with and without vegetation."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_attenuation_coefficient(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
        mixing_length=DataArray([0, 5, 10], dims=["cell_id"]),
    )

    xr.testing.assert_allclose(
        result, DataArray([0.0, 1.67332, 2.828427], dims=["cell_id"])
    )


def test_calculate_wind_above_canopy(dummy_data):
    """Test wind above canopy."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_above_canopy(
        wind_heights=DataArray(
            [[10, 20, 30], [20, 30, 40], [40, 50, 60]], dims=["heights", "cell_id"]
        ),
        zero_plane_displacement=DataArray([0, 10, 10], dims="cell_id"),
        roughness_length_momentum=DataArray([0.003, 0.4, 1.5], dims="cell_id"),
        diabatic_correction_momentum_above=DataArray(
            [[1, 1, 1], [1, 1, 1], [1, 1, 1]], dims=["heights", "cell_id"]
        ),
        friction_velocity=dummy_data["friction_velocity"],
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [
                [244.3518425, 265.14625792, 285.94067333],
                [41.23594781, 49.90028757, 58.56462732],
                [13.95133583, 15.97866137, 18.53278949],
            ],
            dims=["cell_id", "heights"],
        ),
    )


def test_calculate_wind_below_canopy(dummy_data):
    """Test wind within canopy."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_below_canopy(
        canopy_node_heights=dummy_data.data["canopy_node_heights"],
        wind_profile_above=DataArray(
            [
                [244.0, 265.0, 285.0],
                [41.0, 49.0, 58.0],
                [13.0, 15.0, 18.0],
            ],
            dims=["cell_id", "heights"],
        ),
        wind_attenuation_coefficient=DataArray([0, 0.1, 0.3], dims=["cell_id"]),
        canopy_height=dummy_data.data["canopy_height"],
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [
                [0.0, 0.0, 0.0],
                [52.48057, 60.973724, 67.386386],
                [13.334728, 15.492744, 16.450761],
            ],
            dims=["cell_id", "canopy_layers"],
        ),
    )


def test_calculate_wind_profile(dummy_data):
    """Test wind profile above and within canopy."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_profile(
        wind_heights=DataArray(
            [[10, 20, 30], [20, 30, 40], [40, 50, 60]], dims=["heights", "cell_id"]
        ),
        canopy_node_heights=dummy_data.data["canopy_node_heights"],
        data=dummy_data,
    )

    # check wind above canopy
    xr.testing.assert_allclose(
        result[0],
        DataArray(
            DataArray(
                [
                    [244.351842, 265.146258, 285.940673],
                    [46.458135, 54.341054, 62.595567],
                    [0.0, 0.0, 13.311866],
                ],
                dims=["cell_id", "heights"],
            ),
        ),
    )
    # check wind below canopy
    xr.testing.assert_allclose(
        result[1],
        DataArray(
            [
                [0.0, 0.0, 0.0],
                [5.950523e-02, 2.030195e03, 2.135631e06],
                [6.086929e-03, 2.846548e-01, 1.325216e00],
            ],
            dims=["cell_id", "canopy_layers"],
        ),
    )
