---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.4
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

# Theory of litter decay

The litter model we use is based on the well established approach of
{cite}`kirschbaum_modelling_2002`. In our model, litter is divided into a number of
separate pools based on input material type, chemistry and spatial location (i.e. above-
vs below-ground). These pools each have a characteristic decay rate, which gets modified
by environmental conditions and, for some of the pools, by their lignin concentrations.
Notably, these decay rates are not affected by the nitrogen and phosphorus
concentrations of the pools. Instead, nitrogen and phosphorus concentrations affect the
partitioning of input organic matter between litter pools, i.e. if the nutrient
concentrations of a particular input are low, then a higher proportion of the input goes
into slow decaying litter pools. This indirectly captures the impact of nitrogen and
phosphorus chemistry on litter decay.

The rest of this page provides details on the specific litter pools, the partitioning of
organic matter input between them, the tracking of litter chemistry and the impacts
animals have on litter accumulation and decay.

## Litter pools

In our model, pools are principally defined by input type, e.g. woody, structural and
metabolic. They are then further subdivided into above- and below-ground pools. Some of
these pools cannot be fully characterised due to insufficient data, so we neglect them
following {cite}`fatichi_mechanistic_2019`. This means that we use a single
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
dynamics, i.e. all wood losses from tree falls, branch fall etc, are assumed to be added
to an above-ground woody pool. We assume that the vast majority of dead wood ends up
decaying on top of the soil, and so there is no corresponding below-ground pool. We
considered including a separate pool for standing dead trees, as wood decaying in this
form would experience a very different environment and hence would be expected to decay
at a different rate. However, this felt like too much effort for what is likely to be a
small effect.

### Below-ground metabolic litter

For the below-ground pools, roots (both fine and coarse) are the major source of biomass.
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

$$f_l(L) = \exp{(rL)},$$

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

$$f_{m,i} = f_M - l_i * (s_N N_i + s_P P_i),$$

where $f_M$ is the maximum fraction that can go to the metabolic pool, $l_i$ is the
lignin proportion for input stream $i$, $N_i$ is the carbon:nitrogen ratio of input
stream $i$, $P_i$ is the carbon:phosphorus ratio of input stream $i$, $s_N$ parametrises
the responsiveness of the split to changes in the product of lignin proportion and
carbon:nitrogen ratio, and $s_P$ parametrises the responsiveness of the split to changes
in the product of lignin proportion and carbon:phosphorus ratio.

### Split of nutrient inputs between pools

Now that the split of input sources between pools has been determined, we have to
determine how the various nutrients contained in the input biomass are split between
pools. For lignin it is straightforward, as by definition only woody and structural litter
pools contain lignin. So, all lignin from input biomass is added to the relevant
structural (or woody) pool and none of it is added to the metabolic pools.

The situation is more complex for nitrogen and phosphorus, as both litter pools contain
them. Furthermore, the division between metabolic and structural litter is a modelling
convenience rather than an empirically measurable split. We use a simple relation (see
above) to determine the fraction of the carbon mass flows to metabolic ($f_m$) and
structural litter ($f_s$), while in theory this relation could be extended to also
predict nitrogen and phosphorus flow, doing so would introduce a large number of
parameters that cannot be estimated based on empirical data. So, in order to keep the
number of unmeasurable parameters down, we assume (following
{cite:t}`kirschbaum_modelling_2002`) that the nutrient concentrations of the inputs to a
metabolic/structural pool pair always follow a fixed ratio,

$$\rho = \frac{r_m}{r_s},$$

where $r_m$ is the concentration of the nutrient (relative to the carbon mass) in the
input to the metabolic litter pool, $r_s$ is the concentration in the input to the
corresponding structural litter pool, and $\rho$ is their ratio. Based on this, the
nutrient mass that flow into each pool is therefore

$$n_s = n_T / (1 + \rho * (C_m/C_s))$$

and

$$n_m = \rho * (C_m/C_s) * n_s$$

