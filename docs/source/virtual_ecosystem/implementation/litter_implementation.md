---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.2
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# The Litter Model implementation

## Required variables

The tables below show the variables that are required to initialise the litter model and
then update it at each time step.

```{code-cell}
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        'LitterModel', 
        ['vars_required_for_init', 'vars_required_for_update']
    ), 
    raw=True
)
```

## Model overview

When the litter model is run, the first thing it does is subtract the amount of litter
consumed by animals from the relevant pools. This happens first to ensure that the
litter eaten by animals never gets treated as also having decayed into the soil.
However, there is an issue with this approach in that it gives animals preferential
access to litter over microbes (which drive the decay processes). This is something we
may have to address in future, potentially by only making a limited portion of the
litter available for animal consumption.

Once the size of the pools post animal consumption has been found, then the decay rates
of the pools are calculated. These rates vary based on environmental conditions (these
factors are calculated using the [environmental factors
submodule](virtual_ecosystem.models.litter.env_factors)) and the lignin proportion of
each pool. The decay rate for all the pools are calculated using the
[calculate_decay_rates
function](virtual_ecosystem.models.litter.carbon.calculate_decay_rates).

The total input of plant matter is calculated. This comes from two sources, the death of
plants and their tissues, and waste products generated herbivory (where animals remove
plant biomass but fail to consume all of it). Before plant tissues die plants actively
remove limiting nutrients from them, in contrast herbivores actively seek out plant
matter rich in limiting nutrients, so inputs from the two different sources would be
expected to have different chemistries. So, for each input plant matter type (leaves,
roots, dead wood and reproductive tissues) both the total input mass and the chemistry
of this input mass needs to be calculated. The flow to each litter pool also needs to be
calculated. All of this is calculated and stored using the [LitterInputs
class](virtual_ecosystem.models.litter.inputs.LitterInputs).

With the new inputs to the litter and the decay of the existing litter known, the
updated litter pool sizes can then be calculated. This is done using the
[calculate_updated_pools
function](virtual_ecosystem.models.litter.carbon.calculate_updated_pools). The chemistry
of these new pools is then found using the [calculate_new_pool_chemistries
method](virtual_ecosystem.models.litter.chemistry.LitterChemistry.calculate_new_pool_chemistries)
of the [LitterChemistry
class](virtual_ecosystem.models.litter.chemistry.LitterChemistry). As a final step
minerialisation (rates at which nutrients enter the soil) rates are found. We track
carbon (using the [calculate_total_C_mineralised
function](virtual_ecosystem.models.litter.carbon.calculate_total_C_mineralised)) and
also nitrogen and phosphorus (using `LitterChemistry` class methods).

## Generated variables

The calculations described above result in the following variables being calculated and
saved within the model data store, and then updated

```{code-cell}
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'LitterModel', 
        ['vars_populated_by_first_update']
    ), 
    raw=True
)
```

## Updated variables

The table below shows the complete set of model variables that are updated at each model
step.

```{code-cell}
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'LitterModel', 
        ['vars_updated']
    ), 
    raw=True
)
```
