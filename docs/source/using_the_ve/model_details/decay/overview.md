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

# The decay models

The Virtual Ecosystem includes two models that capture the decay of organic matter. The
[`litter` model](./litter_config.md) is a simple model to capture the initial stages of
plant matter decay, and the [`soil` model](./soil_config.md) is a much more complex
model that captures the subsequent stages that occur within the soil. These models are
**not** alternative implementations, so for standard runs of the Virtual Ecosystem you
will need to include **both** models.

## Preparing the input data for the decay models

Input data preparation for the `litter` model is (relatively) straightforward as it only
requires array data (the specific variables required can be found in the [variables
table](../../variables/variables.md)).

The `soil` model also requires a large number of array variables (again consult the
[variables table](../../variables/variables.md)). However, in this case you also need to
provide parametrisation for the [soil microbial
groups](./soil_config.md#soil-microbial-groups) included in the model, as well as the
[enzymes they produce](./soil_config.md#soil-enzyme-classes). These should be provided
in a configuration (`.toml`) file. [We provide baseline estimates for these parameters,
along with comments describing the source of each
estimate.](./default_microbial_params.md)
