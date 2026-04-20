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
mystnb:
  render_markdown_format: myst
---

# Running the Virtual Ecosystem for your location

This page guides you through setting up Virtual Ecosystem simulations for your location.
The complete setup requires extensive data and effort, so this tutorial focuses on the
general process of changing model settings and loading new data. For the full setup,
consult the [core settings](./core_settings/overview.md) and [model-specific setup
details](./model_details/overview.md). We strongly recommend [running the example
simulation](./virtual_ecosystem_in_use.ipynb) before configuring a new site.

To run a Virtual Ecosystem simulation for your own location you will need to:

1. [Select the set of models you want to run](#selecting-the-models-you-want-to-run)
1. [Provide any location specific constant values (as well as any constants that you
  disagree with our choice of default value for)](#changing-model-constants)
1. [Provide the core details of the experiment you want to run, e.g. grid size, grid
   resolution, simulation length, etc](#changing-the-core-simulation-setup)
1. [Provide NetCDF input data that matches the spatial (and in some cases temporal)
   dimensions of your experimental
   area](#providing-the-data-required-to-run-your-simulations)
1. [Provide data on the plant functional types and animal functional groups included in
   the simulation (as csv inputs)](#other-data-inputs)

## Configuration system overview

All the changes you will need to make to setup the Virtual Ecosystem will involve making
changes to the configuration. So, we will start this tutorial with a brief overview
of how the Virtual Ecosystem configuration system is used.

The configuration can be split up over whatever amount of files you wish (though we
would advise against structuring it as one massive hard to read file, or hundreds of
tiny files). All configuration files must be written as [`toml`](https://toml.io/en/).
When the run starts, the configuration inputs are combined and the resulting combined
model configuration is validated. By default, the combined configuration is written out
to a single file to provide a permanent record of the model configuration. In all cases,
your `toml` configuration files only need to specify values that do not have a default
value (typically file paths) or where you want to change a default.

An example of a `toml` configuration is shown below:

```toml
[core]
[core.grid]
cell_nx = 10
cell_ny = 10
```

Here, the first tag indicates the module in question (e.g. `core`), and subsequent tags
indicate (potentially nested) module level configuration details (e.g. horizontal grid
size `cell_nx`).

Note that **configuration setting cannot be repeated between files** as there is no way
to establish which of two values (of e.g. `core.grid.cell_nx`) the user intended to
provide. When settings are repeated, the validation of the configuration will fail.

Validation occurs automatically when the simulation starts. If any issues are found then
the simulation will terminate, with the details of the issues being written to the
simulation log file. The validation checks for a much broader range of things that just
repeated settings, including that configured input files actually exist and that numeric
inputs are within a range of accepted values.

### Selecting the models you want to run

The Virtual Ecosystem allows you to choose which set of models you wish to run. Unless
you are trying to run static model simulations (in which case consult the [static mode
guide](./virtual_ecosystem_in_static_mode.ipynb)), you will always want to run the
primary set of Virtual Ecosystem models. In this case, the only choice you will have to
make is which microclimate implementation you wish to use (i.e. `abiotic_simple` or
`abiotic`). The choice of models to be configured is indicated by including the required
model names as top level entries in the model configuration. Note that the model name is
required, even if the configuration uses all of the default settings. For example, this
configuration specifies that six models are to be used, all with their default settings:

```toml
[core]  # optional
[soil]
[litter]
[hydrology]
[plants]
[abiotic]
[animals]
```

The `[core]` element is optional as the Virtual Ecosystem core module is always
required and the default core settings will be used if it is omitted. It can be useful
to include it as a reminder that a particular configuration is intentionally using the
default settings. Each module configuration section can of course be expanded to change
defaults.

```{note}
The order in which models are run is **not** something that can be controlled by users
(i.e. execution order is **not** controlled by where models are placed in the
configuration). As some models require outputs of the other models in order to run,
there are hard constraints the order they can be run in. The simulation automatically
choose a valid model execution order during the configuration process.
```

## Changing model constants

The majority of constants included in the Virtual Ecosystem are universal and so are not
expected to vary site to site. This means that you **do not** have to provide new values
for them to set up a new site (though you are very welcome to change them if you
disagree with our choices of values). However, some things that we include as
"constants" are in fact site specific (e.g. the deposition rate of inorganic
phosphorus), and you will have to change them for your site setup. To change the value
of constant you need to provide an updated value for it within a configuration file,
under a `[model_name.constants]` tag. This looks like:

```toml
[soil.constants]
phosphorus_deposition_rate = 2.0e-05 # High rate for Amazon Rainforest
```

You **only** need to provide values for constants that you wish to change (i.e. the site
specific ones, and any for which you disagree with our choice of default values). All
constants that you don't provide values for will just use the default value. Details of
all Virtual Ecosystem constants and their default values can be found in the [model
specific setup details documentation](./model_details/overview).

## Changing the core simulation setup

Next, you need to provide are the core settings for your simulation runs. There are a
[large number of configuration options](./core_settings/core_configuration.md) that you
will need to decide on. However, to keep this tutorial to reasonable length we will
focus on two of the most important, the spatial and temporal scales of the simulation.

The spatial scales of the simulation are controlled by the settings under `[core.grid]`.
The Virtual Ecosystem expects coordinates in metres, so you should choose a [projected
coordinate system](https://en.wikipedia.org/wiki/Projected_coordinate_system) for your
site of interest and define a set of grid cells to cover the area at a resolution
appropriate for your data. You need to **take real care** when setting the spatial scale
as the data you provide to the model **has to** be on the same scale, i.e. all input
data must be for the same grid size, shape and extent.

```{important}
  Do not use a geographic coordinate system - you cannot use degree coordinates with the
  Virtual Ecosystem.
```

The temporal settings are controlled by the settings under `[core.timing]`. The Virtual
Ecosystem updates the simulation state at discrete intervals. You need to decide how
long an interval to use and how many time steps to run. Again, you need to **take real
care** when setting the temporal scale as any time varying input data (e.g. climate
inputs) you provide to the model **has to** cover the time period that you want your
simulation to run for.

These core simulation settings can be changed in the same way we previously changed
constants, i.e.

```toml
[core.grid]
cell_area = 10000.0 # hectare grid cells (i.e. 10000.0 m^2)
cell_nx = 100 # 100 grid cells in x direction
cell_ny = 50 # 50 grid cells in y direction

[core.timing]
start_date = "2018-01-01" # Start date in YYYY-MM-DD format
run_length = "5 years" # Run for 5 years with default update time step (1 month)
```

```{important}
  These details need to be consistent across all of the input data, so it may be useful
  to create a core site extents file that all your data preparation scripts can use to
  set these values.
```

## Providing the data required to run your simulations

The final step to setting up your simulations is adding the required data. This is both
the data that defines the initial state of your study site and time series data for the
forcing variables (e.g. climate data). This is a pretty complex step, so before we get
into the details, we should briefly mention how the Virtual Ecosystem stores data.

The majority of variables in the Virtual ecosystem are stored in the `data` object (we
will talk about the ones that aren't later). Data is stored in the data object object in
a format similar to [`netCDF`](https://www.unidata.ucar.edu/software/netcdf), i.e. this
is what the {term}`LMWC` soil variable looks like in the example data:

```{code-cell} ipython3
:tags: [remove-cell]

%%bash
# Remove any existing ve_example installations from the temporary directory
if [ -d /tmp/ve_example ]; then
  rm -r /tmp/ve_example
fi

# Install the example data directory from the Virtual Ecosystem package
ve_run --install-example /tmp/
```

```{code-cell} ipython3
:tags: [remove-cell]

import xarray

# Example: load or define your datasets
ve_example_data = xarray.load_dataset("/tmp/ve_example/data/example_soil_data.nc")
```

```{code-cell} ipython3
:tags: [hide-input]

ve_example_data["soil_cnp_pool_lmwc"]
```

Because the formats are so similar, input data must be provided as `netCDF` files, which
are then added to the `data` object as part of the configuration process.

### Input data dimensions

The `netCDF` files that you provide will be arrays of data, e.g. initial values for soil
nitrogen concentrations or above canopy air temperatures over time. Many variables will
be arrays over multiple different dimensions (e.g. space and time). The array data that
you provide must use dimensions that the Virtual Ecosystem recognises. We provide
[detailed description of these critical dimensions (or core axes) elsewhere](./axes.md),
but in short the possible dimensions are:

* `spatial`: This is actually a kind of aggregate dimension, because spatial data can
  use `cell_id` or `x` and `y` coordinates - these two things map onto each other (see
  the [core.grid](./core_settings/core_configuration.md#the-spatial-grid) configuration
  settings for details).

* `time`: This dimension is used to index time steps along configured time extent for
  the simulation. Some variables only need to set the initial conditions and do not need
  a time axis, but other forcing variables (like temperature and precipitation) need to
  supply a value for each cell at each time step.

* `pft`: Some data requires values per plant functional type. An example is the initial
  number of propagules per PFT in grid cells.

* `layer`: Some data varies vertically by canopy layer (e.g. temperature), and this
  dimension captures that variation. This dimension is primarily used for variables
  generated during the model run, so you are unlikely to need to use it for input data
  (unless you are running models in [`static` mode](./core_settings/static_models.md)).

### Preparing your array data input files

The first thing you need to do to prepare your files is to look at the required
variables for each science model that you want to include in the simulation and make a
list of those variables.

Details of the variables required to setup each model can be found in the [data
variables](./variables/variables.md) page. Note that you only have to provide and
configure the input variables shown in that table in bold. The other setup variables for
a model will have been calculated by the setup process of earlier models.

```{warning}
The `axis` field in that data is currently **not to be trusted** - we have
not systematically reviewed that data and there isn't any internal checking that the
stated axes are what is on the data.
```

Then for each variable you will need to compile appropriate data - given the axes
required - and saved as NetCDF files, providing labelled dimensions and coordinates to
match input data to the axes and coordinates of your model configuration. The process
for compiling this data varies dramatically by model, and you should refer to the [model
specific setup documentation](./model_details/overview.md) to understand how to compile
data for the specific models you are interested in. You can also consult the [example
data](./example_data.md) page for examples of NetCDF input files.

:::{important}
Input variables are usually clearly thematically linked to the scientific domain of a
single model. However, in some cases models require less obvious data. For example:

* The plants model requires shortwave downwelling radiation. Although this seems like an
  abiotic variable, it is required for modelling plant growth and the plants model
  partitions radiation within the canopy.

* The animal model requires fungal fruiting body densities for consumption by
  fungivores. The soil and litter models update these values but the data is first
  required by the animal model.

Collecting data for a simulation is likely to involve a data science team with different
domain knowledge for the different models. You may not want to break down data
collection tasks strictly by model and instead identify variables that may require
domain knowledge from elsewhere in the team.
:::

### Configuring array data inputs

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

All file paths that you provide **must** be valid paths to `netCDF` files. Configuration
errors will also occur if any of the variable names (`var_name`) you provide are not
found in the associated `netCDF` file. Finally, if the dimension lengths or any
coordinates (such as `x` and `y` locations) of a variable are not compatible with the
model configuration then a configuration error will occur.

### Other data inputs

Some initial model data does not use the main data loading system. This is typically
where the data does not map neatly onto one of the core axes mentioned above. These
data will have specific model configuration settings. For example:

* The plants model requires a set of defined plant functional types (PFTs). This is
  a CSV file defining a set required trait values for each PFT, and the path to this
  file is set in the [plants model configuration
  options](./model_details/plants/plants_config.md#plant-functional-types)

* The plant model also requires a defined initial cohort structure, which sets the
  initial cohorts present in each cell. This again is defined as a CSV file with the
  path set in the [plants model configuration
  options](./model_details/plants/plants_config.md#plant-cohort-data)

* The animal model also requires a set of defined [functional
  groups](./model_details/animal/functional_group_data.md). These are defined in a CSV
  file with the path provided as part of the animal model configuration.

* The soil model requires [parameter estimates for the microbial functional groups and
  enzyme classes](./model_details/decay/default_microbial_params.md) that it uses.
  However, they are added as part of the configuration (in a similar manner to model
  constants) rather than in a data file.

There is no generic system for reading in CSV data, instead a path to each file needs to
be provided as part of the configuration of the relevant model, e.g.

```toml
[plants]
cohort_data_path = "../data/example_plant_cohorts.csv"
pft_definitions_path = "../data/plant_pfts.csv"

[animal]
functional_group_definitions_path = '../data/animal_functional_groups.csv'
```

## List of required data files

To close this tutorial, we will briefly recap the full set of files that you need to
provide:

* You must provide a folder of `toml` files containing the configuration settings for
  Virtual Ecosystem. These files can be named whatever you like (though you should aim
  to give them easy to understand names). You can split the configuration settings over
  as many or as few files as you like (though you want to ensure that purpose of each
  individual file is obvious). A path to this folder has to be provided when using
  `ve_run`.
* You must provide array data for every variable that is required to setup or update the
  models you wish to run, **except** the ones that are populated by one of the other
  models. To figure out what these variables are you should consult the [data
  variables](./variables/variables.md) page. These variables can be provided over as
  many or as few files as you wish, but again you need to make sure that the purpose of
  each file is clear. For the example data we chose to split by model, but if a
  different split makes more sense for your use case you should use that instead. Paths
  to each of these files then need to be provided as part of the configuration.
* You also need to provide three csv files. One defining plant functional types, one
  giving the location and density of the plant cohorts, and one giving the location and
  density of the animal cohorts. You can name these files whatever you like (again,
  choose sensible names), but need to provide paths to each of them as part of the
  configuration.
