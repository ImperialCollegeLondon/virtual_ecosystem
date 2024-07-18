---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.2
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# The abiotic simple model implementation

This section walks through the steps in generating and updating the
[abiotic_simple](virtual_ecosystem.models.abiotic_simple.abiotic_simple_model)
model which is currently the default abiotic model version in the Virtual Ecosystem
configuration.

## Required variables

The abiotic_simple model requires a timeseries of the following variables to
initialise and update the model:

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        'AbioticSimpleModel', 
        ['vars_required_for_init', 'vars_required_for_update']
    ), 
    raw=True
)
```

### A note on pre-processing

The atmospheric variables from regional climate models, observations, or reanalysis are
typically provided in spatial resolutions that are much coarser than the
requirements of the Virtual Ecosystem, and follow different naming and unit conventions.
Please check the following:

* **Does the input climate data match the model grid?**

  This match is necessary for the model to run and to have the effects of topography and
  elevation incorporated that we described in the
  [theory section](../theory/microclimate_theory.md#factors-affecting-microclimate).
  This spatial downscaling step is not included in the Virtual Ecosystem.

* **What is the reference height?**

  Different data sources provide data at
  different vertical levels and with different underlying assumptions, which lead to
  biases in the model output. For example, the reference height can be 1.5 m or 2 m, above
  ground or above the canopy, measured or interpolated. In the Virtual Ecosystem, the
  reference height is assumed to be 2 m above the top of the canopy (2 m above the
  ground in absence of vegetation).

* **What are the expected units?**

  Make sure that the units of the required input variables match those of the required
  variables in the table above, e.g temperatures in Celsius, pressure in kPa, etc.

* **What are the variables names?**

  Check the input data variable names match the Virtual Ecosystem naming convention
  as listed in the table above.

We have used a simple pre-processing script to create the climate data used in
the [example data](../../using_the_ve/example_data.md) from ERA5-Land monthly averaged
data, downloaded from the Copernicus Climate Data Store
[here](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land-monthly-means?tab=overview).
The code is available [here](../../using_the_ve/example_data.md#climate-data).

## Model overview

The `abiotic_simple` model is a simple regression model that estimates microclimatic
variables based on empirical relationships between leaf area index (LAI) and atmospheric
temperature (T), relative humidity (RH), and vapour pressure deficit (VPD) to derive
logarithmic profiles of these variables from external climate data such as regional
climate models or satellite observations. The model also provides information on
atmospheric pressure and $\ce{CO_{2}}$ and soil temperatures at different depths.

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

## Generated variables

When the abiotic simple model initialises, it uses the input data to populate the following
variables. When the model first updates, it then sets further variables.

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'AbioticSimpleModel', 
        ['vars_populated_by_init', 'vars_populated_by_first_update']
    ), 
    raw=True
)
```

## Updated variables

The table below shows the complete set of model variables that are updated at each model
step.

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'AbioticSimpleModel', 
        ['vars_updated']
    ), 
    raw=True
)
```
