"""Example soil data for `ve_run`.

This script generates the data required to run the soil component of the example
dataset. **It is important to note that none of this data is real data**. Instead, this
data is a set of plausible values that the soil model absolutely has to function
sensibly for.
"""

import numpy as np
from xarray import Dataset

from virtual_ecosystem.example_data.generation_scripts.common import cell_displacements

gradient = np.outer(cell_displacements / 90, cell_displacements / 90)

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

# Generate a range of plausible values (0.00015-0.0005) for the microbial necromass pool
# [kg C m^-3].
necromass_values = 0.00015 + 0.00035 * (gradient) / (64)

# Generate a range of plausible values (0.01-0.5) for the POM enzyme pool [kg C m^-3].
pom_enzyme_values = 0.01 + 0.49 * (gradient) / (64)

# Generate a range of plausible values (0.01-0.5) for the MAOM enzyme pool [kg C m^-3].
maom_enzyme_values = 0.01 + 0.49 * (gradient) / (64)

# Make example soil dataset
example_soil_data = Dataset(
    data_vars=dict(
        pH=(["x", "y"], pH_values),
        bulk_density=(["x", "y"], bulk_density_values),
        clay_fraction=(["x", "y"], clay_fraction_values),
        soil_c_pool_lmwc=(["x", "y"], lmwc_values),
        soil_c_pool_maom=(["x", "y"], maom_values),
        soil_c_pool_microbe=(["x", "y"], microbial_C_values),
        soil_c_pool_pom=(["x", "y"], pom_values),
        soil_c_pool_necromass=(["x", "y"], necromass_values),
        soil_enzyme_pom=(["x", "y"], pom_enzyme_values),
        soil_enzyme_maom=(["x", "y"], maom_enzyme_values),
    ),
    coords=dict(
        x=(["x"], cell_displacements),
        y=(["y"], cell_displacements),
    ),
    attrs=dict(description="Soil data for dummy Virtual Ecosystem model."),
)

# Save the example soil data file as netcdf
example_soil_data.to_netcdf("../data/example_soil_data.nc")
