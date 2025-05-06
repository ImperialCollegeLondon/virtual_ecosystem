"""Simple climate data pre-processing example for `ve_run` example data.

This section illustrates how to perform simple manipulations to adjust ERA5-Land data to
use in the Virtual Ecosystem. This includes reading climate data from netcdf,
converting the data into an input format that is suitable for the abiotic module (e.g.
Kelvin to Celsius conversion), adding further required variables, and writing the output
in a new netcdf file. This does **not** include spatially interpolating coarser
resolution climate data or the effects of local topography.

Input file: ERA5_land_example.nc

Metadata:

* Muñoz Sabater, J. (2019): ERA5-Land monthly averaged data from 1950 to present.
  Copernicus Climate Change Service (C3S) Climate Data Store (CDS).
  [DOI: 10.24381/cds.68d2bb30](https://doi.org/10.24381/cds.68d2bb30)
  (Accessed on 16-04-2025)
* Web catalogue entry: Copernicus Climate Change Service (C3S) (2022): ERA5-Land monthly
  averaged data from 1950 to present. Copernicus Climate Change Service (C3S) Climate
  Data Store (CDS). [DOI: 10.24381/cds.68d2bb30](https://doi.org/10.24381/cds.68d2bb30)
  (Accessed on 16-04-2025)
* Product type: Monthly averaged reanalysis
* Variable: 2m dewpoint temperature, 2m temperature, Surface pressure, Total
  precipitation
* Year: 2013, 2014
* Month: January, February, March, April, May, June, July, August, September, October,
  November, December
* Time: 00:00
* Sub-region extraction: North 6°, West 116°, South 4°, East 118°
* Format: NetCDF3

Once the new netcdf file is created, the final step is to add the grid information to
the grid config `TOML` to load this data correctly when setting up a Virtual Ecosystem
Simulation. Here, we can also add the 45 m offset to position the coordinated at the
centre of the grid cell.

[core.grid]
cell_nx = 9
cell_ny = 9
cell_area = 8100
xoff = -45.0
yoff = -45.0
"""

import numpy as np
import xarray as xr
from xarray import DataArray

from virtual_ecosystem.example_data.generation_scripts.common import (
    time_index,
    x_cell_ids,
    y_cell_ids,
)

# 1. Load ERA5_Land data in low resolution

dataset = xr.open_dataset("../source/ERA5_land_example.nc")

# 2. Convert temperatures units
# The standard output unit of ERA5-Land temperatures is Kelvin which we need to convert
# to degree Celsius for the Virtual Ecosystem. This includes 2m air temperature and
# 2m dewpoint temperature which are used to calculate relative humidity in next step.

dataset["t2m_C"] = dataset["t2m"] - 273.15  # 2m air temperature
dataset["d2m_C"] = dataset["d2m"] - 273.15  # 2m dewpoint temperature

# 3. Calculate relative humidity
# Relative humidity (RH) is not a standard output from ERA5-Land but can be calculated
# from 2m dewpoint temperature (DPT) and 2m air temperature (T)

dataset["rh2m"] = 100.0 * (
    np.exp(17.625 * dataset["d2m_C"] / (243.04 + dataset["d2m_C"]))
    / np.exp(17.625 * dataset["t2m_C"] / (243.04 + dataset["t2m_C"]))
)

# 4. Convert precipitation units
# The standard output unit for total precipitation in ERA5-Land is meters which we need
# to convert to millimeters. Further, the data represents mean daily accumulated
# precipitation for the 9x9km grid box, so the value has to be scaled to monthly (here
# 30 days). TODO handel daily inputs

dataset["tp_mm"] = dataset["tp"] * 1000 * 30

# 5. Convert surface pressure units
# The standard output unit for surface pressure in ERA5-Land is Pascal (Pa) which we
# need to convert to Kilopascal (kPa).

dataset["sp_kPa"] = dataset["sp"] / 1000

# 6. Clean dataset and rename variables
# In this step, we delete the initial temperature variables (K), precipitation (m), and
# surface pressure(Pa) and rename the remaining variables according to the Virtual
# Ecosystem naming convention.

dataset_cleaned = dataset.drop_vars(["d2m", "d2m_C", "t2m", "tp", "sp"])
dataset_renamed = dataset_cleaned.rename(
    {
        "sp_kPa": "atmospheric_pressure_ref",
        "tp_mm": "precipitation",
        "t2m_C": "air_temperature_ref",
        "rh2m": "relative_humidity_ref",
    }
)

# 7. Add further required variables
# In addition to the variables from the ERA5-Land datasset, a time series of atmospheric
# CO2 is needed. We add this here as a constant field. Mean annual temperature
# is calculated from the full time series of air temperatures; in the future, this
# should be done for each year.

dataset_renamed["atmospheric_co2_ref"] = DataArray(
    np.full_like(dataset_renamed["air_temperature_ref"], 400),
    dims=["valid_time", "latitude", "longitude"],
)
dataset_renamed["wind_speed_ref"] = DataArray(
    np.full_like(dataset_renamed["air_temperature_ref"], 0.1),
    dims=["valid_time", "latitude", "longitude"],
)
dataset_renamed["mean_annual_temperature"] = dataset_renamed[
    "air_temperature_ref"
].mean(dim="valid_time")


# 8. project data on model grid
# The following code segment interpolates the data on to the model grid (here 9x9) and
# fills nan value with the grid mean
time = time_index
lat = dataset_renamed.latitude.values
lon = dataset_renamed.longitude.values

# Create new target lat/lon grid
new_lat = np.linspace(lat.min(), lat.max(), len(y_cell_ids))
new_lon = np.linspace(lon.min(), lon.max(), len(x_cell_ids))

# Interpolate spatially (lat/lon) with nearest neighbor method
data_9x9x24 = dataset_renamed.interp(
    latitude=new_lat, longitude=new_lon, method="nearest"
)

# Fill nan values with grid mean
dataset_filled = data_9x9x24.map(lambda x: x.fillna(x.mean(skipna=True)))

# 9. Change coordinates and dimensions
# The following code segment changes the coordinate names from `longitude/latitude` to
# `x/y` and the units from `minutes` to `meters`. The ERA5-Land coordinates are treated
# as the centre points of the grid cells which means that when setting up the grid, an
# offset of 4.5 km has to be added.
# Further, the example model iterates over time indices rather than real datetime.
# Therefore, we add a `time_index` coordinate to the dataset:

dataset_xyt = (
    dataset_filled.rename_dims(
        {"longitude": "x", "latitude": "y", "valid_time": "time_index"}
    )
    .drop_vars({"longitude", "latitude", "valid_time"})
    .assign_coords(
        {
            "x": np.arange(0, 810, 90),
            "y": np.arange(0, 810, 90),
            "time_index": np.arange(0, 24, 1),
        }
    )
)

# 10. Save netcdf
# Once we confirmed that our dataset is complete and our calculations are correct, we
# save it as a new netcdf file. This can then be fed into the code data loading system
# here {mod}`~virtual_ecosystem.core.data`.

dataset_xyt.to_netcdf("../data/example_climate_data.nc")
