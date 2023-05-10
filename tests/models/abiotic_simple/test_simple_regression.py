"""Test module for abiotic_simple.simple_regression.py."""

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray


@pytest.fixture
def layer_roles_fixture():
    """Create list of layer roles for 10 canopy layers and 2 soil layers."""
    from virtual_rainforest.models.abiotic_simple.abiotic_simple_model import (
        set_layer_roles,
    )

    return set_layer_roles(10, 2)


def test_setup_simple_regression(dummy_climate_data, layer_roles_fixture):
    """Test initialisation of variables with same dimensions."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        setup_simple_regression,
    )

    data = dummy_climate_data

    # default soil moisture
    result = setup_simple_regression(data=data, layer_roles=layer_roles_fixture)

    xr.testing.assert_allclose(
        result[1],
        DataArray(
            np.full((15, 3), np.nan),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, 15),
                "layer_roles": (
                    "layers",
                    layer_roles_fixture[0:15],
                ),
                "cell_id": [0, 1, 2],
            },
            name="relative_humidity",
        ),
    )
    xr.testing.assert_allclose(
        result[-2],
        xr.concat(
            [
                DataArray(np.full((2, 3), 50), dims=["layers", "cell_id"]),
                DataArray(np.full((13, 3), np.nan), dims=["layers", "cell_id"]),
            ],
            dim="layers",
        ).assign_coords(data["layer_heights"].coords),
    )


def test_log_interpolation(dummy_climate_data, layer_roles_fixture):
    """Test interpolation for temperature and humidity non-negative."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        log_interpolation,
    )

    data = dummy_climate_data

    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # temperature
    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=layer_roles_fixture,
        layer_heights=data["layer_heights"],
        upper_bound=80,
        lower_bound=0,
        gradient=-2.45,
    )

    exp_output = xr.concat(
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
    )
    exp_output1 = exp_output.assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture[0:15]),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result, exp_output1)

    # relative humidity
    result_hum = log_interpolation(
        data=data,
        reference_data=data["relative_humidity_ref"].isel(time=0),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_roles=layer_roles_fixture,
        layer_heights=data["layer_heights"],
        upper_bound=100,
        lower_bound=0,
        gradient=5.4,
    )
    exp_humidity = xr.concat(
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
    )
    exp_humidity = exp_humidity.assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture[0:15]),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result_hum, exp_humidity)


def test_calculate_saturation_vapor_pressure(dummy_climate_data):
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        calculate_saturation_vapor_pressure,
    )

    data = dummy_climate_data
    result = calculate_saturation_vapor_pressure(
        data["air_temperature_ref"].isel(time=0)
    )

    exp_output = DataArray(
        [1.41727, 1.41727, 1.41727],
        dims=["cell_id"],
        coords={"cell_id": data.grid.cell_id},
    )
    xr.testing.assert_allclose(result, exp_output)


def test_calculate_vapor_pressure_deficit():
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        calculate_vapor_pressure_deficit,
    )

    temperature = xr.concat(
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
    )
    rel_humidity = xr.concat(
        [
            DataArray(
                [
                    [90.0, 90.0, 90.0],
                    [88.5796455, 88.5796455, 88.5796455],
                    [79.65622765, 79.65622765, 79.65622765],
                    [64.40154408, 64.40154408, 64.40154408],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [0, 0, 0],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )

    result = calculate_vapor_pressure_deficit(
        temperature,
        rel_humidity,
    )
    exp_output = xr.concat(
        [
            DataArray(
                [
                    [0.141727, 0.141727, 0.141727],
                    [0.161233, 0.161233, 0.161233],
                    [0.280298, 0.280298, 0.280298],
                    [0.470266, 0.470266, 0.470266],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [[0.90814, 0.90814, 0.90814], [0.984889, 0.984889, 0.984889]],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    xr.testing.assert_allclose(result, exp_output)


def test_run_simple_regression(dummy_climate_data, layer_roles_fixture):
    """Test interpolation."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        run_simple_regression,
    )

    data = dummy_climate_data
    result = run_simple_regression(
        data=data,
        layer_roles=layer_roles_fixture,
        time_index=0,
    )

    exp_output = xr.concat(
        [
            DataArray(
                [
                    [30.0, 30.0, 30.0],
                    [29.91965, 29.91965, 29.91965],
                    [29.414851, 29.414851, 29.414851],
                    [28.551891, 28.551891, 28.551891],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((7, 3), np.nan), dims=["layers", "cell_id"]),
            DataArray(
                [
                    [26.19, 26.19, 26.19],
                    [22.81851, 22.81851, 22.81851],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((2, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    exp_output1 = exp_output.assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture[0:15]),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result[0], exp_output1)


def test_interpolate_soil_temperature(dummy_climate_data, layer_roles_fixture):
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        interpolate_soil_temperature,
    )

    data = dummy_climate_data

    surface_temperature = DataArray(
        [22.0, 22, 22],
        dims="cell_id",
    )
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        layer_roles=layer_roles_fixture,
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"],
    )

    exp_output = xr.concat(
        [
            DataArray(
                [
                    [22.0, 22.0, 22.0],
                    [21.42187035, 21.42187035, 21.42187035],
                    [20.0, 20.0, 20.0],
                ],
                dims=["layers", "cell_id"],
                coords={
                    "layers": [0, 1, 2],
                    "layer_roles": ("layers", layer_roles_fixture[0:3]),
                    "cell_id": [0, 1, 2],
                },
            ),
            DataArray(
                np.full((12, 3), np.nan),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(3, 15),
                    "layer_roles": ("layers", layer_roles_fixture[3:15]),
                    "cell_id": [0, 1, 2],
                },
            ),
        ],
        dim="layers",  # select bottom two
    )

    xr.testing.assert_allclose(result, exp_output)


def test_calculate_soil_moisture(dummy_climate_data, layer_roles_fixture):
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        calculate_soil_moisture,
    )

    data = dummy_climate_data
    precipitation_surface = data["precipitation"].isel(time=0) * (
        1 - 0.1 * data["leaf_area_index"].sum(dim="layers")
    )

    exp_soil_moisture = xr.concat(
        [
            DataArray(
                [[30.0, 41.0, 90.0], [30.0, 41.0, 90.0]],
                dims=["layers", "cell_id"],
            ),
            DataArray(np.full((13, 3), np.nan), dims=["layers", "cell_id"]),
        ],
        dim="layers",
    )
    exp_soil_moisture = exp_soil_moisture.assign_coords(
        {
            "layers": np.arange(0, 15),
            "layer_roles": ("layers", layer_roles_fixture[0:15]),
            "cell_id": data.grid.cell_id,
        }
    )

    exp_runoff = DataArray(
        [4, 0, 70],
        dims=["cell_id"],
        coords={"cell_id": [0, 1, 2]},
    )
    result = calculate_soil_moisture(
        layer_roles=layer_roles_fixture,
        precipitation_surface=precipitation_surface,
        current_soil_moisture=data["soil_moisture"],
        soil_moisture_capacity=DataArray([30, 60, 90], dims=["cell_id"]),
    )
    xr.testing.assert_allclose(result[0], exp_soil_moisture)
    xr.testing.assert_allclose(result[1], exp_runoff)
