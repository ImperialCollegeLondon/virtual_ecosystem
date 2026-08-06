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

# The abiotic environment models

The Virtual Ecosystem includes three different abiotic environmental models. For most
simulations, you will want to include a model of microclimate, the choices are either a
process based model ([`abiotic`](./abiotic_config.md)) or a less
computational intensive model
([`abiotic_simple`](./abiotic_simple_config.md)). You will also generally
want to include a model of hydrological processes, for which
[`hydrology`](./hydrology_config.md) is the only option.

## Preparing the input data for the abiotic models

The first thing you should do before you start preparing your input data is look at the
guides for pre-processing [elevation data](./elevation_data_guide.md) and [climate
data](./climate_data_guide.md).
