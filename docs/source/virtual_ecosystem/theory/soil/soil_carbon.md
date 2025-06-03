---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.1
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

# The soil carbon cycle

Soils are one of the largest stores ecological stores of carbon. For this reason, there
has been long term interest in modelling the soil carbon cycle. This is a massively
complex task as carbon exists in the soil in a huge variety of forms, therefore
soil carbon modelling (starting with the CENTURY model
{cite}`parton_analysis_1987`) have generally grouped carbon into a small set of pools
with common properties. This is the broad approach that we take in the Virtual
Ecosystem. In this page, we set out the set of carbon pools that our soil model
uses, explain the inputs that these pools receive from the other modules of the
Virtual Ecosystem, and describe the processes that transfer carbon between pools.

## Soil carbon pools

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
a variant of it in our soil model.

Where we differ from the Millennial model is that we only include pools that represent
the chemical protection of carbon, and neglect the pool that represents the physical
protection of carbon (i.e. soil aggregates). This partly to avoid double counting of
protection mechanisms, as it is quite common for carbon that is protected chemically to
also be protected physically. Additionally, pools are appropriately set up to represent
chemical transformations (through enzymatic kinetics), but are less appropriate for
physical transformations (i.e. soil aggregates changing in size is hard to capture with
a discrete set of pools). Properly capturing physical protection of carbon requires the
distribution of particle sizes in soil, which is not something we plan to add in the
immediate future.

The carbon pools that we use in our soil model are as follows:

### Particulate organic matter (POM)

Particulate organic matter (POM) derives from the decomposition and fragmentation of
litter and other necromass. It can be formed from plant material, insect carcasses,
aggregates, fungal matter, etc. Generally, the particulates are of sufficient size that
their original source can still be identified. In most systems this is a pool with a
reasonably fast turnover rate (order of months). However, in heavily waterlogged soils
(i.e. peatlands) this pool turns over far more slowly and is a significant store of
carbon.

### Low molecular weight carbon (LMWC)

Low molecular weight carbon (LMWC) consists of molecules that are simple, soluble and
labile, i.e. those that are immediately utilisable by microbes. It is formed through the
microbially mediated breakdown of more complex carbon, but is also directly supplied by
plant roots. LMWC is commonly lost to leaching or microbial uptake. This pool turns
over rapidly (order of days).

### Mineral associated organic matter (MAOM)

Carbon can be protected from microbial activity by mineral association, whereby
mineral surfaces take up organic matter by adsorption, conferring chemical protection.
This pool turns over very slowly (order of years to decades) and so in most soils it is
the main form of (chemically) protected carbon.

### Microbial biomass

Microbial biomass accounts for a small fraction of total soil carbon.
This pool turns over rapidly (order of days) and only represents a
very small fraction of total soil carbon. However, microbes
are key drivers of soil carbon cycling. It is therefore very important to track
the size of the microbial biomass pool because a significant amount of carbon flows
through it, with microbial respiration being one of the major sources of carbon
loss from the system.

### Microbial necromass

When microbial cells die they break down and form the microbial necromass. This consists
of complex biochemicals that normally would be contained within cells, but are now
exposed directly to the soil environment. This pools turns over rapidly (order of days),
and is very small. However, it is important to track this pool as the biochemicals that
it represents rapidly bind to soil minerals, so the size of this pool can affect how
quickly new protected carbon is formed.

## Soil carbon inputs

### Plant inputs

Most plant inputs enter to the soil via the [litter model](./litter_theory.md), due to
litter mineralisation. A portion of this is assumed to have occurred due leaching of
simple compounds from the litter into the soil. This part of the litter mineralisation
flux gets added to the {term}`LMWC` pool, and is calculated by

$$I_L = C_l * M_C,$$

where $C_l$ is the fraction of litter carbon decomposition that happens by leaching and
$M_C$ is the total rate of carbon mineralisation from the litter. The remainder of the
litter mineralisation is assumed to be in a more complex form and gets added to the
{term}`POM` pool with rate

$$I_M = (1 - C_l) * M_C.$$

Plants also directly provide carbon to the soil in the form of root exudates. These root
exudates are simple carbohydrates, so this input flux is added to the {term}`LMWC` pool.

