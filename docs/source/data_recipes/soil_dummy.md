---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: vr_python3
  language: python
  name: vr_python3
---

# Necessary soil data for dummy module

This section explains how to generate the data required to run the soil component of the
dummy model. **It is important to note that none of this data is real data**. Instead,
this data is a set of plausible values for which the soil model absolutely has to
function sensibly for.

```{code-cell} ipython3
import numpy as np
from xarray import Dataset

# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_spacing = np.arange(0, 721, 90)
gradient = np.multiply.outer(cell_spacing/90, cell_spacing/90)

# Generate a range of plausible values (3.5-4.5) for the soil pH [unitless].
pH_values = 3.5 + 1.00 * (gradient) / (64)

# Generate a range of plausible values (1200-1800) for the bulk density [kg m^-3].
bulk_density_values = 1200.0 + 600.0 * (gradient) / (64)

# Generate a range of plausible values (0.27-0.40) for the clay fraction [fraction].
clay_fraction_values = 0.27 + 0.13 * (gradient) / (64)

# Generate a range of plausible values (0.005-0.01) for the lmwc pool [kg C m^-3].
lmwc_values = 0.005 + 0.005 * (gradient) / (64)

# Generate a range of plausible values (1.0-3.0) for the maom pool [kg C m^-3].
maom_values = 1.0 + 2.0 * (gradient) / (64)

# Generate a range of plausible values (0.0015-0.005) for the microbial C pool
# [kg C m^-3].
microbial_C_values = 0.0015 + 0.0035 * (gradient) / (64)

# Generate a range of plausible values (0.1-1.0) for the POM pool [kg C m^-3].
pom_values = 0.1 + 0.9 * (gradient) / (64)

# Generate a range of plausible values (0.01-0.5) for the POM enzyme pool [kg C m^-3].
pom_enzyme_values = 0.01 + 0.49 * (gradient) / (64)

# Generate a range of plausible values (0.01-0.5) for the MAOM enzyme pool [kg C m^-3].
maom_enzyme_values = 0.01 + 0.49 * (gradient) / (64)

# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_displacements = [0, 90, 180, 270, 360, 450, 540, 630, 720]

# Make dummy soil dataset
dummy_soil_data = Dataset(
    data_vars=dict(
        pH=(["x", "y"], pH_values),
        bulk_density=(["x", "y"], bulk_density_values),
        clay_fraction=(["x", "y"], clay_fraction_values),
        soil_c_pool_lmwc=(["x", "y"], lmwc_values),
        soil_c_pool_maom=(["x", "y"], maom_values),
        soil_c_pool_microbe=(["x", "y"], microbial_C_values),
        soil_c_pool_pom=(["x", "y"], pom_values),
        soil_enzyme_pom = (["x", "y"], pom_enzyme_values),
        soil_enzyme_maom = (["x", "y"], maom_enzyme_values),
    ),
    coords=dict(
        x=(["x"], cell_displacements),
        y=(["y"], cell_displacements),
    ),
    attrs=dict(description="Soil data for dummy Virtual Rainforest model."),
)
dummy_soil_data
```

```python
# Save the dummy soil data file as netcdf
dummy_soil_data.to_netcdf("./dummy_soil_data.nc")
```
