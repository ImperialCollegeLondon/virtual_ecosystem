"""Functions to set up hydrology model and select data for current time step."""

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic import abiotic_tools
from virtual_ecosystem.models.hydrology import above_ground


def setup_hydrology_input_current_timestep(
    data: Data,
    time_index: int,
    days: int,
    seed: None | int,
    layer_structure: LayerStructure,
    soil_layer_thickness_mm: NDArray[np.float32],
    soil_moisture_capacity: float | NDArray[np.float32],
    soil_moisture_residual: float | NDArray[np.float32],
    core_constants: CoreConsts,
    latent_heat_vap_equ_factors: list[float],
) -> dict[str, NDArray[np.float32]]:
    """Select and pre-process inputs for hydrology.update() for current time step.

    The hydrology model currently loops over 30 days per month. Atmospheric variables
    near the surface are selected here and kept constant for the whole month. Daily
    timeseries of precipitation and evapotranspiration are generated from monthly
    values in `data` to be used in the daily loop. States of other hydrology variables
    are selected and updated in the daily loop.

    The function returns a dictionary with the following variables:

    * latent_heat_vapourisation
    * molar_density_air

    * surface_temperature (TODO switch to subcanopy_temperature)
    * surface_humidity (TODO switch to subcanopy_humidity)
    * surface_pressure (TODO switch to subcanopy_pressure)
    * surface_wind_speed (TODO switch to subcanopy_wind_speed)
    * leaf_area_index_sum
    * current_precipitation
    * current_evapotranspiration
    * current_soil_moisture
    * top_soil_moisture_capacity
    * top_soil_moisture_residual
    * previous_accumulated_runoff
    * previous_subsurface_flow_accumulated
    * groundwater_storage

    Args:
        data: Data object that contains inputs from the microclimate model, the plant
            model, and the hydrology model that are required for current update
        time_index: Time index of current time step
        days: Number of days in core time step
        seed: Seed for random rainfall generator
        layer_structure: The LayerStructure instance for a simulation.
        soil_layer_thickness_mm: The thickness of the soil layer, [mm]
        soil_moisture_capacity: Soil moisture capacity, unitless
        soil_moisture_residual: Soil moisture residual, unitless
        core_constants: Set of core constants share across all models
        latent_heat_vap_equ_factors: Factors in calculation of latent heat of
            vapourisation.

    Returns:
        dictionary with all variables that are required to run one hydrology update()
        daily loop
    """

    output = {}

    # Calculate latent heat of vapourisation and density of air for all layers
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

    # named 'surface_...' for now TODO needs to be replaced with 2m above ground
    # We explicitly get a scalar index for the surface layer to extract the values as a
    # 1D array of grid cells and not a 2D array with a singleton layer dimension.
    for out_var, in_var in (
        ("surface_temperature", "air_temperature"),
        ("surface_humidity", "relative_humidity"),
        ("surface_wind_speed", "wind_speed"),
        ("surface_pressure", "atmospheric_pressure"),
    ):
        output[out_var] = data[in_var][layer_structure.index_surface_scalar].to_numpy()

    # Get inputs from plant model
    output["leaf_area_index_sum"] = data["leaf_area_index"].sum(dim="layers").to_numpy()
    output["current_evapotranspiration"] = (
        data["evapotranspiration"].sum(dim="layers") / days
    ).to_numpy()

    # Select soil variables
    output["top_soil_moisture_capacity"] = (
        soil_moisture_capacity * soil_layer_thickness_mm[0]
    )
    output["top_soil_moisture_residual"] = (
        soil_moisture_residual * soil_layer_thickness_mm[0]
    )
    output["current_soil_moisture"] = (  # drop above ground layers
        data["soil_moisture"][layer_structure.index_all_soil]
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
    layer_structure: LayerStructure,
    initial_soil_moisture: float,
    soil_layer_thickness: NDArray[np.float32],
) -> DataArray:
    """Initialise soil moisture in mm.

    Args:
        layer_structure: LayerStructure object that contains information about the
            number and identities of vertical layers
        initial_soil_moisture: Initial relative soil moisture, dimensionless
        soil_layer_thickness: The soil layer thickness in mm.

    Returns:
        soil moisture, [mm]
    """

    # Create a data array filled with initial soil moisture values for all soil layers
    # and np.nan for atmosphere layers

    soil_moisture = layer_structure.from_template(array_name="soil_moisture")

    # The layer_structure.soil_layer_thickness is an np.array so as long as initial soil
    # moisture is either a scalar or an np array of similar length, this will broadcast
    # into the soil layers as a column vector.
    soil_moisture[layer_structure.index_all_soil] = (
        initial_soil_moisture * soil_layer_thickness
    )

    return soil_moisture
