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

# Representation of the soil carbon cycle

TODO - NEED A BETTER OPENING HERE, E.G. WHY USE POOLS AT ALL?

This page explains how we have implemented the soil carbon cycle.

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
microbial biomass pool. Microbes assist in the formation of {term}`LMWC` by excreting
enzymes that breakdown {term}`POM`. They then utilise LMWC to form biomass. Microbial
waste products and necromass either break down into LMWC, or form mineral associations.
In addition, microbial respiration is one of the major sources of carbon loss to the
system. This pool turns over rapidly (order of days) and only represents a very small
fraction of total soil carbon. However, it is very important to track because many soil
processes are driven by microbes, and so depend either implicitly or explicitly on the
size of this pool.
