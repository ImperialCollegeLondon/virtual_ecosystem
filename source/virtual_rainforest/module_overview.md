# The Virtual Rainforest modules

This document provides a brief overview of the modules that make up the Virtual Rainforest.


## Plant Module

The Plant Module models the primary production from plants in the Virtual
Rainforest. We use the P Model ({cite}`Prentice:2014bc,Wang:2017go`), to
estimate the optimal balance between water loss and photosynthetic productivity
and hence gross primary productivity (GPP). The P Model requires estimates of
the following drivers:

* Air temperature (°C)
* Vapour pressure deficit (VPD, Pa)
* Atmospheric pressure (Pa)
* Atmospheric CO2 concentration (parts per million)
* Fraction of absorbed photosynthetically active radiation ($F_{APAR}$,
  unitless)
* Photosynthetic photon flux density (PPFD, $\mu \text{mol}\, m^{-2}\, s^{-1}$)

GPP is then allocated to plant maintenance, respiration and growth using the T
Model ({cite}`Li:2014bc`). 

This growth model is used to simulate the demographics of cohorts of key
plant functional types (PFTs) under physiologically structured population models
developed in the [Plant-FATE](https://jaideep777.github.io/libpspm/) framework.
The framework uses the perfect-plasticity approximation (PPA,
{cite}`purves:2008a`) to model the canopy structure of the plant community, the
light environments of different PFTs and hence the change in the size-structured
demography of each PFT through time.

## Soils Module

## Animal Module

## Abiotic Module
The abiotic module provides the microclimate and hydrology for the Virtual Rainforest. The module contains four subroutines:

* Radiation (Net radiation and Photosynthetic photon flux density)
* Atmosphere (Air temperature and Relative humidity)
* Soil (Soil temperature and Soil moisture)
* Hydrology (Precipitation, Runoff, and Drainage)

In the first version of the module, the radiaton, atmosphere, and soil subroutines run as single-column models for each grid cell independently without horizontal exchange of information. Routines are run on a daily time step and provide daily outputs as well as monthly statistics (multivariate probability distributions) of atmospheric temperature/humidity and soil temperature/moisture for other modules.


## Disturbance Module
