---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.2
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
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
tags: [remove-input]
mystnb:
  markdown_format: myst
---

from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        'AbioticModel', 
        ['vars_required_for_init', 'vars_required_for_update']
    ), 
    raw=True
)
```

## Model overview

### Radiation

The representation of radiation is currently limited to reflection/absorption of direct
downward shortwave radiation and the emission of longwave radiation as part of the
energy balance. Net radiation at the surface $R_N$ is calculated as:

$$R_N = S_0 \cdot (1 - \alpha) - \epsilon_{s} \sigma T^{4}$$

where $S_0$ is the incoming shortwave radiation, $\alpha$ is the albedo of the leaf/soil
surface, $\epsilon$ is the emissivity of the leaf/surface and $T$ is the temperature of
the leaf/soil surface.

In the future, we aim to implement a diurnal cycle of incoming radiation including the
effects of topography on sun angle as well as diffuse radiation.

### Soil energy balance

The ``models.abiotic.soil_energy_balance`` submodule determines the energy balance at
the surface by calculating how incoming solar radiation that reaches the surface is
partitioned in sensible, latent, and ground heat flux. The sensible heat flux from the
soil surface is given by:

$$H_{S} = \frac {\rho_{air} C_{air} (T_{S} - T_{b}^{A})}{r_{A}}$$

where $T_{S}$ is the soil surface temperature, $T_{b}^{A}$ is the
temperature of the bottom air layer and $r_{A}$ is the aerodynamic resistance
of the soil surface, given by

$$r_{A} = \frac {C_{S}}{u_{b}}$$

where $u_{b}$ is the wind speed in the bottom air layer and $C_{S}$ is
the soil surface heat transfer coefficient.

Latent heat flux $\lambda E_S$ is derived by conversion of surface evaporation as
calculated by the hydrology model, and ground heat flux $G$ is calculated as the residual:

$$G = R_N - H_S - \lambda E_S$$

After the flux partitioning, we determine the soil temperatures at different depths.
At the moment, this is achieved with linear interpolation between the surface and
soil temperature at 1 m depth. In the future, we aim for a mechanistic implementation.

### Canopy energy balance

Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly
{cite:p}`maclean_microclimc_2021`.
(For applications where very fine-temporal resolution data might be needed, heat and
vapour exchange must be modelled as transient processes, and heat storage by the canopy,
and the exchange of heat between different layers of the canopy, must be considered
explicitly, see {cite:t}`maclean_microclimc_2021`. This is currently not implemented.)

Under steady-state, the balance equation for the leaves in each canopy layer is as
follows (after {cite:t}`maclean_microclimc_2021`):

```{math}
    & R_{abs} - R_{em} - H - \lambda E \\
    & = R_{abs} - \epsilon_{s} \sigma T_{L}^{4} - c_{P}g_{Ha}(T_{L} - T_{A})
    - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{A}} \\
    & = 0
