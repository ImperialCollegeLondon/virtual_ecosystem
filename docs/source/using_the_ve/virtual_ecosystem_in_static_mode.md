---
execution:
  timeout: 90
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.1
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
  version: 3.10.14
---

# Running the Virtual Ecosystem in Static Mode

## Why use Static Mode?

The Virtual Ecosystem model integrates multiple interacting components—
microclimate, plants, animals, soils, and hydrology. However, these interactions can
obscure cause-effect relationships when analyzing specific processes. The static mode
feature allows freezing selected components while keeping others dynamic, enabling
controlled experiments to examine specific processes.

In this example, we focus on hydrology in isolation by keeping microclimate, vegetation,
animals, and soils static. This allows us to test for example how individual model
parameters influence hydrological processes.

Specifically, we run two experiments and compare the results to the default setup
with all models running dynamically:

- HydroDefault: a 'hydrology-only' simulation with default configuration
- HydroDry: a 'hydrology-only' simulation with a lowered initial soil moisture

In practice this means:

- **Microclimate is fixed** (e.g., temperature and relative humidity do not change).
- **Plants remain static**, meaning constant water uptake, transpiration, and
  interception capacity.
- **No feedbacks from soil microbes or animals on hydrology** are simulated.
- **Only hydrology processes evolve over time** in response to precipitation.

## Using the static mode

### Run ve_example as a baseline

First we need to run the ve_example as a baseline. If you haven't successfully installed
and run the example, please familiarise yourself with the process using the
[example instructions](./virtual_ecosystem_in_use.md).

```{code-cell} ipython3
%%bash
# Remove any existing VE data directory in the /tmp/ directory
if [ -d /tmp/ve_example ]; then
  rm -r /tmp/ve_example
fi
```

```{code-cell} ipython3
%%bash
# Install the example data directory from the Virtual Ecosystem package
ve_run --install-example /tmp/
```

```{code-cell} ipython3
%%bash
# Run the example
ve_run /tmp/ve_example/config \
  --outpath /tmp/ve_example/out/ \
  --logfile /tmp/ve_example/out/ve_example.log
```

### Experiment 1: HydroDefault

#### Set up configuration and directories for HydroDefault

Once the baseline run is complete, you can set up the experiment with default
'hydrology-only' (no changes to parameters or input data):

- Navigate to the `/ve_example/out/` folder.
- Copy the `ve_full_model_configuration.toml` file and rename it, for example to
  `experiment1_config.toml`. We moved this file to a separate folder
  `/ve_example/static_config/`.
- Set the status flags to `static = true` for all but the hydrology model, for example:

  ```toml
  [abiotic_simple]
  static=true
  ```

- Create a new output folder for your experiment, for example
   `/ve_example/experiment1_out/`. This is essential because the Virtual Ecosystem
   output files always have the same name and cannot be overwritten; if they
   already exist in your output folder, the model will crash.

#### Run HydroDefault experiment

To run the static model use the following command, making sure that it points to your
updated configuration file:

```{code-cell} ipython3
%%bash
ve_run /tmp/ve_example/static_config/experiment1_config.toml \
  --outpath /tmp/ve_example/experiment1_out/ \
  --logfile /tmp/ve_example/experiment1_out/experiment1.log
```

#### Compare HydroDefault to fully dynamic ve_example

To compare the results of the HydroDefault experiment to the fully dynamic ve_example,
load the results from `/ve_example/out/` and `/ve_example/experiment1_out/`:

```{code-cell} ipython3
import xarray
import matplotlib.pyplot as plt

# Example: load or define your datasets
ve_example = xarray.load_dataset("/tmp/ve_example/out/all_continuous_data.nc")
experiment1 = xarray.load_dataset(
    "/tmp/ve_example/experiment1_out/all_continuous_data.nc"
)
```

If you plot a hydrology variable, for example the surface runoff, you can see that it
behaves differently in the experiments. This is due to ....

```{code-cell} ipython3
# Choose the variable and cell_id to plot
var_name = "surface_runoff"
cell_to_plot = 25


plt.plot(
    ve_example["time_index"],
    ve_example[var_name].sel(cell_id=cell_to_plot),
    label=f"VE Example",
    linestyle="-",
    color="blue",
)
plt.plot(
    experiment1["time_index"],
    experiment1[var_name].sel(cell_id=cell_to_plot),
    label=f"Experiment 1",
    linestyle="--",
    color="red",
)

plt.xlabel("Time")
plt.ylabel(var_name)
plt.title(f"{var_name} for cell {cell_to_plot}")
plt.legend()
plt.show()
```

Soil moisture reaches the maximum capacity in both scenarios, so there is no difference
between the two:

