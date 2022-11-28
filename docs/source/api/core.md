---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: vr_python3
  language: python
  name: vr_python3
---

# API reference for `core` modules

The {mod}`~virtual_rainforest.core` module contains the key shared resources and
building blocks used to develop the different component models of the Virtual Rainforest
and then to configure them, populate them with data and provide logging.

Each of the core sub-modules has its own API reference page:

* The {mod}`~virtual_rainforest.core.config` submodule covers the
  definition of formal configuration schema for components and the parsing and
  validation of TOML configuration documents against those schema.
* The {mod}`~virtual_rainforest.core.grid` submodule covers the
  definition of the spatial layout to be used in a simulation and provides an interface
  to the spatial relationships between cells.
* The {mod}`~virtual_rainforest.core.data` submodule provides the
  central data object used to store data required by the simulation and methods to
  populate that data object for use in simulations.
* The {mod}`~virtual_rainforest.core.model` submodule provides an Abstract
  Base Class describing the shared API to be used by science models within the Virtual
  Rainforest.
* The {mod}`~virtual_rainforest.core.logger` configures the {class}`~logging.LOGGER`
  instance used throughout the package.
