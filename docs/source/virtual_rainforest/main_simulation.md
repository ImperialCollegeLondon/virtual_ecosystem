# Virtual Rainforest simulation flow

This document describes the main simulation flow of the Virtual Rainforest model. This
flow will now be set out step by step.

## Loading configuration files

As a first step, configuration files are loaded in and validated. These files are of
`toml` format and are found based on paths provided by the user. When these files are
loaded in they are validated to ensure that they are valid `toml`, and that no tags are
repeated. In cases where a required tag is not present in any file, the validation will
fail unless a default value for it has been set. Further details can be found in the
[configuration documentation](./core/config.md).

## Grid creation

The next step is creating a grid, which defines the area and resolution of the
simulation. The [grid documentation](./core/grid.md) describes this object further. This
grid is then used to create an empty `Data` object of the correct size to describe the
simulation.

## Loading and validation of input data

This `Data` object now needs to be populated with data. The data used in the simulation
is stored in a set of data files which are specified in the configuration. This data
is then loaded using the `data.load_data_config` method, which has built in validation
procedures to ensure that the loaded data can be mapped onto the grid. Further details
can be found in the [data system](./core/data.md) and [core axes](./core/axes.md)
documentation.

## Configuration of specific modules

The models used for the specific simulation run can be set in the configuration. This
will generally be the four standard modules (`abiotic`, `animals`, `plants` and `soil`),
but it is also useful to have the ability to run novel modules or different combinations
of the modules. Once a list of modules to configure has been extracted from the
configuration, they are then all configured.

## Extracting simulation timing details

The configuration contains a start time, an end time and an time interval for checking
whether modules need to be updated. Once these details are extracted from the
configuration, a check is performed to ensure that the simulation update interval works
suitably with the time steps for individual models, i.e. that no module has a shorter
time step than the overall simulation update interval.

## Saving the initial state

At this point with input data loaded in and all modules configured, the initial model
state (i.e. the contents of the `data` object) can be saved. This is optional, and is
set by a configuration option which defaults to not saving the initial state. The file
path to save this initial state to is also a configuration option.

## Simulating over time

The previously extracted timing details are used to setup a timing loop, which runs from
the start time to the end time with a time step set by the update interval. At each
step a check is performed to determine if any modules need to be updated. Any that do
need to be updated are then updated.

## Saving the final state

After the full simulation loop has been completed the final simulation state can be
saved. Whether to save this state and where to save it to are again configuration
options, but in this case the default is for the final state to be saved.
