---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

# The implementation of the Virtual Ecosystem

The main workflow of the Virtual Ecosystem ({numref}`fig_simulation_flow`) has the
following steps:

- Users provide a set of **configuration files** that define how a particular simulation
    should run.
- That configuration is validated and compiled into **configuration object** that is
    shared across the rest of the simulation.
- The configuration is then used to create several **core components**: the spatial
    grid, the core constants, the vertical layer structure and the model timing. These
    components are also shared across the simulation.
- The configuration also sets the locations of the **initial input data**. These
    variables are then loaded into the core **data store**, with validation to check that
    the data are compatible with the model configuration.
- The configuration also defines a set of **science models** that should be used in the
    simulation. These are now configured, checking that any configurations settings
    specific to each science model are valid.
- The configured models are then **initialised**, checking that the data store contains
    all required initial data for the model and carrying out any calculations for the
    initial model state.
- The system now iterates forward over the configured time steps. At each time step,
    there is an **update** step for each science model. The model execution order is
    defined by the set of variables required for each model, to ensure that all required
    variables are updated before being used.

:::{figure} ../../\_static/images/simulation_flow.svg
:name: fig_simulation_flow
:alt: Simulation workflow
:width: 650px

The workflow of a Virtual Ecosystem simulation (click to zoom).
:::

## Configuration files

The configuration files use the [`TOML`](https://toml.io/en/) format to provide all of
the details for running a simulation: the spatial layout, the locations of the initial
input data, everything. See the [configuration
documentation](../../using_the_ve/configuration/config.md) in the Using the Virtual
Ecosystem section to find out more.

## Core Components

The Virtual Ecosystem uses several core components to validate and coordinate shared
configuration settings and to initialise model structures. The components are listed
below but also see the [core components overview](./core_components_overview.md) for
more detail:

- The Config object, containing the validated configuration.
- The Grid object, containing the shared spatial structure of the simulation.
- The LayerStructure object, which is used to coordinate the vertical structure of the
    simulation from the top of the canopy down to the lowest soil layer.
- The CoreConstants object, which is used to provide fixed constant values that are
    shared across science models. Each model will have a separate model constants object
    that is used to set model-specific constants.
- The ModelTiming object, which is used to validate the runtime and update frequency of
    the simulation.
- The Data object, which is used to store all of the initial input data along with the
    variables representing the rest of the model state. This is also used to pass data
    between the different models.

## Data

The Virtual Ecosystem primarily expects data to be imported from files in [NetCDF
format](https://www.unidata.ucar.edu/software/netcdf/). This is not the easiest format
to work with but the datasets in the Virtual Ecosystem are commonly multi-dimensional
arrays (e.g. space and time), and the NetCDF format supports this kind of data, as well
as providing critical metadata for data validation.

<!-- TODO: fix this link to the variables.rst file
when the variables system gets merged -->

The Virtual Ecosystem has a long list of the
[variables](../../../../virtual_ecosystem/data_variables.toml) that are used to set up
the simulation and then update the model state through time. The configuration files
need to provide the locations of the variables required to initialise each science
model.

## Science models

The science models in the Virtual Ecosystem all share a common framework, which is used
to coordinate the initialisation and update processes within each model. Each model has
an implementation page describing the initialisation and update stages and required
data, but the [science model overview](./science_model_overview.md) page provides a
quick summary of the models and how they work.

The current suite of science models are:

- the [simple abiotic model](./abiotic_simple_implementation.md),
- the [process-based abiotic model](./abiotic_implementation.md),
- the [hydrology model](./hydrology_implementation.md),
- the [animal model](./animal_implementation.md),
- the [plants model](./plants_implementation.md),
- the [soil model](./soil_implementation.md), and
- the [litter model](./litter_implementation.md).

New models [can be added](../../development/design/defining_new_models.md) to the
Virtual Ecosystem, although this requires reasonable programming expertise.
:::
