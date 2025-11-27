"""Climate data to run `ve_example`.

This code creates a dummy time series of climate input variables which is required to
run the Virtual Ecosystem example. The current values are typical monthly averages for
tropical regions, based on [ERA-5 Land data](https://doi.org/10.24381/cds.68d2bb30) for
the years 2013/14.
"""

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray, Dataset

from virtual_ecosystem.example_data.generation_scripts.common import (
    cell_id,
    n_cells,
    n_dates,
    time,
    time_index,
)

data = Dataset()

# Create a month index (0-11)
months = np.arange(n_dates) % 12


# Helper: annual cycle
def annual_cycle(
    months: NDArray[np.int_], amplitude: float = 0, phase: int = 0
) -> NDArray[np.floating]:
    """Generate a simple annual cycle as a sine wave."""

    return amplitude * np.sin(2 * np.pi * (months + phase) / 12)


# Variable definitions (mean, amplitude of annual cycle, noise)
var_specs = {
    "air_temperature_ref": {"mean": 23.0, "amp": 10.0, "noise": 0.5},  # °C
    "relative_humidity_ref": {"mean": 85.0, "amp": 15.0, "noise": 2.0},  # %
    "precipitation": {"mean": 200.0, "amp": 450.0, "noise": 30.0},  # mm
    "atmospheric_pressure_ref": {"mean": 101.0, "amp": 1.0, "noise": 0.5},  # kPa
    "atmospheric_co2_ref": {"mean": 400.0, "amp": 0.0, "noise": 0.0},  # ppm (fixed)
    "wind_speed_ref": {"mean": 0.15, "amp": 0.05, "noise": 0.05},  # m/s
}

# Loop to fill data
for var, specs in var_specs.items():
    cycle = annual_cycle(months, amplitude=specs["amp"])
    noise = np.random.normal(0, specs["noise"], size=(n_cells, n_dates))
    values = specs["mean"] + cycle + noise
    data[var] = DataArray(
        data=values,
        coords={"cell_id": cell_id, "time_index": time_index},
    )

# Special case: mean annual temperature (static per cell)
data["mean_annual_temperature"] = DataArray(
    data=np.full((n_cells,), fill_value=23.0),
    coords={"cell_id": cell_id},
)

# Add time coordinate
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

# Save to netcdf
data.to_netcdf("../data/example_climate_data.nc")
