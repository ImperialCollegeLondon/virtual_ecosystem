"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

import numpy as np
from pyrealm.constants import CoreConst as PyrealmConst
from pyrealm.core.hygro import calc_specific_heat, calc_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic import abiotic_tools, energy_balance, wind
from virtual_ecosystem.models.abiotic.constants import AbioticConsts


def run_microclimate(
    data: Data,
    time_index: int,
    time_interval: int,
    cell_area: float,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConsts,
    core_constants: CoreConsts,
    pyrealm_const: PyrealmConst,
) -> dict[str, DataArray]:
    """Run microclimate model.

    This function iteratively updates air, soil and canopy temperatures by calculating
    the energy balance for each layer.

    ..TODO: the units of fluxes are in W m-2 and we need to make sure that the input
    energy over a time interval is coherent with the calculations of fluxes in that time
    interval.

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
        pyrealm_const: Set of constants from pyrealm

    Returns:
        dictionary with updated microclimate variables
    """

    output = {}

    # Selection of often used subsets (could be moved to separate function, e.g. tools)
    # NOTE Canopy height will likely become a separate variable, update as required
    canopy_height = data["layer_heights"][1].to_numpy()
    leaf_area_index_sum = np.nansum(data["leaf_area_index"].to_numpy(), axis=0)

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

    # Calculate thickness of above ground layers
    # Add a row of zeros at the bottom to represent ground level (height = 0)
    heights_with_base = np.vstack([wind_heights, np.zeros(wind_heights.shape[1])])
    above_ground_layer_thickness = -np.diff(heights_with_base, axis=0)

    # Wind profiles and resistances
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
        substrate_surface_drag_coefficient=(
            abiotic_constants.substrate_surface_drag_coefficient
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
    # friction_velocity = wind.calculate_friction_velocity(
    #     reference_wind_speed=data["wind_speed_ref"]
    #     .isel(time_index=time_index)
    #     .to_numpy(),
    #     reference_height=(
    #         data["layer_heights"][0].to_numpy()
    #         + abiotic_constants.wind_reference_height
    #     ),
    #     roughness_length=roughness_length,
    #     zero_plane_displacement=zero_plane_displacement,
    #     von_karman_constant=core_constants.von_karmans_constant,
    # )

    #   Friction velocity, [m s-1]
    # friction_velocity = wind.calculate_friction_velocity(
    #     reference_wind_speed=data["wind_speed_ref"]
    #     .isel(time_index=time_index)
    #     .to_numpy(),
    #     reference_height=(
    #         data["layer_heights"][0].to_numpy()
    #         + abiotic_constants.wind_reference_height
    #     ),
    #     roughness_length=roughness_length,
    #     zero_plane_displacement=zero_plane_displacement,
    #     von_karman_constant=core_constants.von_karmans_constant,
    # )

    # Aerodynamic resistance canopy, [s m-1]
    #  TODO The current implementation returns quite high values at the top canopy
    # There seems to be an issue with fluxes as, needs to be checked when fixing
    # temperature update function. Could have to do with low wind speeds.
    # aerodynamic_resistance_canopy = energy_balance.calculate_aerodynamic_resistance(
    #     wind_heights=data["layer_heights"][
    #         layer_structure.index_filled_canopy
    #     ].to_numpy(),
    #     roughness_length=roughness_length,
    #     zero_plane_displacement=zero_plane_displacement,
    #     friction_velocity=friction_velocity,
    #     von_karman_constant=core_constants.von_karmans_constant,
    # )
    aerodynamic_resistance_canopy = np.full_like(
        data["leaf_area_index"][layer_structure.index_filled_canopy], 12.5
    )
    aerodynamic_resistance_canopy_out = layer_structure.from_template()
    aerodynamic_resistance_canopy_out[layer_structure.index_filled_canopy] = (
        aerodynamic_resistance_canopy
    )
    output["aerodynamic_resistance_canopy"] = aerodynamic_resistance_canopy_out

    # Aerodynamic resistance soil, [s m-1]
    aerodynamic_resistance_soil = data["aerodynamic_resistance_surface"].to_numpy()

    # Initialise variables to iterate energy balance to update temperatures
    # TODO check if it actually makes sense to preselect indices, seems messy

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

    iterations = 10  # TODO input var iterations (or convergence criteria)
    for _ in range(iterations):
        #  Calculate atmospheric background variables using mean air temperature
        mean_air_temperature = np.nanmean(all_air_temperature, axis=0)

        # TODO this could take values for each layer instead of bulk
        density_air = abiotic_tools.calculate_air_density(
            air_temperature=mean_air_temperature,
            atmospheric_pressure=atmospheric_pressure[0],  # all layers identical
            specific_gas_constant_dry_air=core_constants.specific_gas_constant_dry_air,
            celsius_to_kelvin=core_constants.zero_Celsius,
        )
        specific_heat_air = calc_specific_heat(
            tc=mean_air_temperature,
        )

        #   Latent heat of vapourisation, [kJ kg-1]
        latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
            temperature=all_air_temperature,
            celsius_to_kelvin=core_constants.zero_Celsius,
            latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
        )

        # Longwave emission from canopy, [W m-2]
        longwave_emission_canopy = energy_balance.calculate_longwave_emission(
            temperature=canopy_temperature + core_constants.zero_Celsius,
            emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann=core_constants.stefan_boltzmann_constant,
        )
        # Longwave emission from soil, [W m-2]
        longwave_emission_soil = energy_balance.calculate_longwave_emission(
            temperature=soil_temperature[0] + core_constants.zero_Celsius,
            emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann=core_constants.stefan_boltzmann_constant,
        )

        #  Sensible heat flux from canopy layers, [W m-2]
        sensible_heat_flux_canopy = energy_balance.calculate_sensible_heat_flux(
            density_air=density_air,
            specific_heat_air=specific_heat_air,
            air_temperature=air_temperature_canopy,
            surface_temperature=canopy_temperature,
            aerodynamic_resistance=aerodynamic_resistance_canopy,
        )

        #  Sensible heat flux from topsoil, [W m-2]
        sensible_heat_flux_soil = energy_balance.calculate_sensible_heat_flux(
            density_air=density_air,
            specific_heat_air=specific_heat_air,
            air_temperature=surface_air_temperature,
            surface_temperature=soil_temperature[0],
            aerodynamic_resistance=aerodynamic_resistance_soil,
        )

        # Saturated vapour pressure of air, [kPa]
        saturated_vapour_pressure_air = calc_vp_sat(
            ta=all_air_temperature,
            core_const=PyrealmConst(),
        )

        #  Actual vapour pressure of air, [kPa]
        actual_vapour_pressure_air = abiotic_tools.calculate_actual_vapour_pressure(
            air_temperature=DataArray(all_air_temperature),
            relative_humidity=DataArray(relative_humidity),
            pyrealm_const=PyrealmConst,
        )

        # Specific humidity of air, [kg kg-1] TODO external function
        specific_humidity_air = (
            abiotic_constants.water_to_air_mass_ratio * actual_vapour_pressure_air
        ) / (atmospheric_pressure - actual_vapour_pressure_air)

        # Latent heat flux canopy, [W m-2]
        # The current implementation converts outputs from plant and hydrology model to
        # ensure energy conservation between modules for now.
        # TODO cross-check with plant model, time step currently month to second
        # TODO also there is a split between evaporation and transpiration, needs to be
        # fixed in #493 - hydrology and evaporation
        # also canopy_evaporation is 2D, chekc that this matches
        # evapotranspiration = data['canopy_evaporation'] + data['transpiration']
        latent_heat_flux_canopy = (
            data["evapotranspiration"][layer_structure.index_filled_canopy].to_numpy()
            / 2.628e6
        ) * latent_heat_vapourisation[1:-1]

        # Latent heat flux topsoil, [W m-2]
        # TODO cross-check with hydrology model, time step currently month to second
        latent_heat_flux_soil = (
            data["soil_evaporation"].to_numpy()
            / 2.628e6
            * latent_heat_vapourisation[-1]
        )

        # TODO name absorption variable like plants - Net radiation topsoil, [W m-2]
        net_radiation_soil = energy_balance.calculate_net_radiation(
            incoming_radiation=data["downward_shortwave_radiation"]
            .isel(time_index=time_index)
            .to_numpy(),
            absorbed_radiation=data["shortwave_absorption"][
                layer_structure.index_topsoil_scalar
            ].to_numpy(),
            longwave_emission=longwave_emission_soil,
            albedo=abiotic_constants.surface_albedo,
        )

        # Ground heat flux, [W m-2]
        ground_heat_flux = (
            net_radiation_soil - latent_heat_flux_soil - sensible_heat_flux_soil
        )

        # Update soil temperatures, [C]
        # TODO Soil parameter currently constants, replace with soil maps
        new_soil_temperature = energy_balance.update_soil_temperature(
            ground_heat_flux=ground_heat_flux,
            soil_temperature=soil_temperature,
            soil_layer_thickness=layer_structure.soil_layer_thickness,
            soil_thermal_conductivity=abiotic_constants.soil_thermal_conductivity,
            soil_bulk_density=abiotic_constants.bulk_density_soil,
            specific_heat_capacity_soil=abiotic_constants.specific_heat_capacity_soil,
            time_interval=time_interval,
        )

        # Update air/canopy temperatures
        # TODO add parameters to constants and include conductivities
        new_canopy_temperature, new_air_temperature_canopy = (
            energy_balance.update_air_canopy_temperature(
                absorbed_radiation_canopy=data["shortwave_absorption"][
                    layer_structure.index_filled_canopy
                ].to_numpy(),
                longwave_emission_canopy=longwave_emission_canopy,
                sensible_heat_flux_canopy=sensible_heat_flux_canopy,
                latent_heat_flux_canopy=latent_heat_flux_canopy,
                air_temperature=air_temperature_canopy + core_constants.zero_Celsius,
                canopy_temperature=canopy_temperature + core_constants.zero_Celsius,
                emissivity_leaf=abiotic_constants.leaf_emissivity,
                specific_heat_air=specific_heat_air,
                density_air=density_air,
                aerodynamic_resistance=aerodynamic_resistance_canopy,
                relaxation_factor=0.1,
                stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            )
        )

        #  TODO check Update surface/soil temperature, use same function as canopy?
        # TODO add vertical mixing, not urgent
        surface_temperature_change = sensible_heat_flux_soil / (
            density_air * specific_heat_air
        )
        new_surface_temperature = (
            surface_air_temperature + core_constants.zero_Celsius
        ) + surface_temperature_change

        soil_temperature = new_soil_temperature
        air_temperature_canopy = (
            new_air_temperature_canopy - core_constants.zero_Celsius
        )
        canopy_temperature = new_canopy_temperature - core_constants.zero_Celsius
        surface_air_temperature = new_surface_temperature - core_constants.zero_Celsius

        all_air_temperature[1 : len(canopy_temperature) + 1] = canopy_temperature
        all_air_temperature[-1] = surface_air_temperature

        # TODO dimensions -  Update atmospheric humidity/VPD
        new_atmospheric_humidity_vars = energy_balance.update_humidity_vpd(
            evapotranspiration=data["evapotranspiration"][
                layer_structure.index_filled_canopy
            ].to_numpy(),
            soil_evaporation=data["soil_evaporation"].to_numpy(),
            saturated_vapour_pressure=saturated_vapour_pressure_air,
            specific_humidity=specific_humidity_air.to_numpy(),
            layer_thickness=above_ground_layer_thickness,
            atmospheric_pressure=atmospheric_pressure,
            water_to_air_mass_ratio=abiotic_constants.water_to_air_mass_ratio,
            dry_air_factor=abiotic_constants.dry_air_factor,
            cell_area=cell_area,
        )
        relative_humidity = new_atmospheric_humidity_vars["relative_humidity"]

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

    # Combine longwave emission in one variable
    # Assumption: accumulated emission in time interval based on accumulated input
    longwave_emission = layer_structure.from_template()
    longwave_emission[layer_structure.index_filled_canopy] = longwave_emission_canopy
    longwave_emission[layer_structure.index_topsoil_scalar] = longwave_emission_soil
    output["longwave_emission"] = longwave_emission

    output["density_air"] = DataArray(density_air, dims="cell_id")
    output["specific_heat_air"] = DataArray(specific_heat_air, dims="cell_id")

    aero_resistance_canopy_out = layer_structure.from_template()
    aero_resistance_canopy_out[layer_structure.index_filled_canopy] = (
        aerodynamic_resistance_canopy
    )
    output["aerodynamic_resistance_canopy"] = aero_resistance_canopy_out

    latent_heat_vapourisation_out = layer_structure.from_template()
    latent_heat_vapourisation_out[layer_structure.index_filled_atmosphere] = (
        latent_heat_vapourisation
    )
    output["latent_heat_vapourisation"] = latent_heat_vapourisation_out
    # Combine sensible heat flux in one variable, TODO consider time interval
    sensible_heat_flux = layer_structure.from_template()
    sensible_heat_flux[layer_structure.index_filled_canopy] = sensible_heat_flux_canopy
    sensible_heat_flux[layer_structure.index_topsoil_scalar] = sensible_heat_flux_soil
    output["sensible_heat_flux"] = sensible_heat_flux  # * time_interval

    # Combine latent heat flux in one variable, TODO consider time interval
    # TODO adjust to model timestep, currently per second
    latent_heat_flux = layer_structure.from_template()
    latent_heat_flux[layer_structure.index_filled_canopy] = latent_heat_flux_canopy
    latent_heat_flux[layer_structure.index_topsoil_scalar] = latent_heat_flux_soil
    output["latent_heat_flux"] = latent_heat_flux * time_interval

    soil_temperature_out = layer_structure.from_template()
    soil_temperature_out[layer_structure.index_all_soil] = soil_temperature
    output["soil_temperature"] = soil_temperature_out

    air_temperature_out = layer_structure.from_template()
    air_temperature_out[layer_structure.index_above] = all_air_temperature[0]
    air_temperature_out[layer_structure.index_filled_canopy] = air_temperature_canopy
    air_temperature_out[layer_structure.index_surface] = surface_air_temperature
    output["air_temperature"] = air_temperature_out

    canopy_temperature_out = layer_structure.from_template()
    canopy_temperature_out[layer_structure.index_filled_canopy] = canopy_temperature
    output["canopy_temperature"] = canopy_temperature_out

    # TODO check dimensions write humidity/VPD
    for var in ["relative_humidity", "vapour_pressure", "vapour_pressure_deficit"]:
        var_out = layer_structure.from_template()
        var_out[layer_structure.index_filled_atmosphere] = (
            new_atmospheric_humidity_vars[var]
        )
        output[var] = var_out

    return output
