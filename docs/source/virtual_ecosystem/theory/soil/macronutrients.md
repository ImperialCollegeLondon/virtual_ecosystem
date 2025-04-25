---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.7
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

# Soil macronutrient cycles

In the Virtual Ecosystem, as well as tracking the flow of carbon through the system, we
also track the flow of nitrogen and phosphorus. The reason for tracking these two is
that they are generally though to be the two macronutrients that most limit ecosystem
productivity. A significant portion of the cycling of these elements occurs associated
with carbon. Beyond this organic macronutrient cycle, each element can also cycle
independently of carbon. The processes involved in these inorganic nutrient cycles tend
to be specific to the element of interest.

## Organic macronutrient cycling

The soil and litter model track the nitrogen and phosphorus stoichiometry of each soil
carbon pool. For the majority of processes, the nutrients are assumed to just follow the
flow of carbon, e.g. when microbes die creating microbial necromass amount of
nutrient added to the necromass pool is calculated as

$$d_n = \frac{d_c}{r_{N,m}},$$

where $d_c$ is the amount of necromass generated in carbon terms and $r_{N,m}$ is the
carbon:nitrogen ratio of the microbial group. There are two processes that do not follow
this pattern: litter decomposition and microbial uptake.

Litter decomposition occurs through two pathways, fragmentation and leaching.
Fragmentation results in large pieces of litter being broken up into smaller and smaller
pieces until they are no longer recognisable as litter. Crucially these fragments are
still organic molecules, so here the nutrient flow still follows the carbon flow.
Leaching occurs when water travelling downwards through the litter layer into the soil
proper carries small molecules with it. As these molecules are very small, they can be
either organic or inorganic, and so the nutrients can escape the organic cycle. For
example, the organic phosphorus gets added to the labile (inorganic) phosphorus pool due
to litter decay with rate

$$I_{l} = (1 - \delta_o) * \lambda_l * I_p,$$

where $I_p$ is the total input of phosphorus from the litter to the soil, $\lambda_p$ is
the fraction of the litter decay that occurs by leaching, and $\delta_o$ is the fraction
of the leached phosphorus that enters the soil in an organic form.

Microbes uptake organic matter (in the form of :term:`LMWC`) so that they can synthesis
new biomass. This organic matter also has nitrogen and phosphorus contents (referred to
as :term:`DON` and :term:`DOP`, respectively). This can result in more macronutrient
being taken up than the microbe needs to sustain it's growth. When this happens the
excess macronutrient gets returned to the soil. The form that this excess nutrient gets
returned in depends on how carbon limited the microbial group is. The closer to carbon
limitation (the point where carbon is the nutrient limiting growth) the microbial group
is the higher the proportion that gets returned in an inorganic form is.

## Inorganic nitrogen cycling

TODO - Add an overall introduction

### Inorganic nitrogen pools

TODO - There's a lot of out of date pools here

TODO - Should also add details of which pools are taken up by plants + microbes, which
pools leach out of the soil, which pools are added to by litter decomp etc

However, there are also significant nitrogen cycle processes that involve inorganic
forms of nitrogen. For this reason a number of inorganic nitrogen pools are additionally
defined. They are as follows:

#### Combined ammonia ($\ce{NH_{3}}$) and ammonium ($\ce{NH^{+}_{4}}$) pool

Nitrogen fixation is a hugely significant process in tropical soils. It generally
produces ammonia ($\ce{NH_{3}}$), which plants can directly take up. Ammonium
($\ce{NH_{4}^{+}}$) is produced during organic matter decomposition by ammonifying
microbes, and can also be directly taken up by plant roots. Transformation of ammonia to
ammonium (and vice versa) is a frequent occurrence in soils, but the process would be
tricky to parametrise and validate. So, for the sake of simplicity, only a single
combined pool is used.

#### Nitrate ($\ce{NO^{-}_{3}}$)

Nitrification results in production of nitrate ($\ce{NO^{-}_{3}}$) from ammonium. This
nitrate can be lost due to leaching and volatilisation, or can be taken up by plant
roots. We use a separate nitrate pool as it is the generally the preferred form of
nitrogen for plant uptake, and so warrants detailed consideration.

#### Nitrite ($\ce{NO^{-}_{2}}$)

Denitrification is a (microbially mediated) process that converts nitrate to gaseous
forms of nitrogen, particularly nitrous oxide ($\ce{N_{2}O}$) and dinitrogen
($\ce{N_{2}}$), which then escape the soil. In order to avoid modelling too many forms
of nitrogen, we choose to only explicitly track the concentration of the intermediate
product nitrite ($\ce{NO^{-}_{2}}$). Though nitrite is not generally taken up by
plants, it can be converted back into nitrate which can be. However, the conversion of
nitrite into nitrous oxide or dinitrogen represents a point of no return, with the
nitrogen being irretrievably lost to the soil. Thus, including an explicit nitrite pool
allows us to capture the key dynamics of nitrogen loss, whilst using a minimal number of
nitrogen pools.

### Inorganic nitrogen cycling processes

TODO - Populate this with details of the key processes which cycle inorganic nitrogen

## Inorganic phosphorus cycling

TODO - Add a general intro

### Inorganic phosphorus pools

TODO - I don't include occluded phosphorus and this should be justified

TODO - Should also add details of which pools are taken up by plants + microbes, which
pools leach out of the soil, which pools are added to by litter decomp etc

However, in other systems substantial quantities of phosphorus exist in inorganic
forms, and so the following inorganic phosphorus pools are also included:

#### Primary mineral P

Phosphorus can enter soils through weathering of primary minerals. Though this
contribution to the overall phosphorus budget is likely to be small in our case, we
include it for the sake of model completeness.

#### Labile P

The inorganic phosphorus that can be taken up by plants is termed labile phosphorus.
This type of phosphorus is formed either by breakdown of organic matter or by weathering
of primary mineral phosphorus.

#### Secondary mineral P

Labile phosphorus can form associations with minerals that prevent uptake by plants.
This is termed secondary mineral phosphorus. This phosphorus can be liberated from its
mineral association as labile phosphorus.

#### Occluded P

Alternatively, secondary mineral phosphorus can become physically occluded, preventing
its liberation. This phosphorus is termed occluded phosphorus, and is inaccessible to
the wider system (at least on biological time scales). Measurements of total soil
phosphorus include this pool, so it is important to model it explicitly.

### Inorganic phosphorus cycling processes

TODO - Populate this with details of the key processes which cycle inorganic phosphorus