where $n_T$ is the total nutrient input (to both pools), and $C_m$ and $C_s$ are the
carbon flows to the metabolic and structural pools, respectively. The equations above
will only be satisfied when the sum of the nutrient input flows to the pools matches the
total input. At present, we allow $\rho$ to vary between nutrients but not between
strata (above- vs below-ground). These values are set in
{attr}`metabolic_to_structural_n_ratio
<virtual_ecosystem.models.litter.model_config.LitterConstants.metabolic_to_structural_n_ratio>`
and {attr}`metabolic_to_structural_p_ratio
<virtual_ecosystem.models.litter.model_config.LitterConstants.metabolic_to_structural_p_ratio>`.
It is important to note, that the choice of these ratios will only affect the nitrogen
and phosphorus mineralisation rates and not the broader litter decay dynamics. This is
because the nitrogen and phosphorus concentrations do not directly affect pool decay
rates.

## Litter decay dynamics

The decay of all litter pools are assumed to follow linear kinetics, with the rate of
change in the carbon mass, $P$, of litter pool $j$ being given by

$$\frac{dP_j}{dt} = I_j - K_j(T,\psi,L)P_j,$$

where $I_j$ is the rate of input to pool $j$ (in carbon terms), $T$ is the temperature,
$\psi$ is the soil water potential and $K_j(T,\psi,L)$ is the decay rate of the pool.
The decay rate of the pool will always depend on temperature, but only for the
below-ground pools will it be affected by soil water potential. Further, lignin content
only affects the decay rates of pools which contain lignin (i.e. structural and woody
pools). As an example, the decay rate of the below-ground structural litter pool is
calculated as

$$K_{bs}(T,\psi,L) = k_{bs} * f_t(T) * A(\psi) * f_l(L),$$

where $k_{bs}$ is the decay rate constant for the below-ground structural litter pool,
$f_l(L)$ is a factor (defined above) capturing the impact of lignin on decay rate,
$f_t(T)$ is a [factor capturing the effect of soil temperature on decay
rates](./environmental_links.md#litter-decay-temperature-response), and $A(\psi)$ is a
[factor capturing the effect of soil moisture on decay
rates](./environmental_links.md#litter-decay-moisture-response).

The dynamics defined above are analytically solvable provided that the input does not
vary over the timescale of interest. Because of this, the litter model does not
numerically integrate the dynamics and instead just uses the exact solution for the
litter pool size at the end of the model update interval ($\tau$). This solution can be
expressed as

$$
P_j(\tau) = \frac{I_j}{K_j(T,\psi,L)} - \left(\frac{I_j}{K_j(T,\psi,L)} -
    P_{j,0}\right) e^{-K_j(T,\psi,L)\tau},
$$

where $P_{j,0}$ is the size of litter pool $j$ at the start of the update interval. We
don't use comparable exact solutions for the nitrogen, phosphorus and lignin dynamics.
Instead, we estimate the loss of each chemical based on the loss of carbon. This
estimation assumes that old litter (i.e. litter that is there at the start of the time
step) decays first and that litter added during the update only decays if the total
decay of litter exceeds the initial litter pool size. Total loss of the chemicals is
then found either using the initial pool chemistry (if total decay is less than the
initial pool size), or a weighted average of the initial pool chemistry and the
chemistry of the input biomass.

:::{admonition} Future directions 🔭

Obtaining exact solutions for the nitrogen, phosphorus and lignin dynamics would improve
the accuracy of the model. For the nitrogen and phosphorus case, this shouldn't be
particularly difficult, but as nitrogen and phosphorus concentrations don't affect
litter pool decay rates the improvement in model accuracy would be marginal. Obtaining
an exact solution for the lignin dynamics would be both trickier to accomplish as
changes in lignin concentration will change litter pool decay rates. However, this
feedback makes tracking lignin concentration accurately far more important for overall
model accuracy.

:::

## Animal impacts on litter

Animals interact with the litter model in two ways. Firstly, all litter pools are
available to be scavenged from by animals. So, the presence of functional groups with
the right traits to exploit a certain litter pool (e.g. termites for woody litter) will
increase the breakdown rate of the pool. Secondly, herbivores often remove more biomass
from plants than they actually consume (e.g. elephants with pull off entire branches
from saplings and then eat only the easy to chew bits). This excess plant biomass gets
added to the litter.

The litter model does not track the decay of animal excrement or carcasses. This is
because the animal model already [models their
decay](../animals/carcasses_and_excrement.md), tracking these within the litter model
would essentially force them to decay twice. Instead the flow of decayed matter from
carcasses and excrement flows straight from the animal model to the soil model.
