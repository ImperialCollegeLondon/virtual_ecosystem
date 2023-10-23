# Example data to run the Virtual rainforest

Some example data is included with Virtual Rainforest to provide an introduction to the
file formats and configuration. To try Virtual Rainforest using this example data, you
first need to install the data to a location of your choice as described [here](./usage.md).

## Elevation data

[This code](../../../virtual_rainforest/example_data/runoff_dummy.py) creates a dummy
elevation map from a digital elevation model ([SRTM](https://www2.jpl.nasa.gov/srtm/))
which is required to run a dummy hydrology model. To cover an area similar to the
climate dummy data, we included a step that reduces that spatial resolution to match the
9 x 9 grid we set for the dummy model. The initial data covers the region 4°N 116°E to
5°N 117°E, see [SAFE wiki](https://safeproject.net/dokuwiki/safe_gis/srtm) for reference
and download.

## Climate data

The dummy climate data set for the example simulation is based on monthly ERA5-Land
which can be downloaded from the [Copernicus climate data store](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels-monthly-means?tab=overview).

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

The following section describes the main steps perfomed to create the following input
variables for the Virtual Rainforest ([see code](../../../virtual_rainforest/example_data/climate_dummy.py)):

* air temperature, [C]
* relative humidity, [-]
* atmospheric pressure, [kPa]
* precipitation, [mm month^-1]
* atmospheric $\ce{CO_{2}}$ concentration, [ppm]
* mean annual temperature, [C]

### Adjustment of units

The standard output unit of ERA5-Land temperatures is Kelvin which needs to be converted
to degree Celsius for the Virtual Rainforest. This includes 2m air temperature and
2m dewpoint temperature which are used to calculate relative humidity later.
The standard output unit for total precipitation in ERA5-Land is meters which we need
to convert to millimeters. Further, the data represents mean daily accumulated
precipitation for the 9x9km grid box, so the value has to be scaled to monthly (here
30 days).
The standard output unit for surface pressure in ERA5-Land is Pascal (Pa) which we
need to convert to Kilopascal (kPa).

### Addition of missing variables

In addition to the variables from the ERA5-Land datasset, a time series of atmospheric
$\ce{CO_{2}}$ is needed. We add this here as a constant field. Mean annual temperature
is calculated from the full time series of air temperatures; in the future, this
should be done for each year.

Relative humidity (RH) is also not a standard output from ERA5-Land but can be calculated
from 2m dewpoint temperature (DPT) and 2m air temperature (T) as follows:

$$ RH = \frac{100\exp(17.625 \cdot DPT)/(243.04+DPT)}
                 {\exp(17.625 \cdot T)/(243.04+T)}
$$

### Matching Virtual Rainforest conventions

Once all input units are adjusted, the variables are re-named according to the Virtual
Rainforest naming convention. The coordinate names have to be changed from
`longitude/latitude` to `x/y` and the units from `minutes` to `meters`. The ERA5-Land
coordinates are treated as the centre points of the grid cells which means that when
setting up the grid, an offset of 4.5 km has to be added.

The Virtual Rainforest is run on a 90 x 90 m grid. This means that some form of
spatial downscaling has to be applied to the dataset, for example by spatially
interpolating coarser resolution climate data and including the effects of local
topography. This is not yet implemented!

For the purpose of a dummy simulation in the development stage, the coordinates can be
overwritten to match the Virtual Rainforest grid and we can select a smaller area.
When setting up the grid, an offset of 45 m has to be added.
Note that the resulting dataset does no longer match a digital elevation model for the
area!

At the moment, the dummy model iterates over time indices rather than real datetime.
Therefore, we add a `time_index` dimension and coordinate to the dataset.

Once we confirmed that our dataset is complete and our calculations are correct, we
save it as a new NetCDF file. This can then be fed into the code data loading system
here {mod}`~virtual_rainforest.core.data`.

## Hydrology data

The hydrology model requires an initial surface runoff field to calculate accumulated
surface runoff. If this variable is not provided by the SPLASH model, it can be created,
for example as a normal distribution, and adjusted to virtual ranforest conventions
([see code here](../../../virtual_rainforest/example_data/runoff_dummy.py)).

## Soil data

[This code](../../../virtual_rainforest/example_data/soil_dummy.py)
creates a set of plausible values for which the soil model absolutely has to
function sensibly for. **It is important to note that none of this data is real data**.
Descriptions of the soil pools can be found [here](./soil/soil_details.md)
source/virtual_rainforest/soil/soil_details.md)

* pH; we're looking at acidic soils so a range of 3.5-4.5 seems plausible.
* Bulk density can vary quite a lot so a range of 1200-1800 kg m^-3 seems sensible.
* Percent clay; we're considering fairly clayey soils, so look at a range of
  27.0-40.0 % clay
* Low molecular weight carbon (LMWC); generally a very small carbon pool, so a range of
  0.005-0.01 kg C m^-3 is used.
* Mineral associated organic matter (MAOM); a huge amount of carbon can be locked away
  as MAOM, so a range of 1.0-3.0 kg C m^-3 is used.
* Microbial Carbon; the carbon locked up as microbial biomass is tiny, so a range of
  0.0015-0.005 kg C m^-3 is used.
* Particulate organic matter (POM); a reasonable amount of carbon is stored as
  particulate organic matter (POM), so a range of 0.1-1.0 kg C m^-3 is used.

## Litter data

The litter component of the dummy model requires the following inputs:

* above ground metabolic litter pools, [kg C m^-2].
* above ground structural litter pools, [kg C m^-2].
* woody litter pools, [kg C m^-2].
* below ground metabolic litter pools, [kg C m^-2].
* below ground structural litter pools, [kg C m^-2].
* lignin proportions of the pools

[This code](../../../virtual_rainforest/example_data/litter_dummy.py)
creates some typical values for the required input data and generates a simple spatial
pattern. **It is important to note that none of this data is real data**. Descriptions
of the relevant litter pools can be found [here](./soil/soil_details.md).

## Plant data

The first dummy version of the Virtual Rainforest did not include a `plant` model.
Therefore, the variables that would be initialized by the `plant` model had to be
provided as an input to the `data` object at the configuration stage.
[This code](../../../virtual_rainforest/example_data/plant_dummy.py) provides a recipe
to create such an input conform with the dummy data for climate, hydrology, and soil.
The following variables are created:

* layer heights, [m]
* leaf area index, [m m^-1]
* layer leaf mass
* evapotranspiration, [mm]

## Animal data

A set of functional groups is provided
[here](../../../virtual_rainforest/example_data/animal_functional_groups.toml).
