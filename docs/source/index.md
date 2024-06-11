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

# Welcome to the Virtual Ecosystem

This repository is the home for the development of the Virtual Ecosystem. The Virtual
Ecosystem is a project to develop a simulation of all of the major processes involved
in a real ecosystem including the:

- growth and demographic processes of the primary producers within the forest,
- microclimatic processes within and around the ecosystem,
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
- Olivia Daniel
- Dr. Jaideep Joshi
- Dr. David Orme
- Dr. Vivienne Groner
- Dr. Jacob Cook
- Dr. Taran Rallings

The research team are supported by the Imperial College London
[Research Software Engineering](https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/research-software-engineering/)
team.

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: The Virtual Ecosystem

  virtual_ecosystem/module_overview.md
  virtual_ecosystem/getting_started.md
  virtual_ecosystem/virtual_ecosystem_in_use.md
  virtual_ecosystem/example_data.md
  virtual_ecosystem/main_simulation.md
  virtual_ecosystem/constants.md
  virtual_ecosystem/variables.md
  virtual_ecosystem/soil/soil_details.md
  virtual_ecosystem/core/grid.md
  virtual_ecosystem/core/data.md
  virtual_ecosystem/core/axes.md
  virtual_ecosystem/core/config.md
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: API reference

  Main <api/main.md>
  Example data <api/example_data.md>
  Core Overview <api/core.md>
  Configuration <api/core/config.md>
  Logger <api/core/logger.md>
  Grid <api/core/grid.md>
  Data <api/core/data.md>
  File readers <api/core/readers.md>
  Core axes <api/core/axes.md>
  Base Model <api/core/base_model.md>
  Core Components <api/core/core_components.md>
  Core Constants <api/core/constants.md>
  Constants Classes <api/core/constants_class.md>
  Constants Loader <api/core/constants_loader.md>
  Schema <api/core/schema.md>
  Module Registry <api/core/registry.md>
  Utility functions <api/core/utils.md>
  Variables <api/core/variables.md>
  Custom exceptions <api/core/exceptions.md>
  Soil Overview <api/soil.md>
  Soil Model <api/soil/soil_model.md>
  Soil Carbon <api/soil/carbon.md>
  Soil Environmental Factors <api/soil/env_factors.md>
  Soil Constants <api/soil/constants.md>
  Abiotic Simple Overview <api/abiotic_simple.md>
  Abiotic Simple Model <api/abiotic_simple/abiotic_simple_model.md>
  Abiotic Simple Microclimate <api/abiotic_simple/microclimate.md>
  Abiotic Simple Constants <api/abiotic_simple/abiotic_simple_constants.md>
  Abiotic Mechanistic Overview <api/abiotic.md>
  Abiotic Mechanistic Model <api/abiotic/abiotic_model.md>
  Abiotic Mechanistic Constants <api/abiotic/abiotic_constants.md>
  Abiotic Mechanistic Tools <api/abiotic/abiotic_tools.md>
  Abiotic Mechanistic Wind <api/abiotic/wind.md>
  Abiotic Mechanistic Energy Balance <api/abiotic/energy_balance.md>
  Abiotic Mechanistic Soil Energy Balance <api/abiotic/soil_energy_balance.md>
  Abiotic Mechanistic Conductivities <api/abiotic/conductivities.md>
  Hydrology Overview <api/hydrology.md>
  Hydrology Model <api/hydrology/hydrology_model.md>
  Hydrology Above-ground <api/hydrology/above_ground.md>
  Hydrology Below-ground <api/hydrology/below_ground.md>
  Hydrology Constants <api/hydrology/constants.md>
  Animal Overview <api/animal>
  Animal Model <api/animal/animal_model.md> 
  Animal Communities <api/animal/animal_communities.md> 
  Animal Protocols <api/animal/protocols.md>
  Animal Cohorts <api/animal/animal_cohorts.md> 
  Animal Functional Groups <api/animal/functional_group.md> 
  Animal Traits <api/animal/animal_traits.md>
  Animal Scaling Functions <api/animal/scaling_functions.md> 
  Animal Constants <api/animal/constants.md> 
  Animal Decay <api/animal/decay.md> 
  Animal Plant Resources <api/animal/plant_resources.md> 
  Litter Overview <api/litter.md>
  Litter Model <api/litter/litter_model.md>
  Litter Pools <api/litter/litter_pools.md>
  Litter Constants <api/litter/constants.md>
  Plants Model <api/plants/plants_model.md>
  Plants Structures <api/plants/plant_structures.md>
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: Command line tools

  command_line_tools/ve_run.md
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
  Package Releases <development/package_releases.md>
```

```{eval-rst}
.. toctree::
  :maxdepth: 4
  :caption: Climate data resources

  Overview climate data <data_recipes/climate_data_recipes.md>
  Copernicus climate data store <data_recipes/CDS_toolbox_template.md>
```

```{eval-rst}
.. toctree::
  :maxdepth: 0
  :caption: Bibliography

  bibliography.md
```
