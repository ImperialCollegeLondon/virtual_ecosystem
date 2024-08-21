"""Example runoff data for `ve_run`.

This code randomly generates normally distributed surface runoff data to run in the
`ve_run` example data without the SPLASH implementation.
"""

import numpy as np
from xarray import DataArray

from virtual_ecosystem.example_data.generation_scripts.common import cell_displacements

# Randomly generate surface runoff with normal distribution
mu, sigma = 10, 2  # mean and standard deviation
s = np.random.default_rng(seed=42).normal(
    mu, sigma, (len(cell_displacements), len(cell_displacements))
)

runoff = DataArray(
    s,
    dims=["x", "y"],
    coords={"x": cell_displacements, "y": cell_displacements},
    name="surface_runoff",
)

# Save to netcdf
runoff.to_netcdf("../data/example_surface_runoff_data.nc")
