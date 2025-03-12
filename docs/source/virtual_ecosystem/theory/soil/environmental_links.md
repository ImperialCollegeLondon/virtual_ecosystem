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

# Environmental impacts on soil processes

Litter decay and soil nutrient transformations are both affected by environment. As the
soil model explicitly includes microbes, temperature effects many different processes in
the model, e.g. enzymatic rates and the carbon use efficiency of microbial growth.
Temperature is more straightforward in the litter model and just effects the decay rate
of each litter pool. Processes that take place underground are also affected by soil
moisture. For the soil moisture response, an empirical relationship is used for both
litter decay and soil organic matter breakdown. For the enzymes in the soil model, their
action is also affected by soil pH and clay fraction. Finally, the rate at which
nutrients leach from the soil is affected by the rate at which water flows downwards
through the soil. We will now describe each of these in more detail.

## Microbial response to temperature

Temperature is one of the most significant drivers of microbial processes. In the soil
model, two different approaches are taken to model the effects of temperature on
microbial process rates. While most processes are modelled using the Arrhenius equation,
a different approach is taken to modelling the efficiency of microbial growth.

### Arrhenius equation

:::{admonition} Future directions 🔭

The Arrhenius equation is a simple model for the impact of temperature on biological
rates. We are using this equation as a simple initial approach to incorporate
temperature in the model, and anticipate deprecating it in favour of more refined models
in future.

:::

We model the thermal variation of the following processes using the Arrhenius equation:

* microbial biomass loss
* microbial uptake rate
* microbial uptake saturation
* enzyme rate
* enzyme saturation

The form of the equation is as follows

$$f(T) = \exp{\frac{-E_a}{R} * (\frac{1}{T} - \frac{1}{T_{\mathrm{ref}}})},$$

where $E_a$ the activation energy of the process of interest, $R$ is the molar gas
constant, $T$ is the environmental temperature, and $T_{\mathrm{ref}}$ the reference
temperature.

### Temperature impact on microbial growth efficiency

TODO - When the CUE pull request is in this section will have to be updated

The efficiency of microbial growth is often expressed in carbon terms as a carbon use
efficiency. This is defined as the ratio of carbon used for the synthesis of new biomass
to the total amount of carbon taken up. This is an emergent property that arises from a
large number of underlying processes (e.g. basal respiration, DNA synthesis efficiency,
etc), most of which would be expected to vary with temperature. Because of this carbon
use efficiency does not follow anything like an exponential increase with temperature,
and so the Arrhenius model is not an appropriate model to use. Instead we use a simple
linear model to calculate carbon use efficiency

$$\epsilon = \epsilon_{\mathrm{ref}} - \alpha * (T - T_{\mathrm{ref}}),$$

where $\epsilon_{\mathrm{ref}}$ is the carbon use efficiency at the reference
temperature, $\alpha$ is the change in carbon efficiency with temperature, $T$ is the
environmental temperature and $T_{\mathrm{ref}}$ is the reference temperature.

## Soil moisture response

Breakdown rates for soil organic matter and breakdown rates for the below-ground litter
pools are both impacted by how wet the soil is. In very dry soils rates are extremely
slow, this is because microbial movement is restricted so microbes struggle to reach
the substrate to break it down. As soils get wetter, microbial motility increases
resulting in faster breakdown rates. However, increasing soil moisture makes it harder
for oxygen to permeate the soil, so at a certain point breakdown rates begin to
decrease with increasing soil moisture as oxygen availability has become limiting. The
"intrinsic" process rates are altered to capture the effect of soil moisture by
multiplying them with a factor that takes the following form

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

## Litter decay temperature response

The decay rates of all classes of litter are effected by temperature. For the
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

## Environmental effects on enzymes

Enzyme mediated processes in the soil are effected by a wide range of environmental
factors: soil clay content, soil pH, soil temperature and soil moisture. These
environmental factors can change the maximum rates of the processes or alternatively
change the half saturation of the process. We will now discuss each of these factors in
detail.

### Impact of clay on enzyme saturation

Clay in the soil protects substrates from enzymatic activity, which increases enzyme
saturation constants. The factor capturing this increase is calculated as

$$f_{c} = P_b + P_c * c,$$

where $c$ is the clay proportion of the soil, $P_b$ is the basic protection that the
soil provides against enzymatic activity and $P_c$ is the rate at which that protection
increases with increasing clay content.

### Impact of pH on enzyme rate

pH values that lie outside the optimal range tend to inhibit microbial activities. We
capture this as a factor that decreases maximum rate, it is calculated as

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

The response of both enzyme rate and enzyme saturation to changing temperature is
modelled using an Arrhenius function (see [here](#arrhenius-equation) for details).

### Impact of soil moisture on enzyme saturation

The response of enzymatic rates to changing soil water potential is modelled using the
same approach as for the below ground litter pools (described
[here](#soil-moisture-response)).

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
