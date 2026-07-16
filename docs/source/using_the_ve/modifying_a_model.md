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