```{code-cell} ipython3
# Choose the variable and cell_id to plot
var_name = "soil_moisture"
cell_to_plot = 25

# Select the bottom two layers (soil layers)
soil_layers = ve_example.layers[-2:]

# Plot for each of the bottom two layers
for layer in soil_layers.values:
    plt.plot(
        ve_example["time_index"],
        ve_example[var_name].sel(cell_id=cell_to_plot, layers=layer),
        label=f"VE Example - Layer {layer}",
        linestyle="-",
        color="blue",
    )
    plt.plot(
        experiment1["time_index"],
        experiment1[var_name].sel(cell_id=cell_to_plot, layers=layer),
        label=f"Experiment 1 - Layer {layer}",
        linestyle="--",
        color="red",
    )

plt.xlabel("Time")
plt.ylabel(var_name)
plt.title(f"{var_name} for cell {cell_to_plot} (soil layers)")
plt.legend()
plt.show()
```

If you plot air temperature in the top canopy layer, you see that it does not change in
the HydroDefault experiment:

```{code-cell} ipython3
# Choose the variable, cell_id to plot
var_name = "air_temperature"
cell_to_plot = 25

# Select the canopy layers
atmosphere_layers = ve_example.layers[0:1]

# Plot for each of the canopy layers
for layer in atmosphere_layers.values:
    plt.plot(
        ve_example["time_index"],
        ve_example[var_name].sel(cell_id=cell_to_plot, layers=layer),
        label=f"VE Example - Layer {layer}",
        linestyle="-",
        color="blue",
    )
    plt.plot(
        experiment1["time_index"],
        experiment1[var_name].sel(cell_id=cell_to_plot, layers=layer),
        label=f"Experiment 1 - Layer {layer}",
        linestyle="--",
        color="red",
    )

plt.xlabel("Time")
plt.ylabel(var_name)
plt.title(f"{var_name} for cell {cell_to_plot} (canopy layers)")
plt.legend()
plt.show()
```

### Experiment 2: HydroDry

#### Set up configuration and directories for HydroDry experiment

To set up a hydrology-only experiment with a change in initial soil moisture, follow
these steps:

- Navigate to the `/ve_example/out/` folder.
- Copy the `ve_full_model_configuration.toml` file and
  rename to `experiment2_config.toml`. We moved this file to a separate folder
  `/ve_example/static_config/`.
- Check the status flags are set to `static = true`, for all but the hydrology model.
- Make further changes to your configuration for your experiment. Here, we modify the
  initial soil moisture (default 0.5):

```toml
  [hydrology]
  initial_soil_moisture = 0.3
  initial_groundwater_saturation = 0.9
  static = false
```

- Create a new output folder for your experiment, for example
  `/ve_example/experiment2_out/`.

#### Run HydroDry experiment

To run the static model use the following command, making sure that it points to your
updated configuration file and a clear output directory:

```{code-cell} ipython3
%%bash
ve_run /tmp/ve_example/static_config/experiment2_config.toml \
  --outpath /tmp/ve_example/experiment2_out/ \
  --logfile /tmp/ve_example/experiment2_out/experiment2.log
```

#### Compare results experiment 1 and experiment 2

To compare the results of different initial soil moisture levels in the hydrology-only
configuration, load the results from `/ve_example/experiment1_out/` and
`/ve_example/experiment2_out/`:

```{code-cell} ipython3
experiment2 = xarray.load_dataset(
    "/tmp/ve_example/experiment2_out/all_continuous_data.nc"
)
```

Now again plot the soil moisture over time. You see that the lower soil layer reaches
the same level in both experiments after a few time steps. The top soil layer however
reaches a different stable level. This indicates that the initial conditions can be
relevant for the outcome of the overall experiment.

```{code-cell} ipython3
# Choose the variable and cell_id to plot
var_name = "soil_moisture"
cell_to_plot = 25

# Select the bottom two layers (soil layers)
soil_layers = ve_example.layers[-2:]

# Plot for each of the bottom two layers
for layer in soil_layers.values:
    plt.plot(
        experiment1["time_index"],
        experiment1[var_name].sel(cell_id=cell_to_plot, layers=layer),
        label=f"Experiment 1- Layer {layer}",
        linestyle="-",
        color="blue",
    )
    plt.plot(
        experiment2["time_index"],
        experiment2[var_name].sel(cell_id=cell_to_plot, layers=layer),
        label=f"Experiment 2 - Layer {layer}",
        linestyle="--",
        color="red",
    )

plt.xlabel("Time")
plt.ylabel(var_name)
plt.title(f"{var_name} for cell {cell_to_plot} (soil layers)")
plt.legend()
plt.show()
```
