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

## Model overview

The litter model uses the following sequence:

1. The amount of litter consumed by animals is subtracted from the relevant pools and
   diverted into animal digestion processes.

2. Decay rates are calculated for the remaining litter in the pools. These rates vary
   based on environmental conditions (see the [environmental factors
   submodule](virtual_ecosystem.models.litter.env_factors)) and the lignin proportion of
   each pool. The decay rates across pools are calculated using the
   [calculate_decay_rates
   function](virtual_ecosystem.models.litter.carbon.calculate_decay_rates).

3. Plant inputs are considered from two sources, which have different stochiometric
   properties.

    * Inputs from tissue senescence and turnover directly from plant communities
      typically have reduced nutrient concentrations through translocation.

    * Plant inputs generated during herbivory, where animals drop unconsumed biomass,
      are not depleted in nutrients and heribvores may be actively selecting plant
      matter rich in limiting nutrients.

    The [LitterInputs class](virtual_ecosystem.models.litter.inputs.LitterInputs)
    therefore handles multiple different tissue types and pathways to keep information
    on the total input mass and chemistry of these different input routes, along with
    flows into the different litter pools.

4. Given the litter loss to consumption and decay and the new inputs, updated litter
   pool sizes are calculated using the [calculate_updated_pools
   function](virtual_ecosystem.models.litter.carbon.calculate_updated_pools).

5. The chemistry of these new pools is then found using the
   [calculate_new_pool_chemistries
   method](virtual_ecosystem.models.litter.chemistry.LitterChemistry.calculate_new_pool_chemistries)
   of the [LitterChemistry
   class](virtual_ecosystem.models.litter.chemistry.LitterChemistry).

6. The mineralisation rates at which nutrients enter the soil are then found. We track
   carbon (using the [calculate_total_C_mineralised
   function](virtual_ecosystem.models.litter.carbon.calculate_total_C_mineralised)) and
   also nitrogen and phosphorus (using `LitterChemistry` class methods).

:::{admonition} Future directions :telescope:

However, there is an issue with this approach in that it gives animals preferential
access to litter over microbes (which drive the decay processes). This is something we
may have to address in future, potentially by only making a limited portion of the
litter available for animal consumption.

:::

## Model variables

## Initialisation and update

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

## Generated variables

The first update of the litter model adds the following variables to the data
environment of the Virtual Ecosystem:

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

At each model step, the following variables are then updated.

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
