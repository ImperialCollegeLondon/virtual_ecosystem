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
      jupytext_version: 1.19.2
---

# The animal model

Animals in the Virtual Ecosystem are represented by the [`animal`
model](./animal_config.md).

## Preparing the input data for the animal model

The primary data you need to provide to the animal model will be a [description of the
functional groups](./functional_group_data.md) found in your study area. This is
provided as a CSV file.

The `animal` model makes very limited use of array data, with required
variables primarily being resource pools originating from other models (which should be
provided by those models) You can check the required variables using the [variables
table](../../variables/variables.md).
