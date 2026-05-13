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

# The plants model

Plant communities in the Virtual Ecosystem are represented by the [`plants`
model](./plants_config.md).

## Preparing the input data for the plants model

You need to provide input data for both the tree communities and the sub-canopy
vegetation to setup the plant model. Each of these follows a different approach.

### Tree communities

To specify tree communities you must define the plant functional types you wish to use,
as well as how they are distributed across the simulation grid. You provide these as two
separate csv files. Further details of what you have to do can be found in [this
extended description of how you configure plant functional types](pft_configuration.md).

### Subcanopy vegetation

The distribution of subcanopy biomass is provided via the array variables (the specific
variables required can be found in the [variables table](../../variables/variables.md)).
The specific properties of this subcanopy vegetation will vary location by location, so
you will **need** to provide parameters for subcanopy vegetation at your site. This is
done by altering the relevant [plant model
constants](./plants_config.md#plants-constants).
