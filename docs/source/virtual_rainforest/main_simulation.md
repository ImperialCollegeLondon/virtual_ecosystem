# Virtual Rainforest simulation flow

This document describes the main simulation flow of the Virtual Rainforest model. The
main stages are:

* setup of the **simulation core** that provides shared resources and functions
* setup of the individual **science models** that simulate the behaviour of different
components of the Virtual Rainforest, and
* iteration of the simulation over the configured timescale.

```{mermaid}
flowchart TD
    A[vr_run] --> B
    B --> F
    C --> F
    D --> F
    D --> G
    E --> F
    H --> H2
    subgraph Core 
    direction LR
    B[Load configuration] --> C[Create grid]
    C --> D[Load data]
    D --> E[Validate timescale]
    end
    subgraph Setup science models
    direction LR
    F[Model configuration] --> G[Model setup]
    G --> H[Model spinup]
    end
    subgraph Simulation
    H2[Save initial state] --> I[Start time]
    I --> J[Update interval]
    J --> K[Update science models]
    K --> L[Save current state]
    L --> J
    L --> M[End time]
    M --> N[Save final state]
    N --> O[Combine continuous data]
    end
```

## Core setup

The first stage in the simulation is the configuration and initialisation of the core
resources and functionality.

### Loading configuration files

First, a set of user-provided configuration files in `TOML` format for a simulation are
loaded. These files are then validated to ensure:

* that they are valid `TOML`,
* and that all the required settings are present and not duplicated.

Some settings will be filled automatically from defaults settings and so can be omitted,
but validation will fail if mandatory settings are omitted. Further details can be found
in the [configuration documentation](./core/config.md).

### Grid creation

Next, the spatial structure of the simulation is configured as a [`Grid`
object](./core/grid.md) that defines the area, coordinate system and geometry of the
individual cells that will be used in the simulation.

### Loading and validation of input data

All of the data required to initialise and run the simulation is then loaded into an
internal [`Data` object](./core/data.md). The model configuration sets the locations of
files containing required variables and this configuration is passed into the
{meth}`~virtual_rainforest.core.data.Data.load_data_config` method, which ensures that:

* the input files are valid and can be read, and
* that the data in files is congruent with the rest of the configuration, such as
  checking the dimensionality and shape of [core axes](./core/axes.md) like the spatial
  grid.

### Simulation timescale

The simulation runs between two dates with an update interval at which each science
model is recalculated. These values are defined in the `core` configuration and are
now validated to ensure that the start date, end date and update interval are sensible.

```{note}
The simulation uses 12 equal length months (30.4375 days) and equal length years (365.25
days), ignoring leap years.
```

## Science models

The Virtual Rainforest is implemented as model objects, each of which is responsible for
simulating a particular aspect of the rainforest ecosystem. The models used for the
specific simulation run can be set in the configuration and will typically include the
four standard models:

* the [`AbioticModel`](../api/abiotic.md) or
  [`AbioticSimpleModel`](../api/abiotic_simple.md),
* the `AnimalModel`,
* the `PlantModel` and the
* [`SoilModel`](../api/soil.md)

but this can be [extended to include new models](../development/defining_new_models.md)
or adopt different combinations of models.

Once a list of models to configure has been extracted from the configuration, all
science models run through a set of steps to prepare for the simulation to start. Each
step is represented using a set of standard model methods that are run in the following
order.

### Model configuration

The loaded configuration should include the configuration details for each individual
science model. These are now used to initialise each requested model using the
{meth}`~virtual_rainforest.core.base_model.BaseModel.from_config` method defined
for each model. This method checks that the configuration is valid for the science
model.

### Model setup

Some models require an additional setup step to calculate values for internal variables
from the initial loaded data or to set up further structures within the model, such as
representations of plant or animal communities. Each model will run the
{meth}`~virtual_rainforest.core.base_model.BaseModel.setup` method defined for the
specific model. In simple science models, this method may not actually need to do
anything.

### Model spinup

Some models may then require a spin up step to allow initial variables to reach an
equilibrium before running the main simulation. Again, each model will run the
{meth}`~virtual_rainforest.core.base_model.BaseModel.spinup` method defined for the
specific model, and again this may not need to do anything for simple models.

### Model update

At this point, the model instance is now ready for simulation. The
{meth}`~virtual_rainforest.core.base_model.BaseModel.update` method for each science
model is run as part of the simulation process described below.

## Simulation process

Now that the simulation core and science models have been configure and initialised,
along with any setup or spinup steps, the simulation itself starts.

### Saving the initial state

The `data` object has now been populated with all of the configured data required to run
the model. The simulation configuration can optionally provide a filepath that will be
used to output a single data file of the initial simulation state.

### Simulation

The science models are now iterated over the configured simulation timescale, running
from the start time to the end time with a time step set by the update interval. At each
step all models are updated. If the simulation has been configured to output continuous
data, the relevant variables will also be saved.

### Saving the final state

After the full simulation loop has been completed, the final simulation state held in
the `Data` object can be optionally be saved to a path provided in the configuration,
defaulting to saving the data.

### Combining continuous data

If the model has been set up to output continuos time data, then there is a final step
to combine the output files into a single file. This step is required as the continuous
data is saved at every time step, resulting in a large number of files. Continuous data
files are found by searching the output folder for files matching the pattern
`"continuous_state*.nc"`. All these files are loaded, combined into a single dataset,
and then deleted. This combined dataset is then saved in the output folder with the file
name `"all_continuous_data.nc"`.

```{warning}
The function to combine the continuous data files reads in **all** files in the
specified output folder that match the pattern `"continuous_state*.nc"`. If a file is
included that matches this pattern but was not generated by the current simulation, the
complete continuous data file will end up either being corrupted or containing incorrect
information. In addition to this, the spurious files will likely be deleted.
```
