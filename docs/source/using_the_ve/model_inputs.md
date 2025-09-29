---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
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

# Model inputs

```{warning}

This is draft text

```

In order to run a Virtual Ecosystem model you will need to provide:

* the configuration for the model, and
* data for all the variables needed to set the initial state of the simulation.

This page provides an overview of how to start thinking about preparing these model
inputs and describes the formats and the validation carried out on them.

## Defining your simulation site

The simulation runs on discrete time steps within a grid of cells so, before you start
doing any data preparation or configuration, you will need to decide on the spatial and
temporal extents of the simulation.

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
core model needs to be configured.

Each model has its own configuration settings - which can be used to control particular
options or paths to required extra files - but also a set of model specific constants.
Both of these are controlled through the model configuration file: see the example
configuration files in the [example data](./example_data.md) page.

1. **Model configuration values**

    The model configuration options are defined in a file called the model schema and
    are then set by users in the model configuration TOML files. An example
    configuration option would be the maximum number of canopy layers in the simulation.

    *Format*: entries in a TOML configuration file.

    *Validation*: The model configuration is checked when the simulation starts. The
    `ve_run` command will log any configuration errors and exit without running any of
    the actual simulation if any of the required variables are missing or have the wrong
    format (as specified in the model schema).

    *Documentation*: TBD

1. **Model constants**

    Each model has its own set of constants, defining values that are held constant
    across the whole simulation. An example would be the `wind_reference_height` in the
    `abiotic` model.

    *Format*: Model constants are configured through the model TOML configuration file.

    *Validation*: Constant values are handled by the constant loading process - which
    currently only checks for missing or mistyped constant names - and then any further
    value validation (e.g. sign, bounds etc) is down to model specific checking.

    *Documentation*: The constants objects *are* documented but only in the API
    documentation. For example:
    <https://virtual-ecosystem.readthedocs.io/en/latest/api/models/abiotic/abiotic_constants.html>

## Model data

The simulation also requires data to set the initial conditions of the grid cells and to
calculate other internal variables.

1. **Model data variables**

    The majority of initial data will consist of arrays of data that are structured
    along one or more of the Virtual Ecosystem dimensions. These are things like a time
    series of above canopy air temperature or initial values for soil nitrogen
    concentations. At the moment have we four critical dimensions within the VE:

    * `spatial`: This is actually a kind of aggregate dimension, because spatial data
      can use `cell_id` or `x` and `y` coordinates - these two things map onto each
      other (see the [grid](./configuration/grid.md) page for details).

    * `time`: This dimension is used to index time steps along configured time extent
      for the simulation. Some variables only need to set the initial conditions and do
      not need a time axis, but other forcing variables (like temperature and
      precipitation) need to supply a value for each cell at each time step.

    * `pft`: Some data requires values per plant functional type. An example is the
      initial number of propagules per PFT in grid cells.

    *Format*: These data will be loaded through the `core.data.variable` syntax in the
    configuration TOML and will typically be be stored as NetCDF files, providing
    labelled dimensions and coordinates. See the [data object](./data/data.md) page for
    more information on loading data and the [example data](./example_data.md) page for
    examples of NetCDF input files.

    *Validation*: The `ve_run` command automatically checks the dimensions of model data
    variables when they are loaded from file and verifies that the dimension lengths and
    any coordinates (such as `x` and `y` locations) are congruent with the model
    configuration.

    *Documentation*: The variables are documented in the [data
    variables](../virtual_ecosystem/implementation/variables.md) page.
    However, the `axis` field in that data is currently **not to be trusted** - we have
    not systematically reviewed that data and there isn't any internal checking that the
    stated axes are what is on the data.

    *Output*: These variables are written out in NetCDF files with the same axis
    structures as the inputs. The model configuration dictates which variables get
    written out when.

1. **Other data inputs**

    Some initial model data does not use the main data loading system. This is typically
    where the data does not map neatly onto one of the core axes mentioned above. The
    following files are the key examples

    * The plants model requires a set of defined plant functional types (PFTs). This is
      a CSV file defining a set required trait values for each PFT, and the path to this
      file is set in the plants model configuration options.

    * The plant model also requires a defined initial cohort structure, which sets the
     initial cohorts present in each cell. This again is defined as a CSV file with the
     path set in the plants model configuration options.
