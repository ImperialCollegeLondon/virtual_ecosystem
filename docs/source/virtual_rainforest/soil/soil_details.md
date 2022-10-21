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
We make the assumption that coarse root debris fragments sufficiently to not need to be
captured in a separate woody pool. The below-ground metabolic litter pool then includes
the easily broken down root debris.

### Below-ground structural litter

As with the above-ground case the fraction of dead root biomass that ends up in the
below-ground structural pool is set by the lignin:N ratio of the input.

## Nitrogen pools

Nitrogen cycling in this module occurs primarily in an organic form. For this reason we
track the stoichiometry of every soil carbon and litter pool. However, there are also
significant nitrogen cycle processes that involve inorganic forms of nitrogen. For this
reason a number of inorganic nitrogen pools are additionally defined. They are as
follows:

### Combined ammonia ($\ce{NH_{3}}$) and ammonium ($\ce{NH_{4}^{+}}$) pool

Nitrogen fixation is a hugely significant process in tropical soils. It generally
produces ammonia ($\ce{NH_{3}}$), which plants can directly take up. Ammonium
($\ce{NH_{4}^{+}}$) is produced during organic matter decomposition by ammonifying
microbes, and can also be directly taken up by plant roots. Transformation of ammonia to
ammonium (and vice versa) is a frequent occurrence in soils, but the process would be
tricky to parametrise and validate. So, for the sake of simplicity, only a single
combined pool is used.

### Nitrate ($\ce{NO_{3}^{-}}$)

Nitrification results in production of nitrate ($\ce{NO_{3}^{-}}$) from ammonium. This
nitrate can be lost due to leaching and volatilisation, or can be taken up by plant
roots. We use a separate nitrate pool as it is the generally the preferred form of
nitrogen for plant uptake, and so warrants detailed consideration.

### Nitrite ($\ce{NO_{2}^{-}}$)

Denitrification is a (microbially mediated) process that converts nitrate to gaseous
forms of nitrogen, particularly nitrous oxide ($\ce{N_{2}O}$) and dinitrogen
($\ce{N_{2}}$), which then escape the soil. In order to avoid modelling too many forms
of nitrogen, we choose to only explicitly track the concentration of the intermediate
product nitrite ($\ce{NO_{2}^{-}}$). Though nitrite is not generally taken up by
plants, it can be converted back into nitrate which can be. However, the conversion of
nitrite into nitrous oxide or dinitrogen represents a point of no return, with the
nitrogen being irretrievably lost to the soil. Thus, including an explicit nitrite pool
allows us to capture the key dynamics of nitrogen loss, whilst using a minimal number of
nitrogen pools.

## Phosphorus pools

Most phosphorus in tropical forest soils is recycled from organic matter inputs. Thus,
as with nitrogen we track the phosphorus stoichiometry of all litter and soil carbon
pools. However, phosphorus does take an inorganic form at key points in the phosphorus
cycle, and so the following inorganic phosphorus pools are also included:

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

Microbes are represented principally as a carbon pool. For certain purposes this pool
will have to be subdivided, e.g. termites feeding upon mycelium should remove biomass
specifically from a fungal sub-pool. This division is probably best handled by using
nested sub-pools, where for example mycorrhizal fungal biomass forms a portion of the
total fungal biomass which in turn is a portion of the total microbial biomass.

Major decisions still need to be made in terms of how this sub-pool division is
implemented in practice. So the above is likely to be revised/extended in the near
future.
