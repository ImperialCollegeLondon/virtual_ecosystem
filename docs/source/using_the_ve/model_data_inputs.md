---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
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
---

# Model data inputs

In order to run a Virtual Ecosystem model you will need to provide:

* A configuration for the model, including both the [core
  configuration](./core_configuration.md) and [configuration for the science
  models](./science_model_configuration.md) you want to include.
* Files providing data for all the variables needed to set the initial state of the
  simulation.

This page provides an overview of how to start thinking about preparing these model
inputs and describes the formats and the validation carried out on them.

## Defining your simulation site

The simulation runs on discrete time steps within a grid of cells so, before you start
doing any data preparation or configuration, you will need to decide on the spatial and
temporal extents of the simulation. The configuration of these model properties are
described in the [core configuration](./core_configuration.md) page, but in summary:

* The [spatial grid](./configuration/grid.md) definition sets the number of grid cells
  in the simulation, the cell size and the spatial coordinates of the cell. The Virtual
  Ecosystem expects coordinates in metres, so you should choose a [projected coordinate
  system](https://en.wikipedia.org/wiki/Projected_coordinate_system) for your site of
  interest and define a set of grid cells to cover the area at a resolution appropriate
  for your data.

  Do not use a geographic coordinate system - you cannot use degree coordinates with the
  Virtual Ecosystem.

* The Virtual Ecosystem updates the simulation state at discrete intervals. You need to
  decide how long an interval to use and how many time steps to run.

These details need to be consistent across all of the input data, so it may be useful to
create a core site extents file that all your data preparation scripts can use to set
these values.

## Model configuration

The Virtual Ecosystem code is organised into distinct **models**, each of which is
responsible for a different part of the simulation. Each model, including the central
core model needs to be configured - see the [science model configuration
page](./science_model_configuration.md)

Each model has its own configuration settings - which can be used to control particular
options or paths to required extra files - but also a set of model specific constants.
Both of these are controlled through the model configuration file: see the example
configuration files in the [example data](./example_data.md) page.

The configuration is validated automatically when it is loaded and the simulation will
exit if there are validation issues with configuration data. The details of any issues
are written to the simulation log file.

## Gridded model data inputs

The simulation then also requires data to set the initial conditions of the grid cells,
to provide time series for each cell of forcing variables, and to calculate other
internal variables.

The majority of initial data will consist of arrays of data that are structured along
one or more of the Virtual Ecosystem dimensions. These are things like a time series of
above canopy air temperature or initial values for soil nitrogen concentations. At the
moment have we the following critical dimensions within the VE:

* `spatial`: This is actually a kind of aggregate dimension, because spatial data can
  use `cell_id` or `x` and `y` coordinates - these two things map onto each other (see
  the [core.grid](./core_configuration.md#the-spatial-grid) configuration settings for
  details).

* `time`: This dimension is used to index time steps along configured time extent for
  the simulation. Some variables only need to set the initial conditions and do not need
  a time axis, but other forcing variables (like temperature and precipitation) need to
  supply a value for each cell at each time step.

* `pft`: Some data requires values per plant functional type. An example is the initial
  number of propagules per PFT in grid cells.

### Preparing model input files

You will first need to look at the required variables for each science model that you
want to include in the simulation and make a list of those variables. Details of the
variables required by each model can be found in the [data
variables](../virtual_ecosystem/implementation/variables.md) page.

```{warning}
The `axis` field in that data is currently **not to be trusted** - we have
not systematically reviewed that data and there isn't any internal checking that the
stated axes are what is on the data.
```

Then for each variable you will need to compile appropriate data - given the axes
required - and saved as NetCDF files, providing labelled dimensions and coordinates to
match input data to the axes and coordinates of your model configuration . See the [data
object](./data/data.md) page for more information on loading data and the [example
data](./example_data.md) page for examples of NetCDF input files.

### Configuring model inputs

Once you have your input data files, you will then need to add the data to your model
configuration. This is done using the `core.data.variable` configuration section: for
each variable, you need to include a configuration section giving the variable name and
then the data file in which the variable is found. Note that you can have multiple
variables in a single NetCDF file.

As an example, the following TOML gives the configuration for loading two climatic data
variables:

```toml
[[core.data.variable]]
file_path = "../data/example_climate_data.nc"
var_name = "air_temperature_ref"
[[core.data.variable]]
file_path = "../data/example_climate_data.nc"
var_name = "relative_humidity_ref"
```

### Validating model inputs

The `ve_run` command automatically checks the dimensions of model data variables when
they are loaded from file and verifies that the dimension lengths and any coordinates
(such as `x` and `y` locations) are congruent with the model configuration.

### Model outputs

The [data outputs section](./core_configuration.md#data-output-settings) in the core
configuration controls which data are written out as the simulation progresses. The data
will be written out in NetCDF files with the same axis structures as the inputs.

## Other data inputs

Some initial model data does not use the main data loading system. This is typically
where the data does not map neatly onto one of the core axes mentioned above. These
data will have specific model configuration settings. For example:

* The plants model requires a set of defined plant functional types (PFTs). This is
  a CSV file defining a set required trait values for each PFT, and the path to this
  file is set in the [plants model configuration
  options](./science_model_configuration.md#plant-functional-types)

* The plant model also requires a defined initial cohort structure, which sets the
  initial cohorts present in each cell. This again is defined as a CSV file with the
  path set in the [plants model configuration
  options](./science_model_configuration.md#plant-cohort-data)

* The animal model also requires a defined initial cohort structure.
