"""The bigleaf module integrates the radiation and energy balance for the
Virtual Ecosystem to retunr updated ground, air and canopy temperatures.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic import (
    abiotic_tools,
    conductivities,
    energy_balance,
    radiation,
    wind,
)
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
from virtual_ecosystem.models.abiotic_simple.microclimate import (
    calculate_saturation_vapour_pressure,
)
from virtual_ecosystem.models.hydrology.constants import HydroConsts


def bigleaf(
    data: Data,
    timestep: dict[str, int],
    time_index: int,
    latitude: NDArray[np.float32],
    longitude: NDArray[np.float32],
    slope: NDArray[np.float32],
    aspect: NDArray[np.float32],
    core_constants: CoreConsts,
    abiotic_constants: AbioticConsts,
    abiotic_simple_constants: AbioticSimpleConsts,
    hydro_constants: HydroConsts,
    layer_structure: LayerStructure,
) -> dict[str, NDArray[np.float32]]:
    """Run Big leaf model for one time step."""

    # Unpack time step
    year = timestep["year"]
    month = timestep["month"]
    day = timestep["day"]
    local_time = timestep["hour"]

    # extract often used variables from data object
    reference_height = data["layer_heights"][0].to_numpy()
    plant_area_index_sum = data["leaf_area_index"].sum(dim="layers").to_numpy()
    canopy_temperature_mean = data["canopy_temperature"].mean(dim="layers").to_numpy()
    canopy_height, ground_temperature, top_soil_moisture = (
        data["layer_heights"][1].to_numpy(),
        data["soil_temperature"][layer_structure.index_topsoil_scalar].to_numpy(),
        data["soil_moisture"][layer_structure.index_topsoil_scalar].to_numpy(),
    )
    (
        air_temperature_ref,
        atmospheric_pressure_ref,
        relative_humidity_ref,
        wind_speed_ref,
    ) = (
        data["air_temperature_ref"].isel(time_index=time_index).to_numpy(),
        data["atmospheric_pressure_ref"].isel(time_index=time_index).to_numpy(),
        data["relative_humidity_ref"].isel(time_index=time_index).to_numpy(),
        data["wind_speed_ref"].isel(time_index=time_index).to_numpy(),
    )
    (
        topofcanopy_shortwave_radiation,
        topofcanopy_diffuse_radiation,
        longwave_radiation_down,
    ) = (
        data["shortwave_radiation_down"].isel(time_index=time_index).to_numpy(),
        data["diffuse_radiation_down"].isel(time_index=time_index).to_numpy(),
        data["longwave_radiation_down"].isel(time_index=time_index).to_numpy(),
    )

    # Calculate absorbed shortwave radiation
    absorbed_shortwave_radiation = radiation.calculate_absorbed_shortwave_radiation(
        plant_area_index_sum=plant_area_index_sum,
        leaf_orientation_coefficient=abiotic_constants.leaf_orientation_coefficient,
        leaf_reluctance_shortwave=abiotic_constants.leaf_reluctance_shortwave,
        leaf_transmittance_shortwave=abiotic_constants.leaf_transmittance_shortwave,
        clumping_factor=abiotic_constants.clumping_factor,
        ground_reflectance=abiotic_constants.ground_reflectance,
        slope=slope,
        aspect=aspect,
        latitude=latitude,
        longitude=longitude,
        year=year,
        month=month,
        day=day,
        local_time=local_time,
        topofcanopy_shortwave_radiation=topofcanopy_shortwave_radiation,
        topofcanopy_diffuse_radiation=topofcanopy_diffuse_radiation,
        leaf_inclination_angle_coefficient=(
            abiotic_constants.leaf_inclination_angle_coefficient
        ),
    )

    # Calculate time-invariant variables
    adjusted_plant_area_index = plant_area_index_sum / (
        1 - abiotic_constants.clumping_factor
    )
    radiation_transmission_coefficient = (
        1 - abiotic_constants.clumping_factor**2
    ) * np.exp(-adjusted_plant_area_index) + abiotic_constants.clumping_factor**2

    # Calculate zero plane displacement height
    zero_plane_displacement = wind.calculate_zero_plane_displacement(
        canopy_height=canopy_height,
        leaf_area_index=plant_area_index_sum,
        zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
    )
    # Used to avoid (h-d)/zm being less than one, meaning log((h-d)/zm) becomes negative
    drag_limit = core_constants.von_karmans_constant / np.sqrt(
        abiotic_constants.substrate_surface_drag_coefficient
        + (abiotic_constants.drag_coefficient * plant_area_index_sum) / 2
    )

    # Initialize variables
    diabatic_factors = {
        "psi_m": np.zeros(len(topofcanopy_shortwave_radiation)),
        "psi_h": np.zeros(len(topofcanopy_shortwave_radiation)),
    }
    ground_heat_flux = np.full_like(topofcanopy_shortwave_radiation, 0.0)

    sensible_heat_flux = (
        0.5 * topofcanopy_shortwave_radiation
        - abiotic_constants.leaf_emissivity
        * core_constants.stefan_boltzmann_constant
        * (air_temperature_ref + core_constants.zero_Celsius) ** 4
    )
    # TODO iterate from here until model converges, not implemented

    # Calculate longwave radiation (from here, micropoint iterates)
    canopy_longwave_emission = radiation.calculate_canopy_longwave_emission(
        leaf_emissivity=abiotic_constants.leaf_emissivity,
        canopy_temperature=data["canopy_temperature"].to_numpy(),
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        zero_Celsius=core_constants.zero_Celsius,
    )
    # longwave radiation from the sky
    longwave_downward_radiation_sky = (
        abiotic_constants.leaf_emissivity * longwave_radiation_down
    )

    # longwave radiation from ground
    ground_longwave_radiation = abiotic_constants.ground_emissivity * (
        radiation_transmission_coefficient * longwave_downward_radiation_sky
        + (1 - radiation_transmission_coefficient)
        * np.nansum(canopy_longwave_emission, axis=0)
    )
    # Calculate absorbed radiation
    ground_total_absorption = (
        absorbed_shortwave_radiation["ground_shortwave_absorption"]
        + ground_longwave_radiation
    )
    canopy_total_absorption = (
        absorbed_shortwave_radiation["canopy_shortwave_absorption"]
        + longwave_downward_radiation_sky
    )
    # Calculate roughness length momentum
    roughness_length_momentum = wind.calculate_roughness_length_momentum(
        canopy_height=canopy_height,
        plant_area_index=plant_area_index_sum,
        zero_plane_displacement=zero_plane_displacement,
        diabatic_correction_heat=diabatic_factors["psi_h"],
        substrate_surface_drag_coefficient=(
            abiotic_constants.substrate_surface_drag_coefficient
        ),
        drag_coefficient=abiotic_constants.drag_coefficient,
        min_roughness_length=abiotic_constants.min_roughness_length,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    # Calculate friction velocity
    friction_velocity = wind.calculate_friction_velocity(
        wind_speed_ref=wind_speed_ref,
        canopy_height=canopy_height,
        zeroplane_displacement=zero_plane_displacement,
        roughness_length_momentum=roughness_length_momentum,
        diabatic_correction_momentum=diabatic_factors["psi_m"],
        von_karmans_constant=core_constants.von_karmans_constant,
        min_friction_velocity=abiotic_constants.min_friction_velocity,
    )
    # Calculate conductivities
    free_convection = conductivities.calculate_free_convection(
        leaf_dimension=abiotic_constants.leaf_dimension,
        sensible_heat_flux=abs(sensible_heat_flux),
    )
    minimum_conductance = free_convection * 2 * plant_area_index_sum
    temperature_average_air_canopy = (air_temperature_ref + canopy_temperature_mean) / 2

    molar_density_air = abiotic_tools.calculate_molar_density_air(
        temperature=temperature_average_air_canopy,
        atmospheric_pressure=atmospheric_pressure_ref,
        standard_mole=core_constants.standard_mole,
        standard_pressure=core_constants.standard_pressure,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )
    air_heat_conductivity = conductivities.calculate_molar_conductance_above_canopy(
        friction_velocity=friction_velocity,
        zero_plane_displacement=zero_plane_displacement,
        roughness_length_momentum=roughness_length_momentum,
        reference_height=reference_height,
        molar_density_air=molar_density_air,
        diabatic_correction_heat=diabatic_factors["psi_h"],
        minimum_conductance=minimum_conductance,
        von_karmans_constant=core_constants.von_karmans_constant,
    )
    stomatal_conductivity = conductivities.calculate_stomatal_conductance(
        shortwave_radiation=topofcanopy_shortwave_radiation,
        maximum_stomatal_conductance=abiotic_constants.maximum_stomatal_conductance * 3,
        half_saturation_stomatal_conductance=(
            abiotic_constants.half_saturation_stomatal_conductance * 3
        ),
    )
    leaf_vapour_conductivity = 1 / (
        1 / air_heat_conductivity + 1 / stomatal_conductivity
    )

    leaf_vapour_conductivity = np.where(
        stomatal_conductivity == 0, 0, leaf_vapour_conductivity
    )

    saturation_vapour_pressure = calculate_saturation_vapour_pressure(
        temperature=data["air_temperature_ref"].isel(time_index=time_index),
        saturation_vapour_pressure_factors=(
            abiotic_simple_constants.saturation_vapour_pressure_factors
        ),
    )
    effective_vapour_pressure_air = (
        saturation_vapour_pressure * relative_humidity_ref / 100
    )
    canopy_temperature_new = energy_balance.calculate_surface_temperature(
        total_absorbed_radiation=canopy_total_absorption,
        heat_conductivity=air_heat_conductivity,
        vapour_conductivity=leaf_vapour_conductivity,
        surface_temperature=air_temperature_ref,
        temperature_average_air_surface=temperature_average_air_canopy,
        atmospheric_pressure=atmospheric_pressure_ref,
        effective_vapour_pressure_air=effective_vapour_pressure_air.to_numpy(),
        surface_emissivity=abiotic_constants.leaf_emissivity,
        ground_heat_flux=ground_heat_flux,
        relative_humidity=relative_humidity_ref,
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=(abiotic_constants.latent_heat_vap_equ_factors),
        molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
        specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
        saturation_vapour_pressure_factors=(
            abiotic_simple_constants.saturation_vapour_pressure_factors
        ),
    )
    dewpoint_temperature = abiotic_tools.calculate_dewpoint_temperature(
        air_temperature=air_temperature_ref,
        effective_vapour_pressure_air=effective_vapour_pressure_air.to_numpy(),
    )
    canopy_temperature_new = np.where(
        canopy_temperature_new < dewpoint_temperature,
        dewpoint_temperature,
        canopy_temperature_new,
    )

    # Calculate ground surface temperature
    soil_layer_thickness_mm = np.tile(
        (layer_structure.soil_layer_thickness * core_constants.meters_to_mm)[:, None],
        len(air_temperature_ref),
    )
    top_soil_moisture_capacity = (
        hydro_constants.soil_moisture_capacity * soil_layer_thickness_mm[0]
    )
    top_soil_moisture_residual = (
        hydro_constants.soil_moisture_residual * soil_layer_thickness_mm[0]
    )
    soil_relative_humidity = (top_soil_moisture - top_soil_moisture_residual) / (
        top_soil_moisture_capacity - top_soil_moisture_residual
    )

    temperature_average_air_ground = (ground_temperature + air_temperature_ref) / 2
    ground_temperature_new = energy_balance.calculate_surface_temperature(
        total_absorbed_radiation=ground_total_absorption,
        heat_conductivity=air_heat_conductivity,  # TODO micropoint uses gHa
        vapour_conductivity=air_heat_conductivity,  # not sure why ??
        surface_temperature=ground_temperature,
        temperature_average_air_surface=temperature_average_air_ground,
        atmospheric_pressure=atmospheric_pressure_ref,
        effective_vapour_pressure_air=effective_vapour_pressure_air,
        surface_emissivity=abiotic_constants.ground_emissivity,
        ground_heat_flux=ground_heat_flux,
        relative_humidity=soil_relative_humidity / soil_layer_thickness_mm[0],
        stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=(abiotic_constants.latent_heat_vap_equ_factors),
        molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
        specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
        saturation_vapour_pressure_factors=(
            abiotic_simple_constants.saturation_vapour_pressure_factors
        ),
    )
    ground_temperature_new = np.where(
        ground_temperature_new > dewpoint_temperature,
        ground_temperature_new,
        dewpoint_temperature,
    )

    # Cap values
    difference_canopy_air_temperature = canopy_temperature_new - air_temperature_ref
    difference_ground_air_temperature = ground_temperature_new - air_temperature_ref
    difference_canopy_air_temperature = np.where(
        np.abs(difference_canopy_air_temperature) > 5.0,  # dTmax, input variable
        5.0,
        difference_canopy_air_temperature,
    )
    difference_ground_air_temperature = np.where(
        np.abs(difference_ground_air_temperature) > 5.0,
        5.0,
        difference_ground_air_temperature,
    )
    canopy_temperature_new = air_temperature_ref + difference_canopy_air_temperature
    ground_temperature_new = air_temperature_ref + difference_ground_air_temperature

    # TODO Run convergence test, not implemented

    # TODO Reassign canopy_temperature and ground_temperature using bwgt (backward
    # weighting to apply when iteratively running the model (default 0.5))
    bwgt = 0.5
    canopy_temperature_mean = (
        bwgt * canopy_temperature_mean + (1 - bwgt) * canopy_temperature_new
    )
    ground_temperature = bwgt * ground_temperature + (1 - bwgt) * ground_temperature_new

    # Recalculate variables
    temperature_average_air_canopy = (canopy_temperature_mean + air_temperature_ref) / 2
    temperature_average_air_canopy_kelvin = (
        core_constants.zero_Celsius + temperature_average_air_canopy
    )
    temperature_average_air_ground = (
        canopy_temperature_mean + temperature_average_air_ground
    ) / 2
    molar_density_air = abiotic_tools.calculate_molar_density_air(
        temperature=temperature_average_air_canopy,
        atmospheric_pressure=atmospheric_pressure_ref,
        standard_mole=core_constants.standard_mole,
        standard_pressure=core_constants.standard_pressure,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )
    specific_heat_air = abiotic_tools.calculate_specific_heat_air(
        temperature=temperature_average_air_canopy,
        molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
        specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
    )

    # Calculate sensible heat flux
    sensible_heat_flux = bwgt * sensible_heat_flux + (1 - bwgt) * (
        air_heat_conductivity
        * specific_heat_air
        * (canopy_temperature_new - air_temperature_ref)
    )

    # Set limits to sensible heat flux
    net_radiation = (
        canopy_total_absorption
        - core_constants.stefan_boltzmann_constant
        * abiotic_constants.leaf_emissivity
        * (canopy_temperature_new + 273.15) ** 4
    )
    sensible_heat_flux = np.where(
        sensible_heat_flux > net_radiation, net_radiation, sensible_heat_flux
    )

    # Recalculate stability variables
    monin_obukov_length = wind.calculate_monin_obukov_length(
        air_temperature=temperature_average_air_canopy_kelvin,
        friction_velocity=friction_velocity,
        sensible_heat_flux=sensible_heat_flux,
        zero_degree=core_constants.zero_Celsius,
        specific_heat_air=specific_heat_air,
        density_air=molar_density_air,
        von_karman_constant=core_constants.von_karmans_constant,
        gravity=core_constants.gravity,
    )

    stability_parameter = wind.calculate_stability_parameter(
        reference_height=reference_height,
        zero_plance_displacement=zero_plane_displacement,
        monin_obukov_length=monin_obukov_length,
    )

    diabatic_factors = wind.calculate_diabatic_correction_factors(
        stability_parameter=stability_parameter,
        stability_formulation="Businger_1971",  # TODO
    )

    phih = wind.calculate_diabatic_influence_heat(
        stability_parameter=stability_parameter,
    )

    # Set limits to diabatic coefficients
    ln1 = np.log(
        (reference_height - zero_plane_displacement) / roughness_length_momentum
    )
    ln2 = np.log(
        (reference_height - zero_plane_displacement)
        / (abiotic_constants.drag_coefficient * roughness_length_momentum)
    )
    diabatic_factors["psi_m"] = np.clip(
        diabatic_factors["psi_m"], -0.9 * ln1, 0.9 * ln1
    )
    diabatic_factors["psi_h"] = np.clip(
        diabatic_factors["psi_h"], -0.9 * ln2, np.minimum(0.9 * ln2, 0.9 * drag_limit)
    )
    # TODO end of i loop here

    #         # Recalculate Ground heat flux TODO add function
    #         new_ground_heat_flux = calculate_ground_heat_flux(
    #             soil_surface_temperature=ground_temperature[i],
    #             soil_moisture=soil_moisture,
    #             bulk_density_soil=bulk_density,
    #             volumetric_mineral_content=volumetric_mineral_content,
    #             volumetric_quartz_content=volumetric_quartz_content,
    #             mass_fraction_clay=mass_fraction_clay,
    #             calculate_yearly_flux=calculate_yearly_flux,
    #             #  Gmax, Gmin, iter??
    #         )
    #         ground_heat_flux = new_ground_heat_flux["ground_heat_flux"]
    #         # min_ground_heat_flux = new_ground_heat_flux["min_ground_heat_flux"]
    #         # max_ground_heat_flux = new_ground_heat_flux["max_ground_heat_flux"]

    # End of iterative loop here
    output = {
        "canopy_temperature": canopy_temperature_mean,
        "ground_temperature": ground_temperature,
        "sensible_heat_flux": sensible_heat_flux,
        "ground_heat_flux": ground_heat_flux,
        "net_radiation": net_radiation,
        "psih": diabatic_factors["psi_h"],
        "psim": diabatic_factors["psi_m"],
        "phih": phih,
        "monin_obukov_length": monin_obukov_length,
        "friction_velocity": friction_velocity,
        "canopy_shortwave_absorption": absorbed_shortwave_radiation[
            "canopy_shortwave_absorption"
        ],
        "ground_shortwave_absorption": absorbed_shortwave_radiation[
            "ground_shortwave_absorption"
        ],
        "albedo": absorbed_shortwave_radiation["albedo"],
    }

    return output
