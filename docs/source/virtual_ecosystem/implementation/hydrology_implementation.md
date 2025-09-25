---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
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

# The hydrology model implementation

This section walks through the steps in generating and updating the
[hydrology](../../../../virtual_ecosystem/models/hydrology/hydrology_model.py)
model which is part of the default Virtual Ecosystem configuration. The flow of key
inputs, state variables, and processes are illustrated in {numref}`hydrology`.

The processes [within a grid cell](#within-grid-cell-hydrology) are loosely based
on the LISFLOOD model {cite}`van_der_knijff_lisflood_2010`. These structure and flows of
this '4-Bucket Model' are summarised in {numref}`bucket_model`. The processes
[across the model grid](#across-grid-hydrology) are loosely based on
the [pysheds](https://github.com/mdbartos/pysheds) package.

:::{figure} ../../_static/images/hydrology.svg
:name: hydrology
:alt: Hydrology
:class: bg-primary
:width: 600px

Hydrology inputs, state variables, and processes in Virtual Ecosystem (click to zoom).
Yellow boxes represent atmospheric input variables, green box and arrows indicate where
water enters and leaves the plant model.
:::

```{note}
Calculating hydrological processes at coarse time scales is problematic and so the
hydrology model uses an internal daily time step to model hydrology. When the model is
run with a coarser update interval - and hence the precipitation and transpiration
inputs are totals over more than one day - the hydrology model partitions the input data
 into daily values. Precipitation is randomly partitioned between days and the total
 transpiration is evenly divided across days.

The values returned by the hydrology model are then monthly means or monthly accumulated
values.
```

## Required variables

The tables below show the variables that are required to initialise the hydrology model
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
        "HydrologyModel", ["vars_required_for_init", "vars_required_for_update"]
    ),
    raw=True,
)
```

The model also requires several parameters that as described in detail in
{py:class}`~virtual_ecosystem.models.hydrology.constants.HydroConsts`.
The default values are set for forest ecosystems.

## Within grid cell hydrology

The vertical component of the hydrology model determines the water balance within each
grid cell. This includes [above ground](../../api/models/hydrology/above_ground.md)
processes such as rainfall, canopy interception and evaporation, leaf drainage, and
surface runoff out of the grid cell.
The [below ground](../../api/models/hydrology/below_ground.md) component considers
infiltration, bypass flow, percolation (= vertical flow), {term}`soil moisture` and
{term}`soil matric potential`, horizontal
sub-surface runoff out of the grid cell, and changes in groundwater storage.

:::{figure} ../../_static/images/4bucketmodel.svg
:name: bucket_model
:alt: 4-Bucket Model
:class: bg-primary
:width: 600px

The 4-Bucket Model represented within grid cell hydrology processes in the Virtual
Ecosystem. Red solid arrows indicate upward vertical flows, red dashed arrows show
vertical downward flows. The blue arrows indicate horizontal flows out of the
grid cell with solid lines representing water that flows out of each layer in the
current time step and dashed lines representing water that originates from upstream
grid cells and flows through the grid cell directly to the stream.
**NOTE!** Top soil and middle soil are currently treated as one layer in the model.
Subsurface runoff (Q2) and interflow (Q3) are currently not implemented; the
river discharge is calculated as the sum of surface runoff (Q1) and the flows out of the
groundwater buckets (Q4+Q5).
:::

### Canopy interception

Canopy interception is estimated using the following storage-based equation after
{cite:t}`aston_rainfall_1979` and {cite:t}`merriam_note_1960` as implemented in
{cite:t}`van_der_knijff_lisflood_2010`:

$$\textrm{Int} = S_{max} \left[1 - \exp\left(\frac{-k \cdot R \cdot \delta t}{S_{max}}\right)\right]$$

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

$$k=0.046 \cdot LAI$$

### Canopy evaporation and leaf drainage

Evaporation of intercepted water from the canopy following the LISFLOOD model
{cite:t}`van_der_knijff_lisflood_2010`. The maximum evaporation per time step $EW_{max}$
is proportional to the fraction of vegetated area:

```{math}
  EW_{max} = EW_{0} [1 - e^{(-\kappa_{gb} LAI)}] \Delta t
```

where $EW_{0}$ is the potential evaporation rate, the dimensionless constant
$\kappa_{gb}$ is the extinction coefficient for global solar radiation. In LISFLOOD,
$\kappa_{gb}$ is given by the product $0.75 \cdot \kappa_{df}$, where $\kappa_{df}$ is
the extinction coefficient for diffuse visible light: its value is provided as input to
the model and it varies between 0.4 and 1.1.

The actual amount of evaporation $EW_{int}$ is limited by the amount of
water stored on the leaves $Int_{cum}$:

```{math}
  EW_{int} = min(EW_{max} \Delta t, Int_{cum})
```

Another amount of water falls to the soil because of leaf drainage which is modelled
as a linear reservoir:

```{math}
  D_{int} = \frac{1}{T_{int}} Int_{cum} \Delta t
```

where $D_{int}$ is the amount of leaf drainage per time step and $T_{int}$ is a time
constant (or residence time) of the interception store. Setting $T_{int} = 1$ day is
strongly recommended and means that all the water in the interception store
evaporates or falls to the soil surface as leaf drainage within one day.

### Water at the surface

Precipitation that reaches the surface is defined as incoming precipitation minus canopy
evaporation plus leaf drainage. The water at the
surface can follow different trajectories: runoff at the surface,
remain at the surface as searchable resource for animals, return to the atmosphere via
evaporation, or infiltrate into the soil where it can be taken up by plants or percolate
to the groundwater.

### Surface Runoff

Surface runoff is calculated with a simple bucket model based on
{cite:t}`davis_simple_2017`: if precipitation exceeds top {term}`soil moisture capacity`
, the excess water is added to runoff and top soil moisture is set to soil
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

$$\alpha = \frac{1.8 \cdot \Theta}{\Theta + 0.3}$$

$$E_{g} = \frac{\rho_{air}}{R_{a}} \cdot (\alpha \cdot q_{sat}(T_{s}) - q_{g})$$

where $\Theta$ is the available top soil moisture (here {term}`relative soil moisture`)
, $E_{g}$ is the evaporation flux (W m-2), $\rho_{air}$ is the
density of air (kg m-3), $R_{a}$ is the aerodynamic resistance (unitless),
$q_{sat}(T_{s})$ (unitless) is the saturated specific humidity, and
$q_{g}$ is the {term}`specific soil moisture` near the surface (unitless).

In a final step, the bare soil evaporation is adjusted to shaded soil evaporation
{cite:t}`supit_system_1994`:

$$E_{act} = E_{g} \cdot \exp(-\kappa_{gb} \cdot LAI)$$

where $\kappa_{gb}$ is the extinction coefficient for global radiation, and
$LAI$ is the total leaf area index.

### Infiltration

Infiltration is currently handled in a very simplistic way: the water that 'fits in the
topsoil bucket' is added to the topsoil layer. We aim to implement a more realistic
process that accounts for soil type specific infiltration capacities.

### Bypass flow

Bypass flow is here defined as the flow that bypasses the soil matrix and drains
directly to the groundwater. During each time step, a fraction of the water that is
available for infiltration is added to the groundwater directly (i.e. without first
entering the soil matrix). It is assumed that this fraction is a power function of
the relative saturation of the superficial and upper soil layers. This results in
the following equation (after {cite:t}`van_der_knijff_lisflood_2010`):

$$D_{pref, gw} = W_{av} \cdot (\frac{w_{1}}{w_{s1}})^{c_{pref}}$$

$D_{pref, gw}$ is the amount of preferential flow per time step (mm),
$W_{av}$ is the amount of water that is available for infiltration, and
$c_{pref}$ is an empirical shape parameter. This parameter affects how much of
the water available for infiltration goes directly to groundwater via preferential
bypass flow; a value of 0 means all surface water goes directly to groundwater, a
value of 1 gives a linear relation between soil moisture and bypass flow.
The equation returns a preferential flow component that becomes increasingly
important as the soil gets wetter.

### Vertical flow

To calculate the flow of water through unsaturated soil, we combine
Richards' equation and Darcy's law for unsaturated flow.
First, we calculate the effective saturation $S_{e}$ and effective unsaturated hydraulic
conductivity $K(\Theta)$ based on the moisture content $\Theta$ using the van
Genuchten - Mualem model
({cite:t}`van_genuchten_closed-form_1980`, {cite:t}`mualem_new_1976`).

First, the effective saturation is calculated as:

$$S_{e} = \frac{\Theta - \Theta_{r}}{\Theta_{s} - \Theta_{r}}$$

where $\Theta_{r}$ is the {term}`soil moisture residual` and $\Theta_{s}$ is
the {term}`soil moisture saturation`.

Then, the effective unsaturated hydraulic conductivity is computed as:

$$K(\Theta) = K_{s} \cdot S_{e}^{L} \cdot [1-(1-S_{e}^{\frac{1}{m}})^{m}]^{2}$$

where $K_{s}$ is the saturated hydraulic conductivity,
$L$ is the pore connectivity parameter (assumed to be 0.5 in most of studies),
and $m=1-1/n$ is a
shape parameter derived from the non-linearity parameter $n$.

The soil matric potential $\Psi_{m}$ is calculated as follows:

$$\Psi_{m} = - \frac{1}{\alpha} (S_{e}^{-\frac{1}{m}}-1)^\frac{1}{n}$$

where $\alpha$ is the inverse of air entry value.

Then, the function applies
Darcy's law to calculate the water flow rate $q$ in $\frac{mm}{day^1}$ considering the
effective unsaturated hydraulic conductivity:

$$q = - K(\Theta) \cdot (\frac{d \Psi_{m}}{dz} + 1)$$

where $\frac{d \Psi_{m}}{dz}$ is the soil matric potential gradient with $z$
    the elevation (gravitational potential) or {term}`gravitational head`.

```{note}
There are severe limitations to this approach on the temporal and spatial scale of this
model and this can only be treated as a very rough approximation!
```

### Soil moisture redistribution

Soil moisture is updated for each layer by removing the vertical flow
of the current layer and adding it to the layer below. The implementation is based
on {cite:t}`van_der_knijff_lisflood_2010`. Additionally, the canopy transpiration is
removed from the second soil layer.

```{note}
We do currently NOT include any horizontal flows from the soil layers towards the stream
(Q2 and Q3 in {numref}`bucket_model`).
```

### Belowground runoff and groundwater storage

Groundwater storage and runoff towards the channel are modelled using two parallel
linear reservoirs, similar to the approach used in the HBV-96 model
{cite}`lindstrom_development_1997` and the LISFLOOD
{cite}`van_der_knijff_lisflood_2010` (see for full documentation).

The upper zone represents a quick runoff component, which includes fast groundwater
and (vertical) subsurface flow through macro-pores in the soil. The lower zone
represents the slow groundwater component that generates the base flow.

The runoff from the upper zone to the channel, $Q_{uz}$, (mm),
(Q4 in {numref}`bucket_model`) equals:

$$Q_{uz} = \frac{1}{T_{uz}} \cdot UZ \cdot \Delta t$$

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

$$D_{uz,lz} = min(GW_{perc} \cdot \Delta t, UZ)$$

where $GW_{perc}$, [mm day-1], is the maximum percolation rate from the upper to
the lower groundwater zone. The runoff from the lower zone to the channel $Q_{lz}$,
(mm), (Q5 in {numref}`bucket_model`) is then computed by:

$$Q_{lz} = \frac{1}{T_{lz}} \cdot LZ \cdot \Delta t$$

$T_{lz}$ is the reservoir constant for the lower groundwater layer, (days),
and $LZ$ is the amount of water that is stored in the lower zone, (mm).
$LZ$ is computed as follows:

$$LZ = D_{uz,lz} - (GW_{loss} \cdot \Delta t)$$

where $D_{uz,lz}$ is the percolation from the upper groundwater zone, (mm),
and $GW_{loss}$ is the maximum percolation rate from the lower groundwater
zone, (mm day-1).

The amount of water defined by $GW_{loss}$ never rejoins the river channel and
is lost beyond the catchment boundaries or to deep groundwater systems. The larger
the value of $GW_{loss}$, the larger the amount of water that leaves the system.

## Across grid hydrology

The second part of the hydrology model calculates the horizontal water movement across
the full model grid including {term}`surface runoff` and {term}`sub-surface runoff`,
combined into {term}`local runoff generation` and eventually
{term}`total river discharge`.

Hereinafter, we refer to river discharge $Q$ to indicate the amount of water
passing a particular point of a river (m3 s−1), whereas total runoff $R$ is regarded as
the depth of water produced from a drainage area during a particular time interval (mm).

### Drainage map

The flow direction of water above and below ground is based on a digital elevation model
which needs to be provided as a NetCDF file at the start of the simulation.
Here an description of the steps that happen during the hydrology model
initialisation (plotting only for illustration):

```{code-cell} ipython3
# Read elevation data from NetCDF
import numpy as np
import xarray as xr
from xarray import DataArray

input_file = "../../_static/river_DEM.nc"
digital_elevation_model = xr.open_dataset(input_file)
elevation = digital_elevation_model["elevation"]
```

```{code-cell} ipython3
# Create Grid and Data objects and add elevation data
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.data import Data

grid = Grid(
    grid_type="square", cell_area=8100, cell_nx=9, cell_ny=9, xoff=-45, yoff=-45
)
data = Data(grid=grid)
data["elevation"] = elevation

# Plot elevation data on grid
import matplotlib.pyplot as plt
from matplotlib import colors

ele_plot = DataArray(
    data["elevation"].to_numpy().reshape((9, 9)),
    dims=("x", "y"),
    coords={"x": np.arange(9), "y": np.arange(9)},
)
plt.figure(figsize=(10, 6))
ele_plot.plot(cmap="terrain")
plt.title("Elevation, m")
plt.xlabel("x")
plt.ylabel("y")
plt.show()
```

The initialisation step of the hydrology model finds all the neighbours for each grid
cell and determine which neighbour has the lowest elevation. The code below returns the
neighbours of the grid cell with `cell_id = 56` as an example.

```{code-cell} ipython3
grid.set_neighbours(distance=100)
grid.neighbours[56]
```

Based on that relationship, the model determines all upstream neighbours
for each grid cell and creates a drainage map, i.e. a dictionary that contains for each
grid cell all upstream grid cells. For example, `cell_id = 34` has upstream cells
with the indices `[4, 13, 22]`. This gives the flow direction.

```{code-cell} ipython3
from virtual_ecosystem.models.hydrology.above_ground import calculate_drainage_map

drainage_map = calculate_drainage_map(
    grid=grid,
    elevation=np.array(data["elevation"]),
)
```

### Runoff and river discharge

We track horizontal water fluxes in two pathways — surface and subsurface runoff — and
then combine them into total river discharge.

#### Surface runoff ($R_{surface}$)

Water moving over the land surface into the river channel. For each cell, this includes:

* Local surface runoff: water generated within the cell during the current timestep.
* Upstream surface runoff: surface runoff generated in all upstream cells during the
  same timestep.

#### Subsurface runoff ($R_{subsurface}$)

Water moving laterally through soil and groundwater pathways towards the river channel.
For each cell, this includes:

* Local subsurface runoff: lateral + baseflow generated in the cell during the current
  timestep.
* Upstream subsurface runoff: subsurface runoff generated in upstream cells during the
  same timestep.

#### Total river discharge ($Q_{total}$)

The total volume passing through a cell’s channel ({term}`total river discharge`) is the
sum of these two pathways:

$$Q_{total} = R_{surface} + R_{subsurface}$$

This total volume can then be converted to a river discharge rate in cubic meters per
second (m3 s-1) using cell area and unit conversions.

```{code-cell} ipython3
from virtual_ecosystem.models.hydrology.above_ground import route_horizontal_flow

# Local runoff
subsurface_runoff = DataArray(np.full_like(data["elevation"], 1.0), dims="cell_id")
surface_runoff = DataArray(np.full_like(data["elevation"], 12), dims="cell_id")

# Total runoff = local runoff generation + upstream inflow
total_runoff = route_horizontal_flow(
    drainage_map=drainage_map,
    surface_runoff=surface_runoff,
    subsurface_runoff=subsurface_runoff,
)

# Reshape to 9x9 grid and plot total runoff map
reshaped_data = DataArray(
    total_runoff.reshape((9, 9)),
    dims=("x", "y"),
    coords={"x": np.arange(9), "y": np.arange(9)},
)

plt.figure(figsize=(10, 6))
reshaped_data.plot(cmap="Blues")
plt.title("Total runoff, mm")
plt.xlabel("x")
plt.ylabel("y")
plt.show()
```

```{code-cell} ipython3
from virtual_ecosystem.models.hydrology.above_ground import (
    convert_mm_flow_to_m3_per_second,
)

# Convert total runoff [mm] to river discharge rate [m3 s-1]
river_discharge_rate = convert_mm_flow_to_m3_per_second(
    river_discharge_mm=total_runoff,
    area=grid.cell_area,
    days=1,
    seconds_to_day=86400,
    meters_to_millimeters=1000,
)

# Reshape to 9x9 grid and plot river discharge rate
reshaped_data_rate = DataArray(
    river_discharge_rate.reshape((9, 9)),
    dims=("x", "y"),
    coords={"x": np.arange(9), "y": np.arange(9)},
)

plt.figure(figsize=(10, 6))
reshaped_data_rate.plot(cmap="Blues")
plt.title("River discharge rate, m3 s-1")
plt.xlabel("x")
plt.ylabel("y")
plt.show()
```

```{note}
To close the water balance, water needs to enter and leave the grid at some point. These
boundaries are currently not implemented.
```

## Generated variables

When the hydrology model initialises, it uses the input data to populate the following
variables. When the model first updates, it then sets further variables.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(
    generate_variable_table(
        "HydrologyModel", ["vars_populated_by_init", "vars_populated_by_first_update"]
    ),
    raw=True,
)
```

## Updated variables

The table below shows the complete set of model variables that are updated at each model
step.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(generate_variable_table("HydrologyModel", ["vars_updated"]), raw=True)
```
