"""Functions to set up hydrology model and select data for current time step."""

import numpy as np
from numpy.typing import NDArray
from pyrealm.core.hygro import calc_specific_heat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic import abiotic_tools
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants
from virtual_ecosystem.models.hydrology import above_ground
from virtual_ecosystem.models.hydrology.model_config import HydrologyConstants


def initialise_atmosphere_for_hydrology(
    data: Data,
    model_constants: HydrologyConstants,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    layer_structure: LayerStructure,
):
    """Initialise atmospheric variables required for hydrology model.

    Args:
        data: Data object
        model_constants: Set of constants for hydrology model
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants shared across all models
        layer_structure: The LayerStructure instance for a simulation

    Returns:
        aerodynamic_resistance_surface, aerodynamic_resistance_canopy,
            stomatal_conductance, density_air, specific_heat_air,
            latent_heat_vapourisation
    """

    output = {}

    # Initialise scalar layers
    initial_values = [
        (
            "aerodynamic_resistance_surface",
            layer_structure.index_surface_scalar,
            model_constants.initial_aerodynamic_resistance_surface,
        ),
        (
            "aerodynamic_resistance_canopy",
            layer_structure.index_filled_canopy,
            model_constants.initial_aerodynamic_resistance_canopy,
        ),
        (
            "stomatal_conductance",
            layer_structure.index_filled_canopy,
            model_constants.initial_stomatal_conductance,
        ),
    ]

    for key, index, value in initial_values:
        layer = layer_structure.from_template()
        layer[index] = value
        output[key] = layer

    # Extract air temperature and pressure
    air_temp = data["air_temperature_ref"].isel(time_index=0).to_numpy()
    air_pressure = data["atmospheric_pressure_ref"].isel(time_index=0).to_numpy()

    # Density of air
    density_air = abiotic_tools.calculate_air_density(
        air_temperature=air_temp,
        atmospheric_pressure=air_pressure,
        specific_gas_constant_dry_air=core_constants.specific_gas_constant_dry_air,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )
    density_air_layer = layer_structure.from_template()
    density_air_layer[layer_structure.index_filled_atmosphere] = density_air
    output["density_air"] = density_air_layer

    # Specific heat of air
    specific_heat_air = calc_specific_heat(tc=air_temp)
    specific_heat_air_layer = layer_structure.from_template()
    specific_heat_air_layer[layer_structure.index_filled_atmosphere] = specific_heat_air
    output["specific_heat_air"] = specific_heat_air_layer

    # Latent heat of vapourisation
    latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
        temperature=air_temp,
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
    )
    latent_heat_layer = layer_structure.from_template()
    latent_heat_layer[layer_structure.index_filled_atmosphere] = (
        latent_heat_vapourisation
    )
    output["latent_heat_vapourisation"] = latent_heat_layer

    return output


def setup_hydrology_input_current_timestep(
    data: Data,
    time_index: int,
    days: int,
    seed: None | int,
    layer_structure: LayerStructure,
    soil_layer_thickness_mm: NDArray[np.floating],
    soil_moisture_saturation: float | NDArray[np.floating],
    soil_moisture_residual: float | NDArray[np.floating],
) -> dict[str, NDArray[np.floating]]:
    """Select and pre-process inputs for hydrology.update() for current time step.

    The hydrology model currently loops over 30 days per month. Atmospheric variables in
    the canopy and
    near the surface are selected here and kept constant for the whole month. Daily
    timeseries of precipitation and canopy transpiration are generated from monthly
    values in `data` to be used in the daily loop. States of other hydrology variables
    are selected and updated in the daily loop.

    The function returns a dictionary with the following variables:

    * surface_temperature (TODO switch to subcanopy_temperature)
    * surface_humidity (TODO switch to subcanopy_humidity)
    * surface_pressure (TODO switch to subcanopy_pressure)
    * surface_wind_speed (TODO switch to subcanopy_wind_speed)

    * atmospheric_pressure_canopy
    * air_temperature_canopy
    * vapour_pressure_deficit_canopy

    * leaf_area_index_sum
    * current_precipitation
    * current_transpiration
    * current_soil_moisture
    * top_soil_moisture_saturation
    * top_soil_moisture_residual
    * groundwater_storage

    Args:
        data: Data object that contains inputs from the microclimate model, the plant
            model, and the hydrology model that are required for current update
        time_index: Time index of current time step
        days: Number of days in core time step
        seed: Seed for random rainfall generator
        layer_structure: The LayerStructure instance for a simulation.
        soil_layer_thickness_mm: The thickness of the soil layer, [mm]
        soil_moisture_saturation: Soil moisture saturation, unitless
        soil_moisture_residual: Soil moisture residual, unitless

    Returns:
        dictionary with all variables that are required to run one hydrology update()
        daily loop
    """

    output = {}

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
    output["leaf_area_index_sum"] = np.nansum(
        data["leaf_area_index"].to_numpy(), axis=0
    )
    output["current_transpiration"] = np.nansum(
        data["transpiration"].to_numpy() / days, axis=0
    )

    # Select soil variables
    output["top_soil_moisture_saturation"] = (
        soil_moisture_saturation * soil_layer_thickness_mm[0]
    )
    output["top_soil_moisture_residual"] = (
        soil_moisture_residual * soil_layer_thickness_mm[0]
    )
    output["current_soil_moisture"] = (  # drop above ground layers
        data["soil_moisture"][layer_structure.index_all_soil]
    ).to_numpy()

    # Get ground water level
    output["groundwater_storage"] = data["groundwater_storage"].to_numpy()

    return output


