---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
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

# Model data inputs

## Other data inputs

Some initial model data does not use the main data loading system. This is typically
where the data does not map neatly onto one of the core axes mentioned above. These
data will have specific model configuration settings. For example:

* The plants model requires a set of defined plant functional types (PFTs). This is
  a CSV file defining a set required trait values for each PFT, and the path to this
  file is set in the [plants model configuration
  options](./science_model_configuration.md#plant-functional-types)

* The plant model also requires a defined initial cohort structure, which sets the
  initial cohorts present in each cell. This again is defined as a CSV file with the
  path set in the [plants model configuration
  options](./science_model_configuration.md#plant-cohort-data)

* The animal model also requires a defined initial cohort structure.
