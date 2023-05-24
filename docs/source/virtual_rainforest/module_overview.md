# The Virtual Rainforest modules

This document provides a brief overview of the modules that make up the Virtual
Rainforest.

## Core Module

The `core` module is responsible for:

- **Model configuration**: running a model requires a configuration file to set the
  various options to be used. The `core` module provides loading and validation routines
  for this configuration.

- **Logger configuration**: the various modules in the model can emit a lot of logging
  information and the `core` module is used to set up the logging depth and log files.

- **Spatial grid setup**: a model typically contains individual cells to capture spatial
  heterogeneity and establish landscape scale processes. The `core` module supports the
  configuration of those cells and potentially mapping of habitats to cells.

- **Input validation**: once a model is configured, the `core` module is able to
  validate the various inputs to the model to make sure that they are consistent with
  the spatial grid configuration and each other.

- **Cell initiation and timekeeping**: each cell contains instances of the various
  modules used to simulate behaviour within that cell. The `core` module sets up those
  instances.

- **Timekeeping**: the `core` module is also responsible for the timekeeping of the
  simulation - ensuring that the modules execute the right commands at the right time.

## Plant Module

The Plant Module models the primary production from plants in the Virtual Rainforest. We
use the P Model {cite}`prentice_balancing_2014,wang_towards_2017`, to estimate the
optimal balance between water loss and photosynthetic productivity and hence gross
primary productivity (GPP). The P Model requires estimates of the following drivers:

- Air temperature (°C)
- Vapour pressure deficit (VPD, Pa)
- Atmospheric pressure (Pa)
- Atmospheric CO2 concentration (parts per million)
- Fraction of absorbed photosynthetically active radiation ($F_{APAR}$, unitless)
- Photosynthetic photon flux density (PPFD, $\mu \text{mol}, m^{-2}, s^{-1}$)

GPP is then allocated to plant maintenance, respiration and growth using the T Model
{cite}`li_simulation_2014`.

This growth model is used to simulate the demographics of cohorts of key plant
functional types (PFTs) under physiologically structured population models developed in
the [Plant-FATE](https://jaideep777.github.io/libpspm/) framework. The framework uses
the perfect-plasticity approximation (PPA, {cite:t}`purves_predicting_2008`) to model the
canopy structure of the plant community, the light environments of different PFTs and
hence the change in the size-structured demography of each PFT through time.

## Soil Module

The principal function of the Soil Module is to model the cycling of nutrients. This
cycling is assumed to be primarily driven by microbial activity, which in turn is
heavily impacted by both environmental and soil conditions. Plant-microbe interactions
are taken to principally be either exchanges of or competition for nutrients, and so are
modelled within the same nutrient cycling paradigm. Three specific nutrient cycles are
incorporated into this module:

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

Further theoretical background for the soil module can be found
[here](./soil/soil_details.md).

## Animal Module

## Abiotic Module

The abiotic module provides the microclimate and hydrology for the Virtual Rainforest.
Using a small set of input variables from external sources such as reanalysis or
regional climate models, the module calculates atmospheric and soil parameters that
drive the dynamics of plants, animals, and microbes at different vertical levels:

- above canopy (canopy height + reference measurement height, typically 2m)
- canopy layers (maximum of ten layers, minimum one layers)
- subcanopy (2 m)
- surface layer (10 cm)
- soil layers (currently one near surface layer and one layer at 1 m below ground)

At the moment, the default option is a simple regression based model that estimates
microclimate for a monthly time step. We are also working on a process-based abiotic
model that runs on a shorter time step, typically sub-daily, and could be used to run
the Virtual Rainforest in high temporal resolution or for representative days per month.

### Abiotic simple model

The abiotic simple model uses linear regressions from
{cite}`hardwick_relationship_2015` and {cite}`jucker_canopy_2018` to predict
atmospheric temperature and relative humidity at ground level (2m) given the above
canopy conditions and leaf area index of intervening canopy. A within canopy profile is
then interpolated using a logarithmic curve between the above canopy observation and
ground level prediction.
Soil temperature is interpolated between the surface layer and the air temperature at
1 m depth which equals the mean annual temperature.
The moduel also provides a constant vertical profile of atmospheric pressure and
$\ce{CO_{2}}$.
Soil moisture and surface runoff are calculated with a simple bucket model based on
{cite}`davis_simple_2017`; vertical flow is currently not implemented.

### Process-based abiotic model

The process-based abiotic model contains four subroutines - the radiation balance, the
energy balance, the water balance, and the atmospheric $\ce{CO_{2}}$ balance - provide
the following variables at different vertical levels:

- Net radiation and Photosynthetic photon flux density
- Air temperature, relative humidity, and vapour pressure deficit
- Soil temperature and soil moisture
- Atmospheric $\ce{CO_{2}}$ concentration
- above- and belowground runoff, mean vertical flow, and streamflow (at catchment scale)

#### The Radiation balance

The radiation balance submodule calculates location-specific solar irradiance
(shortwave), reflection and scattering of shortwave radiation from canopy and surface,
vertical profile of net shortwave radiation, and outgoing longwave radiation from canopy
and surface.

#### The Energy balance

The Energy balance submodule derives sensible and latent heat fluxes from canopy and
surface to the atmosphere, and updates air temperature, relative humidity, and vapor
pressure deficit at each level. The vertical mixing between levels is assumed to be
driven by heat conductance because turbulence is typically low below the canopy
{cite}`maclean_microclimc_2021`. Part of the net radiation is converted into soil heat
flux. The vertical exchange of heat between soil levels is coupled to the atmospheric
mixing.

#### The Water balance

The first part of the water balance submodule determines the water balance within each
grid cell including rainfall, intercept, throughfall and stemflow, surface water storage
(= depression storage), surface runoff out of the grid cell (= overland flow),
infiltration, percolation (= vertical flow), soil moisture profile, water table depth,
and subsurface flow out of the grid cell.

The second part of the module caluclates the water balance across the full model grid
based on the TOPMODEL (e.g. {cite:t}`metcalfe_dynamic_2015`) including surface runoff,
subsurface flow, return flow, and streamflow.

#### The atmospheric $\ce{CO_{2}}$ balance

The atmospheric $\ce{CO_{2}}$ submodule calculates the vertical profile of atmospheric
$\ce{CO_{2}}$ below the canopy. It takes into account the carbon assimilation/
respiration from plants and respiration from animals and soil microbes and mixes
vertically depending on wind speed below the canopy.

## Disturbance Module

Introducing disturbances (e.g. logging) into the model will usually require making
alterations to the state of multiple modules. As such, different disturbance models are
collected in a separate Disturbance Module. This module will be capable of altering the
state of all the other modules, and will do so in a manner that allows the source of the
changes to be explicitly identified.
