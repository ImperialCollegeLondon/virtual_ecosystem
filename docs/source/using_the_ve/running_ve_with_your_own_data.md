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

TODO - Add a section about changing model constants (phosphorus deposition is a good
example)

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

1. [Configuring the science models](./science_model_configuration.md) that you want
    to include in your simulation.

1. [Creating any data inputs](./model_data_inputs.md) required by your science models
    and then adding those to your configuration files.

1. [Details of the spatial data axis.](./axes.md) This is unlikely to remain as a page,
   but is useful content to merge into the tutorial

1. [Explanation of how to use the configuration system.](./config.md) This is unlikely
   to remain as a page, but is useful content to merge into the tutorial
