---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
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

# Microbial representation

The microbial groups we include are represented as separate carbon pools. These pools
can produce enzymes which drive many of the key processes in the soil model. Most of the
parameters related to the activity of each microbial group can be configured separately.
This includes their uptake rates for different resources, their turnover rates, their
stoichiometric ratios, their thermal responses, and details of the enzymes they produce.
The processes that microbial groups are involved in and the different functional groups
we represent in the model will now be explained in more detail.

## Microbial processes

Microbial activity is one of the biggest drivers of soil organic matter turnover, so it
is important to capture the underlying processes in detail. In our model, microbes take
up carbon, nitrogen and phosphorus (in organic and inorganic forms). This is then used
to synthesis new biomass, which can be used to replace lost biomass (from cell death and
cellular maintenance), to grow, to produce externally secreted enzymes or (in the case
of fungi) to produce reproductive bodies.

### Nutrient uptake and growth

In the model microbes can take up the following resources: carbon in the form of
{term}`LMWC`, inorganic nitrogen in the form of ammonium and nitrate, and inorganic
labile phosphorus. When microbes take up carbon they also take up organic nitrogen and
phosphorus with it (these fractions are termed {term}`DON` and {term}`DOP`,
respectively), so organic nutrient uptake is not tracked as a separate process. The
maximum uptake rate for each resource is found using

$$m_{i,j} = \frac{k_{i,j}*f_{T,r}*f_W*f_{p}*R_j*C_i}{R_j + f_{T,s}*K_{i,j}},$$

