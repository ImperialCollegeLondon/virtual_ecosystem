# The Virtual Ecosystem models

This document provides a brief overview of the models that make up the Virtual
Ecosystem.

## Core Model

The `core` model is responsible for:

- **Model configuration**: running a model requires a configuration file to set the
  various options to be used. The `core` model provides loading and validation routines
  for this configuration.

- **Logger configuration**: the various models in the Virtual Ecosystem can emit a lot
  of logging information and the `core` model is used to set up the logging depth and
  log files.

- **Spatial grid setup**: a model typically contains individual cells to capture spatial
  heterogeneity and establish landscape scale processes. The `core` model supports the
  configuration of those cells and potentially mapping of habitats to cells.

- **Input validation**: once a model is configured, the `core` model is able to
  validate the various inputs to the model to make sure that they are consistent with
  the spatial grid configuration and each other.

- **Cell initiation and timekeeping**: each cell contains instances of the various
  models used to simulate behaviour within that cell. The `core` model sets up those
  instances.

- **Timekeeping**: the `core` model is also responsible for the timekeeping of the
  simulation - ensuring that the models execute the right commands at the right time.

## Abiotic Model

The Abiotic Model provides the three-dimensional microclimate for the Virtual Ecosystem.
Using a small set of input variables from external sources such as reanalysis or
regional climate models, the model calculates atmospheric and soil parameters that
drive the dynamics of plants, animals, and microbes at different vertical levels:

- above canopy (canopy height + reference measurement height, typically 2 m)
- canopy (dynamic heights provided by plant model)
- surface (10 cm above ground)
- topsoil (25 cm below ground)
- subsoil (minimum of one layer at 1 m depth)

At the moment, the default option is the
[abiotic_simple](../api/models/abiotic_simple.md) model, a simple regression
model that estimates microclimatic variables based on empirical data for a monthly
model timestep.
In parallel, we are working on a process-based
[abiotic](../api/models/abiotic.md) model, which will provide microclimate on
a (sub-)daily resolution. Both versions of the abiotic model provide the following key
variables at relevant vertical levels:

- Air temperature (°C), relative humidity (-), and vapour pressure deficit (VPD, kPa)
- Soil temperature (°C)
- Atmospheric $\ce{CO_{2}}$ concentration (ppm)
- Atmospheric Pressure (kPa)

### Simple Abiotic Model

The [abiotic_simple](../api/models/abiotic_simple.md) model is a one-column model
that operates on a grid cell basis and does not consider horizontal exchange of energy,
atmospheric water, and momentum. The model uses linear regressions from
{cite}`hardwick_relationship_2015` and {cite}`jucker_canopy_2018` to predict
atmospheric temperature, relative humidity, and vapour pressure deficit
at ground level (1.5 m) given the above canopy conditions and leaf area index of
intervening canopy. A vertical profile across all atmospheric layers is then
interpolated using a logarithmic curve between the above canopy observation and ground
level prediction. Soil temperature is interpolated between the surface layer and the
soil temperature at 1 m depth which roughly equals the mean annual temperature.
The model also provides a constant vertical profile of atmospheric pressure and
atmospheric $\ce{CO_{2}}$ based on external inputs.

### Process-based Abiotic Model

The process-based [abiotic](../api/models/abiotic.md) model will contain a sub-daily
mechanistic representation of the radiation balance, the energy
balance, and wind profiles. Submodules will be closely coupled to the hydrology and
plants models through the exchange of energy and water. The model will also provides a
constant vertical profile of atmospheric pressure and atmospheric $\ce{CO_{2}}$ based on
external inputs. Most processes will be calculated on a per grid cell basis; horizontal
exchange of properties will be considered at a later stage. The first model draft is
loosely based on the 'microclimc' model by {cite}`maclean_microclimc_2021`.

```{note}
Some of the features described here are not yet implemented.
```

#### Radiation balance

The radiation balance submodule will calculate location-specific solar irradiance
(shortwave), reflection and scattering of shortwave radiation from canopy and surface, a
vertical profile of net shortwave radiation, and outgoing longwave radiation from canopy
and surface. A basic version of the surface and canopy radiation balance is currently
included in the energy balance submodule.

#### Energy balance

The [energy balance](../api/models/abiotic/energy_balance.md) and
[soil energy balance](../api/models/abiotic/soil_energy_balance.md) submodules will
derive sensible and latent heat fluxes from canopy layers and surface to the atmosphere.
Part of the net radiation will be converted into soil heat flux. Based on these
turbulent fluxes, air temperature, canopy temperature, relative humidity, and soil
temperature will be updated simultaneously at each level. The vertical mixing between
layers is assumed to be driven by
[heat conductance](../api/models/abiotic/conductivities.md) because turbulence is
typically low below the canopy {cite}`maclean_microclimc_2021`.

#### Wind

The [wind](../api/models/abiotic/wind.md) submodule will calculate the above- and
within-canopy wind profiles for the Virtual Ecosystem. These profiles determine the
exchange of heat and water between soil and atmosphere below the canopy
as well as the exchange with the atmosphere above the canopy.

## Hydrology Model

The [hydrology](../api/models/hydrology.md) model simulates the hydrological
processes in the Virtual Ecosystem. We placed hydrology in a separate model to allow
easy replacement with a different hydrology model. Also, this separation provides more
flexibility in defining the order of models an/or processes in the overall Virtual
Ecosystem workflow.

```{note}
Some of the features described here are not yet implemented.
```

### Vertical hydrology components

