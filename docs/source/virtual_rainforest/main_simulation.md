# Virtual Rainforest simulation flow

This document describes the main simulation flow of the Virtual Rainforest model. This
flow will now be set out step by step.

## Loading configuration files

As a first step, configuration files are loaded in and validated. These files are of
`toml` format and are found based on paths provided by the user. When these files are
loaded in they are validated to ensure that they are valid `toml`, and that all the
required settings are present and not duplicated. The Virtual Rainforest code provides
default settings for some configuration options and these will be used automatically if
that setting is not found in the configuration, but if no default is set then the
validation will fail. Further details can be found in the [configuration
documentation](./core/config.md).

## Grid creation

The next step is creating a grid, which defines the spatial structure of the simulation:
the area, coordinate system and geometry of the individual cells that will be used in
the simulation. The [grid documentation](./core/grid.md) describes this object further.
This grid is then used to create an empty `Data` object of the correct size to describe
the simulation.

## Loading and validation of input data

This `Data` object now needs to be populated with data. The data used in the simulation
is stored in a set of data files which are specified in the configuration. This data is
then loaded using the `data.load_data_config` method, which has built in validation
procedures to ensure that the loaded data can be mapped onto the spatial grid and also
other core dimensions for the configured simulation. Further details can be found in the
[data system](./core/data.md) and [core axes](./core/axes.md) documentation.

## Configuration of specific models

The Virtual Rainforest is implemented as model objects, each of which is responsible for
simulating a particular aspect of the rainforest ecosystem. The models used for the
specific simulation run can be set in the configuration. This will typically be the four
standard models ([`AbioticModel`](../api/abiotic.md), `AnimalModel`, `PlantModel` and
[`SoilModel`](../api/soil.md)), but this can be extended to include new models or
different combinations of models. For more information about implementing new models,
see [this page](../development/defining_new_models.md) about the required module
structure and the model API. Once a list of models to configure has been extracted from
the configuration, they are then all configured.

## Extracting simulation timing details

The configuration contains a start time, an end time and an time interval for checking
whether models need to be updated. Once these details are extracted from the
configuration, a check is performed to ensure that the simulation update interval works
suitably with the time steps for individual models, i.e. that no model has a shorter
time step than the overall simulation update interval.

## Saving the initial state

The `data` object has now been populated with all of the configured data required to run
the model. It can now optionally be saved to a file set in the configuration to generate
a single data file of the initial model state.

## Simulating over time

The previously extracted timing details are used to setup a timing loop, which runs from
the start time to the end time with a time step set by the update interval. At each
step a check is performed to determine if any models need to be updated. Any that do
need to be updated are then updated.

## Saving the final state

After the full simulation loop has been completed the final simulation state can be
saved. Whether to save this state and where to save it to are again configuration
options, but in this case the default is for the final state to be saved.
