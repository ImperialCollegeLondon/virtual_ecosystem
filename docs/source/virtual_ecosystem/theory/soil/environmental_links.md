---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

Litter decay and soil nutrient transformations are both affected by temperature. As the
soil model explicitly includes microbes, temperature effects many different processes in
the model, e.g. enzymatic rates and the carbon use efficiency of microbial growth.
Temperature is more straightforward in the litter model and just effects the decay rate
of each litter pool. Processes that take place underground are also affected by soil
moisture. For the soil moisture response, an empirical relationship is used for both
litter decay and soil organic matter breakdown.

:::{admonition} In progress 🛠️

The representation of soil microbial communities has still not been finalised. Once this
has happened this section of the documentation will be extended to detail the relevant
thermal responses.

:::

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
