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

TODO - Talk about animal inputs + consumption once that is settled

## Litter pools

In our model, pools are principally defined by input type, e.g. woody, structural and
metabolic. They are then further subdivided into above- and below-ground pools. Some of
these pools cannot be fully characterised due to insufficient data and so following
{cite}`fatichi_mechanistic_2019`, we neglect them. This means that we use a single
above-ground woody litter pool, rather than coarse and fine woody, and we do not include
any below-ground woody pool. This leaves us with the following pools:

### Above-ground metabolic litter

Above-ground metabolic litter can originate as any non-woody above-ground plant matter
(e.g. bark, leaves, fruit, etc). By definition the pool contains plant matter that is
easily broken down, and so this pool by definition contains no lignin.

### Above-ground structural litter

High lignin concentration biomass from leaves etc is instead included in the
above-ground structural litter pool. This pool shares a set of sources with the
metabolic pool, but is defined as containing the more recalcitrant material.

### Above-ground woody litter

Above-ground dead wood is treated separately due to its substantially different turnover
dynamics. So, all wood losses from tree falls, branch fall etc, is assumed to be added
to an above-ground woody pool. We assume that the vast majority of dead wood ends up
decaying on top of the soil, and so there is no corresponding below-ground pool. We
considered including a separate pool for standing dead trees, as wood decaying in this
form would experience a very different environment and hence would be expected to decay
at a different rate. This felt like too much effort for what is likely to be a small
effect.

### Below-ground metabolic litter

For the below-ground pools roots (both fine and coarse) are the major source of biomass.
The below-ground metabolic litter pool then includes the easily broken down root debris,
which is likely to come predominantly from fine-root turnover.

### Below-ground structural litter

As with the above-ground case only the structural pool contains lignin, this pool
represents hard to break down components of root turnover.

## Litter chemistry

Three aspects of litter chemistry are tracked. Lignin is tracked because its
concentration is one of the biggest factors effecting litter decay rates. Nitrogen and
phosphorus are also major factors in determining litter quality and the total rate of
litter breakdown. However, our primary reason for tracking litter nitrogen and
phosphorus concentrations is to track the rate of entry of phosphorus and nitrogen into
the soil, where both can be major limiting factors for microbial activity. For this
reason, we consider only lignin concentration to have a direct impact on decay rates
(for the pools that contain lignin) and not nitrogen and phosphorus concentrations. In
order to capture the impact of lignin on decay, decay rates are reduced by multiplying
them with a factor that takes the following form

$$I_L = \exp{(rL)},$$

where $L$ is the proportion of the litter pool which is lignin and $r$ is a (negative)
empirical constant setting the strength of the inhibition. This choice of function form
follows {cite:t}`kirschbaum_modelling_2002`.

The litter model takes in input biomass from the plant model as four separate biomass
streams: wood, leaves, roots, and reproductive biomass (e.g. fruits and flowers). All
wood input goes to the woody litter pool, but the other three streams need to be
partitioned between the relevant metabolic and structural litter pools. This partition
depends on the lignin concentration of the input biomass, as well as its nitrogen and
phosphorus concentrations. The fraction of a given input biomass stream ($i$) that goes
into the relevant metabolic litter pool is given by

$$f_{m,i} = f_M - l_i * (s_N N_i + s_P P_i)$$

where $f_M$ is the maximum fraction that can go to the metabolic pool, $l_i$ is the
lignin proportion for input stream $i$, $N_i$ is the carbon:nitrogen ratio of input
stream $i$, $P_i$ is the carbon:phosphorus ratio of input stream $i$, $s_N$ parametrises
the responsiveness of the split to changes in the product of lignin proportion and
carbon:nitrogen ratio, and $s_P$ parametrises the responsiveness of the split to changes
in the product of lignin proportion and carbon:phosphorus ratio.

## Environmental impacts on decay rates

The decay rates of all classes of litter are effected by temperature. For the
above-ground pools, this temperature is simply the air temperature just above the soil
surface. For the below ground pools, the temperature is an average of the temperatures
for the biologically active soil layers. The "intrinsic" litter decay rates are altered
to capture the effect of temperature by multiplying them with a factor that takes the
following form

$$f(T) = \exp{\left(\gamma \frac{T - T_{\mathrm{ref}}}{T + T_{\mathrm{off}}}\right)}$$

where $T$ is the litter temperature, $T_\mathrm{ref}$ is reference temperature used to
establish "intrinsic" litter decay rates, $T_\mathrm{off}$ is an offset temperature, and
$\gamma$ is a parameter capturing how responsive litter decay rates are to temperature
changes.

TODO - ADD SOMETHING SIMILAR FOR SOIL MOISTURE
