"""Necessary plant data for `vr_run` example without plant model.

The first dummy version of the Virtual Rainforest does not include a `plant` model.
Therefore, the variables that would be initialized by the `plant` module need to be
provided as an input to the `data` object at the configuration stage. The following code
section provides a recipe to create such an input conform with the dummy data for
climate, hydrology, and soil.
"""

import numpy as np
from xarray import DataArray, Dataset

from virtual_rainforest.core.utils import set_layer_roles

layer_roles = set_layer_roles(10, [-0.5, -1.0])

# Compile a dataset

plant_dummy_dataset = Dataset()
layer_heights = np.repeat(
    a=[32.0, 30.0, 20.0, 10.0, np.nan, 1.5, 0.1, -0.1, -1.0],
    repeats=[1, 1, 1, 1, 7, 1, 1, 1, 1],
)
plant_dummy_dataset["layer_heights"] = DataArray(
    np.broadcast_to(layer_heights, (81, 15)).T,
    dims=["layers", "cell_id"],
    coords={
        "layers": np.arange(15),
        "layer_roles": ("layers", layer_roles),
        "cell_id": np.arange(0, 81),
    },
    name="layer_heights",
)

leaf_area_index = np.repeat(a=[np.nan, 1.0, np.nan], repeats=[1, 3, 11])
plant_dummy_dataset["leaf_area_index"] = DataArray(
    np.broadcast_to(leaf_area_index, (81, 15)).T,
    dims=["layers", "cell_id"],
    coords={
        "layers": np.arange(15),
        "layer_roles": ("layers", layer_roles),
        "cell_id": np.arange(0, 81),
    },
    name="leaf_area_index",
)

layer_leaf_mass = np.repeat(a=[np.nan, 10000.0, np.nan], repeats=[1, 3, 11])
plant_dummy_dataset["layer_leaf_mass"] = DataArray(
    np.broadcast_to(leaf_area_index, (81, 15)).T,
    dims=["layers", "cell_id"],
    coords={
        "layers": np.arange(15),
        "layer_roles": ("layers", layer_roles),
        "cell_id": np.arange(0, 81),
    },
    name="layer_leaf_mass",
)

evapotranspiration = np.repeat(a=[np.nan, 20.0, np.nan], repeats=[1, 3, 11])
plant_dummy_dataset["evapotranspiration"] = DataArray(
    np.broadcast_to(evapotranspiration, (81, 15)).T,
    dims=["layers", "cell_id"],
    coords={
        "layers": np.arange(15),
        "layer_roles": ("layers", layer_roles),
        "cell_id": np.arange(0, 81),
    },
    name="evapotranspiration",
)

# write to NetCDF
plant_dummy_dataset.to_netcdf("./plants_dummy.nc")
