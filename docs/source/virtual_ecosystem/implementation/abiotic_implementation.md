---
jupytext:
  formats: md:myst
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

# The abiotic model implementation

```{warning}
The process-based abiotic model is still under development and currently not available
for Virtual Ecosystem simulations with `ve_run`. This page provides a brief summary of
the current status and the directions in which we aim to take the model development
forward.
```

## Required variables

The tables below show the variables that are required to initialise the abiotic model
and then update it at each time step. Please check also the
[notes on climate data pre-processing](../../using_the_ve/data/notes_preprocessing.md).

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

### Radiation

The current representation of radiation is limited to the reflection and absorption of
direct downward shortwave radiation and the emission of longwave radiation as part of
the surface energy balance.

The net radiation $R_N$ ($\mathrm{W\,m^{-2}}$) at the leaf or soil surface is
calculated as:

$$R_N = S_0 \cdot (1 - \alpha) - \epsilon_{s} \sigma T^{4}$$

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

### Soil energy balance

The `models.abiotic.soil_energy_balance` submodule determines the energy balance at the
soil surface by partitioning net radiation $R_N$ into:

- Sensible heat flux $H_S$ ($\mathrm{W\,m^{-2}}$),

- Latent heat flux $Q_{\text{LE}}$ ($\mathrm{W\,m^{-2}}$), and

- Ground heat flux $G$ ($\mathrm{W\,m^{-2}}$).

The **sensible heat flux** from the soil surface is given by:

$$H_{S} = \frac {\rho_{air} C_{air} (T_{S} - T_{A})}{r_{A}}$$

where:

$T_S$:
Soil surface temperature (°C)

$T_A$:
Air temperature in the bottom atmospheric layer (°C)

$r_A$:
Aerodynamic resistance of the soil surface ($\mathrm{s\,m^{-1}}$)

$\rho_{air}$:
Air density ($\mathrm{kg\,m^{-3}}$)

$C_{air}$:
Specific heat capacity of air ($\mathrm{J\,kg^{-1}\,K^{-1}}$)

The **aerodynamic resistance of the soil surface** is given by:

$$r_{A} = \frac {C_{E}}{u}$$

where:

$u$:
Horizontal wind speed at the bottom air layer ($\mathrm{m\,s^{-1}}$)

$C_E$:
Drag coefficient for evaporation (–)

The **latent heat flux** is derived by conversion of surface evaporation as
calculated by the hydrology model.

The **ground heat flux** $G$ is calculated as the residual of the energy balance:

$$G = R_N - H_S - Q_{\text{LE}}$$

### Soil temperature update

After the energy fluxes at the land surface have been partitioned, we simulate how heat
is transported vertically through the soil profile by updating the temperature of each
soil layer over time. This is done using an explicit finite-difference approach, which
numerically solves the one-dimensional heat diffusion equation. The method accounts for
thermal diffusivity and the net ground heat flux to calculate temperature changes at
each soil depth.

The **soil thermal diffusivity** $\alpha$ ($\mathrm{m^{2}\,s^{-1}}$) determines the rate
at which heat is conducted through the soil. It is defined as:

$$\alpha = \frac{\lambda}{\rho c}$$

where:

$\lambda$:
Soil thermal conductivity ($\mathrm{W\,m^{-1}\,K^{-1}}$), indicating how
  easily heat moves through soil

$\rho$:
Soil bulk density ($\mathrm{kg\,m^{-3}}$), including solids and pore spaces

$c$:
Soil specific heat capacity ($\mathrm{J\,kg^{-1}\,K^{-1}}$), the energy required to raise
the temperature of 1 kg of soil by 1 K.

#### Temperature Update Scheme

Let $T_i^t$ represent the temperature (°C or K) of the $i^\text{th}$ soil layer at time
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

