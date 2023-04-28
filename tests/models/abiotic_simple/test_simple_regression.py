"""Test module for abiotic_simple.simple_regression.py."""

import numpy as np
import xarray as xr
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.grid import Grid

# test data set
layer_roles = [
    "above",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "canopy",
    "subcanopy",
    "surface",
    "soil",
    "soil",
]


# Setup the data object with two cells.
grid = Grid(cell_nx=3, cell_ny=1)
data = Data(grid)

# Add the required data.
data["air_temperature_ref"] = DataArray(
    np.full((3, 3), 30),
    dims=["cell_id", "time"],
)
data["mean_annual_temperature"] = DataArray(
    np.full((3), 20),
    dims=["cell_id"],
)
data["relative_humidity_ref"] = DataArray(
    np.full((3, 3), 90),
    dims=["cell_id", "time"],
)
data["atmospheric_pressure_ref"] = DataArray(
    np.full((3, 3), 1.5),
    dims=["cell_id", "time"],
)
data["atmospheric_co2_ref"] = DataArray(
    np.full((3, 3), 400),
    dims=["cell_id", "time"],
)

data["leaf_area_index"] = xr.concat(
    [
        DataArray(np.full((1, 3), 3)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
data["leaf_area_index"] = data["leaf_area_index"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)

data["layer_heights"] = xr.concat(
    [
        DataArray([[32, 32, 32], [30, 30, 30], [20, 20, 20], [10, 10, 10]]),
        DataArray(np.full((7, 3), np.nan)),
        DataArray([[1.5, 1.5, 1.5], [0.1, 0.1, 0.1]]),
        DataArray([[-0.1, -0.1, -0.1], [-1, -1, -1]]),
    ],
    dim="dim_0",
)
data["layer_heights"] = (
    data["layer_heights"]
    .rename({"dim_0": "layers", "dim_1": "cell_id"})
    .assign_coords(
        {
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        }
    )
)


def test_setup_simple_regression():
    """Test initialisation of variables with same dimensions."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        setup_simple_regression,
    )

    result = setup_simple_regression(data=data, layer_roles=layer_roles)

    xr.testing.assert_allclose(
        result[0],
        DataArray(
            np.full((len(layer_roles), len(data.grid.cell_id)), np.nan),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, len(layer_roles)),
                "layer_roles": (
                    "layers",
                    layer_roles[0 : len(layer_roles)],
                ),
                "cell_id": data.grid.cell_id,
            },
            name="air_temperature",
        ),
    )
    xr.testing.assert_allclose(
        result[1],
        DataArray(
            np.full((len(layer_roles), len(data.grid.cell_id)), np.nan),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, len(layer_roles)),
                "layer_roles": (
                    "layers",
                    layer_roles[0 : len(layer_roles)],
                ),
                "cell_id": data.grid.cell_id,
            },
            name="relative_humidity",
        ),
    )


def test_lai_regression():
    """Test lai regression."""
    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        lai_regression,
    )

    result = lai_regression(
        reference_data=data["air_temperature_ref"].isel(time=0),
        leaf_area_index=data["leaf_area_index"],
        gradient=-2.45,
    )

    xr.testing.assert_allclose(
        result,
        DataArray(
            [22.65, 22.65, 22.65],
            dims="cell_id",
            coords={
                "cell_id": data.grid.cell_id,
            },
        ),
    )


def test_log_interpolation():
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        lai_regression,
        log_interpolation,
    )

    value_from_lai_regression = lai_regression(
        reference_data=data["air_temperature_ref"].isel(time=0),
        leaf_area_index=data["leaf_area_index"],
        gradient=-2.45,
    )

    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(time=0),
        layer_roles=layer_roles,
        layer_heights=data["layer_heights"],
        value_from_lai_regression=value_from_lai_regression,
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
            DataArray(
                np.full((7, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [16.145945, 16.145945, 16.145945],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((2, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    )
    exp_output1 = exp_output.assign_coords(
        {
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result, exp_output1)


def test_calculate_saturation_vapor_pressure():
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        calculate_saturation_vapor_pressure,
    )

    result = calculate_saturation_vapor_pressure(
        data["air_temperature_ref"].isel(time=0)
    )

    exp_output = DataArray(
        [1.41727, 1.41727, 1.41727],
        dims=["cell_id"],
        coords={
            "cell_id": data.grid.cell_id,
        },
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
            DataArray(
                np.full((7, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [16.145945, 16.145945, 16.145945],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((2, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
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
            DataArray(
                np.full((7, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [
                    [22.65, 22.65, 22.65],
                    [-36.94837978, -36.94837978, -36.94837978],
                ],  # TODO set boundaries
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((2, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
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
            DataArray(
                np.full((7, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [[0.90814, 0.90814, 0.90814], [1.34879, 1.34879, 1.34879]],
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((2, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    )
    xr.testing.assert_allclose(result, exp_output)


def test_run_simple_regression():
    """Test interpolation."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        run_simple_regression,
    )

    result = run_simple_regression(
        data=data,
        layer_roles=layer_roles,
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
            DataArray(
                np.full((7, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
            DataArray(
                [
                    [26.19, 26.19, 26.19],
                    [22.81851, 22.81851, 22.81851],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((2, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    )
    exp_output1 = exp_output.assign_coords(
        {
            "layers": np.arange(0, len(layer_roles)),
            "layer_roles": (
                "layers",
                layer_roles[0 : len(layer_roles)],
            ),
            "cell_id": data.grid.cell_id,
        }
    )
    xr.testing.assert_allclose(result[0], exp_output1)


def test_interpolate_soil_temperature():
    """Test."""

    from virtual_rainforest.models.abiotic_simple.simple_regression import (
        interpolate_soil_temperature,
    )

    surface_temperature = DataArray(
        [22.81851036, 22.81851036, 22.81851036],
        dims="cell_id",
    )
    result = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        layer_roles=layer_roles,
        surface_temperature=surface_temperature,
        mean_annual_temperature=data["mean_annual_temperature"],
    )

    exp_output = xr.concat(
        [
            DataArray(
                np.full(
                    (13, 3),
                    np.nan,
                ),
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(0, 13),
                    "layer_roles": (
                        "layers",
                        layer_roles[0:13],
                    ),
                    "cell_id": [0, 1, 2],
                },
            ),
            DataArray(
                [[22.00377816, 22.00377816, 22.00377816], [20.0, 20.0, 20.0]],
                dims=["layers", "cell_id"],
                coords={
                    "layers": np.arange(13, 15),
                    "layer_roles": (
                        "layers",
                        layer_roles[13:15],
                    ),
                    "cell_id": [0, 1, 2],
                },
            ),
        ],
        dim="layers",  # select bottom two
    )

    xr.testing.assert_allclose(result, exp_output)
