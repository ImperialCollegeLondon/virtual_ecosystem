---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

# The Plants Model implementation

## Required variables

The tables below show the variables that are required to initialise the plants model and
then update it at each time step.

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

The required variables starting with `plant_cohorts_` provide the initial inventory of
the plants growing within each cell in the simulation. These variables are one
dimensional arrays that together form a 'data frame', with each row representing a plant
cohort. Each cohort:

* occurs in a single cell (`plant_cohorts_cell_id`),
* has an initial size as the diameter at breast height (`plant_cohorts_dbh`),
* has an initial number of individuals (`plant_cohorts_n`), and
* a plant functional type (`plant_cohort_pft`).

The plant functional types (PFT) for a simulat are set in the configuration of the Plant
Model. Each PFT defines a set of traits that determine the geometry of stem growth, root
and leaf turnover rates, wood density and respiration costs.

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
