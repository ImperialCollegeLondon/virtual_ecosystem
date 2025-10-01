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
        [1353.0, 583.0, 248.333, 118.0, 24.0, 35.0, 11.0, 46.333, 0.0],
        [1122.667, 446.111, 404.0, 462.667, 65.444, 52.667, 40.667, 0.0, 11.222],
        [928.667, 284.778, 277.222, 552.667, 655.111, 671.667, 54.667, 42.222, 831.778],
        [1008.0, 992.333, 440.0, 582.0, 523.0, 338.333, 596.0, 548.0, 314.0],
        [619.0, 580.778, 471.222, 271.333, 293.667, 169.0, 609.333, 301.444, 175.667],
        [374.0, 415.111, 500.111, 318.667, 138.556, 91.444, 88.0, 81.0, 152.778],
        [1262.0, 316.667, 606.333, 401.0, 116.0, 110.667, 107.0, 16.0, 11.667],
        [159.333, 1121.778, 1207.222, 524.333, 253.889, 77.444, 76.667, 34.333, 9.889],
        [0.0, 820.222, 1154.889, 850.333, 299.222, 183.556, 7.333, 8.111, 17.889],
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
