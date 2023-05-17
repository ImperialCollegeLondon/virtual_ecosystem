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

# Climate data download from the COPERNICUS Climate data store and CDS toolbox

The atmospheric variables from regional climate models or observations are typically
provided in spatial and temporal resolutions that are different from the requirements
of the Virtual Rainforest. This document describes how to download climate data from
the Copernicus [Climate Data Store](https://cds.climate.copernicus.eu/) (CDS) and basic
pre-processing options using the
[CDS toolbox](https://cds.climate.copernicus.eu/cdsapp#!/toolbox).
At present, the pre-processing does not include scaling or topographic adjustment.

NOTE: You need to create a user account to access all data and functionalities.

The data handling for simulations is managed by the {mod}`~virtual_rainforest.core.data`
module and the {class}`~virtual_rainforest.core.data.Data` class, which provides the
data loading and storage functions for the Virtual Rainforest. The data system is
extendable to provide support for different file formats and axis validation but that is
beyond the scope of this document.

## Climate input variables

The simple abiotic module of the Virtual Rainforest requires the following climate input
variables (or derivatives) at each time step (default: monthly means):

* Air temperature (typically 2m; mean, minimum, and maximum)
* Relative humidity (typically 2m; relative or specific humidity)
* Atmospheric pressure (typically mean sealevel or surface pressure)
* Precipitation
* optional: atmospheric $\ce{CO_{2}}$ concentration, soil temperature, soil moisture

## Recommended data sets

We recommend the following data sets to force the monthly Virtual Rainforest
microclimate simulations:

* ERA5-Land monthly
  
  ERA5 is the fifth generation reanalysis dataset of the European Centre for
  Medium-Range Weather Forecasts (ECMWF). This reanalysis dataset
  combines model data with observations from across the world into a globally complete
  and consistent dataset using the laws of physics.

  The ERA5-Land dataset provides a consistent view of the evolution of land
  variables over several decades at an enhanced resolution compared to ERA5. It contains
  a detailed record from 1950 onwards, with a temporal resolution of 1 hour. The native
  spatial resolution of the ERA5-Land reanalysis dataset is 9 km on a reduced Gaussian
  grid (TCo1279). The data in the CDS has been regridded to a regular lat-lon grid of
  0.1x0.1 degrees.

  The full documentation and download link can be accessed
  [here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means?tab=overview).

* WFDE5
  
  This global dataset provides bias-corrected reconstruction of near-surface
  meteorological variables derived from the fifth generation of the ECMWF ERA5. The
  output is available in hourly and daily time steps for the period 1979-2019 in
  0.5 x 0.5 deg resolution.
  
  The full documentation and download link can be accessed [here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/derived-near-surface-meteorological-variables?tab=overview).

* CORDEX-SEA
  
  This data set was created with regional climate models (RCM) as part of the
  Coordinated Regional Climate Downscaling Experiment (CORDEX). The spatial
  resolution is 0.22 x 0.22 deg, the spatial extent is 15°S to 27°N and 89 to 146°E,
  the temporal resolution depends on the selected period:
  * historical data (1950-2005) is available in hourly time step
  * scenario data (2006-2100; RCP 2.6, 4.5 and 8.5) is available in daily time step
  
  The full documentation and download link can be accessed [here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/projections-cordex-domains-single-levels?tab=overview).

* Atmospheric $\ce{CO_{2}}$
  
  Observed global $\ce{CO_{2}}$ levels (Mauna Loa, NOAA/GML) are available in monthly or
  annual resolution (1958 - present) [here](https://gml.noaa.gov/ccgg/trends/graph.html)
  . Monthly data derived from satellite observation (2002 - present) is available
  [here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/satellite-carbon-dioxide?tab=overview)
  . Alternatively, reconstructed gridded monthly $\ce{CO_{2}}$ data for the historical
  period (1953 - 2013) and future CMIP6 scenarios (2015 - 2150) can be downloaded
  [here](https://zenodo.org/record/5021361){cite:p}`cheng_wei_global_2021`.

## Step-by-step example to download ERA5-Land monthly data

Follow [this link](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means?tab=overview)
to access overview information about the data set. You find a detailed documentation of
the data set in the 'Documentation' section. To select data, navigate to the tab
'Download Data'.

### Selection ERA5-Land variables

This is an example of a selection of tabs to download a 20x20 grid data set for the
simple abiotic model from ERA5-Land monthly data set:

* Product type: Monthly averaged reanalysis
* Variable: 2m dewpoint temperature, 2m temperature, Surface pressure, Total
  precipitation
* Year: 2013, 2014
* Month: select all
* Time: 00:00
* Geographical area: Sub-region extraction (N 6°, W 116.1°, S 4.1°, E 118°)
* Format: Zipped NetCDF-3 (experimental)

Once you selected the data, you can download the dataset. Further processing for the
Virtual Rainforest using xarray is illustrated [here](./ERA5_preprocessing_example.md).

## Step-by-step example to reproject and download CORDEX-SEA data

Follow [this link](https://cds.climate.copernicus.eu/cdsapp#!/dataset/projections-cordex-domains-single-levels?tab=overview)
to access overview information about the data set. You
find a detailed documentation of the data set in the 'Documentation' section. To select
data, navigate to the tab 'Download Data'.

### Selection CORDEX_SEA

This is an example of a selection of tabs to download historical '2m air temperature'
from the CORDEX-SEA:

* Domain (South-East Asia),
* Experiment (here: 'historical', RCPs available)
* Horizontal resolution ('0.22 degree x 0.22 degree')
* Temporal resolution ('daily mean')
* Variables (here: '2m_air_temperature')
* Global climate model (here: 'mohc_hadgem2_es')
* Regional climate model (here: 'gerics_remo2015')
* Ensemble member (r1i1p1)
* Start year and End year (here: 2001-2005)

Once you selected the data, click on 'show Toolbox request' at the bottom of the page,
copy the code, and open the CDS toolbox editor.

### Toolbox template CORDEX-SEA

The template below describes how to request a data set, reproject the data on a regular
grid (note that the projection name is not changed!), select the area of interest,
calculate the monthly means, and download the product. For illustration, the routine
also plots the mean value. Adjust the 'data' lines to match your data request. You find
the full documentation of the CDS toolbox [here](https://cds.climate.copernicus.eu/toolbox/doc/index.html).

```{code-block} ipython
# EXAMPLE CODE to preprocess CORDEX-SEA with CDS toolbox

import cdstoolbox as ct

@ct.application(title='Download data')
@ct.output.download()
@ct.output.figure()
def download_application():
    data =ct.catalogue.retrieve(
        'projections-cordex-domains-single-levels',
        {
            'domain': 'south_east_asia',
            'experiment': 'historical',
            'horizontal_resolution': '0_22_degree_x_0_22_degree',
            'temporal_resolution': 'daily_mean',
            'variable': '2m_air_temperature',
            'gcm_model': 'mohc_hadgem2_es',
            'rcm_model': 'gerics_remo2015',
            'ensemble_member': 'r1i1p1',
            'start_year': '2001',
            'end_year': '2005',
        }
    )

    regular = ct.geo.make_regular(data, xref='rlon', yref='rlat')
    sel_extent = ct.cube.select(regular, extent=[116., 118, 4., 6.])
    monthly_mean = ct.climate.monthly_mean(sel_extent)
    
    average = ct.cube.average(monthly_mean, dim='time')
    fig = ct.cdsplot.geomap(average)

    return monthly_mean, fig
```
