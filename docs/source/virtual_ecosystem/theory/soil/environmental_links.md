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

# Environmental impacts on soil processes

Litter decay and soil nutrient transformations are both affected by environment. At the
most basic level these are impacts on the microbial components of the soil and litter
models, which then impact the models more broadly. There are three different ways that
these impacts are represented in the models. The rates of processes that are implicitly
driven by microbes can change, the growth rates of the different microbial groups can be
directly affected, or the enzymatic rates can be affected. Each of these cases will be
dealt with in detail below.

At present, the only environmental impact we represent that isn't mediated by microbes
is the the rate at which nutrients leach from the soil. As such, this process does not
fit into any of the cases mentioned already, and so it will be discussed in a separate
section.

## Changes to rates of implicitly microbially driven processes

The soil model explicitly represents the soil microbes involved in decomposition.
However, extending this representation to all the processes would be incredibly hard to
parameterise, so some processes are instead represented by empirically obtained
expressions that implicitly represent the actions of the microbial community. As these
processes are driven by microbes they are affected by environmental conditions, in
particular soil temperature and moisture.

### Litter decay temperature response

The decay rates of all classes of litter are affected by temperature. For the
above-ground pools, this temperature is simply the air temperature just above the soil
surface. For the below ground pools, the temperature is an average of the temperatures
for the biologically active soil layers. The "intrinsic" litter decay rates are altered
to capture the effect of temperature by multiplying them with a factor that takes the
following form

$$f(T) = \exp{\left(\gamma \frac{T - T_{\mathrm{ref}}}{T + T_{\mathrm{off}}}\right)},$$

where $T$ is the litter temperature, $T_\mathrm{ref}$ is reference temperature used to
establish "intrinsic" litter decay rates, $T_\mathrm{off}$ is an offset temperature, and
$\gamma$ is a parameter capturing how responsive litter decay rates are to temperature
changes.

### Litter decay moisture response

Breakdown rates for below-ground litter pools are significantly impacted by soil
moisture. In very dry soils, breakdown rates are extremely slow because microbial
movement is restricted from reaching the substrate to break it down. As soils get
wetter, microbial motility increases resulting in faster breakdown rates. However,
further increasing soil moisture makes oxygen less permeable in the soil, so after a
certain peak breakdown rates begin to decrease with increasing soil moisture as oxygen
becomes limiting. The "intrinsic" process rates are altered to capture the effect of
soil moisture by multiplying them with a factor that takes the following form

$$
A(\psi) = 1 - \left(
\frac{\log_{10}|\psi| - \log_{10}|\psi_{o}|}
{\log_{10}|\psi_{h}| - \log_{10}|\psi_{o}|}
\right)^\alpha,
$$

where $\psi$ is the soil water potential, $\psi_{o}$ is the "optimal" water potential at
which substrate breakdown is maximised, $\psi_{h}$ is the water potential at which
substrate breakdown stops entirely, and $\alpha$ is an empirically determined parameter
which sets the curvature of the response to changing soil water potential.

### Nitrification temperature factor

The rate of nitrification in the soil changes with temperature. We capture this effect
using an empirical function taken from {cite}`xu-ri_terrestrial_2008`, where the impact
of temperature on nitrifaction rate captured as

$$
f_{T,n}(T) = \left(\frac{T_m - T}{T_m - T_o}\right)^{s_n}
             * \exp{\left(s_n * \frac{T - T_o}{T_m - T_o}\right)},
$$

where $T_m$ is the maximum temperature that nitrification occurs at, $T_o$ is the
optimal temperature for nitrification, and $s_n$ is the sensitivity of nitrification to
changes in temperature.

### Nitrification moisture factor

The rate of nitrification in the soil also varies with soil moisture. In this case, we
use a function taken from {cite}`fatichi_mechanistic_2019` to capture this effect.
The factor capturing the impact of soil moisture on nitrification rate is calculated as

$$
f_{w,n}(S_e) = \frac{S_e * (1 - S_e)}{0.25},
$$

where $S_e$ is the effective saturation.

### Denitrification temperature factor

Denitrification rate is also impacted by temperature. To capture this we modify an
empirical expression provided in {cite}`xu-ri_terrestrial_2008`. This allows the impact
that temperature has on denitrification rate to be calculated as

$$
f_{T,d}(T) =
\begin{cases}
0, \quad T <= T_h \\
f_\infty * \exp{\left(-\frac{s_d}{T - T_h}\right)}, \quad T > T_h \\
\end{cases}
$$

where $f_\infty$ is the impact of the factor at infinite temperature, $s_d$ is the
(inverse) sensitivity of denitrification to changes in temperature and $T_h$ is the
temperature below which denitrification halts.

### Denitrification moisture factor

Soil moisture also effects the rate of denitrification. We capture this effect using a
function taken from {cite}`fatichi_mechanistic_2019`, which is expressed as

$$
f_{w,d}(S_e) = {S_e}^2
$$

where $S_e$ is the effective saturation.

## Environmental effects on enzymes

Many processes in the soil model are mediated by extra-cellular enzymes produced by the
microbial groups. The kinetics of these enzymes are modified by a wider range of
environmental factors: soil clay content, soil pH, soil temperature and soil moisture.
These environmental factors can change the maximum rates of the processes or
alternatively change the half saturation of the process. We will now discuss each of
these factors in detail.

