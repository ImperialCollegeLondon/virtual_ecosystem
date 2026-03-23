---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
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

# The abiotic model implementation

```{warning}
The process-based abiotic model is currently the default abiotic model version in the
Virtual Ecosystem configuration; however, the model is still under development.
This page provides a summary of the current status and the directions in which we aim to
take the model development forward.

A known issue is that the `ve_example` simulation fails after approximately five time
steps. This occurs because the leaf area index in the understorey increases to
unrealistically high values, which in turn causes numerical instability in the surface
temperature update. Resolving this issue is a priority for future development.
```

## Required variables

The tables below show the variables that are required to initialise the abiotic model
and then update it at each time step.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        "AbioticModel", ["vars_required_for_init", "vars_required_for_update"]
    ),
    raw=True,
)
```

## Model overview

The abiotic model simulates the exchange of energy, water, and heat between the land
surface, vegetation canopy, soil, and atmosphere. These processes regulate
microclimate conditions that directly influence ecosystem dynamics.

To ensure numerical stability and capture sub-daily variability, the model operates on
a reconstructed **mean diurnal cycle**, derived from monthly mean input data.

## Temporal resolution strategy

### The mean diurnal cycle

Calculating abiotic processes at coarse temporal resolution (e.g. monthly) can introduce
numerical instability and obscure important sub-daily dynamics. To address this, the
model simulates a single representative (average) day for each month. From monthly mean
inputs, a full diurnal cycle is reconstructed, allowing processes to be resolved at
hourly time steps.

The resulting hourly values are then used to derive monthly means and ranges of state
variables required by other models.

### Diurnal cycle reconstruction

Monthly mean climate variables at reference height above the canopy are converted into
hourly values over a 24-hour period using simplified, physically motivated assumptions.

**Air temperature** follows a sinusoidal cycle, peaking in the early afternoon (~14:00).
The amplitude is defined by a prescribed daily temperature range (currently part of
the model configuration), which produces a smooth oscillation around the monthly mean.

**Incoming shortwave radiation** is distributed across daylight hours using a half-sine
curve which is zero at night and peaks at midday. The resulting hourly fractions are
normalised and used to distribute monthly shortwave absorption across hours, layers,
and grid cells.

```{note}
Daylength is estimated from month and latitude and is constrained between 6 and 18
hours. Sunrise and sunset are then calculated symmetrically around noon.

