---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
language_info:
  codemirror_mode:
    name: ipython
    version: 3
  file_extension: .py
  mimetype: text/x-python
  name: python
  nbconvert_exporter: python
  pygments_lexer: ipython3
  version: 3.11.9
---

# Defining subcanopy vegetation

The subcanopy/understory vegetation is defined using array variables that define
the biomasses in each of two simple pools for each cell in the simulation, with
units of kg C m-2:

* Vegetative subcanopy biomass that includes both structural and leaf tissue of
  the understory.
* Reproductive subcanopy biomass that represents the subcanopy seedbank.

The two pools are coupled: mass is added to the reproductive biomass at each time step
and new vegetative biomass sprouts from the reproductive biomass pool.

## Array definitions

Both these variables are defined as array variables with spatial (`x` and `y`)
dimensions and should be provided in a NetCDF file. The code below shows the expected
data structure:

```{code-cell} ipython3
import numpy as np
import xarray as xr

subcanopy_vegetation_biomass = xr.DataArray(
    np.ones((10, 10)),
    dims=["x", "y"],
    coords={
        "x": np.arange(50, 1000, 100),
        "y": np.arange(50, 1000, 100),
    },
)

subcanopy_vegetation_biomass
```

## Data source configuration

Once the input data are created, the plant model configuration needs to be updated to
provide paths to the data files containing the variables. Because NetCDF files can hold
multiple variables, this can simply point both variables to the same file, as in the
example below.

```toml
[[core.data.variable]]
file_path = "../data/example_plant_data.nc"
var_name = "subcanopy_vegetation_biomass"
[[core.data.variable]]
file_path = "../data/example_plant_data.nc"
var_name = "subcanopy_seedbank_biomass"
```

## Configuration of subcanopy constants

In addition to the initial biomasses, the subcanopy model is parameterised using a set
of constant values that are set using the [plant model configuration](plants_config.md).
