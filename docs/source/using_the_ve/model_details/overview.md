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

# Model specific setup details

This section contains the details you need to know to setup specific models. Rather than
providing separate sections for every single model we group them by type, as a large
amount of the setup process will be shared. The four types of models are as follows

* The [abiotic environment models](./abiotic/overview.md) (`abiotic`, `abiotic_simple`
  and `hydrology`)
* The animal model
* The plants model
* The decay models (`litter` and `soil`)

There's still a large amount of loose content that needs to be integrated with the above
structure. It consists of:

* A page containing an [explanation of how to configure plant functional
  types](./pft_configuration.md).
* A page giving a [model by model breakdown of the configuration
  options](./science_model_configuration.md), including default values for constants.
