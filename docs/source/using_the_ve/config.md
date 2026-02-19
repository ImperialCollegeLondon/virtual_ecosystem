---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
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
---

# The configuration module

This module is used to configure a `virtual_ecosystem` simulation run. This module
reads in a set of configuration files written using `toml`. It is setup in such a way as
to allow a reduced set of modules to be configured (e.g. just `plants` and `soil`), and
to allow specific module implementations to be configured (e.g. `abiotic_simple`
instead of `abiotic`). It deliberately accepts multiple configuration files in order to
allow users to maintain a library of model configuration files that can be used within
multiple different simulations.

When the run starts, the configuration inputs are combined and the resulting combined
model configuration is validated. By default, the combined configuration is written out
to a single file to provide a permanent record of the model configuration. All file
paths within the combined configuration are converted to absolute paths to ensure that
input paths across the initial configurations can be located from within the combined
configuration - this does tie the combined configuration paths to the file system in
which the simulation is run.

::::{dropdown} An example configuration file
:::{literalinclude} ../_static/ve_full_model_configuration.toml
:language: toml
:::
::::

## Configuration files

We decided to use `toml` as our configuration file format because it is: easily human
readable (unlike `JSON`), allows nesting (unlike `ini`), not overly complex (unlike
`yaml`), and is well supported in the `python` ecosystem (unlike
[`strict_yaml`](https://github.com/crdoconnor/strictyaml)). An example of a `toml`
configuration is shown below:

```toml
[core]
[core.grid]
cell_nx = 10
cell_ny = 10
```

Here, the first tag indicates the module in question (e.g. `core`), and subsequent tags
indicate (potentially nested) module level configuration details (e.g. horizontal grid
size `cell_nx`).

The configuration system does not require a single input config file, instead the
configuration can be separated out into a set of config files. This allows different
configuration files to be reused in a modular way, allowing a library of configuration
options to be set up.

When a simulation is run, users can identify a set of specific configuration files or
specific folders containing a set of files that should all be used. This set of files
will be loaded and assembled into a complete configuration. Optionally, the
configuration can include instructions to export the assembled configuration as single
file that provides a useful record of the setup for a particular simulation.

```toml
[core.data_output_options]
save_merged_config = true
output = "/output/directory"
out_merge_file_name = "merged_configuration.toml"
```

Note that **configuration setting cannot be repeated between files** as there is no way
to establish which of two values (of e.g. `core.grid.cell_nx`) the user intended to
provide. When settings are repeated, the configuration process will report a critical
error and the simulation will terminate.

## Optional module loading

The config system allows for different module implementations and combinations to be
configured. The choice of models to be configured is indicated by including the required
model names as top level entries in the model configuration. Note that the model name is
required, even if the configuration uses all of the default settings. For example, this
configuration specifies that four models are to be used, all with their default
settings:

```toml
[core]  # optional
[soil]
[hydrology]
[plants]
[abiotic]
```

The `[core]` element is optional as the Virtual Ecosystem core module is always
required and the default core settings will be used if it is omitted. It can be useful
to include it as a reminder that a particular configuration is intentionally using the
default settings. Each module configuration section can of course be expanded to change
defaults.

```{warning}
Note that there is no guarantee that a particular set of configured models work in
combination. You will need to look at model details to understand which other modules
might be required.
```

## Final output

In addition to saving the configuration as an output file, it is also returned so that
downstream functions can make use of it. This is as a simple nested dictionary.
