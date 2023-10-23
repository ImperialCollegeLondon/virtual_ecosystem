"""Necessary surface runoff data for `vr_run` example.

This code randomly generates normally distributed surface runoff data to run
`vr_run` example without the SPLASH implementation.
"""

import numpy as np
from xarray import DataArray

# Randomly generate surface runoff with normal distribution
mu, sigma = 10, 2  # mean and standard deviation
s = np.random.default_rng(seed=42).normal(mu, sigma, 81)

# How far the center of each cell is from the origin. This applies to both the x and y
# direction independently, so cell (0,0) is at the origin, whereas cell (2,3) is 180m
# from the origin in the x direction and 270m in the y direction.
cell_displacements = [0, 90, 180, 270, 360, 450, 540, 630, 720]

runoff = DataArray(
    s.reshape(9, 9),
    dims=["x", "y"],
    coords={"x": cell_displacements, "y": cell_displacements},
    name="surface_runoff",
)
runoff

# Save to netcdf
runoff.to_netcdf("./surface_runoff_dummy.nc")
