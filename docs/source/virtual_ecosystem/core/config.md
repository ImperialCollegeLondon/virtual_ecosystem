# The configuration module

This module is used to configure a `virtual_ecosystem` simulation run. This module
reads in a set of configuration files written using `toml`. It is setup in such a way as
to allow a reduced set of modules to be configured (e.g. just `plants` and `soil`), and
to allow specific module implementations to be configured (e.g. `plants_with_hydro`
instead of `plants`). The resulting combined model configuration is validated against a
set of [`JSON Schema`](https://json-schema.org). If this passes, a combined output file is
saved as a permanent record of the model configuration. This configuration is also saved
as a dictionary accessible to other modules and scripts.

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
configuration files to be re-used in a modular way, allowing a library of configuration
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
[abiotic_simple]
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

## JSON schema

The contents of the config files are validated using [`JSON
Schema`](https://json-schema.org), this is performed using the `python` package
[`jsonschema`](https://pypi.org/project/jsonschema/). We use these schema to validate
the most basic properties of the input data (e.g. that the path to a file is a string),
with more complex validation being left to downstream functions. We check for missing
expected tags, unexpected tags, that tags are of the correct type, and where relevant
that input values are strictly positive. Additionally, we use these schema to populate
default values when tags are not provided. The schema is saved a `JSON` file, which
follows the pattern below:

```json
{
   "type": "object",
   "properties": {
      "core": {
         "description": "Configuration settings for the core module",
         "type": "object",
         "properties": {
            "grid": {
               "description": "Details of the grid to configure",
               "type": "object",
               "properties": {
                  "nx": {
                     "description": "Number of grid cells in x direction",
                     "type": "integer",
                     "exclusiveMinimum": 0,
                     "default": 100
                  },
                  "ny": {
                     "description": "Number of grid cells in y direction",
                     "type": "integer",
                     "exclusiveMinimum": 0,
                     "default": 100
                  }
               },
               "default": {},
               "required": [
                  "nx",
                  "ny"
               ]
            }
         },
         "default": {},
         "required": [
            "grid",
         ]
      }
   },
   "required": [
      "core"
   ]
}
```

The type of every single tag should be specified, with `object` as the type for tags
that are containers for more nested tags (i.e. `core`). In cases where strictly
positive values are required this is achieved by setting `exclusiveMinimum` to zero. For
each `object`, the `required` key specifies the tags that must be included for
validation to pass.

We do not permit configuration tags that are not included within a schema, therefore the
config module automatically sets `additionalProperties` as `false` for every object in
the schema. The `default` key is used to specify the default value that should be
inserted if the tag in question is not provided for the user. The default value for all
objects should be set as `{}` to ensure that nested defaults can be found and populated.
In general, we use default keys to specify relatively simple defaults (e.g. lists or
single values), more complex defaults (e.g. tables of plant functional types, climate
time series) are not currently supported. The individual module schema are saved as
`JSON` files within their respective module folders, then loaded by the module
`__init__.py` scripts and written to the schema registry using a decorator. The config
module extracts the relevant schema from the registry and combines them into a single
schema in order to carry out final validation. If any of these schema are incorrectly
formatted the configuration process will critically fail.

## Final output

In addition to saving the configuration as an output file, it is also returned so that
downstream functions can make use of it. This is as a simple nested dictionary.