where $k_{i,j}$ is the rate constant for uptake of resource $j$ by microbial group $i$,
$C_i$ is the abundance of microbial group $i$, $R_j$ is the availability of resource
$j$, $K_{i,j}$ is the saturation constant for uptake of resource $j$ by microbial group
$i$, $f_{T,r}$ is a factor capturing the impact of temperature on the uptake rate,
$f_{T,s}$ is a factor capturing the impact of temperature on the concentration at which
the uptake saturates, $f_W$ is a factor capturing the impact of soil moisture on the
uptake rate, and $f_{p}$ is a factor capturing the impact of soil pH on the uptake rate.
These factors are all defined in the [soil-abiotic environment links documentation
page](./environmental_links.md#environmental-effects-on-enzymes).

The maximum rate that carbon can be incorporated into biomass is then found by
multiplying the [carbon use
efficiency](./environmental_links.md#microbial-growth-efficiency) by the maximum rate of
{term}`LMWC` uptake. This will only be the growth rate when the microbial group is
carbon limited (rather than nitrogen or phosphorus limited). Each microbial group has a
stoichiometry for new biomass, which is an weighted average of their cellular biomass
stoichiometric ratios and the stoichiometric ratios of the extracellular enzymes that
they produce. This is average is weighted by the fraction of new biomass allocation to
growth vs each type of enzyme production. The limitation that each nutrient places on
carbon assimilation is then found by multiplying the stoichiometric ratio for each
nutrient by the sum of the maximum uptake rates for all forms of the nutrient (organic
and inorganic). The actual growth rate is then found (following Liebig's law of the
minimum) as

$$G = min(G_C,G_N,G_P),$$

where $G_C$ is the maximum growth rate possible due to the availability of carbon,
$G_N$ is the maximum growth rate (in carbon terms) due to the availability of nitrogen,
and $G_P$ is the maximum growth rate (in carbon terms) due to the availability of
phosphorus.

Organic nutrients are preferentially taken up, this is because organic matter will
always be needed for growth as it contains all three potential limiting factors. Any
nutrient demand not met by organic uptake is met by the uptake of inorganic nutrients.
In the case of nitrogen, this inorganic uptake is split between ammonium and nitrate
based on the ratio of their maximum uptake rates. It's important to note that while the
maximum rate of organic nutrient uptake is determined by the product of maximum rate of
{term}`LMWC` uptake and the stoichiometry of the LMWC pool, the actual uptake rate can
be higher than the product of the **actual** rate of LMWC uptake and the pool
stoichiometry. This represents LMWC being taken up, nutrients being extracted, and then
surplus carbon being exuded.

Microbes can also acquire an excess of nutrients through organic matter uptake and need
to exude them. However, there are multiple forms in which these nutrients can be exuded
as. We assume that the fraction that gets returned in organic form can be estimated
based on the degree of carbon limitation as

$$L_C = \frac{G}{m_{i,c} * \epsilon_i},$$

where $m_{i,c}$ is the maximum uptake rate of carbon for microbial group $i$ and
$\epsilon_i$ is the carbon use efficiency for microbial group $i$. There isn't anything
mechanistic to base the split between ammonium and nitrate on, so instead we introduce a
(configurable) [ammonium mineralisation
proportion](virtual_ecosystem.models.soil.model_config.SoilConstants.ammonium_mineralisation_proportion)
constant to determine how nitrogen mineralisation is split between the two.

### Enzyme production

Microbial groups in the model can produce extra-cellular enzymes that drive soil
processes. Which enzymes are produced and the allocation to production of each type is
controlled by the parameterisation of the specific microbial functional groups. Enzyme
classes are differentiated by the substrate they break down (at present this can be
{term}`POM` or {term}`MAOM`) and by whether they were produced by bacteria or fungi. The
reason for splitting enzymes by source is that, due to their substantially larger
genomes, fungi can produce significantly more complex enzymes, which we feel is an
important difference to capture. Much like microbial functional groups, the keys
parameters of each enzyme class are individually configurable.

In the model, microbial groups allocate a (configurable) fraction of their synthesis of
new biomass to the production of each type of enzyme that they produce. This comes from
the synthesis of new biomass rather than net change in biomass so that enzymes are
actually produced when microbial populations are at steady-state. The abundance of
extra-cellular enzymes in the soil can also decline due to denaturation, with these
denatured enzymes being added to the soil necromass pool.

## Microbial functional groups

We include a total of four microbial functional groups in the model: bacteria,
saprotrophic fungi, arbuscular mycorrhizal fungi and ectomycorrhizal fungi. We
differentiate between bacteria and fungi because it's a major taxonomic division and so
should be expected to show meaningfully different responses to environmental change. We
treat saprotrophic and mycorrhizal fungi separately because they acquire carbon in a
very different manner. Finally, we split mycorrhizal fungi into the two most common
mycorrhizal types (ecto and arbuscular) because ectomycorrhizal fungi commit
substantially more resources to the production of enzymes. There are more microbial
groups that we could have included explicitly in the model (e.g. nitrogen fixing
bacteria, nitrifying bacteria, etc). However, for these groups there tends to be a real
lack of field data on the abundance of these groups and so we don't include them.

Details of processes that the model includes that are not shared between all
microbial functional groups are given below.

### Fungal fruiting

Fungal groups allocate a (configurable) fixed proportion of their synthesis of new
biomass to the production of fungal fruiting bodies. The stoichiometric ratios of these
bodies are lower than for soil fungal biomass, so producing them takes a proportionally
greater uptake of nutrients.

These fruiting bodies are made available for animal consumption (this process is tracked
with the animal model). Fungal fruiting bodies that aren't consumed decay back into the
soil in a labile organic form, i.e. as {term}`LMWC`, {term}`DON` and {term}`DOP`.

### Mycorrhiza

TODO - BUILD DOCS AND PROOF THIS WHOLE SECTION

Mycorrhizal fungi differ from both bacteria and saprotrophic fungi in that they cannot
use the forms of carbon that can be taken up from the soil to grow. Instead, they are
entirely dependent on their symbiotic plant partners for the carbon they need to grow.
Because of this mycorrhizal fungi are assumed to preferentially take up inorganic forms
of nutrients. They can take up organic matter if the availability of inorganic matter is
insufficient, but this is used solely for the acquisition of nutrients and the carbon
contained in this organic matter is returned to the soil as {term}`LMWC`. If the plant
supply of carbon exceeds the mycorrhizal fungi's ability to use it then the excess is
exuded into the soil (again as {term}`LMWC`).

In return for the carbon they depend on, mycorrhizal fungi supply nutrients to the
plants. We assume that mycorrhiza supply a fixed (but configurable) fraction of the
nutrients that they uptake to their plant partners. This is a fairly strong assumption,
as in reality mycorrhizal fungi should vary the amount of nutrients they supply to
plants based on the amount of carbon received, not just soil nutrient availability. We
hope that by using this assumption we can treat the outcome of the (incredibly) complex
eco-evolutionary involved in plant-mycorrhizal nutrient trading as a model parameter, to
be determined based on real world data.

At present, the soil model runs after the plants model (when running the standard set of
models). This means that the nutrients the plants receive were effectively supplied on
the previous time step. In many ways this lag is biologically realistic, as plants do
show delayed responses to changes in soil nutrient conditions. However it does mean that
an estimate of the nutrient supplied by the mycorrhizal fungi on the zeroth timestep is
needed in order to run the first plant model time step. This estimate is made based on
the initial soil conditions under the assumption that mycorrhizal fungi take up
nutrients at the maximum possible rate. This is almost certainly an overestimate, but
one that only really impact the initial time step of the simulation.

We include two different mycorrhizal groups in the soil model, ectomycorrhizal fungi and
arbuscular mycorrhizal fungi. The only difference between these groups are how they are
parametrised, with arbuscular mycorrhizal fungi investing far less in the production of
extracellular enzymes.
