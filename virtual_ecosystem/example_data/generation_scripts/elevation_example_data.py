"""Elevation data for `ve_run` example.

This code creates an example elevation map from a digital elevation model
([SRTM](https://www2.jpl.nasa.gov/srtm/)) which is required to run the example hydrology
model.

The commented code is used to download an existing processed SRTM dataset for the SAFE
Project area, covering the region 4°N 116°E to 5°N 117°E, see [SAFE
wiki](https://safeproject.net/dokuwiki/safe_gis/srtm) for reference. The processed
datafile can be downloaded from its [Zenodo record](https://zenodo.org/records/3490488).
The dataset is then downscaled to match the required target resolution of 90m. At the
moment this does not _actually_ align with the climate data, it is simply forced to the
same coordinates and resolution.

To save processing and to avoid adding requirements to the package, the resulting data
is simply stored here and written to an appropriate file format.
"""

import numpy as np
from xarray import DataArray

from virtual_ecosystem.example_data.generation_scripts.common import cell_displacements

# # Load DEM in 30m resolution
# original_data = requests.get(
#     "https://zenodo.org/records/3490488/files/SRTM_UTM50N_processed.tif"
# )

# data_path = Path("SRTM_UTM50N_processed.tif")
# with open(data_path, "wb") as f:
#     f.write(original_data.content)

# dem = rioxarray.open_rasterio("SRTM_UTM50N_processed.tif")

# # Specify the original grid coordinates
# x = dem.coords["x"]  # type: ignore
# y = dem.coords["y"]  # type: ignore

# # Create a new grid of longitude and latitude coordinates with higher resolution
# new_resolution = 26000
# new_x = np.arange(x.min(), x.max(), new_resolution)  # type: ignore
# new_y = np.arange(y.min(), y.max(), new_resolution)  # type: ignore

# # Project DEM to new mesh
# dem_9x9 = dem.interp(x=new_x, y=new_y)  # type: ignore

# # Reduce the data to reuired information for netcdf
# dem_cleaned = (
#     dem_9x9.drop_vars(
#       ["band", "spatial_ref"]
#     ).squeeze("band").drop_indexes(["x", "y"])
# )

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
dem_cleaned = DataArray(name="elevation", data=dem_data, dims=("x", "y"))

# Change coordinates to match exmple data grid
dem_placed = dem_cleaned.assign_coords(
    {"x": cell_displacements, "y": cell_displacements}
)

# Save to netcdf and remove downloaded data
dem_placed.to_netcdf("../data/example_elevation_data.nc")
