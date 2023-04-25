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
data["vapor_pressure_deficit_ref"] = xr.concat(
    [
        DataArray(np.full((1, 3), 90)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
data["vapor_pressure_deficit_ref"] = data["vapor_pressure_deficit_ref"].rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)

leaf_area_index = xr.concat(
    [
        DataArray(np.full((1, 3), 3)),
        DataArray(np.full((len(layer_roles) - 1, 3), np.nan)),
    ],
    dim="dim_0",
)
leaf_area_index = leaf_area_index.rename({"dim_0": "layers", "dim_1": "cell_id"})

canopy_node_heights = xr.concat(
    [
        DataArray(np.full((1, 3), np.nan)),
        DataArray([[30, 30, 30], [20, 20, 20], [10, 10, 10]]),
        DataArray(np.full((11, 3), np.nan)),
    ],
    dim="dim_0",
)
canopy_node_heights = canopy_node_heights.rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)
atmosphere_node_heights = xr.concat(
    [
        DataArray([[32, 32, 32], [30, 30, 30], [20, 20, 20], [10, 10, 10]]),
        DataArray(np.full((7, 3), np.nan)),
        DataArray([[1.5, 1.5, 1.5], [0.1, 0.1, 0.1]]),
        DataArray(np.full((2, 3), np.nan)),
    ],
    dim="dim_0",
)
atmosphere_node_heights = atmosphere_node_heights.rename(
    {"dim_0": "layers", "dim_1": "cell_id"}
)
soil_node_depths = xr.concat(
    [
        DataArray(np.full((13, 3), np.nan)),
        DataArray([[-0.1, -0.1, -0.1], [-1, -1, -1]]),
    ],
    dim="dim_0",
)
soil_node_depths = soil_node_depths.rename({"dim_0": "layers", "dim_1": "cell_id"})


def test_setup_simple_regression():
    """Test initialisation of variables."""

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
            name="air_temperature_min",
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
            name="air_temperature_max",
        ),
    )


def test_run_simple_regression():
    """Test interpolation."""

    from virtual_rainforest.models.abiotic.simple_regression import (
        run_simple_regression,
        setup_simple_regression,
    )

    variable_list = setup_simple_regression(layer_roles, data=data)
    input_list = []
    for i in range(0, len(variable_list)):
        input_name = variable_list[i].name
        input_list.append(input_name)

    result = run_simple_regression(
        data=data,
        layer_roles=layer_roles,
        input_list=input_list,
        canopy_node_heights=canopy_node_heights,
        atmosphere_node_heights=atmosphere_node_heights,
        soil_node_depths=soil_node_depths,
        leaf_area_index=leaf_area_index,
    )

    xr.testing.assert_allclose(
        result[0].isel(layers=[1, 2, 3]),
        DataArray(
            [
                [29.994939, 29.994939, 29.994939],
                [29.96314, 29.96314, 29.96314],
                [29.908781, 29.908781, 29.908781],
            ],
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(1, 4),
                "layer_roles": (
                    "layers",
                    layer_roles[1:4],
                ),
                "cell_id": data.grid.cell_id,
            },
            name="air_temperature_min",
        ),
    )
    xr.testing.assert_allclose(
        result[0].isel(layers=[0]),
        DataArray(
            [[30.0, 30.0, 30.0]],
            dims=["layers", "cell_id"],
            coords={
                "layers": [0],
                "layer_roles": (
                    "layers",
                    [layer_roles[0]],
                ),
                "cell_id": data.grid.cell_id,
            },
            name="air_temperature_min",
        ),
    )
    xr.testing.assert_allclose(
        result[2].isel(layers=[0]),
        DataArray(
            [[90, 90, 90]],
            dims=["layers", "cell_id"],
            coords={
                "layers": [0],
                "layer_roles": (
                    "layers",
                    [layer_roles[0]],
                ),
                "cell_id": data.grid.cell_id,
            },
            name="relative_humidity_min",
        ),
    )
