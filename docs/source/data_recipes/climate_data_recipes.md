# Climate data recipes

This section provides examples for climate data downloading and simple pre-processing.

The [Copernicus climate data store](./CDS_toolbox_template.md) section contains a list
of recommended data sets to run the Virtual Ecosystem and describes how to download
climate data from the Copernicus
[Climate Data Store](https://cds.climate.copernicus.eu/) (CDS)
and basic pre-processing options using the
[CDS toolbox](https://cds.climate.copernicus.eu/cdsapp#!/toolbox).

```{note}
At present, the pre-processing does not include scaling or topographic adjustment.
```

Metadata:

* Muñoz-Sabater,J. et al: ERA5-Land: A state-of-the-art global reanalysis dataset for
  land applications, Earth Syst. Sci. Data,13, 4349-4383, 2021.
  [https://doi.org/10.5194/essd-13-4349-2021](https://doi.org/10.5194/essd-13-4349-2021)
* Product type: Monthly averaged reanalysis
* Variable: 2m dewpoint temperature, 2m temperature, Surface pressure, Total
  precipitation
* Year: 2013, 2014
* Month: January, February, March, April, May, June, July, August, September, October,
  November, December
* Time: 00:00
* Sub-region extraction: North 6°, West 116°, South 4°, East 118°
* Format: NetCDF3

We have used a simple recipe from this data source to create the climate data used in
the [example data](../virtual_ecosystem/example_data.md). The code in that recipe is
shown below:

````{admonition} climate_example_data.py
:class: dropdown
```{literalinclude} ../../../virtual_ecosystem/example_data/generation_scripts/climate_example_data.py
```
````

In more detail, that script carries out  the main steps perfomed to create the following
input variables for the Virtual Ecosystem:

* air temperature, [C]
* relative humidity, [-]
* atmospheric pressure, [kPa]
* precipitation, [mm month^-1]
* atmospheric $\ce{CO_{2}}$ concentration, [ppm]
* mean annual temperature, [C]

## Adjustment of units

The standard output unit of ERA5-Land temperatures is Kelvin which needs to be converted
to degree Celsius for the Virtual Ecosystem. This includes 2m air temperature and
2m dewpoint temperature which are used to calculate relative humidity later.
The standard output unit for total precipitation in ERA5-Land is meters which we need
to convert to millimeters. Further, the data represents mean daily accumulated
precipitation for the 9x9km grid box, so the value has to be scaled to monthly (here
30 days).
The standard output unit for surface pressure in ERA5-Land is Pascal (Pa) which we
need to convert to Kilopascal (kPa).

## Addition of missing variables

In addition to the variables from the ERA5-Land data, a time series of atmospheric
$\ce{CO_{2}}$ is needed. We add this here as a constant field across all grid cells and
vertical layers. Mean annual temperature is calculated from the full time series of air
temperatures; in the future, this should be done for each year.

Relative humidity (RH) is also not a standard output from ERA5-Land but can be
calculated from 2m dewpoint temperature (DPT) and 2m air temperature (T) as follows:

$$ RH = \frac{100\exp(17.625 \cdot DPT)/(243.04+DPT)}
                 {\exp(17.625 \cdot T)/(243.04+T)}
$$

## Matching Virtual Ecosystem grid and naming conventions

Once all input units are adjusted, the variables are re-named according to the Virtual
Ecosystem naming convention. The coordinate names have to be changed from
`longitude/latitude` to `x/y` and the units from `minutes` to `meters`. The ERA5-Land
coordinates are treated as the centre points of the grid cells which means that when
setting up the grid, an offset of 4.5 km has to be added.

```{note}
The example data is run using a 90 x 90 m grid. This means that some form of
spatial downscaling has to be applied to the dataset, for example by spatially
interpolating coarser resolution climate data and including the effects of local
topography. This is not yet implemented!
```

For the purpose of a example data simulation in the development stage, the script
curently selects a 9 by 9 sample of the grid and overwrites the coordinates to align to
the example grid resolution. Note that the resulting dataset does no longer match a
digital elevation model for the area!

At the moment, the dummy model iterates over time indices rather than real datetime.
Therefore, we add a `time_index` dimension and coordinate to the dataset.
