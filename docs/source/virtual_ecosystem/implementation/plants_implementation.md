---
jupytext:
  formats: md:myst
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
  version: 3.12
---

# The Plants Model implementation

## Plant functional types

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

The PFT definitions file needs to include the following fields defining the PFT names
and then values for all of the traits:

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

## Required array variables

In addition to the definition of the plant communities, the plants model needs some
additional array data to be set. These provide values that can be easily structured as
arrays by grid cell id and by plant functional type name:

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        "PlantsModel", ["vars_required_for_init", "vars_required_for_update"]
    ),
    raw=True,
)
```

## Model overview

The Plant Model works by using the cohort data within each cell to generate the heights
and vertical canopy profiles of all individuals. These are then used to build a
community wide canopy structure under the perfect-plasticity approximation model
{cite}`purves_predicting_2008`. The area of the grid cell is used to constrain the
community-wide distribution of crown area into closure layers: as the canopies of taller
trees use up the available space in the top most layer, shorter trees then fill up lower
canopy layers until all of the community crown-area is allocated to a canopy layer.

These canopy layers then define the vertical light profile through the canopy. The
photosynthetic photon flux density (PPFD) is partially intercepted by each canopy layer,
giving the eventual PPFD reaching ground level.

The P Model {cite}`prentice_balancing_2014` is then used to estimate the light use
efficiency for each individual across their canopy contributions to each canopy layer.
The specific canopy conditions of air temperature, vapor pressure deficit, atmospheric
pressure and $\ce{CO2}$ concentration define the optimal trade-off between carbon uptake
and water loss for the leaves in each canopy layer. The PPFD flux intercepted by each
layer can then be used to scale the light use efficienct up to the gross primary
productivity (GPP) of each layer, and these can be summed across layers to generate per
stem GPP.

The Virtual Ecosystem then uses the T model {cite}`li_simulation_2014` to estimate the
increase in diameter at breast height from the GPP. The T model estimates maintenance
and respiration costs for a given stem and then allocates the resulting net-primary
productivity (NPP) to growth, generating an expected change in diameter at breast height
given the wood density, stem geometry and NPP. These calculated increments are then
applied to the cohorts and the larger stems are used for the next update.

Mortality and reproduction have not yet been implemented.

## Generated variables

The calculations described above result in the following variables being calculated and
saved within the model data store, and then updated

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(
    generate_variable_table(
        "PlantsModel", ["vars_populated_by_init", "vars_populated_by_first_update"]
    ),
    raw=True,
)
```

## Updated variables

The table below shows the complete set of model variables that are updated at each model
step.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(generate_variable_table("PlantsModel", ["vars_updated"]), raw=True)
```
