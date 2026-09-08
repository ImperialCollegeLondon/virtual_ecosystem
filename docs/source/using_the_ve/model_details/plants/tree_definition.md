---
jupytext:
  formats: md:myst
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

# Defining tree communities

There are three steps to setting up tree communities in the Plants model. You will need
to define:

1. The plant functional types (PFTs) to be used in the model.
1. The size-structured cohorts of those PFTs growing in the cells of the simulation.
1. The initial distribution of propagules of the PFTs across cells.

## Plant functional types

Plant functional types in the plants model are defined by a set of trait values that
describe the allometry, carbon allocation, demography and stoichiometry of each PFT.

The PFT definitions for a simulation need to be stored in a
CSV file: each PFT must have a unique name and each row then provides the trait values
for that PFT. For example, the file below defines two plant functional types:
`broadleaf` and `shrub`.

````{dropdown} pft_definitions.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/plant_pfts.csv
```
`````

The [configuration of the plants model](./plants_config.md) must then provide the
`pft_definitions_path` setting that gives the path to that CSV file:

```toml
[plants]
pft_definitions_path = '/path/to/pft_definitions.csv'
```

Many of the traits required for each PFT are used to define the allometry of growing
trees, the vertical structure of the canopy and the estimation of growth from gross
primary productivity, using the implementation of the T Model {cite:p}`li_tmodel_2014`
in the [`pyrealm`
package](https://pyrealm.readthedocs.io/en/stable/users/demography/flora.html#plant-traits).
The Virtual Ecosystem extends the set of traits used in `pyrealm` to add traits to
define stoichiometric ratios, lignin concentrations, fruiting behaviour and other
extended aspects of tree demography.

The PFT definitions file needs to include the following fields (the order doesn't
matter) defining the PFT names and then values for all of the traits:

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
# This cell generates a CSV table from the pydantic validation object for PFT data,
# ensuring that the description here is up to date with the codebase.

from IPython.display import display_markdown

from virtual_ecosystem.models.plants.functional_types import VEFloraValidator
import re

rows = ["Field name,Description,Default value"]

# Parse the fields from the trait validator pydantic model
for trait, field in VEFloraValidator.model_fields.items():

    # Skip reference variables lai_base and tau_f_base, which may disappear.
    if trait.endswith("_base"):
        continue

    # Tidy the description to remove newlines, convert latex and quote to wrap commas
    desc = "" if field.description is None else field.description
    desc = re.sub(r":math:`\\(.+)`", r"$\\\1$", desc)
    desc = re.sub(r":math:`(.+)`", r"$\1$", desc)
    desc = f'"{desc.replace("\n", " ")}"'

    # Add to the rows
    rows.append(
        f"`{trait}`,{desc},{ '-' if field.default is None else field.default[0]}"
    )

# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(rows)}\n```",
    raw=True,
)
```

## Initial cohort data

The plants model then needs an initial distribution of size-structured cohorts across
the cells within the simulation. This is defined using a CSV file, where each row
represents a size-structured cohort of a given PFT growing in one of the simulation
cells. An example file looks like this:

````{dropdown} cohort_data.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/example_plant_cohorts.csv
```
````

Again, the [configuration of the plants model](./plants_config.md) then must provide a
`cohort_data_path` setting giving the location of the cohort data.

```toml
[plants]
cohort_data_path = '/path/to/cohort_data.csv'
```

The fields in the cohort data file are:

```{csv-table}
:header-rows: 1

field,description
`plant_cohorts_pft`,"The plant functional type of the cohort: a text value that must
match one of the PFT names set in the PFT definitions."
`plant_cohorts_cell_id`, "The grid cell in which the cohort is found."
`plant_cohorts_dbh`, "The initial size of each individual in the cohort, as the diameter
at breast height (metres)."
`plant_cohorts_n`, "The initial number of individuals in the cohort."
```

```{note}
Even if you intend cohort distributions to be identical across all simulation cells you
still **must** provide the input data described above for every single cell individually.
```

### Initial PFT propagule distributions

The distribution of PFT propagules must be provided as an array variable in a NetCDF
file. The array must have spatial dimensions (`x` and `y`) mapping counts onto cells and
also a `pft` dimension, allowing a count to be defined for each PFT in each cell. The
Python code below generates an example of the required format:

```{code-cell} ipython3
import numpy as np
import xarray as xr

pft_propagules = xr.DataArray(
    np.ones((2, 10, 10)),
    dims=["pft", "x", "y"],
    coords={
        "pft": ["broadleaf", "shrub"],
        "x": np.arange(50, 1000, 100),
        "y": np.arange(50, 1000, 100),
    },
)

pft_propagules
```

The [model configuration](./plants_config.md) then needs to include the path to the
NetCDF file containing this array variable.

```toml
[[core.data.variable]]
file_path = "../data/example_plant_data.nc"
var_name = "plant_pft_propagules"
```
