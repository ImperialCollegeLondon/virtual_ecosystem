---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
language_info:
  codemirror_mode:
    name: ipython
    version: 3
  file_extension: .py
  mimetype: text/x-python
  name: python
  nbconvert_exporter: python
  pygments_lexer: ipython3
  version: 3.11.9
mystnb:
  render_markdown_format: myst
---

# Elevation Data Preprocessing

The notes given below were originally written by Dr. Lelavathy Samikan Mazilamani. They
are based on the script used to generate the Maliau elevation dataset
([maliau_elevation_data_processing_script.py](https://github.com/ImperialCollegeLondon/ve_data_science/blob/main/analysis/abiotic/data_download/maliau_elevation_data_processing_script.py)).

## General Notes

The elevation dataset provides the static topographic surface required by the Virtual
Ecosystem (VE) hydrology module. Elevation influences key hydrological processes within
the model domain, including surface runoff generation, drainage pathways, flow routing,
terrain-driven redistribution of water, and spatial variation in hydrological
connectivity. To ensure consistency across all VE modules, elevation data must:

* Be aligned to the official VE site specific grid definition
* Use the same projected coordinate system
* Match the exact model resolution
* Contain no missing or invalid spatial cells
* Be formatted into a VE-compatible NetCDF structure

Elevation preprocessing typically involves:

* Loading a Digital Elevation Model (DEM) in a projected coordinate system
* Reading the VE site definition file (TOML) to obtain grid resolution and cell centres
* Reprojecting and resampling the DEM to match the VE grid
* Masking raster `nodata` values using metadata-defined flags
* Filling any remaining gaps to ensure spatial continuity
* Converting projected coordinates into grid-relative coordinates
* Exporting the processed elevation surface as a NetCDF dataset

This ensures that hydrology module operates on a consistent and spatially aligned
topographic surface.

## Example: Maliau Basin

For the Maliau Basin configuration, elevation preprocessing is performed using a [30 m
Shuttle Radar Topography Mission (SRTM) DEM](https://doi.org/10.1029/2005rg000183)
{cite:p}`farr_shuttle_2007`. The DEM covers the SAFE Project region (4°N 116°E to 5°N
117°E), is reprojected to UTM Zone 50N (EPSG:32650), [and can be downloaded from
Zenodo](https://zenodo.org/records/3490488). The VE hydrological module requires
elevation input aligned to a resolution of 90 m grid, whereas the original SRTM product
is provided at approximately 30 m resolution. To reconcile this difference, the
elevation data is resampled to the target 90 m grid using bilinear aggregation, which
smooths fine-scale terrain while preserving broad-scale topographic patterns. This
ensures consistency with the VE spatial resolution. In future, terrain-preserving or
hydrologically explicit resampling approaches could also be explored.

The first thing to do is load the dependencies needed for this workflow.

```{code-block} python
from pathlib import Path

import numpy as np
import rasterio
import tomllib
import xarray as xr
from rasterio.enums import Resampling
from rasterio.warp import reproject
from scipy import ndimage
```

As different types of input data will share the same grid definitions, we recommend that
you store your grid definition within a `toml` file, which can then be used across
preprocessing scripts. In our case, we have called this file
`maliau_grid_definition_90m.toml`. We will now load it in and extract UTM eastings and
northings,  projection information (EPSG code) and target resolution of our desired grid
from it.

```{code-block} python
with open("../../../sites/maliau_grid_definition_90m.toml", "rb") as f:
    site_config = tomllib.load(f)

cell_x = np.array(site_config["cell_x_centres"])  # UTM eastings
cell_y = np.array(site_config["cell_y_centres"])  # UTM northings
epsg_code = site_config["epsg_code"]
res = site_config["res"]  # target resolution (90 m)
```

The next step is to open the input SRTM (Shuttle Radar Topography Mission) DEM file
using the `rasterio` package. This provides access to the georeferenced raster data
(elevation values).

Based on the site configuration we prepare a target grid to resample the SRTM data onto.
The resampling is done using a `bilinear`resampling method,  which averages values
within a block of cells to compute the new cell value. This is smoother than
nearest-neighbor, avoids artifacts, and is suitable for continuous data like elevation.

```{code-block} python
# Define input directory and filename for the SRTM dataset for the SAFE Project area,
# covering the region 4°N 116°E to 5°N 117°E
input_srtm = Path("SRTM_UTM50N_processed.tif")

with rasterio.open(input_srtm) as src:
    data = src.read(1).astype(float)
    data = np.where(data < 0, np.nan, data)  # mask invalid

    # Prepare the target grid following the resolution and spatial extent we want for
    # resampling the DEM. This grid will be used to reproject or resample
    # the original SRTM data.
    ny, nx = len(cell_y), len(cell_x)
    transform = rasterio.transform.from_origin(
        west=min(cell_x) - res / 2, north=max(cell_y) + res / 2, xsize=res, ysize=res
    )
    dst_data = np.empty((ny, nx), dtype=np.float32)

    # We use `bilinear`resampling method,  which averages values within a block of
    # cells to compute the new cell value. This is smoother than nearest-neighbor,
    # avoids artifacts, and is suitable for continuous data like elevation.

    reproject(
        source=data,
        destination=dst_data,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=f"EPSG:{epsg_code}",
        resampling=Resampling.bilinear,
    )

```

```{note}
In future, we could also consider methods that explicitly capture terrain
variability (e.g., variance-preserving aggregation) or preserve hydrological
connectivity (e.g., flow-directed resampling). This is not yet implemented!
```

The next step is to mask invalid data with NaN values. Many DEM products (e.g., SRTM,
ASTER, Copernicus DEM) use special placeholder values such as -9999 or -32768 to
indicate missing data (nodata). These values are not real elevations and must be masked
out. Instead of assuming all negative values are invalid (which would incorrectly remove
genuine terrain below sea level), we read the official "nodata" value from the raster
metadata (src.nodata) and replace only those flagged cells with NaN.This makes the
script more general-purpose and safe for use in coastal or low-lying regions where valid
elevations can be negative.

```{code-block} python
nodata_val = src.nodata
dst_data = np.where(dst_data == nodata_val, np.nan, dst_data)
```

With invalid values now masked they need to be replaced. This is done by filling in
nearest neighbour values, and ensures the DEM is spatially continuous and can be used in
hydrological or other modelling workflows without gaps.

```{code-block} python
if np.isnan(dst_data).any():
    mask = np.isnan(dst_data)
    filled_data = dst_data.copy()

    nearest_index = ndimage.distance_transform_edt(
        mask, return_distances=False, return_indices=True
    )
    filled_data[mask] = dst_data[tuple(nearest_index[:, mask])]
    dst_data = filled_data
```

After cleaning and resampling, we prepare the DEM in a structured dataset format.
The original grid coordinates (cell_x, cell_y) represent projected UTM
cell-centre positions. To ensure consistency with VE inputs, these coordinates are
converted to distances relative to the grid origin (cell centre based).
This results in regularly spaced x and y coordinates starting at 0 and increasing by
the grid resolution, and ensures that spatial positions are defined consistently and
independently of absolute map coordinates.

```{code-block} python
x = cell_x - cell_x[0]
y = cell_y - cell_y[0]
```

The elevation data now needs to be converted into the format used by the Virtual
Ecosystem. The unique and ordered x and y coordinate vectors define the spatial
dimensions of the dataset. Elevation values are stored as a 2D array with dimensions (x,
y). Because rasterio reads raster data in (y, x) order, the array is transposed to (x,
y).

```{code-block} python
x_unique = np.sort(np.unique(x))
y_unique = np.sort(np.unique(y))

elevation_matrix = dst_data.T.astype(np.float32)
```

The full `xarray` Dataset can now be created and saved. It uses x and y as spatial
dimensions (distance from grid origin in meters), with elevation in meters being the
only variable.

```{code-block} python
dataset_xy = xr.Dataset(
    {"elevation": (("x", "y"), elevation_matrix)},
    coords={
        "x": x_unique.astype(np.float32),
        "y": y_unique.astype(np.float32),
    },
)

dataset_xy.to_netcdf("elevation_maliau_2010_2020_90m.nc")
```

The resulting NetCDF file serves as the authoritative elevation surface for the Maliau
Basin VE configuration. All hydrological processes within the model reference this
grid-aligned elevation dataset to ensure spatial consistency.