### Canopy energy balance

Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly
{cite:p}`maclean_microclimc_2021`.
(For applications where very fine-temporal resolution data might be needed, heat and
vapour exchange must be modelled as transient processes, and heat storage by the canopy,
and the exchange of heat between different layers of the canopy, must be considered
explicitly, see {cite:t}`maclean_microclimc_2021`. This is currently not implemented.)

Under steady-state, the balance equation $EB$ for the leaves in each canopy layer is as
follows (after {cite:t}`maclean_microclimc_2021`):

```{math}
    & EB \\
    & = R_{\text{abs}} - R_{\text{em}} - H - Q_{\text{LE}} \\
    & = R_{\text{abs}} - \epsilon_{s} \sigma T_{L}^{4} - \frac{\rho_a c_p}{r_a}(T_{L} - T_{A})
    - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{A}} \\
    & = 0
```

where:

$R_{\text{abs}}$:
Shortwave radiation absorbed by the canopy ($\mathrm{W\,m^{-2}}$)

$R_{\text{em}}$:
Emitted longwave radiation from the canopy ($\mathrm{W\,m^{-2}}$)

$H$:
Sensible heat flux from the canopy to the air ($\mathrm{W\,m^{-2}}$)

$Q_{\text{LE}}$:
Latent heat flux associated with transpiration from the canopy to the air
($\mathrm{W\,m^{-2}}$)

$\epsilon_{s}$:
Emissivity of the leaf (-), typically close to 1

$\sigma$:
Stefan–Boltzmann constant ($5.67 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$)

$T_{L}$:
Temperature of the leaf (°C)

$T_{A}$:
Temperature of the air surrounding the leaf (°C)

$\lambda$:
Latent heat of vapourisation of water ($\mathrm{kJ\,kg^{-1}}$)

$e_{L}$:
Effective vapour pressure of the leaf (kPa)

$e_{A}$:
Vapour pressure of air (kPa)

$p_{A}$:
Atmospheric pressure (kPa)

$g_{v}$:
Conductance for vapour loss from the leaves ($\mathrm{mol\,m^{-2}\,s^{-1}}$) as a
function of the stomatal conductance $g_{c}$ ($\mathrm{s\,m^{-1}}$)

### Air and canopy temperature update

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. This method estimates updated canopy and air temperatures
by linearizing the canopy energy balance and applying a Newton iteration. This
approach accounts for the strong temperature dependence of radiative losses and ensures
numerical stability in canopy energy balance closure, following the method described by
{cite:t}`yang_scope_2021`. The goal is to find the leaf temperature that closes the
energy balance at the leaf surface, see previous section.

#### Newton Linearization

To iteratively solve for the leaf temperature that satisfies the energy balance $EB$, we
use the Newton method:

```{math}
T_L^{\text{new}} =
T_L^{\text{old}} + W \cdot \frac{EB}{\frac{\partial EB}{\partial T_L^{\text{old}}}}
```

where:

$T_L^{\text{old}}$:
Current estimate of leaf temperature (°C)

$T_L^{\text{new}}$:
Updated estimate of leaf temperature (°C)

$W$:
Step-size weighting factor (–), typically between 0.1 and 1

$\frac{\partial EB}{\partial T_L^{\text{old}}}$:
The first derivative of the energy balance with respect to temperature

This update adjusts the leaf temperature proportionally to the energy imbalance, scaled
by the sensitivity of that imbalance to temperature. The weighting factor $W$ ensures
numerical stability, especially in conditions where the balance is sensitive to small
temperature changes.

#### Derivative of energy balance

The temperature derivative of the energy balance as formulated above
is calculated analytically as:

