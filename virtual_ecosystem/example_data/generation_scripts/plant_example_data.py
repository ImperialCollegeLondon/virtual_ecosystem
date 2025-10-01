"""Script to generate example data to initialise the plants model.

This script exports a NetCDF file containing a simple plant community setup for the 9 by
9 example grid. Each cell contains a single cohort of each of two different plant
functional types.

"""

import numpy as np
from pandas import DataFrame
from xarray import DataArray, Dataset

from virtual_ecosystem.example_data.generation_scripts.common import (
    cell_id,
    n_cells,
    n_dates,
    time,
    time_index,
)

# Plant cohort dimensions
n_cohorts = n_cells * 2
cohort_index = np.arange(n_cohorts)

# Generate the initial cohort data as a pandas dataframe

cohort_data = DataFrame(
    dict(
        plant_cohorts_n=np.array([5, 10] * n_cells),
        plant_cohorts_pft=np.array(["broadleaf", "shrub"] * n_cells),
        plant_cohorts_cell_id=np.repeat(cell_id, 2),
        plant_cohorts_dbh=np.array([0.1, 0.05] * n_cells),
    )
)

cohort_data.to_csv("../data/example_plant_cohorts.csv", index=False)

# Populate the required array data variables into an xarray dataset
data = Dataset()

# PFT propagules
data["plant_pft_propagules"] = DataArray(
    data=np.full((n_cells, 2), fill_value=100, dtype=np.int_),
    coords={
        "cell_id": cell_id,
        "pft": np.array(["broadleaf", "shrub"]),
    },
)

# Subcanopy vegetation
# Spatio-temporal data
data["subcanopy_vegetation_biomass"] = DataArray(
    data=np.full((n_cells,), fill_value=0.07),
    coords={"cell_id": cell_id},
)

data["subcanopy_seedbank_biomass"] = DataArray(
    data=np.full((n_cells,), fill_value=0.07),
    coords={"cell_id": cell_id},
)

# Spatio-temporal data
data["downward_shortwave_radiation"] = DataArray(
    data=np.full((n_cells, n_dates), fill_value=2040),
    coords={"cell_id": cell_id, "time_index": time_index},
)


data["time"] = DataArray(time, coords={"time_index": time_index})

data.to_netcdf("../data/example_plant_data.nc")
