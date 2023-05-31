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
from xarray import Dataset

def generate_pH_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of pH values.
    
    We're looking at acidic soils so a range of 3.5-4.5 seems plausible.
    """
    return 3.5 + (x * y) / (64)


def generate_BD_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of bulk density values.
    
    Bulk density can vary quite a lot so a range of 1200-1800 kg m^-3 seems sensible.
    """
    return 1200.0 + 600.0 * (x * y) / (64)


def generate_clay_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of clay content values.
    
    We're considering fairly clayey soils, so look at a range of 27.0-40.0 % clay.
    """
    return 27.0 + 13.0 * (x * y) / (64)


def generate_lmwc_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of lmwc values.
    
    LMWC generally a very small carbon pool, so a range of 0.005-0.01 kg C m^-3 is used.
    """
    return 0.005 + 0.005 * (x * y) / (64)


def generate_maom_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of maom values.
    
    A huge amount of carbon can be locked away as MAOM, so a range of 1.0-3.0 kg C m^-3
    is used.
    """
    return 1.0 + 2.0 * (x * y) / (64)


def generate_microbial_C_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of microbial C values.
    
    The carbon locked up as microbial biomass is tiny, so a range of 0.0015-0.005
    kg C m^-3 is used.
    """
    return 0.0015 + 0.0035 * (x * y) / (64)


# Generate range of cell numbers in the a x and y directions. Here we have a 9x9 grid,
# so cells are numbered from 0 to 8 in each direction.
x_cell_ids = range(0, 9)
y_cell_ids = range(0, 9)

# Make matrices containing all the relevant values
pH_values = [[generate_pH_values(x, y) for y in y_cell_ids] for x in x_cell_ids]
bulk_density_values = [
    [generate_BD_values(x, y) for y in y_cell_ids] for x in x_cell_ids
]
percent_clay_values = [
    [generate_clay_values(x, y) for y in y_cell_ids] for x in x_cell_ids
]
lmwc_values = [[generate_lmwc_values(x, y) for y in y_cell_ids] for x in x_cell_ids]
maom_values = [[generate_maom_values(x, y) for y in y_cell_ids] for x in x_cell_ids]
microbial_C_values = [
    [generate_microbial_C_values(x, y) for y in y_cell_ids] for x in x_cell_ids
]

# List of displacements (applies to both x and y)
disps = [0, 90, 180, 270, 360, 450, 540, 630, 720]

# Make dummy soil dataset
dummy_soil_data = Dataset(
    data_vars=dict(
        pH=(["x", "y"], pH_values),
        bulk_density=(["x", "y"], bulk_density_values),
        percent_clay=(["x", "y"], percent_clay_values),
        soil_c_pool_lmwc=(["x", "y"], lmwc_values),
        soil_c_pool_maom=(["x", "y"], maom_values),
        soil_c_pool_microbe=(["x", "y"], microbial_C_values),
    ),
    coords=dict(
        x=(["x"], disps),
        y=(["y"], disps),
    ),
    attrs=dict(description="Soil data for dummy Virtual Rainforest model."),
)
dummy_soil_data
```

```python
# Save the dummy soil data file as netcdf
dummy_soil_data.to_netcdf("./dummy_soil_data.nc")
```