The mean latitude of the grid has to be provided to the model configuration. In the
future, this will be determined internally from the input model data projection and
extent.
```

**Relative humidity** is computed assuming constant atmospheric vapour pressure.
Saturation vapour pressure depends on temperature, actual vapour pressure is derived
from monthly mean humidity, and hourly humidity is computed from their ratio. Values are
constrained between 0 and 100%.

**Evapotranspiration** is distributed hourly proportional to absorbed radiation when
present and uniform when radiation is absent. **Soil evaporation** follows the same
approach, using total absorbed radiation across layers
to determine hourly scaling.

### Numerical workflow

At each Virtual Ecosystem model time step, a sequence of steps is executed as
illustrated in {numref}`abiotic_workflow`.

:::{figure} ../../_static/images/abiotic_workflow.svg
:name: abiotic_workflow
:alt: Abiotic workflow
:class: bg-primary
:width: 600px

Numerical workflow of the abiotic model, starting with initialisation (yellow), followed
by 24 runs of the hourly loop (green), and closed with post-processing (blue).
Static variables are variables that are updated by the abiotic model but held
constant during the diurnal cycle. This currently includes atmospheric pressure and
$\ce{CO2}$ and the wind profiles.
State variables refer to all variables that are updated hourly by the abiotic model.
This includes vertical profiles of air temperature, relative humidity, soil temperature,
and energy fluxes, for full list see [list of updated variables](#updated-variables).
The aggregation step at the end returns mean values of the representative day.
:::

## Energy balance framework

The exchange of energy between the Earth's surface or canopy and the surrounding
atmosphere involves five important categories of processes:

* *Absorption* and *emission* of electromagnetic radiation by the surface/canopy
* *Thermal conduction* of heat energy within the ground
* *Turbulent transfer* of heat energy towards or away from the surface within the
  atmosphere
* *Evaporation*, *transpiration*, and *condensation* of water
* *Primary productivity*

Each of these processes can be associated with an energy flux density, which is the rate
of transfer of energy normal to a surface of unit area (in $\mathrm{W\,m^{-2}}$).

The energy balance of a surface layer of finite depth and unit horizontal area can be
written as:

$$\frac{dQ}{dt} = R_n - G - H - \lambda E (- PP)$$

where each term is later expanded for the [canopy](#canopy-energy-balance), and
[soil surface](#soil-energy-balance).

**Variable definitions:**

$Q$:
Total heat energy stored in the surface layer.

$R_n$:
Net surface irradiance (commonly referred to as the net radiation). It
represents the gain of energy by the surface from radiation. It is a positive number
when it is towards the surface. This includes long- and shortwave radiation.

$G$:
Ground Heat Flux. It is the loss of energy by heat conduction through the
lower boundary. It is a positive number when it is directed away from the surface into
ground. The value at the surface is denoted $G_{0}$.

$H$:
Sensible Heat Flux. It represents the loss of energy by the
surface by heat transfer to the atmosphere. It is positive when directed
away from the surface into the atmosphere.

$\lambda E$:
Latent Heat Flux. It represents a loss of energy from the
surface due to evaporation and/or transpiration. ($\lambda$  is the specific latent heat
of evaporation,
units $\mathrm{J\,kg^{-1}}$ and E is the evaporation rate, with units
$\mathrm{kg\,m^{-2}\,s^{-1}}$).

$PP$:
Primary productivity, represents the energy that plants use to photosynthesize.

## Radiative forcing

### Net radiation

The net radiation $R_n$ ($\mathrm{W\,m^{-2}}$) at the leaf or soil surface is
calculated as:

$$R_n = S_0 \cdot (1 - \alpha) + LW_{down} - \epsilon_{s} \sigma T^{4}$$

where:

$S_0$:
Incoming shortwave radiation ($\mathrm{W\,m^{-2}}$)

$\alpha$:
Surface albedo, the fraction of shortwave radiation reflected (–)

$LW_{down}$:
Incoming longwave radiation ($\mathrm{W\,m^{-2}}$)

$\epsilon_s$:
Surface emissivity, the efficiency of longwave radiation emission (–)

$\sigma$:
Stefan–Boltzmann constant ($5.67 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$)

$T$:
Surface temperature (°C)

Shortwave radiation $S_0$ and longwave radiation $LW_{down}$ are progressively
attenuated through the canopy, as leaves absorb a portion of the incoming radiation.

```{Note}
In the future, we aim to implement a more advance radiative transfer scheme, including:
- the effects of topography on sun angle, and
- the contribution of diffuse radiation.
```

## Canopy processes

### Canopy energy balance

Given that the time increments of the model are one hour,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly
{cite:p}`maclean_microclimc_2021`.

Under steady-state, the balance equation $\frac{dQ}{dt}$ for the leaves in each canopy
layer is as follows:

```{math}
    & \frac{dQ}{dt} \\
    & = R_{n} - H_l - \lambda E_l (- PP)\\
    & = R_{\text{abs}} - \epsilon_{l} \sigma T_{l}^{4} -
    \frac{\rho_a c_p}{r_a}(T_{l} - T_{a})
    - \lambda g_{v} \frac {e_{l} - e_{a}}{p_{a}} (- PP)\\
    & = 0
