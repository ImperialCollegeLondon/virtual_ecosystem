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

# Implementation of the hydrology model

This section walks through the steps in generating and updating the
[hydrology](../../../../virtual_ecosystem/models/hydrology/hydrology_model.py)
model which is part of the default Virtual Ecosystem configuration. The key processes
are illustrated in {numref}`hydrology`.

The processes [within a grid cell](#within-grid-cell-hydrology) are loosely based
on the LISFLOOD model {cite}`van_der_knijff_lisflood_2010`. The processes
[across the model grid](#across-grid-hydrology) are loosely based on
the [pysheds](https://github.com/mdbartos/pysheds) package.

:::{figure} ../../_static/images/hydrology.jpg
:name: hydrology
:alt: Hydrology
:class: bg-primary
:width: 600px

Hydrology processes in Virtual Ecosystem (click to zoom). Yellow boxes
represent atmospheric input variables, green box and arrows indicate where water
enters and leaves the plant model.
:::

```{note}
Many of the underlying processes are problematic at a monthly timestep, which is
currently the only supported update interval. As a short-term work around, the input
precipitation is randomly distributed over 30 days and input evapotranspiration is
divided by 30, and the return variables are monthly means or monthly accumulated values.
```

## Required variables

The tables below show the variables that are required to initialise the hydrology model
and then update it at each time step.

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
        'HydrologyModel', 
        ['vars_required_for_init', 'vars_required_for_update']
    ), 
    raw=True
)
```

The model also requires several parameters that as described in detail in
{py:class}`~virtual_ecosystem.models.hydrology.constants.HydroConsts`.
The default values are set for forest ecosystems.

## Generated variables

When the hydrology model initialises, it uses the input data to populate the following
variables. When the model first updates, it then sets further variables.

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'HydrologyModel', 
        ['vars_populated_by_init', 'vars_populated_by_first_update']
    ), 
    raw=True
)
```

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
        'HydrologyModel', 
        ['vars_updated']
    ), 
    raw=True
)
```

## Within grid cell hydrology

The vertical component of the hydrology model determines the water balance within each
grid cell. This includes [above ground](../../api/models/hydrology/above_ground.md)
processes such as rainfall, canopy interception, and surface runoff out of the grid cell.
The [below ground](../../api/models/hydrology/below_ground.md) component considers
infiltration, bypass flow, percolation (= vertical flow), soil moisture and matric
potential, horizontal sub-surface flow out of the grid cell, and changes in
groundwater storage.

### Canopy interception

Canopy interception is estimated using the following storage-based equation after
{cite:t}`aston_rainfall_1979` and {cite:t}`merriam_note_1960` as implemented in
{cite:t}`van_der_knijff_lisflood_2010`:

$$Int = S_{max} * [1 - e \frac{(-k*R*\delta t}{S_{max}})]$$

where $Int$ (mm) is the interception per time step, $S_{max}$ (mm) is the maximum
interception, $R$ (mm) is the rainfall intensity per time step and the factor $k$
accounts for the density of the vegetation.

$S_{max}$ is calculated using an empirical equation
{cite}`von_hoyningen-huene_interzeption_1981`:

```{math}
\begin{cases}
    0.935 + 0.498 \cdot \text{LAI} - 0.00575 \cdot \text{LAI}^{2}, & \text{LAI} > 0.1 \\
    0, &  \text{LAI} \le 0.1,
