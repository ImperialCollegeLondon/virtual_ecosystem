---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.4
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
mystnb:
  render_markdown_format: myst
---

# Modifying a model

Once you have set up a model for your site, you are almost certainly going to want to
modify the initial configuration to explore model behaviour under different conditions.

There are a number of different ways you can do this and we describe some options below.
In general, we strongly advise against creating many copies of configuration files and
altering each set. This is hard to do systematically and creates a lot of file
duplication and it is generally easier to use one of the solutions below to run
alternative models based on the same initial core set of config files.

## Overriding a configuration parameter

The `ve_run` command accepts a `--config` option that can be used to override one or
more of the settings from the configuration file. This makes it fairly easy to have a
single core set of config files and permute a small number of settings.

For example, if you wanted to rerun the model for your site but using a different
maximum soil depth for microbial activity and leaf albedo then you could run:

```bash
ve_run \
  config/data_variables.toml \
  config/soil_config.toml \
  ...
  config/animal_config.toml \
  --config core.constants.microbial_simulation_depth=0.5 \
  --config abiotic.constants.leaf_albedo=0.2
```

The resulting model run will override any values already set in the configuration files
and use `microbial_simulation_depth=0.5` and `leaf_albedo=0.2`.

## Using an alternative configuration file

The approach only works for explicitly named configuration settings and some parts of
the configuration include tables of entries that do not have direct names. One example
are the data variables: there is no configuration entry
`core.data.variables.air_temperature`.

One way to tackle this problem is to swap one of your configuration files. The Virtual
Ecosystem permits modular configuration files for exactly this reason: it allows you to
build up a library of different configuration options, like a menu, that you can combine
to simulate different situations.

For example, if you wanted to run a simulation under different climate change scenarios,
you might create specific TOML files that only contain the climatic variables and then
have two runs:

```bash
ve_run \
  config/non_climatic_data_variables.toml \
  config/rcp_26_climate_variables.toml \
  config/soil_config.toml \
  ...
  config/animal_config.toml \
```

```bash
ve_run \
  config/non_climatic_data_variables.toml \
  config/rcp_45_climate_variables.toml \
  config/soil_config.toml \
  ...
  config/animal_config.toml \
```

## Iterating over many inputs

If you are trying to explore model sensitivity to parameter variation then it is fairly
easy to loop over combinations of configuration settings using `--config`. However, this
doesn't work if you need to iterate over different input data files. For example, if you
have 1000 simulations of climatic patterns from El Niño-Southern Oscillation events then
you might want to change the abiotic conditions to use each one of those input data
files.

### File substitution

One approach that works if the models are running in series or on different computers
(such as on an HPC cluster) is to generate a configuration model that points to a
placeholder data file location and then copy the appropriate real data to that location
before running the file.

For example, your might have a data configuration file
`config/climate_data_variables.toml` that looks like this:

```toml
# Climate data
[[core.data.variable]]
file_path = "simulation_inputs/climate.nc"
var_name = "air_temperature_ref"
[[core.data.variable]]
file_path = "simulation_inputs/climate.nc"
var_name = "relative_humidity_ref"
```

And then you copy the correct file into the climate data location before running the
model:

```bash
cp enso_simulations/enso_0001.nc simulation_inputs/climate.nc

ve_run \
  config/climate_data_variables.toml \
  config/soil_config.toml \
  ...
  config/animal_config.toml \
```

### Dynamic file definition

File substitution does not work well if you are running models in parallel on the same
system: the shared location can only point to one file at a time. An alternative
approach is to set a **path marker** in the configuration and then provide the file
path when calling `ve_run` using the `--data-paths` (or `-p`) option. The path marker
must be a string starting with a dollar sign - for example'$ENSO_FILE'.

In this approach, your climate configuration file `config/climate_data_variables.toml`
would look like this:

```toml
# Climate data
[[core.data.variable]]
file_path = '$ENSO_FILE'
var_name = "air_temperature_ref"
[[core.data.variable]]
file_path = '$ENSO_FILE'
var_name = "relative_humidity_ref"
```

```{important}
At present, you can only define dynamic values in this way for configuration options
that point to file or directory paths.
```

You can then set the location of `ENSO_FILE` when running the model using the `-p`
option. Note that the dollar sign should not be included when setting the `-p` argument.
You can use multiple `-p` options to provide multiple path markers.

```bash
ve_run \
  config/climate_data_variables.toml \
  config/soil_config.toml \
  ...
  config/animal_config.toml \
  -p ENSO_FILE=enso_simulations/enso_0001.nc
```

## Configuring disturbances

The Virtual Ecosystem defines a set of disturbance models, which can be used to make
repeated alterations to the simulation. For example, the `add_fertiliser` disturbance
increases the concentration of inorganic nitrogen in the relevant soil pools, in order
to mimic the impacts of repeated fertiliser addition in agricultural landscapes.

To setup a disturbance, you need to include it within a configuration file. You then
need to provide any specific configuration settings that the disturbance requires. In
the case of the fertiliser addition disturbance, these are the total amount of inorganic
nitrogen added (per disturbance event) and the fraction of this addition that is nitrate
(rather than ammonium).

The final thing you need to decide is how frequently the disturbance should occur. Each
specific disturbance model will have a default for this, but you are likely to want to
override it for specific use cases. There are two ways of doing this. Firstly, you can
provide a list of specific time steps to run at using the `run_at` option.
Alternatively, the frequency with which the disturbance occurs can be set using
`run_every`. This is also provided as a list of integers, but here the first element is
the timestep for which the disturbance first occurs, the second element is the number of
timesteps between disturbance events, and the third element is the timestep beyond which
the disturbance shouldn't occur. You can choose include only two elements, in which case
the disturbance will keep occurring until the end of the simulation. You can choose to
include only one element, in which case the disturbance will first occur at the timestep
given by this element and then occur for every timestep afterwards until the end of the
simulation.

With all this decided, the complete configuration for a disturbance should look
something like this:

```toml
# Setup fertiliser disturbance
[disturbance.add_fertiliser]
# disturbance starts on the initial timestep, then happens every other time step
# until the 12th timestep
run_every = [0, 2, 12]
inorganic_nitrogen_addition = 5e-3
nitrate_fraction = 0.75
```
