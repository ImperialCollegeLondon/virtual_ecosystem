"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

from types import SimpleNamespace
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calc_specific_heat, calc_vp_sat

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic import abiotic_tools, energy_balance, wind
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants
from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


def compute_weights_from_absorbed_radiation(
    radiation: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Convert a 2D radiation array into normalized weights that sum to 1.

    Args:
        radiation: 2D array of absorbed radiation values for each layer and cell

    Returns:
        2D array of normalized weights corresponding to the absorbed radiation
    """
    total = np.nansum(radiation)

    if total == 0:
        raise ValueError("Total radiation is zero — cannot normalize.")

    return radiation / total


def prepare_static_inputs(
    data: Data,
    idx: SimpleNamespace,
    time_index: int,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConstants,
) -> dict[str, Any]:
    """Prepare static inputs for microclimate model.

    These are inputs that do not change during the hourly loop, but can vary in space
    and between time steps. They include canopy height, leaf area index, atmospheric
    pressure and CO2 profiles, and absorbed longwave radiation.

    If there is no canopy, canopy height and leaf area index sum are set to zero.

    Args:
        data: Data object
        idx: SimpleNamespace with indices for different layers and variables
        time_index: Time index
        layer_structure: Layer structure object
        abiotic_constants: Set of constants for abiotic model

    Returns:
        Dictionary with prepared static inputs for microclimate model
    """

    # NOTE Canopy height will likely become a separate variable, update as required
    canopy_height = np.nan_to_num(data["layer_heights"][1].to_numpy())

    # LAI sum over all canopy layers only for wind profile, NOT understorey layer
    leaf_area_index_sum = np.nan_to_num(
        np.nansum(data["leaf_area_index"][idx.canopy].to_numpy(), axis=0)
    )

    # Evapotranspiration from plant and hydrology model, [mm per time interval]
    evapotranspiration = (data["canopy_evaporation"] + data["transpiration"]).to_numpy()

    # Atmospheric pressure profile set to reference value, [kPa]
    atmospheric_pressure = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_pressure_ref"],
        time_index=time_index,
    )
    atmospheric_pressure_true = atmospheric_pressure[idx.atm].to_numpy()

    # Atmospheric CO2 profile set to reference value, [kPa]
    atmospheric_co2 = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_co2_ref"],
        time_index=time_index,
    )
    atmospheric_co2_true = atmospheric_co2[idx.atm].to_numpy()

    # Calculate atmospheric layer geometry
    atmospheric_layer_geometry = abiotic_tools.calculate_atmospheric_layer_geometry(
        data=data,
        layer_structure=layer_structure,
    )

    # Absorbed longwave radiation by canopy, [W m-2]
    shortwave_absorption = data["shortwave_absorption"].to_numpy()
    downward_longwave = (
        data["downward_longwave_radiation"].isel(time_index=time_index).to_numpy()
    )

    weights = compute_weights_from_absorbed_radiation(radiation=shortwave_absorption)

    absorbed_longwave_radiation = (
        downward_longwave * weights * abiotic_constants.leaf_emissivity
    )

    absorbed_longwave_radiation[idx.topsoil] = (
        downward_longwave * weights[idx.topsoil] * abiotic_constants.soil_emissivity
    )
    cell_area = data.grid.cell_area

    return {
        "canopy_height": canopy_height,
        "lai_sum": leaf_area_index_sum,
        "evapotranspiration": evapotranspiration,
        "atmospheric_pressure": atmospheric_pressure_true,
        "atmospheric_co2": atmospheric_co2_true,
        "geometry": atmospheric_layer_geometry,
        "absorbed_longwave_radiation": absorbed_longwave_radiation,
        "cell_area": cell_area,
    }


def calculate_wind_profiles(
    static: dict[str, Any],
    data: Data,
    time_index: int,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
) -> dict[str, Any]:
    """Calculate wind profiles for microclimate model.

    This includes the zero plane displacement height, roughness length for momentum,
    wind speed profile, friction velocity, and turbulent mixing coefficient above the
    canopy.

    If there is no canopy, zero plane displacement and roughness length are set to zero,
    and the wind speed profile is constant with height and equal to the reference wind
    speed.

    Args:
        static: Dictionary with prepared static inputs for microclimate model
        data: Data object
        time_index: Time index
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models

    Returns:
        Dictionary with calculated wind profiles for microclimate model
    """

    #   Zero plane displacement height, [m]
    zero_plane_displacement = wind.calculate_zero_plane_displacement(
        canopy_height=static["canopy_height"],
        leaf_area_index=static["lai_sum"],
        zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
    )

    #   Roughness length for momentum, [m]
    roughness_length = wind.calculate_roughness_length_momentum(
        canopy_height=static["canopy_height"],
        leaf_area_index=static["lai_sum"],
        zero_plane_displacement=zero_plane_displacement,
        substrate_surface_roughness_length=(
            abiotic_constants.substrate_surface_roughness_length
        ),
        roughness_element_drag_coefficient=(
            abiotic_constants.roughness_element_drag_coefficient
        ),
        roughness_sublayer_depth_parameter=(
            abiotic_constants.roughness_sublayer_depth_parameter
        ),
        max_ratio_wind_to_friction_velocity=(
            abiotic_constants.max_ratio_wind_to_friction_velocity
        ),
        min_roughness_length=abiotic_constants.min_roughness_length,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    #   Wind speed, [m s-1]
    wind_reference_height = (
        static["canopy_height"] + abiotic_constants.wind_reference_height
    )
    reference_wind_speed = data["wind_speed_ref"].isel(time_index=time_index).to_numpy()

    wind_profile = wind.calculate_wind_profile(
        reference_wind_speed=reference_wind_speed,
        reference_height=wind_reference_height,
        wind_heights=static["geometry"]["heights"],
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        min_wind_speed=abiotic_constants.min_windspeed_below_canopy,
    )

    #   Friction velocity, [m s-1]
    friction_velocity = wind.calculate_friction_velocity(
        reference_wind_speed=reference_wind_speed,
        reference_height=wind_reference_height,
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    # Turbulent mixing coefficient above canopy, [m2 s-1]
    mixing_coefficient = wind.calculate_mixing_coefficients_canopy(
        layer_midpoints=static["geometry"]["layer_midpoints"],
        canopy_height=static["canopy_height"],
        friction_velocity=friction_velocity,
        von_karman_constant=core_constants.von_karmans_constant,
        max_mixing_coefficient=abiotic_constants.max_mixing_coefficient,
    )

    return {
        "zero_plane_displacement": np.nan_to_num(zero_plane_displacement, nan=0.0),
        "roughness_length": np.nan_to_num(roughness_length, nan=0.0),
        "friction_velocity": np.nan_to_num(friction_velocity, nan=0.0),
        "wind_profile": wind_profile,
        "mixing_coefficient": np.nan_to_num(mixing_coefficient, nan=0.0),
    }


def generate_hourly_forcing(
    data: Data,
    static: dict[str, Any],
    time_index: int,
    month: int,
    latitude: float,
) -> dict[str, Any]:
    """Generate hourly profiles for atmospheric forcing variables.

    This includes air temperature, shortwave absorption, relative humidity,
    evapotranspiration, and soil evaporation. The diurnal cycle is generated from
    monthly data using a sinusoidal function.

    Args:
        data: Data object
        static: Dictionary with prepared static inputs for microclimate model
        time_index: Time index
        month: Current month (1-12)
        latitude: Latitude of the location, [degrees]

    Returns:
        Dictionary with generated hourly profiles for atmospheric forcing variables
    """
    return abiotic_tools.generate_diurnal_cycle_from_monthly_data(
        monthly_air_temperature=data["air_temperature_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        monthly_shortwave_absorption=data["shortwave_absorption"].to_numpy(),
        monthly_relative_humidity=data["relative_humidity_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        monthly_evapotranspiration=static["evapotranspiration"],
        monthly_soil_evaporation=data["soil_evaporation"].to_numpy(),
        latitude_deg=latitude,
        month=month,
        daily_temp_amplitude=5,  # TODO abiotic_constants or input data
    )


def initialize_state(
    data: Data,
    idx: SimpleNamespace,
) -> dict[str, Any]:
    """Initialize state variables for microclimate model.

    Args:
        data: Data object
        idx: Indices for different layer types

    Returns:
        Dictionary with initialized state variables
    """

    return {
        "all_air_temperature": data["air_temperature"][idx.atm].to_numpy(),
        "canopy_air_temperature": data["air_temperature"][idx.canopy].to_numpy(),
        "canopy_temperature": data["canopy_temperature"][idx.canopy].to_numpy(),
        "surface_air_temperature": data["air_temperature"][idx.surface].to_numpy(),
        "understorey_temperature": data["air_temperature"][idx.surface].to_numpy(),
        "soil_temperature": data["soil_temperature"][idx.soil].to_numpy(),
        "relative_humidity": data["relative_humidity"][idx.atm].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
    }


def initialize_hourly_record(
    data: Data,
    vars_updated: tuple[str, ...],
    time_dim: int,
    layer_structure: LayerStructure,
) -> dict[str, Any]:
    """Initialize hourly record arrays for microclimate model.

    Args:
        data: Data object
        vars_updated: Tuple containing strings of all variables that are updated by the
            abiotic model
        time_dim: Number of time steps in the hourly record (e.g., 24 for a full day)
        layer_structure: Layer structure object with information on the number of layers
            and their indices

    Returns:
        Dictionary with initialized hourly record arrays for microclimate model
    """
    variables = {name: data[name] for name in vars_updated}
    return abiotic_tools.initialize_data_record(
        variables=variables,
        time_dim=time_dim,
        layers=layer_structure.n_layers,
        cell_ids=data.grid.n_cells,
    )


def update_forcing_boundary_conditions(
    state: dict[str, Any],
    hourly_forcing: dict[str, Any],
    hour: int,
    idx: SimpleNamespace,
) -> dict[str, Any]:
    """Update forcing boundary conditions for microclimate model.

    This updates atmospheric air temperature, humidity, shortwave absorption,
    evapotranspiration, and soil evaporation for the current hour.

    Args:
        state: Current state variables for microclimate model
        hourly_forcing: Generated hourly profiles for atmospheric forcing variables
        hour: Current hour index
        idx: SimpleNamespace with layer indices

    Returns:
        Updated state variables with new boundary conditions
    """

    # Replace atmospheric air temperature and humidity above canopy
    state["all_air_temperature"][0] = hourly_forcing["air_temperature_hourly"][hour, :]
    state["relative_humidity"][0] = hourly_forcing["relative_humidity_hourly"][hour, :]

    # Select shortwave absorption profiles
    state["shortwave_absorption_canopy"] = hourly_forcing[
        "shortwave_absorption_hourly"
    ][hour, idx.canopy, :]
    state["shortwave_absorption_understorey"] = hourly_forcing[
        "shortwave_absorption_hourly"
    ][hour, idx.surface, :]
    state["shortwave_absorption_soil"] = hourly_forcing["shortwave_absorption_hourly"][
        hour, idx.topsoil, :
    ]

    # Select evapotranspiration and soil evaporation
    state["evapotranspiration_canopy"] = hourly_forcing["evapotranspiration_hourly"][
        hour, idx.canopy, :
    ]
    state["evapotranspiration_understorey"] = hourly_forcing[
        "evapotranspiration_hourly"
    ][hour, idx.surface, :]
    state["soil_evaporation"] = hourly_forcing["soil_evaporation_hourly"][hour, :]

    return state


def calculate_thermodynamics(
    state: dict[str, Any],
    static: dict[str, Any],
    hourly_forcing: dict[str, Any],
    hour: int,
    n_cells: int,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
) -> dict[str, Any]:
    """Calculate thermodynamic variables for microclimate model.

    This includes the density of air, specific heat capacity of air, latent heat of
    vapourisation, aerodynamic resistances for day and nighttime, and ventilation rate
    above the canopy.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        hourly_forcing: Generated hourly profiles for atmospheric forcing variables
        hour: Current hour index
        n_cells: Number of grid cells in the model
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models

    Returns:
        Dictionary with calculated thermodynamic variables for microclimate model
    """
    # Define daytime hours
    shortwave_day = hourly_forcing["shortwave_absorption_hourly"][hour, :, :]
    is_day = np.nan_to_num(shortwave_day, nan=0.0).any() > 0

    # Density of air, [kg m-3]
    density_air = abiotic_tools.calculate_air_density(
        air_temperature=state["all_air_temperature"],
        atmospheric_pressure=static["atmospheric_pressure"],
        specific_gas_constant_dry_air=core_constants.specific_gas_constant_dry_air,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )

    # Specific heat capacity of air, [J kg-1 K-1]
    specific_heat_air = calc_specific_heat(
        tc=state["all_air_temperature"],
    )

    #   Latent heat of vapourisation, [kJ kg-1]
    latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
        temperature=state["all_air_temperature"],
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
    )
    latent_heat_vapourisation_j = latent_heat_vapourisation * 1000  # [J kg-1]

    # Aerodynamic resistances for day and nighttime, [s m-1]
    if is_day:
        aerodynamic_resistance_canopy = np.repeat(
            abiotic_constants.aerodynamic_resistance_canopy_day, n_cells
        )
        aerodynamic_resistance_soil = state["aerodynamic_resistance_soil"]

    else:
        aerodynamic_resistance_canopy = np.repeat(
            abiotic_constants.aerodynamic_resistance_canopy_night, n_cells
        )
        aerodynamic_resistance_soil = np.repeat(
            abiotic_constants.aerodynamic_resistance_soil_night, n_cells
        )

    #  Ventilation rate above canopy, [s-1]
    ventilation_rate = wind.calculate_ventilation_rate(
        aerodynamic_resistance=aerodynamic_resistance_canopy,
        characteristic_height=static["canopy_height"]
        + state["zero_plane_displacement"],
    )

    return {
        "density_air": density_air,
        "specific_heat_air": specific_heat_air,
        "latent_heat_vapourisation": latent_heat_vapourisation_j,
        "aerodynamic_resistance_canopy": aerodynamic_resistance_canopy,
        "aerodynamic_resistance_soil": aerodynamic_resistance_soil,
        "ventilation_rate": ventilation_rate,
    }


def calculate_vegetation_temperature(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    idx: SimpleNamespace,
) -> NDArray[np.floating]:
    """Calculate canopy and understorey temperature for microclimate model.

    This uses the energy balance equation to solve for canopy temperature based on
    absorbed radiation, evapotranspiration, aerodynamic resistance, and other
    thermodynamic variables.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        idx: SimpleNamespace with layer indices

    Returns:
        new vegetation temperature
    """

    vegetation_temperature = np.concatenate(
        [state["canopy_temperature"], [state["understorey_temperature"]]], axis=0
    )
    vegetation_air_temperature = np.concatenate(
        [state["canopy_air_temperature"], [state["surface_air_temperature"]]], axis=0
    )

    evapotranspiration = np.concatenate(
        [state["evapotranspiration_canopy"], [state["evapotranspiration_understorey"]]],
        axis=0,
    )
    shortwave_absorption = np.concatenate(
        [
            state["shortwave_absorption_canopy"],
            [state["shortwave_absorption_understorey"]],
        ],
        axis=0,
    )
    absorbed_longwave_radiation = np.concatenate(
        [
            static["absorbed_longwave_radiation"][idx.canopy],
            [static["absorbed_longwave_radiation"][idx.surface]],
            [static["absorbed_longwave_radiation"][idx.topsoil]],
        ],
        axis=0,
    )

    return energy_balance.solve_canopy_temperature(
        canopy_temperature_initial=vegetation_temperature,
        air_temperature=vegetation_air_temperature,
        evapotranspiration=evapotranspiration,
        absorbed_shortwave_radiation=shortwave_absorption,
        absorbed_longwave_radiation=absorbed_longwave_radiation,
        specific_heat_air=state["specific_heat_air"][1:],
        density_air=state["density_air"][1:],
        aerodynamic_resistance=state["aerodynamic_resistance_canopy"],
        latent_heat_vapourisation=state["latent_heat_vapourisation"][1:],
        emissivity_leaf=abiotic_constants.leaf_emissivity,
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
        seconds_to_hour=core_constants.seconds_to_hour,
        return_fluxes=False,
        maxiter=10000,
    )


def calculate_vegetation_fluxes(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    idx: SimpleNamespace,
) -> dict[str, Any]:
    """Calculate vegetation fluxes for microclimate model.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        hourly_forcing: Generated hourly profiles for atmospheric forcing variables
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        idx: SimpleNamespace with layer indices

    Returns:
        Dictionary with vegetation fluxes
    """

    vegetation_temperature = np.concatenate(
        [state["canopy_temperature"], [state["understorey_temperature"]]], axis=0
    )
    vegetation_air_temperature = np.concatenate(
        [state["canopy_air_temperature"], [state["surface_air_temperature"]]], axis=0
    )
    evapotranspiration = np.concatenate(
        [state["evapotranspiration_canopy"], [state["evapotranspiration_understorey"]]],
        axis=0,
    )
    shortwave_absorption = np.concatenate(
        [
            state["shortwave_absorption_canopy"],
            [state["shortwave_absorption_understorey"]],
        ],
        axis=0,
    )

    absorbed_longwave_radiation = np.concatenate(
        [
            static["absorbed_longwave_radiation"][idx.canopy],
            [static["absorbed_longwave_radiation"][idx.surface]],
        ],
        axis=0,
    )

    fluxes = energy_balance.calculate_energy_balance_residual(
        canopy_temperature_initial=vegetation_temperature,
        air_temperature=vegetation_air_temperature,
        evapotranspiration=evapotranspiration,
        absorbed_shortwave_radiation=shortwave_absorption,
        absorbed_longwave_radiation=absorbed_longwave_radiation,
        leaf_emissivity=abiotic_constants.leaf_emissivity,
        specific_heat_air=state["specific_heat_air"][1:],
        density_air=state["density_air"][1:],
        aerodynamic_resistance=state["aerodynamic_resistance_canopy"],
        latent_heat_vapourisation=state["latent_heat_vapourisation"][1:],
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
        seconds_to_hour=core_constants.seconds_to_hour,
        return_fluxes=True,
    )

    return fluxes


def calculate_soil_fluxes(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    time_interval: float,
    idx: SimpleNamespace,
) -> dict[str, NDArray[np.floating]]:
    """Calculate soil fluxes for microclimate model.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        hourly_forcing: Generated hourly profiles for atmospheric forcing variables
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        time_interval: Time interval for flux calculations, [s]
        idx: SimpleNamespace with layer indices

    Returns:
        Dictionary with soil fluxes
    """

    out = {}

    # longwave emission from topsoil, [W m-2]
    out["longwave_emission_soil"] = energy_balance.calculate_longwave_emission(
        temperature=state["soil_temperature"][0],
        emissivity=abiotic_constants.soil_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    #  Sensible heat flux from topsoil, [W m-2]
    out["sensible_heat_flux_soil"] = energy_balance.calculate_sensible_heat_flux(
        density_air=state["density_air"][-1],
        specific_heat_air=state["specific_heat_air"][-1],
        air_temperature=state["surface_air_temperature"],
        surface_temperature=state["soil_temperature"][0],
        aerodynamic_resistance=state["aerodynamic_resistance_soil"],
    )

    # Latent heat flux topsoil, [W m-2]
    out["latent_heat_flux_soil"] = energy_balance.calculate_latent_heat_flux(
        evapotranspiration=state["soil_evaporation"],
        latent_heat_vapourisation=state["latent_heat_vapourisation"][-1],
        time_interval=time_interval,
    )

    # Ground heat flux, [W m-2]
    out["ground_heat_flux_soil"] = (
        state["shortwave_absorption_soil"]
        - out["longwave_emission_soil"]
        - out["latent_heat_flux_soil"]
        - out["sensible_heat_flux_soil"]
        + static["absorbed_longwave_radiation"][idx.topsoil, :]
    )

    return out


def update_air_temperature(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_bounds: AbioticSimpleBounds,
    time_interval: float,
) -> NDArray[np.floating]:
    """Update air temperature profiles based on calculated fluxes and wind mixing.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        abiotic_bounds: Bounds for air temperature to ensure physical realism
        time_interval: Time interval for flux calculations, [s]

    Returns:
        Updated air temperature profiles for microclimate model
    """

    # Update canopy air temperatures, [C]
    canopy_air_temperature = energy_balance.update_air_temperature(
        air_temperature=state["canopy_air_temperature"],
        sensible_heat_flux=state["sensible_heat_flux"][0:-1],
        specific_heat_air=state["specific_heat_air"][1:-1],
        density_air=state["density_air"][1:-1],
        mixing_layer_thickness=static["geometry"]["thickness"][1:-1],
        time_interval=time_interval,
    )

    # Update surface air temperatures, [C]
    surface_air_temperature = energy_balance.update_air_temperature(
        air_temperature=state["surface_air_temperature"],
        sensible_heat_flux=state["sensible_heat_flux"][-1]
        + state["sensible_heat_flux_soil"],
        specific_heat_air=state["specific_heat_air"][-1],
        density_air=state["density_air"][-1],
        mixing_layer_thickness=static["geometry"]["thickness"][-1],
        time_interval=time_interval,
    )

    # Update all air temperatures, [C]
    all_air_temperature = np.copy(state["all_air_temperature"])
    all_air_temperature[1 : len(canopy_air_temperature) + 1] = canopy_air_temperature
    all_air_temperature[-1] = surface_air_temperature
    all_air_temperature = wind.mix_and_ventilate(
        input_variable=all_air_temperature,
        ventilation_rate=state["ventilation_rate"],
        mixing_coefficient=state["mixing_coefficient"],
        limits=abiotic_bounds.air_temperature[:2],
    )

    return all_air_temperature


def update_atmospheric_humidity(
    state: dict[str, Any],
    static: dict[str, Any],
    pyrealm_core_constants: PyrealmCoreConst,
    core_constants: CoreConstants,
    abiotic_constants: AbioticConstants,
    time_interval: float,
) -> dict[str, Any]:
    """Update atmospheric humidity profiles based on fluxes and wind mixing."""

    # Saturated vapour pressure of air, [kPa]
    saturated_vapour_pressure_air = calc_vp_sat(
        ta=state["all_air_temperature"],
        core_const=pyrealm_core_constants,
    )

    # Specific humidity of air, [kg kg-1]
    specific_humidity_air = abiotic_tools.calculate_specific_humidity(
        air_temperature=state["all_air_temperature"],
        relative_humidity=state["relative_humidity"],
        atmospheric_pressure=static["atmospheric_pressure"],
        molecular_weight_ratio_water_to_dry_air=(
            core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        pyrealm_core_constants=pyrealm_core_constants,
    )

    # Calculate specific humidity at saturation
    mixing_ratio_saturation = (
        core_constants.molecular_weight_ratio_water_to_dry_air
        * saturated_vapour_pressure_air
        / (static["atmospheric_pressure"] - saturated_vapour_pressure_air)
    )
    max_specific_humidity = mixing_ratio_saturation / (1 + mixing_ratio_saturation)

    # Update atmospheric humidity variables, integration interval 1 hour
    return energy_balance.update_humidity_vpd(
        canopy_evapotranspiration=state["evapotranspiration_canopy"],
        understorey_evapotranspiration=state["evapotranspiration_understorey"],
        soil_evaporation=state["soil_evaporation"],
        saturated_vapour_pressure=saturated_vapour_pressure_air,
        specific_humidity=specific_humidity_air,
        layer_thickness=static["geometry"]["thickness"],
        atmospheric_pressure=static["atmospheric_pressure"],
        density_air=state["density_air"],
        mixing_coefficient=state["mixing_coefficient"],
        ventilation_rate=state["ventilation_rate"],
        molecular_weight_ratio_water_to_dry_air=(
            core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        dry_air_factor=abiotic_constants.dry_air_factor,
        cell_area=static["cell_area"],
        limits=(0, max_specific_humidity[0]),  # TODO make layer specific
        time_interval=time_interval,
    )


# def Run loop for each hour
def run_hour_step(
    state: dict[str, Any],
    static: dict[str, Any],
    hourly_forcing: dict[str, Any],
    hour: int,
    idx: SimpleNamespace,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    pyrealm_constants: PyrealmCoreConst,
    abiotic_bounds: AbioticSimpleBounds,
    time_interval: float,
):
    """Run one hour step of the microclimate model.

    This function will be called iteratively for each hour in the day, updating the
    state variables based on the calculated fluxes and thermodynamics.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        hourly_forcing: Generated hourly profiles for atmospheric forcing variables
        hour: Current hour index
        idx: SimpleNamespace with layer indices
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        pyrealm_constants: Set of constants from pyrealm core that are used in
            calculations
        abiotic_bounds: Set of bounds for abiotic values
        time_interval: Time interval for flux calculations, [s]

    Returns:
        Updated state variables for the current hour
    """
    # Update forcing boundary conditions for the current hour
    update_forcing_boundary_conditions(
        state=state, hourly_forcing=hourly_forcing, hour=hour, idx=idx
    )

    # Update tehermodynamics
    thermo = calculate_thermodynamics(
        state=state,
        static=static,
        hourly_forcing=hourly_forcing,
        hour=hour,
        n_cells=idx.cell_id,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )
    state.update(thermo)

    # Update vegetation temperature
    vegetation_temperature = calculate_vegetation_temperature(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )
    state["vegetation_temperature"] = vegetation_temperature

    # Calculate vegetation fluxes
    vegetation_fluxes = calculate_vegetation_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )
    state.update(vegetation_fluxes)

    # Calculate soil fluxes
    soil_fluxes = calculate_soil_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        time_interval=time_interval,
        idx=idx,
    )
    state.update(soil_fluxes)

    # Calculate soil temperature
    soil_temperature = energy_balance.update_soil_temperature(
        ground_heat_flux=state["ground_heat_flux_soil"],
        soil_temperature=state["soil_temperature"],
        soil_layer_thickness=static["geometry"]["thickness"][-1],
        soil_thermal_conductivity=abiotic_constants.soil_thermal_conductivity,
        soil_bulk_density=abiotic_constants.bulk_density_soil,
        specific_heat_capacity_soil=abiotic_constants.specific_heat_capacity_soil,
        time_interval=time_interval,
    )
    state["soil_temperature"] = soil_temperature

    # Update air temperature
    air_temperature = update_air_temperature(
        state=state,
        static=static,
        abiotic_bounds=abiotic_bounds,
        time_interval=1,  # core_constants.seconds_to_hour,
    )
    state["air_temperature"] = air_temperature

    # Update atmospheric humidity
    air_humidity = update_atmospheric_humidity(
        state=state,
        static=static,
        pyrealm_core_constants=pyrealm_constants,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        time_interval=time_interval,
    )
    state.update(air_humidity)
    print(state["mixing_coefficient"])
    return state


# def run_microclimate(
#     data: Data,
#     vars_updated: tuple[str, ...],
#     time_index: int,
#     time_dim: int,
#     time_interval: float,
#     month: int,
#     latitude: float,
#     layer_structure: LayerStructure,
#     abiotic_constants: AbioticConstants,
#     core_constants: CoreConstants,
#     abiotic_bounds: AbioticSimpleBounds,
# ) -> dict[str, Any]:
#     """Run the microclimate model for one day, iterating through hourly time steps.

#     This function prepares static inputs, calculates wind profiles, generates hourly
#     forcing, initializes state and record variables, and then iteratively updates the
#     state variables based on calculated fluxes and thermodynamics for each hour.

#     Args:
#         data: Data object containing all model variables and grid information
#         vars_updated: Tuple containing strings of all variables that are updated by
#             abiotic model
#         time_index: Time index for the current day in the data
#         time_dim: Number of time steps in the hourly record (e.g., 24 for a full day)
#         time_interval: Time interval for flux calculations, [s]
#         month: Current month (1-12) for generating diurnal cycle
#         latitude: Latitude of the location, [degrees]
#         layer_structure: Layer structure object with information on number of layers
#             and their indices
#         abiotic_constants: Set of constants for abiotic model
#         core_constants: Set of constants that are shared across all models
#         abiotic_bounds: Bounds for air temperature to ensure physical realism

#     Returns:
#         Dictionary with updated state variables and hourly record for the day
#     """

#     # Select indices for different layer types
#     idx = build_indices(data=data, layer_structure=layer_structure)

#     # Initialise state dict
#     state = initialize_state(
#         data=data,
#         idx=idx,
#     )

#     # Prepare static inputs for microclimate model
#     static = prepare_static_inputs(
#         data=data,
#         idx=idx,
#         time_index=time_index,
#         layer_structure=layer_structure,
#         abiotic_constants=abiotic_constants,
#     )

#     # Calculate wind profiles for microclimate model
#     wind_state = calculate_wind_profiles(
#         static=static,
#         abiotic_constants=abiotic_constants,
#         core_constants=core_constants,
#         data=data,
#         time_index=time_index,
#     )
#     state.update(wind_state)

#     # Generate hourly forcing for microclimate model
#     forcing = generate_hourly_forcing(
#         data=data,
#         static=static,
#         time_index=time_index,
#         month=month,
#         latitude=latitude,
#     )

#     # Initialize hourly record for microclimate model
#     data_record = initialize_hourly_record(
#         data=data,
#         vars_updated=abiotic_constants.vars_updated,
#         time_dim=time_dim,
#         layer_structure=layer_structure,
#     )

#     for hour in range(time_dim):
#         state = run_hour_step(
#             data=data,
#             state=state,
#             static=static,
#             hourly_forcing=forcing,
#             hour=hour,
#             idx=idx,
#             abiotic_constants=abiotic_constants,
#             core_constants=core_constants,
#             pyrealm_constants=core_constants,
#             time_interval=time_interval,
#             time_index=time_index,
#         )

#         # Check that all vars are updated
#         abiotic_tools.validate_variables(
#             names=vars_updated,
#             values=state,
#             exclude=("density_air", "specific_heat_air", "wind_speed"),
#         )

#         # Record this hour
#         abiotic_tools.record_hourly_output(
#             hour=hour,
#             data_record=data_record,
#             layer_structure=layer_structure,
#             hourly_values=state,
#         )

#     return assemble_output(
#         data=data,
#         data_record=data_record,
#         layer_structure=layer_structure,
#     )

# # TODO
# # def Write to hourly record
# # selection of variables to write to hourly record with correct indices


# def combine output to write to data
