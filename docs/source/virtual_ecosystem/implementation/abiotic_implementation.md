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
```

## Required variables

The tables below show the variables that are required to initialise the abiotic model
and then update it at each time step. Please check also the [guide for pre-processing
climate data](../../using_the_ve/model_details/abiotic/climate_data_guide.md).

<!-- markdownlint-disable-next-line MD033-->
- <a
  href="../../using_the_ve/variables/variables.html?models=abiotic&roles=vars_required_for_init">Variables
  required to initialise the abiotic model.</a>

<!-- markdownlint-disable-next-line MD033-->
- <a
  href="../../using_the_ve/variables/variables.html?models=abiotic&roles=vars_required_for_update">Variables
  required to update the abiotic model.</a>

## Model overview

The exchange of energy between the Earth's surface or canopy and the surrounding
atmosphere involves five important categories of processes:

- *Absorption* and *emission* of electromagnetic radiation by the surface/canopy
- *Thermal conduction* of heat energy within the ground
- *Turbulent transfer* of heat energy towards or away from the surface within the
  atmosphere
- *Evaporation*, *transpiration*, and *condensation* of water
- *Primary productivity*

Each of these processes can be associated with an energy flux density, which is the rate
of transfer of energy normal to a surface of unit area (in $\mathrm{W\,m^{-2}}$).

The energy balance of a surface layer of finite depth and unit horizontal area can be
written as:

$$\frac{dQ}{dt} = R_n - G - H - \lambda E (- PP)$$

where each term is later expanded for the [canopy](#canopy-energy-balance),
[understorey](#understorey-energy-balance), and [soil surface](#soil-energy-balance).

**Variable definitions:**

$Q$:
Total heat energy stored in the surface layer.

$R_n$:
Net surface irradiance (commonly referred to as the net radiation). It
represents the gain of energy by the surface from radiation. It is a positive number
when it is towards the surface.

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

```{note}
Calculating abiotic processes at coarse time scales can lead to numerical instability,
so the abiotic model uses an equilibrium assumption and where required, the integration
interval is 1 hour.