\end{cases}
```

where LAI is the average Leaf Area Index (m2 m-2). $k$ is estimated as:

$$k=0.046 * LAI$$

### Water at the surface

Precipitation that reaches the surface is defined as incoming precipitation minus canopy
interception (throughfall and stemflow are currently not implemented). The water at the
surface can follow different trajectories: runoff at the surface,
remain at the surface as searchable resource for animals, return to the atmosphere via
evaporation, or infiltrate into the soil where it can be taken up by plants or percolate
to the groundwater.

### Surface Runoff

Surface runoff is calculated with a simple bucket model based on
{cite:t}`davis_simple_2017`: if precipitation exceeds top soil moisture capacity, the
excess water is added to runoff and top soil moisture is set to soil
moisture capacity value; if the top soil is not saturated, precipitation is
added to the current soil moisture level and runoff is set to zero.

### Searchable resource

Some of the water that land at the surface is stored in depressions as puddles or
larger standing water that is a searchable resources for animals. This is currently not
implemented.

### Evaporation

The implementation of soil evaporation is based on classical bulk aerodynamic formulation.
We use the so-called 'alpha' method to estimate the evaporative flux
{cite}`mahfouf_comparative_1991` and the implementation by
{cite:t}`barton_parameterization_1979`:

$$\alpha = \frac{1.8 * \Theta}{\Theta + 0.3}$$

$$E_{g} = \frac{\rho_{air}}{R_{a}} * (\alpha * q_{sat}(T_{s}) - q_{g})$$

where $\Theta$ is the available top soil moisture (relative volumetric water
content), $E_{g}$ is the evaporation flux (W m-2), $\rho_{air}$ is the
density of air (kg m-3), $R_{a}$ is the aerodynamic resistance (unitless),
$q_{sat}(T_{s})$ (unitless) is the saturated specific humidity, and
$q_{g}$ is the surface specific humidity (unitless).

In a final step, the bare soil evaporation is adjusted to shaded soil evaporation
{cite:t}`supit_system_1994`:

$$E_{act} = E_{g} * exp(-\kappa_{gb}*LAI)$$

where $\kappa_{gb}$ is the extinction coefficient for global radiation, and
$LAI$ is the total leaf area index.

### Infiltration

Infiltration is currently handeled in a very simplistic way: the water that 'fits in the
topsoil bucket' is added to the topsoil layer. We aim to implement a more realistic
process that accounts for soil type specific infiltration capacities.

### Bypass flow

Bypass flow is here defined as the flow that bypasses the soil matrix and drains
directly to the groundwater. During each time step, a fraction of the water that is
available for infiltration is added to the groundwater directly (i.e. without first
entering the soil matrix). It is assumed that this fraction is a power function of
the relative saturation of the superficial and upper soil layers. This results in
the following equation (after {cite:t}`van_der_knijff_lisflood_2010`):

$$D_{pref, gw} = W_{av} * (\frac{w_{1}}{w_{s1}})^{c_{pref}}$$

$D_{pref, gw}$ is the amount of preferential flow per time step (mm),
$W_{av}$ is the amount of water that is available for infiltration, and
$c_{pref}$ is an empirical shape parameter. This parameter affects how much of
the water available for infiltration goes directly to groundwater via preferential
bypass flow; a value of 0 means all surface water goes directly to groundwater, a
value of 1 gives a linear relation between soil moisture and bypass flow.
The equation returns a preferential flow component that becomes increasingly
important as the soil gets wetter.

### Vertical flow

To calculate the flow of water through unsaturated soil, we use the Richards equation.
First, the function calculates the effective saturation $S$ and effective hydraulic
conductivity $K(S)$ based on the moisture content $\Theta$ using the Mualem-van
Genuchten model {cite}`van_genuchten_closed-form_1980`:

$$S = \frac{\Theta - \Theta_{r}}{\Theta_{s} - \Theta_{r}}$$

and

$$K(S) = K_{s}* \sqrt{S} *(1-(1-S^{1/m})^{m})^{2}$$

where $\Theta_{r}$ is the residual moisture content,$\Theta_{s}$ is the saturated
moisture content, $K_{s}$ is the saturated hydraulic conductivity, and $m=1-1/n$ is a
shape parameter derived from the non-linearity parameter $n$. Then, the function applies
Darcy's law to calculate the water flow rate $q$ in $\frac{m^3}{s^1}$ considering the
effective hydraulic conductivity:

$$q = - K(S)*(\frac{dh}{dl}-1)$$

where $\frac{dh}{dl}$ is the hydraulic gradient with $l$ the length of the flow path in
meters (here equal to the soil depth).

```{note}
There are severe limitations to this approach on the temporal and spatial scale of this
model and this can only be treated as a very rough approximation!
```

### Soil moisture and matrix potential

Soil moisture is updated for each layer by removing the vertical flow
of the current layer and adding it to the layer below. The implementation is based
on {cite:t}`van_der_knijff_lisflood_2010`. Additionally, the evapotranspiration is
removed from the second soil layer.

For some model functionalities, such as plant water uptake and soil microbial activity,
soil moisture needs to be converted to matric potential. The model provides a coarse
estimate of soil water potential :$\Psi_{m}$ taken from
{cite:t}`campbell_simple_1974`:

$$\Psi_{m} = \Psi_{e} * (\frac{\Theta}{\Theta_{s}})^{b}$$

where $\Psi_{e}$ is the air-entry, $\Theta$ is the volumetric water content,
$\Theta_{s}$ is the saturated water content, and $b$ is the water retention curvature
parameter.

### Subsurface flow and groundwater storage

Groundwater storage and transport are modelled using two parallel linear reservoirs,
similar to the approach used in the HBV-96 model
{cite}`lindstrom_development_1997` and the LISFLOOD
{cite}`van_der_knijff_lisflood_2010` (see for full documentation).

The upper zone represents a quick runoff component, which includes fast groundwater
and subsurface flow through macro-pores in the soil. The lower zone represents the
slow groundwater component that generates the base flow.

The outflow from the upper zone to the channel, $Q_{uz}$, (mm), equals:

$$Q_{uz} = \frac{1}{T_{uz}} * UZ * \Delta t$$

where $T_{uz}$ is the reservoir constant for the upper groundwater layer
(days), and $UZ$ is the amount of water that is stored in the upper zone (mm).
The amount of water stored in the upper zone is computed as follows:

$$UZ = D_{ls,gw} + D_{pref,gw} - D{uz,lz}$$

where $D_{ls,gw}$ is the flow from the lower soil layer to groundwater,
$D_{pref,gw}$ is the amount of preferential flow or bypass flow per time step,
$D_{uz,lz}$ is the amount of water that percolates from the upper to the lower
zone, all in (mm).

The water percolates from the upper to the lower zone is the inflow to the lower
groundwater zone. This amount of water is provided by the upper groundwater zone.
$D_{uz,lz}$ is a fixed amount per computational time step and it is defined as
follows:

$$D_{uz,lz} = min(GW_{perc} * \Delta t, UZ)$$

where $GW_{perc}$, [mm day], is the maximum percolation rate from the upper to
the lower groundwater zone. The outflow from the lower zone to the channel is then
computed by:

$$Q_{lz} = \frac{1}{T_{lz}} * LZ * \Delta t$$

$T_{lz}$ is the reservoir constant for the lower groundwater layer, (days),
and $LZ$ is the amount of water that is stored in the lower zone, (mm).
$LZ$ is computed as follows:

$$LZ = D_{uz,lz} - (GW_{loss} * \Delta t)$$

where $D_{uz,lz}$ is the percolation from the upper groundwater zone, (mm),
and $GW_{loss}$ is the maximum percolation rate from the lower groundwater
zone, (mm day-1).

The amount of water defined by $GW_{loss}$ never rejoins the river channel and
is lost beyond the catchment boundaries or to deep groundwater systems. The larger
the value of $GW_{loss}$, the larger the amount of water that leaves the system.

## Across grid hydrology

The second part of the hydrology model calculates the horizontal water movement across
the full model grid including accumulated surface runoff and sub-surface flow, and river
discharge rate.

The flow direction of water above and below ground is based on a digital elevation model.
First, we find all the neighbours for each grid cell and determine which neigbour has
the lowest elevation. Based on that relationship, we determine all upstream neighbours
for each grid cell. The accumulated surface runoff is calculated as the sum of current
runoff and the runoff from upstream cells at the previous time step.

elevation
flowmap

Total river discharge is calculated as the sum of above- and below ground horizontal
flow and converted to river discharge rate in m3/s.

```{note}
The hydrology model requires a spinup period to establish a steady state flow of
accumulated above and below ground flow - each simulation time step then represents the
total flow through a grid cell. This is currently not implemented.

To close the water balance, water needs to enter and leave the grid at some point. These
boundaries are currently not implemented.
```
