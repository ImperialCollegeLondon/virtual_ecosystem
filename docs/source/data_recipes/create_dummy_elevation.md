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

# Elevation data for dummy module

This section explains how to create a low resolution dummy elevation map from a
digital elevation model ([SRTM](https://www2.jpl.nasa.gov/srtm/)) for use in
`vr_run --example`. The initial data covers the region 4°N 116°E to 5°N 117°E, see
[SAFE wiki](https://safeproject.net/dokuwiki/safe_gis/srtm) for reference and download.

```python
import xarray as xr
import numpy as np
from xarray import DataArray
import rioxarray

# 1. Load DEM in 30m resolution
dem = rioxarray.open_rasterio('./SRTM_UTM50N_processed.tif')

# 2. Resample DEM to 90 m
# Specify the original grid coordinates
x = dem['x'].values
y = dem['y'].values

# 3. Create a new grid of longitude and latitude coordinates with higher resolution
new_resolution=26000
new_x = np.arange(x.min(), x.max(), new_resolution)
new_y = np.arange(y.min(), y.max(), new_resolution)

# 4. Project DEM to new mesh
dem_9x9 = dem.interp(x = new_x, y = new_y)

# 5. Reduce the data to reuired information for netcdf
dem_cleaned= dem_9x9.drop_vars(['band','spatial_ref']).squeeze('band').drop_indexes(['x','y']).rename('elevation')

# 6. Change coordinates to match dummy data
# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_displacements = [0, 90, 180, 270, 360, 450, 540, 630, 720]

dem_placed = dem_cleaned.assign_coords({'x': cell_displacements, 'y': cell_displacements})

# 7. Save to netcdf
dem_placed.to_netcdf('../../example_data/elevation_dummy.nc')
```
