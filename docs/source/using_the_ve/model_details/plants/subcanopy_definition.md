---
jupyter:
  jupytext:
    cell_metadata_filter: all,-trusted
    main_language: python
    notebook_metadata_filter: settings,mystnb,language_info,execution
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
---

# Defining subcanopy vegetation

The subcanopy/understory vegetation is define as two simple pools with a single biomass
for each cell in the simulation:

* Vegetative subcanopy biomass that includes both structural and leaf tissue of
  the understory.
* Reproductive subcanopy biomass that represents the subcanopy seedbank.

The two pools are coupled: mass is added to the reproductive biomass at each time step
and new vegetative biomass sprouts from the reproductive biomass pool.

Both these variables are define as array variables with spatial (`x` and `y`) dimensions
and should be provided in a NetCDF file. The code below provides an example of the
required data structure:

```{code-cell} ipython3
import numpy as np
import xarray as xr

subcanopy_vegetation_biomass = xr.DataArray(
  np.ones((10,10)),
  dims=['x','y'],
  coords={
    'x':np.arange(50, 1000, 100),
    'y': np.arange(50, 1000, 100),
  }
)

subcanopy_vegetation_biomass
```

Once the input data are created, the plant model configuration needs to be updated to
add the location of data file containing the variables:

```toml
[[core.data.variable]]
file_path = "../data/example_plant_data.nc"
var_name = "subcanopy_vegetation_biomass"
[[core.data.variable]]
file_path = "../data/example_plant_data.nc"
var_name = "subcanopy_seedbank_biomass"
```
