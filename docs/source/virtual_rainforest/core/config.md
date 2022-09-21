# The `core.config` module

This module is used to configure a `virtual_rainforest` simulation run. This module
reads in a set of configuration files written using `toml`. It is setup in such a way as
to allow a reduced set of modules to be configured (e.g. just `plants` and `soil`), and
to allow specific module implementations to be configured (e.g. `plants_with_hydro`
instead of `plants`). The resulting combined model configuration is validated against a
set of [JSON schema](https://json-schema.org). If this passes, a combined output file is
saved as a permanent record of the model configuration. This configuration is also saved
as a dictionary accessible to other modules and submodules.

## Configuration files

We decided to use `toml` as our configuration file format because it is: easily human
readable (unlike `JSON`), allows nesting (unlike `ini`), not overly complex (unlike
`yaml`), and is well supported in the `python` ecosystem (unlike
[`strict_yaml`](https://github.com/crdoconnor/strictyaml)). An example of a `toml`
configuration is shown below:

```toml
[config.core]
modules = ["plants"]

[config.core.grid]
nx = 10
ny = 10
```

Here, the first tag indicates that this is a config file, the second the module in
question (e.g. `core`), and subsequent tags indicate (potentially nested) module level
configuration details (e.g. horizontal grid size `nx`).

The configuration system does not require a single input config file, instead the config
input can be spread across an arbitrarily large number of config files. However,
information cannot be repeated between files as there is no way to establish which of
two values (of e.g. `config.core.grid.nx`) the user intended to provide. In this case,
the module will throw critical error and the `virtual_rainforest` model will not
configure. Config files are read from a folder that the user specifies, this can either
be every `toml` file in the folder, or a user provided list of files. If a file exists
in this folder that has the same name as the user provided output file name the
configuration will critically fail, in order to minimise the chance of significant
confusion downstream.

## Optional module loading

The config system allows for different module implementations and combinations to be
configured. While the `core` module must always be configured, all other modules are
optional. The list of modules to be configured must always included as
`config.core.modules`. Failure to include this, or the inclusion of repeated module
names will cause configuration to critically fail.

## JSON schema

WITH EXAMPLE, where are they defined, schema registry, BADLY FORMATTED JSON SCHEMA

## Final output

DESCRIBE COMPLETE_CONFIG object, also mention possible extension
