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

## Abiotic Model

The Abiotic Model provides the microclimate for the Virtual Ecosystem.
Using a small set of input variables from external sources such as reanalysis or
regional climate models, the model calculates atmospheric and soil parameters that
drive the dynamics of plants, animals, and microbes at different vertical levels:

- above canopy (canopy height + reference measurement height, typically 2m)
- canopy layers (maximum of ten layers, minimum one layers)
- subcanopy (2 m)
- surface layer (10 cm)
- soil layers (currently one near surface layer and one layer at 1 m below ground)

At the moment, the default option is a simple regression model that estimates
microclimate for a monthly time step. We are also working on a process-based abiotic
model that runs on a shorter time step, typically sub-daily, and could be used to run
the Virtual Ecosystem in high temporal resolution or for representative days per month.
Both versions of the abiotic model provide the following variables at different vertical
levels:

- Air temperature, relative humidity, and vapour pressure deficit
- Soil temperature
- Atmospheric $\ce{CO_{2}}$ concentration
- Atmospheric Pressure

### Simple Abiotic Model

The Simple Abiotic Model is a one-column model that operates on a grid cell basis and
does not consider horizontal exchange of energy, atmospheric water, and momentum.
The model uses linear regressions from {cite}`hardwick_relationship_2015` and
{cite}`jucker_canopy_2018` to predict
atmospheric temperature, relative humidity, and vapour pressure deficit
at ground level (1.5 m) given the above canopy conditions and leaf area index of
intervening canopy. A vertical profile across all atmospheric layers is then
interpolated using a logarithmic curve between the above canopy observation and ground
level prediction. Soil temperature is interpolated between the surface layer and the air
temperature at around 1 m depth which equals the mean annual temperature.
The model also provides a constant vertical profile of atmospheric pressure and
atmospheric $\ce{CO_{2}}$.

### Process-based Abiotic Model

The Process-based Abiotic Model will contain five subroutines: radiation, energy balance
, water balance, wind, and atmospheric $\ce{CO_{2}}$. The model will be based on the
'microclimc' model by {cite}`maclean_microclimc_2021`.

#### Radiation

The Radiation submodule calculates location-specific solar irradiance
(shortwave), reflection and scattering of shortwave radiation from canopy and surface,
vertical profile of net shortwave radiation, and outgoing longwave radiation from canopy
and surface. This will likely be replaced by the SPLASH model in the future.

#### Energy balance

The Energy balance submodule derives sensible and latent heat fluxes from canopy and
surface to the atmosphere, and updates air temperature, relative humidity, and vapor
pressure deficit at each level. The vertical mixing between levels is assumed to be
driven by heat conductance because turbulence is typically low below the canopy
{cite}`maclean_microclimc_2021`. Part of the net radiation is converted into soil heat
flux. The vertical exchange of heat between soil levels is coupled to the atmospheric
mixing.

#### Water balance

The Water balance submodule will link atmospheric humidity to the hydrology model and
coordinate the exchange of water between pools, i.e. between the soil, plants, animals,
and the atmosphere.

#### Wind

The wind submodule calculates the above- and within-canopy wind profiles for the Virtual
Ecosystem. These profiles will determine the exchange of heat, water, and $\ce{CO_{2}}$
between soil and atmosphere below the canopy as well as the exchange with the atmsophere
above the canopy.

#### Atmospheric $\ce{CO_{2}}$

The Atmospheric $\ce{CO_{2}}$ submodule will calculate the vertical profile of
atmospheric $\ce{CO_{2}}$ below the canopy. It will include the carbon assimilation/
respiration from plants and respiration from animals and soil microbes and mix
vertically depending on wind speed below the canopy.

## Hydrology Model

The Hydrology model simulates the hydrological processes in the Virtual Ecosystem. We
placed hydrology in a separate model in order to allow easy replacement with a different
hydrology model. Also, this provides more flexibility in defining the order of
models an/or processes in the overall Virtual Ecosystem workflow.

The first part of the Hydrology model determines the water balance within each
grid cell including rainfall, intercept, surface runoff out of the grid cell,
infiltration, percolation (= vertical flow), soil moisture profile, and
horizontal sub-surface flow out of the grid
cell.

The second part of the submodule calculates the water balance across the full model
grid including accumulated surface runoff, sub-surface flow, return flow, and streamflow
. This second part is still in development.

## Disturbance Model

Introducing disturbances (e.g. logging) into the model will usually require making
alterations to the state of multiple models. As such, different disturbance models are
collected in a separate Disturbance Model. This model will be capable of altering the
state of all the other models, and will do so in a manner that allows the source of the
changes to be explicitly identified.
