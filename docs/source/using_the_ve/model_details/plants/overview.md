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
      jupytext_version: 1.19.5
---

# The plants model

Plant communities in the Virtual Ecosystem are represented by the `plants` model. Each
cell in the simulation can contain:

* a vertically structured tree community consisting of size structured cohorts of defined
   plant functional types (PFTs), and
* a simple subcanopy (or understory) layer that represents herbaceous biomass underneath
  the main canopy as simple pools of vegetative and reproductive biomass.

<!-- markdownlint-disable MD033 -->
These features are defined using two CSV files that define PFTs and tree cohorts across
cells and a small number of <a
href='../../variables/variables.html?models=plants&roles=vars_required_for_init'>required
initial array variables</a> that set initial PFT propagule counts and subcanopy
biomasses for each cell, along with a time series of the downwelling shortwave radiation
that powers plant growth through time.
<!-- markdownlint-enable MD033 -->

Setting up the model requires you to:

1. [Define the tree communities](./tree_definition.md).
2. [Define initial subcanopy biomasses](./subcanopy_definition.md).
3. [Configure the model](./plants_config.md) to point to the data sources and to
   customise any further model settings.
