"""Elevation data for `ve_run` example.

This code creates a dummy elevation map which is required to run the Virtual
Ecosystem example.
"""

import numpy as np
from xarray import DataArray, Dataset

from virtual_ecosystem.example_data.generation_scripts.common import cell_displacements

# Create a simple digital elevation model (DEM) for 9x9 grid as a DataArray
# Values are in meters above sea level

dem_data = np.array(
    [
        [300, 250, 200, 150, 100, 150, 200, 250, 300],
        [260, 210, 160, 110, 70, 120, 170, 220, 270],
        [220, 170, 120, 80, 50, 100, 150, 200, 250],
        [180, 140, 100, 60, 30, 70, 120, 170, 220],
        [140, 110, 80, 40, 25, 50, 100, 150, 200],
        [100, 80, 50, 25, 15, 14, 80, 130, 180],
        [140, 100, 70, 40, 20, 8, 50, 100, 160],
        [180, 140, 100, 70, 50, 7, 6, 60, 120],
        [220, 180, 140, 100, 80, 60, 5, 4, 0],
    ]
)


dem = DataArray(
    data=dem_data,
    dims=("x", "y"),
    coords={"x": cell_displacements, "y": cell_displacements},
    attrs={"units": "m", "description": "Height above sea level"},
)

# Save to netcdf
ds = Dataset(
    {"elevation": dem},
    attrs={
        "dataset_description": """This dataset contains a simple digital elevation map 
        for the simulation, required to run the
        {mod}`~virtual_ecosystem.models.hydrology.hydrology_model`."""
    },
)

ds.to_netcdf("../data/example_elevation_data.nc")
