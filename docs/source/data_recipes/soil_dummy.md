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

TODO - Add some text here talking about what data is necessary

TODO - Add some justification for values in each case (in doc strings)

```{code-cell} ipython3
from xarray import Dataset

def generate_pH_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of pH values."""
    return 3.5 + (x * y) / (64)


def generate_BD_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of bulk density values."""
    return 1200.0 + 600 * (x * y) / (64)


def generate_clay_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of clay content values."""
    return 27.0 + 13.0 * (x * y) / (64)


def generate_lmwc_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of lmwc values."""
    return 0.005 + 0.005 * (x * y) / (64)


def generate_maom_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of maom values."""
    return 1.0 + 2.0 * (x * y) / (64)


def generate_microbial_C_values(x: float, y: float) -> float:
    """Function to generate a reasonable range of microbial C values."""
    return 0.0015 + 0.0035 * (x * y) / (64)


# Generate range of x and y values
x_coords = range(0, 9)
y_coords = range(0, 9)

# Make matrices containing all the relevant values
pH_values = [[generate_pH_values(x, y) for y in y_coords] for x in x_coords]
bulk_density_values = [[generate_BD_values(x, y) for y in y_coords] for x in x_coords]
percent_clay_values = [[generate_clay_values(x, y) for y in y_coords] for x in x_coords]
lmwc_values = [[generate_lmwc_values(x, y) for y in y_coords] for x in x_coords]
maom_values = [[generate_maom_values(x, y) for y in y_coords] for x in x_coords]
microbial_C_values = [
    [generate_microbial_C_values(x, y) for y in y_coords] for x in x_coords
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
```

```python
# Save the dummy soil data file as netcdf
dummy_soil_data.to_netcdf("./dummy_soil_data.nc")
```
