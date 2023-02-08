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

# API reference for `abiotic` modules

The {mod}`~virtual_rainforest.models.abiotic` module is one of the component models of
the Virtual Rainforest. It is comprised of several submodules that calculate the
radiation balance, the energy balance, the water balance and the atmospheric CO2
balance.

Each of the abiotic sub-modules has its own API reference page:

* The {mod}`~virtual_rainforest.models.abiotic.model` submodule instantiates the
  AbioticModel class which consolidates the functionality of the abiotic module into a
  single class, which the high level functions of the Virtual Rainforest can then use.
