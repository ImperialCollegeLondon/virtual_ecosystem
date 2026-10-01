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

# Model specific setup details

This section contains the details you need to know to setup specific models. Rather than
providing separate sections for every single model we group them by type, as a large
amount of the setup process will be shared. The four types of models are as follows

* The [abiotic environment models](./abiotic/overview.md) (`abiotic`, `abiotic_simple`
  and `hydrology`)
* The [animal model](./animal/overview.md)
* The [plants model](./plants/overview.md)
* The [decay models](./decay/overview.md) (`litter` and `soil`)

## Validation of science model configurations

As with the core configuration, each science model in the Virtual Ecosystem has a
defined set of configuration options that are built into the definition of the model.
Those options will also have specific validation settings that are used to check that
the setting values that you provide are appropriate for the model: these constraints are
automatically enforced when your configuration files are loaded. If configuration data
contains invalid values, then the simulation will exit and the log will contain a
detailed breakdown of any configuration validation issues.

The details of the validation constraints for a particular model configuration are
described in the documentation of the model configuration. The model setup details pages
(provided above) contain links to pages describing the details of these validation
constraints for the model in question - these pages are part of the API (application
programming interface) so are a bit more technical but provide the a complete
description of the model settings.
