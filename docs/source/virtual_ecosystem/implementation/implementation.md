# The implementation of the Virtual Ecosystem

The main workflow of the Virtual Ecosystem has the following steps:

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

:::{figure} ../_static/images/simulation_flow.svg
:name: fig_simulation_flow
:alt: Simulation workflow
:width: 650px

The workflow of a Virtual Ecosystem simulation.
:::