```

where $R_{abs}$ is absorbed radiation, $R_{em}$ emitted radiation, $H$
the sensible heat flux, $\lambda E$ the latent heat flux, $\epsilon_{s}$ the
emissivity of the leaf, $\sigma$ the Stefan-Boltzmann constant, $T_{L}$ the
absolute temperature of the leaf, $T_{A}$ the absolute temperature of the air
surrounding the leaf, $\lambda$ the latent heat of vapourisation of water,
$e_{L}$ the effective vapour pressure of the leaf, $e_{A}$ the vapour
pressure of air and $p_{A}$ atmospheric pressure. $g_{Ha}$ is the heat
conductance between leaf and atmosphere, $g_{v}$ represents the conductance
for vapour loss from the leaves as a function of the stomatal conductance $g_{c}$.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a linearisation approach to solve the equation for
leaf temperature and air temperature simultaneously after
{cite:t}`maclean_microclimc_2021`.

The air temperature surrounding the leaf $T_{A}$ is assumed to be influenced
by leaf temperature $T_{L}$, soil temperature $T_{0}$, and reference air
temperature $T_{R}$ as follows:

$$g_{tR} c_{p} (T_{R} - T_{A}) + g_{t0} c_{p} (T_{0} - T_{A}) + g_{L} c_{p} (T_{L} - T_{A})
= 0$$

where $c_{p}$ is the specific heat of air at constant pressure and
$g_{tR}$, $g_{t0}$ and $g_{L}$ are conductance from reference
height, the ground and from the leaf, respectively.
$g_{L} = 1/(1/g_{HA} + 1/g_{z})$ where $g_{HA}$ is leaf boundary layer
conductance and $g_{z}$ is the sub-canopy turbulent conductance at the height
of the leaf over the mean distance between the leaf and the air.

Defining $T_{L} - T_{A}$ as $\Delta T$ and rearranging gives:

$$T_{A} = a_{A} + b_{A} \Delta T_{L}$$

where $a_{A} = \frac{(g_{tR} T_{R} + g_{t0} T_{0})}{(g_{tR} + g_{t0})}$ and
$b_{A} = \frac{g_{L}}{(g_{tR} + g_{t0})}$ .

The sensible heat flux between the leaf and the air is given by

$$g_{Ha} c_{p} (T_{L} - T_{A}) = b_{H} \Delta T_{L}$$

where $b_{H} = g_{Ha} c_{p}$. The equivalent vapour flux equation is

$$g_{tR}(e_{R} - e_{a}) + g_{t0} (e_{0} - e_{a}) + g_{v} (e_{L} - e_{a}) = 0$$

where $e_{L}$, $e_{A}$, $e_{0}$ and $e_{R}$ are the vapour
pressure of the leaf, air, soil and air at reference height, respectively, and
$g_{v}$ is leaf conductance for vapour given by
$g_{v} = \frac{1}{(\frac{1}{g_{c} + g_{L})}}$ where $g_{c}$ is stomatal
conductance. Assuming the leaf to be saturated, and approximated by
$e_{s} [T_{R}]+\Delta_{v} [T_{R}]\Delta T_{L}$ where $\Delta_{v}$ is the
slope of the saturated pressure curve at temperature $T_{R}$, and rearranging
gives

$$e_{a} = a_{E} + b_{E} \Delta T_{L}$$

where
$a_{E} = \frac{(g_{tR} e_{R} + g_{t0} e_{0} + g_{v} e_{s}[T_{R}])}{(g_{tR} + g_{t0} + g_{v})}$
and $b_{E} = \frac{(\Delta_{V} [T_{R}])}{(g_{tR} + g_{t0} + g_{v})}$.

The latent heat term is given by

$$\lambda E = \frac{\lambda g_{v}}{p_{a}} (e_{L} - e_{A})$$

Substituting $e_{A}$ for its linearized form, again assuming $e_{L}$
is approximated by $e_{s} [T_{R}]+\Delta_{v} [T_{R}]\Delta T_{L}$, and
rearranging gives:

$$\lambda E = a_{L} + b_{L} \Delta T_{L},$$

where $a_{L} = \frac{\lambda g_{v}}{p_{a}} (e_{s} [T_{R}] - a_{E})$ and
$b_{L} = \frac{\lambda g_{v}}{p_{a}} (\Delta_{V} [T_{R}] - b_{E})$.

The radiation emitted by the leaf $R_{em}$ is given by the Stefan Boltzmann
law and can be linearised as follows:

$$R_{em} = a_{R} + b_{R} \Delta T_{L}$$

where $a_{R} = \epsilon_{s} \sigma a_{A}^{4}$ and
$b_{R} = 4 \epsilon_{s} \sigma (a_{A}^{3} b_{A} + T_{R}^{3})$.

The full heat balance equation for the difference between leaf and canopy air
temperature becomes

$$\Delta T_{L} = \frac{R_{abs} - a_{R} - a_{L}}{(1 + b_{R} + b_{L} + b_{H})}$$

The equation is then used to calculate air and leaf temperature as follows:

$$T_{A} = a_{A} + b_{A} \Delta T_{L}$$

and

$$T_{L} = T_{A} + \Delta T_{L}.$$

### Wind

The wind profile determines the exchange of heat, water, and $\ce{CO_{2}}$ between soil
and atmosphere below the canopy as well as the exchange with the atmosphere above the canopy.

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
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'AbioticModel',
        ['vars_updated']
    ),
    raw=True
)
```
