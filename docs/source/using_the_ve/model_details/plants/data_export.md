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

The main data structures in the Virtual Ecosystem are stored as [array
variables](../../variables/variables.md) and exported to Zarr or NetCDF formats through
the [core data output
settings](../../core_settings/core_configuration.md#data-output-settings). These
variables have consistent array dimensions throughout the simulation, such as time or
cell ID.

However, the Plants Model is driven primarily by the plant cohort data within the
simulation or by community level data derived from communities of cohorts within
individual cells in the simulation. The number of cohorts varies constantly through the
simulation through recruitment and mortality: there is no consistent dimension for
exporting the data as arrays. Instead, the plant model stores cohort and community data
using the [data frame](https://pandas.pydata.org/docs/user_guide/dsintro.html#dataframe)
model: the data can be arranged as a table with many fields of information and rows can
be added or dropped from the table during the simulation.

The Plants Model therefore provides an additional configurable data exporter that allows
cohort and community data to be exported at each time step. Data are exported to CSV
format files and the data for each time step is appended to the files to generate a
single file containing a time series through a simulation.

There are three kinds of data output available for export from the plants model, written
to separate files in the output directory for a simulation.

* [**Cohort data**](#cohort-data): provides data on the number of individuals within
  each cohort at each timestep, along with the traits, allometry, carbon allocation and
  stoichiometric biomasses of the identical individuals within the cohort. The data are
  written to the file `plants_cohort_data.csv`
* [**Community canopy data**](#community-canopy-data): provides community level summary
  data on the vertically structured canopy within each cell at each time step. The data
  are written to the file `plants_community_canopy_data.csv`.
* [**Stem canopy data**](#stem-canopy-data): provides data on the contribution of
  individual crowns within cohorts to the vertically structured canopy within each cell
  at each time step. Data are written to the file `plants_stem_canopy_data.csv`.

## Configuration settings

Data export is controlled through the `["plants.community_data_export"]` configuration
section, which contains a separate setting for each of the three export data types above.
Each setting accepts a list of attribute names to export for that data type:

* `[]`: the default value of an empty list does not export any attributes.
* `["attribute_a", "attribute_b"]`: the named attributes are exported.
* `"ALL"`: This is a special keyword value that provides a shortcut to exporting all
  available attributes.

The default settings are shown below along with a short description of each setting:

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

rows = ["Field name,Description"]

# Parse the fields from the trait validator pydantic model
for trait, field in PlantsExportConfig.model_fields.items():

    # Tidy the description to remove newlines, convert latex and quote to wrap commas
    desc = "" if field.description is None else field.description
    desc = re.sub(r":math:`\\(.+)`", r"$\\\1$", desc)
    desc = re.sub(r":math:`(.+)`", r"$\1$", desc)
    desc = f'"{desc.replace("\n", " ")}"'

    # Add to the rows
    rows.append(f"`{trait}`,{desc}")

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

## Mandatory fields

Each of the three date types has a set of mandatory fields that provide indices for the
data rows and are always include when other attributes are being exported. You do not
have to add these attributes to the configuration - they will be added automatically -
but you can include them for clarity.

The mandatory fields for cohort (CH), community canopy (CC) and stem canopy (SC) data
are shown below:

```{csv-table}
:header-rows: 1

Field,Description, CH, CC, SC
`cohort_id`,"A unique ID code for the cohort that persists through the time
    series.", *, , *
`cell_id`,"The grid cell in which the cohort is found.", *, *, *
`time`,"The time stamp of the simulation step for the exported data.", *, *, *
`time_index`,"The index along the time axis for the exported data.", *, *, *
`canopy_layer_index`,"The index of canopy layers in the vertical axis of the
    simulation", , *, *
`heights`,"The closure height of canopy layers in the simulation [m]", , *, *
```

## Cohort data

The simulation provides a set of cohort-level attributes that fall into the following groups:

* Mandatory fields that are always exported when cohort data is requested. These are:
  `cohort_id`, `cell_id`, `time` and  `time_index`.
* The core cohort details - how many individuals of which PFT are in a cell at this
  timestep.
* The PFT trait data for the cohort.
* Predictions from the T Model for the cohort, which can be broken down into three
  subgroups:
  * The stem allometry of the cohort, predicted from individual size (diameter at breast
    height, metres) following the T Model.
  * The GPP and Carbon allocation for the cohort in the time step, where the GPP is
    predicted using the P Model and allocation follows the T Model.
  * The predicted growth increments for individuals in the cohort, following the T
    Model.
* The realised biomasses of carbon, nitrogen and phosphorous for the plants tissues in
  each individual. These biomasses can depart from the theoretical allometry under the T
  Model due to ecological process like herbivory.

### Core cohort details

The table below shows the core cohort attributes.

```{csv-table}
:header-rows: 1

Field,Description
`pft_name`,"The plant functional type of the cohort: a text value that must match one
 of the PFT names set in the PFT definitions."
`n_individuals`,"The current number of individuals in the cohort."
```

### Plant functional type trait data

These attribute field names and descriptions are identical to the fields reported in the
[definition of PFTs](./tree_definition.md#plant-functional-types) used in the model.

```{note}
These fields mostly duplicate values from the PFT definitions to make it easier to make
calculations across cohorts. You may want to exclude them to reduce file sizes and then
simply use the PFT name for each cohort to merge the PFT definitions back onto the
cohort level data.

There are two exceptions: the `lai` and  `tau_f` values change within the simulation
to capture herbivory effects on light capture and carbon allocation for individuals
within cohorts. The field definitions do not change from the input trait data but `lai`
is decreased by herbivory and `tau_f` increases to capture the additional turnover and
carbon costs of herbivory.
```

### Allometry, allocation and growth attributes

The table below shows the allometry, carbon allocation and growth increment fields
available for export.

:::{note}

The tissue masses in the table below are _theoretical_ predictions of the values from
the allometry of the T Model. Herbivory can reduce the [realised
biomasses](#realised-tissue-biomasses) of some tissues. At present, the Virtual
Ecosystem only tracks mass loss from folivory.
:::

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
        if (attr in cls._array_attrs) and (attr != "cohort_id"):
            tmodel_options.append(f'`{attr}`,"{desc}"')


# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(tmodel_options)}\n```",
    raw=True,
)
```

### Realised tissue biomasses

The Plants model records the elemental masses in each of the tissues of individuals
within cohorts, along with any surplus elemental masses that accumulate when tissues
have reached their ideal stoichiometric ratios.

The fields below lists the exportable attributes giving the elemental biomasses for the
tissues in individuals within each cohort. These are _realised_ tissue masses,
accounting for herbivory and so the carbon masses can differ from the allometric
predictions of tissue carbon mass under the T Model that are described in the previous
section.

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
from virtual_ecosystem.models.plants.biomasses import PLANT_BIOMASS_TISSUES

biomass_options = ["Field,Description"]

for tissue in PLANT_BIOMASS_TISSUES:
    for element in ["C", *tissue.elements]:
        biomass_options.append(
            f"`{tissue.tissue_name}_{element.lower()}_biomass`,"
            f"Mass of {element} in {tissue.tissue_name} tissue (kg{{{element}}})"
        )


for element in ["C", *tissue.elements]:
    biomass_options.append(
        f"`surplus_{element.lower()}_biomass`,"
        f"Mass of {element} in surplus pool for individuals (kg{{{element}}})"
    )


# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(biomass_options)}\n```",
    raw=True,
)
```

## Community canopy data

The community canopy data provides details of the whole community canopy properties.
This includes the canopy layer closure heights under the perfect plasticity
approximation and the modelled light environment through the canopy.

In addition to the traits below, the mandatory fields for community canopy data are:
`cell_id`, `time`, `time_index`, `canopy_layer_index` and `heights`.

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

The stem canopy data provide details of how individual stems within each cohort contribute
to the overall canopy of the plant community. In addition to the traits below, the
mandatory fields for stem canopy data are: `cohort_id`, `cell_id`, `time`, `time_index`,
`canopy_layer_index` and `heights`.

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
