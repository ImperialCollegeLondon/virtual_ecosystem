"""Functions to set up hydrology model and select data for current time step."""

# noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic import abiotic_tools
from virtual_ecosystem.models.hydrology import above_ground


def calculate_layer_thickness(
    soil_layer_heights: NDArray[np.float32],
    meters_to_mm: float,
) -> NDArray[np.float32]:
    """Calculate layer thickness from soil layer depth profile.

    Args:
        soil_layer_heights: Soil layer heights, [m]
        meters_to_mm: Meter to millimeter conversion factor

    Returns:
        Soil layer thickness, [mm]
    """

    return np.diff(soil_layer_heights, axis=0, prepend=0) * (-meters_to_mm)


def setup_hydrology_input_current_timestep(
    data: Data,
    time_index: int,
    days: int,
    seed: None | int,
    layer_roles: list[str],
    soil_layer_thickness: NDArray[np.float32],
    soil_moisture_capacity: float | NDArray[np.float32],
    soil_moisture_residual: float | NDArray[np.float32],
    core_constants: CoreConsts,
    latent_heat_vap_equ_factors: list[float],
) -> dict[str, NDArray[np.float32]]:
    """Select and pre-process inputs for hydrology.update() for current time step.

    The function returns a dictionary with the following variables:

    * latent_heat_vapourisation
    * molar_density_air
    * current_precipitation
    * subcanopy_temperature
    * subcanopy_humidity
    * subcanopy_pressure
    * subcanopy_wind_speed
    * leaf_area_index_sum
    * current_evapotranspiration
    * soil_layer_heights
    * soil_layer_thickness
    * top_soil_moisture_capacity_mm
    * top_soil_moisture_residual_mm
    * soil_moisture_true (no above ground layers)
    * previous_accumulated_runoff
    * previous_subsurface_flow_accumulated
    * groundwater_storage

    Args:
        data: Data object that contains inputs from the microclimate model, the plant
            model, and the hydrology model that are required for current update
        time_index: Time index of current time step
        days: Number of days in core time step
        seed: Seed for random rainfall generator
        layer_roles: List of layer roles
        soil_layer_thickness: The thickness of the soil layer (mm)
        soil_moisture_capacity: Soil moisture capacity, unitless
        soil_moisture_residual: Soil moisture residual, unitless
        core_constants: Set of core constants share across all models
        latent_heat_vap_equ_factors: Factors in calculation of latent heat of
            vapourisation.


    Returns:
        dictionary with all variables that are required to run one hydrology update()
    """

    output = {}

    # Calculate latent heat of vapourisation and density of air
    latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
        temperature=data["air_temperature"].to_numpy(),
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=latent_heat_vap_equ_factors,
    )
    output["latent_heat_vapourisation"] = latent_heat_vapourisation

    molar_density_air = abiotic_tools.calculate_molar_density_air(
        temperature=data["air_temperature"].to_numpy(),
        atmospheric_pressure=data["atmospheric_pressure"].to_numpy(),
        standard_mole=core_constants.standard_mole,
        standard_pressure=core_constants.standard_pressure,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )
    output["molar_density_air"] = molar_density_air

    # Get atmospheric variables
    output["current_precipitation"] = above_ground.distribute_monthly_rainfall(
        (data["precipitation"].isel(time_index=time_index)).to_numpy(),
        num_days=days,
        seed=seed,
    )

    for out_var, in_var in (
        ("subcanopy_temperature", "air_temperature"),
        ("subcanopy_humidity", "relative_humidity"),
        ("subcanopy_wind_speed", "wind_speed"),
        ("subcanopy_pressure", "atmospheric_pressure"),
    ):
        output[out_var] = (
            data[in_var].isel(layers=layer_roles.index("subcanopy")).to_numpy()
        )

    # Get inputs from plant model
    output["leaf_area_index_sum"] = data["leaf_area_index"].sum(dim="layers").to_numpy()
    output["current_evapotranspiration"] = (
        data["evapotranspiration"].sum(dim="layers") / days
    ).to_numpy()

    # Select soil variables
    # FIXME - there's an implicit axis order built into these calculations (vertical
    #         profile is axis 0) that needs fixing.
    output["top_soil_moisture_capacity_mm"] = (
        soil_moisture_capacity * soil_layer_thickness[0]
    )
    output["top_soil_moisture_residual_mm"] = (
        soil_moisture_residual * soil_layer_thickness[0]
    )
    output["soil_moisture_mm"] = (  # drop above ground layers
        data["soil_moisture"].isel(layers=data["layer_roles"] == "soil")
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
    soil_layer_thickness: NDArray[np.float32],
    layer_structure: LayerStructure,
    n_cells: int,
    initial_soil_moisture: float | NDArray[np.float32],
) -> DataArray:
    """Initialise soil moisture in mm.

    Args:
        soil_layer_thickness: Soil layer thickness, [mm]
        layer_structure: LayerStructure object that contains information about the
            number and identities of vertical layers
        n_cells: Number of grid cells
        initial_soil_moisture: Initial relative soil moisture, dimensionless

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
        dims=["layers", "cell_id"],
        coords={
            "layers": np.arange(layer_structure.n_layers),
            "layer_roles": ("layers", layer_structure.layer_roles),
            "cell_id": np.arange(n_cells),
        },
        name="soil_moisture",
    )
