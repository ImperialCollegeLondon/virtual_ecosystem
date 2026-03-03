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
mystnb:
  render_markdown_format: myst
---

# Science model configuration in the Virtual Ecosystem

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
from virtual_ecosystem.core.configuration import Configuration
from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.core.registry import get_model_configuration_class
from IPython.display import display, Markdown, HTML
from importlib import import_module
```

Each of the science models in the Virtual Ecosystem has its own configuration section.
For some models, the configuration may only consist of a set of model-specific constant
values. In other cases, the science model may require additional configuration details,
such as paths to data files providing configuration data or initialisation values.

```{admonition} Data configuration
:class: important

This page specifically describes the model specific configuration settings. In addition,
you will need to configure the sources of the gridded array data providing the data
variables required by each model:

* The variables required for each model are described in the [model implementation
  pages](../../virtual_ecosystem/implementation/how_it_works.md#science-models).
* A complete list of variables can be found in the [variables description
  page](../variables/variables.md).

```

In all cases, your TOML configuration files only need to specify values that do not have
a default value (typically file paths) or where you want to change a default. To include
a model using only the default values, it is enough just to include the model name as a
header section. So for example:

```{code-block} toml
# This is sufficient to configure the abiotic model with default settings
[abiotic]
```

## Validation of science model configurations

As with the core configuration, each science model in the Virtual Ecosystem has a
defined set of configuration options that are built into the definition of the model.
Those options will also have specific validation settings that are used to check that
the setting values that you provide are appropriate for the model: these constraints are
automatically enforced when your configuration files are loaded. If configuration data
contains invalid values, then the simulation will exit and the log will contain a
detailed breakdown of any configuration validation issues.

The details of the validation constraints for a particular model configuration are
described in the documentation of the model configuration. These are linked in each
section below - these pages are part of the API (application programming interface) so
are a bit more technical but provide the a complete description of the model settings.

## Plants model

[See also the [configuration details](../../api/models/plants/model_config.md)]

Configuration for the `plants` model includes four sections:

* A path to a CSV file defining the plant functional types to be used in the model
  (`[plants.pft_definitions_path]`)
* A path to another CSV file defining the size-structured communities of plant
  functional types found in each cell (`[plants.cohort_data_path]`).
* Configuration details for the export of plant community data at each time step
  (`[plants.community_data_export]`).
* A set of constants values used within the model (`[plants.constants]`) that need to be
  specified in the configuration if you want to change them from the default values.

### Plant functional types

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from pyrealm.demography.flora import Flora
from virtual_ecosystem.models.plants.functional_types import ExtraTraitsPFT

# This is clunky but ok for now.
traits = [*Flora.array_attrs, *ExtraTraitsPFT.array_attrs]

for calc_trait in ["q_m", "z_max_prop"]:
    traits.remove(calc_trait)

glue("pft_traits", ", ".join([f'"{t}"' for t in traits]))
```

The `plants.pft_definitions_path` configuration setting must point to a CSV defining
the plant functional types to be used in a simulation. Each row in the CSV must provide
a unique PFT name and then a set of plant functional trait values for that PFT. The file
in the example data is a good template to use for preparing this file. The required
trait fields are:

{glue:text}`pft_traits`.

### Plant cohort data

The `plants.cohort_data_path` configuration setting must point to a CSV file defining
the cohorts in each cell. Again, the file in the example data is a good template but the
basic structure is that each row must provide size-structured cohort data as:

* the name of a PFT,
* a cell ID value,
* the size of the individuals in the cohort as diameter at breast height, and
* the number of individuals in the cohort.

### Plants community data export

The plants model holds a large amount of detailed data on the plant communities growing
in each cell, on the community-wide canopy structure within each cell and the canopy
properties of individual stems within each cohort. This data is not required by other
science models and so is not shared through the central data store. If you want to look
at plant community data within a simulation, you will need to configure export of plant
community data using the following configuration settings.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

glue(
    "cohort_attributes",
    ", ".join(
        [
            f'"{t}"'
            for t in CommunityDataExporter.available_attributes["cohort_attributes"]
        ]
    ),
)

glue(
    "community_canopy_attributes",
    ", ".join(
        [
            f'"{t}"'
            for t in CommunityDataExporter.available_attributes[
                "community_canopy_attributes"
            ]
        ]
    ),
)

glue(
    "stem_canopy_attributes",
    ", ".join(
        [
            f'"{t}"'
            for t in CommunityDataExporter.available_attributes[
                "stem_canopy_attributes"
            ]
        ]
    ),
)
```

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

config_object = PlantsExportConfig()
dump_config_toml("plants.community_data_export", config_object)
model_config_to_deflist("plants.community_data_export", config_object)
```

There are three possible data files that can be exported - you select one or more by
including them in `[plants.community_data_export.required]` and can then select which
attributes you want exported using the appropriate attributes configuration option.

The choices are:

* If `cohorts` is included in `required_data` then the file `plants_cohorts_data.csv`
  will be exported for each time step. The available attributes for plant cohort data
  are: {glue:text}`cohort_attributes`.

* If `community_canopy` is included in `required_data` then the file
  `plants_community_canopy_data.csv` will be exported for each time step. The available
  attributes for plant cohort data are: {glue:text}`community_canopy_attributes`.

* If `stem_canopy` is included in `required_data` then the file
  `plants_stem_canopy_data.csv` will be exported for each time step. The available
  attributes for plant cohort data are: {glue:text}`stem_canopy_attributes`.

To show the configuration of the exporter in use, the TOML data below configures the
exporter to write out trait data in all three data files:

```{code-cell} ipython3
:tags: [remove-input]

config_object = PlantsExportConfig(
    required_data=["cohorts", "community_canopy", "stem_canopy"],
    cohort_attributes=["cell_id", "cohort_id", "dbh", "delta_dbh", "stem_height"],
    community_canopy_attributes=["cell_id", "canopy_layer_index", "heights"],
    stem_canopy_attributes=["cell_id", "cohort_id", "canopy_layer_index", "fapar"],
)
dump_config_toml("plants.community_data_export", config_object)
```

### Plants constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.plants.model_config import PlantsConstants

config_object = PlantsConstants()
dump_config_toml("plants.constants", config_object)
model_config_to_deflist("plants.constants", config_object)
```

## Animal model

[See also the [configuration details](../../api/models/animal/model_config.md)]

### Animal functional groups

The `animals.functional_group_definitions_path` configuration setting must point to a
CSV defining the animal functional groups to be used in a simulation. Each row in the
CSV must provide a unique group name and then a set of functional trait values for
that group. The file in the example data is a good template to use for preparing this
file. The required trait fields are:

"name", "taxa", "diet", "metabolic_type", "reproductive_environment",
"reproductive_type", "development_type", "development_status",
"offspring_functional_group", "excretion_type", "migration_type",
"vertical_occupancy", "birth_mass", "adult_mass"

### Animal Constants

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for animal constants
.. currentmodule:: virtual_ecosystem.models.animal.model_config
```

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.animal.model_config import AnimalConstants

config_object = AnimalConstants()
dump_config_toml("animal.constants", config_object)
model_config_to_deflist("animal.constants", config_object)
```
