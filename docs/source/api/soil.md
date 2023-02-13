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

# API reference for `soil` modules

The {mod}`~virtual_rainforest.models.soil` module is one of the component models of the
Virtual Rainforest. It is comprised of a number of submodules.

Each of the soil sub-modules has its own API reference page:

* The {mod}`~virtual_rainforest.models.soil.model` submodule instantiates the SoilModel
  class which consolidates the functionality of the soil module into a single class,
  which the high level functions of the Virtual Rainforest can then make use of.
* The {mod}`~virtual_rainforest.models.soil.carbon` provides a model for the soil carbon
  cycle.
