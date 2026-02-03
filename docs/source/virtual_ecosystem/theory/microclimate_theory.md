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

# Microclimate

This page provides an overview of the [key factors](#factors-affecting-microclimate)
influencing the microclimate of an ecosystem and the [main
processes](#balancing-energy-water-and-carbon) that drive the energy, carbon, and water
cycle.

Two alternative microclimate implementations exist in the Virtual Ecosystem the [simple
abiotic model](../implementation/abiotic_simple_implementation.md) and the
[process-based abiotic model](../implementation/abiotic_implementation.md). Details of
the actual equations used to simulate microclimate are to be found there.

## Definition

Microclimates are defined as the local climate conditions that organisms and ecosystems
are exposed to. In terrestrial ecosystems, microclimates often deviate strongly from the
climate representative of a large geographic region, the macroclimate
{cite}`kemppinen_microclimate_2024`. For example, the temperature directly above a
rainforest canopy might be modulated due to small scale variations in topography and
aspect. The temperature above the canopy is typically several degrees higher than near
the surface, the surface under a dense canopy tends to be cooler than unshaded surface
spots, and temperatures generally decrease with elevation.

Many ecosystems have a high spatial variability of microclimates providing suitable
habitats for a diverse range of species. Scales of microclimates typically range between
0.1-100 m horizontally, 10-100 m vertically, and seconds to minutes temporally
{cite}`bramer_chapter_2018`.

## Factors affecting microclimate

Microclimates are mediated by macroclimate, topography, vegetation type and structure,
and soil. Many of these factors can be affected by human cativities, for example through
deforestation and other land use changes.

### Macroclimate

* **Solar radiation**: The latitude and associated seasonal changes of the sun angle
  determine the amount of solar energy received at a location. Local features like tree
  cover can create microclimatic variations in sunlight exposure.
* **Baseline temperature**: Macroclimate establishes the general temperature range for a
  region. Local features can cause variations within this range (e.g., heat islands,
  shaded areas).
* **Precipitation patterns**: The overall amount and distribution of precipitation are
  dictated by macroclimate. Local factors such as topography can modify precipitation
  (e.g., rain shadows, increased moisture in valleys).
* **Wind patterns**: Large-scale atmospheric circulation influences regional wind
  patterns. Local topography and vegetation structures can alter wind flow, leading to
  microclimatic differences.
* **Humidity levels**: The macroclimate sets the general humidity level of an area.
  Proximity to water bodies, vegetation density, and soil moisture can create localized
  variations.
* **Seasonal variations**: Seasonal changes in temperature, precipitation, and solar
  radiation are governed by the macroclimate.

### Topography

* **Elevation**: The height above sea level affects temperature, pressure, and
  precipitation. Higher areas tend to be cooler, have a lower pressure, and have a
  higher chance of receiving precipitation as snow.
* **Slope and aspect**: The angle and direction of a slope influence sunlight exposure,
  wind exposure, and water runoff. This can affect microclimate directly (e.g.
  temperature, moisture availability) and indirectly (e.g. soil erosion changes surface
  properties).

### Vegetation

* **Leaf Area Index (LAI)**: The leaf area per unit ground area influences light
  penetration, temperature, and humidity. LAI is an important factor in determining the
  productivity and energy balance of an ecosystem.
* **Canopy cover**: The proportion of the ground covered by the vertical projection of
  tree crowns affects light availability, wind patterns, and temperature.
* **Plant height**: The height of vegetation can influence wind patterns, shading, and
  temperature.

### Soil

* **Soil albedo**: The reflectivity of the soil determines how much incoming solar
  radiation is reflected to the sky.
* **Soil type**: The soil type affects the thermal and hydraulic properties of the soil
  which determine how well heat is stored and conducted and how easily water
  infiltrates, evaporates, and percolates through the soil.
* **Soil moisture**: Soil moisture is a key factor in partitioning turbulent fluxes at
  the surface. Evaporative cooling and the associated buffering effect of vegetation of
  maximum temperatures.

## Balancing energy, water, and carbon

The dynamics of microclimate in a terrestrial ecosystem in primarily driven by five key
components: radiation balance, energy balance, water balance, carbon balance, and
turbulent transfer (see {numref}`abiotic_sketch`). These components are connected
through the exchange of energy, water, and carbon and can be described with the general
energy balance equation:

$$
\begin{align}
\frac{dQ}{dt} & = (1 - \alpha) S_\downarrow + L_\downarrow - \epsilon \sigma
  (T_{sfc} + 273.15)^4 \\
  & = H + L_{v}E + G + PP
\end{align}
$$

where $\frac{dQ}{dt}$ is the change in heat storage, $\alpha$ is the surface albedo,
$S_\downarrow$ and $L_\downarrow$ are downwelling shortwave and longwave radiation,
respectively. $\epsilon$ is the emissivity of the surface, $\sigma$ is the
Stefan-Boltzmann constant, and $T_sfc$ is the surface temperature in Celsius. $H$ is the
sensible heat flux, $\lambda E$ is the latent heat flux, $G$ is the ground heat flux,
and $PP$ stands for primary productivity.

* **Radiation balance**: The radiation balance refers to the equilibrium between
  incoming solar radiation and outgoing terrestrial radiation within an ecosystem. How
  much radiation is reflected, scattered and absorbed depends on the albedo and
  structure of the surface and vegetation.
* **Energy balance**: The energy balance describes the equilibrium of absorbed and
  released energy at a surface, for example the soil surface or the canopy. This balance
  is closely coupled to the radiation balance through net radiation, which is
  partitioned into turbulent fluxes (latent, sensible, and ground heat flux), used for
  photosynthesis, and changes in heat storage.
* **Water balance**: The water balance refers to the equilibrium of absorbed and
  released water by different (here abiotic) ecosystem components. This balance is
  linked to the energy balance via evapotranspiration and latent heat flux from the soil
  surface. Beyond the local water balance, we also consider [hydrology at the catchment
  scale](./hydrology_theory.md).
* **Carbon balance**: The carbon balance is linked to the radiation, energy and water
  balance by net primary productivity: the conversion of light, atmospheric carbon,
  water, (and nutrients) into biomass minus respiration. The carbon cycle continues as
  plant biomass is either eaten by herbivores or falls to the ground where it is
  decomposed. If not respired by animals or plants, carbon enters the soil where it is
  and eventually recycled to the atmosphere.
* **Turbulent transfer**: The turbulent transfer and wind mix all the atmospheric
  properties vertically and horizontally, leading to ecosystem characteristic patterns
  and profiles of microclimatic variables.
