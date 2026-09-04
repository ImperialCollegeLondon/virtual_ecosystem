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

# Configuring plant communities

There are two steps to setting up plant communities in the Plants model:

1. Defining sets of traits for each of the plant functional types (PFTs) to be used in the
   model.
2. Defining the sets of size-structured cohorts of different PFTs growing in the cells
   of the simulation.

## Plant functional types

Plant functional types in the plants model are defined as a set of trait values that
describe the allometry, carbon allocation, demography and stoichiometry of each PFT.

The PFT definitions for a simulation need to be stored in a
CSV file: each PFT must have a unique name and each row then provides the trait values
for that PFT. For example, the file below defines two plant functional types:
`broadleaf` and `shrub`.

````{dropdown} pft_definitions.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/plant_pfts.csv
```
`````

The configuration of the plants model must then provide the `pft_definitions_path`
setting that gives the path to that CSV file:

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
:tags: [remove-input]

# This cell generates a CSV file from the pydantic validation object for PFT data,
# ensuring that the description here is up to date with the codebase.

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

# Dump CSV data to file for ingestion by csv-table directive.
with open("pft_data.csv", "w") as pft_data:
    pft_data.write("\n".join(rows))
```

<!-- This simply ingests the file generated above and displays it as a table. -->
```{csv-table}
:file: pft_data.csv
:header-rows: 1
:quote: '"'
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

The location of this file has to be configured using the `cohort_data_path` setting
within the plants model configuration:

```toml
[plants]
cohort_data_path = '/path/to/cohort_data.csv'
```

The fields in the cohort data file are:

* `plant_cohorts_pft`: The plant functional type of the cohort: a text value that must
  match one of the PFT names set in the PFT definitions.
* `plant_cohorts_cell_id`: The grid cell in which the cohort is found.
* `plant_cohorts_dbh`: The initial size of each individual in the cohort, as the
  diameter at breast height (metres)
* `plant_cohorts_n`: The initial number of individuals in the cohort.

```{note}
Even if you intend cohort distributions to be identical across all simulation cells you
still **must** provide the input data described above for every single cell individually.
```
