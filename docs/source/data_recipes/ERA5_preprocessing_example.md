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

This section illustrates how to perform simple manipulations to adjust ERA5 data to use
in the Virtual Rainforest. This includes reading climate data from netcdf, converting
the data into an input formate that is suitable for the abiotic module (e.g. Kelvin to
Celcius conversion), and writing the output in a new netcdf file. This does not include
scaling or topographic adjustment.

## Dummy data set

Example file: [dummy_climate_data.nc](./dummy_climate_data.nc)

### Metadata

Reference:
Hersbach, H., Bell, B., Berrisford, P., Biavati, G., Horányi, A., Muñoz Sabater, J.,
Nicolas, J., Peubey, C., Radu, R., Rozum, I., Schepers, D., Simmons, A., Soci, C., Dee,
D., Thépaut, J-N. (2019): ERA5 monthly averaged data on single levels from 1959 to
present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS).
(Accessed on < DD-MMM-YYYY >), 10.24381/cds.f17050d7

Product type:
Monthly averaged reanalysis

Variable:
10m wind speed, 2m dewpoint temperature, 2m temperature, Soil temperature level 1,
Surface pressure, TOA incident solar radiation, Total cloud cover, Total precipitation,
Volumetric soil water layer 1

Year:
2013, 2014

Month:
January, February, March, April, May, June, July, August, September, October, November,
December

Time:
00:00

Sub-region extraction:
North 6°, West 116°, South 4°, East 118°

Format:
NetCDF (experimental)

## Code example

### 1. Load the data

```{code-cell} ipython3
import xarray as xr
import numpy as np

dataset = xr.open_dataset("./dummy_climate_data.nc")
dataset
```

### 2. Convert temperatures

The standard output unit of ERA5 tempertures is Kelvin which we need to convert into
degree Celcius for the Virtual Rainforest. This includes 2m air temperature, 2m dewpoint
temperature (used to calculate relative humidity in next step), and topsoil temperature.

```{code-cell} ipython3
dataset["t2m_C"] = dataset["t2m"]-273.15 # 2m air temperature
dataset["d2m_C"] = dataset["d2m"]-273.15 # 2m dewpoint temperature
dataset["stl1_C"] = dataset["stl1"]-273.15 # top soil temperature
```

### 3. Calculate relative humidity

Relative humidity (RH) is not a standard output from ERA5 but can be calculated from 2m
dewpoint temperature (DPT) and 2m temperature (T) as follows:

$$ RH = {{100*exp(17.625*DPT)/(243.04+DPT)} \over {exp(17.625*T)/(243.04+T)}} $$

```{code-cell} ipython3
 dataset["rh2m"] = (
    100.0
    * (np.exp(17.625 * dataset["d2m_C"] / (243.04 + dataset["d2m_C"])) 
    / np.exp(17.625 * dataset["t2m_C"] / (243.04 + dataset["t2m_C"])))
    )
```

### 4. Clean dataset and save netcdf

```{code-cell} ipython3
dataset_cleaned = dataset.drop_vars(["d2m","t2m","stl1"])
dataset_cleaned
```

Once you confirmed that your dataset is complete and your calculations are correct, save
it as a new netcdf file. This can then be fed into the code data loading system,
see {mod}`~virtual_rainforest.core.data`.

```{code-block} ipython3
dataset_cleaned.to_netcdf("./dummy_climate_data_processed.nc")
```
