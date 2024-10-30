"""Simple top of canopy shortwave radiation for `ve_run` example data.

This code creates top of canopy shortwave radiation data as input to setup the abiotic
model. The current values are typical hourly averages for tropical regions.

Once the new netcdf file is created, the final step is to add the grid information to
the grid config `TOML` to load this data correctly when setting up a Virtual Ecosystem
Simulation. Here, we can also add the 45 m offset to position the coordinated at the
centre of the grid cell.

[core.grid]
cell_nx = 9
cell_ny = 9
cell_area = 8100
xoff = -45.0
yoff = -45.0
"""

import numpy as np
from xarray import DataArray, Dataset

from virtual_ecosystem.example_data.generation_scripts.common import (
    cell_id,
    n_cells,
    n_dates,
    time,
    time_index,
)

data = Dataset()

# Spatio-temporal shortwave radiation flux data [W m-2]
data["topofcanopy_radiation"] = DataArray(
    data=np.full((n_cells, n_dates), fill_value=250),
    coords={"cell_id": cell_id, "time_index": time_index},
)

data["time"] = DataArray(time, coords={"time_index": time_index})

data.to_netcdf("../data/example_topofcanopy_radiation.nc")
