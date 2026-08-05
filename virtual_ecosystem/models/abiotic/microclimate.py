"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

from types import SimpleNamespace
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calculate_specific_heat, calculate_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic import abiotic_tools, energy_balance, wind
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants
from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


def prepare_static_inputs(
    data: Data,
    idx: SimpleNamespace,
    time_index: int,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
) -> dict[str, Any]:
    """Prepare static inputs for microclimate model.

    These are inputs that do not change during the hourly loop, but can vary in space
    and between VE time steps. They include canopy height, sum over canopy leaf area
    index, atmospheric pressure and CO2 profiles, absorbed longwave radiation, and cell
    area.

    If there is no canopy, canopy height and leaf area index sum are set to zero.

    Args:
        data: Data object
        idx: SimpleNamespace with indices for different layers and variables
        time_index: Time index
        layer_structure: Layer structure object
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models

    Returns:
        Dictionary with prepared static inputs for microclimate model
    """

    # NOTE Canopy height will likely become a separate variable, update as required
    canopy_height = np.nan_to_num(data["layer_heights"][1].to_numpy())

    # LAI sum over all canopy layers only for wind profile, NOT understorey layer
    leaf_area_index_sum = np.nan_to_num(
        np.nansum(data["leaf_area_index"][idx.canopy].to_numpy(), axis=0)
    )

    leaf_area_index = data["leaf_area_index"].copy().to_numpy()

    # Evapotranspiration from plant and hydrology model, [mm per time interval]
    evapotranspiration = (data["canopy_evaporation"] + data["transpiration"]).to_numpy()

    # Atmospheric pressure profile set to reference value, [kPa]
    atmospheric_pressure = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_pressure_ref"],
        time_index=time_index,
    )
    atmospheric_pressure_true = atmospheric_pressure.to_numpy()

    # Atmospheric CO2 profile set to reference value, [kPa]
    atmospheric_co2 = abiotic_tools.update_profile_from_reference(
        layer_structure=layer_structure,
        mask_variable=data["air_temperature"],
        variable_name=data["atmospheric_co2_ref"],
        time_index=time_index,
    )
    atmospheric_co2_true = atmospheric_co2.to_numpy()

    # Calculate atmospheric layer geometry
    atmospheric_layer_geometry = abiotic_tools.calculate_atmospheric_layer_geometry(
        data=data,
        idx=idx,
        minimum_mixing_depth=abiotic_constants.minimum_mixing_depth,
    )

    # Absorbed longwave radiation, [W m-2]
    downward_longwave = (
        data["downward_longwave_radiation"].isel(time_index=time_index).to_numpy()
    )

    absorbed_longwave_radiation = energy_balance.calculate_absorbed_longwave_radiation(
        downward_longwave=downward_longwave,
        leaf_area_index=data["leaf_area_index"].to_numpy(),
        soil_temperature=data["soil_temperature"].to_numpy(),
        canopy_temperature=data["canopy_temperature"].to_numpy(),
        leaf_emissivity=abiotic_constants.leaf_emissivity,
        soil_emissivity=abiotic_constants.soil_emissivity,
        extinction_coefficient_lw=abiotic_constants.extinction_coefficient_longwave,
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
        surface_index=idx.surface,
        topsoil_index=idx.topsoil,
    )

    # Cell area, [m2]
    cell_area = data.grid.cell_area

    return {
        "canopy_height": canopy_height,
        "leaf_area_index": leaf_area_index,
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
    layer_structure: LayerStructure,
) -> dict[str, Any]:
    """Calculate wind profiles for microclimate model.

    This function calculates the zero plane displacement height, roughness length for
    momentum, wind speed profile, friction velocity, and turbulent mixing coefficient
    above the canopy. These variables currently remain constant over the course of one
    day.

    If there is no canopy, zero plane displacement and roughness length are set to zero,
    and the wind speed profile is constant with height and equal to the reference wind
    speed.

    Args:
        static: Dictionary with prepared static inputs for microclimate model
        data: Data object
        time_index: Time index
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        layer_structure: Layer structure

    Returns:
        Dictionary with calculated wind profiles for microclimate model
    """

    #   Zero plane displacement height, [m]
    zero_plane_displacement = wind.calculate_zero_plane_displacement(
        canopy_height=static["canopy_height"],
        leaf_area_index=static["lai_sum"],
        zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
        denominator_tolerance=abiotic_constants.denominator_tolerance,
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
        denominator_tolerance=abiotic_constants.denominator_tolerance,
    )

    #   Wind speed, [m s-1]
    wind_reference_height = (
        static["canopy_height"] + abiotic_constants.wind_reference_height
    )
    reference_wind_speed = data["wind_speed_ref"].isel(time_index=time_index).to_numpy()

    wind_speed = layer_structure.from_template()
    wind_speed[layer_structure.index_filled_atmosphere] = wind.calculate_wind_profile(
        reference_wind_speed=reference_wind_speed,
        reference_height=wind_reference_height,
        wind_heights=static["geometry"]["heights"][
            layer_structure.index_filled_atmosphere
        ],
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        min_wind_speed=abiotic_constants.min_windspeed_below_canopy,
        denominator_tolerance=abiotic_constants.denominator_tolerance,
    )

    #   Friction velocity, [m s-1]
    friction_velocity = wind.calculate_friction_velocity(
        reference_wind_speed=reference_wind_speed,
        reference_height=wind_reference_height,
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        von_karman_constant=core_constants.von_karmans_constant,
        denominator_tolerance=abiotic_constants.denominator_tolerance,
    )

    # Turbulent mixing coefficient above canopy, [m2 s-1]
    mixing_coefficient = layer_structure.from_template()
    mixing_coefficient[layer_structure.index_filled_atmosphere] = (
        wind.calculate_mixing_coefficients_canopy(
            layer_midpoints=np.nan_to_num(
                static["geometry"]["layer_midpoints"][
                    layer_structure.index_filled_atmosphere
                ],
                nan=0.0,
            ),
            canopy_height=static["canopy_height"],
            friction_velocity=friction_velocity,
            von_karman_constant=core_constants.von_karmans_constant,
            max_mixing_coefficient=abiotic_constants.max_mixing_coefficient,
            denominator_tolerance=abiotic_constants.denominator_tolerance,
        )
    )

    return {
        "zero_plane_displacement": np.nan_to_num(zero_plane_displacement, nan=0.0),
        "roughness_length": np.nan_to_num(roughness_length, nan=0.0),
        "friction_velocity": np.nan_to_num(friction_velocity, nan=0.0),
        "wind_speed": wind_speed,
        "mixing_coefficient": np.nan_to_num(mixing_coefficient, nan=0.0),
    }


