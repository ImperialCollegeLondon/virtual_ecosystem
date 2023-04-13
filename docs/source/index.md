---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Welcome to the Virtual Rainforest

This repository is the home for the development of the Virtual Rainforest. The Virtual
Rainforest is a project to develop a simulation of all of the major processes involved
in a real rainforest including the:

- growth and demographic processes of the primary producers within the forest,
- microclimatic processes within and around the rainforest,
- hydrological processes within the canopy, soil and drainage networks,
- biotic and abiotic processes within the soil, and the
- growth and demography of heterotrophs.

## Project details

This project is funded by a 2021 Distinguished Scientist award from the
[NOMIS Foundation](https://nomisfoundation.ch) to Professor Robert Ewers:

- [NOMIS Award details](https://nomisfoundation.ch/people/robert-ewers/)
- [NOMIS project summary](https://nomisfoundation.ch/research-projects/a-virtual-rainforest-for-understanding-the-stability-resilience-and-sustainability-of-complex-ecosystems/)

```{image} _static/images/logo-nomis-822-by-321.png
:alt: NOMIS logo
:class: bg-primary
:width: 250px
```

The research is based at [Imperial College London](https://imperial.ac.uk):

```{image} _static/images/IMP_ML_1CS_4CP_CLEAR-SPACE.png
:alt: Imperial logo
:class: bg-primary
:width: 250px
```

## Project Team

- Professor Robert Ewers
- Olivia Daniels
- Dr. Jaideep Joshi
- Dr. David Orme
- Dr. Vivienne Groner
- Dr. Jacob Cook
- Taran Rallings

The research team are supported by the Imperial College London
[Research Software Engineering](https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/research-software-engineering/)
team.

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: The Virtual Rainforest

  virtual_rainforest/module_overview.md
  virtual_rainforest/usage.md
  virtual_rainforest/main_simulation.md
  virtual_rainforest/soil/soil_details.md
  virtual_rainforest/core/grid.md
  virtual_rainforest/core/data.md
  virtual_rainforest/core/axes.md
  virtual_rainforest/core/config.md
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: API reference

  Main <api/main.md>
  Core Overview <api/core.md>
  Configuration <api/core/config.md>
  Logger <api/core/logger.md>
  Grid <api/core/grid.md>
  Data <api/core/data.md>
  File readers <api/core/readers.md>
  Core axes <api/core/axes.md>
  Base Model <api/core/base_model.md>
  Utility functions <api/core/utils.md>
  Custom exceptions <api/core/exceptions.md>
  Soil Overview <api/soil.md>
  Soil Model <api/soil/soil_model.md>
  Soil Carbon <api/soil/carbon.md>
  Soil Constants <api/soil/constants.md>
  Abiotic Overview <api/abiotic.md>
  Abiotic Model <api/abiotic/abiotic_model.md>
  Abiotic Tools <api/abiotic/abiotic_tools.md>
  Abiotic Radiation <api/abiotic/radiation.md>
  Abiotic Wind <api/abiotic/wind.md>
  Abiotic Atmospheric CO2 <api/abiotic/atmospheric_co2.md>
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: Command line tools

  command_line_tools/vr_run.md
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: Development

  Strategy <development/code_development_strategy.md>
  Developer Setup <development/developer_setup.md>
  Documentation Overview <development/documentation/overview.md>
  Jupyter Notebooks <development/documentation/jupyter_notebooks.md>
  Docstring Style <development/documentation/docstring_style.md>
  API Generation <development/documentation/api_generation.md>
  Core Design <development/design/core.md>
  Adding New Models <development/defining_new_models.md>
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: Climate data pre-processing
  :hidden:

  Download Copernicus data <data_recipes/CDS_toolbox_template.md>
  Preprocess Copernicus data <data_recipes/ERA5_preprocessing_example.md>
```

```{eval-rst}
.. toctree::
  :maxdepth: 0
  :caption: Bibliography

  bibliography.md
```
