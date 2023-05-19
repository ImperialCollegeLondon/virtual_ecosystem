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

# Simple climate data pre-processing example for dummy module

This section illustrates how to perform simple manipulations to adjust ERA5-Land data to
use in the Virtual Rainforest. This includes reading climate data from netcdf,
converting the data into an input format that is suitable for the abiotic module (e.g.
Kelvin to Celsius conversion), adding further required variables, and writing the output
in a new netcdf file.
**This does not include spatially interpolating coarser resolution climate data**
**and including the effects of local topography**.

## Dummy data set

Example file: [dummy_climate_data.nc](./dummy_climate_data.nc)

### Metadata

- Reference: Hersbach, H., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz
  Sabater, J., Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A.,
  Soci, C., Dee, D., Thépaut, J-N. (2019): ERA5 monthly averaged data on single levels
  from 1959 to present. Copernicus Climate Change Service (C3S) Climate Data Store
  (CDS). (Accessed on \< DD-MMM-YYYY >), 10.24381/cds.f17050d7

- Product type: Monthly averaged reanalysis

- Variable: 10m wind speed, 2m dewpoint temperature, 2m temperature, Soil temperature
  level 1, Surface pressure, TOA incident solar radiation, Total cloud cover, Total
  precipitation, Volumetric soil water layer 1

- Year: 2013, 2014

- Month: January, February, March, April, May, June, July, August, September, October,
  November, December

- Time: 00:00

- Sub-region extraction: North 6°, West 116°, South 4°, East 118°

- Format: NetCDF (experimental)

## Code example

### 1. Load the data

```{code-cell} ipython3
import xarray as xr
import numpy as np
from xarray import DataArray

dataset = xr.open_dataset("./dummy_climate_data.nc")
dataset
```

### 2. Convert temperatures

The standard output unit of ERA5 tempertures is Kelvin which we need to convert into
degree Celsius for the Virtual Rainforest. This includes 2m air temperature, 2m dewpoint
temperature (used to calculate relative humidity in next step), and topsoil temperature.

```{code-cell} ipython3
dataset["t2m_C"] = dataset["t2m"]-273.15 # 2m air temperature
dataset["d2m_C"] = dataset["d2m"]-273.15 # 2m dewpoint temperature
dataset["stl1_C"] = dataset["stl1"]-273.15 # top soil temperature
```

### 3. Calculate relative humidity

Relative humidity (RH) is not a standard output from ERA5 but can be calculated from 2m
dewpoint temperature (DPT) and 2m temperature (T) as follows:

$$ RH = \frac{100\exp(17.625 \cdot DPT)/(243.04+DPT)}
                 {\exp(17.625 \cdot T)/(243.04+T)}
$$

```{code-cell} ipython3
dataset["rh2m"] = (
    100.0
    * (np.exp(17.625 * dataset["d2m_C"] / (243.04 + dataset["d2m_C"])) 
    / np.exp(17.625 * dataset["t2m_C"] / (243.04 + dataset["t2m_C"])))
    )
```

### 4. Clean dataset and rename variables

In this step, we delete the initial temperature variables (K) and rename the remaining
variables according to the Virtual Rainforest naming convention (see
[here](../../../virtual_rainforest/data_variables.toml) ).

```{code-cell} ipython3
dataset_cleaned = dataset.drop_vars(["d2m",'d2m_C',"t2m","stl1"])
dataset_renamed = dataset_cleaned.rename({
    'si10':'wind_speed_ref',
    'sp':'atmospheric_pressure_ref',
    'tp':'precipitation',
    'swvl1':'soil_moisture_ref',
    't2m_C':'air_temperature_ref',
    'rh2m': 'relative_humidity_ref',
    'stl1_C': 'top_soil_temperature_ref',
    'tisr':'TOA_incoming_solar_radiation',
    'tcc':'total_could_cover',
    })
dataset_renamed.data_vars
```

### 5. Select required variables and add further required variables

The set of required variables depends on the complexity of the abiotic model that is
selected for the simulation. For the simple abiotic model, we require only a subset of
the loaded climate data, and can therefore drop unrequired variables. In addition to the
climatic variables, a time series of atmospheric CO2 is needed. We add this here as a
constant field. Mean annual temperature is calculated from the full time series of air
temperatures; in the future, this should be done for each year.

```{code-cell} ipython3
dataset_simple = dataset_renamed.drop_vars(
  [
    'wind_speed_ref',
    'soil_moisture_ref',
    'top_soil_temperature_ref',
    'TOA_incoming_solar_radiation',
    'total_could_cover',
  ]
)
dataset_simple['atmospheric_co2_ref'] = DataArray(
  np.full_like(dataset_simple['air_temperature_ref'],400),
  dims=['time', 'latitude', 'longitude'],
)
dataset_simple['mean_annual_temperature'] = (
  dataset_simple["air_temperature_ref"].mean(dim = 'time')
  )
dataset_simple
```

### 7. Change coordinates to x-y in meters

The following code segment changes the coordinate names from `longitude/latitude` to
`x/y` and the units from `minutes` to `meters`. The ERA5-Land coordinates are treated as
the centre points of the grid cells which means that when setting up the grid, an offset
of 4.5 km has to be added (see Section 11).

```{code-cell} ipython3
dataset_xy = dataset_renamed.rename_dims({'longitude':'x','latitude':'y'}).assign_coords({'x':np.arange(0,180000,9000),'y':np.arange(0,180000,9000)}).drop({'longitude','latitude'})
dataset_xy.coords
```

### 8. Scale to 90 m resolution

The Virtual Rainforest is run on a 90 x 90 m grid. This means that some form of spatial
downscaling has to be applied to the dataset, for example by spatially interpolating
coarser resolution climate data and including the effects of local topography.
**This is not yet implemented!**

For the purpose of a dummy simulation in the development stage, the coordinates can be
overwritten to match the Virtual Rainforest grid and we can select a smaller area.
When setting up the grid (see Section 11), an offset of 45 m has to be added. Note that
the resulting dataset does no longer match a digital elevation model for the area!

```{code-cell} ipython3
dataset_xy_100 = dataset_renamed.rename_dims({'longitude':'x','latitude':'y'}).assign_coords({'x':np.arange(0,1800,90),'y':np.arange(0,1800,90)}).drop({'longitude','latitude'})
dataset_xy_dummy = dataset_xy_100.isel(x=np.arange(9),y=np.arange(9))
dataset_xy_dummy.coords
```

### 9. Add time_index

The dummy model iterates over time indices rather than real datetime. Therefore, we add
a `time_index` coordinate to the dataset:

```{code-cell} ipython3
dataset_xy_timeindex = dataset_xy_dummy.rename_dims({'time':'time_index'}).assign_coords({'time_index':np.arange(0,24,1)})
dataset_xy_timeindex.coords
```

### 10. Save netcdf

Once we confirmed that our dataset is complete and our calculations are correct, we save
it as a new netcdf file. This can then be fed into the code data loading system here
{mod}`~virtual_rainforest.core.data`.

```{code-block} ipython3
dataset_xy_timeindex.to_netcdf("./ERA5_land_dummy.nc")
```

### 11. Update grid config `TOML`

The final step is to add the grid information to the grid config `TOML` to load this
data correctly when setting up a Virtual Rainforest Simulation, [see here](../virtual_rainforest/core/config.md)
. Here, we can also add the 45m offset to position the coordinated at the
centre of the grid cell.

```toml
[core.grid]
cell_nx = 9
cell_ny = 9
cell_area = 8100
xoff = -45.0
yoff = -45.0
```