### Impact of clay on enzyme saturation

Clay in the soil protects substrates from enzymatic activity, which increases enzyme
saturation constants. The factor capturing this increase is calculated as

$$f_{c} = P_b + P_c * c,$$

where $c$ is the clay proportion of the soil, $P_b$ is the basic protection that the
soil provides against enzymatic activity and $P_c$ is the rate at which that protection
increases with increasing clay content.

### Impact of pH on enzyme rate

pH values that lie outside the optimal range tend to inhibit microbial activities. We
capture this as

$$
f_p =
\begin{cases}
0, \quad pH < pH_\mathrm{min} \\
\frac{pH - pH_\mathrm{min}}{pH_l - pH_\mathrm{min}}, \quad
pH_\mathrm{min} < pH < pH_l \\
1, \quad pH_l < pH < pH_u \\
\frac{pH_\mathrm{max} - pH}{pH_\mathrm{max} - pH_u}, \quad
pH_u < pH < pH_\mathrm{max} \\
0, \quad pH > pH_\mathrm{max}
\end{cases}
$$

where $pH$ is the soil pH, $pH_\mathrm{min}$ is the minimum pH at which enzymatic
activity can occur, $pH_l$ is the lowest pH for which enzymatic activity is maximised,
$pH_u$ is the highest pH for which enzymatic activity is maximised, and
$pH_\mathrm{max}$ is the maximum pH at which enzymatic activity can occur.

### Impact of temperature on enzyme rate and saturation

:::{admonition} Future directions 🔭

The Arrhenius equation is a simple model for the impact of temperature on biological
rates. We use this equation as a simple initial approach to incorporating
temperature in the model, and anticipate deprecating it in favour of more refined models
in future.

:::

The thermal response of enzymatic rates and saturations is modelled using the Arrhenius
equation. The form of this equation is as follows

$$f(T) = \exp{\frac{-E_a}{R} * (\frac{1}{T} - \frac{1}{T_{\mathrm{ref}}})},$$

where $E_a$ is the activation energy of the process of interest, $R$ is the molar gas
constant, $T$ is the environmental temperature, and $T_{\mathrm{ref}}$ the reference
temperature.

### Impact of soil moisture on enzyme saturation

The response of enzymatic rates to changing soil water potential is modelled using the
same approach as for the below ground litter pools (described
[here](#litter-decay-moisture-response)).

## Direct environmental impacts on microbes

Environmental factors also directly impact the growth of the different microbial groups
in the model. The rate at which microbes can take up resources is affected by a wide
range of environmental conditions. The efficiency microbes can grow is also affected by
temperature, as is rate at which they lose biomass due to cell death and protein
degradation.

### Microbial uptake

The uptake of resources by microbes is effected by a wide range of environmental
factors, affecting both uptake rate and saturation. We use the same approach to
calculate the environmental impacts on uptake rate and saturation as was used for
enzymatic rate and saturation (described [here](#environmental-effects-on-enzymes)).

### Microbial growth efficiency

The efficiency of microbial growth is often expressed in carbon terms as a carbon use
efficiency (CUE). This is defined as the proportion of carbon used for the synthesis of
new biomass to the total amount of carbon taken up. This is an emergent property that
arises from a large number of underlying processes (e.g. basal respiration, DNA
synthesis efficiency, etc.), most of which would be expected to vary with temperature.
Carbon use efficiency usually does not increase exponentially with temperature,
therefore the Arrhenius model is rarely an appropriate model. Instead we use a simple
logistic model to describe the temperature dependence of carbon use efficiency

$$
\mathrm{logit}\left(\epsilon\right) =
\epsilon_{\mathrm{ref}} + \alpha * (T - T_{\mathrm{ref}}),
$$

where $\epsilon_{\mathrm{ref}}$ is the carbon use efficiency at the reference
temperature, $\alpha$ is the change in carbon efficiency with temperature, $T$ is the
environmental temperature and $T_{\mathrm{ref}}$ is the reference temperature. The logit
link function is used to ensure that carbon use efficiency $\epsilon$ is bound between 0
and 1 as it is a proportion.

### Biomass loss

The impact of temperature on the rate of biomass loss is assumed to follow the Arrhenius
equation, which is described in detail
[here](#impact-of-temperature-on-enzyme-rate-and-saturation).

## Soil nutrient leaching rate

Soil nutrient leaching occurs when the downwards movement of water though the soil
carries away dissolved nutrients with it. As such, this process only applies to the
soluble forms of nutrients, i.e. the simplest and most readily uptaken forms. To
calculate the leaching rate for a given solute, we first have to calculate the amount of
it that we would expect to find in a dissolved form using

$$D_i = C_i * N_i,$$

where $N_i$ is the density of solute $i$ in the soil and $C_i$ is the solubility
coefficient for solute $i$. The solubility coefficient represents the proportion of the
solute that you would expect to find in a dissolved form and ranges between zero and
one. We then need to know the rate at which the water column gets completely replaced,
this can be calculated as

$$\mu = J / W,$$

where $J$ is the rate of flow of water through the soil, and $W$ is the amount of water
contained in the water column. We can then combine the above to calculate the leaching
rate for substrate $i$ as

$$L_i = \mu * D_i.$$
