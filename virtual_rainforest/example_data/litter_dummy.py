"""Necessary litter data for `vr_run` example.

This section explains how to generate the data required to run the litter component of
the dummy model. It is important to note that none of this data is real data.
Instead, the code below creates some typical values for the required input data and
generates a simple spatial pattern. Descriptions of the relevant litter pools can be
found here: /virtual_rainforest/docs/source/virtual_rainforest/soil/soil_details.md.
"""

import numpy as np
from xarray import Dataset

# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_spacing = np.arange(0, 721, 90)
gradient = np.multiply.outer(cell_spacing / 90, cell_spacing / 90)

# Generate a range of plausible values (0.05-0.5) for the above ground metabolic litter
# pools [kg C m^-2].
above_metabolic_values = 0.05 + 0.45 * (gradient) / (64)

# Generate a range of plausible values (0.05-0.5) for the above ground structural litter
# pools [kg C m^-2].
above_structural_values = 0.05 + 0.45 * (gradient) / (64)

# Generate range of plausible values (4.75-12.0) for the woody litter pools [kg C m^-2].
woody_values = 4.75 + 7.25 * (gradient) / (64)

# Generate a range of plausible values (0.03-0.08) for the below ground metabolic litter
# pools [kg C m^-2].
below_metabolic_values = 0.03 + 0.05 * (gradient) / (64)

# Generate range of plausible values (0.05-0.125) for the below ground structural litter
# pools [kg C m^-2].
below_structural_values = 0.05 + 0.075 * (gradient) / (64)

# Generate a range of plausible values (0.01-0.9) for lignin proportions of the pools.
lignin_values = 0.01 + 0.89 * (gradient) / (64)

# Make dummy litter dataset
dummy_litter_data = Dataset(
    data_vars=dict(
        litter_pool_above_metabolic=(["x", "y"], above_metabolic_values),
        litter_pool_above_structural=(["x", "y"], above_structural_values),
        litter_pool_woody=(["x", "y"], woody_values),
        litter_pool_below_metabolic=(["x", "y"], below_metabolic_values),
        litter_pool_below_structural=(["x", "y"], below_structural_values),
        lignin_above_structural=(["x", "y"], lignin_values),
        lignin_woody=(["x", "y"], lignin_values),
        lignin_below_structural=(["x", "y"], lignin_values),
    ),
    coords=dict(
        x=(["x"], cell_spacing),
        y=(["y"], cell_spacing),
    ),
    attrs=dict(description="Litter data for dummy Virtual Rainforest model."),
)

# Save the dummy litter data file as netcdf
dummy_litter_data.to_netcdf("./dummy_litter_data.nc")
