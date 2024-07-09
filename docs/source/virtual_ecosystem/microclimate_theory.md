# Microclimate

This page provides an overview of the [key factors](#factors-affecting-microclimate)
influencing the microclimate of an ecosystem, the
[main processes](#balancing-energy-water-and-carbon) that drive the energy, carbon, and
water cycle,
required [input and state variables](#key-microclimatic-variables) used to
estimate these processes and
the [interactions with biotic process](#links-to-biotic-components).
Further, this page offers a brief overview over
microclimate [data collection](#microclimate-data-collection) and
[modelling](#microclimate-modelling) approaches as well as open
[challenges and limitations](#challenges-and-limitations) in microclimate research.

## Definition

Microclimates are defined as the local climate conditions that organisms and ecosystems
are exposed to. In terrestrial ecosystems, microclimates often deviate strongly from the
climate representative of a large geographic region, the macroclimate
{cite}`kemppinen_microclimate_2024`.
For example, the temperature directly above a rainforest canopy might be modulated
due to small scale variations in topography and aspect. The temperature above the canopy
is typically several degrees higher than near the surface, the surface
under a dense canopy tends to be cooler than unshaded surface spots, and temperatures
generally decrease with elevation.

Many ecosystems have a high spatial variability of microclimates providing
suitable habitats for a diverse range of species. Scales of microclimates typically
range between 0.1-100 m horizontally, 10-100 m vertically, and seconds to minutes
temporally {cite}`bramer_chapter_2018`.

## Factors affecting microclimate

Microclimates are mediated by macroclimate, topography, vegetation tye and structure, and
soil. Many of these factors can be affected by human cativities, for example through
deforestation and other land use changes.

### Macroclimate

* **Solar radiation**: The latitude and associated seasonal changes of the sun angle determine
the amount of solar energy received at a location. Local features like tree cover can
create microclimatic variations in sunlight exposure.
* **Baseline temperature**: Macroclimate establishes the general temperature range for a
region. Local features can cause variations within this range (e.g., heat islands,
shaded areas).
* **Precipitation patterns**: The overall amount and distribution of precipitation are
dictated by macroclimate. Local factors such as topography can modify precipitation
(e.g., rain shadows, increased moisture in valleys).
* **Wind patterns**: Large-scale atmospheric circulation influences
regional wind patterns. Local topography and vegetation structures can alter wind flow,
leading to microclimatic differences.
* **Humidity levels**: The macroclimate sets the general humidity level of an area.
Proximity to water bodies, vegetation density, and soil moisture can create localized
variations.
* **Seasonal variations**: Seasonal changes in temperature, precipitation, and solar
radiation are governed by the macroclimate.

### Topography

* **Elevation**: The height above sea level affects temperature, pressure, and
precipitation. Higher areas tend to be cooler, have a lower pressure, and have a higher
chance of receiving precipitation as snow.
* **Slope and aspect**: The angle and direction of a slope influence sunlight exposure,
wind exposure, and water runoff. This can affect microclimate directly (e.g. temperature
, moisture availability) and indirectly (e.g. soil erosion changes surface properties).

### Vegetation

* **Leaf Area Index (LAI)**: The leaf area per unit ground area influences light
penetration, temperature, and humidity. LAI is an important factor in determining the
productivity and energy balance of an ecosystem.
* **Canopy cover**: The proportion of the ground covered by the vertical projection of
tree crowns affects light availability, wind patterns, and temperature.
* **Plant height**: The height of vegetation can influence wind patterns, shading,
and temperature.

### Soil

* **Soil albedo**: The reflectivity of the soil determines how much incoming solar
radiation is reflected to the sky.
* **Soil type**: The soil type affects the thermal and hydraulic properties of the soil
which determine how well heat is stored and conducted and how easily water infiltrates,
evaporates, and percolates through the soil.
* **Soil moisture**: Soil moisture is a key factor in partitioning turbulent fluxes at
the surface. Evaporative cooling and the associated buffering effect of vegetation of
maximum temperatures.

## Balancing energy, water, and carbon

The dynamics of microclimate in a terrestrial ecosystem in primarily driven by five key
components: radiation balance, energy balance, water balance, carbon balance, and
turbulent transfer (see [Figure x](./abiotic_theory.md)). These components are connected
through the exchange of
energy, water, and carbon and can be described with the general energy balance equation:

$$
R_N & = (1 - \alpha) S_\downarrow + L_\downarrow - \epsilon \sigma (T_{sfc} + 273.15)^4 \\
    & = H + L_{v}E + G + NPP
$$

where $R_N$ is the net radiation at the surface, $\alpha$ is the surface albedo,
$S_\downarrow$ and $L_\downarrow$ are downwelling shortwave and longwave radiation,
respectively. $\epsilon$ is the emissivity of the surface, $\sigma$ is the
Stefan-Boltzmann constant, and $T_sfc$ is the surface temperature in Celsius.
$H$ is the sensible heat flux, $L_v E$ is the latent heat flux, $G$ is the ground heat
flux, and $NPP$ stands for net primary productivity.

* **Radiation balance**: The radiation balance refers to the equilibrium between incoming
solar radiation and outgoing terrestrial radiation within an ecosystem. How much
radiation is reflected, scattered and absorbed depends on the albedo and structure of
the surface and vegetation.
* **Energy balance**: The energy balance describes the equilibrium of absorbed and released
energy at a surface, for example the soil surface or the canopy. This balance is closely
coupled to the radiation balance through net radiation, which is partitioned into
turbulent fluxes (latent, sensible, and ground heat flux), used for photosynthesis, and
changes in heat storage.
* **Water balance**: The water balance refers to the equilibrium of absorbed and released
water by different (here abiotic) ecosystem components. This balance is linked to the
energy balance via evapotranspiration and latent heat flux from the soil surface.
The hydrology on catchment scale is described in more detail [here](./hydrology_theory.md).
* **Carbon balance**: The carbon balance is linked to the radiation, energy and water
balance by net primary productivity: the conversion of light, atmospheric carbon, water,
(and nutrients) into biomass minus respiration. The carbon cycle continues as plant biomass
is either eaten by herbivores or falls to the ground where it is decomposed. If not
respired by animals or plants, carbon enters the soil where it is and eventually
recycled to the atmosphere.
* **Turbulent transfer**: The turbulent transfer and wind mix all the atmospheric
properties vertically and horizontally, leading to ecosystem characteristic patterns and
profiles of microclimatic variables.

## Key microclimatic variables

### Solar Radiation

* **Direct solar radiation**: Sunlight that reaches the surface directly from the sun
affects temperatures, photosynthesis in plants, and the energy balance of an area.
* **Diffuse solar radiation**: Sunlight scattered by molecules and particles in the
atmosphere is essential for plant growth in shaded or cloudy conditions.
* **Photosynthetically Active Radiation (PAR)**: PAR is the portion of sunlight
(400-700 nm wavelength) that plants use for photosynthesis.

### Temperature

* **Air temperature**: Air temperature at different vertical levels within and below
vegetation cover is probably the most important microclimate variable because it
determines metabolic rates, growth, and survival of organisms.
* **Soil temperature**: The temperature of the soil at various depths affects plant
growth, root activity, and microbial activity. Soil temperature can significantly differ
from air temperature due to soil composition and moisture content.
* **Surface temperature**: The temperature of the ground or other surfaces can be
significantly different from the air temperature above; often it is much hotter.

### Humidity

* **Relative humidity**: The percentage of moisture in the air relative to the maximum
amount the air can hold at that temperature. It impacts endotherm comfort, plant
transpiration, and microbial activity.
* **Vapour pressure deficit (VPD)**: The difference between the amount of
moisture in the air and how much moisture the air can hold when it is saturated. VPD is a
crucial factor for plant transpiration and water stress; higher VPD indicates a greater
potential for evaporation and transpiration.
* **Soil moisture**: The amount of water contained within soil affects evaporation rates
, soil microbial activity, and the availability of water for plants.
* **Soil matric potential**: Soil matric potential refers to the energy status of water
in soil which represents the force per unit area that the soil matrix exerts on water due
to capillary and adsorptive forces. It influences the movement and availability of water
to plants, with lower values indicating drier conditions and higher values indicating
wetter conditions.

### Wind

* **Wind Speed**: The rate at which air is moving horizontally influences
temperature regulation, evaporation rates, and the dispersion of atmospheric gasses.
* **Wind Direction**: The direction from which the wind is blowing affects microclimate
by influencing temperature distribution, humidity, and the transport of seeds and pollen.
* **Turbulence**: Turbulence refers to the irregular, chaotic movement of air that affects
the mixing of atmospheric elements. Turbulence influences heat exchange, moisture
distribution, and the dispersion of aerosols.

### Precipitation

* **Rainfall**: The amount of rain that falls in a given area over a specific period.
Rainfall is vital for replenishing water sources and maintaining soil moisture.
* **Snowfall**: The amount of snow that falls, which can be measured as snow depth or water
equivalent. Snowfall influences temperature regulation, soil moisture, and water supply.
* **Dew and Frost**: The formation of water droplets or ice crystals on surfaces, which can
affect plant health and soil conditions. Dew and frost are critical in areas where
precipitation is low.

### Atmospheric Pressure

Barometric pressure describes the pressure exerted by the atmosphere at a given point.
Pressure decreases with height and influences weather patterns; changes in atmospheric
pressure can indicate upcoming weather changes, such as storms.

### Atmospheric $\ce{CO_{2}}$

Although atmospheric $\ce{CO_{2}}$ is not a microclimatic variable, it is closely tied
in the balance of energy through its critical role in photosynthesis. It should therefore
be considered when studying the dynamics on ecosystems.

## Links to biotic components

Microclimates affect biota in a number of ways. Physically, microclimate shapes the
3-dimensional vegetation structure that organisms live in. Physiologically, temperatures
in particular affect metabolic rates. Further, microclimates drive behaviour, species
interactions, and evolutionary processes.

### Habitat suitability

* **Temperature**: Microclimatic temperature variations influence the distribution and
behaviour of organisms. Certain species thrive in specific temperature ranges provided by
microclimates.
* **Moisture availability**: Local soil moisture and humidity levels determine the types
of plants and animals that can survive in an area, affecting germination, growth, and
reproduction.
* **Light levels**: Microclimatic variations in sunlight due to canopy cover or terrain
affect photosynthesis rates and plant growth.
* **Soil conditions**: Microclimate influences soil temperature, moisture, and nutrient
availability, which are critical for plant productivity and microbial activity.

### Animal behaviour and distribution

* **Thermal regulation**: Animals use microclimatic variations to regulate their body
temperature, such as basking in sunny areas or seeking shade.
* **Foraging and nesting**: Microclimatic conditions affect the availability of food
resources and suitable nesting sites for animals.

### Species interactions

* **Competition and predation**: Microclimates can create microhabitats that support
different species, influencing competition and predation dynamics.
* **Pollination and seed dispersal**: Microclimatic conditions affect the activity of
pollinators and the dispersal mechanisms of seeds, shaping plant reproduction and
distribution.

### Microbial activity

* **Decomposition Rates**: Soil moisture and temperature, influenced by microclimate,
affect the activity of decomposers and nutrient cycling in ecosystems.
* **Soil Microbiome**: Microclimatic conditions influence the diversity and function of
soil microbial communities, impacting soil health and plant growth.

### Adaptation and evolution

* **Local Adaptations**: Organisms may develop specific adaptations to survive in the unique
conditions of their microclimate, leading to genetic diversity.
* **Microclimatic Niches**: Species may exploit distinct microclimatic niches, reducing
competition and promoting biodiversity within an ecosystem.

### Stress and resilience

* **Environmental Stressors**: Microclimatic extremes (e.g., drought, frost) can impose
stress on biota, affecting survival and reproductive success.
* **Refugia**: Microclimates can offer refugia for species when macroclimatic conditions
become unfavourable, e.g. under climate change or during extreme events.
* **Resilience Mechanisms**: Biota may develop resilience mechanisms such as dormancy,
migration, or phenotypic plasticity to cope with microclimatic variability.

## Methods for microclimate science

This section gives a broad overview over common methods and models in microclimate
research. Recent advances in data aquisition for microclimate research and microclimate
modelling are provided in a comprehensive review by {cite:t}`kemppinen_microclimate_2024`.

### Microclimate data collection

Effective microclimate modelling relies on accurate data collection, ideally from a
combination of sources:

* **Meteorological stations**: Meteorological stations provide detailed, real-time data
on temperature, humidity, wind speed, and solar radiation for locations across an area.
* **Remote sensing**: Satellites, planes, drones, and other technologies offer
extensive spatial coverage, capturing data on land surface temperatures and
vegetation health.
* **In-situ measurements**: Ground-based sensors complement provide high-resolution data
on specific local conditions.
* **Reanalysis**: Reanalysis data sets such as ERA5 represent a combination of observations
and modelling which can complement measurements by filling gaps in spatial cover and timeseries.

### Microclimate modelling

Microclimate models use various computational approaches to simulate the interactions
between atmospheric, terrestrial, and hydrological processes:

* **Energy balance models** calculate the exchange of energy between the surface and the
atmosphere, accounting for factors like radiation, convection, and conduction.
* **Statistical models** utilize historical data to identify patterns and predict future
conditions.
* **Process-based models**, which incorporate physical laws and biological processes,
offer a detailed simulation of microclimate dynamics over time and space, providing
insights into how changes in one factor may impact the entire system.

## Challenges and limitations

* **Data availability and quality**: Microclimate models require high-resolution, long-term
meteorological data for calibration and validation. Most ecosystems, especially in
remote areas, lack sufficient weather stations and ground observations to offer the data
required to model microclimate accurately.
* **Computational resources**: High-resolution microclimate models can be computationally
intensive, requiring significant processing power and time.
* **Model complexity**: Accurately simulating microclimate processes involves complex
interactions between various atmospheric, terrestrial, and hydrological factors. Not all
of these interactions are well understood. Simplifications and assumptions necessary for
computational feasibility can reduce model accuracy.
* **Parameter sensitivity**: Microclimate models are highly sensitive to input parameters
such as soil moisture, vegetation cover, and land surface properties. Small errors in
these parameters can lead to significant deviations in model outputs.
* **Representation of extreme events**: Accurately modelling extreme weather events with
high spatial and temporal precision (e.g., heatwaves, storms) is difficult due to their
complex and unpredictable nature. However, these events can have disproportionate impacts
on ecosystem dynamics and in particular mortality rates.
* **Integration with other models**: Combining microclimate models with broader
ecological or hydrological models involves addressing compatibility and consistency issues.
This includes for example interconnected processes happing at different time scales.
* **Human impacts**: Incorporating the effects of human activities (e.g. urbanization,
land use changes, conservation actions) into microclimate models adds another layer of
complexity.
