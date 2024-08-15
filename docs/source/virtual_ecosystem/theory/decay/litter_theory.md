# Theory of litter decay

The litter model we use is based on the well established approach of
{cite}`kirschbaum_modelling_2002`. In our model, litter is divided into a number of
separate pools based on input material type, chemistry and spatial location (i.e. above-
vs below-ground). These pools each have a characteristic decay rate, which gets modified
by environmental conditions and for some of the pools by their lignin concentrations.
Notably, these decay rates are not affected by the nitrogen and phosphorus
concentrations of the pools. Instead, nitrogen and phosphorus concentrations effect the
partitioning of input organic matter between litter pools, i.e. if the nutrient
concentrations of a particular input are low a higher proportion of the input goes into
slow decaying litter pools. This indirectly captures the impact of nitrogen and
phosphorus chemistry on litter decay.

The rest of this page gives provides details on the specific litter pools, the
partitioning of organic matter input between them, and the environmental factors that
effect decay rates.

## Litter pools

TODO - Change this based on new high level intro, also need to think how this fits with
how I'm explaining partition.
We also select our litter pools from a pre-existing framework
{cite}`kirschbaum_modelling_2002`. Here, pools are principally defined by input type,
e.g. coarse wood, fine wood, structural and metabolic. They are then further subdivided
into above- and below-ground pools. Some of these pools cannot be fully characterised
due to insufficient data and so following {cite}`fatichi_mechanistic_2019`, we neglect
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

TODO - add Chemistry + Partition section
TODO - Add section about Environmental factors