### Animal inputs

The animal model contains excrement and carcass pools which are available to scavengers.
A certain portion of these pools is assumed to periodically decay into the soil. As
breakdown is already implicitly modelled within the animal model, we assume that these
animal inputs to the soil go solely into the {term}`LMWC` pool.

## Exchanges between soil pools

### Microbial uptake and growth

Microbes take up {term}`LMWC` both as a source of energy and as a source of carbon.
These resources are then used to synthesis new biomass, replace cells that have died and
proteins that have degraded, and to produce extra-cellular enzymes. The net change in
the size of the microbial pool is given by

$$\frac{dM}{dt} = \lambda - d - P_E,$$

where $\lambda$ is the rate of new biomass synthesis, $d$ is the rate at which biomass
is lost to cell death and protein degradation, and $P_E$ is the rate at which enzymes are
produced.

### Enzyme mediated decomposition

Both {term}`POM` and {term}`MAOM` are broken down into {term}`LMWC` by
enzyme-mediated reactions. As mentioned above, these enzymes are produced by microbes,
and are pool specific (i.e. one enzyme class breaks down {term}`POM` and the other
breaks down {term}`MAOM`). The rate of these decomposition processes is given by

$$D_i = f_{T,r}*f_W*f_{p}*k_i*\frac{E_i*P_i}{f_{T,s}*f_{c}*K_i + P_i}$$

where $P_i$ is the concentration of the resource type $i$, $E_i$ is the concentration of
the relevant enzyme class, $k_i$ is the decomposition rate constant, $K_i$ is the
decomposition saturation constant, $f_{T,r}$ is a factor capturing the impact of
temperature on the process rate, $f_{T,s}$ is a factor capturing the impact of
temperature on the concentration at which the enzyme saturates, $f_W$ is a factor
capturing the impact of soil moisture on the process rate, $f_{p}$ is a factor capturing
the impact of soil pH on the process rate, and $f_{c}$ is a factor capturing the impact
of soil clay content on the concentration at which the enzyme saturates. Definitions of
these environmental factors can be found
[here](./environmental_links.md#environmental-effects-on-enzymes).

### Microbial turnover

The rate at which microbial biomass is lost to both cell death and protein degradation
($d$) is temperature dependent (the modelling of this temperature dependence is
described [here](./environmental_links.md#biomass-loss)). All of this losses get added
to the necromass pool. The breakdown of this necromass pool to form {term}`LMWC` is
modelled using linear kinetics as

$$D_n = k_d * N,$$

where $k_d$ is the rate constant for necromass breakdown and $N$ is the size of the
necromass pool. The sorption of necromass to soil minerals to form {term}`MAOM` is also
modelled using linear kinetics as

$$S_n = k_s * N,$$

where $k_s$ is the rate constant for necromass sorption. The ratio of $k_d$ and $k_s$
will be the same as the ratio between the amount necromass that becomes {term}`LMWC` and
the amount that becomes {term}`MAOM`.

### Mineral sorption and desorption

{term}`MAOM` can also be formed via sorption of {term}`LMWC`. The carbon associated with
the soil surface can also desorb, this leads to a decrease in the size of the
{term}`MAOM` pool and a corresponding production of {term}`LMWC`. We model both of these
processes using linear kinetics, the resulting net change in the size of the
{term}`LMWC` pool can be expressed as

$$\Delta L = K_d * M - K_s * L,$$

where $K_d$ is the rate constant for {term}`MAOM` desorption, $K_s$ is the rate constant
for {term}`LMWC` sorption, $M$ is the size of the {term}`MAOM` pool and $L$ is the size
of the {term}`LMWC` pool. Most {term}`MAOM` formation occurs via necromass sorption,
therefore the default value for $K_s$ is small relative to $k_s$.

### Leaching of soil carbon

Leaching of nutrients from the soil occurs when water passing downwards through the soil
carries dissolved nutrients away with it. By definition, any organic matter that is
simple enough to solubilise is included in the {term}`LMWC` pool, so this is the only
soil carbon pool to be affected by leaching. The expression we use to calculate leaching
rates can be found [here](./environmental_links.md#soil-nutrient-leaching-rate).
