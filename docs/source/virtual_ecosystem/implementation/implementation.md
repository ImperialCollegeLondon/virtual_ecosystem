# The implementation of the Virtual Ecosystem

The main workflow of the Virtual Ecosystem ({numref}`fig_simulation_flow`) has the
following steps:

* Users provide a set of **configuration files** that define how a particular simulation
  should run.
* That configuration is validated and compiled into **configuration object** that is
  shared  across the rest of the simulation.
* The configuration is then used to create several **core components**: the spatial
  grid, the core constants, the vertical layer structure and the model timing. These
  components are also shared across the simulation.
* The configuration also sets the locations of the **initial input data**. These
  variables are then loaded into the core **data store**, with validation to check that
  the data are compatible with the model configuration.
* The configuration also defines a set of **science models** that should be used in the
  simulation. These are now configured, checking that any configurations settings
  specific to each science model are valid.
* The configured models are then **initialised**, checking that the data store contains
  all required initial data for the model and carrying out any calculations for the
  initial model state.
* The system now iterates forward over the configured time steps. At each time step,
  there is an **update** step for each science model. The model execution order is
  defined by the set of variables required for each model, to ensure that all required
  variables are updated before being used.

:::{figure} ../../_static/images/simulation_flow.svg
:name: fig_simulation_flow
:alt: Simulation workflow
:width: 650px

The workflow of a Virtual Ecosystem simulation (click to zoom).
:::

## Configuration files

The configuration files use the [`TOML`](https://toml.io/en/) format to provide all of
the details for running a simulation: the spatial layout, the locations of the initial
input data, everything. You can see what an example complete configuration file looks
like below - but don't panic and read the [configuration
documentation](../../using_the_ve/configuration/config.md) on using the virtual
ecosystem to find out more.

::::{dropdown} An example configuration file
:::{literalinclude} ../../_static/vr_full_model_configuration.toml
:language: toml
:::
::::

## Core Components

TBD

## Data

The Virtual Ecosystem primarily expects data to be imported from files in [NetCDF
format](https://www.unidata.ucar.edu/software/netcdf/). This is not the easiest format
to work with but the datasets in the Virtual Ecosystem are commonly multi-dimensional
arrays (e.g. space and time), and the NetCDF format supports this kind of data, as well
as providing critical metadata for data validation.

## Variables

The Virtual Ecosystem has an [long list of variables](#variables) (TBD - update
link when variables system goes live) that are used to set up the simulation and then
update the model state through time. The configuration files need to provide the
locations of the variables required to initialise each science model.

## Science models

The science models in the Virtual Ecosystem all share a common framework, which is used
to coordinate the initialisation and update processes within each model. The models used
for a specific simulation can vary and the following models are currently being
developed:

* the [simple abiotic model](./abiotic_simple_implementation.md),
* the [process-based abiotic model](./abiotic_implementation.md),
* the [hydrology model](./hydrology_implementation.md),
* the [animal model](./animal_implementation.md),
* the [plants model](./plants_implementation.md),
* the [soil model](./soil_implementation.md), and
* the [litter model](./litter_implementation.md).

New models [can be added](../../development/design/defining_new_models.md ) to the
Virtual Ecosystem, although this requires reasonable programming expertise.
