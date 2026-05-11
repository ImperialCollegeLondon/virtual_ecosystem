---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.2
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

# Climate Data Preprocessing

The notes given below were originally written by Dr. Lelavathy Samikan Mazilamani. They
are based on the script that defines a function to download ERA5 data
([cdsapi_downloader.py](https://github.com/ImperialCollegeLondon/ve_data_science/blob/main/analysis/abiotic/data_download/cdsapi_downloader.py))
and the script that used to generate the Maliau climate dataset
([maliau_climate_data_processing_script.py](https://github.com/ImperialCollegeLondon/ve_data_science/blob/main/analysis/abiotic/data_download/maliau_climate_data_processing_script.py)).

## General Notes

Climate data provide the dynamic atmospheric forcing required by the Virtual Ecosystem
(VE) model. These data drive key abiotic and hydrological processes, including
evapotranspiration, plant physiological responses, soil moisture dynamics, radiation
balance, and precipitation-driven runoff.

To ensure consistency across all VE modules, climate datasets must:

* Be spatially aligned to the official VE site grid definition
* Use a consistent projected coordinate system
* Match the model grid resolution
* Use VE-standard variable names
* Be converted to appropriate physical units
* Be formatted into a VE-compatible NetCDF structure

```{note}
Different data sources provide data at different vertical levels and with different
underlying assumptions, which lead to biases in the model output. For example, the
reference height can be 1.5 m or 2 m, above ground or above the canopy, measured or
interpolated. In the Virtual Ecosystem, the reference height is assumed to be 2 m above
the top of the canopy (2 m above the ground in absence of vegetation).
```

Climate preprocessing typically involves two stages:

1. Data Download
    * Retrieve ERA5-Land reanalysis data from the Copernicus Climate Data Store (CDS)
    * Select required atmospheric variables
    * Define temporal range (e.g., 2010–2020)
    * Specify spatial bounding box
    * Compile variables into a single NetCDF dataset
2. Data Processing and Grid Alignment
    * Load the VE site grid definition (TOML)
    * Assign coordinate reference system (CRS)
    * Reproject data from WGS84 to the VE projected coordinate system (e.g., UTM)
    * Resample or interpolate to the VE grid resolution
    * Convert units to VE conventions
    * Derive additional variables (e.g., relative humidity, mean annual temperature)
    * Rename variables to VE-standard naming
    * Reformat dimensions to VE-style (x, y, time_index)
    * Export final processed dataset as NetCDF

This ensures that all climate forcing data are spatially and structurally compatible
with the VE model.

## Example: Maliau Basin

For the Maliau Basin configuration, climate data are derived from [ERA5-Land monthly
averaged reanalysis datasets obtained via the Copernicus Climate Data Store
(CDS)](https://doi.org/10.24381/cds.68d2bb30) {cite:p}`munoz-sabater_era5-land_2021`.

To access the [Copernicus Data Store](https://cds.climate.copernicus.eu/) (CDS) you
will need to register, and configure your `.cdsapirc` file in your home directory. The
Copernicus Climate Data Store provides [comprehensive guidance on setting up and using
their API](https://cds.climate.copernicus.eu/how-to-api).

The process given below is computational intensive, so for large variable downloads, it
is recommended to run one variable at a time.

First we define a function that downloads the ERA5 variables that we require from the
data store.

```{code-block} python
from pathlib import Path

import cdsapi
import xarray

REQUIRED_VARIABLES = [
    "2m_temperature",  # abiotic variable
    "2m_dewpoint_temperature",  # abiotic variable
    "surface_pressure",  # abiotic variable
    "10m_u_component_of_wind",  # abiotic variable
    "total_precipitation",  # hydrological variable
    "surface_solar_radiation_downwards",  # plant variable # abiotic variable
    "surface_thermal_radiation_downwards",  # abiotic variable
]

def cdsapi_era5_downloader(years: list[int], bbox: list[float], outfile: Path):
    """ERA5 hourly data downloader.

    Downloads a time series of the set of required variables from the CDS for the
    "reanalysis-era5-land-monthly-means" dataset for the region within a provided
    bounding box and for a set of years.

    Args:
        years: A list of years to download
        bbox: The bounding box of the data to download in degrees,
        outfile: An output path for the compiled data file.

    """

    # Each variable is downloaded to a separate file, so collect temporary filenames
    downloaded_files = []

    # Get the CDSAPI client
    client = cdsapi.Client()

    for var in REQUIRED_VARIABLES:
        # Create the request dictionary - all hourly observations of the requested
        # variable in the requested years
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "variable": var,
            "year": [str(y) for y in years],
            "month": [f"{i:02d}" for i in range(1, 13)],  # All months in a year
            "time": [f"{i:02d}:00" for i in range(24)],  # All hours in a day
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": bbox,
        }

        # Retrieve the request from the client. The file will download to a random UUID
        # filename by default - we collect these to compile the data to a single file.
        file = client.retrieve(
            name="reanalysis-era5-land-monthly-means", request=request
        ).download()
        downloaded_files.append(file)

    # Load the individual datafiles and then merge them into a single Dataset
    netcdf_datasets = [xarray.load_dataarray(d) for d in downloaded_files]
    compiled_data = xarray.merge(netcdf_datasets)

    # Write the compiled data to the output file
    compiled_data.to_netcdf(outfile)

    # Tidy up the individual variable files
    for file in downloaded_files:
        Path(file).unlink()

```

With the download function defined we now need to import it along with the other
dependencies:

```{code-block} python
from pathlib import Path

import numpy as np
import tomllib
import xarray
import xarray as xr
from cdsapi_downloader import cdsapi_era5_downloader
from rasterio import Affine
from rasterio.crs import CRS
from rasterio.warp import Resampling
```

Next we run the downloader tool, with our desired spatial (4.6°N 116.8°E to 4.8°N
117.0°E) and temporal extents (2010-2021).

```{code-block} python
cdsapi_era5_downloader(
    years=list(range(2010, 2021)),
    bbox=[4.6, 116.8, 4.8, 117.0],
    outfile="era5_monthly_2010_2020_maliau.nc",
)
```

The `abiotic` and `hydrology` modules require atmospheric forcing variables aligned to
the model grid resolution of 100 m. However, the downloaded dataset
`era5_monthly_2010_2020_maliau.nc` is provided at a much coarser spatial resolution
(approximately 11 km). To reconcile this difference, the ERA5-Land monthly averaged
variables are reprojected and resampled to the target 100 m grid using the
nearest-neighbour method.

```{note}
The process shown below was originally written for a 90 m grid resolution. However, it
can be adjusted to any desired grid resolution (e.g., 100 m) by modifying the scenario
configuration, for example by changing the
[site definition file](../../core_settings/site_definition_guide.md) that defines the
Virtual Ecosystem grid.
```

```{code-block} python
# Load the destination grid details
with open("maliau_grid_definition_90m.toml", "rb") as maliau_grid_file:
    site_config = tomllib.load(maliau_grid_file)

# Define the XY shape of the data in the destination dataset
dest_shape = (
    site_config["cell_nx"],
    site_config["cell_ny"],
)

# Define the affine matrix giving the coordinates of pixels in the destination dataset
dest_transform = Affine(
    site_config["res"],
    0,
    site_config["ll_x"],
    0,
    site_config["res"],
    site_config["ll_y"],
)
```

We now want to open the ERA5 dataset in WGS84. We need CRS manually because it is not
set in the file. However, times **must not** be decoded from CF to np.datetime64,
because we'd have to convert back to write the file.

```{code-block} python
era5_data_WGS84 = xarray.open_dataset(
    "era5_monthly_2010_2020_maliau.nc",
    engine="netcdf4",
    decode_times=False,
)
# CRS needs to be set manually
wgs84_crs = CRS.from_epsg(4326)
era5_data_WGS84 = era5_data_WGS84.rio.write_crs(wgs84_crs)
```

The ERA5 data can now be reprojected to UTM 50N using the rasterio accessor tools.

```{note}
The interpolation mapping used here at the moment is the `nearest`method of rasterio.
Other methods are available:
https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling
We might want to use a different interpolation strategy to give a smooth surface .
```

```{code-block} python
utm50N_crs = CRS.from_epsg(32650)
era5_data_UTM50N = era5_data_WGS84.rio.reproject(
    dst_crs=utm50N_crs,
    shape=dest_shape,
    transform=dest_transform,
    resampling=Resampling.nearest,
)
```

```{warning}
The Virtual Ecosystem example data is run on a 90 x 90 m grid.
This means that some form of spatial downscaling has to be applied to the dataset,
for example by spatially interpolating coarser resolution climate data and including
the effects of local topography. This is not yet implemented!
```

We now need to convert the units of the dataset to match those expected by the Virtual
Ecosystem.

```{code-block} python
dataset = era5_data_UTM50N

# The standard output unit of 2m dewpoint temperature (d2m ) and 2m air temperature
# (t2m) is Kelvin (K) which we need to convert to degree Celsius (C) for the
# Virtual Ecosystem.
dataset["t2m_C"] = dataset["t2m"] - 273.15
dataset["d2m_C"] = dataset["d2m"] - 273.15

# Relative humidity (rh) is not a standard output from ERA5-Land but can be calculated
# from 2m dewpoint temperature (d2m in C) and 2m air temperature (t2m in C)
dataset["rh"] = 100.0 * (
    np.exp(17.625 * dataset["d2m_C"] / (243.04 + dataset["d2m_C"]))
    / np.exp(17.625 * dataset["t2m_C"] / (243.04 + dataset["t2m_C"]))
)

# The standard output unit for total precipitation (tp) in ERA5-Land is meters (m)
# which we need to convert to millimeters (mm). Further, the data represents mean daily
# accumulated precipitation for the 9x9km grid box, so the value has to be scaled to
#  monthly (here 30 days). TODO handle daily inputs
dataset["tp_mm"] = dataset["tp"] * 1000 * 30

# The standard output unit for surface pressure (sp) in ERA5-Land is Pascal (Pa) which
# we need to convert to kilopascal (kPa) by dividing by 1000.
dataset["sp_kPa"] = dataset["sp"] / 1000

# The standard output unit for surface solar radiation downward (ssrd) in ERA5-Land is
# Joule per square meter (Jm-2) which need to be converted to Watts per square meter
# (Wm-2) by dividing by the number of seconds in a month
dataset["ssrd_Wm-2"] = dataset["ssrd"] / 2592000

# The standard output unit for surface thermal radiation downward (strd) in ERA5-Land is
# Joule per square meter (Jm-2) which need to be converted to Watts per square meter
# (Wm-2) by dividing by the number of seconds in a month
dataset["strd_Wm-2"] = dataset["strd"] / 2592000
```

Some variables then need to be renamed to match Virtual Ecosystem conventions.

```{code-block} python
dataset_cleaned = dataset.drop_vars(["d2m", "d2m_C", "t2m", "tp", "sp", "ssrd", "strd"])
dataset_renamed = dataset_cleaned.rename(
    {
        "sp_kPa": "atmospheric_pressure_ref",
        "tp_mm": "precipitation",
        "t2m_C": "air_temperature_ref",
        "rh": "relative_humidity_ref",
        "u10": "wind_speed_ref",
        "ssrd_Wm-2": "downward_shortwave_radiation",
        "strd_Wm-2": "downward_longwave_radiation",
    }
)
```

A time series of atmospheric CO2 is needed but is not included in ERA5. We add this here
as a constant field of 400ppm.

```{code-block} python
air_temp_shape = dataset_renamed["air_temperature_ref"].shape
dataset_renamed["atmospheric_co2_ref"] = xr.DataArray(
    400 * np.ones(air_temp_shape),
    dims=dataset_renamed["air_temperature_ref"].dims,
    coords=dataset_renamed["air_temperature_ref"].coords,
)
```

Mean annual temperature then need to be calculated from the full time series of air
temperatures.

```{note}
In the future we plan to include a time series of mean annual data for every year.
```

```{code-block} python
time_dim = next(
    dim for dim in dataset_renamed["air_temperature_ref"].dims if "time" in dim
)

dataset_renamed["mean_annual_temperature"] = dataset_renamed[
    "air_temperature_ref"
].mean(dim=time_dim)
```

The dimensions of the reprojected dataset now need to be converted into the Virtual
Ecosystem (VE) spatial layout, using x and y as physical spatial dimensions and
time_index as the temporal dimension.

```{code-block} python
cell_x = np.array(site_config["cell_x_centres"])  # UTM eastings
cell_y = np.array(site_config["cell_y_centres"])  # UTM northings
epsg_code = site_config["epsg_code"]
res = site_config["res"]  # target resolution (90 m)
```

The original grid coordinates (cell_x, cell_y) represent projected UTM cell-centre
positions. To ensure consistency with VE inputs, these coordinates are converted to
distances relative to the grid origin (cell centre based). This results in regularly
spaced x and y coordinates starting at 0 and increasing by the grid resolution.

```{code-block} python
x = cell_x - cell_x[0]
y = cell_y - cell_y[0]
```

Identify the existing time dimension name in the dataset (e.g. 'time'), allowing the
script to remain robust to different NetCDF conventions.

```{code-block} python
time_dim = next(
    dim for dim in dataset_renamed["air_temperature_ref"].dims if "time" in dim
)
```

Rename the time dimension to "time_index" and assign spatial coordinates (x, y) as
explicit coordinate variables.

```{code-block} python
n_time = dataset_renamed.sizes[time_dim]

dataset_xyt = dataset_renamed.rename_dims({time_dim: "time_index"}).assign_coords(
    {
        "x": x.astype(np.float32),
        "y": y.astype(np.float32),
        "time_index": np.arange(n_time, dtype=np.int32),
    }
)

# Explicitly enforce dimension order as (x, y, time_index).
dataset_xyt = dataset_xyt.transpose("x", "y", "time_index")
```

Once we confirmed that our dataset is complete and our calculations are correct, we save
it as a new netcdf file.

```{code-block} python
output_dir_reprojected = Path(".../../../data/derived/abiotic/era5_land_monthly")
output_dir_reprojected.mkdir(parents=True, exist_ok=True)
output_filename_reprojected = output_dir_reprojected / "era5_maliau_2010_2020.90m.nc"

dataset_xyt.to_netcdf(output_filename_reprojected)
```
