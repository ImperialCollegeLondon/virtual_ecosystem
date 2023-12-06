"""Example soil data for `vr_run`.

This script generates the data required to run the soil component of the example
dataset. **It is important to note that none of this data is real data**. Instead, this
data is a set of plausible values that the soil model absolutely has to function
sensibly for.
"""

import numpy as np
from numpy.typing import NDArray
from xarray import Dataset

from virtual_rainforest.example_data.generation_scripts.common import (
    cell_displacements,
    x_cell_ids,
    y_cell_ids,
)

# Product of cell ids to generate a simple gradient
xy = np.outer(x_cell_ids, y_cell_ids)


def generate_pH_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of pH values.

    We're looking at acidic soils so a range of 3.5-4.5 seems plausible.
    """
    return 3.5 + (xy) / (64)


def generate_BD_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of bulk density values.

    Bulk density can vary quite a lot so a range of 1200-1800 kg m^-3 seems sensible.
    """
    return 1200.0 + 600.0 * (xy) / (64)


def generate_clay_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of clay content values.

    We're considering fairly clayey soils, so look at a range of 27.0-40.0 % clay.
    """
    return 27.0 + 13.0 * (xy) / (64)


def generate_lmwc_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of lmwc values.

    LMWC generally a very small carbon pool, so a range of 0.005-0.01 kg C m^-3 is used.
    """
    return 0.005 + 0.005 * (xy) / (64)


def generate_maom_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of maom values.

    A huge amount of carbon can be locked away as MAOM, so a range of 1.0-3.0 kg C m^-3
    is used.
    """
    return 1.0 + 2.0 * (xy) / (64)


def generate_microbial_C_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of microbial C values.

    The carbon locked up as microbial biomass is tiny, so a range of 0.0015-0.005
    kg C m^-3 is used.
    """
    return 0.0015 + 0.0035 * (xy) / (64)


def generate_pom_values(xy: NDArray) -> NDArray:
    """Function to generate a reasonable range of pom values.

    A reasonable amount of carbon is stored as particulate organic matter (POM), so a
    range of 0.1-1.0 kg C m^-3 is used.
    """
    return 0.1 + 0.9 * (xy) / (64)


# Make matrices containing all the relevant values
pH_values = generate_pH_values(xy)
bulk_density_values = generate_BD_values(xy)
percent_clay_values = generate_clay_values(xy)
lmwc_values = generate_lmwc_values(xy)
maom_values = generate_maom_values(xy)
microbial_C_values = generate_microbial_C_values(xy)
pom_values = generate_pom_values(xy)

# Make example soil dataset
example_soil_data = Dataset(
    data_vars=dict(
        pH=(["x", "y"], pH_values),
        bulk_density=(["x", "y"], bulk_density_values),
        percent_clay=(["x", "y"], percent_clay_values),
        soil_c_pool_lmwc=(["x", "y"], lmwc_values),
        soil_c_pool_maom=(["x", "y"], maom_values),
        soil_c_pool_microbe=(["x", "y"], microbial_C_values),
        soil_c_pool_pom=(["x", "y"], pom_values),
    ),
    coords=dict(
        x=(["x"], cell_displacements),
        y=(["y"], cell_displacements),
    ),
    attrs=dict(description="Soil data for dummy Virtual Rainforest model."),
)

# Save the example soil data file as netcdf
example_soil_data.to_netcdf("../data/example_soil_data.nc")
