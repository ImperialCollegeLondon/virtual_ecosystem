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

The abiotic module provides the microclimate and hydrology for the Virtual Rainforest. 
The module contains three subroutines:

* Radiation balance
* Energy balance
* Water balance

The <b>Radiation balance</b> subroutine uses incoming solar radiation and vegetation 
structure to calculate vertical profiles of Net radiation and Photosynthetic photon 
flux density.

The <b>Energy balance</b> subroutine calculates 1) sensible heat flux from leaves and 
soil, 2) latent heat flux from leaves and soil based on the Penman-Monteith 
(or Priestley–Taylor) equation, and 3) soil heat flux based on Fourier's law. 
The output of the subroutine includes vertical profiles of atmospheric temperature, 
relative humidity, and soil temperature. In the first version of the module, energy 
balance subroutine runs as single-column model for each grid cell independently 
without horizontal exchange of information. 

The <b>Water balance</b> subroutine uses rainfall to calculate runoff, infiltration, 
soil moisture, and drainage. The outputs include vertical soil moisture profiles, 
average vertical flow, and horizontal flows between grid cells.

All routines run on a daily time step and provide daily outputs as 
well as monthly statistics (multivariate probability distributions) of atmospheric 
temperature/humidity, soil temperature/moisture, and hydrological parameters.

## Disturbance Module

Introducing disturbances (e.g. logging) into the model will usually require making
alterations to the state of multiple modules. As such, different disturbance models are
collected in a seperate disturbance module. This module will be capable of altering the
state of all the other modules, and will do so in a manner that allows the source of the
changes to be explicitly identified.
