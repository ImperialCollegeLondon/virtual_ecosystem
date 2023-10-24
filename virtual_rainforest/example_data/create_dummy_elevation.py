"""Elevation data for `vr_run` example.

This code creates a dummy elevation map from a digital elevation model
([SRTM](https://www2.jpl.nasa.gov/srtm/)) which is required to run a dummy hydrology
model. To cover an area similar to the climate dummy data, we included a step that
reduces that spatial resolution to match the 9 x 9 grid we set for the dummy model.
The initial data covers the region 4°N 116°E to 5°N 117°E, see
[SAFE wiki](https://safeproject.net/dokuwiki/safe_gis/srtm) for reference and download.
"""

import numpy as np
import rioxarray

# Load DEM in 30m resolution
dem = rioxarray.open_rasterio("your_path/SRTM_UTM50N_processed.tif")

# Specify the original grid coordinates
x = dem.coords["x"]  # type: ignore  # noqa
y = dem.coords["y"]  # type: ignore  # noqa

# Create a new grid of longitude and latitude coordinates with higher resolution
new_resolution = 26000
new_x = np.arange(x.min(), x.max(), new_resolution)  # type: ignore  # noqa
new_y = np.arange(y.min(), y.max(), new_resolution)  # type: ignore  # noqa

# Project DEM to new mesh
dem_9x9 = dem.interp(x=new_x, y=new_y)  # type: ignore  # noqa

# Reduce the data to reuired information for netcdf
dem_cleaned = (
    dem_9x9.drop_vars(["band", "spatial_ref"]).squeeze("band").drop_indexes(["x", "y"])
)

# Change coordinates to match dummy data grid
# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_displacements = [0, 90, 180, 270, 360, 450, 540, 630, 720]

dem_placed = dem_cleaned.assign_coords(
    {"x": cell_displacements, "y": cell_displacements}
)

# Save to netcdf
dem_placed.to_netcdf("./elevation_dummy.nc")
