"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

from types import SimpleNamespace

import numpy as np
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calc_specific_heat, calc_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic import abiotic_tools, energy_balance, wind
from virtual_ecosystem.models.abiotic.energy_balance import (
    calculate_conductive_flux_understorey,
)
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants
from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


def run_microclimate(
    data: Data,
    vars_updated: tuple[str, ...],
    time_index: int,
    time_interval: float,
    month: int,
    cell_area: float,
    latitude: float,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    pyrealm_core_constants: PyrealmCoreConst,
    abiotic_bounds: AbioticSimpleBounds,
) -> dict[str, DataArray]:
    """Run microclimate model.

    This function updates air, soil, understorey, and canopy temperatures by calculating
    the radiation and energy balance for each layer. We currently make the assumption
    that over the time interval of one month, different compartments are in equilibrium.
    For numerical stability, the integration interval is 1 hour.

    The understorey layer is treated as a separate vegetation layer with its own
    radiation and energy balance. The implementation is based
    on a forest floor model for heat and moisture including a litter layer by
    :cite:t:`ogee_a_forest_2002`.

    ..TODO: Temperatures change between Kelvin and Celsius due to a mix of references,
    needs to be revisited and converted properly.


    Args:
        data: Data object
        vars_updated: Tuple containing strings of all variables that are updated by the
            abiotic model
        time_index: Time index
        time_interval: Time interval, [s]
        month: Current month (1-12)
        cell_area: Cell area, [m2]
        latitude: Latitude of the location, [degrees]
        layer_structure: Layer structure object
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        pyrealm_core_constants: Set of core constants for pyrealm
        abiotic_bounds: Bounds for vertical mixing of atmospheric variables

    Returns:
        dictionary with updated microclimate variables
    """

    output: dict[str, DataArray] = {}

    idx = SimpleNamespace(
        above=layer_structure.index_above,
        canopy=layer_structure.index_filled_canopy,
        surface=layer_structure.index_surface_scalar,
        atm=layer_structure.index_filled_atmosphere,
        flux=layer_structure.index_flux_layers,
        soil=layer_structure.index_all_soil,
        topsoil=layer_structure.index_topsoil_scalar,
        layers=layer_structure.n_layers,
        cell_id=data.grid.n_cells,
    )

    # -------------------------------------------------------------------------
    # Geometry and static profiles
    # -------------------------------------------------------------------------

    # NOTE Canopy height will likely become a separate variable, update as required
    canopy_height = data["layer_heights"][1].to_numpy()

    # LAI sum over all canopy layers only for wind profile, NOT understorey layer
    leaf_area_index_sum = np.nansum(
        data["leaf_area_index"][idx.canopy].to_numpy(), axis=0
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

    # Calculate atmospheric layer geometry
    atmospheric_layer_geometry = abiotic_tools.calculate_atmospheric_layer_geometry(
        data=data,
        layer_structure=layer_structure,
    )

    # Effective heat capacity of understorey vegetation, [J m-2 K-1]
    effective_heat_capacity_understorey = (
        energy_balance.calculate_understorey_effective_heat_capacity(
            layer_thickness=atmospheric_layer_geometry["thickness"][-1],
            leaf_area_index=data["leaf_area_index"][idx.surface].to_numpy(),
            leaf_mass_per_area=abiotic_constants.leaf_mass_per_area_understorey,
            leaf_specific_heat=abiotic_constants.specific_heat_capacity_understorey,
            air_volumetric_heat_capacity=core_constants.air_volumetric_heat_capacity,
        )
    )

    # -------------------------------------------------------------------------
    # Wind profiles
    # -------------------------------------------------------------------------

    #   Zero plane displacement height, [m]
    zero_plane_displacement = wind.calculate_zero_plane_displacement(
        canopy_height=canopy_height,
        leaf_area_index=leaf_area_index_sum,
        zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
    )

    #   Roughness length for momentum, [m]
    roughness_length = wind.calculate_roughness_length_momentum(
        canopy_height=canopy_height,
        leaf_area_index=leaf_area_index_sum,
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
    wind_reference_height = canopy_height + abiotic_constants.wind_reference_height
    reference_wind_speed = data["wind_speed_ref"].isel(time_index=time_index).to_numpy()

    wind_profile = wind.calculate_wind_profile(
        reference_wind_speed=reference_wind_speed,
        reference_height=wind_reference_height,
        wind_heights=atmospheric_layer_geometry["heights"],
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
        layer_midpoints=atmospheric_layer_geometry["layer_midpoints"],
        canopy_height=canopy_height,
        friction_velocity=friction_velocity,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    # -------------------------------------------------------------------------
    # Diurnal forcing
    # -------------------------------------------------------------------------

    # Generate hourly profiles for atmospheric forcing variables
    hourly_forcing = abiotic_tools.generate_diurnal_cycle_from_monthly_data(
        monthly_air_temperature=data["air_temperature_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        monthly_shortwave_absorption=data["shortwave_absorption"].to_numpy(),
        monthly_relative_humidity=data["relative_humidity_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        monthly_evapotranspiration=evapotranspiration,
        monthly_soil_evaporation=data["soil_evaporation"].to_numpy(),
        latitude_deg=latitude,
        month=month,
        daily_temp_amplitude=5,  # TODO abiotic_constants or input data
    )

    # -------------------------------------------------------------------------
    # Initialise state variables
    # -------------------------------------------------------------------------

    all_air_temperature = data["air_temperature"][idx.atm].to_numpy()
    canopy_air_temperature = data["air_temperature"][idx.canopy].to_numpy()
    surface_air_temperature = data["air_temperature"][idx.surface].to_numpy()

    canopy_temperature = data["canopy_temperature"][idx.canopy].to_numpy()
    understorey_temperature = data["canopy_temperature"][idx.surface].to_numpy()
    soil_temperature = data["soil_temperature"][idx.soil].to_numpy()

    relative_humidity = data["relative_humidity"][idx.atm].to_numpy()
    downward_longwave_radiation = (
        data["downward_longwave_radiation"].isel(time_index=time_index).to_numpy()
    )
    # TODO get correct timestep/nighttime value, might require moving around
    conductive_flux_understorey = np.repeat(0, idx.cell_id)
    sensible_heat_flux_soil = np.repeat(0, idx.cell_id)

    # -------------------------------------------------------------------------
    # Hourly record arrays
    # -------------------------------------------------------------------------

    variables = {name: data[name] for name in vars_updated}
    data_record = abiotic_tools.initialize_data_record(
        variables=variables,
        time_dim=24,
        layers=layer_structure.n_layers,
        cell_ids=data.grid.n_cells,
    )

    # -----------------------------------------------------------------------------
    # Hourly loop
    # -----------------------------------------------------------------------------

    for hour in range(24):
        # Define daytime hours
        shortwave_day = hourly_forcing["shortwave_absorption_hourly"][hour, :, :]
        is_day = np.nan_to_num(shortwave_day, nan=0.0).any() > 0

        # Replace atmospheric air temperature and humidity above canopy, [C]
        all_air_temperature[0] = hourly_forcing["air_temperature_hourly"][hour, :]
        relative_humidity[0] = hourly_forcing["relative_humidity_hourly"][hour, :]

        # Select shortwave absorption profiles, [W m-2]
        shortwave_absorption_canopy = hourly_forcing["shortwave_absorption_hourly"][
            hour, idx.canopy, :
        ]
        shortwave_absorption_understorey = hourly_forcing[
            "shortwave_absorption_hourly"
        ][hour, idx.surface, :]
        shortwave_absorption_soil = hourly_forcing["shortwave_absorption_hourly"][
            hour, layer_structure.index_topsoil_scalar, :
        ]

        # Select evapotranspiration and soil evaporation, [mm per hour]
        evapotranspiration_canopy = hourly_forcing["evapotranspiration_hourly"][
            hour, idx.canopy, :
        ]
        evapotranspiration_understorey = hourly_forcing["evapotranspiration_hourly"][
            hour, idx.surface, :
        ]
        soil_evaporation = hourly_forcing["soil_evaporation_hourly"][hour, :]

        # -------------------------------------------------------------------------
        #  Thermodynamics
        # -------------------------------------------------------------------------

        # Density of air, [kg m-3]
        density_air = abiotic_tools.calculate_air_density(
            air_temperature=all_air_temperature,
            atmospheric_pressure=atmospheric_pressure_true,
            specific_gas_constant_dry_air=core_constants.specific_gas_constant_dry_air,
            celsius_to_kelvin=core_constants.zero_Celsius,
        )

        # Specific heat capacity of air, [J kg-1 K-1]
        specific_heat_air = calc_specific_heat(
            tc=all_air_temperature,
        )

        #   Latent heat of vapourisation, [kJ kg-1]
        latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
            temperature=all_air_temperature,
            celsius_to_kelvin=core_constants.zero_Celsius,
            latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
        )
        latent_heat_vapourisation_j = latent_heat_vapourisation * 1000  # [J kg-1]

        # Aerodynamic resistances for day and nighttime, [s m-1]
        if is_day:
            aerodynamic_resistance_canopy = np.repeat(
                abiotic_constants.aerodynamic_resistance_canopy_day, data.grid.n_cells
            )
            aerodynamic_resistance_soil = data["aerodynamic_resistance_soil"].to_numpy()

        else:
            aerodynamic_resistance_canopy = np.repeat(
                abiotic_constants.aerodynamic_resistance_canopy_night, data.grid.n_cells
            )
            aerodynamic_resistance_soil = np.repeat(
                abiotic_constants.aerodynamic_resistance_soil_night, data.grid.n_cells
            )

        #  Ventilation rate above canopy, [s-1]
        ventilation_rate = wind.calculate_ventilation_rate(
            aerodynamic_resistance=aerodynamic_resistance_canopy,
            characteristic_height=canopy_height + zero_plane_displacement,
        )

        # -------------------------------------------------------------------------
        # Radiation balance
        # -------------------------------------------------------------------------

        # Longwave emission [W m-2]
        longwave_emission_understorey = energy_balance.calculate_longwave_emission(
            temperature=understorey_temperature + core_constants.zero_Celsius,
            emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann=core_constants.stefan_boltzmann_constant,
        )

        longwave_emission_soil = energy_balance.calculate_longwave_emission(
            temperature=soil_temperature[0] + core_constants.zero_Celsius,
            emissivity=abiotic_constants.soil_emissivity,
            stefan_boltzmann=core_constants.stefan_boltzmann_constant,
        )

        longwave_emission_canopy = energy_balance.calculate_longwave_emission(
            temperature=canopy_temperature + core_constants.zero_Celsius,
            emissivity=abiotic_constants.soil_emissivity,
            stefan_boltzmann=core_constants.stefan_boltzmann_constant,
        )

        # Net radiation, [W m-2]
        net_radiation_canopy = (
            shortwave_absorption_canopy
            - longwave_emission_canopy
            + downward_longwave_radiation
            + 0.5 * (longwave_emission_understorey * abiotic_constants.leaf_emissivity)
        )

        net_radiation_understorey = (
            shortwave_absorption_understorey
            - longwave_emission_understorey
            + 0.5
            * (
                np.nanmean(longwave_emission_canopy, axis=0)
                * abiotic_constants.leaf_emissivity
            )
            + longwave_emission_soil
        )

        net_radiation_soil = (
            shortwave_absorption_soil
            + 0.5 * (longwave_emission_understorey * abiotic_constants.leaf_emissivity)
            - longwave_emission_soil
        )

        # -------------------------------------------------------------------------
        # Canopy energy balance
        # -------------------------------------------------------------------------

        # Solve energy balance for canopy temperature, [C]
        canopy_temperature = energy_balance.solve_canopy_temperature(
            canopy_temperature_initial=canopy_temperature,
            air_temperature=canopy_air_temperature,
            evapotranspiration=evapotranspiration_canopy,
            absorbed_shortwave_radiation=shortwave_absorption_canopy,
            absorbed_longwave_radiation=downward_longwave_radiation
            + 0.5 * (longwave_emission_understorey * abiotic_constants.leaf_emissivity),
            specific_heat_air=specific_heat_air[1:-1],
            density_air=density_air[1:-1],
            aerodynamic_resistance=aerodynamic_resistance_canopy,
            latent_heat_vapourisation=latent_heat_vapourisation_j[1:-1],
            emissivity_leaf=abiotic_constants.leaf_emissivity,
            stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            zero_Celsius=core_constants.zero_Celsius,
            seconds_to_hour=core_constants.seconds_to_hour,
            return_fluxes=False,
            maxiter=10000,
        )

        # Calculate new energy balance and return all fluxes, [W m-2]
        energy_balance_canopy = energy_balance.calculate_energy_balance_residual(
            canopy_temperature_initial=canopy_temperature,
            air_temperature=canopy_air_temperature,
            evapotranspiration=evapotranspiration_canopy,
            absorbed_shortwave_radiation=shortwave_absorption_canopy,
            absorbed_longwave_radiation=downward_longwave_radiation
            + 0.5 * (longwave_emission_understorey * abiotic_constants.leaf_emissivity),
            leaf_emissivity=abiotic_constants.leaf_emissivity,
            specific_heat_air=specific_heat_air[1:-1],
            density_air=density_air[1:-1],
            aerodynamic_resistance=aerodynamic_resistance_canopy,
            latent_heat_vapourisation=latent_heat_vapourisation_j[1:-1],
            stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            zero_Celsius=core_constants.zero_Celsius,
            seconds_to_hour=core_constants.seconds_to_hour,
            return_fluxes=True,
        )

        if not isinstance(energy_balance_canopy, dict):
            to_raise = ValueError("The energy balance has not returned any fluxes!")
            LOGGER.error(to_raise)
            raise to_raise

        longwave_emission_canopy = energy_balance_canopy["longwave_emission_canopy"]
        latent_heat_flux_canopy = energy_balance_canopy["latent_heat_flux_canopy"]
        sensible_heat_flux_canopy = energy_balance_canopy["sensible_heat_flux_canopy"]

        # Update canopy air temperatures, [C], # TODO integration interval 1 hour
        canopy_air_temperature = energy_balance.update_air_temperature(
            air_temperature=canopy_air_temperature,
            sensible_heat_flux=sensible_heat_flux_canopy,
            specific_heat_air=specific_heat_air[1:-1],
            density_air=density_air[1:-1],
            mixing_layer_thickness=atmospheric_layer_geometry["thickness"][1:-1],
        )

        # -------------------------------------------------------------------------
        # Understorey energy balance
        # -------------------------------------------------------------------------

        #  Sensible heat flux from understorey vegetation, [W m-2]
        sensible_heat_flux_understorey = energy_balance.calculate_sensible_heat_flux(
            density_air=density_air[-1],
            specific_heat_air=specific_heat_air[-1],
            air_temperature=surface_air_temperature,
            surface_temperature=understorey_temperature,
            aerodynamic_resistance=aerodynamic_resistance_canopy,
        )

        # Latent heat flux understorey vegetation, [W m-2]
        latent_heat_flux_understorey = energy_balance.calculate_latent_heat_flux(
            evapotranspiration=evapotranspiration_understorey,
            latent_heat_vapourisation=latent_heat_vapourisation_j[-1],
            time_interval=time_interval,
        )

        # Conductive flux from understorey vegetation to soil, [W m-2]
        # A positive flux is directed towards the soil
        conductive_flux_understorey = calculate_conductive_flux_understorey(
            soil_temperature=soil_temperature[0],
            understorey_temperature=understorey_temperature,
            understorey_layer_thickness=atmospheric_layer_geometry["heights"][-1],
            soil_thermal_conductivity=abiotic_constants.soil_thermal_conductivity,
            understorey_thermal_conductivity=abiotic_constants.understorey_thermal_conductivity,
        )

        # Update understory vegetation temperatures, [C]

        understorey_temperature = energy_balance.update_understorey_temperature(
            current_temperature=understorey_temperature,
            net_radiation=net_radiation_understorey,
            sensible_heat_flux=sensible_heat_flux_understorey,
            conductive_flux=-conductive_flux_understorey,
            effective_heat_capacity=effective_heat_capacity_understorey,
            time_step_seconds=1.0,  # TODO core_constants.seconds_to_hour,
            latent_heat_flux=latent_heat_flux_understorey,
            max_delta_temperature=10.0,  # TODO add to constants
        )

        # -------------------------------------------------------------------------
        # Soil energy balance
        # -------------------------------------------------------------------------

        #  Sensible heat flux from topsoil, [W m-2]
        sensible_heat_flux_soil = energy_balance.calculate_sensible_heat_flux(
            density_air=density_air[-1],
            specific_heat_air=specific_heat_air[-1],
            air_temperature=surface_air_temperature,
            surface_temperature=soil_temperature[0],
            aerodynamic_resistance=aerodynamic_resistance_soil,
        )

        # Latent heat flux topsoil, [W m-2]
        latent_heat_flux_soil = energy_balance.calculate_latent_heat_flux(
            evapotranspiration=soil_evaporation,
            latent_heat_vapourisation=latent_heat_vapourisation_j[-1],
            time_interval=time_interval,
        )

        # Ground heat flux, [W m-2]
        # Note the convention is that latent and sensible heat fluxes are negative when
        # directed away from the surface, hence added here
        ground_heat_flux = (
            net_radiation_soil - latent_heat_flux_soil - sensible_heat_flux_soil
            # + conductive_flux_understorey # TODO causes ridiculous values
        )

        # Update soil temperatures, [C], integration interval 1 hour
        # TODO Revisit implementation of soil temperature update, Newton or force-store
        # TODO Soil parameter currently constants, replace with soil maps
        # TODO include effect of soil moisture
        soil_temperature = energy_balance.update_soil_temperature(
            ground_heat_flux=ground_heat_flux,
            soil_temperature=soil_temperature,
            soil_layer_thickness=layer_structure.soil_layer_thickness,
            soil_thermal_conductivity=abiotic_constants.soil_thermal_conductivity,
            soil_bulk_density=abiotic_constants.bulk_density_soil,
            specific_heat_capacity_soil=abiotic_constants.specific_heat_capacity_soil,
            time_interval=core_constants.seconds_to_hour,
        )

        # Update surface air temperatures, [C], TODO integration interval 1 hour
        surface_air_temperature = energy_balance.update_air_temperature(
            air_temperature=surface_air_temperature,
            sensible_heat_flux=sensible_heat_flux_understorey + sensible_heat_flux_soil,
            specific_heat_air=specific_heat_air[-1],
            density_air=density_air[-1],
            mixing_layer_thickness=atmospheric_layer_geometry["thickness"][-1],
        )

        # Update all air temperatures, [C]
        all_air_temperature[1 : len(canopy_temperature) + 1] = canopy_air_temperature
        all_air_temperature[-1] = surface_air_temperature

        all_air_temperature = wind.mix_and_ventilate(
            input_variable=all_air_temperature,
            ventilation_rate=ventilation_rate,
            mixing_coefficient=mixing_coefficient,
            limits=abiotic_bounds.air_temperature[:2],
        )

        # NOTE Advection not implemented as everything is removed with time interval>=1h
        # and horizontal transfer is not implemented
        # advection_rate = (
        #   data["wind_speed_ref"].isel(time_index=time_index).to_numpy()
        #   / np.sqrt(cell_area)
        # )
        # advected_fraction = np.clip(advection_rate * time_interval, 0, 1)
        # all_air_temperature[0] -=all_air_temperature[0] *advected_fraction

        # Update atmospheric humidity/VPD
        # Saturated vapour pressure of air, [kPa]
        saturated_vapour_pressure_air = calc_vp_sat(
            ta=all_air_temperature,
            core_const=pyrealm_core_constants,
        )

        # Specific humidity of air, [kg kg-1]
        specific_humidity_air = abiotic_tools.calculate_specific_humidity(
            air_temperature=all_air_temperature,
            relative_humidity=relative_humidity,
            atmospheric_pressure=atmospheric_pressure_true,
            molecular_weight_ratio_water_to_dry_air=(
                core_constants.molecular_weight_ratio_water_to_dry_air
            ),
            pyrealm_core_constants=pyrealm_core_constants,
        )

        # Calculate specific humidity at saturation
        mixing_ratio_saturation = (
            core_constants.molecular_weight_ratio_water_to_dry_air
            * saturated_vapour_pressure_air
            / (atmospheric_pressure_true - saturated_vapour_pressure_air)
        )
        max_specific_humidity = mixing_ratio_saturation / (1 + mixing_ratio_saturation)

        # Update atmospheric humidity variables, integration interval 1 hour
        new_atmospheric_humidity_vars = energy_balance.update_humidity_vpd(
            canopy_evapotranspiration=evapotranspiration_canopy,
            understorey_evapotranspiration=evapotranspiration_understorey,
            soil_evaporation=soil_evaporation,
            saturated_vapour_pressure=saturated_vapour_pressure_air,
            specific_humidity=specific_humidity_air,
            layer_thickness=atmospheric_layer_geometry["thickness"],
            atmospheric_pressure=atmospheric_pressure_true,
            density_air=density_air,
            mixing_coefficient=mixing_coefficient,
            ventilation_rate=ventilation_rate,
            molecular_weight_ratio_water_to_dry_air=(
                core_constants.molecular_weight_ratio_water_to_dry_air
            ),
            dry_air_factor=abiotic_constants.dry_air_factor,
            cell_area=cell_area,
            limits=(0, max_specific_humidity[0]),  # TODO make layer specific
            time_interval=core_constants.seconds_to_hour,
        )
        relative_humidity = new_atmospheric_humidity_vars["relative_humidity"]

        # Record data
        hourly_values = {
            # 1D arrays
            "ground_heat_flux": ground_heat_flux,
            "conductive_flux_understorey": conductive_flux_understorey,
            "aerodynamic_resistance_canopy": aerodynamic_resistance_canopy,
            # 2D layered arrays
            "longwave_emission": [
                (idx.canopy, longwave_emission_canopy),
                (idx.surface, longwave_emission_understorey),
                (idx.topsoil, longwave_emission_soil),
            ],
            "net_radiation": [
                (idx.canopy, net_radiation_canopy),
                (idx.surface, net_radiation_understorey),
                (idx.topsoil, net_radiation_soil),
            ],
            "sensible_heat_flux": [
                (idx.canopy, sensible_heat_flux_canopy),
                (idx.surface, sensible_heat_flux_understorey),
                (idx.topsoil, sensible_heat_flux_soil),
            ],
            "latent_heat_flux": [
                (idx.canopy, latent_heat_flux_canopy),
                (idx.surface, latent_heat_flux_understorey),
                (idx.topsoil, latent_heat_flux_soil),
            ],
            "soil_temperature": [
                (idx.soil, soil_temperature),
            ],
            "air_temperature": [
                (idx.above, all_air_temperature[0]),
                (idx.canopy, canopy_air_temperature),
                (idx.surface, surface_air_temperature),
            ],
            "latent_heat_vapourisation": [
                (idx.atm, latent_heat_vapourisation),
            ],
            "relative_humidity": [
                (idx.atm, new_atmospheric_humidity_vars["relative_humidity"]),
            ],
            "vapour_pressure_deficit": [
                (idx.atm, new_atmospheric_humidity_vars["vapour_pressure_deficit"]),
            ],
            "canopy_temperature": [
                (idx.canopy, canopy_temperature),
                (idx.surface, understorey_temperature),
            ],
        }

        # Check that all vars are updated
        abiotic_tools.validate_variables(
            names=vars_updated,
            values=hourly_values,
            exclude=("density_air", "specific_heat_air", "wind_speed"),
        )

        # Record this hour
        abiotic_tools.record_hourly_output(
            hour=hour,
            data_record=data_record,
            layer_structure=layer_structure,
            hourly_values=hourly_values,
        )

    # End of loop

    # Write in output dictionary

    # Static atmospheric variables
    output["atmospheric_pressure"] = atmospheric_pressure
    output["atmospheric_co2"] = atmospheric_co2

    # 1D arrays
    one_d_vars = [
        "ground_heat_flux",
        "conductive_flux_understorey",
        "aerodynamic_resistance_canopy",
    ]
    for var in one_d_vars:
        output[var] = DataArray(np.nanmean(data_record[var], axis=0), dims="cell_id")

    # 2d arrays
    two_d_atm_vars_static = ["density_air", "specific_heat_air", "wind_speed"]
    two_d_atm_vars_static_data = [wind_profile, specific_heat_air, density_air]
    for var_name, var_value in zip(two_d_atm_vars_static, two_d_atm_vars_static_data):
        temp_array = layer_structure.from_template()
        temp_array[idx.atm] = var_value
        output[var_name] = temp_array

    two_d_atm_vars = [
        "latent_heat_vapourisation",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
    ]
    for var in two_d_atm_vars:
        output[var] = abiotic_tools.mean_to_layers(
            var=var,
            index=idx.atm,
            data_record=data_record,
            layer_structure=layer_structure,
        )

    two_d_soil_vars = ["soil_temperature"]
    for var in two_d_soil_vars:
        output[var] = abiotic_tools.mean_to_layers(
            var=var,
            index=idx.soil,
            data_record=data_record,
            layer_structure=layer_structure,
        )

    two_d_flux_vars = [
        "longwave_emission",
        "net_radiation",
        "sensible_heat_flux",
        "latent_heat_flux",
    ]
    for var in two_d_flux_vars:
        output[var] = abiotic_tools.mean_to_layers(
            var=var,
            index=idx.flux,
            data_record=data_record,
            layer_structure=layer_structure,
        )

    canopy_temperature_out = layer_structure.from_template()
    mean_vals = np.nanmean(data_record["canopy_temperature"], axis=0)
    canopy_temperature_out[idx.canopy] = mean_vals[idx.canopy]
    canopy_temperature_out[idx.surface] = mean_vals[idx.surface]
    output["canopy_temperature"] = canopy_temperature_out

    return output
