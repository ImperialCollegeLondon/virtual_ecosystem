---
jupytext:
  formats: md:myst
  main_language: python
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
  version: 3.11.9
---

# Hydrology

This page provides an overview of the [key factors](#factors-affecting-hydrology)
influencing the hydrology of an ecosystem, the main processes that drive the
hydrological cycle at [local scale](#local-water-balance) and [catchment
scale](#catchment-scale-water-balance).

Hydrology only has a single implementation within the Virtual Ecosystem (the
`hydrology` model). Details of the actual equations used to simulate hydrology are
described in the [relevant section of the "How it works"
documentation](../implementation/hydrology_implementation.md)

## Definition

In the context of the Virtual Ecosystem, hydrology is defined as the distribution and
movement of water both on and below the Earth's surface as well as through organisms.

Water is crucial in an ecosystem for several reasons. It is essential for the survival
of all living organisms, providing the medium for biochemical reactions and cellular
processes. Further, water plays a key role in many ecosystem processes such as
photosynthesis, nutrient cycling, and the decomposition of organic matter. Water
facilitates the movement of nutrients and minerals within the soil which enables plant
growth and maintains soil health. Aquatic environments, such as rivers, lakes, and
wetlands, provide habitats for a wide range of species which supports biodiversity.
Additionally, water bodies influence microclimates by regulating temperatures through
heat absorption and release.

## Factors affecting hydrology

The hydrology on an ecosystem is mostly determined by macro- and microclimate,
topography, soil and geology, vegetation type and structure, and human activities such
as land use change.

### Climate

* **Precipitation**: The amount, timing, and type of precipitation (rain, snow, etc.)
  directly influence water availability and flow patterns.
* **Temperature**: Temperature affects evaporation rates and the amount of water that
  plants and soil can retain.
* **Evapotranspiration**: The combined process of evaporation and transpiration affects
  water loss from the surface to the atmosphere.

### Topography

* **Slope**: The steepness of the terrain affects how quickly water runs off the surface
  and infiltrates the soil.
* **Elevation**: Higher elevations tend to receive more precipitation, which impacts
  water flow and distribution.
* **Landforms**: Natural features such as mountains, valleys, and plains influence the
  direction and speed of water movement.

### Soil and Geology

* **Soil type**: Different soil types (sand, clay, loam) have varying capacities to
  retain and filter water.
* **Permeability**: The ability of soil and rock to absorb and transmit water affects
  groundwater recharge and surface runoff.
* **Rock formations**: The composition and structure of underlying rock formations
  influence groundwater storage and flow.

### Vegetation

* **Plant types**: Different species of plants have varying water needs and capacities
  to absorb and transpire water.
* **Density**: Dense vegetation can slow down surface runoff, enhance infiltration, and
  reduce soil erosion.
* **Root systems**: Deep and extensive root systems can increase soil stability and
  improve water infiltration and retention.

### Human activities

* **Deforestation**: Removing trees and vegetation decreases transpiration, increases
  runoff, and contributes to soil erosion.
* **Agriculture**: Irrigation, crop type, and farming practices influence water usage,
  runoff, and infiltration.
* **Water management practices**: Dams, reservoirs, and water diversion projects impact
  the natural distribution and availability of water.
* **Urbanization**: Development and construction alter natural water flow, increase
  surface runoff, and reduce infiltration.

## Key hydrological variables and processes

### Local water balance

The local water balance is, similar to the microclimate, driven by large scale
hydrological patterns and affects the living conditions for organisms at the local
scale. The local water balance can be represented by the equation:

$
\Delta S = P − ET − R
$ (water_balance)

where $\Delta S$ represents the net change in water stored in the system, $P$ stands for
precipitation, the total water input, $ET$ is the evapotranspiration with accounts for
water loss to the atmosphere, and runoff $R$ represents water that flows out of the
system.

The water balance include above and below ground processes that together describe the
flow of water through the system:

#### Above ground

* **Precipitation**: This includes all forms of water input from the atmosphere, such as
  rain, snow, sleet, and hail. The quantity and frequency of precipitation directly
  affect the amount of water entering the local system.

* **Intercept**: Some precipitation is caught and held by plant leaves, branches, and
  stems before it reaches the ground. This intercepted water can either evaporate back
  into the atmosphere or eventually drip to the soil.

* **Evapotranspiration**: Evaporation describes the process where water is converted
  from liquid to vapor and released into the atmosphere from surfaces like soil, water
  bodies, and vegetation. Transpiration rferns to the release of water vapor from plants
  into the atmosphere through small openings in their leaves called stomata. Combined,
  these processes account for water loss from the surface and vegetation to the
  atmosphere.

* **Surface runoff**: The portion of precipitation that flows over the land surface
  toward streams, rivers, and other water bodies. Runoff is influenced by factors such
  as land slope, soil saturation, and land use. High runoff can lead to erosion and
  nutrient loss.

#### Below ground

* **Infiltration**: The process where water on the ground surface enters the soil.
  Infiltration rates depend on soil type, soil moisture, land cover, and land management
  practices. Enhanced infiltration reduces surface runoff and recharges groundwater.
* **Bypass flow**: Some of the water that infiltarted into the soil bypasses the soil
  matrix and drains directly to the groundwater, for example through soil pipes.
* **Groundwater flow**: Water that infiltrates the soil can percolate down to recharge
  groundwater aquifers. Groundwater flow contributes to maintaining base flow in rivers
  and streams during dry periods. The rate of groundwater flow is determined by the
  permeability of subsurface materials and the hydraulic gradient.
* **Storage changes**: Water storage can occur in various forms such as soil moisture,
  surface water bodies (lakes, reservoirs), and groundwater. Changes in storage are
  influenced by the balance between inputs (precipitation) and outputs
  (evapotranspiration, runoff, groundwater flow).
* **Root water uptake**: A fraction of soil water is extracted by plants. On average,
  the amount of water extracted from soil is approximately the same as transpiration
  rates.

### Catchment scale water balance

At catchment scale, horizontal movement and distribution is considered. This includes
above and below ground flow of water.

* **Surface runoff and surface water flow**: Runoff represents the portion of
  precipitation that flows over the land surface and into streams, rivers, and lakes.
  Surface water flow dynamics are influenced by topography, soil characteristics, land
  cover, and human activities.
* **Groundwater Flow and Storage**: Water that infiltrates the soil can move
  horizontally through aquifers, contributing to groundwater storage. Horizontal
  groundwater flow interacts with surface water bodies, influencing base flow in rivers
  and streams.
