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

# The plants model

Plant communities in the Virtual Ecosystem are represented by the [`plants`
model](./plants_config.md).

## Preparing the input data for the plants model

Input data preparation for the `plants` model involves providing some array data (the
specific variables required can be found in the [variables
table](../../variables/variables.md)). It also involves providing details of the plant
functional types, both in terms of their parametrisation and their distribution across
cells. We provide an [extended description of how you configure plant functional
types](pft_configuration.md).
