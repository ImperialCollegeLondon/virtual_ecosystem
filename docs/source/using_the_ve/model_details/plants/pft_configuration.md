---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.3
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

# Configuring plant functional types

The Plants Model requires the definition of a set of plant functional types, which are
defined as a set of trait values that describe the allometry, carbon allocation,
demography and stoichiometry of each PFT.

The PFT definitions for a simulation need to be stored in a
CSV file: each PFT must have a unique name and each row then provides the trait values
for that PFT. The configuration of the plants model must then provide the
`pft_definitions_path` setting that gives the path to that CSV file:

```toml
[plants]
pft_definitions_path = '/path/to/pft_definitions.csv'
```

The majority of the traits required for each PFT are used to define the allometry of
growing trees, the vertical structure of the canopy and the estimation of growth from
gross primary productivity. This modelling uses an implementation called the T Model
[insert citation] and you can read more
about the T Model and traits in the documentation for the [`pyrealm`
package](https://pyrealm.readthedocs.io/en/stable/users/demography/flora.html#plant-traits),
which is used by the Virtual Ecosystem to simulate plant growth.

In addition to the T Model, the Virtual Ecosystem also defines a set of extra traits to
describe the stoichiometry of plant tissues. Stoichiometry is not currently implemented
in the `pyrealm` package and so these values are additional requirements of the Virtual
Ecosystem.

The PFT definitions file needs to include the following fields (the order doesn't
matter) defining the PFT names and then values for all of the traits:

```{csv-table}
:header: >
: Field name,Description,Example value,VE only

name,TBD,pioneer,
hd,TBD,116.0,
ca_ratio,TBD,390.43,
f_g,TBD,0.02,
h_max,TBD,25.33,
lai,TBD,1.8,
m,TBD,2,
n,TBD,5,
name,TBD,'shrub',
par_ext,TBD,0.5,
resp_f,TBD,0.1,
resp_r,TBD,0.913,
resp_s,TBD,0.044,
resp_rt,TBD,0.05,
rho_s,TBD,200.0,
sla,TBD,14.0,
tau_f,TBD,4.0,
tau_r,TBD,1.04,
tau_rt,TBD,1,
yld,TBD,0.6,
zeta,TBD,0.17,
gpp_topslice,TBD,0.1,
p_foliage_for_reproductive_tissue,TBD,0.05,
deadwood_c_n_ratio,TBD,60.7,✓
deadwood_c_p_ratio,TBD,856.5,✓
leaf_turnover_c_n_ratio,TBD,25.5,✓
leaf_turnover_c_p_ratio,TBD,415.0,✓
plant_reproductive_tissue_turnover_c_n_ratio,TBD,12.5,✓
plant_reproductive_tissue_turnover_c_p_ratio,TBD,125.5,✓
root_turnover_c_p_ratio,TBD,656.7,✓
root_turnover_c_n_ratio,TBD,45.6,✓
foliage_c_n_ratio,TBD,15,✓
foliage_c_p_ratio,TBD,300,✓
```

## Initial cohort data

The plants model then needs an initial distribution of size-structured cohorts across
the cells within the simulation. This is configured using the `cohort_data_path`
setting within the model configuration:

```toml
[plants]
cohort_data_path = '/path/to/cohort_data.csv'
```

The initial cohort data must be provided as a CSV file, with each row representing a
plant cohort. The fields in this file must set:

* `plant_cohort_pft`: the plant functional type of the cohort, matching one of the
  names set in the PFT definitions.
* `plant_cohorts_cell_id`: the grid cell in which the cohort is found.
* `plant_cohorts_dbh`: the initial size of each individual in the cohort, as the
  diameter at breast height (m)
* `plant_cohorts_n`: the initial number of individuals in the cohort

```{note}
Even if you intend cohort distributions to be identical across all simulation cells you
still **must** provide the input data described above for every single cell individually.
```

## Example files

The dropdowns below show the example versions of the plant functional type definitions
and the plant cohort distribution.

````{dropdown} pft_definitions.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/plant_pfts.csv
```
````

````{dropdown} cohort_data.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/example_plant_cohorts.csv
```
````
