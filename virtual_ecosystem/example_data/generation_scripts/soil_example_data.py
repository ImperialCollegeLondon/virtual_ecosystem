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
pH_values = 3.5 + 1.00 * gradient / 64.0

# Generate a range of plausible values (1200-1800) for the bulk density [kg m^-3].
bulk_density_values = 1200.0 + 600.0 * gradient / 64.0

# Generate a range of plausible values (0.27-0.40) for the clay fraction [fraction].
clay_fraction_values = 0.27 + 0.13 * gradient / 64.0

# Generate a range of plausible values (0.005-0.01) for the lmwc pool [kg C m^-3].
lmwc_values = 0.005 + 0.005 * gradient / 64.0

# Generate a range of plausible values (1.0-3.0) for the maom pool [kg C m^-3].
maom_values = 1.0 + 2.0 * gradient / 64.0

# Generate a range of plausible values (0.0015-0.005) for the bacterial C pool
# [kg C m^-3].
bacterial_C_values = 0.0015 + 0.0035 * gradient / 64.0

# Generate a range of plausible values (0.0015-0.005) for the fungal C pool
# [kg C m^-3].
fungal_C_values = 0.0015 + 0.0035 * gradient / 64.0

# Generate a range of plausible values (0.1-1.0) for the POM pool [kg C m^-3].
pom_values = 0.1 + 0.9 * gradient / 64.0

# Generate a range of plausible values (0.00015-0.0005) for the microbial necromass pool
# [kg C m^-3].
necromass_values = 0.00015 + 0.00035 * gradient / 64.0

# Generate a range of plausible values (0.01-0.5) for the POM enzyme pool [kg C m^-3].
pom_enzyme_values = 0.01 + 0.49 * gradient / 64.0

# Generate a range of plausible values (0.01-0.5) for the MAOM enzyme pool [kg C m^-3].
maom_enzyme_values = 0.01 + 0.49 * gradient / 64.0

# Generate a range of plausible values (2.5e-4 - 5.0e-4) for the DON pool [kg N m^-3]
don_values = 2.5e-4 + 2.5e-4 * gradient / 64.0

# Generate a range of plausible values (7.5e-4 - 1.5e-3) for the particulate N pool [kg
# N m^-3]
particulate_n_values = 7.5e-4 + 7.5e-4 * gradient / 64.0

# Generate a range of plausible values (0.2-0.6) for the maom nitrogen pool [kg N m^-3].
maom_n_values = 0.2 + 0.4 * gradient / 64.0

# Generate a range of plausible values (1e-3-5e-3) for the ammonium pool [kg N m^-3].
ammonium_values = 1e-3 + 4e-3 * gradient / 64.0

# Generate a range of plausible values (1e-3-5e-3) for the nitrate pool [kg N m^-3].
nitrate_values = 1e-3 + 4e-3 * gradient / 64.0

# Generate a range of plausible values (3e-5-0.0001) for the microbial necromass
# nitrogen pool [kg N m^-3].
necromass_n_values = 3e-5 + 7e-5 * gradient / 64.0

# Generate a range of plausible values (1e-5 - 2e-5) for the DOP pool [kg P m^-3]
dop_values = 1e-5 + 1e-5 * gradient / 64.0

# Generate a range of plausible values (3e-5 - 6e-5) for the particulate P pool [kg P
# m^-3]
particulate_p_values = 3e-5 + 3e-5 * gradient / 64.0

# Generate a range of plausible values (0.008-0.024) for the maom phosphorus pool [kg P
# m^-3].
maom_p_values = 0.008 + 0.016 * gradient / 64.0

# Generate a range of plausible values (1.2e-6 - 4e-6) for the microbial necromass
# phosphorus pool [kg P m^-3].
necromass_p_values = 1.2e-6 + 2.8e-6 * gradient / 64.0

# Generate a range of plausible values (0.001-0.005) for the primary phosphorus pool [kg
# P m^-3].
primary_p_values = 0.001 + 0.004 * gradient / 64.0

# Generate a range of plausible values (0.005-0.05) for the secondary phosphorus pool
# [kg P m^-3].
secondary_p_values = 0.005 + 0.045 * gradient / 64.0

# Generate a range of plausible values (2.5e-5-5e-5) for the labile inorganic phosphorus
# pool [kg P m^-3].
labile_p_values = 2.5e-5 + 2.5e-5 * gradient / 64.0

# Make example soil dataset
example_soil_data = Dataset(
    data_vars=dict(
        pH=(["x", "y"], pH_values),
        bulk_density=(["x", "y"], bulk_density_values),
        clay_fraction=(["x", "y"], clay_fraction_values),
        soil_c_pool_lmwc=(["x", "y"], lmwc_values),
        soil_c_pool_maom=(["x", "y"], maom_values),
        soil_c_pool_bacteria=(["x", "y"], bacterial_C_values),
        soil_c_pool_fungi=(["x", "y"], fungal_C_values),
        soil_c_pool_pom=(["x", "y"], pom_values),
        soil_c_pool_necromass=(["x", "y"], necromass_values),
        soil_enzyme_pom_bacteria=(["x", "y"], pom_enzyme_values),
        soil_enzyme_maom_bacteria=(["x", "y"], maom_enzyme_values),
        soil_enzyme_pom_fungi=(["x", "y"], pom_enzyme_values),
        soil_enzyme_maom_fungi=(["x", "y"], maom_enzyme_values),
        soil_n_pool_don=(["x", "y"], don_values),
        soil_n_pool_particulate=(["x", "y"], particulate_n_values),
        soil_n_pool_maom=(["x", "y"], maom_n_values),
        soil_n_pool_necromass=(["x", "y"], necromass_n_values),
        soil_n_pool_ammonium=(["x", "y"], ammonium_values),
        soil_n_pool_nitrate=(["x", "y"], nitrate_values),
        soil_p_pool_dop=(["x", "y"], dop_values),
        soil_p_pool_particulate=(["x", "y"], particulate_p_values),
        soil_p_pool_maom=(["x", "y"], maom_p_values),
        soil_p_pool_necromass=(["x", "y"], necromass_p_values),
        soil_p_pool_primary=(["x", "y"], primary_p_values),
        soil_p_pool_secondary=(["x", "y"], secondary_p_values),
        soil_p_pool_labile=(["x", "y"], labile_p_values),
    ),
    coords=dict(
        x=(["x"], cell_displacements),
        y=(["y"], cell_displacements),
    ),
    attrs=dict(description="Soil data for dummy Virtual Ecosystem model."),
)

# Save the example soil data file as netcdf
example_soil_data.to_netcdf("../data/example_soil_data.nc")
