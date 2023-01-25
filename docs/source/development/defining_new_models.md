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

# How to add a new model to the Virtual Rainforest

The Virtual Rainforest is designed to be modular, meaning that the set of models to be
used in a particular run is configurable at the start of the simulation. We are starting
out by defining a core set of models (`abiotic`, `animals`, `plants` and `soil`), which
will generally all be included for the vast majority of simulations. In future, it might
be desirable to include models for other aspects of rainforests (e.g. `freshwater`), or
to include multiple modelling approaches for a process. When this happens a new model
should be created. This page will set out the process for adding a new model to the
Virtual Rainforest in a manner that allows it to be used appropriately by the `core`
simulation functionality.

## Define a new `Model` class

You should first start by defining a new folder for your model (within
`virtual_rainforest/models/`).

```bash
mkdir virtual_rainforest/models/freshwater
```

Within this folder a `python` script defining the model should be created.

```bash
touch virtual_rainforest/models/freshwater/model.py
```

This script must import the [`BaseModel` class](../api/core/model.md) as new class must
inherit from this abstract base class.

```{code-block} ipython
from virtual_rainforest.core.model import BaseModel
```
