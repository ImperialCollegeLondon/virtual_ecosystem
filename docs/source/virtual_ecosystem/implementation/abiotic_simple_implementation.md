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

## Overview and key steps

The [abiotic_simple](../../../../virtual_ecosystem/models/abiotic_simple/abiotic_simple_model.py)
model is a simple regression model that estimates microclimatic variables based on empirical
relationships between leaf area index (LAI) and atmospheric temperature (T), relative
humidity (RH), and vapour pressure deficit (VPD) to derive logarithmic profiles of these
variables from external climate data such as regional climate models or satellite observations.

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

## Initialising the model

The {py:meth}`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model` module
creates a
{py:class}`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the {py:class}`~virtual_ecosystem.core.base_model.BaseModel` class.
For details on setting up a model, please go to
[Using the Virtual Ecosystem](../../using_the_ve/virtual_ecosystem_in_use.md).

To initialise the `abiotic_simple` model as part of a Virtual Ecosystem simulation,
timeseries of the following variables at reference height (2m above the canopy) need
to be provided for each grid cell at the start of the simulation:

* monthly mean air temperature, (°C)
* mean annual temperature, (°C)
* monthly mean relative humidity, (-)
* monthly mean atmospheric pressure, (kPa)
* monthly atmospheric $\ce{CO_{2}}$, (ppm)

An example for climate data downloading and simple pre-processing is given in the
[climate data recipe section](../../using_the_ve/data/climate_data_recipes.md).
Note that these sources provide data at different heights and with different underlying
assumptions which lead to different biases in the model output.

```python
from __future__ import annotations

from typing import Any

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic_simple import microclimate
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)


class AbioticSimpleModel(
    BaseModel,
    model_name="abiotic_simple",
    model_update_bounds=("1 day", "1 month"),
    required_init_vars=(
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
    ),
    vars_updated=(
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
    ),
):
    """A class describing the abiotic simple model.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        model_constants: Set of constants for the abiotic_simple model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: AbioticSimpleConsts = AbioticSimpleConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.model_constants = model_constants
        """Set of constants for the abiotic simple model"""
        self.bounds = AbioticSimpleBounds()
        """Upper and lower bounds for abiotic variables."""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> AbioticSimpleModel:
        """Factory function to initialise the abiotic simple model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(
            config, "abiotic_simple", "AbioticSimpleConsts"
        )

        LOGGER.info(
            "Information required to initialise the abiotic simple model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            model_constants=model_constants,
        )
```

Part of the initialisation step (currently in `setup()`) is the initialisation of soil
temperature array and the
calculation of a time series of vapour pressure deficit (kPa) at reference height.

```python
    def setup(self) -> None:
        """Function to set up the abiotic simple model.

        At the moment, this function only initializes soil temperature for all
        soil layers and calculates the reference vapour pressure deficit for all time
        steps. Both variables are added directly to the self.data object.
        """

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            saturation_vapour_pressure_factors=(
                self.model_constants.saturation_vapour_pressure_factors
            ),
        )
        self.data["vapour_pressure_deficit_ref"] = vapour_pressure_and_deficit[
            "vapour_pressure_deficit"
        ]
        self.data["vapour_pressure_ref"] = vapour_pressure_and_deficit[
            "vapour_pressure"
        ]
```

## Update

At each time step when the model updates, the
{py:meth}`~virtual_ecosystem.models.abiotic_simple.microclimate.run_microclimate`
function is called to perform steps 1 to 4. In addition to climatic input variables,
the function expects leaf area index and the heights/depths of all above and below
ground layers. At the end of each update, the following variables are returned to the
data object:

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

```python
    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic simple model.

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # This section performs a series of calculations to update the variables in the
        # abiotic model. This could be moved to here and written directly to the data
        # object. For now, we leave it as a separate routine.
        output_variables = microclimate.run_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=time_index,
            constants=self.model_constants,
            bounds=self.bounds,
        )
        self.data.add_from_dict(output_dict=output_variables)
