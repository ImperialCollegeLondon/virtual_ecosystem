---
jupyter:
  jupytext:
    cell_metadata_filter: all,-trusted
    main_language: python
    notebook_metadata_filter: settings,mystnb,language_info,execution
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
---

# Running the Virtual Ecosystem for your site

This page is intended to guide you through the process of setting up the Virtual
Ecosystem simulations for your site of interest. Doing this successfully requires large
quantities of both data and effort, far exceeding what could be covered in a single
tutorial. As such, this tutorial aims to cover the general process of changing model
configuration settings and loading in new data. You will then have to read the
documentation for the [core settings](./core_settings/overview.md) and the [model
specific setup details](./model_details/overview.md) in detail to be able to fully setup
your site. Given this complexity, this we strongly recommend that you try [setting up
and running the example simulation](./virtual_ecosystem_in_use.ipynb) before attempting
to setup up the Virtual Ecosystem for a new site.

## Configuration system overview

All the changes you will need to make to setup the Virtual Ecosystem will involve making
changes to the configuration. So, we will start this tutorial with a brief overview
of how the Virtual Ecosystem configuration system is used.

The configuration can be split up over whatever amount of files you wish (though we
would advise against structuring it as one massive hard to read file, or hundreds of
tiny files). All configuration files must be written as [`toml`](https://toml.io/en/).
When the run starts, the configuration inputs are combined and the resulting combined
model configuration is validated. By default, the combined configuration is written out
to a single file to provide a permanent record of the model configuration. In all cases,
your `toml` configuration files only need to specify values that do not have a default
value (typically file paths) or where you want to change a default.

An example of a `toml` configuration is shown below:

```toml
[core]
[core.grid]
cell_nx = 10
cell_ny = 10
```

Here, the first tag indicates the module in question (e.g. `core`), and subsequent tags
indicate (potentially nested) module level configuration details (e.g. horizontal grid
size `cell_nx`).

Note that **configuration setting cannot be repeated between files** as there is no way
to establish which of two values (of e.g. `core.grid.cell_nx`) the user intended to
provide. When settings are repeated, the configuration process will report a critical
error and the simulation will terminate.

### Selecting the models you want to run

The Virtual Ecosystem allows you to choose which set of models you wish to run. You can
choose to run a reduced set of models (e.g. just `plants` and `soil`), though this is
quite tricky as it requires information previously produced by the removed models to be
provided as input data (e.g. herbivory rates which are normally produced by the `animal`
model). More commonly, this functionality will be used to pick between alternative model
implementations (e.g. `abiotic_simple` instead of `abiotic`). The choice of models to be
configured is indicated by including the required model names as top level entries in
the model configuration. Note that the model name is required, even if the configuration
uses all of the default settings. For example, this configuration specifies that four
models are to be used, all with their default settings:

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

## Changing model constants

The majority of constants included in the Virtual Ecosystem are universal and so are not
expected to vary site to site. This means that you **do not** have to provide new values
for them to set up a new site (though you are very welcome to change them if you
disagree with our choices of values). However, some things that we include as
"constants" are in fact site specific (e.g. the deposition rate of inorganic
phosphorus), and you will have to change them for your site setup. To change the value
of constant you need to provide an updated value for it within a configuration file,
under a `[model_name.constants]` tag. This looks like:

```toml
[soil.constants]
phosphorus_deposition_rate = 2.0e-05 # High rate for Amazon Rainforest
```

You **only** need to provide values for constants that you wish to change (i.e. the site
specific ones, and any for which you disagree with our choice of default values). All
constants that you don't provide values for will just use the default value. Details of
all Virtual Ecosystem constants and their default values can be found in the
[configuration options reference
documentation](./model_details/science_model_configuration).

## Further info

TODO - Add a section about changing core configuration (i.e. grid size, location,
simulation time run)

TODO - Add a tutorial step for changing data source, this will probably have the
following subsections

1) Loading data as csv guide (i.e. plant and animal functional data)
2) Loading data as netcdf (i.e. how most data comes in), this needs to involve a simple
   explanation of what the data object is (probably including axes), then this needs to
   be linked to at other appropriate points. This could be a page rather than just a
   section on this page

TODO - The below should be gradually deleted as the tutorial comes together.

Steps which already have pages to make use of:

1. Defining the [configuration of the model core system](./core_configuration.md),
    which establishes the spatial and temporal context of your simulation

1. [Creating any data inputs](./model_data_inputs.md) required by your science models
    and then adding those to your configuration files.

1. [Details of the spatial data axis.](./axes.md) This is unlikely to remain as a page,
   but is useful content to merge into the tutorial
