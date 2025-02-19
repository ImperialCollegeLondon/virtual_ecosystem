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

Soils are one of the largest stores ecological stores of carbon. For this reason, there
has been long term interest in modelling the soil carbon cycle. This is a massively
complex task as carbon exists in the soil in a huge variety of forms. Because of this
approaches to soil carbon modelling (starting with the CENTURY model
{cite}`parton_analysis_1987`) have generally grouped carbon into a small set of pools
with common properties. This is the broad approach that we take in the Virtual
Ecosystem. In this page, we set out the set of pools that our model of the soil carbon
cycle uses, explain the inputs that these pools receive from the other components of the
Virtual Ecosystem, and describe the processes that transfer carbon between pools.

## Soil carbon pools

TODO - Add something here about how we only consider chemical protection, and not
physical protection.

Historically, the predominant framework for modelling soil carbon has been the CENTURY
model {cite}`parton_analysis_1987`, which divides soil organic matter into three pools
(active, slow and passive). These pools are characterised primarily by their turnover
rates, but are also differentiated by lignin content of the organic matter that flows
into each pool. This framework has come under sustained criticism as these pools are
conceptual and not directly measurable. In response to this there has been a movement
towards using soil carbon pool definitions that are based upon measurable physical and
chemical properties. The Millennial model combines the most commonly used of these soil
carbon pools into a single model {cite}`abramoff_millennial_2018`. This model framework
is both comprehensive and defines measurable pools, and for this reason we make use of
it in our soil module.

The relevant pools are as follows:

### Particulate organic matter (POM)

Particulate organic matter (POM) derives from the decomposition and fragmentation of
litter and other necromass. It can be formed from plant material, insect carcasses,
aggregates, fungal matter, etc. Generally, the particulates are of sufficient size that
their original source can still be determined. In most systems this is a pool with a
reasonably fast turnover rate (order of months). However, in heavily waterlogged soils
(i.e. peatlands) this pool turns over far more slowly and is a significant store of
carbon.

### Low molecular weight carbon (LMWC)

Low molecular weight carbon (LMWC) consists of molecules that are simple, soluble and
labile, i.e. those that are immediately utilisable by microbes. It is formed through the
microbially mediated breakdown of more complex carbon, but is also directly supplied by
plant roots. LMWC is commonly lost to leaching, or by microbial uptake. This pool turns
over rapidly (order of days).

### Mineral associated organic matter (MAOM)

Carbon can be protected from microbial activity by mineral association, whereby
mineral surfaces take up organic matter by adsorption, conferring chemical protection.
This pool turns over very slowly (order of years to decades) and so in most soils it is
the main form of (chemically) protected carbon.

### Microbial biomass

Microbial biomass accounts for a small fraction of total soil carbon. However, microbes
are key drivers of soil carbon cycling, with significant flows of carbon through the
microbial biomass pool, with microbial respiration is one of the major sources of carbon
loss to the system. This pool turns over rapidly (order of days) and only represents a
very small fraction of total soil carbon. However, it is very important to track because
many soil processes are driven by microbes, and so depend either implicitly or
explicitly on the size of this pool.

### Microbial necromass

When microbial cells die they breakdown forming what is termed microbial necromass. This
consists of complex biochemicals that normally would be contained within cells, that are
now exposed directly to the soil environment. This pools turns over rapidly (order of
days), and is very small. However, it is important to track this pool as the
biochemicals that it represents rapidly associated with soil minerals, so the size of
this pool can effect how quickly new protected carbon is formed.

TODO - Add inputs section

TODO - Add a section for exchange processes
