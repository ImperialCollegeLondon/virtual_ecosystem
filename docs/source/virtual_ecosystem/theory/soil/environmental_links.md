# Environmental impacts on soil processes

TODO - Link to this in the overall theory page
TODO - Add intro

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

The decay rates for the two below-ground litter pools are also impacted by how wet the
soil is. In very dry soils decay rates are extremely slow, this is because microbial
movement is restricted so microbes struggle to reach litter fragments to decompose them.
As soils get wetter, microbial motility increases resulting in faster decay rates.
However, increasing soil moisture makes it harder for oxygen to permeate the soil, so at
a certain point litter decay rates begin to decrease with increasing soil moisture as
oxygen availability has become limiting. The "intrinsic" litter decay rates are altered
to capture the effect of soil moisture by multiplying them with a factor that takes the
following form

$$
A(\psi) = 1 - \left(
\frac{\log_{10}|\psi| - \log_{10}|\psi_{o}|}
{\log_{10}|\psi_{h}| - \log_{10}|\psi_{o}|}
\right)^\alpha,
$$

where $\psi$ is the soil water potential, $\psi_{o}$ is the "optimal" water potential at
which litter decay is maximised, $\psi_{h}$ is the water potential at which decay stops
entirely, and $\alpha$ is an empirically determined parameter which sets the curvature
of the response to changing soil water potential.