def initialise_soil_moisture_mm(
    layer_structure: LayerStructure,
    initial_soil_moisture: float,
    soil_layer_thickness: NDArray[np.floating],
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


def calculate_psychrometric_constant(
    atmospheric_pressure: NDArray[np.floating],
    latent_heat_vapourization: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    molecular_weight_ratio_water_to_dry_air: float,
):
    """Calculate the psychrometric constant.

    NOTE this might be replaced with pyrealm implementation

    Args:
        atmospheric_pressure: Atmospheric pressure, [KPa].
        latent_heat_vapourization: Latent heat of vaporization, [kJ kg-1]
        specific_heat_air: Specific heat of air at constant pressure, [kJ kg-1 K-1]
        molecular_weight_ratio_water_to_dry_air: Ratio of molecular weights of water to
            dry air

    Returns:
        Psychrometric constant in [kPa K-1]
    """

    return (specific_heat_air * atmospheric_pressure) / (
        latent_heat_vapourization * molecular_weight_ratio_water_to_dry_air
    )


def check_precipitation_surface(precipitation_surface: NDArray[np.floating]) -> None:
    """Check that precipitation at the surface is not negative.

    Args:
        precipitation_surface: Precipitation at the surface

    Returns:
        error if precipitation is negative in any grid cell
    """
    if (precipitation_surface < 0.0).any():
        LOGGER.critical(
            "Surface precipitation should not be negative! Consider checking that the"
            " canopy water balance is correct."
        )
        raise ValueError(
            "Surface precipitation should not be negative! Consider checking that the"
            " canopy water balance is correct."
        )


def calculate_effective_saturation(
    soil_moisture: NDArray[np.floating],
    soil_moisture_saturation: float | NDArray[np.floating],
    soil_moisture_residual: float | NDArray[np.floating],
) -> NDArray[np.floating]:
    """Calculate the effective soil saturation based on the soil moisture.

    This is kept as a separate function because the soil model also needs to use this
    quantity.

    Args:
        soil_moisture: Volumetric relative water content in top soil, [unitless]
        soil_moisture_saturation: Soil moisture saturation, [unitless]
        soil_moisture_residual: Residual soil moisture, [unitless]

    Returns:
        The :term:`effective saturation` of the soil [unitless]
    """

    return (soil_moisture - soil_moisture_residual) / (
        soil_moisture_saturation - soil_moisture_residual
    )


def check_monthly_mass_balance(
    drainage_map: dict[int, list[int]],
    surface_channel_inflow_mm: NDArray[np.floating],
    monthly_precipitation_mm: NDArray[np.floating],
    monthly_evaporation_mm: NDArray[np.floating],
) -> None:
    """Check that total monthly streamflow at outlet(s) does not exceed total precip.

    The function identifies the outlet cells (cells with no downstream connections) from
    the drainage map. It then sums the surface channel inflow at these outlet cells and
    compares it to the total catchment precipitation minus total evaporation. If the
    streamflow exceeds the available water, an AssertionError is raised.

    If no true outlet cells exist, the flow from the lowest cells (cells with fewest
    upstream connections) is used for the check.

    Args:
        drainage_map: Dict mapping each cell ID -> list of upstream cell IDs
        surface_channel_inflow_mm: Monthly total surface channel inflow per cell, [mm]
        monthly_precipitation_mm: Monthly total precipitation per cell, [mm]
        monthly_evaporation_mm: Monthly total evaporation per cell, [mm]

    Raises:
        AssertionError: if monthly streamflow exceeds total catchment precipitation.
    """
    n_cells = len(drainage_map)
    all_cells = set(range(n_cells))

    # Cells that are upstream to others
    cells_with_downstream = set()
    for upstream_ids in drainage_map.values():
        cells_with_downstream.update(upstream_ids)

    # Outlet cells = cells with no downstream
    outlet_cells = list(all_cells - cells_with_downstream)

    # If no outlet, pick the "lowest" cells (fewest upstream neighbors)
    if not outlet_cells:
        upstream_counts = {
            cell: len(upstream_ids) for cell, upstream_ids in drainage_map.items()
        }
        min_upstream = min(upstream_counts.values())
        outlet_cells = [
            cell for cell, count in upstream_counts.items() if count == min_upstream
        ]

    # Total streamflow at outlet(s)
    monthly_outlet_flow_mm = surface_channel_inflow_mm[outlet_cells].sum()

    # Total catchment precipitation and soil evaporation
    total_catchment_precip_mm = np.sum(monthly_precipitation_mm)
    total_catchment_evaporation_mm = np.sum(monthly_evaporation_mm)

    # Mass balance check
    if (
        monthly_outlet_flow_mm
        > total_catchment_precip_mm - total_catchment_evaporation_mm
    ):
        raise AssertionError(
            f"Mass balance violated: total streamflow ({monthly_outlet_flow_mm:.2f} mm)"
            f" exceeds total catchment precip ({total_catchment_precip_mm:.2f} mm). "
            f"Outlet cells: {outlet_cells}"
        )
