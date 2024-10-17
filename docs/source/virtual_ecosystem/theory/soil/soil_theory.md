---
jupytext:
  formats: md:myst
  main_language: python
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

# Theory of the soil model

This page provides general details of the theory underlying the soil module, it is
currently a bit of a work in progress as the soil model is being actively extended at
present. This page provides a description of the soil [carbon](#soil-carbon-pools),
[nitrogen](#nitrogen-pools), and [phosphorus](#phosphorus-pools) pools that the soil
model is constructed from. It also provides a brief outline of our [approach to
representing soil microbes](#microbial-representation).

:::{admonition} In progress 🛠️

The theory for soil nitrogen, phosphorus and microbial communities is not yet final. As
such, these sections are currently relatively short and will be expanded significantly in
future.

:::

## Soil carbon pools

The fundamental basis of this module are carbon pools. Historically, the predominant
framework for modelling soil carbon has been the CENTURY model
{cite}`parton_analysis_1987`, which divides soil organic matter into three pools
(active, slow and passive). These pools are characterised primarily by their turnover
rates, but are also differentiated by lignin content of the organic matter that flows
into each pool. This framework has come under sustained criticism as these pools are
conceptual and not directly measurable. In response to this there has been a movement
towards using soil carbon pool definitions that are based upon measurable physical and
chemical properties. The Millennial model combines the most commonly used of these soil
carbon pools into a single model {cite}`abramoff_millennial_2018`. This model
framework is both comprehensive and defines measurable pools, and for this reason we
make use of it in our soil module.

The relevant pools are as follows:

### Particulate organic matter (POM)

Particulate organic matter (POM) derives from the decomposition and fragmentation of
litter and other necromass. It can be formed from plant material, insect carcasses,
aggregates, fungal matter, etc. Generally, the particulates are of sufficient size that
their original source can still be determined. POM can associate with soil aggregates,
or be further broken down by microbial activity. In most systems this is a pool with a
reasonably fast turnover rate (order of months). However, in heavily waterlogged soils
(i.e. peatlands) this pool turns over far more slowly and is a significant store of
carbon.

### Low molecular weight carbon (LMWC)

Low molecular weight carbon (LMWC) consists of molecules that are simple, soluble and
labile, i.e. those that are immediately utilisable by microbes. It is formed through the
microbially mediated breakdown of POM, but is also directly supplied by plant roots.
LMWC is commonly lost to leaching, or by microbial uptake. This pool turns over rapidly
(order of days).

### Mineral associated organic matter (MAOM)

Carbon can be protected from microbial activity by mineral association, whereby
mineral surfaces take up organic matter by adsorption, conferring chemical protection.
It is generally microbial biomass and LMWC that gets absorbed in this way. Aggregates
can form from MAOM, which they then release upon breakdown. When desorption occurs
carbon is released from mineral association in the form of LMWC. This pool turns over
very slowly (order of years to decades) and so in most soils it is the main form of
(chemically) protected carbon.

### Microbial biomass

Microbial biomass accounts for a small fraction of total soil carbon. However, microbes
are key drivers of soil carbon cycling, with significant flows of carbon through the
microbial biomass pool. Microbes assist in the formation of LMWC by excreting enzymes
that breakdown POM. They then utilise LMWC to form biomass. Microbial waste products and
necromass either break down into LMWC, or form mineral associations. In addition,
microbial respiration is one of the major sources of carbon loss to the system. This
pool turns over rapidly (order of days) and only represents a very small fraction of
total soil carbon. However, it is very important to track because many soil processes
are driven by microbes, and so depend either implicitly or explicitly on the size of
this pool.

## Nitrogen pools

Nitrogen cycling in this module occurs primarily in an organic form. For this reason we
track the stoichiometry of every soil carbon and litter pool. However, there are also
significant nitrogen cycle processes that involve inorganic forms of nitrogen. For this
reason a number of inorganic nitrogen pools are additionally defined. They are as
follows:

### Combined ammonia ($\ce{NH_{3}}$) and ammonium ($\ce{NH^{+}_{4}}$) pool

Nitrogen fixation is a hugely significant process in tropical soils. It generally
produces ammonia ($\ce{NH_{3}}$), which plants can directly take up. Ammonium
($\ce{NH_{4}^{+}}$) is produced during organic matter decomposition by ammonifying
microbes, and can also be directly taken up by plant roots. Transformation of ammonia to
ammonium (and vice versa) is a frequent occurrence in soils, but the process would be
tricky to parametrise and validate. So, for the sake of simplicity, only a single
combined pool is used.

### Nitrate ($\ce{NO^{-}_{3}}$)

Nitrification results in production of nitrate ($\ce{NO^{-}_{3}}$) from ammonium. This
nitrate can be lost due to leaching and volatilisation, or can be taken up by plant
roots. We use a separate nitrate pool as it is the generally the preferred form of
nitrogen for plant uptake, and so warrants detailed consideration.

### Nitrite ($\ce{NO^{-}_{2}}$)

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

## Phosphorus pools

Most phosphorus in tropical forest soils is recycled from organic matter inputs. Thus,
as with nitrogen we track the phosphorus stoichiometry of all litter and soil carbon
pools. However, in other systems substantial quantities of phosphorus exist in inorganic
forms, and so the following inorganic phosphorus pools are also included:

### Primary mineral P

Phosphorus can enter soils through weathering of primary minerals. Though this
contribution to the overall phosphorus budget is likely to be small in our case, we
include it for the sake of model completeness.

### Labile P

The inorganic phosphorus that can be taken up by plants is termed labile phosphorus.
This type of phosphorus is formed either by breakdown of organic matter or by weathering
of primary mineral phosphorus.

### Secondary mineral P

Labile phosphorus can form associations with minerals that prevent uptake by plants.
This is termed secondary mineral phosphorus. This phosphorus can be liberated from its
mineral association as labile phosphorus.

### Occluded P

Alternatively, secondary mineral phosphorus can become physically occluded, preventing
its liberation. This phosphorus is termed occluded phosphorus, and is inaccessible to
the wider system (at least on biological time scales). Measurements of total soil
phosphorus include this pool, so it is important to model it explicitly.

## Microbial representation

Microbes are represented as carbon pools, each of which produces a set of enzymes. Each
microbial group will be represented by a separate pool, and will either produce a
different set of enzymes, or the same set in differing proportions.

Major decisions still need to be made in terms of which functional groups will be
included, and how exactly they will differ. So, the above is likely to be
revised/extended in the near future.
