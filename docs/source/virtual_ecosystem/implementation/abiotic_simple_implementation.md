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

This section walks through the steps in generating and updating the abiotic simple model.

The `abiotic_simple model` is a simple regression model that estimates microclimatic
variables based on empirical relationships between leaf area index (LAI) and
atmospheric temperature, relative humidity, and vapour pressure deficit to derive
logarithmic profiles of these variables from external climate data such as
regional climate models or satellite observations. Note that these sources provide
data at different heights and with different underlying assumptions which lead to
different biases in the model output. For below canopy values (1.5 m),
the implementation is based on {cite}`hardwick_relationship_2015` as

$$y = m * LAI + c$$

where $y$ is the variable of interest, $m$ is the gradient
(see [here](../../../../virtual_ecosystem/models/abiotic_simple/constants.py))
and $c$ is the intersect which we set to the external data values (Step 1 in figure below).
We assume that the gradient remains constant.

The other atmospheric layers are calculated by logarithmic regression and
interpolation between the input at the top of the canopy and the 1.5 m values (Step 2 in
figure below).
Soil temperature is interpolated between the surface layer and the temperature at
1 m depth which equals the mean annual temperature.
The function also provides constant atmospheric pressure and $\ce{CO2}$ for
all atmospheric levels.

```{image} ../../_static/images/abiotic_simple.png
:alt: Abiotic simple
:class: bg-primary
:width: 650px
```

Figure: Basic concept of the abiotic simple model. TODO

## Initialising the model

To initialise the `abiotic_simple` model
as part of a Virtual Ecosystem simulation, timeseries of the following
variables  at reference height (2m above the canopy) need to be provided for each grid
cell at the start of the simulation:

* monthly mean air tempeature, (°C)
* mean annual temperature, (°C)
* monthly mean relative humidity, (-)
* monthly mean atmospheric pressure, (kPa)
* monthly atmospheric $\ce{CO_{2}}$, (ppm)

An example for climate data downloading and simple pre-processing is given in the
[climate data recipe section](../../using_the_ve/data/climate_data_recipes.md).

Part of the initialisation step is the initialisation of soil temperature for all
soil layers and the calculation of a time series of vapour pressure deficit (kPa) at
reference height.

## Update

At each time step, the `run_microclimate`
function is called that updates the following microclimatic
variables at relevant heights (e.g. canopy, surface, soil) and adds the output to the
`data` object. In addition to climatic variables, the function expects leaf area index
and the heights/depths of all above and below ground layers.

<!-- ```{python}
output_variables = microclimate.run_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=time_index,
            constants=self.model_constants,
            bounds=self.bounds,
        )
self.data.add_from_dict(output_dict=output_variables)
``` -->
