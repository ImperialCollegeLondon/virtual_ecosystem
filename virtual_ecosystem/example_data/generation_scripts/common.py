"""Common components for example data generation.

This file defines some simple shared components used for generating the example datasets
and which will be imported by the other code in this module.
"""

import numpy as np

# Generate range of cell numbers in the x and y directions. Here we have a 9x9 grid,
# so cells are numbered from 0 to 8 in each direction.
nx = 9
ny = 9
x_cell_ids = np.arange(nx)
y_cell_ids = np.arange(ny)

# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_displacements = np.arange(0, 721, 90)

# Cell id codes
n_cells = nx * ny
cell_id = np.arange(n_cells)

# Time dimension - a time series of 24 months.
time = np.arange(np.datetime64("2013-01"), np.datetime64("2015-01")).astype(
    "datetime64[D]"
)
n_dates = len(time)
time_index = np.arange(n_dates)
