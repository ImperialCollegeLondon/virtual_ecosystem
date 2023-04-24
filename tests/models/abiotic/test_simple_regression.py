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
    )

    result = run_simple_regression(
        data=data,
        layer_roles=layer_roles,
        canopy_node_heights=canopy_node_heights,
        leaf_area_index=leaf_area_index,
    )
    print(result)

    xr.testing.assert_allclose(
        result[0].isel(layers=[1, 2, 3]),
        DataArray(
            [
                [30.0, 30.0, 30.0],
                [29.96751658, 29.96751658, 29.96751658],
                [29.91198581, 29.91198581, 29.91198581],
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
            np.full((1, 3), np.nan),
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
