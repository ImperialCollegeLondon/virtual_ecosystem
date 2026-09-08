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
language_info:
  name: python
  version: 3.13.1
  mimetype: text/x-python
  codemirror_mode:
    name: ipython
    version: 3
  pygments_lexer: ipython3
  nbconvert_exporter: python
  file_extension: .py
---

# Plants model data export

Much of the data in the Plants Model is stored at the level of the individual cohorts
that form the tree communities present in different cells. The number of cohorts changes
constantly through the simulation through recruitment and mortality and consist of
many fields of information about each cohort. The cohort data are stored within the
model in [data frame](https://pandas.pydata.org/docs/user_guide/dsintro.html#dataframe)
formats and, because these data frames do not have consistent unchanging dimensions, are
not stored or exported using the same system as the [array
variables](../../variables/variables.md) used elsewhere in the model.

Instead, the Plants Model provides a configurable exporter options that allow cohort and
community data to be exported at each time step. Data are exported to CSV format files
and the data for each time step is appended to the files to generate a single file
containing a time series through a simulation.

This page describes the configuration and available options and variables.

## Configuration settings

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

config_object = PlantsExportConfig()
dump_config_toml("plants.community_data_export", config_object)


model_config_to_deflist("plants.community_data_export", config_object)
```

## Cohort data

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
# This cell autogenerates a configuration for the model from the code objects, which
# keeps these docs up to date with the code state. Note that that highlighting
# (emphasize-lines) settings in the TOML output will not automatically adjust if the
# configuration changes

import json

import tomli_w
from IPython.display import display_markdown

from virtual_ecosystem.core.model_config import DataSource
from virtual_ecosystem.models.plants.model_config import PlantsConfiguration
from virtual_ecosystem.models.plants.plants_model import PlantsModel

# Generate a default plant configuration, using model_construct() to bypass validation
# on placeholder file names
plants_cfg = json.loads(
    PlantsConfiguration.model_construct(
        pft_definitions_path="/path/to/pft_definitions.csv",
        cohort_data_path="/path/to/cohort_data.csv",
    ).model_dump_json()
)

# Build complete set of config including data variables
cfg = {"core": {"variable": []}, "plants": plants_cfg}

for var in PlantsModel.vars_required_for_init:
    cfg["core"]["variable"].append(
        json.loads(
            DataSource.model_construct(
                file_path="/path/to/plant_data.nc", var_name=var
            ).model_dump_json()
        )
    )

# Display as markdown
display_markdown(
    "```{code-block} toml\n:emphasize-lines: 3-6,11-12\n\n"
    + tomli_w.dumps(cfg)
    + "```",
    raw=True,
)
```

## Plants constants

The plant constants section shown in the configuration above sets a large number of
constants that drive how the simulation works. These are described below:

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
# This cell generates a CSV table from the pydantic validation object for PFT data,
# ensuring that the description here is up to date with the codebase.

from virtual_ecosystem.models.plants.model_config import PlantsConstants
import re

rows = ["Field name,Description,Default value"]

# Parse the fields from the trait validator pydantic model
for trait, field in PlantsConstants.model_fields.items():

    # Tidy the description to remove newlines, convert latex and quote to wrap commas
    desc = "" if field.description is None else field.description
    desc = re.sub(r":math:`\\(.+)`", r"$\\\1$", desc)
    desc = re.sub(r":math:`(.+)`", r"$\1$", desc)
    desc = f'"{desc.replace("\n", " ")}"'

    # Add to the rows
    rows.append(f"`{trait}`,{desc},{ '-' if field.default is None else field.default}")


# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(rows)}\n```",
    raw=True,
)
```

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

### Realised tissue biomasses

```{code-cell} ipython3
from virtual_ecosystem.models.plants.plants_model import PLANT_BIOMASS_TISSUES

biomass_options = ["Field,Description"]

for tissue in PLANT_BIOMASS_TISSUES:
    for element in ["C", *tissue.elements]:
        biomass_options.append(
            f"`{tissue.tissue_name}_{element.lower()}_biomass`,"
            f"Mass of {element} in {tissue.tissue_name} tissue (kg{{{element}}})"
        )

# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(biomass_options)}\n```",
    raw=True,
)
```

```{code-cell} ipython3
from virtual_ecosystem.core.docutils import get_init_attr_docs
from pyrealm.demography.tmodel import StemAllometry, StemAllocation, GrowthIncrements

tmodel_options = ["Field,Description"]

for cls in (StemAllometry, StemAllocation, GrowthIncrements):
    for attr, desc in get_init_attr_docs(cls.__init__).items():
        if attr in cls._array_attrs:
            tmodel_options.append(f'`{attr}`,"{desc}"')


# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(tmodel_options)}\n```",
    raw=True,
)
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

To show the configuration of the exporter in use, the TOML settings below show how to
configure the exporter to write out selected trait data for all three data files:

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
