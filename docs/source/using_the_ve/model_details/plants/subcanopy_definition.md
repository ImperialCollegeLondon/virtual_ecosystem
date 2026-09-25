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

The array for each pool provides initial biomasses in [kg m-2] of carbon, nitrogen and
phosphorous for each cell. The variable array structure therefore needs to provide both
spatial (`x` and `y`) dimensions and an elements dimension and should be provided in a
NetCDF file. You can supply only the carbon masses - in which case the pool biomasses
for N and P  will be initialised from the [configured subcanopy ideal nutrient
ratios](./plants_config.md#plants-constants) - or you can provide all the biomasses to
set different starting masses and ratios. If you are only providing carbon masses, the
biomasses for the other elements must still be included in the array and as `np.nan`
values.

The code below create an example of the expected data structure:

```{code-cell} ipython3
import numpy as np
import xarray as xr

carbon = np.full((10, 10, 1), 1)
nitrogen = np.full((10, 10, 1), 0.05)  # C/N ratio of 20
phosphorous = np.full((10, 10, 1), 0.01)  # C/P ratio of 100

# If both nitrogen and phosphorous were defined using:
#   np.full((10, 10, 1), np.nan)
# then the resulting pool would initialise with N and P biomasses at the ideal ratios

subcanopy_vegetation_biomass = xr.DataArray(
    np.concatenate([carbon, nitrogen, phosphorous], axis=2),
    dims=["x", "y", "element"],
    coords={
        "x": np.arange(50, 1000, 100),
        "y": np.arange(50, 1000, 100),
        "element": np.array(["C", "N", "P"]),
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