```

Here the steps in
{py:meth}`~virtual_ecosystem.models.abiotic_simple.microclimate.run_microclimate`
in more detail using the same inputs as for the
update at time_index=0:

```python
# Inputs
data=self.data
layer_structure=self.layer_structure
time_index=0
constants=self.model_constants
bounds=self.bounds
```

The first step is to vertically sum leaf area index values:

```python
# sum leaf area index over all canopy layers
leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")
```

Next, the atmospheric variables are interpolated as described in Step 1 and 2:

```python
output = {}

# interpolate atmospheric profiles
for var in ["air_temperature", "relative_humidity", "vapour_pressure_deficit"]:
    lower, upper, gradient = getattr(bounds, var)

    output[var] = log_interpolation(
        data=data,
        reference_data=data[var + "_ref"].isel(time_index=time_index),
        leaf_area_index_sum=leaf_area_index_sum,
        layer_structure=layer_structure,
        layer_heights=data["layer_heights"],
        upper_bound=upper,
        lower_bound=lower,
        gradient=gradient,
    ).rename(var)
```

with the
{py:meth}`~virtual_ecosystem.models.abiotic_simple.microclimate.log_interpolation`
function working as follows:

``` python
# Calculate microclimatic variable at 1.5 m as function of leaf area index
lai_regression = DataArray(
    leaf_area_index_sum * gradient + reference_data, dims="cell_id"
)

# Calculate per cell slope and intercept for logarithmic within-canopy profile
slope = (reference_data - lai_regression) / (
    np.log(layer_heights.isel(layers=0)) - np.log(1.5)
)
intercept = lai_regression - slope * np.log(1.5)

# Calculate the values within cells by layer
positive_layer_heights = np.where(layer_heights > 0, layer_heights, np.nan)
layer_values = (
     np.log(positive_layer_heights) * slope.to_numpy() + intercept.to_numpy()
)

# set upper and lower bounds and return arrays
return_array = layer_structure.from_template()
return_array[:] = np.clip(layer_values, lower_bound, upper_bound)
```

Next, the reference values of atmospheric pressure and $\ce{CO2}$ are broadcasted to
the atmospheric layers:

```python
# Mean atmospheric pressure profile, [kPa]
# TODO: this should only be filled for filled/true above ground layers
output["atmospheric_pressure"] = layer_structure.from_template()
output["atmospheric_pressure"][layer_structure.index_atmosphere] = data[
    "atmospheric_pressure_ref"
].isel(time_index=time_index)

# Mean atmospheric C02 profile, [ppm]
# TODO: this should only be filled for filled/true above ground layers
output["atmospheric_co2"] = layer_structure.from_template()
output["atmospheric_co2"][layer_structure.index_atmosphere] = data[
    "atmospheric_co2_ref"
].isel(time_index=time_index)
```

Finally, soil temperature profiles are generated with linear interpolation and the
`output` dictionary is returned:

```python
# Calculate soil temperatures
lower, upper = getattr(bounds, "soil_temperature")
output["soil_temperature"] = interpolate_soil_temperature(
    layer_heights=data["layer_heights"],
    surface_temperature=output["air_temperature"].isel(
        layers=layer_structure.index_surface
    ),
    mean_annual_temperature=data["mean_annual_temperature"],
    layer_structure=layer_structure,
    upper_bound=upper,
    lower_bound=lower,
)
```

with the
{py:meth}`~virtual_ecosystem.models.abiotic_simple.microclimate.interpolate_soil_temperature`
function working as follows:

```python
# select surface layer (atmosphere) and generate interpolation heights
surface_layer = layer_heights[layer_structure.index_surface].to_numpy()
soil_depths = layer_heights[layer_structure.index_all_soil].to_numpy()
interpolation_heights = np.concatenate(
    [surface_layer, -1 * soil_depths + surface_layer]
)

# Calculate per cell slope and intercept for logarithmic soil temperature profile
slope = (surface_temperature.to_numpy() - mean_annual_temperature.to_numpy()) / (
    np.log(interpolation_heights[0]) - np.log(interpolation_heights[-1])
)
intercept = surface_temperature.to_numpy() - slope * np.log(
    interpolation_heights[0]
)

# Calculate the values within cells by layer and clip by the bounds
layer_values = np.clip(
    np.log(interpolation_heights) * slope + intercept, lower_bound, upper_bound
)

# return arrays
return_xarray = layer_structure.from_template()
return_xarray[layer_structure.index_all_soil] = layer_values[1:]
```
