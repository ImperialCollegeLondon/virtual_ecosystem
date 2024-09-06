# Notes on climate data pre-processing

The atmospheric variables from regional climate models, observations, or reanalysis are
typically provided in spatial resolutions that are much coarser than the
requirements of the Virtual Ecosystem, and follow different naming and unit conventions.
Please check the following:

* **Does the input climate data match the model grid?**

  This match is necessary for the model to run and to have the effects of topography and
  elevation incorporated that we described in the
  [theory section](../../virtual_ecosystem/theory/microclimate_theory.md#factors-affecting-microclimate).
  This spatial downscaling step is not included in the Virtual Ecosystem.

* **What is the reference height?**

  Different data sources provide data at
  different vertical levels and with different underlying assumptions, which lead to
  biases in the model output. For example, the reference height can be 1.5 m or 2 m, above
  ground or above the canopy, measured or interpolated. In the Virtual Ecosystem, the
  reference height is assumed to be 2 m above the top of the canopy (2 m above the
  ground in absence of vegetation).

* **What are the expected units?**

  Make sure that the units of the required input variables match those of the required
  variables in the table above, e.g temperatures in Celsius, pressure in kPa, etc.

* **What are the variables names?**

  Check the input data variable names match the Virtual Ecosystem naming convention
  as listed in the table above.

We have used a simple pre-processing script to create the climate data used in
the [example data](../../using_the_ve/example_data.md) from ERA5-Land monthly averaged
data, downloaded from the Copernicus Climate Data Store
[here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means?tab=overview).
The code is available [here](../../using_the_ve/example_data.md#climate-data).
