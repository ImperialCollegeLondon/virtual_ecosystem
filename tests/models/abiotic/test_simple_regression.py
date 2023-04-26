"""Test module for abiotic.simple_regression.py."""

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
data["air_temperature_ref"] = xr.concat(
    [
        DataArray(np.full((1, 3), 30)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
data["air_temperature_ref"] = data["air_temperature_ref"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)
data["relative_humidity_ref"] = xr.concat(
    [
        DataArray(np.full((1, 3), 90)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
data["relative_humidity_ref"] = data["relative_humidity_ref"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)
data["atmospheric_pressure_ref"] = xr.concat(
    [
        DataArray(np.full((1, 3), 1)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
data["atmospheric_pressure_ref"] = data["atmospheric_pressure_ref"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)

data["atmospheric_co2_ref"] = xr.concat(
    [
        DataArray(np.full((1, 3), 1)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
data["atmospheric_co2_ref"] = data["atmospheric_co2_ref"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
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
        DataArray(np.full((2, 3), np.nan)),
    ],
    dim="dim_0",
)
data["layer_heights"] = data["layer_heights"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)


def test_setup_simple_regression():
    """Test initialisation of variables with same dimensions."""

    from virtual_rainforest.models.abiotic.simple_regression import (
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
    from virtual_rainforest.models.abiotic.simple_regression import lai_regression

    result = lai_regression(
        reference_data=data["air_temperature_ref"].isel(layers=0),
        leaf_area_index=data["leaf_area_index"],
        gradient=-2.45,
    )

    xr.testing.assert_allclose(result, DataArray([22.65, 22.65, 22.65], dims="cell_id"))


def test_log_interpolation():
    """Test."""

    from virtual_rainforest.models.abiotic.simple_regression import (
        lai_regression,
        log_interpolation,
    )

    value_from_lai_regression = lai_regression(
        reference_data=data["air_temperature_ref"].isel(layers=0),
        leaf_area_index=data["leaf_area_index"],
        gradient=-2.45,
    )

    result = log_interpolation(
        data=data,
        reference_data=data["air_temperature_ref"].isel(layers=0),
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

    from virtual_rainforest.models.abiotic.simple_regression import (
        calculate_saturation_vapor_pressure,
    )

    result = calculate_saturation_vapor_pressure(data["air_temperature_ref"])

    exp_output = xr.concat(
        [
            DataArray(
                [
                    [1.41727, 1.41727, 1.41727],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((14, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    )
    xr.testing.assert_allclose(result, exp_output)


def test_calculate_vapor_pressure_deficit():
    """Test."""

    from virtual_rainforest.models.abiotic.simple_regression import (
        calculate_vapor_pressure_deficit,
    )

    result = calculate_vapor_pressure_deficit(
        data["air_temperature_ref"],
        data["relative_humidity_ref"],
    )
    exp_output = xr.concat(
        [
            DataArray(
                [
                    [0.141727, 0.141727, 0.141727],
                ],
                dims=["layers", "cell_id"],
            ),
            DataArray(
                np.full((14, 3), np.nan),
                dims=["layers", "cell_id"],
            ),
        ],
        dim="layers",
    )
    xr.testing.assert_allclose(result, exp_output)


def test_run_simple_regression():
    """Test interpolation."""

    from virtual_rainforest.models.abiotic.simple_regression import (
        run_simple_regression,
    )

    result = run_simple_regression(
        data=data,
        layer_roles=layer_roles,
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
