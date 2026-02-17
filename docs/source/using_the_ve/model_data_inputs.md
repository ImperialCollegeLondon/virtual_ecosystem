---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
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

### Preparing gridded data input files

You will first need to look at the required variables for each science model that you
want to include in the simulation and make a list of those variables. Details of the
variables required by each model can be found in the [data
variables](./variables/variables.md) page.

```{warning}
The `axis` field in that data is currently **not to be trusted** - we have
not systematically reviewed that data and there isn't any internal checking that the
stated axes are what is on the data.
```

Then for each variable you will need to compile appropriate data - given the axes
required - and saved as NetCDF files, providing labelled dimensions and coordinates to
match input data to the axes and coordinates of your model configuration . See the [data
object](../development/design/data.md) page for more information on loading data and the
[example data](./example_data.md) page for examples of NetCDF input files.

### Configuring gridded data inputs

```{tip}
This section only covers the configuration of gridded data files. You will also need to
configure the [model core settings](./core_configuration.md), the [science model
settings](./science_model_configuration.md) for your simulation and the
location of [other data input files](#other-data-inputs).
```

Once you have your input data files, you will then need to add the data to your model
configuration. This is done using the `core.data.variable` configuration section: for
each variable, you need to include a configuration section giving the variable name and
then the data file in which the variable is found. Note that you can have multiple
variables in a single NetCDF file.

As an example, the following TOML gives the configuration for loading two climatic data
variables stored in the same file:

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