def generate_hourly_forcing(
    data: Data,
    static: dict[str, Any],
    time_index: int,
    month: int,
    days: int,
    latitude: float,
    abiotic_constants: AbioticConstants,
) -> dict[str, Any]:
    """Generate hourly profiles for atmospheric forcing variables.

    This function generates a diurnal cycle of air temperature, shortwave absorption,
    relative humidity, evapotranspiration, and soil evaporation. This diurnal cycle is
    generated from monthly data using a sinusoidal function.

    Args:
        data: Data object
        static: Dictionary with prepared static inputs for microclimate model
        time_index: Time index
        month: Current month (1-12)
        days: Number of days per month
        latitude: Latitude of the location, [degrees]
        abiotic_constants: Set of constants for abiotic model

    Returns:
        Dictionary with generated hourly profiles for atmospheric forcing variables
    """
    total_shortwave_absorption = (
        energy_balance.calculate_total_absorbed_shortwave_radiation(
            downward_shortwave_radiation=data["downward_shortwave_radiation"]
            .isel(time_index=time_index)
            .to_numpy(),
            shortwave_absorption_by_canopy=data["shortwave_absorption"].to_numpy(),
            fraction_par_used=abiotic_constants.fraction_par_used_for_photosynthesis,
            leaf_absorptance_non_par=abiotic_constants.leaf_absorptance_non_par,
            par_fraction=abiotic_constants.par_fraction_of_shortwave_radiation,
        )
    )

    return abiotic_tools.generate_diurnal_cycle_from_monthly_data(
        monthly_air_temperature=data["air_temperature_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        monthly_shortwave_absorption=total_shortwave_absorption,
        monthly_relative_humidity=data["relative_humidity_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        monthly_evapotranspiration=static["evapotranspiration"],
        monthly_soil_evaporation=data["soil_evaporation"].to_numpy(),
        latitude_deg=latitude,
        month=month,
        days=days,
        daily_temp_amplitude=data["diurnal_temperature_range_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
    )


def initialize_state(
    data: Data,
) -> dict[str, Any]:
    """Initialize state variables for microclimate model.

    This function initialises state variables that are updated during the diurnal cycle.

    Args:
        data: Data object

    Returns:
        Dictionary with initialized state variables
    """

    return {
        "air_temperature": data["air_temperature"].to_numpy(),
        "canopy_temperature": data["canopy_temperature"].to_numpy(),
        "soil_temperature": data["soil_temperature"].to_numpy(),
        "relative_humidity": data["relative_humidity"].to_numpy(),
        "aerodynamic_resistance_soil": data["aerodynamic_resistance_soil"].to_numpy(),
        "longwave_emission": data["longwave_emission"].to_numpy(),
    }


def initialize_hourly_record(
    data: Data,
    vars_updated: tuple[str, ...],
    time_dim: int,
    layer_structure: LayerStructure,
) -> dict[str, Any]:
    """Initialize hourly record arrays for microclimate model.

    This function initialised a dictionary of data arrays for all variables that are
    updated by the abiotic model. These arrays collect the hourly data which is later
    averaged and returned to the data object.

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
) -> dict[str, Any]:
    """Update forcing boundary conditions for microclimate model.

    This function updates boundary conditions and forcing for atmospheric air
    temperature, relative humidity, shortwave absorption, evapotranspiration, and soil
    evaporation for the current hour.

    Args:
        state: Current state variables for microclimate model
        hourly_forcing: Generated hourly profiles for atmospheric forcing variables
        hour: Current hour index

    Returns:
        Updated state variables with new boundary conditions
    """

    # Replace atmospheric air temperature and humidity above canopy
    state["air_temperature"][0] = hourly_forcing["air_temperature_hourly"][hour, :]
    state["relative_humidity"][0] = hourly_forcing["relative_humidity_hourly"][hour, :]

    # Select shortwave absorption profiles for hour
    state["shortwave_absorption"] = hourly_forcing["shortwave_absorption_hourly"][
        hour, :, :
    ]

    # Select evapotranspiration and soil evaporation for hour
    state["evapotranspiration"] = hourly_forcing["evapotranspiration_hourly"][
        hour, :, :
    ]
    state["soil_evaporation"] = hourly_forcing["soil_evaporation_hourly"][hour, :]

    return state


def calculate_thermodynamics(
    state: dict[str, Any],
    static: dict[str, Any],
    hourly_forcing: dict[str, Any],
    hour: int,
    n_cells: int,
    idx: SimpleNamespace,
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
        idx: SimpleNamespace with layer indices
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
        air_temperature=state["air_temperature"],
        atmospheric_pressure=static["atmospheric_pressure"],
        specific_gas_constant_dry_air=core_constants.specific_gas_constant_dry_air,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )

    # Specific heat capacity of air, [J kg-1 K-1]
    specific_heat_air = calculate_specific_heat(
        tc=state["air_temperature"],
    )

    #   Latent heat of vapourisation, [kJ kg-1]
    latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
        temperature=state["air_temperature"],
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
    )
    latent_heat_vapourisation_j = latent_heat_vapourisation * 1000  # [J kg-1]

    # Aerodynamic resistances for day and nighttime, [s m-1]
    if is_day:
        # Fallback for no canopy
        wind_height = np.nan_to_num(
            static["geometry"]["heights"][1],
            nan=abiotic_constants.wind_reference_height,
        )
        wind_speed = np.where(
            np.isnan(static["wind_speed"][1]),
            static["wind_speed"][idx.above],
            static["wind_speed"][1],
        )

        aerodynamic_resistance_canopy = aerodynamic_resistance_canopy = (
            wind.calculate_aerodynamic_resistance(
                wind_heights=wind_height,
                roughness_length=static["roughness_length"],
                zero_plane_displacement=static["zero_plane_displacement"],
                wind_speed=wind_speed,
                von_karman_constant=core_constants.von_karmans_constant,
                fallback_resistance=abiotic_constants.aerodynamic_resistance_canopy_day,
                denominator_tolerance=abiotic_constants.denominator_tolerance,
            )
        )
        aerodynamic_resistance_canopy = aerodynamic_resistance_canopy.squeeze()
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
        + static["zero_plane_displacement"],
        understorey_ventilation_rate=abiotic_constants.understorey_ventilation_rate,
        surface_layer_height=static["geometry"]["thickness"][idx.surface],
        denominator_tolerance=abiotic_constants.denominator_tolerance,
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

    This uses the energy balance equation to solve for canopy and understorey
    temperature based on absorbed radiation, evapotranspiration, aerodynamic resistance,
    and other thermodynamic variables.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        idx: SimpleNamespace with layer indices

    Returns:
        new vegetation temperature
    """
    n_layers, n_cells = state["canopy_temperature"].shape

    # Build layer-specific aerodynamic resistance array
    aerodynamic_resistance_2d = np.full((n_layers, n_cells), np.nan)

    # Canopy layers use canopy resistance
    aerodynamic_resistance_2d[idx.canopy, :] = state["aerodynamic_resistance_canopy"]

    # Surface layer uses soil/understorey resistance
    aerodynamic_resistance_2d[idx.surface, :] = state["aerodynamic_resistance_soil"]

    residual = energy_balance.make_canopy_residual(
        state=state,
        static=static,
        aerodynamic_resistance=aerodynamic_resistance_2d,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )

    # Result contains new canopy and understorey temperature
    mask = np.isfinite(static["leaf_area_index"])
    canopy_temperature_true = state["canopy_temperature"].copy()
    canopy_temperature_true[~mask] = np.nan

    vegetation_temperature = energy_balance.secant_solve_cells_layers(
        residual_function=residual,
        initial_guess=canopy_temperature_true,
        maxiter_secant=abiotic_constants.maxiter_secant_solver,
        convergence_tolerance=abiotic_constants.convergence_tolerance_secant_solver,
        small_perturbation_second_guess=(
            abiotic_constants.small_perturbation_second_guess_secant_solver
        ),
        denominator_tolerance=abiotic_constants.denominator_tolerance,
    )

    return vegetation_temperature


def calculate_vegetation_fluxes(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    idx: SimpleNamespace,
) -> dict[str, Any]:
    """Calculate vegetation fluxes for microclimate model.

    This function calculates the components of the vegetation energy balance, including
    net radiation, longwave emission, and sensible and latent heat flux.

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

    n_layers, n_cells = state["canopy_temperature"].shape

    # Same layer-specific resistance as used in the solver
    aerodynamic_resistance_2d = np.full((n_layers, n_cells), np.nan)
    aerodynamic_resistance_2d[idx.canopy, :] = state["aerodynamic_resistance_canopy"]
    aerodynamic_resistance_2d[idx.surface, :] = state["aerodynamic_resistance_soil"]

    fluxes = energy_balance.calculate_energy_balance_residual(
        canopy_temperature_initial=state["canopy_temperature"],
        air_temperature=state["air_temperature"],
        evapotranspiration=state["evapotranspiration"],
        absorbed_shortwave_radiation=state["shortwave_absorption"],
        absorbed_longwave_radiation=static["absorbed_longwave_radiation"],
        leaf_emissivity=abiotic_constants.leaf_emissivity,
        specific_heat_air=state["specific_heat_air"],
        density_air=state["density_air"],
        aerodynamic_resistance=aerodynamic_resistance_2d,
        latent_heat_vapourisation=state["latent_heat_vapourisation"],
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
        seconds_to_hour=core_constants.seconds_to_hour,
        return_fluxes=True,
    )

    return fluxes  # type: ignore


def calculate_soil_fluxes(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    time_interval: float,
    idx: SimpleNamespace,
) -> dict[str, NDArray[np.floating]]:
    """Calculate soil fluxes for microclimate model.

    This function calculates the components of the soil energy balance, including
    net radiation, longwave emission, sensible and latent heat flux, and ground heat
    flux.

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
        temperature=state["soil_temperature"][idx.topsoil]
        + core_constants.zero_Celsius,
        emissivity=abiotic_constants.soil_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    #  Sensible heat flux from topsoil, [W m-2]
    out["sensible_heat_flux_soil"] = energy_balance.calculate_sensible_heat_flux(
        density_air=state["density_air"][idx.surface],
        specific_heat_air=state["specific_heat_air"][idx.surface],
        air_temperature=state["air_temperature"][idx.surface],
        surface_temperature=state["soil_temperature"][idx.topsoil],
        aerodynamic_resistance=state["aerodynamic_resistance_soil"],
    )

    # Latent heat flux topsoil, [W m-2]
    out["latent_heat_flux_soil"] = energy_balance.calculate_latent_heat_flux(
        evapotranspiration=state["soil_evaporation"],
        latent_heat_vapourisation=state["latent_heat_vapourisation"][idx.surface],
        time_interval=time_interval,
    )

    # Ground heat flux, [W m-2]
    out["ground_heat_flux"] = (
        state["shortwave_absorption"][idx.topsoil]
        - out["longwave_emission_soil"]
        - out["latent_heat_flux_soil"]
        - out["sensible_heat_flux_soil"]
        + static["absorbed_longwave_radiation"][idx.topsoil]
    )

    # Net radiation, [W m-2]
    out["net_radiation_soil"] = (
        state["shortwave_absorption"][idx.topsoil]
        - out["longwave_emission_soil"]
        + static["absorbed_longwave_radiation"][idx.topsoil]
    )

    return out


def update_air_temperature(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_bounds: AbioticSimpleBounds,
    idx: SimpleNamespace,
    min_leaf_area_index_for_mixing: float,
    integration_time_step: float,
) -> NDArray[np.floating]:
    """Update air temperature profiles based on calculated fluxes and turbulent mixing.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        abiotic_bounds: Bounds for air temperature to ensure physical realism
        idx: Indices for different layer types
        denominator_tolerance: Small value to prevent division by zero in calculations
        min_leaf_area_index_for_mixing: Minimum leaf area index required for turbulent
            mixing to occur.
        integration_time_step: Time step for sensible heat flux integration, [s]

    Returns:
        Updated air temperature profiles for microclimate model
    """
    # Update canopy air temperatures, [C]
    canopy_air_temperature = energy_balance.update_canopy_air_temperature(
        air_temperature=state["air_temperature"],
        sensible_heat_flux=state["sensible_heat_flux"],
        specific_heat_air=state["specific_heat_air"],
        density_air=state["density_air"],
        mixing_layer_thickness=static["geometry"]["thickness"],
        integration_time_step=integration_time_step,
    )

    # Update all air temperatures, [C]
    # We assume here that if the canopy is very thin, it is in
    # equilibrium with the air. This is to prevent unrealistic air temperatures when
    # there is very little canopy.
    canopy_air_temperature[idx.canopy] = np.where(
        static["leaf_area_index"][idx.canopy] > min_leaf_area_index_for_mixing,
        canopy_air_temperature[idx.canopy],
        state["air_temperature"][idx.canopy],
    )

    mixing_limits = (
        abiotic_bounds.air_temperature[0],
        np.repeat(abiotic_bounds.air_temperature[1], len(state["ventilation_rate"])),
    )
    air_temperature = wind.mix_and_ventilate(
        input_variable=canopy_air_temperature,
        ventilation_rate=state["ventilation_rate"],
        mixing_coefficient=static["mixing_coefficient"],
        limits=mixing_limits,
        surface_index=idx.surface,
    )

    return air_temperature


def update_atmospheric_humidity(
    state: dict[str, Any],
    static: dict[str, Any],
    pyrealm_core_constants: PyrealmCoreConst,
    core_constants: CoreConstants,
    abiotic_constants: AbioticConstants,
    abiotic_bounds: AbioticSimpleBounds,
    idx: SimpleNamespace,
    time_interval: float,
) -> dict[str, Any]:
    """Update atmospheric humidity profiles based on fluxes and turbulent mixing.

    Args:
        state: Current state variables for microclimate model
        static: Prepared static inputs for microclimate model
        pyrealm_core_constants: Set of constants from pyrealm core that are used
        core_constants: Set of constants that are shared across all models
        abiotic_constants: Set of constants for abiotic model
        abiotic_bounds: Bounds for atmospheric humidity variables
        idx: SimpleNamespace with layer indices
        time_interval: Time interval for flux calculations, [s]

    Returns:
        dict with atmospheric humidity, vapour pressure, vapour pressure deficit,
            specific humidity
    """

    # Saturated vapour pressure of air, [kPa]
    saturated_vapour_pressure_air = calculate_vp_sat(
        tc=state["air_temperature"],
        core_const=pyrealm_core_constants,
    )

    # Specific humidity of air, [kg kg-1]
    specific_humidity_air = abiotic_tools.calculate_specific_humidity(
        air_temperature=state["air_temperature"],
        relative_humidity=state["relative_humidity"],
        atmospheric_pressure=static["atmospheric_pressure"],
        molecular_weight_ratio_water_to_dry_air=(
            core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        pyrealm_core_constants=pyrealm_core_constants,
    )

    # Add water from evapotranspiration and soil evaporation to atmosphere
    specific_humidity_with_added_water = energy_balance.update_specific_humidity(
        evapotranspiration=state["evapotranspiration"],
        soil_evaporation=state["soil_evaporation"],
        specific_humidity=specific_humidity_air,
        layer_thickness=static["geometry"]["thickness"],
        density_air=state["density_air"],
        mm_to_kg=core_constants.mm_to_kg,
        cell_area=static["cell_area"],
        time_interval=time_interval,
        surface_index=idx.surface,
    )

    # Calculate specific humidity at saturation
    mixing_ratio_saturation = (
        core_constants.molecular_weight_ratio_water_to_dry_air
        * saturated_vapour_pressure_air
        / (static["atmospheric_pressure"] - saturated_vapour_pressure_air)
    )
    max_specific_humidity = mixing_ratio_saturation / (1 + mixing_ratio_saturation)

    # Calculate mean maximum specific humidity for each cell as upper limits
    mean_max_specific_humidity = np.nanmax(max_specific_humidity[idx.atm], axis=0)

    # Vertical mixing
    specific_humidity_mixed = wind.mix_and_ventilate(
        input_variable=specific_humidity_with_added_water,
        mixing_coefficient=static["mixing_coefficient"],
        ventilation_rate=state["ventilation_rate"],
        limits=(
            abiotic_constants.min_specific_humidity,
            mean_max_specific_humidity,
        ),
        surface_index=idx.surface,
    )

    # Update atmospheric humidity variables, integration interval 1 hour
    output_vars = energy_balance.update_humidity_vpd(
        saturated_vapour_pressure=saturated_vapour_pressure_air,
        specific_humidity_mixed=specific_humidity_mixed,
        layer_thickness=static["geometry"]["thickness"],
        atmospheric_pressure=static["atmospheric_pressure"],
        density_air=state["density_air"],
        molecular_weight_ratio_water_to_dry_air=(
            core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        dry_air_factor=abiotic_constants.dry_air_factor,
        cell_area=static["cell_area"],
        limits_relative_humidity=abiotic_bounds.relative_humidity,
        limits_vapour_pressure_deficit=abiotic_bounds.vapour_pressure_deficit,
        denominator_tolerance=abiotic_constants.denominator_tolerance,
    )

    return output_vars


def run_hour_step(
    state: dict[str, Any],
    static: dict[str, Any],
    hourly_forcing: dict[str, Any],
    hour: int,
    idx: SimpleNamespace,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    pyrealm_core_constants: PyrealmCoreConst,
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
        layer_structure: LayerStructure
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        pyrealm_core_constants: Set of constants from pyrealm core that are used in
            calculations
        abiotic_bounds: Set of bounds for abiotic values
        time_interval: Time interval for flux calculations, [s]

    Returns:
        Updated state variables for the current hour
    """
    # Update forcing boundary conditions for the current hour
    update_forcing_boundary_conditions(
        state=state, hourly_forcing=hourly_forcing, hour=hour
    )

    # Update thermodynamics
    thermo = calculate_thermodynamics(
        state=state,
        static=static,
        hourly_forcing=hourly_forcing,
        hour=hour,
        n_cells=idx.cell_id,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        idx=idx,
    )
    state.update(thermo)

    # Update air temperature, canopy temperature, and fluxes
    canopy_temperature, air_temperature, canopy_fluxes = (
        energy_balance.solve_canopy_temperature_with_air_coupling(
            state=state,
            static=static,
            abiotic_constants=abiotic_constants,
            core_constants=core_constants,
            maxiter_air=abiotic_constants.maxiter_air_secant_solver,
            air_temperature_tolerance=5,
            maxiter_secant=abiotic_constants.maxiter_secant_solver,
            convergence_tolerance=abiotic_constants.convergence_tolerance_secant_solver,
            small_perturbation_second_guess=(
                abiotic_constants.small_perturbation_second_guess_secant_solver
            ),
            denominator_tolerance=abiotic_constants.denominator_tolerance,
            idx=idx,
        )
    )

    state["canopy_temperature"] = canopy_temperature
    state["air_temperature"] = air_temperature
    state.update(canopy_fluxes)

    # Calculate soil fluxes
    soil_fluxes = calculate_soil_fluxes(
        state=state,
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        time_interval=time_interval,
        idx=idx,
    )

    state["sensible_heat_flux"][idx.topsoil] = soil_fluxes["sensible_heat_flux_soil"]
    state["latent_heat_flux"][idx.topsoil] = -soil_fluxes["latent_heat_flux_soil"]
    state["longwave_emission"][idx.topsoil] = soil_fluxes["longwave_emission_soil"]
    state["net_radiation"][idx.topsoil] = soil_fluxes["net_radiation_soil"]
    state["ground_heat_flux"] = soil_fluxes["ground_heat_flux"]

    # Calculate soil temperature
    soil_temperature = energy_balance.update_soil_temperature(
        ground_heat_flux=state["ground_heat_flux"],
        soil_temperature=state["soil_temperature"][idx.soil],
        soil_layer_thickness=layer_structure.soil_layer_thickness,
        soil_thermal_conductivity=abiotic_constants.soil_thermal_conductivity,
        soil_bulk_density=abiotic_constants.bulk_density_soil,
        specific_heat_capacity_soil=abiotic_constants.specific_heat_capacity_soil,
        time_interval=core_constants.seconds_to_hour,
    )
    state["soil_temperature"][idx.soil] = soil_temperature

    # Update atmospheric humidity
    air_humidity = update_atmospheric_humidity(
        state=state,
        static=static,
        pyrealm_core_constants=pyrealm_core_constants,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        abiotic_bounds=abiotic_bounds,
        idx=idx,
        time_interval=time_interval,
    )
    state.update(air_humidity)
    return state


def build_output_from_record(
    data_record: dict[str, Any],
    static: dict[str, Any],
    layer_structure: LayerStructure,
    vars_updated: tuple[str, ...],
) -> dict[str, DataArray]:
    """Build model output from hourly record and static/state variables.

    This function also checks if variables are missing from var updated list.

    Args:
        data_record: Hourly data record
        static: Static inputs
        layer_structure: LayerStructure object
        vars_updated: Tuple containing strings of all variables that are updated by the
            abiotic model

    Returns:
        Dictionary of DataArray outputs. Raises ValueError when unsupported variable
            dimensions are provided and when requested variables could not be produced
    """

    output: dict[str, DataArray] = {}
    vars_set = set(vars_updated)

    # Static atmospheric layered variables
    atm_index = layer_structure.index_filled_atmosphere
    for name in static:
        if name not in vars_set:
            continue

        temp = layer_structure.from_template()
        temp[atm_index] = static[name][atm_index]
        output[name] = temp

    # Hourly recorded variables
    for var, values in data_record.items():
        # skip variables we don't want
        if var not in vars_set:
            continue

        values_arr = np.asarray(values)

        # detect time dimension
        if values_arr.ndim > 1:
            if var == "diurnal_temperature_range":
                air = data_record["air_temperature"]
                soil = data_record["soil_temperature"]

                combined = np.stack([air, soil], axis=0)
                min_value = np.nanmin(combined, axis=(0, 1))
                max_value = np.nanmax(combined, axis=(0, 1))
                values_out = max_value - min_value

            else:
                values_out = np.nanmean(values_arr, axis=0)

        # assign dims
        if values_out.ndim == 1:
            dims = ["cell_id"]
        elif values_out.ndim == 2:
            dims = ["layers", "cell_id"]
        else:
            raise ValueError(
                f"Unsupported dimensions for variable '{var}': {values.shape}"
            )

        output[var] = DataArray(values_out, dims=dims)

    # check for requested variables that never appeared
    missing = vars_set - output.keys()
    if missing:
        # only raise error if missing variable is not in static
        missing_not_in_static = [v for v in missing if v not in static]
        if missing_not_in_static:
            raise ValueError(
                f"Requested variables not produced: {missing_not_in_static}"
            )

    if missing:
        raise ValueError(f"Requested variables not produced: {missing}")

    return output


def run_microclimate(
    data: Data,
    vars_updated: tuple[str, ...],
    time_index: int,
    time_dim: int,
    time_interval: float,
    month: int,
    days: int,
    latitude: float,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    pyrealm_core_constants: PyrealmCoreConst,
    abiotic_bounds: AbioticSimpleBounds,
) -> dict[str, Any]:
    """Run the microclimate model for one day, iterating through hourly time steps.

    This function prepares static inputs, calculates wind profiles, generates hourly
    forcing, initializes state and record variables, and then iteratively updates the
    state variables based on calculated fluxes and thermodynamics for each hour.

    Args:
        data: Data object containing all model variables and grid information
        vars_updated: Tuple containing strings of all variables that are updated by
            abiotic model
        time_index: Time index for the current day in the data
        time_dim: Number of time steps in the hourly record (e.g., 24 for a full day)
        time_interval: Time interval for flux calculations, [s]
        month: Current month (1-12) for generating diurnal cycle
        days: Number of days per month
        latitude: Latitude of the location, [degrees]
        layer_structure: Layer structure object with information on number of layers
            and their indices
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        pyrealm_core_constants: Set of constants from pyrealm
        abiotic_bounds: Bounds for air temperature to ensure physical realism

    Returns:
        Dictionary with updated state variables and hourly record for the day
    """

    # Select indices for different layer types, shorter than layer_structure naming
    idx = abiotic_tools.build_indices(data=data, layer_structure=layer_structure)

    # Initialise state dict
    state = initialize_state(
        data=data,
    )

    # Prepare static inputs for microclimate model
    static = prepare_static_inputs(
        data=data,
        idx=idx,
        time_index=time_index,
        layer_structure=layer_structure,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
    )

    # Calculate wind profiles for microclimate model
    wind_state = calculate_wind_profiles(
        static=static,
        abiotic_constants=abiotic_constants,
        core_constants=core_constants,
        data=data,
        time_index=time_index,
        layer_structure=layer_structure,
    )
    static.update(wind_state)

    # Generate hourly forcing for microclimate model
    forcing = generate_hourly_forcing(
        data=data,
        static=static,
        time_index=time_index,
        month=month,
        days=days,
        latitude=latitude,
        abiotic_constants=abiotic_constants,
    )

    # Initialize hourly record for microclimate model
    vars_hourly_updated = tuple(v for v in vars_updated if v not in static)

    data_record = initialize_hourly_record(
        data=data,
        vars_updated=vars_hourly_updated,
        time_dim=time_dim,
        layer_structure=layer_structure,
    )

    # Update microclimate date for 24 hours (time_dim)
    for hour in range(time_dim):
        state = run_hour_step(
            state=state,
            static=static,
            hourly_forcing=forcing,
            hour=hour,
            idx=idx,
            layer_structure=layer_structure,
            abiotic_constants=abiotic_constants,
            core_constants=core_constants,
            pyrealm_core_constants=pyrealm_core_constants,
            time_interval=time_interval,
            abiotic_bounds=abiotic_bounds,
        )

        # Check that all vars are updated
        abiotic_tools.validate_variables(
            names=vars_hourly_updated,
            values=state,
            exclude={  # These intermediate variables are already in data or merged
                "aerodynamic_resistance_soil",
                "energy_balance_residual",
                "evapotranspiration",
                "shortwave_absorption",
                "soil_evaporation",
                "specific_humidity",
                "ventilation_rate",
                "diurnal_temperature_range",
            },
        )

        # Record this hour
        abiotic_tools.record_hourly_output(
            hour=hour,
            data_record=data_record,
            hourly_values=state,
        )

    output = build_output_from_record(
        data_record=data_record,
        static=static,
        layer_structure=layer_structure,
        vars_updated=vars_updated,
    )
    output["latent_heat_vapourisation"] /= 1000.0

    return output
