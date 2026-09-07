---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Plants model configuration

[See also the [configuration details](../../../api/models/plants/model_config.md)]

Configuration for the `plants` model includes four sections:

* A path to a CSV file defining the plant functional types to be used in the model
  (`[plants.pft_definitions_path]`)
* A path to another CSV file defining the size-structured communities of plant
  functional types found in each cell (`[plants.cohort_data_path]`).
* Configuration details for the export of plant community data at each time step
  (`[plants.community_data_export]`).
* A set of constants values used within the model (`[plants.constants]`) that need to be
  specified in the configuration if you want to change them from the default values.

## Plant functional types

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.plants.functional_types import VEFloraValidator

traits = list(VEFloraValidator.model_fields.keys())

# Remove internally assigned values
for calc_trait in ["lai_base", "tau_f_base"]:
    traits.remove(calc_trait)

glue("pft_traits", ", ".join([f'"{t}"' for t in traits]))
```

The `plants.pft_definitions_path` configuration setting must point to a CSV defining
the plant functional types to be used in a simulation. Each row in the CSV must provide
a unique PFT name and then a set of plant functional trait values for that PFT. The file
in the example data is a good template to use for preparing this file. The required
trait fields are:

{glue:text}`pft_traits`.

## Plant cohort data

The `plants.cohort_data_path` configuration setting must point to a CSV file defining
the cohorts in each cell. Again, the file in the example data is a good template but the
basic structure is that each row must provide size-structured cohort data as:

* the name of a PFT,
* a cell ID value,
* the size of the individuals in the cohort as diameter at breast height, and
* the number of individuals in the cohort.

## Plants community data export

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

## Plants constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.plants.model_config import PlantsConstants

config_object = PlantsConstants()
dump_config_toml("plants.constants", config_object)
model_config_to_deflist("plants.constants", config_object)
```
