---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: vr_python3
  language: python
  name: vr_python3
---

# Essential plant data for dummy model

The first dummy version of the Virtual Rainforest does not include a `plant` model.
Therefore, the variables that would be initialized by the `plant` module need to be
provided as an input to the `data` object at the configuration stage. The following code
section provides a recipe to create such an input conform with the dummy data for
[climate](./ERA5_preprocessing_example.md) and soil (add link here).

```{code-cell} ipython3
import xarray as xr
import numpy as np
from xarray import DataArray

# set layer roles
layer_roles = ["above"] + 10 * ["canopy"] + ["subcanopy"] + ["surface"] + 2 * ["soil"]

plant_dummy = {}
layer_heights = np.repeat(
        a=[32.0, 30.0, 20.0, 10.0, np.nan, 1.5, 0.1, -0.1, -1.0],
        repeats=[1, 1, 1, 1, 7, 1, 1, 1, 1],
    )
plant_dummy["layer_heights"] = DataArray(
        np.broadcast_to(layer_heights, (81, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles),
            "cell_id": np.arange(0,81),
        },
        name="layer_heights",
    )

leaf_area_index = np.repeat(a=[np.nan, 1.0, np.nan], repeats=[1, 3, 11])
plant_dummy["leaf_area_index"] = DataArray(
        np.broadcast_to(leaf_area_index, (81, 15)).T,
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(15),
            "layer_roles": ("layers", layer_roles),
            "cell_id": np.arange(0,81),
        },
        name="leaf_area_index",
)
plant_dummy
```

```{code-cell} ipython3
# write to NetCDF
xr.Dataset(plant_dummy).to_netcdf("./plants_dummy.nc")
```
