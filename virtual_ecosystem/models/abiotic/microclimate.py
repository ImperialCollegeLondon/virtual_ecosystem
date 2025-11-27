"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

import numpy as np
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calc_specific_heat, calc_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic import abiotic_tools, energy_balance, wind
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants
from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds


def run_microclimate(
    data: Data,
    time_index: int,
    time_interval: float,
    cell_area: float,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    pyrealm_core_constants: PyrealmCoreConst,
    abiotic_bounds: AbioticSimpleBounds,
) -> dict[str, DataArray]:
    """Run microclimate model.

    This function updates air, soil and canopy temperatures by calculating
    the energy balance for each layer. We currently make the assumption that over the
    time interval of one month, different compartments are in equilibrium. For numerical
    stability, the integration interval is 1 hour.

    ..TODO: Temperatures change between Kelvin and Celsius due to a mix of references,
    needs to be revisited and converted properly.


    Args:
        data: Data object
        time_index: Time index
        time_interval: Time interval, [s]
        cell_area: Cell area, [m2]
        layer_structure: Layer structure object
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models
        pyrealm_core_constants: Set of core constants for pyrealm
        abiotic_bounds: Bounds for vertical mixing of atmospheric variables

    Returns:
        dictionary with updated microclimate variables
    """

    output = {}

    # Precompute reusable quantities

    # NOTE Canopy height will likely become a separate variable, update as required
    canopy_height = data["layer_heights"][1].to_numpy()
    # NOTE currently sums LAI over all canopy layers, not surface grass layer
    leaf_area_index_sum = np.nansum(
        data["leaf_area_index"][layer_structure.index_filled_canopy].to_numpy(), axis=0
    )

    atmospheric_pressure_out = layer_structure.from_template()
    atmospheric_pressure_out[layer_structure.index_filled_atmosphere] = data[
        "atmospheric_pressure_ref"
    ].isel(time_index=time_index)
    atmospheric_pressure = atmospheric_pressure_out[
        layer_structure.index_filled_atmosphere
    ].to_numpy()

    wind_reference_height = canopy_height + abiotic_constants.wind_reference_height
    wind_heights = data["layer_heights"][
        layer_structure.index_filled_atmosphere
    ].to_numpy()

    # Calculate thickness of above ground layers and midpoints
    above_ground_layer_thickness = (
        abiotic_tools.compute_layer_thickness_for_varying_canopy(heights=wind_heights)
    )

    # Compute cumulative thickness excluding the current layer (layer tops)
    layer_top = (
        np.cumsum(above_ground_layer_thickness, axis=1) - above_ground_layer_thickness
    )

    # Compute midpoints
    layer_midpoints = layer_top + above_ground_layer_thickness / 2

    # -------------------------------------------------------------------------
    # Wind profiles and resistances
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
    wind_profile = wind.calculate_wind_profile(
        reference_wind_speed=data["wind_speed_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        reference_height=wind_reference_height,
        wind_heights=wind_heights,
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        min_wind_speed=abiotic_constants.min_windspeed_below_canopy,
    )

    #   Friction velocity, [m s-1]
    friction_velocity = wind.calculate_friction_velocity(
        reference_wind_speed=data["wind_speed_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        reference_height=(
            data["layer_heights"][0].to_numpy()
            + abiotic_constants.wind_reference_height
        ),
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    # Aerodynamic resistance canopy, [s m-1]
    # TODO Revisit when model produces realistic forest structure and/or calibrate
    # default value.
    # Very high r_a (>1000 s/m) breaks Newton method, but physically possible when:
    #    - LAI is small
    #    - wind speed is very low (u < 0.5 m/s)
    #    - roughness length is small (z0 < 0.01 m)
    #
    # aerodynamic_resistance_canopy = wind.calculate_aerodynamic_resistance(
    #     wind_heights=canopy_height,
    #     roughness_length=roughness_length,
    #     zero_plane_displacement=zero_plane_displacement,
    #     wind_speed=wind_profile[1],
    #     von_karman_constant=core_constants.von_karmans_constant,
    # )
    aerodynamic_resistance_canopy = np.repeat(
        abiotic_constants.aerodynamic_resistance_canopy_default, data.grid.n_cells
    )

    output["aerodynamic_resistance_canopy"] = DataArray(
        aerodynamic_resistance_canopy, dims="cell_id"
    )

    # Aerodynamic resistance soil, [s m-1]
    aerodynamic_resistance_soil = data["aerodynamic_resistance_surface"].to_numpy()

    # Turbulent mixing coefficient above canopy, [m2 s-1]
    mixing_coefficient = wind.calculate_mixing_coefficients_canopy(
        layer_midpoints=layer_midpoints,
        canopy_height=canopy_height,
        friction_velocity=friction_velocity,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    #  Ventilation rate above canopy, [s-1]
    ventilation_rate = wind.calculate_ventilation_rate(
        aerodynamic_resistance=aerodynamic_resistance_canopy,
        characteristic_height=canopy_height + zero_plane_displacement,
    )

    # -------------------------------------------------------------------------
    # Initialise temperatures and humidity profiles
    # -------------------------------------------------------------------------

    all_air_temperature = data["air_temperature"][
        layer_structure.index_filled_atmosphere
    ].to_numpy()
    air_temperature_canopy = data["air_temperature"][
        layer_structure.index_filled_canopy
    ].to_numpy()
    surface_air_temperature = data["air_temperature"][
        layer_structure.index_surface_scalar
    ].to_numpy()
    canopy_temperature = data["canopy_temperature"][
        layer_structure.index_filled_canopy
    ].to_numpy()
    soil_temperature = data["soil_temperature"][
        layer_structure.index_all_soil
    ].to_numpy()
    relative_humidity = data["relative_humidity"][
        layer_structure.index_filled_atmosphere
    ].to_numpy()

    # Evapotranspiration from plant and hydrology model, per time interval
    evapotranspiration = data["canopy_evaporation"] + data["transpiration"]

    # -------------------------------------------------------------------------
    #  Calculate atmospheric background variables
    # -------------------------------------------------------------------------
    # Density of air, [kg m-3]
    density_air = abiotic_tools.calculate_air_density(
        air_temperature=all_air_temperature,
        atmospheric_pressure=atmospheric_pressure,
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

    # -------------------------------------------------------------------------
    # Soil energy balance
    # -------------------------------------------------------------------------
    # Longwave emission from soil, [W m-2]
    longwave_emission_soil = energy_balance.calculate_longwave_emission(
        temperature=soil_temperature[0] + core_constants.zero_Celsius,
        emissivity=abiotic_constants.soil_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Net radiation topsoil, shortwave in - longwave out, [W m-2]
    net_radiation_soil = (
        data["shortwave_absorption"][layer_structure.index_topsoil_scalar].to_numpy()
        - longwave_emission_soil
    )

    #  Sensible heat flux from topsoil, [W m-2]
    sensible_heat_flux_soil = energy_balance.calculate_sensible_heat_flux(
        density_air=density_air[-1],
        specific_heat_air=specific_heat_air[-1],
        air_temperature=surface_air_temperature,
        surface_temperature=soil_temperature[0],
        aerodynamic_resistance=aerodynamic_resistance_soil,
    )

    # Latent heat flux topsoil, [W m-2]
    latent_heat_flux_soil = (
        data["soil_evaporation"].to_numpy() * latent_heat_vapourisation[-1] * 1000
    ) / time_interval

    # Ground heat flux, [W m-2]
    # Note the convention is that latent and sensible heat fluxes are negative when
    # directed away from the surface, hence added here
    ground_heat_flux = (
        net_radiation_soil + latent_heat_flux_soil + sensible_heat_flux_soil
    )

    # Update soil temperatures, [C], integration interval 1 hour
    # TODO Revisit implementation of soil temperature update, consider Newton
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

    # -------------------------------------------------------------------------
    # Update canopy and air temperatures using the Newton method
    # -------------------------------------------------------------------------

    # Solve energy balance for canopy temperature, [C], integration interval 1 hour
    canopy_temperature = energy_balance.solve_canopy_temperature(
        canopy_temperature_initial=canopy_temperature,
        air_temperature=air_temperature_canopy,
        evapotranspiration=evapotranspiration[
            layer_structure.index_filled_canopy
        ].to_numpy()
        / (time_interval * core_constants.seconds_to_hour),
        absorbed_radiation_canopy=data["shortwave_absorption"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        specific_heat_air=specific_heat_air[1:-1],
        density_air=density_air[1:-1],
        aerodynamic_resistance=aerodynamic_resistance_canopy,
        latent_heat_vapourisation=latent_heat_vapourisation[1:-1] * 1000,
        emissivity_leaf=abiotic_constants.leaf_emissivity,
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
        seconds_to_hour=core_constants.seconds_to_hour,
        return_fluxes=False,
        maxiter=10000,
    )

    # Update air temperature based on new canopy and soil temperatures, [C]
    air_temperature_canopy = energy_balance.update_air_temperature(
        air_temperature=air_temperature_canopy,
        surface_temperature=canopy_temperature,
        specific_heat_air=specific_heat_air[1:-1],
        density_air=density_air[1:-1],
        aerodynamic_resistance=aerodynamic_resistance_canopy,
        mixing_layer_thickness=above_ground_layer_thickness[1:-1],
    )

    surface_air_temperature = energy_balance.update_air_temperature(
        air_temperature=surface_air_temperature,
        surface_temperature=soil_temperature[0],
        specific_heat_air=specific_heat_air[-1],
        density_air=density_air[-1],
        aerodynamic_resistance=aerodynamic_resistance_soil,
        mixing_layer_thickness=above_ground_layer_thickness[-1],
    )

    all_air_temperature[1 : len(canopy_temperature) + 1] = air_temperature_canopy
    all_air_temperature[-1] = surface_air_temperature

    all_air_temperature = wind.mix_and_ventilate(
        input_variable=all_air_temperature,
        layer_thickness=above_ground_layer_thickness,
        ventilation_rate=ventilation_rate,
        mixing_coefficient=mixing_coefficient,
        limits=abiotic_bounds.air_temperature[:2],
        time_interval=core_constants.seconds_to_hour,
    )

    # NOTE Advection not implemented as everything is removed with time interval>1h
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
        atmospheric_pressure=atmospheric_pressure,
        molecular_weight_ratio_water_to_dry_air=(
            core_constants.molecular_weight_ratio_water_to_dry_air
        ),
        pyrealm_core_constants=pyrealm_core_constants,
    )

    # Calculate specific humidity at saturation
    mixing_ratio_saturation = (
        core_constants.molecular_weight_ratio_water_to_dry_air
        * saturated_vapour_pressure_air
        / (atmospheric_pressure - saturated_vapour_pressure_air)
    )
    max_specific_humidity = mixing_ratio_saturation / (1 + mixing_ratio_saturation)

    # Update atmospheric humidity variables, integration interval 1 hour
    new_atmospheric_humidity_vars = energy_balance.update_humidity_vpd(
        evapotranspiration=evapotranspiration[
            layer_structure.index_filled_canopy
        ].to_numpy()
        / (time_interval * core_constants.seconds_to_hour),
        soil_evaporation=data["soil_evaporation"].to_numpy()
        / (time_interval * core_constants.seconds_to_hour),
        saturated_vapour_pressure=saturated_vapour_pressure_air,
        specific_humidity=specific_humidity_air,
        layer_thickness=above_ground_layer_thickness,
        atmospheric_pressure=atmospheric_pressure,
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

    # Calculate new energy balance and return all fluxes, [W m-2]
    new_energy_balance_canopy = energy_balance.calculate_energy_balance_residual(
        canopy_temperature_initial=canopy_temperature,
        air_temperature=air_temperature_canopy,
        evapotranspiration=evapotranspiration[
            layer_structure.index_filled_canopy
        ].to_numpy()
        / (time_interval * core_constants.seconds_to_hour),
        absorbed_radiation_canopy=data["shortwave_absorption"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        leaf_emissivity=abiotic_constants.leaf_emissivity,
        specific_heat_air=specific_heat_air[1:-1],
        density_air=density_air[1:-1],
        aerodynamic_resistance=aerodynamic_resistance_canopy,
        latent_heat_vapourisation=latent_heat_vapourisation[1:-1] * 1000,
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
        seconds_to_hour=core_constants.seconds_to_hour,
        return_fluxes=True,
    )

    # Net radiation canopy, [W m-2]
    if not isinstance(new_energy_balance_canopy, dict):
        to_raise = ValueError("The energy balance has not returned any fluxes!")
        LOGGER.error(to_raise)
        raise to_raise

    longwave_emission_canopy = new_energy_balance_canopy["longwave_emission_canopy"]
    latent_heat_flux_canopy = new_energy_balance_canopy["latent_heat_flux_canopy"]
    sensible_heat_flux_canopy = new_energy_balance_canopy["sensible_heat_flux_canopy"]

    net_radiation_canopy = (
        data["shortwave_absorption"][layer_structure.index_filled_canopy].to_numpy()
        - longwave_emission_canopy
    )

    # Write in output dictionary
    # Mean atmospheric pressure profile, [kPa]
    # TODO: #484 this should only be filled for filled/true above ground layers
    output["atmospheric_pressure"] = atmospheric_pressure_out

    # Mean atmospheric C02 profile, [ppm]
    # TODO: #484 this should only be filled for filled/true above ground layers
    output["atmospheric_co2"] = layer_structure.from_template()
    output["atmospheric_co2"][layer_structure.index_atmosphere] = data[
        "atmospheric_co2_ref"
    ].isel(time_index=time_index)

    wind_speed = layer_structure.from_template()
    wind_speed[layer_structure.index_filled_atmosphere] = wind_profile
    output["wind_speed"] = wind_speed

    specific_heat_air_out = layer_structure.from_template()
    specific_heat_air_out[layer_structure.index_filled_atmosphere] = specific_heat_air
    output["specific_heat_air"] = specific_heat_air_out

    density_air_out = layer_structure.from_template()
    density_air_out[layer_structure.index_filled_atmosphere] = density_air
    output["density_air"] = density_air_out

    # Combine longwave emission in one variable
    longwave_emission = layer_structure.from_template()
    longwave_emission[layer_structure.index_filled_canopy] = longwave_emission_canopy
    longwave_emission[layer_structure.index_topsoil_scalar] = longwave_emission_soil
    output["longwave_emission"] = longwave_emission

    net_radiation = layer_structure.from_template()
    net_radiation[layer_structure.index_filled_canopy] = net_radiation_canopy
    net_radiation[layer_structure.index_topsoil_scalar] = net_radiation_soil
    output["net_radiation"] = net_radiation

    latent_heat_vapourisation_out = layer_structure.from_template()
    latent_heat_vapourisation_out[layer_structure.index_filled_atmosphere] = (
        latent_heat_vapourisation
    )
    output["latent_heat_vapourisation"] = latent_heat_vapourisation_out

    # Combine sensible heat flux in one variable
    sensible_heat_flux = layer_structure.from_template()
    sensible_heat_flux[layer_structure.index_filled_canopy] = sensible_heat_flux_canopy
    sensible_heat_flux[layer_structure.index_topsoil_scalar] = sensible_heat_flux_soil
    output["sensible_heat_flux"] = sensible_heat_flux

    # Combine latent heat flux in one variable
    latent_heat_flux = layer_structure.from_template()
    latent_heat_flux[layer_structure.index_filled_canopy] = latent_heat_flux_canopy
    latent_heat_flux[layer_structure.index_topsoil_scalar] = latent_heat_flux_soil
    output["latent_heat_flux"] = latent_heat_flux

    soil_temperature_out = layer_structure.from_template()
    soil_temperature_out[layer_structure.index_all_soil] = soil_temperature
    output["soil_temperature"] = soil_temperature_out

    air_temperature_out = layer_structure.from_template()
    air_temperature_out[layer_structure.index_above] = all_air_temperature[0]
    air_temperature_out[layer_structure.index_filled_canopy] = air_temperature_canopy
    air_temperature_out[layer_structure.index_surface_scalar] = surface_air_temperature
    output["air_temperature"] = air_temperature_out

    canopy_temperature_out = layer_structure.from_template()
    canopy_temperature_out[layer_structure.index_filled_canopy] = canopy_temperature
    output["canopy_temperature"] = canopy_temperature_out

    # Write humidity/VPD
    for var in ["relative_humidity", "vapour_pressure", "vapour_pressure_deficit"]:
        var_out = layer_structure.from_template()
        var_out[layer_structure.index_filled_atmosphere] = (
            new_atmospheric_humidity_vars[var]
        )
        output[var] = var_out

    return output
