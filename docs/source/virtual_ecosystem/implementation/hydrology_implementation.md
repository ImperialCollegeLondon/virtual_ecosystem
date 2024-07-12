# Implementatioon of the hydrology model

This section walks through the steps in generating and updating the
[hydrology](../../../../virtual_ecosystem/models/hydrology/hydrology_model.py)
model which is part of the default Virtual Ecosystem configuration.
The model is loosely based on the LISFLOOD model {cite}`van_der_knijff_lisflood_2010`.
The key processes are illustrated in {numref}`hydrology`.

:::{figure} ../../_static/images/hydrology.jpg
:name: hydrology
:alt: Hydrology
:class: bg-primary
:width: 500px

Hydrology processes implemented in Virtual Ecosystem (click to zoom).
:::

```{note}
Many of the underlying processes are problematic at a monthly timestep, which is
currently the only supported update interval. As a short-term work around, the input
precipitation is randomly distributed over 30 days and input evapotranspiration is
divided by 30, and the return variables are monthly means or monthly accumulated values.
```

## Required input data

The `hydrology` model requires the following variables to initialise and update the
model:

``` python
required_init_vars=(
    "layer_heights",
    "elevation",
)

required_update_vars=(
    "air_temperature",
    "relative_humidity",
    "atmospheric_pressure",
    "precipitation",
    "wind_speed",
    "leaf_area_index",
    "layer_heights",
    "soil_moisture",
    "evapotranspiration",
    "surface_runoff_accumulated",
    "subsurface_flow_accumulated",
)
```

The model also requires several parameters that as described in detail in
{py:class}`~virtual_ecosystem.models.hydrology.constants.HydroConsts`.
The default values are set for forest ecosystems.

## Vertical hydrology components

The vertical component of the hydrology model determines the water balance within each
grid cell. This includes [above ground](../../api/models/hydrology/above_ground.md)
processes such as rainfall, intercept, and surface runoff out of the grid cell.
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

.. math::
:nowrap:

\[
       S_{max} =
        \begin{cases}
            0.935 + 0.498 \cdot \text{LAI} - 0.00575 \cdot \text{LAI}^{2},
                & \text{LAI} > 0.1 \\
            0, &  \text{LAI} \le 0.1,
        \end{cases}
\]

where LAI is the average Leaf Area Index (m2 m-2). $k$ is estimated as:

$$k=0.046 * LAI$$

### Water at the surface

Precipitation that reaches the surface is defined as incoming precipitation minus canopy
interception. This water can follow five different trajectories: runoff at the surface,
remain at the surface as searchable resource for animals, infiltrate into the soil,
or return to the atmosphere via evaporation.

### Surface Runoff

Surface runoff is calculated with a simple bucket model based on
{cite:t}`davis_simple_2017`: if precipitation exceeds top soil moisture capacity, the
excess water is added to runoff and top soil moisture is set to soil
moisture capacity value; if the top soil is not saturated, precipitation is
added to the current soil moisture level and runoff is set to zero.

### Searchable resource

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
the following equation (after :cite:t:`van_der_knijff_lisflood_2010`):

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

For some model functionalities, such as plant water uptake and soil microbila activity,
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
:cite:p:`lindstrom_development_1997` and the LISFLOOD
:cite:p:`van_der_knijff_lisflood_2010` (see for full documentation).

The upper zone represents a quick runoff component, which includes fast groundwater
and subsurface flow through macro-pores in the soil. The lower zone represents the
slow groundwater component that generates the base flow.

The outflow from the upper zone to the channel, :math:`Q_{uz}`, [mm], equals:

:math:`Q_{uz} = \frac{1}{T_{uz}} * UZ * \Delta t`

where :math:`T_{uz}` is the reservoir constant for the upper groundwater layer
[days], and :math:`UZ` is the amount of water that is stored in the upper zone [mm].
The amount of water stored in the upper zone is computed as follows:

:math:`UZ = D_{ls,gw} + D_{pref,gw} - D{uz,lz}`

where :math:`D_{ls,gw}` is the flow from the lower soil layer to groundwater,
:math:`D_{pref,gw}` is the amount of preferential flow or bypass flow per time step,
:math:`D_{uz,lz}` is the amount of water that percolates from the upper to the lower
zone, all in [mm].

The water percolates from the upper to the lower zone is the inflow to the lower
groundwater zone. This amount of water is provided by the upper groundwater zone.
:math:`D_{uz,lz}` is a fixed amount per computational time step and it is defined as
follows:

:math:`D_{uz,lz} = min(GW_{perc} * \Delta t, UZ)`

where :math:`GW_{perc}`, [mm day], is the maximum percolation rate from the upper to
the lower groundwater zone. The outflow from the lower zone to the channel is then
computed by:

:math:`Q_{lz} = \frac{1}{T_{lz}} * LZ * \Delta t`

:math:`T_{lz}` is the reservoir constant for the lower groundwater layer, [days],
and :math:`LZ` is the amount of water that is stored in the lower zone, [mm].
:math:`LZ` is computed as follows:

:math:`LZ = D_{uz,lz} - (GW_{loss} * \Delta t)`

where :math:`D_{uz,lz}` is the percolation from the upper groundwater zone,[mm],
and :math:`GW_{loss}` is the maximum percolation rate from the lower groundwater
zone, [mm day].

The amount of water defined by :math:`GW_{loss}` never rejoins the river channel and
is lost beyond the catchment boundaries or to deep groundwater systems. The larger
the value of ath:`GW_{loss}`, the larger the amount of water that leaves the system.

### Horizontal hydrology components
<!-- 
The second part of the hydrology model calculates the horizontal water movement across
the full model grid including accumulated surface runoff and sub-surface flow, and river
discharge rate, [see](../../api/models/hydrology/above_ground.md). The flow direction is
based on a digital elevation model.

The accumulated surface runoff is calculated as the sum of current runoff and the runoff
from upstream cells at the previous time step, see accumulate_horizontal_flow() .

The horizontal flow between grid cells currently uses the same function as the above
ground runoff.

Total river discharge is calculated as the sum of above- and below ground horizontal
flow and converted to river discharge rate in m3/s. -->

## Returned variables
