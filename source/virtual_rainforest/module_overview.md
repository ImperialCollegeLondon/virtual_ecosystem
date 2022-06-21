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
The abiotic module provides the microclimate and hydrology for the Virtual Rainforest. The module contains five subroutines:
- Radiation (Net radiation and Photosynthetic photon flux density)
- Hydrology (Precipitation, Runoff, and Soil moisture)
- Atmospheric humidity
- Atmospheric temperature
- Soil temperature

In the first version of the module, these five subroutines calculate vertical profiles of net radiation, Photosynthetic photon flux density, Soil temperature/moisture, and Atmospheric temperature/humidity for each grid cell independently without horizontal exchange of information. Routines are run on a daily time step and provide daily outputs as well as monthly statistics of atmospheric temperature/humidity and soil temperature/moisture for other modules.

### 1. Radiation
The calculation of Net radiation ($H_{N}$) and Photosynthetic photon flux density (PPFD, $\mu \text{mol}\, m^{-2}\, s^{-1}$) is based on the SPLASH model {cite}`Davis:2017`. 

The calculation begins with modeling the extraterrestrial solar flux, $I_0$ ($\text {W m}^{−2}$), as a function of the solar constant, a distance factor, and an inclination factor. 

The daily top-of-the-atmosphere solar radiation, $H_0$ ($\text {J m}^{−2}$), is calculated as twice the integral of $I_0$ measured between solar noon and the sunset angle, $h_s$, assuming that all angles related to Earth on its orbit are constant over a whole day.

The net surface radiation, $H_N$($\text {J m}^{−2}$), is the integral of the net surface radiation flux received at the land surface, $I_N$ ($\text {W m}^{−2}$), which is classically defined as the difference between the net incoming shortwave radiation flux, $I_{SW}$ ($\text {W m}^{−2}$) and the net outgoing long-wave radiation flux, $I_{LW}$ ($\text {W m}^{−2}$)). Both $I_{SW}$ and $I_{LW}$ can be calculated internally or taken from regional climate models. For calculations later on in the subroutine, $H_N$ is split in a positive $H_N^+$ and negative $H_N^-$ component.

The vertical profile of $H_N$ is calculated by reduction of radiation based on Leaf area index, leaf transmissivity factor, and depth of each layer.

The $PPFD$ is calculated is calculated based on the number of quanta received (moles of photons) within the visible light spectrum, which also corresponds to the action spectrum of photosynthesis (Monteith and Unsworth, 1990).

The vertical profile of $PPFD$ is calculated by reduction based on Leaf area index, light absorption factor, and depth of each layer.

### 2. Hydrology
Daily soil moisture, $W_n$ (mm), is calculated based on the previous day’s moisture content, $W_{n−1}$, incremented by daily precipitation, $P_n$ ($\text{mm d}^{−1}$), and condensation, $C_n$ ($\text {mm d}^{−1}$), and reduced by daily actual evapotranspiration,$E^a_n$ ($\text {mm d}^{−1}$), and runoff, $RO$ (mm) based on the SPLASH model {cite}`Davis:2017`:

$W_n = W_{n−1} + P_n + C_n − E^a_n − RO$

$P_n$ is a model input, $C_n$ is estimated based on the daily negative net radiation, $E^a_n$ is the analytical integral of the
minimum of the instantaneous evaporative supply and demand rates over a single day, and $RO$ is the amount of soil moisture in excess of the holding capacity.

Under steady-state conditions, the SPLASH model preserves the water balance, such that $\sum (P_n + C_n) = \sum (E^a_n + RO)$.

To solve this simple “bucket model”, the following steps are taken at the daily timescale: calculate
the radiation terms (see Section 1.), estimate the condensation, estimate the evaporative supply, estimate the evaporative demand, calculate the actual evapotranspiration, and update the daily soil moisture.

The daily condensation, $C_n$, may be expressed as the water equivalent of the absolute value of negative net radiation, $H_N^-$.

The evaporative supply rate, $S_w$ ($\text {mm h}^{−1}$), is assumed to be constant over the day and can be estimated based on a linear
proportion of the previous day’s soil moisture, $W_{n−1}$ {cite}`Federer1982`.

The evaporative demand rate, $D_p$ ($\text {mm h}^{−1}$), is set equal to the potential evapotranspiration rate, $E^p$ ($\text {mm h}^{−1}$), as defined by Priestley and Taylor (1972).

The calculation of daily actual evapotranspiration, $E^a_n$ ($\text {mm d}^{−1}$), is based on the daily integration of the actual evapotranspiration rate, $E^a$ ($\text {mm h}^{−1}$), which may be defined as the minimum of the evaporative supply and demand rates
{cite}`Federer1982`.

The calculation of daily runoff, $RO$, is based on the excess of daily soil moisture without runoff compared to the holding capacity, $W_m$.

With analytical expressions for $C_n$, $E^a_n$, and $RO$, $W_n$ can be calculated by equation above.

The vertical distribution of water in different soil levels is calculated like this...

### 3. Atmospheric humidity


### 4. Atmospheric temperature


### 5. Soil temperature




## Disturbance Module
