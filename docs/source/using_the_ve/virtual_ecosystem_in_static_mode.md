---
jupytext:
  formats: md:myst
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

## Why Use Static Mode?

The Virtual Ecosystem model integrates multiple interacting components—
**microclimate, plants, animals, soils, and hydrology**. However, these interactions can
obscure cause-effect relationships when analyzing specific processes. The static mode
feature allows freezing selected components while keeping others dynamic, enabling
controlled experiments to examine specific processes.

In this example, we focus on hydrology in isolation by keeping microclimate, vegetation,
animals, and soils static. This allows us to test for example how individual model
parameters influence hydrological processes, and how different rainfall regimes impact
hydrological variables.

### What This Means in Practice

- **Microclimate is fixed** (e.g., temperature and relative humidity do not change).
- **Plants remain static**, meaning constant water uptake, transpiration, and
  interception capacity.
- **No feedbacks from soil microbes or animals on hydrology** are simulated.
- **Only hydrology processes evolve over time** in response to precipitation.

## Setting Up the Static Model

Before proceeding, ensure you have successfully run the example dataset as described in
the [example instructions](./virtual_ecosystem_in_use.md). If not, we recommend
completing that first.

Once the example run is complete, you can start your hydrology-focused experiments.
For example, you can modify the input rainfall, adjust infiltration parameters, or
change how monthly rainfall is distributed over the days of the month. Comparing each
change to the default setup allows you to quantify isolated effects.

In this tutorial, we run two experiments:

- a 'hydrology-only' simulation with default configuration
- a 'hydrology-only' simulation with a modified initial soil moisture

### Experiment 1: Standard 'hydrology-only' simulation

First we need to run the ve_example as a baseline. Once complete, we can set up the
hydrology-only experiment (no changes to parameters or input data):

1. Navigate to the `/ve_example/out/` folder.
2. Copy the `vr_full_model_configuration.toml` file to `/ve_example/config/` and rename
  to `experiment1_config.toml`.
3. Set the status flags to `static = true` for all but the hydrology model, for example:

    ```toml
    [abiotic_simple]
    static=true
    ```

4. Create a new output folder for your experiment, for example
   `/ve_example/experiment1_out/`. This is essential because the Virtual ecosystem
   output files always have the same name and cannot be overwritten; if they
   already exist in your output folder, the model will crash.

#### Run experiment 1

To run the static model use the following command, making sure that it points to your
updated configuration file:

  ```sh
    ve_run /path/ve_example/config/experiment1_config.toml \
      --outpath /path/ve_example/experiment1_out/ \
      --logfile /path/ve_example/experiment1_out/ve_example.log
  ```

#### Compare experiment 1 to default model

To compare the results of the standard hydrology-only vs full dynamic ve_example, load
the results from `/ve_example/out/` and `/ve_example/experiment1_out/`:

``` python
standard_continuous = xarray.load_dataset("/tmp/ve_example/out/all_continuous_data.nc")
hydro_only_continuous = xarray.load_dataset(
    "/tmp/ve_example/experiment1_out/all_continuous_data.nc"
)
```

If you plot a hydrology variable, for example soil moisture of the topsoil
layer over time, you can see ...

```python
plot soil moisture time series both simulations
```

If you plot leaf area index, you see that it does not change in the hydrology_only
experiment.

```python
plot plant area index time series both simulations
```

### Experiment 2: 'hydrology-only' simulation with lower initial soil moisture

To set up a hydrology-only experiment with a change in initial soil moisture, follow
these steps:

1. Navigate to the `/ve_example/out/` folder.
2. Copy the `vr_full_model_configuration.toml` file to `/ve_example/config/` and rename
    to `experiment2_config.toml`.
3. Check the status flags are set to `static = true`, for all but the hydrology model.
4. Make further changes to your configuration for your experiment. Here, we modify the
  initial soil moisture values (default 0.5):

    ```toml
      [hydrology]
      initial_soil_moisture = 0.3
      initial_groundwater_saturation = 0.9
      static = false
    ```

5. Create a new output folder for your experiment, for example
  `/ve_example/experiment2_out/`.

#### Run  experiment 2

To run the static model use the following command, making sure that it points to your
updated configuration file:

  ```sh
    ve_run /path/ve_example/experiment2_out/experiment2_config.toml \
      --outpath /path/ve_example/experiment2_out/ \
      --logfile /path/ve_example/experiment2_out//ve_example.log
  ```

#### Compare results experiment 2

To compare the results of different initial soil moisture levels in the hydrology-only
configuration, load the results from `/ve_example/experiment1_out/` and
`/ve_example/experiment2_out/`:

```python
exp1_continuous = xarray.load_dataset(
  "/tmp/ve_example/experiment1_out/all_continuous_data.nc"
)
exp2_continuous = xarray.load_dataset(
  "/tmp/ve_example/experiment2_out/all_continuous_data.nc"
)
```

Now agian plot the soil moisture over time:

```python
plot time series of soil moisture
```
