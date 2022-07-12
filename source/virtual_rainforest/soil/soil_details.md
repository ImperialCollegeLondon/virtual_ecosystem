# Further details of soil module

This document contains details of the plan for the soil module. At some future date it
should probably be split into multiple pages.

## Soil carbon pools

The fundamental basis of this module are carbon pools. Historically, the predominant
framework for modelling soil carbon has been the CENTURY model
({cite}`parton_analysis_1987`), which divides soil organic matter into three pools
(active, slow and passive). These pools are characterised primarily by their turnover
rates, but are also differentiated by lignin content of the organic matter that flows
into each pool. This framework has come under sustained criticism as these pools are
conceptual and not directly measurable. In response to this there has been a movement
towards using soil carbon pool definitions that defined by measurable physical and
chemical properties. The Millennial model combines the most commonly used of these soil
carbon pools into a single model ({cite}`abramoff_millennial_2018`). This model
framework is both comprehensive and defines measurable pools, and for this reason we
make use of it in our soil module.

The relevant pools are as follows:

### Particulate organic matter (POM)

Particulate organic matter (POM) derives from the decomposition and fragmentation of
litter and other necromass. It can be formed from plant material, insect carcasses,
aggregates, fungal matter, etc. Generally, the particulates are of sufficient size that
their original source can still be determined. POM can associate with soil aggregates,
or be further broken down by microbial activity.

### Low molecular weight carbon (LMWC)

Low molecular weight carbon (LMWC) consists of molecules that are simple, soluble and
labile, i.e. those that are immediately utilisable by microbes. It is formed through the
microbially mediated breakdown of POM, but is also directly supplied by plant roots.
LMWC is commonly lost to leaching, or by microbial uptake.

### Aggregate carbon

Soil aggregates are structures composed of organic matter and minerals. Due to the
(comparatively) strong forces that bind them together, carbon held within the aggregate
volume is to a certain degree "protected" from microbial processes, and so has a far
greater residence time. Through a combination of chemical, physical and biological
mechanisms soil aggregates can be destabilised, leading to the formation of a mix of POM
and mineral associated organic matter (MAOM).

### Mineral associated organic matter (MAOM)

Another mechanism by which carbon is protected from microbial activity is mineral
association, whereby mineral surfaces take up organic matter by adsorption, conferring
chemical protection. It is generally microbial biomass and LMWC that gets absorbed in
this way. Aggregates can form from MAOM, which they then release upon breakdown. When
desorption occurs carbon is released from mineral associated in the form of LMWC.

### Microbial biomass

Microbial biomass accounts for a small fraction of total soil carbon. However, microbes
are key drivers of soil carbon cycling, with significant flows of carbon through the
microbial biomass pool. Microbes assist in the formation of LMWC by excreting enzymes
that breakdown POM. They then utilise LMWC to form biomass. Microbial waste products and
necromass either break down into LMWC, or form mineral associations. In addition,
microbial respiration is one of the major sources of carbon loss to the system.

## Litter pools

We also select our litter pools from a pre-existing framework
({cite}`kirschbaum_modelling_2002`). Here, pools are principally defined by input type,
e.g. coarse wood, fine wood, structural and metabolic. They are then further subdivided
into above- and below-ground pools. Some of these pools cannot be fully characterised
due to insufficient data and so following ({cite}`fatichi_mechanistic_2019`) we neglect
them. This means that we use a single above-ground woody litter pool, rather than coarse
and fine woody, and we do not include any below-ground woody pool. This leaves us with
the following pools

### Above-ground metabolic litter

Above-ground metabolic litter can originate as any non-woody above-ground plant matter
(e.g. bark, leaves, fruit, etc). By definition the pool contains plant matter that is
easily broken down, i.e. that with low lignin concentration.

### Above-ground structural litter

High lignin concentration biomass from leaves etc is instead included in the
above-ground structural litter pool. This pool shares a set of sources with the
metabolic pool, and the split between them in determined based on the lignin:N ratio of
the input.

### Above-ground woody litter

Above-ground dead wood is treated separately due to its substantially different turnover
dynamics. So all wood losses from tree falls, branch fall etc, is assumed to be added to
an above-ground woody pool.

### Below-ground metabolic litter

For the below-ground pools roots (both fine and coarse) are the major source of biomass.
We make the assumption that coarse root debris fragments sufficiently to not need to
be captured in a separate woody pool. The below-ground metabolic litter pool then
includes the easily broken down root debris.

### Below-ground structural litter

As with the above-ground case the fraction of dead root biomass that ends up in the
below-ground structural pool is set by the lignin:N ratio of the input.

## Nitrogen pools

MOST NITROGEN CYCLES WITH THE ORGANIC MATTER

THEN EXPLAIN THE INORGANIC POOLS, AND THE REASON THAT WE WOULD INCLUDE THEM

## Phosphorus pools

MOST PHOSPHORUS CYCLES WITH THE ORGANIC MATTER

THEN EXPLAIN THE INORGANIC POOLS, AND THE REASON THAT WE WOULD INCLUDE THEM

## Microbial representation

HMMM THIS IS THE ONE THAT REQUIRES THOUGHT