The vertical component of the hydrology model determines the water balance within each
grid cell. This includes [above ground](../api/models/hydrology/above_ground.md)
processes such as rainfall, intercept, and surface runoff out of the grid cell.
The [below ground](../api/models/hydrology/below_ground.md) component considers
infiltration, bypass flow, percolation (= vertical flow), soil moisture and matric
potential, horizontal sub-surface flow out of the grid cell, and changes in
groundwater storage.
The model is loosely based on the LISFLOOD model {cite}`van_der_knijff_lisflood_2010`.

### Horizontal hydrology components

The second part of the hydrology model calculates the horizontal water movement across
the full model grid including accumulated surface runoff and sub-surface flow, and river
discharge rate, [see](../api/models/hydrology/above_ground.md). The flow direction is
based on a digital elevation model.

## Plant Model

The Plant Model models the primary production from plants in the Virtual Ecosystem. We
use the P Model {cite}`prentice_balancing_2014,wang_towards_2017`, to estimate the
optimal balance between water loss and photosynthetic productivity and hence gross
primary productivity (GPP). The P Model requires estimates of the following drivers:

- Air temperature (°C)
- Vapour pressure deficit (VPD, Pa)
- Atmospheric pressure (Pa)
- Atmospheric $\ce{CO_{2}}$ concentration (parts per million)
- Fraction of absorbed photosynthetically active radiation ($F_{APAR}$, unitless)
- Photosynthetic photon flux density (PPFD, $\mu \text{mol}, m^{-2}, s^{-1}$)

GPP is then allocated to plant maintenance, respiration and growth using the T Model
{cite}`li_simulation_2014`.

This growth model is used to simulate the demographics of cohorts of key plant
functional types (PFTs) under physiologically structured population models developed in
the [Plant-FATE](https://jaideep777.github.io/libpspm/) framework. The framework uses
the perfect-plasticity approximation (PPA, {cite:t}`purves_predicting_2008`) to model
the canopy structure of the plant community, the light environments of different PFTs
and hence the change in the size-structured demography of each PFT through time.

## Soil Model

The principal function of the Soil Model is to model the cycling of nutrients. This
cycling is assumed to be primarily driven by microbial activity, which in turn is
heavily impacted by both environmental and soil conditions. Plant-microbe interactions
are taken to principally be either exchanges of or competition for nutrients, and so are
modelled within the same nutrient cycling paradigm. Three specific nutrient cycles are
incorporated into this model:

### Carbon cycle

The Carbon cycle uses as its basic structure a recently described soil-pool model termed
the Millennial model {cite}`abramoff_millennial_2018`. This model splits carbon into
five separate pools: particulate organic matter, low molecular weight carbon (LMWC),
mineral associated organic matter, aggregates and microbial biomass. Though plant root
exudates feed directly into the LMWC pool, most biomass input will less direct and occur
via litter decomposition. Thus, we utilize a common set of litter pools
{cite}`kirschbaum_modelling_2002`, that are divided between above- and below-ground
pools, and by biomass source (e.g. deadwood).

### Nitrogen cycle

The Nitrogen cycle is strongly coupled to the carbon cycle, therefore tracking the
stoichiometry of the carbon pools is key to modelling it correctly. In addition,
specific forms of nitrogen are explicitly modelled. They are as follows: a combined
$\ce{NH_{3}}$ and $\ce{NH_{4}^{+}}$ pool to represent the products of nitrogen
fixation and ammonification, a $\ce{NO_{3}^{-}}$ pool to represent the products of
nitrification, and a $\ce{NO_{2}^{-}}$ pool to capture the process of denitrification.

### Phosphorous cycle

The Phosphorus cycle is similarly coupled to the carbon cycle. The additional inorganic
pools tracked in this case are as follows: primary phosphorus in the form of weatherable
minerals, mineral phosphorus which can be utilized by plants and microbes, secondary
phosphorus which is mineral associated but can be recovered as mineral phosphorus, and
occluded phosphorus which is irrecoverably bound within a mineral structure.

### Further details

Further theoretical background for the Soil Model can be found
[here](./soil/soil_details.md).

## Animal Model

The Animal Model simulates the animal consumers for the Virtual Ecosystem. We follow the
Madingley Model {cite}`harfoot_madingley_2014` to provide the foundational structure
as well as some of the dynamics. The key processes of the model are:

- foraging and trophic dynamics
- migration
- birth
- metamorphosis
- metabolism
- natural mortality

### Functional Groups

Animals within the Animal Model are sorted into functional groups, not biological
species. Functional groups share functional traits and body-mass ranges and
so behave similarly within the ecosystem. Defining a functional group within the
Animal Model requires the following traits:

- name
- taxa: mammal, bird, insect
- diet: herbivore, carnivore
- metabolic type: endothermic, ectothermic
- reproductive type: semelparous, iteroparous, nonreproductive
- development type: direct, indirect
- development status: adult, larval
- offspring functional group
- excretion type: ureotelic, uricotelic
- birth mass (kg)
- adult mass (kg)

A set of these functional groups are used to define an instance of the Animal Model.

### Animal Cohorts

Animals are represented as age-specific cohorts, containing many individuals of the
same functional type. The key Animal Model processes are run at the cohort level.
We track the internal state of the average individual of that cohort over time to
determine the resulting dynamics, such that events like starvation and metamorphosis
occur based on that cohort's internal state. Predator-prey interactions, likewise, occur
between animal cohorts as part of foraging system.

## Disturbance Model

Introducing disturbances (e.g. logging) into the model will usually require making
alterations to the state of multiple models. As such, different disturbance models are
collected in a separate Disturbance Model. This model will be capable of altering the
state of all the other models, and will do so in a manner that allows the source of the
changes to be explicitly identified.
