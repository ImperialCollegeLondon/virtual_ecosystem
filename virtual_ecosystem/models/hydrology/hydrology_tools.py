"""Functions to set up hydrology model and select data for each time step."""

# noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.hydrology import above_ground


def calculate_layer_thickness(
    soil_layer_heights: NDArray[np.float32],
    meters_to_mm: float,
) -> NDArray[np.float32]:
    """Calculate layer thickness from soil layer depth profile.

    Args:
        soil_layer_heights: soil layer heights, [m]
        meters_to_mm: meter to millimeter conversion factor

    Returns:
        soil layer thickness, mm
    """

    return np.diff(soil_layer_heights, axis=0, prepend=0) * (-meters_to_mm)


def setup_hydrology_input_current_timestep(
    data: Data,
    time_index: int,
    days: int,
    seed: None | int,
    layer_roles: list[str],
    soil_layer_thickness: NDArray[np.float32],
    soil_moisture_capacity: float,
    soil_moisture_residual: float,
) -> dict[str, NDArray[np.float32]]:
    """Select and pre-process inputs to hydrology.update() for current time step.

    The function resturns a dictionary with the following variables:

    * current_precipitation
    * subcanopy_temperature
    * subcanopy_humidity
    * subcanopy_pressure
    * leaf_area_index_sum
    * current_evapotranspiration
    * soil_layer_heights
    * soil_layer_thickness
    * top_soil_moisture_capacity_mm
    * top_soil_moisture_residual_mm
    * soil_moisture_mm
    * previous_accumulated_runoff
    * previous_subsurface_flow_accumulated
    * groundwater_storage

    Args:
        data: Data object that contains inputs from the microclimate model, the plant
            model, and the hydrology model that are required for current update
        time_index: time index
        days: number of days
        seed: seed for random rainfall generator
        layer_roles: list of layer roles
        soil_moisture_capacity: soil moisture capacity, unitless
        soil_moisture_residual: soil moisture residual, unitless

    Returns:
        dictionary with all variables that are required to run one hydrology update()
    """

    output = {}

    # Get atmospheric variables
    output["current_precipitation"] = above_ground.distribute_monthly_rainfall(
        (data["precipitation"].isel(time_index=time_index)).to_numpy(),
        num_days=days,
        seed=seed,
    )
    output["subcanopy_temperature"] = (
        data["air_temperature"].isel(layers=layer_roles.index("subcanopy"))
    ).to_numpy()
    output["subcanopy_humidity"] = (
        data["relative_humidity"].isel(layers=layer_roles.index("subcanopy"))
    ).to_numpy()
    output["subcanopy_pressure"] = (
        data["atmospheric_pressure_ref"].isel(time_index=time_index).to_numpy()
    )

    # Get inputs from plant model
    output["leaf_area_index_sum"] = data["leaf_area_index"].sum(dim="layers").to_numpy()
    output["current_evapotranspiration"] = (
        data["evapotranspiration"].sum(dim="layers") / days
    ).to_numpy()

    # Select soil variables
    output["top_soil_moisture_capacity_mm"] = (
        soil_moisture_capacity * soil_layer_thickness[0]
    )
    output["top_soil_moisture_residual_mm"] = (
        soil_moisture_residual * soil_layer_thickness[0]
    )
    # FIXME - there's an implicit axis order built into these calculations (vertical
    #         profile is axis 0) that needs fixing.

    # Convert soil moisture (volumetric relative water content) to mm as follows:
    # water content in mm = relative water content / 100 * depth in mm
    # Example: for 20% water at 40 cm this would be: 20/100 * 400mm = 80 mm
    output["soil_moisture_mm"] = (
        data["soil_moisture"].isel(layers=data["layer_roles"] == "soil")
        * soil_layer_thickness
    ).to_numpy()

    # Get accumulated runoff/flow and ground water level from previous time step
    output["previous_accumulated_runoff"] = data[
        "surface_runoff_accumulated"
    ].to_numpy()
    output["previous_subsurface_flow_accumulated"] = data[
        "subsurface_flow_accumulated"
    ].to_numpy()
    output["groundwater_storage"] = data["groundwater_storage"].to_numpy()

    return output


def initialise_soil_moisture_mm(
    soil_layer_thickness: DataArray,
    layer_structure: LayerStructure,
    n_cells: int,
    initial_soil_moisture: float | NDArray[np.float32],
) -> DataArray:
    """Initialise soil moisture in mm.

    Args:
        soil_layer_thickness: soil layer thickness, [mm]
        layer_structure: layer structure object that contains information about the
            number and identities of vertical layers
        n_cells: Number of grid cells
        initial_soil_moisture: Initial relavtive soil moisture, dimensionless

    Returns:
        soil moisture, [mm]
    """

    # Create 1-dimensional numpy array filled with initial soil moisture values for
    # all soil layers and np.nan for atmosphere layers
    soil_moisture_values = np.repeat(
        a=[np.nan, initial_soil_moisture],
        repeats=[
            layer_structure.n_layers - len(layer_structure.soil_layers),
            len(layer_structure.soil_layers),
        ],
    )
    layer_thickness_array = np.concatenate(
        [
            np.repeat(
                np.nan, layer_structure.n_layers - len(layer_structure.soil_layers)
            ),
            soil_layer_thickness[:, 0],
        ]
    )

    # Broadcast 1-dimensional array to grid and assign dimensions and coordinates
    return DataArray(
        np.broadcast_to(
            soil_moisture_values * layer_thickness_array,
            (n_cells, layer_structure.n_layers),
        ).T,
        dims=soil_layer_thickness.dims,
        coords=soil_layer_thickness.coords,
        name="soil_moisture",
    )
