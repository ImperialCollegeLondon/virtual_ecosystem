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

The plants model is configured using a TOML format file that is used to set required
data paths and to alter model settings and constants. It may be helpful to read the
[general overview of the configuration
system](../../running_ve_with_your_own_data.md#configuration-system-overview) before
reading this section. You can also look at the [API documentation of the plants
configuration](../../../api/models/plants/model_config.md): it is aimed at programmers
but does contain useful detail.

## Configuration sections

The configuration for the `plants` model has two sections that are mandatory - these are
simply the settings that point to the required input data to run the model.

* The settings for the array variables required by the model - see the [tree
  configuration](./tree_definition.md) and [subcanopy
  configuration](./subcanopy_definition.md) pages for details. These are configured
  using the `[core.variable]` setting

* Paths to CSV files defining the plant functional types and size-structured cohorts to
  be used in the model. These are configured using the `[plants.pft_definitions_path]`
  and `[plants.cohort_data_path]` settings, and the files and configuration are
  described in more detail in the [tree community configuration
  page](./tree_definition.md).

The remaining sections all have default values and so the model will run if they are
omitted, but you will likely want to change the defaults to values appropriate for your
site or to change cohort and community data output options. These sections are:

* The values of constants used within the model (`[plants.constants]`). These all have
  default values but you will need to provide configuration details if you want to use
  different values. These are described below.

* The configuration of data export options for the plant cohort and communities at
  each time step (`[plants.community_data_export]`). This data are not stored as array
  variables and so are not exported in the main Zarr output file. You will need to
  [configure these export options](./data_export.md) if you want to explore cohort
  dynamics and canopy structure through the simulation.

A complete plant configuration, including all the default fields is shown below. The
mandatory fields are highlighted.

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