The outputs returned by the abiotic model are therefore equilibrium values for that
representative hour. A planned future improvement is to allow true hourly input, so the
model can capture full diurnal cycles and return time-averaged values of key variables.
```

### Net radiation

The current representation of the radiation balance is limited to the reflection and
absorption of direct downward shortwave radiation and the emission of longwave radiation
as part of the surface energy balance.

The net radiation $R_n$ ($\mathrm{W\,m^{-2}}$) at the leaf or soil surface is
calculated as:

$$R_n = S_0 \cdot (1 - \alpha) - \epsilon_{s} \sigma T^{4}$$

where:

$S_0$:
Incoming shortwave radiation ($\mathrm{W\,m^{-2}}$)

$\alpha$:
Surface albedo, the fraction of shortwave radiation reflected (–)

$\epsilon_s$:
Surface emissivity, the efficiency of longwave radiation emission (–)

$\sigma$:
Stefan–Boltzmann constant ($5.67 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$)

$T$:
Surface temperature (°C)

Shortwave radiation $S_0$ is progressively attenuated through the canopy, as leaves
absorb a portion of the incoming radiation.

```{Note}
In the future, we aim to implement a full diurnal cycle of incoming radiation, including:
- the effects of topography on sun angle, and
- the contribution of diffuse radiation.
```

### Canopy energy balance

Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly
{cite:p}`maclean_microclimc_2021`.
(For applications where very fine-temporal resolution data might be needed, heat and
vapour exchange must be modelled as transient processes, and heat storage by the canopy,
and the exchange of heat between different layers of the canopy, must be considered
explicitly, see {cite:t}`maclean_microclimc_2021`. This is currently not implemented.)

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
Shortwave radiation absorbed by the canopy, equivalent to $S_0 (1-\alpha)$
($\mathrm{W\,m^{-2}}$)

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

### Air and canopy temperature update

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

#### Air Temperature Coupling

After updating the canopy temperature, we update the air temperature in the
adjacent canopy layer to reflect its coupling with the leaf temperature following
{cite:t}`bonan_climate_2019`:

The sensible heat flux between canopy and air is

$$H = \frac{\rho_a c_p}{r_a}(T_{l} - T_{a})$$

and the air temperature evolves as

$$T_{a}^{\text{new}} = T_{a}^{\text{old}} + \frac{H \Delta t}{\rho_a c_p z}$$

where:

$T_a$:
Air temperature, (°C)

$z$:
Thickness of the air layer we are updating, (m)

Finally, we consider vertical mixing between layers (including the understorey layer
described in the following section) and heat is transferred to the air above the canopy.

```{note}
Advection of heat above the canopy is currently not implemented as everything is
removed with time interval >= 1h and horizontal transfer is not considered.
```

### Understorey energy balance

The understorey vegetation layer as currently implemented in the Virtual Ecosystem
modifies water and energy exchange between the soil and the air above. It intercepts a
fraction of throughfall, blocks most of the incoming radiation and reduces soil
evaporation. The energy balance of this layer differs from that of the
canopy because the understorey is structurally different and has therefore a
different structural and functional traits (e.g., aerodynamic resistance,
density).

Importantly, due to the understorey's density and proximity to the soil surface, we need
to account for heat conductance into the soil. This convective heat flux, $G_{u}$, is
later added to the soil energy balance.

```{note}
Moisture dynamics within the understorey layer are not currently represented.
```

#### Understorey temperature update

The understorey energy balance follows the heat and moisture framework of
{cite:t}`ogee_a_forest_2002`, extended to represent understorey vegetation as a mixture
of leaves and air rather than a compact litter layer.

The understorey temperature evolves according to

```{math}
\frac{\delta T_{u}}{\delta t}
= \frac{R_{n,0} - H_{0} - \lambda E_{0} - G_{u}}{c_{u} z_{u}}
```

where the conductive heat flux into the soil is

$$G_{u} = -(\lambda_{g} \lambda_{u})^{0.5} \frac{T_{s} - T_{u}}{z_{u}}$$

and the effective volumetric heat capacity of the understorey is

$$c_{u} = (\frac{LAI \cdot LMA}{z_{u}} c_{l} + c_{pv}) z_{u}$$

where:

$T_{u}$:
Understorey temperature (°C)

$T_{s}$:
Topsoil temperature (°C)

$R_{n,0}$:
Net radiation above the understorey ($\mathrm{W\,m^{-2}}$)

$H_{0}$:
Sensible heat flux above understorey ($\mathrm{W\,m^{-2}}$)

$\lambda E_{0}$:
Latent heat flux above understorey ($\mathrm{W\,m^{-2}}$)

$G_{u}$:
Conductive heat flux between understorey and soil ($\mathrm{W\,m^{-2}}$)

$\lambda_{u}$:
Understorey thermal conductivity ($\mathrm{W\,m^{-1}},K^{-1}$)

$\lambda_{s}$:
Soil surface thermal conductivity ($\mathrm{W\,m^{-1}},K^{-1}$)

$LAI$:
Leaf area index $\mathrm{m\,m^{-1}}$

$LMA$:
Leaf mass per area $\mathrm{kg\,m^{-2}}$

$c_{l}$:
Leaf specific heat capacity ($\mathrm{J\,kg^{-1}},K^{-1}$)

$c_{u}$:
Understorey specific heat capacity ($\mathrm{J\,kg^{-1}},K^{-1}$)

$c_{pv}$:
Volumetric heat capacity of air ($\mathrm{J\, m^{-3}\,K^{-1}}$)

$z_{u}$:
Thickness of understorey layer (m)

#### Understorey air temperature coupling

After updating the understorey temperature, we update the temperature of the
near-surface air using the same method as described for the canopy air temperature
{cite:p}`bonan_climate_2019`:

The sensible heat flux between understorey and air is

$$H_{u} = \frac{\rho_{a} c_{p}}{r_{a}}(T_{u} - T_{a,u})$$

and the air temperature evolves as

$$T_{a,u}^{\text{new}} = T_{a,u}^{\text{old}} + \frac{H_{u} \Delta t}{\rho_{a} c_{p} z_{u}}$$

where:

$T_{a,u}$:
Air temperature (°C)

### Soil energy balance

The `models.abiotic.energy_balance` submodule determines the energy balance at the
soil surface by partitioning net radiation $R_N$ into different fluxes.

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

$$G = R_n - H_s - \lambda E_s + G_{u}$$

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

#### Update of atmospheric moisture

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

### Wind

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

- Canopy resistance, using wind speeds within the canopy layer.
- Soil resistance, passed as an external input from the hydrology model.

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

## Generated variables

The calculations described above result in the following variables being calculated and
saved within the data object, and then updated

<!-- markdownlint-disable-next-line MD033-->
- <a
  href="../../using_the_ve/variables/variables.html?models=abiotic&roles=vars_populated_by_init">Variables
  generated by abiotic model initialisation.</a>

<!-- markdownlint-disable-next-line MD033-->
- <a
  href="../../using_the_ve/variables/variables.html?models=abiotic&roles=vars_populated_by_first_update">Variables
  generated by the first abiotic model update.</a>

## Updated variables

The link below provides the complete set of model variables that are updated at each model
step.

<!-- markdownlint-disable-next-line MD033-->
- <a
  href="../../using_the_ve/variables/variables.html?models=abiotic&roles=vars_updated">Variables
  updated by the abiotic model.</a>
