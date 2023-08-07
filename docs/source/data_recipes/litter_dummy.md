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

# Necessary litter data for dummy module

This section explains how to generate the data required to run the litter component of
the dummy model. **It is important to note that none of this data is real data**.
Instead, this data is a set of plausible values for which the litter model absolutely
has to function sensibly for.

```{code-cell} ipython3
from xarray import Dataset

def generate_above_metabolic_values(x: float, y: float) -> float:
    """Generate a range of plausible values for the aboveground metabolic litter pool.
    
    A range of 0.05-0.5 kg C m^-2 seems plausible.
    """
    return 0.05 + 0.45 * (x * y) / (64)


def generate_above_structural_values(x: float, y: float) -> float:
    """Generate a range of plausible values for the aboveground structural litter pool.
    
    A range of 0.05-0.5 kg C m^-2 seems plausible.
    """
    return 0.05 + 0.45 * (x * y) / (64)


# Generate range of cell numbers in the a x and y directions. Here we have a 9x9 grid,
# so cells are numbered from 0 to 8 in each direction.
x_cell_ids = range(0, 9)
y_cell_ids = range(0, 9)

# Make matrices containing all the relevant values
above_metabolic_values = [
    [generate_above_metabolic_values(x, y) for y in y_cell_ids] for x in x_cell_ids
]
above_structural_values = [
    [generate_above_structural_values(x, y) for y in y_cell_ids] for x in x_cell_ids
]

# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_displacements = [0, 90, 180, 270, 360, 450, 540, 630, 720]

# Make dummy litter dataset
dummy_litter_data = Dataset(
    data_vars=dict(
        litter_pool_above_metabolic=(["x", "y"], above_metabolic_values),
        litter_pool_above_structural=(["x", "y"], above_structural_values),
    ),
    coords=dict(
        x=(["x"], cell_displacements),
        y=(["y"], cell_displacements),
    ),
    attrs=dict(description="Litter data for dummy Virtual Rainforest model."),
)
dummy_litter_data
```

```python
# Save the dummy litter data file as netcdf
dummy_litter_data.to_netcdf("./dummy_litter_data.nc")
```
