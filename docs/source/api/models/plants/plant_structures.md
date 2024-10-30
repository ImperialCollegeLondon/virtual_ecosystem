---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

# Plant structures for the {mod}`~virtual_ecosystem.models.plants` module

This page documents three submodules of the `plants` module:

1. The plant functional types (PFTs) that make up the flora used in a simulation.
2. The plant community structures, describing the cohorts of stems of different PFTs
   with different diameters at breast height within a grid cell.
3. The canopy structure generated in a grid cell by the plant community.

## The plant {mod}`~virtual_ecosystem.models.plants.functional_types` module

```{eval-rst}
.. automodule:: virtual_ecosystem.models.plants.functional_types
    :autosummary:
    :members:
```

## The plants {mod}`~virtual_ecosystem.models.plants.community` module

```{eval-rst}
.. automodule:: virtual_ecosystem.models.plants.community
    :autosummary:
    :members:
```

## The plants {mod}`~virtual_ecosystem.models.plants.canopy` module

```{eval-rst}
.. automodule:: virtual_ecosystem.models.plants.canopy
    :autosummary:
    :members:
```
