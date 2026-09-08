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

There are three kinds of data output available for export from the plants model, written
to separate files in the output directory for a simulation.

* [**Cohort data**](#cohort-data): writes data to the file `plants_cohort_data.csv` on
  the cohorts across the simulation, with attributes provided for each cohort at each
  timestep.
* [**Community canopy data**](#community-canopy-data): writes data to the file
  `plants_community_canopy_data.csv`  on the canopy structure within each cell in the
  simulation for each time step, with attributes provided for each community and each
  canopy layer at each timestep.
* [**Stem canopy data**](#stem-canopy-data): writes data to the file
  `plants_stem_canopy_data.csv` data on the individual stem contributions to the
  community canopy, with attributes provided for each cohort in each canopy layer for
  each timestep.

The sections below describe the configuration settings and then the available attributes
for each data type.

## Configuration settings

Data export is controlled through the `["plants.community_data_export"]` configuration
section. In the default configuration shown below, the default settings do not
include any attribute names for any of the three data types and so no data is exported.

```{code-cell} ipython3
:tags: [remove-input]

from IPython.display import display_markdown
import re
from virtual_ecosystem.core.docutils import (
    dump_config_toml,
    get_init_attr_docs,
    get_dataclass_attr_docs,
)
from virtual_ecosystem.models.plants.model_config import PlantsExportConfig

config_object = PlantsExportConfig()
dump_config_toml("plants.community_data_export", config_object)
```

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
# This cell generates a CSV table from the pydantic validation object for the exporter
# ensuring that the description here is up to date with the codebase.

rows = ["Field name,Description,Default value"]

# Parse the fields from the trait validator pydantic model
for trait, field in PlantsExportConfig.model_fields.items():

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

The alternative configuration below exports selected attributes for all three data
types and shows the use of the `"ALL"` keyword as a shortcut for exporting all
attributes for a data type.

```{code-cell} ipython3
:tags: [remove-input]

config_object = PlantsExportConfig(
    cohort_attributes="ALL",
    community_canopy_attributes=["cell_id", "canopy_layer_index", "heights"],
    stem_canopy_attributes=["cell_id", "cohort_id", "canopy_layer_index", "fapar"],
)
dump_config_toml("plants.community_data_export", config_object)
```

## Cohort data

The simulation provides a lot of different cohort-level attributes that fall into the
following main groupings:

* The core cohort details - how many individuals of which PFT are in a cell at this
  timestep.
* The PFT trait data for the cohort.
* The stem allometry of the cohort, predicted from individual size (diameter at breast
  height, metres) following the T Model.
* The GPP and Carbon allocation for the cohort in the time step, where the GPP is
  predicted using the P Model and allocation follows the T Model.
* The predicted growth increments for individuals in the cohort, following the T Model.
* The realised biomasses of carbon, nitrogen and phosphorous for the plants tissues in
  each individual. These biomasses can depart from the theoretical allometry under the T
  Model due to ecological process like herbivory.

### Core cohort details

The table below shows the core cohort attribute. The first four fields are _always_
included in cohort level data even if they are not explicitly included in the cohort
attribute export configuration.

```{csv-table}
:header-rows: 1

Field,Description
`cohort_id`,"A unique ID code for the cohort that persists through the time series."
`cell_id`,"The grid cell in which the cohort is found."
`time`,"The time stamp of the simulation step for the exported data."
`time_index`,"The index along the time axis for the exported data."
`pft_name`,"The plant functional type of the cohort: a text value that must match one
 of the PFT names set in the PFT definitions."
`n_individuals`,"The current number of individuals in the cohort."
```

### Plant functional type trait data

These attribute field names and descriptions are identical to the fields reported in the
[definition of PFTs](./tree_definition.md#plant-functional-types) used in the model.

```{note}
These fields are mostly constant through time: it may be convenient to include them in
the plant data export but you can also exclude them and match cohorts back to the
original PFT input file using the PFT name as a merge key.

An exception is that the `lai` and  `tau_f` fields are altered within the model for
individual cohorts to capture herbivory effects on light capture and carbon allocation.
```

### Allometry and allocation attributes

The table below shows the allometry, carbon allocation and growth increment fields
available for export.

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
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

### Realised tissue biomasses

The fields below show the realised biomass attributes that can be exported.

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
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

## Community canopy data

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
from pyrealm.demography.canopy import CommunityCanopyData

community_canopy_options = ["Field,Description"]

for attr, desc in get_dataclass_attr_docs(CommunityCanopyData).items():
    if attr in CommunityCanopyData._array_attrs:
        community_canopy_options.append(f'`{attr}`,"{desc}"')

# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'"
    f"\n\n{"\n".join(community_canopy_options)}\n```",
    raw=True,
)
```

## Stem canopy data

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
from pyrealm.demography.canopy import CohortCanopyData

cohort_canopy_options = ["Field,Description"]

for attr, desc in get_dataclass_attr_docs(CohortCanopyData).items():
    if attr in CohortCanopyData._array_attrs:
        cohort_canopy_options.append(f'`{attr}`,"{desc}"')

# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\""
    f"'\n\n{"\n".join(cohort_canopy_options)}\n```",
    raw=True,
)
```
