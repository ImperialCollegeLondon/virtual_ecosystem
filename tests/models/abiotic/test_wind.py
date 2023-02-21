"""Test module for wind.py."""

# from contextlib import nullcontext as does_not_raise

import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def dummy_data():
    """Creates a dummy data object for use in wind tests."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    # Setup the data object with two cells.
    grid = Grid(cell_nx=2, cell_ny=1)
    data = Data(grid)

    # Add the required data.
    data["canopy_height"] = DataArray([10, 50], dims=["cell_id"])
    data["canopy_node_heights"] = DataArray(
        [[1, 5, 10], [1, 15, 25]], dims=["cell_id", "canopy_layers"]
    )
    data["leaf_area_index"] = DataArray(
        [
            [1, 2, 3],
            [1, 2, 3],
        ],
        dims=["cell_id", "canopy_layers"],
    )
    data["temperature_2m"] = DataArray([10, 30], dims=["cell_id"])
    data["atmospheric_pressure"] = DataArray([101, 103], dims=["cell_id"])
    data["sensible_heat_flux_top"] = DataArray([50, 10], dims=["cell_id"])
    data["friction_velocity"] = DataArray([12, 2], dims=["cell_id"])

    return data


def test_calculate_zero_plane_displacement(dummy_data):
    """Test zero plane displacement calculated correctly."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_zero_plane_displacement(
        canopy_height=dummy_data.data["canopy_height"],
        leaf_area_index=dummy_data.data["leaf_area_index"],
    )

    xr.testing.assert_allclose(result, DataArray([8.51111, 42.55554], dims=["cell_id"]))


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
        roughness_length_momentum=DataArray([1, 1], dims="cell_id"),
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
        result, DataArray([120.618713, 118.276602], dims=["cell_id"])
    )


def test_calc_specific_heat_air(dummy_data):
    """Test."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calc_specific_heat_air(temperature=dummy_data.data["temperature_2m"])

    xr.testing.assert_allclose(result, DataArray([29.194, 29.214], dims=["cell_id"]))


def test_calculate_wind_above_canopy(dummy_data):
    """Test wind above canopy."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_above_canopy(
        wind_heights=DataArray(
            [[50, 70], [50, 80], [50, 100]], dims=["heights", "cell_id"]
        ),
        zero_plane_displacement=DataArray([10, 20], dims="cell_id"),
        roughness_length_momentum=DataArray([1, 1], dims="cell_id"),
        diabatic_correction_momentum_above=DataArray(
            [[1, 1], [1, 1], [1, 1]], dims=["heights", "cell_id"]
        ),
        friction_velocity=dummy_data["friction_velocity"],
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[111.666384, 111.666384, 111.666384], [20.560115, 21.471723, 22.910133]],
            dims=["cell_id", "heights"],
        ),
    )


def test_calculate_wind_below_canopy(dummy_data):
    """Test wind below canopy."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_below_canopy(
        canopy_node_heights=dummy_data.data["canopy_node_heights"],
        wind_profile_above=DataArray(
            [[1, 2, 3], [4, 5, 6]],
            dims=["cell_id", "heights"],
        ),
        wind_attenuation_coefficient=DataArray([1, 2], dims=["cell_id"]),
        canopy_height=dummy_data.data["canopy_height"],
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [[1.219709, 1.819592, 3.0], [0.845151, 1.479582, 2.207277]],
            dims=["cell_id", "canopy_layers"],
        ),
    )


def test_calculate_wind_profile(dummy_data):
    """Test wind profile."""

    from virtual_rainforest.models.abiotic import wind

    result = wind.calculate_wind_profile(
        wind_heights=DataArray(
            [[50, 70], [50, 80], [50, 100]], dims=["heights", "cell_id"]
        ),
        canopy_node_heights=dummy_data.data["canopy_node_heights"],
        data=dummy_data,
    )

    # check wind above canopy
    xr.testing.assert_allclose(
        result[0],
        DataArray(
            [[111.241788, 111.241788, 111.241788], [21.424657, 22.202161, 23.46772]],
            dims=["cell_id", "heights"],
        ),
    )
    # check wind below canopy
    xr.testing.assert_allclose(
        result[1],
        DataArray(
            [[3.230525, 15.573346, 111.241788], [0.49757, 1.496341, 3.285374]],
            dims=["cell_id", "canopy_layers"],
        ),
    )
