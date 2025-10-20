---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
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

# The Soil Model implementation

## Model overview

The soil model stores the size of a large number of soil pools within a [PoolData
class](virtual_ecosystem.models.soil.pools.PoolData). These pools are generally
densities of carbon, nitrogen of phosphorus. The soil model is updated by numerically
integrating the [calculate_all_pool_updates
method](virtual_ecosystem.models.soil.pools.SoilPools.calculate_all_pool_updates) of the
[SoilPools](virtual_ecosystem.models.soil.pools.SoilPools) class. This method calculates
how much the soil pools should change based on a large number of processes:

1. Soil receives inputs from litter decay and the decay of animal necromass (simulated
   within the animal model). These inputs are split into dissolved and particulate forms,
   and the nutrient content is further divided into organic and inorganic forms.
1. Carbon is transformed between two different protected forms and a form usable by
   microbes. The rates at which this happens is based on environmental conditions (see
   the [environmental factors submodule](virtual_ecosystem.models.soil.env_factors)) and
   presence of microbially produced enzymes in the soil.
1. Microbes grow by taking up carbon, nitrogen and phosphorus from the soil, this is
   handled by the [uptake submodule](virtual_ecosystem.models.soil.uptake). Some of the
   carbon that microbes uptake is respired in order to gain energy, this carbon is then
   lost to the soil.
1. Mycorrhizal fungi are a special case of microbial nutrient uptake, as they are
   entirely dependent on their host plant for carbon. They uptake nitrogen and
   phosphorus (in both organic and inorganic forms), some of which is used for growth
   and maintenance, with the rest being supplied to their symbiotic plant partners.
1. Fungi allocate a certain proportion of their growth to the production of reproductive
   fruiting bodies. These bodies are either consumed by animals or decay back into the
   soil.
1. While organic nutrient flows follow the flow of carbon, nutrient cycling also
   involves inorganic nutrients which cycle independently. These cycles couple due to
   microbial mineralisation, which in our model occurs when microbes have an excess of
   nutrients and so release them in an inorganic form.
1. Inorganic nitrogen can also be formed through nitrogen fixation. Our model includes
   both plant-associated and free-living versions of this process.
1. This nitrogen, which is fixed in the form of ammonium, can nitrify to form nitrate,
   another inorganic form of nitrogen that both plants and microbes can utilise. This
   nitrate can be denitrified which causes the nitrogen contained in it to be lost from
   the soil.
1. Labile inorganic phosphorus can also be released from mineral forms in the soil. This
   labile inorganic phosphorus can be used by both plants and microbes, but can become
   inaccessible when it associates with soil minerals.
1. Many nutrients forms are also soluble, these can then be lost from the soil due to
   nutrient leaching.
1. The soil model also allows animals to consume {term}`POM`, soil bacteria and soil
   fungi.

The model contains four functional groups (bacteria, saprotrophic fungi, arbuscular
mycorrhizal fungi, and ectomycorrhizal fungi). The parameters associated with each group
are stored using a [MicrobialGroupConstants data
class](virtual_ecosystem.models.soil.microbial_groups.MicrobialGroupConstants), and the
full set required for the simulation is constructed using the
[make_full_set_of_microbial_groups
function](virtual_ecosystem.models.soil.microbial_groups.make_full_set_of_microbial_groups).
Similarly, enzyme classes are distinguished by whether they were produced by fungi or
bacteria and by what substrate they break down ({term}`MAOM` or {term}`POM`). So, there
is a total of four enzyme classes in the model. The parameters associated with each
class are stored in an [EnzymeConstants data
class](virtual_ecosystem.models.soil.microbial_groups.EnzymeConstants), and the full set
of them can be constructed using the [make_full_set_of_enzymes
function](virtual_ecosystem.models.soil.microbial_groups.make_full_set_of_enzymes).

## Model variables

## Initialisation and update

The tables below show the variables that are required to initialise the soil model and
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
        "SoilModel", ["vars_required_for_init", "vars_required_for_update"]
    ),
    raw=True,
)
```

## Generated variables

The soil model does not currently generate any variables. If that changes this section
will need to be updated.

## Updated variables

At each model step, the following variables are then updated.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(generate_variable_table("SoilModel", ["vars_updated"]), raw=True)
```
