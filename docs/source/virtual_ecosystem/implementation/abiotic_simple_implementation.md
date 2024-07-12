---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.1
kernelspec:
  display_name: pyrealm_python3
  language: python
  name: pyrealm_python3
---

# Implementation of the abiotic simple model

This section walks through the steps in generating and updating the
[abiotic_simple](../../../../virtual_ecosystem/models/abiotic_simple/abiotic_simple_model.py)
model which is currently the default abiotic model version in the Virtual Ecosystem
configuration.

The `abiotic_simple` model is a simple regression model that estimates microclimatic
variables based on empirical relationships between leaf area index (LAI) and atmospheric
temperature (T), relative humidity (RH), and vapour pressure deficit (VPD) to derive
logarithmic profiles of these variables from external climate data such as regional
climate models or satellite observations. The model also provides information on
atmospheric pressure and $\ce{CO_{2}}$ and soil temperatures at different depths.

## Required input data

The `abiotic_simple` model requires a timeseries of the following variables to
initialise and update the model (`_ref` refers to the referenece height 2 m above the
canopy):

``` python
vars_required_for_init=(
        "air_temperature_ref", # [C]
        "relative_humidity_ref", # [-]
    ),

vars_required_for_update=(
        "air_temperature_ref", # [C]
        "relative_humidity_ref", # [-]
        "vapour_pressure_deficit_ref", # [kPa], calculated in __init__
        "atmospheric_pressure_ref", # [kPa]
        "atmospheric_co2_ref", # [ppm]
        "leaf_area_index", # [m m-1], provided by plants model
        "layer_heights", # [m], provided by model core structure
    )
```

An example for climate data downloading and simple pre-processing is given in the
[climate data recipe section](../../using_the_ve/data/climate_data_recipes.md).
Consider that these sources provide data at different heights and with different
underlying assumptions which lead to different biases in the model output.

```{note}
The input climate data needs to be in the same spatial resolution as the model grid and,
thus, have the effects of topography and elevation incorporated that we described in
the [theory section](../theory/microclimate_theory.md#factors-affecting-microclimate).
This spatial downscaling step is not included in the Virtual Ecosystem.
```

## Model workflow

This sections describes the workflow of the `abiotic_simple` model update step.
At each time step when the model updates, the
{py:meth}`~virtual_ecosystem.models.abiotic_simple.microclimate.run_microclimate`
function is called to perform the steps outlined below.

### Step 1: Linear regression above ground

The linear regression for below canopy values (1.5 m) is based on
{cite:t}`hardwick_relationship_2015` as

$$y = m * LAI + c$$

where $y$ is the variable of interest, $m$ is the gradient
(see {py:class}`~virtual_ecosystem.models.abiotic_simple.constants.AbioticSimpleBounds`)
and $c$ is the intersect which we set to the external data values,
see {numref}`abiotic_simple_step1`.
We assume that the gradient remains constant throughout the simulation.

:::{figure} ../../_static/images/step1.png
:name: abiotic_simple_step1
:alt: Abiotic simple step1
:class: bg-primary
:width: 450px

Linear regression between leaf area index (LAI) and temperature (T) or
vapour pressure deficit (VPD) at 1.5 m above the ground. The y-axis is intersected
at the temperature at reference height. Orange crosses indicate 1.5m and reference height.
:::

### Step 2: Logarithmic interpolation above ground

The values for any other aboveground heights, including but not limited to
canopy layers and surface layer, are calculated by logarithmic regression and
interpolation between the input 2 m above the canopy and the 1.5 m values, see
{numref}`abiotic_simple_step2`.

:::{figure} ../../_static/images/step2.png
:name: abiotic_simple_step2
:alt: Abiotic simple step2
:class: bg-primary
:width: 450px

Logarithmic interpolation between temperature (T) or vapour pressure deficit
(VPD) at 1.5 m and the reference height 2m above the canopy. This approach returns
values at any height of interest. Orange crosses indicate 1.5 m and reference height as
in {numref}`abiotic_simple_step1`.
:::

### Step 3: Broadcasting constant atmospheric properties

The model also broadcasts the reference values for atmospheric pressure and
$\ce{CO2}$ to all atmospheric levels as they are currently assumed to remain constant
during one time step.

### Step 4: Linear interpolation below ground

Soil temperatures are interpolated between the surface layer and the
temperature at 1 m depth which approximately equals the mean annual temperature, i.e.
can assumed to be constant over the year.

## Returned variables

At the end of each time step, vertical profiles of the following variables are returned
to the `data` object:

``` python
vars_updated=(
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
    )
```
