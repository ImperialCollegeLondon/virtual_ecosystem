---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.6
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
- **Plants remain static**, meaning no water uptake or transpiration, and constant
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

There are two
possible options to setup such an experiment depending on the data you have available.
The examples below illustrate the two approaches at the example of doubling rainfall
and changing initial soil moisture on topsoil moisture.

### Option 1: Starting fresh (Default Approach)

Use this if you have all required input data but do not yet know what the output
variables will be. The model initializes as in a fully active setup, running one update
to populate all variables. After the first update, all components except hydrology
remain static.

To set one or more models to static:

1. Navigate to the `/ve_example/out/` folder.
2. Copy the `vr_full_model_configuration.toml` file and rename to
  `static_model_config.toml`.
3. Set the status flags to `static = true`, for example:

    ```toml
    [abiotic_simple]
    static=true
    ```

4. Make further changes to your configuration for your experiment (e.g. change input
   data, process implementation, or parameters). Here we change the rainfall input file
   (TODO):

```toml
    [[core.data.variable]]
      file = "/private/tmp/ve_example/data/double_rainfall.nc"
      var_name = "precipitation"
   ```

5. Ensure that you update the output directory and verify all paths.

### Option 2: Starting from a previous run

Use this if you have a previous model output file and want to continue from a known
state. The model loads output data to populate all variables, ensuring a defined
starting condition. Static components remain unchanged, while hydrology continues
updating.

To set one or more models to static **AND** start from previous run:

1. Navigate to the `/ve_example/out/` folder.
2. Copy the `vr_full_model_configuration.toml` file and rename to
  `static_model_config.toml`.
3. Set the status flags to `static = true`, for example:

    ```toml
    [abiotic_simple]
    static=true
    ```

4. Copy, rename and move the `final_state.nc` file, for example to `restart_state.nc` in
   `/ve_example/data/`. Define paths to load all Virtual Ecosystem variables from the
   new file, for example:

   ```toml
   [[core.data.variable]]
    file = "/private/tmp/ve_example/data/restart_state.nc"
    var_name = "root_turnover_c_p_ratio"
   ```

5. Make further changes to your configuration for your experiment. Here, we modify the
  initial soil moisture values (default 0.5):

  ```toml
    [hydrology]
    initial_soil_moisture = 0.3
    initial_groundwater_saturation = 0.9
    static = false
  ```

6. Ensure that you update the output directory and verify all paths.

## Running the static models

To run the static model use the following command, making sure that it points to your
updated configuration file:

  ```sh
    ve_run /path/ve_example/out/static_model_config.toml \
      --outpath /path/ve_example/out \
      --logfile /path/ve_example/out/ve_example.log
  ```
  
TODO check that this works, add both examples?

## Compare results

TODO To compare the results of the different experiments, load the input files and plot
the variable of interest, for example soil moisture of the top soil layer.

TODO load baseline static, change in precip, change in initial soil moisture; plot maps
or time series