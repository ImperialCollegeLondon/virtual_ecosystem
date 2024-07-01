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
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Climate data download from the COPERNICUS Climate data store and CDS toolbox

The atmospheric variables from regional climate models or observations are typically
provided in spatial and temporal resolutions that are different from the requirements
of the Virtual Ecosystem. This document describes how to download climate data from
the Copernicus [Climate Data Store](https://cds.climate.copernicus.eu/) (CDS) and basic
pre-processing options using the
[CDS toolbox](https://cds.climate.copernicus.eu/cdsapp#!/toolbox).
You need to create a user account to access all data and functionalities.

```{note}
At present, the pre-processing does not include scaling or topographic adjustment.
```

## Climate input variables

The abiotic module of the Virtual Ecosystem requires the following climate input
variables (or derivatives) at each time step (default: monthly means):

* Air temperature (typically 2m; mean, minimum, and maximum)
* Air humidity (typically 2m; relative or specific humidity)
* Air pressure (typically mean sea level or surface pressure)
* Wind speed (typically 10m)
* Precipitation
  
and optionally:

* atmospheric $\ce{CO_{2}}$ concentration
* soil temperature
* soil moisture

## Recommended data sets

We recommend the following data sets to force the Virtual Ecosystem microclimate
simulations:

* ERA5 / ERA5-Land
  
  ERA5 is the fifth generation ECMWF reanalysis for the global climate and weather for
  the past 4 to 7 decades. This reanalysis dataset combines model data with
  observations from across the world into a globally complete and consistent dataset
  using the laws of physics. The data is available in hourly and monthly averaged time
  steps at a spatial resolution is in 0.25 x 0.25 deg resolution. The data set starts
  in 1950 and is updated regularely.

  The full documentation and download link can be accessed
  [here for hourly data](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview)
  and [here for monthly data](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels-monthly-means?tab=overview)

  ERA5-Land is a reanalysis dataset providing a consistent view of the evolution of land
  variables over several decades at an enhanced resolution compared to ERA5 (0.1 x 0.1
  deg).

  The full documentation and download link can be accessed
  [here for hourly data](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview)
  and [here for monthly data](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means?tab=overview)

  Example code to manipulate downloaded ERA5-Land data as used in the `ve_run` example
  is available [here](../../../../virtual_ecosystem/example_data/generation_scripts/climate_example_data.py).

* WFDE5
  
  This global dataset provides bias-corrected reconstruction of near-surface
  meteorological variables derived from the fifth generation of the European Centre for
  Medium-Range Weather Forecasts (ECMWF) atmospheric reanalyses (ERA5). The output is
  available in hourly and daily time steps for the period 1979-2019 in 0.5 x 0.5 deg
  resolution.
  
  The full documentation and download link can be accessed
  [here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/derived-near-surface-meteorological-variables?tab=overview)
  .

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
  .  Monthly data derived from satellite observation (2002 - present) is available
  [here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/satellite-carbon-dioxide?tab=overview)
  . Alternatively, reconstructed gridded monthly $\ce{CO_{2}}$ data for the historical
  period (1953 - 2013) and future CMIP6 scenarios (2015 - 2150) can be downloaded
  [here](https://zenodo.org/record/5021361) {cite:p}`cheng_wei_global_2021`.
  
## Step-by-step example

Follow one of the links above to access overview information about the data set. You
find a detailed documentation of the data set in the 'Documentation' section. To select
data, navigate to the tab 'Download Data'.

### Selection

This is an example of a selection of tabs to download historical '2m air temperature'
from the CORDEX-SEA (you can download multiple variables and years in one request):

* Domain (South-East Asia),
* Experiment (here: 'historical', RCPs available)
* Horizontal resolution ('0.22 degree x 0.22 degree')
* Temporal resolution ('daily mean')
* Variables (here: '2m_air_temperature')
* Global climate model (here: 'mohc_hadgem2_es')
* Regional climate model (here: 'gerics_remo2015')
* Ensemble member (r1i1p1)
* Start year and End year (here: 2001-2005)

Once you selected the data, you can either download the dataset for further processing
or click on 'show Toolbox request' at the bottom of the page, copy the code, and open
the CDS toolbox editor.

The code to manipulate climate data as used in the `ve_run` example is available
[here](../../../../virtual_ecosystem/example_data/generation_scripts/climate_example_data.py).

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

The data handling for simulations is managed by the {mod}`~virtual_ecosystem.core.data`
module and the {class}`~virtual_ecosystem.core.data.Data` class, which provides the
data loading and storage functions for the Virtual Ecosystem. The data system is
extendable to provide support for different file formats and axis validation but that is
beyond the scope of this document.