```

where:

$R_{\text{abs}}$:
Shortwave and longwave radiation absorbed by the canopy ($\mathrm{W\,m^{-2}}$)

$R_{\text{em}}$:
Emitted longwave radiation from the canopy ($\mathrm{W\,m^{-2}}$)

$H_{l}$:
Sensible heat flux from the canopy to the air ($\mathrm{W\,m^{-2}}$)

$\lambda E_{l}$:
Latent heat flux associated with transpiration from the canopy to the air
($\mathrm{W\,m^{-2}}$)

$\epsilon_{l}$:
Emissivity of the leaf (-), typically close to 1

$\sigma$:
Stefan–Boltzmann constant ($5.67 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$)

$T_{l}$:
Temperature of the leaf (°C)

$T_{a}$:
Temperature of the air surrounding the leaf (°C)

$\lambda$:
Latent heat of vapourisation of water ($\mathrm{kJ\,kg^{-1}}$)

$e_{l}$:
Effective vapour pressure of the leaf (kPa)

$e_{a}$:
Vapour pressure of air (kPa)

$p_{a}$:
Atmospheric pressure (kPa)

$g_{v}$:
Conductance for vapour loss from the leaves ($\mathrm{mol\,m^{-2}\,s^{-1}}$) as a
function of the stomatal conductance $g_{c}$ ($\mathrm{s\,m^{-1}}$)

$PP$:
Primary productivity, represents the energy that plants use to photosynthesize

### Temperature solution

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. This method estimates updated canopy and air temperatures
by linearizing the canopy energy balance and applying a Newton iteration. This
approach accounts for the strong temperature dependence of radiative losses and ensures
numerical stability in canopy energy balance closure, following the method described by
{cite:t}`yang_scope_2021`. The goal is to find the leaf temperature that closes the
energy balance at the leaf surface, see previous section.

#### Newton Linearization

To iteratively solve for the leaf temperature that satisfies the energy balance
$\frac{dQ}{dt}$ = 0, we use the Newton method:

```{math}
T_l^{\text{new}} = T_l^{\text{old}} + W \cdot
\frac{\frac{dQ}{dt}}{\frac{\partial \frac{dQ}{dt}}{\partial T_l^{\text{old}}}}
```

where:

$T_l^{\text{old}}$:
Current estimate of leaf temperature (°C)

$T_l^{\text{new}}$:
Updated estimate of leaf temperature (°C)

$W$:
Step-size weighting factor (–), typically between 0.1 and 1

$\frac{\partial \frac{dQ}{dt}}{\partial T_l^{\text{old}}}$:
The first derivative of the energy balance with respect to temperature

This update adjusts the leaf temperature proportionally to the energy imbalance, scaled
by the sensitivity of that imbalance to temperature. The weighting factor $W$ ensures
numerical stability, especially in conditions where the balance is sensitive to small
temperature changes.

#### Derivative of energy balance

The temperature derivative of the energy balance as formulated above
is calculated analytically as:

```{math}
\frac{\partial \frac{dQ}{dt}}{\partial T_l^{\text{old}}} =
\frac{\rho_a c_p}{r_a} +
\frac{\rho_a \Delta_v}{r_a + r_s} \lambda +
4 \epsilon_l \sigma (T_l^{\text{old}} + 273.15)^3
```

where:

$\rho_a$:
Air density ($\mathrm{kg\, m^{-3}}$)

$c_p$:
Specific heat capacity of air ($\mathrm{J\, kg^{-1}\,K^{-4}}$)

$r_a$:
Aerodynamic resistance of the canopy ($\mathrm{s\, m^{-1}}$)

$r_s$:
Stomatal resistance ($\mathrm{s\, m^{-1}}$)

$\Delta_v$:
Slope of the saturation vapour pressure curve ($\mathrm{kPa\, K^{-1}}$)

$\lambda$:
Latent heat of vapourisation of water ($\mathrm{kJ\, kg^{-1}}$)

$\epsilon_l$:
Leaf emissivity (-)

$\sigma$:
Stefan–Boltzmann constant ($5.67 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$)

$T_l^{\text{old}}$:
Previous estimate of leaf temperature (°C, converted to K in the radiation term)

This derivative represents the rate at which each energy loss term changes with leaf
temperature: convective, evaporative, and radiative. It ensures that the update step
accounts for the nonlinear temperature dependence, especially of radiative loss.

### Air-canopy temperature coupling

After updating the canopy temperature, we update the air temperature in the
adjacent canopy layer to reflect its coupling with the leaf temperature following
{cite:t}`bonan_climate_2019`:

The sensible heat flux between canopy and air is

$$H = \frac{\rho_{a} c_{p}}{r_{a}}(T_{l} - T_{a})$$

and the air temperature evolves as

$$T_{a}^{\text{new}} = T_{a}^{\text{old}} + \frac{H}{\rho_{a} c_{p} z}$$

where:

$T_a$:
Air temperature, (°C)

$z$:
Thickness of the air layer we are updating, (m)

In the understorey vegetation, we add the contribution of soil sensible heat flux and
longwave emission to the equation.

Finally, we consider vertical mixing between all vegetation layers and heat is
transferred to the air above the canopy.

```{note}
Advection of heat above the canopy is currently not implemented as everything is
removed with time interval >= 1h and horizontal transfer is not considered.
```

## Soil processes

### Soil energy balance

The energy balance at the soil surface is solved by partitioning net radiation $R_N$
into different fluxes.

The **sensible heat flux** from the soil surface is given by:

$$H_{s} = \frac {\rho_{a} c_{p} (T_{s} - T_{a})}{r_{a}}$$

where:

$T_s$:
Soil surface temperature (°C)

$T_a$:
Air temperature in the bottom atmospheric layer (°C)

$r_a$:
Aerodynamic resistance of the soil surface ($\mathrm{s\,m^{-1}}$)

$\rho_{a}$:
Air density ($\mathrm{kg\,m^{-3}}$)

$c_{p}$:
Specific heat capacity of air at constant pressure ($\mathrm{J\,kg^{-1}\,K^{-1}}$)

The aerodynamic resistance of the soil surface is given by
{cite:p}`barton_parameterization_1979`:

$$r_{a} = \frac{1}{C_{E} u}$$

where:

$u$:
Horizontal wind speed at the bottom air layer ($\mathrm{m\,s^{-1}}$)

$C_E$:
Drag coefficient for evaporation (–)

The **latent heat flux** is derived by conversion of surface evaporation as
calculated by the hydrology model.

The **ground heat flux** is calculated as the residual of the energy balance at the
soil surface plus the conductive heat from the understorey layer:

$$G = R_{n} - H_{s} - \lambda E_{s} + G_{u}$$

### Soil temperature update

After the energy fluxes at the land surface have been partitioned, we simulate how heat
is transported vertically through the soil profile by updating the temperature of each
soil layer over time. This is done using an explicit finite-difference approach, which
numerically solves the one-dimensional heat diffusion equation. The method accounts for
thermal diffusivity and the net ground heat flux to calculate temperature changes at
each soil depth.

The **soil thermal diffusivity** $\alpha$ ($\mathrm{m^{2}\,s^{-1}}$) determines the rate
at which heat is conducted through the soil. It is defined as:

$$\alpha = \frac{k}{\rho_s c_s}$$

where:

$k$:
Soil thermal conductivity ($\mathrm{W\,m^{-1}\,K^{-1}}$), indicating how
  easily heat moves through soil

$\rho_s$:
Soil bulk density ($\mathrm{kg\,m^{-3}}$), including solids and pore spaces, currently
constant across all grid cells and layers

$c_s$:
Soil specific heat capacity ($\mathrm{J\,kg^{-1}\,K^{-1}}$), the energy required to
raise the temperature of 1 kg of soil by 1 K.

#### Temperature Update Scheme

Let $T_i^t$ represent the temperature (°C) of the $i^{\text{th}}$ soil layer at time
$t$. The soil column is discretized into $n$ layers, each of thickness $\Delta z$ (m),
and time advances in steps of $\Delta t$ (s).

**Top layer update** (surface boundary condition):

The topmost layer ($i = 0$) is updated using the net ground heat flux $G$
($\mathrm{W\,m^{-2}}$):

$$T_0^{t+\Delta t} = T_0^t + \left(\frac{\Delta t}{\rho c \Delta z}\right) G$$

**Interior layers update**:

Each interior layer ($i = 1, \dots, n-2$) exchanges heat with adjacent layers following
the diffusion equation:

```{math}
\begin{aligned}
T_i^{t+\Delta t} =
& T_i^t + (\frac{\Delta t}{\Delta z^2}) \alpha (T_{i+1}^t - 2T_i^t + T_{i-1}^t)
\end{aligned}
```

This term approximates vertical conduction using the second spatial derivative of
temperature.

**Bottom layer update** (no-flux boundary condition):

A zero heat flux is assumed at the bottom boundary ($i = n-1$), so the bottom layer only
exchanges heat with the layer above:

```{math}
\begin{aligned}
T_{n-1}^{t+\Delta t} =
& T_{n-1}^t + (\frac{\Delta t}{\Delta z^2}) \alpha (T_{n-2}^t - T_{n-1}^t)
\end{aligned}
```

## Atmospheric moisture

Evapotranspiration and soil evaporation are initially provided in millimetres of water
depth. These values are converted to a mass of water per unit volume of air
($\mathrm{kg\, m^{-3}}$) then added to the relevant atmospheric
layers: canopy evapotranspiration is distributed across the layers surrounding the
vegetation, while soil evaporation is added to the lowest layer near the surface.

Using the updated water mass, specific humidity is recalculated for each layer by
dividing the total water mass by the volume of air in that layer. Then, the new specific
humidity is vertically mixed between layers and ventilated at the top of the canopy to
make sure that water does not accumulate unrealistcally in the canopy but stays connected
to the atmosphere above. To maintain physical realism, additional redistribution steps
are taken where necessary until all layers in the canopy are within realistic bounds.
The resulting change in specific humidity is then used to compute the new vapour pressure
, relative humidity, and vapour pressure deficit.

```{note}
Advection of water above the canopy is currently not implemented as everything is
removed with time interval >= 1h and horizontal transfer is not considered.
```

## Turbulence and wind

The wind profile determines the exchange of heat, water, and $\ce{CO_{2}}$ between soil
and atmosphere below the canopy as well as the exchange with the atmosphere above the
canopy. The wind speed above the canopy is provided as an input to the model at each
time step.

This section describes the implementation of wind profiles within the canopy, friction
velocity, aerodynamic resistance, vertical mixing rates, and ventilation rate used to
model turbulent mixing with air above the canopy.

The **zero-plane displacement height** $d$ (m) is a concept used in micrometeorology to
describe the flow of air near the ground or over surfaces like a forest canopy or crops.
It represents the height above the actual ground where the wind speed is theoretically
reduced to zero due to the obstruction caused by the roughness elements (like trees
or buildings).

$d$ is estimated as a function of canopy height $h_{c}$ (m), leaf area index $LAI$
 $\mathrm{m\,m^{-1}}$, and a scaling parameter $\beta_{d}$ after
 {cite:t}`maclean_microclimc_2021`:

```{math}
d = h_c \left( 1 - \frac{1 - \exp\left(-\sqrt{\beta_d \cdot \text{LAI}}\,\right)}
{\sqrt{\beta_d \cdot \text{LAI}}} \right)
```

This ensures $d \to 0$ in the absence of vegetation and approaches a fraction of
canopy height in dense vegetation.

The **roughness length** $z_0$ (m) determines the height above the ground where the wind
speed theoretically becomes zero under neutral atmospheric conditions. It is influenced
by the drag imposed by both the substrate and the vegetation canopy. The roughness
length is computed as (after {cite:t}`maclean_microclimc_2021`):

$$z_{0} = (h_c − d) exp⁡(−\kappa \frac{1}{R} − C_d)$$

with

$$R = \sqrt{C_s + \frac{C_r LAI}{2}}$$

where $C_{s}$ is the substrate surface roughness length, $C_{r}$ is the roughness
element (vegetation) drag coefficient, $C_{d}$ is the roughness sublayer depth parameter,
$\kappa$ is the von Karman constant, and $LAI$ is the leaf area index
($\mathrm{m\,m^{-1}}$).

The **wind speed** ($\mathrm{m\,s^{-1}}$) at any height $z$ (m) is computed using the
logarithmic wind profile under neutral conditions (based on
{cite:t}`holmes_wind_2019`):

```{math}
u(z) = u_{\text{ref}} \cdot \frac{\ln\left( \frac{z - d}{z_0} \right)}
{\ln\left( \frac{z_{\text{ref}} - d}{z_0} \right)}
```

where $u(z)$ is wind speed at height $z$, $u_{\text{ref}}$ is reference wind speed at
height $z_{\text{ref}}$, $d$ is the zero-plane displacement height, $z_{0}$ is the
roughness length.

Minimum wind speed is enforced below the canopy to avoid unrealistically low turbulent
transport.

**Friction velocity** $u_{*}$ ($\mathrm{m\,s^{-1}}$) quantifies the shear stress
imposed by wind near the surface and is calculated from the wind speed profile
(based on {cite:t}`holmes_wind_2019`):

$$u_* = \frac{\kappa \cdot u(z)}{\ln\left( \frac{z - d}{z_0} \right)}$$

Friction velocity is used to estimate turbulence strength and mixing coefficients.

The **aerodynamic resistance** $r_a$ ($\mathrm{s\,m^{-1}}$) quantifies the resistance to
vertical transfer of scalars (heat, water vapour) between surface and air
(based on {cite:t}`jansson_coupled_2004`):

```{math}
r_a = \frac{1}{g_a} = \frac{\left[ \ln\left( \frac{z - d}{z_0} \right) \right]^2}
{\kappa^2 \cdot u(z)}
```

Separate values are computed for:

* Canopy resistance, using wind speeds within the canopy layer.
* Soil resistance, passed as an external input from the hydrology model.

```{note}
We currently distinguish between daytime and night time values or aerodynamic resistance
. The calculation above are true for daytime conditions; during nighttime, values are
set to a constant value which can be defined in the model configuration. This will be
updated once the nighttime wind speed can be calculated reliably.
```

The **eddy diffusivity** or **turbulent mixing coefficients** for heat ($k_H$) and
momentum ($k_M$) ($\mathrm{m^{2}\,s^{-1}}$) are used to mix water and energy in the
canopy. Inside the canopy, turbulence is strongly damped by vegetation drag, and a
simple linear profile like used for the top of the canopy like
$k_{H,M} = \kappa u^{*}(z-d)$ {cite:p}`raupach_coherent_1996`
does not match observed eddy diffusivity well. Instead, empirical profiles based on
measurements are used, and these often take parabolic or other non-linear forms like:

$$k_{H,M}(z)=\kappa u^{*}z(1-zh)^{2}$$

where $\kappa$ is the von Karman constant (dimensionless), $u_{*}$ is
the friction velocity ($\mathrm{m\,s^{-1}}$), $z$ is the height (m) for which
coefficients are calculated, and $h_c$ is the canopy height (m).

This particular form goes to zero at both z=0 and z=h and peaks somewhere within the
canopy.

The **ventilation rate** $v$ represents the rate of air exchange above the
canopy and is defined as (after {cite:t}`wolfe_forest_2011`):

$$v = \frac{1}{r_a \cdot h}$$

Where $r_a$ is the aerodynamic resistance from the top canopy layer and $h$ is the
vertical scale of exchange, or characteristic height, here canopy height (m).

This rate is used to estimate convective removal of heat and water vapour from the
canopy.

## Updated variables

The table below shows the complete set of model variables that are updated at each model
step.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(generate_variable_table("AbioticModel", ["vars_updated"]), raw=True)
```
