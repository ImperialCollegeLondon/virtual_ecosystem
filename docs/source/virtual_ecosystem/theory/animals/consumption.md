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

# Animal consumption

In the Virtual Ecosystem animal cohorts can have a wide variety of diets. These diets
are constrained by habitat strata, i.e. animals that live solely in the canopy cannot
access ground based resources, and due to the dietary preferences of animals. The point
of this page is to set out what the possible dietary preferences. There are three
broad-brush diets: carnivory, herbivory and detritivory. Each of these is further broken
down into the specific pools that animals can consume from.

## Carnivory

Animal cohorts can eat individuals from other animal cohorts. This is generally
only restricted by body size constraints.

## Herbivory

Animal cohorts can also consume various plant tissues. The full set of plant tissues
available for plant consumption can be seen in {numref}`plant_biomass_flows`.

:::{figure} ../../../_static/images/plant_model_biomass_flows.svg
:name: plant_biomass_flows
:alt: An image showing how plant biomass flows both to animals and to litter/soil
:scale: 100 %
:align: center

A visualisation of the biomass pools produced by the plants models and their possible
destinations. Links indicated by dashed lines represent links that are planned but not
yet implemented.

All living plant tissues are possible targets of herbivory, and every tissue has a
turnover rate. For most cases this turnover is passed directly to the litter, but as
fallen fruits and seeds are consumed by ground level herbivores we define special pools
for them. The fallen seed pool does not decay and either gets eaten by animals or
contributes to the propagation of new plant cohorts. Fallen fruits can also be eaten by
animals, but can also decay (with a rate [calculated by the plants
model](../plants/fallen_fruit_and_seeds.md#fruit-decay)), this decay passes biomass
directly to the soil model.

There is a mechanical inefficiency inherent to herbivory, i.e. animals do not consume
100% of the biomass that they pull off of plants. So, while the biomass removed by
herbivory primarily contributes to increased animal cohort, a part of it is also added
to the litter as "herbivory waste", which subsequently gets passed to the litter.
:::

## Detritivory

TODO - POPULATE THIS SECTION, EXPLAINING THAT BROWN WEB IS MAYBE A BETTER CATCH ALL TERM

TODO - ADD BROWN WEB IMAGE IN HERE AND EXPLAIN

TODO - REWRITE THIS TO FIT THE NEW STYLE
Both animal carcasses and excrement are important resources for animals to scavenge
from, as such the [decay of carcasses and excrement](./carcasses_and_excrement.md) is
tracked as part of the animal model.
