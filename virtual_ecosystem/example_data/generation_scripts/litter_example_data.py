"""Necessary litter data for `ve_run` example.

This script generates the data required to run the litter component in the example
dataset. It is important to note that none of this data is real data. Instead, the code
below creates some typical values for the required input data and generates a simple
spatial pattern. Descriptions of the relevant litter pools can be found here:
/virtual_ecosystem/docs/source/virtual_ecosystem/soil/soil_details.md.
"""

import numpy as np
from xarray import Dataset

from virtual_ecosystem.example_data.generation_scripts.common import cell_displacements

# Calculate a gradient
gradient = np.multiply.outer(cell_displacements / 90, cell_displacements / 90)

# Generate a range of plausible values (0.05-0.5) for the above ground metabolic litter
# pools [kg C m^-2].
above_metabolic_values = 0.05 + 0.45 * gradient / 64.0

# Generate a range of plausible values (0.05-0.5) for the above ground structural litter
# pools [kg C m^-2].
above_structural_values = 0.05 + 0.45 * gradient / 64.0

# Generate range of plausible values (4.75-12.0) for the woody litter pools [kg C m^-2].
woody_values = 4.75 + 7.25 * gradient / 64.0

# Generate a range of plausible values (0.03-0.08) for the below ground metabolic litter
# pools [kg C m^-2].
below_metabolic_values = 0.03 + 0.05 * gradient / 64.0

# Generate range of plausible values (0.05-0.125) for the below ground structural litter
# pools [kg C m^-2].
below_structural_values = 0.05 + 0.075 * gradient / 64.0

# Generate a range of plausible values (0.01-0.9) for lignin proportions of the pools.
lignin_values = 0.01 + 0.89 * gradient / 64.0

# Generate a range of plausible values (5.0-12.0) for metabolic litter C:N ratio
c_n_metabolic_values = 5.0 + 7.0 * gradient / 64.0

# Generate a range of plausible values (25.0-60.0) for structural litter C:N ratio
c_n_structural_values = 25.0 + 35.0 * gradient / 64.0

# Generate a range of plausible values (30.0-70.0) for woody litter C:N ratio
c_n_woody_values = 30.0 + 40.0 * gradient / 64.0

# Generate a range of plausible values (50.0-120.0) for metabolic litter C:N ratio
c_p_metabolic_values = 50.0 + 70.0 * gradient / 64.0

# Generate a range of plausible values (250.0-600.0) for structural litter C:N ratio
c_p_structural_values = 250.0 + 350.0 * gradient / 64.0

# Generate a range of plausible values (300.0-700.0) for woody litter C:N ratio
c_p_woody_values = 300.0 + 400.0 * gradient / 64.0

# Construct CNP triplets
above_metabolic_cnp = np.stack(
    [
        above_metabolic_values,
        above_metabolic_values / c_n_metabolic_values,
        above_metabolic_values / c_p_metabolic_values,
    ],
    axis=2,
)

above_structural_cnp = np.stack(
    [
        above_structural_values,
        above_structural_values / c_n_structural_values,
        above_structural_values / c_p_structural_values,
    ],
    axis=2,
)

woody_cnp = np.stack(
    [
        woody_values,
        woody_values / c_n_woody_values,
        woody_values / c_p_woody_values,
    ],
    axis=2,
)

below_metabolic_cnp = np.stack(
    [
        below_metabolic_values,
        below_metabolic_values / c_n_metabolic_values,
        below_metabolic_values / c_p_metabolic_values,
    ],
    axis=2,
)

below_structural_cnp = np.stack(
    [
        below_structural_values,
        below_structural_values / c_n_structural_values,
        below_structural_values / c_p_structural_values,
    ],
    axis=2,
)

# Make example litter dataset
example_litter_data = Dataset(
    data_vars=dict(
        litter_pool_above_metabolic_cnp=(["x", "y", "element"], above_metabolic_cnp),
        litter_pool_above_structural_cnp=(["x", "y", "element"], above_structural_cnp),
        litter_pool_woody_cnp=(["x", "y", "element"], woody_cnp),
        litter_pool_below_metabolic_cnp=(["x", "y", "element"], below_metabolic_cnp),
        litter_pool_below_structural_cnp=(["x", "y", "element"], below_structural_cnp),
        lignin_above_structural=(["x", "y"], lignin_values),
        lignin_woody=(["x", "y"], lignin_values),
        lignin_below_structural=(["x", "y"], lignin_values),
    ),
    coords=dict(
        x=(["x"], cell_displacements),
        y=(["y"], cell_displacements),
        element=(["element"], ["C", "N", "P"]),
    ),
    attrs={
        "dataset_description": """This dataset contains example values for the various
        litter pools used in the
        {mod}`~virtual_ecosystem.models.litter.litter_model`."""
    },
)

example_litter_data.litter_pool_above_metabolic_cnp.attrs = dict(
    units="kg m^-2",
    description="Size of the above ground metabolic litter pool in carbon, nitrogen and"
    " phosphorus units",
)
example_litter_data.litter_pool_above_structural_cnp.attrs = dict(
    units="kg m^-2",
    description="Size of the above ground structural litter pool in carbon, nitrogen "
    "and phosphorus units",
)
example_litter_data.litter_pool_woody_cnp.attrs = dict(
    units="kg m^-2",
    description="Size of the woody litter pool in carbon, nitrogen and phosphorus"
    " units",
)
example_litter_data.litter_pool_below_metabolic_cnp.attrs = dict(
    units="kg m^-2",
    description="Size of the below ground metabolic litter pool in carbon, nitrogen and"
    " phosphorus units",
)
example_litter_data.litter_pool_below_structural_cnp.attrs = dict(
    units="kg m^-2",
    description="Size of the below ground structural litter pool in carbon, nitrogen "
    "and phosphorus units",
)
example_litter_data.lignin_above_structural.attrs = dict(
    units="kg lignin C (kg C)^-1",
    description="Proportion of above-ground structural pool carbon that is lignin",
)
example_litter_data.lignin_woody.attrs = dict(
    units="kg lignin C (kg C)^-1",
    description="Proportion of woody pool carbon that is lignin",
)
example_litter_data.lignin_below_structural.attrs = dict(
    units="kg lignin C (kg C)^-1",
    description="Proportion of below-ground structural pool carbon that is lignin",
)

# Save the dummy litter data file as netcdf
example_litter_data.to_netcdf("../data/example_litter_data.nc")