```{math}
\frac{\partial EB}{\partial T_L^{\text{old}}} =
\frac{\rho_a c_p}{r_a} +
\frac{\rho_a \Delta_v}{r_a + r_s} \lambda +
4 \epsilon \sigma (T_L^{\text{old}} + 273.15)^3
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

$\epsilon$:
Leaf emissivity (-)

$\sigma$:
Stefan–Boltzmann constant ($5.67 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$)

$T_L^{\text{old}}$:
Previous estimate of leaf temperature (°C, converted to K in the radiation term)

This derivative represents the rate at which each energy loss term changes with leaf
temperature: convective, evaporative, and radiative. It ensures that the update step
accounts for the nonlinear temperature dependence, especially of radiative loss.

#### Air Temperature Coupling

After updating the canopy temperature, we optionally update the air temperature in the
adjacent canopy layer to reflect its coupling with the leaf temperature:

```{math}
T_A^{\text{new}} = T_A^{\text{old}} + \alpha \cdot (T_L^{\text{new}} - T_A^{\text{new}})
```

where:

$T_A$:
Air temperature (K)

$\alpha$:
Relaxation factor (–), typically < 1 for stability

This update assumes the leaf acts as a source or sink of heat for the air layer, and
relaxes the air temperature toward the new leaf temperature. The relaxation factor
$\alpha$ controls how tightly coupled the two temperatures are.

```{note}
There is currently no vertical mixing between layers and no heat is transferred to the
air above the canopy.
```

#### Update of atmospheric moisture

To account for moisture added to the atmosphere from canopy transpiration and soil
evaporation, the model updates key atmospheric humidity variables in each vertical
layer. This ensures consistency in the representation of atmospheric water content
across the grid.

Evapotranspiration and soil evaporation are initially provided in millimetres of water
depth. These values are converted to a mass of water per unit volume of air (kg m⁻³)
using the grid cell area. The evaporated water is then added to the relevant atmospheric
layers: canopy evapotranspiration is distributed across the layers directly above the
vegetation, while soil evaporation is added to the lowest layer near the surface.

Using the updated water mass, specific humidity is recalculated for each layer by
dividing the total water mass by the volume of air in that layer. This change in
specific humidity is then used to compute the new vapour pressure, taking into account
the atmospheric pressure and the molecular weight difference between water vapour and
dry air. To maintain physical realism, the vapour pressure is capped at the saturated
vapour pressure, avoiding supersaturation.

Finally, the model derives relative humidity as the ratio of vapour pressure to
saturated vapour pressure, expressed as a percentage. The vapour pressure deficit (VPD)
is then calculated as the difference between saturated and actual vapour pressure,
indicating the remaining atmospheric demand for water.

This update step ensures that changes in canopy and soil water fluxes are accurately
reflected in the atmospheric humidity profile, which in turn affects subsequent energy
and water balance calculations.

```{note}
At the moment we get 100% relative humididty and VPD=0, likely because there is no
vertical mixing and removal of water at the top of the canopy (advection).
```

### Wind

The wind profile determines the exchange of heat, water, and $\ce{CO_{2}}$ between soil
and atmosphere below the canopy as well as the exchange with the atmosphere above the
canopy.

The wind profile above the canopy is described as follows (based on
{cite:t}`campbell_introduction_1998` as implemented in {cite:t}`maclean_microclimc_2021`):

$$u_z = \frac{u^{*}}{0.4} ln \frac{z-d}{z_M} + \Psi_M$$

where $u_z$ is wind speed at height $z$ above the canopy, $d$ is
the height above ground within the canopy where the wind profile extrapolates to
zero, $z_m$ the roughness length for momentum, $\Psi_M$ is a diabatic
correction for momentum and $u^{*}$ is the friction velocity, which gives the
wind speed at height $d + z_m$.

The wind profile below canopy is derived as follows:

$$u_z = u_h \exp(a(\frac{z}{h} - 1))$$

where $u_z$ is wind speed at height $z$ within the canopy, $u_h$
is wind speed at the top of the canopy at height $h$, and $a$ is a wind
attenuation coefficient given by $a = 2 l_m i_w$, where $c_d$ is a drag
coefficient that varies with leaf inclination and shape, $i_w$ is a
coefficient describing relative turbulence intensity and $l_m$ is the mean
mixing length, equivalent to the free space between the leaves and stems. For
details, see {cite:t}`maclean_microclimc_2021`.

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
