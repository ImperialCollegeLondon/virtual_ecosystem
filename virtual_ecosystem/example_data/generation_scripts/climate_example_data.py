"""Climate data to run `ve_example`.

This code creates a dummy time series of climate input variables which is required to
run the Virtual Ecosystem example. The current values are typical monthly averages for
tropical regions.
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

# Air temperature [°C]
data["air_temperature_ref"] = DataArray(
    data=np.random.uniform(25, 35, size=(n_cells, n_dates)),
    coords={"cell_id": cell_id, "time_index": time_index},
)

# Relative humidity [%]
data["relative_humidity_ref"] = DataArray(
    data=np.random.uniform(75, 95, size=(n_cells, n_dates)),
    coords={"cell_id": cell_id, "time_index": time_index},
)

# Precipitation [mm]
data["precipitation"] = DataArray(
    data=np.random.uniform(0, 200, size=(n_cells, n_dates)),
    coords={"cell_id": cell_id, "time_index": time_index},
)

# Atmospheric pressure [kPa]
data["atmospheric_pressure_ref"] = DataArray(
    data=np.random.uniform(95, 103, size=(n_cells, n_dates)),
    coords={"cell_id": cell_id, "time_index": time_index},
)

# Atmospheric CO2 concentration [ppm]
data["atmospheric_co2_ref"] = DataArray(
    data=np.full((n_cells, n_dates), fill_value=400),
    coords={"cell_id": cell_id, "time_index": time_index},
)

# Wind speed [m s-1]
data["wind_speed_ref"] = DataArray(
    data=np.random.uniform(0.01, 0.3, size=(n_cells, n_dates)),
    coords={"cell_id": cell_id, "time_index": time_index},
)

# Mean annual temperature [°C]
data["mean_annual_temperature"] = DataArray(
    data=np.full((n_cells,), fill_value=25),
    coords={"cell_id": cell_id},
)

data["time"] = DataArray(time, coords={"time_index": time_index})

# Add attributes
data.attrs["dataset_description"] = """The dummy climate data for the example
simulation provides reference data for the climatic conditions above the canopy for all
time steps in the model, along with climatological data on the mean annual temperature.
"""

data.air_temperature_ref.attrs = dict(
    units="°C", description="Air temperature above canopy"
)
data.relative_humidity_ref.attrs = dict(
    units="%", description="Relative humidity above canopy"
)
data.precipitation.attrs = dict(units="mm", description="Total monthly precipitation")
data.atmospheric_pressure_ref.attrs = dict(
    units="kPa", description="Atmospheric pressure above canopy"
)
data.atmospheric_co2_ref.attrs = dict(
    units="ppm", description="Atmospheric CO2 concentration"
)
data.wind_speed_ref.attrs = dict(
    units="m s-1", description="Wind speed above the canopy"
)
data.mean_annual_temperature.attrs = dict(
    units="°C", description="Mean annual temperature"
)

# Remove datetime dimension as not needed for the example
data_out = data.drop_vars("time")

# Save to netcdf
data_out.to_netcdf("../data/example_climate_data.nc")
