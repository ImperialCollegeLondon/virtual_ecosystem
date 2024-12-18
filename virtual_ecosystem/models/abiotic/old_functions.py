"""Collection of retired functions for future reference."""

# """The bigleaf module integrates the radiation and energy balance for the
# Virtual Ecosystem to retunr updated ground, air and canopy temperatures.
# """

# import numpy as np
# from numpy.typing import NDArray

# from virtual_ecosystem.core.constants import CoreConsts
# from virtual_ecosystem.core.core_components import LayerStructure
# from virtual_ecosystem.core.data import Data
# from virtual_ecosystem.models.abiotic import (
#     abiotic_tools,
#     conductivities,
#     energy_balance,
#     radiation,
#     wind,
# )
# from virtual_ecosystem.models.abiotic.constants import AbioticConsts
# from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts
# from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
#     calculate_saturation_vapour_pressure,
# )
# from virtual_ecosystem.models.hydrology.constants import HydroConsts


# def bigleaf(
#     data: Data,
#     timestep: dict[str, int],
#     time_index: int,
#     latitude: NDArray[np.float32],
#     longitude: NDArray[np.float32],
#     slope: NDArray[np.float32],
#     aspect: NDArray[np.float32],
#     core_constants: CoreConsts,
#     abiotic_constants: AbioticConsts,
#     abiotic_simple_constants: AbioticSimpleConsts,
#     hydro_constants: HydroConsts,
#     layer_structure: LayerStructure,
# ) -> dict[str, NDArray[np.float32]]:
#     """Run Big leaf model for one time step."""

#     # Unpack time step
#     year = timestep["year"]
#     month = timestep["month"]
#     day = timestep["day"]
#     local_time = timestep["hour"]

#     # extract often used variables from data object
#     reference_height = data["layer_heights"][0].to_numpy()
#     plant_area_index_sum = data["leaf_area_index"].sum(dim="layers").to_numpy()
#     canopy_temperature_mean = data["canopy_temperature"].mean(dim="layers").to_numpy()
#     canopy_height, ground_temperature, top_soil_moisture = (
#         data["layer_heights"][1].to_numpy(),
#         data["soil_temperature"][layer_structure.index_topsoil_scalar].to_numpy(),
#         data["soil_moisture"][layer_structure.index_topsoil_scalar].to_numpy(),
#     )
#     (
#         air_temperature_ref,
#         atmospheric_pressure_ref,
#         relative_humidity_ref,
#         wind_speed_ref,
#     ) = (
#         data["air_temperature_ref"].isel(time_index=time_index).to_numpy(),
#         data["atmospheric_pressure_ref"].isel(time_index=time_index).to_numpy(),
#         data["relative_humidity_ref"].isel(time_index=time_index).to_numpy(),
#         data["wind_speed_ref"].isel(time_index=time_index).to_numpy(),
#     )
#     (
#         topofcanopy_shortwave_radiation,
#         topofcanopy_diffuse_radiation,
#         longwave_radiation_down,
#     ) = (
#         data["shortwave_radiation_down"].isel(time_index=time_index).to_numpy(),
#         data["diffuse_radiation_down"].isel(time_index=time_index).to_numpy(),
#         data["longwave_radiation_down"].isel(time_index=time_index).to_numpy(),
#     )

#     # Calculate absorbed shortwave radiation
#     absorbed_shortwave_radiation = radiation.calculate_absorbed_shortwave_radiation(
#         plant_area_index_sum=plant_area_index_sum,
#         leaf_orientation_coefficient=abiotic_constants.leaf_orientation_coefficient,
#         leaf_reluctance_shortwave=abiotic_constants.leaf_reluctance_shortwave,
#         leaf_transmittance_shortwave=abiotic_constants.leaf_transmittance_shortwave,
#         clumping_factor=abiotic_constants.clumping_factor,
#         ground_reflectance=abiotic_constants.ground_reflectance,
#         slope=slope,
#         aspect=aspect,
#         latitude=latitude,
#         longitude=longitude,
#         year=year,
#         month=month,
#         day=day,
#         local_time=local_time,
#         topofcanopy_shortwave_radiation=topofcanopy_shortwave_radiation,
#         topofcanopy_diffuse_radiation=topofcanopy_diffuse_radiation,
#         leaf_inclination_angle_coefficient=(
#             abiotic_constants.leaf_inclination_angle_coefficient
#         ),
#     )

#     # Calculate time-invariant variables
#     adjusted_plant_area_index = plant_area_index_sum / (
#         1 - abiotic_constants.clumping_factor
#     )
#     radiation_transmission_coefficient = (
#         1 - abiotic_constants.clumping_factor**2
#     ) * np.exp(-adjusted_plant_area_index) + abiotic_constants.clumping_factor**2

#     # Calculate zero plane displacement height
#     zero_plane_displacement = wind.calculate_zero_plane_displacement(
#         canopy_height=canopy_height,
#         leaf_area_index=plant_area_index_sum,
#         zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
#     )
#     # Used to avoid (h-d)/zm being less than one, meaning log((h-d)/zm) becomes neg
#     drag_limit = core_constants.von_karmans_constant / np.sqrt(
#         abiotic_constants.substrate_surface_drag_coefficient
#         + (abiotic_constants.drag_coefficient * plant_area_index_sum) / 2
#     )

#     # Initialize variables
#     diabatic_factors = {
#         "psi_m": np.zeros(len(topofcanopy_shortwave_radiation)),
#         "psi_h": np.zeros(len(topofcanopy_shortwave_radiation)),
#     }
#     ground_heat_flux = np.full_like(topofcanopy_shortwave_radiation, 0.0)

#     sensible_heat_flux = (
#         0.5 * topofcanopy_shortwave_radiation
#         - abiotic_constants.leaf_emissivity
#         * core_constants.stefan_boltzmann_constant
#         * (air_temperature_ref + core_constants.zero_Celsius) ** 4
#     )
#     # TODO iterate from here until model converges, not implemented

#     # Calculate longwave radiation (from here, micropoint iterates)
#     canopy_longwave_emission = radiation.calculate_canopy_longwave_emission(
#         leaf_emissivity=abiotic_constants.leaf_emissivity,
#         canopy_temperature=data["canopy_temperature"].to_numpy(),
#         stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
#         zero_Celsius=core_constants.zero_Celsius,
#     )
#     # longwave radiation from the sky
#     longwave_downward_radiation_sky = (
#         abiotic_constants.leaf_emissivity * longwave_radiation_down
#     )

#     # longwave radiation from ground
#     ground_longwave_radiation = abiotic_constants.ground_emissivity * (
#         radiation_transmission_coefficient * longwave_downward_radiation_sky
#         + (1 - radiation_transmission_coefficient)
#         * np.nansum(canopy_longwave_emission, axis=0)
#     )
#     # Calculate absorbed radiation
#     ground_total_absorption = (
#         absorbed_shortwave_radiation["ground_shortwave_absorption"]
#         + ground_longwave_radiation
#     )
#     canopy_total_absorption = (
#         absorbed_shortwave_radiation["canopy_shortwave_absorption"]
#         + longwave_downward_radiation_sky
#     )
#     # Calculate roughness length momentum
#     roughness_length_momentum = wind.calculate_roughness_length_momentum(
#         canopy_height=canopy_height,
#         plant_area_index=plant_area_index_sum,
#         zero_plane_displacement=zero_plane_displacement,
#         diabatic_correction_heat=diabatic_factors["psi_h"],
#         substrate_surface_drag_coefficient=(
#             abiotic_constants.substrate_surface_drag_coefficient
#         ),
#         drag_coefficient=abiotic_constants.drag_coefficient,
#         min_roughness_length=abiotic_constants.min_roughness_length,
#         von_karman_constant=core_constants.von_karmans_constant,
#     )

#     # Calculate friction velocity
#     friction_velocity = wind.calculate_friction_velocity(
#         wind_speed_ref=wind_speed_ref,
#         canopy_height=canopy_height,
#         zeroplane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         diabatic_correction_momentum=diabatic_factors["psi_m"],
#         von_karmans_constant=core_constants.von_karmans_constant,
#         min_friction_velocity=abiotic_constants.min_friction_velocity,
#     )
#     # Calculate conductivities
#     free_convection = conductivities.calculate_free_convection(
#         leaf_dimension=abiotic_constants.leaf_dimension,
#         sensible_heat_flux=abs(sensible_heat_flux),
#     )
#     minimum_conductance = free_convection * 2 * plant_area_index_sum
#     temperature_average_air_canopy =
# (air_temperature_ref + canopy_temperature_mean) / 2

#     molar_density_air = abiotic_tools.calculate_molar_density_air(
#         temperature=temperature_average_air_canopy,
#         atmospheric_pressure=atmospheric_pressure_ref,
#         standard_mole=core_constants.standard_mole,
#         standard_pressure=core_constants.standard_pressure,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#     )
#     air_heat_conductivity = conductivities.calculate_molar_conductance_above_canopy(
#         friction_velocity=friction_velocity,
#         zero_plane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         reference_height=reference_height,
#         molar_density_air=molar_density_air,
#         diabatic_correction_heat=diabatic_factors["psi_h"],
#         minimum_conductance=minimum_conductance,
#         von_karmans_constant=core_constants.von_karmans_constant,
#     )
#     stomatal_conductivity = conductivities.calculate_stomatal_conductance(
#         shortwave_radiation=topofcanopy_shortwave_radiation,
#         maximum_stomatal_conductance=(
# abiotic_constants.maximum_stomatal_conductance * 3
# ),
#         half_saturation_stomatal_conductance=(
#             abiotic_constants.half_saturation_stomatal_conductance * 3
#         ),
#     )
#     leaf_vapour_conductivity = 1 / (
#         1 / air_heat_conductivity + 1 / stomatal_conductivity
#     )

#     leaf_vapour_conductivity = np.where(
#         stomatal_conductivity == 0, 0, leaf_vapour_conductivity
#     )

#     saturation_vapour_pressure = calculate_saturation_vapour_pressure(
#         temperature=data["air_temperature_ref"].isel(time_index=time_index),
#         saturation_vapour_pressure_factors=(
#             abiotic_simple_constants.saturation_vapour_pressure_factors
#         ),
#     )
#     effective_vapour_pressure_air = (
#         saturation_vapour_pressure * relative_humidity_ref / 100
#     )
#     canopy_temperature_new = energy_balance.calculate_surface_temperature(
#         total_absorbed_radiation=canopy_total_absorption,
#         heat_conductivity=air_heat_conductivity,
#         vapour_conductivity=leaf_vapour_conductivity,
#         surface_temperature=air_temperature_ref,
#         temperature_average_air_surface=temperature_average_air_canopy,
#         atmospheric_pressure=atmospheric_pressure_ref,
#         effective_vapour_pressure_air=effective_vapour_pressure_air.to_numpy(),
#         surface_emissivity=abiotic_constants.leaf_emissivity,
#         ground_heat_flux=ground_heat_flux,
#         relative_humidity=relative_humidity_ref,
#         stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#         latent_heat_vap_equ_factors=(abiotic_constants.latent_heat_vap_equ_factors),
#         molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#         specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#         saturation_vapour_pressure_factors=(
#             abiotic_simple_constants.saturation_vapour_pressure_factors
#         ),
#     )
#     dewpoint_temperature = abiotic_tools.calculate_dewpoint_temperature(
#         air_temperature=air_temperature_ref,
#         effective_vapour_pressure_air=effective_vapour_pressure_air.to_numpy(),
#     )
#     canopy_temperature_new = np.where(
#         canopy_temperature_new < dewpoint_temperature,
#         dewpoint_temperature,
#         canopy_temperature_new,
#     )

#     # Calculate ground surface temperature
#     soil_layer_thickness_mm = np.tile(
#         (layer_structure.soil_layer_thickness * core_constants.meters_to_mm)[:, None],
#         len(air_temperature_ref),
#     )
#     top_soil_moisture_capacity = (
#         hydro_constants.soil_moisture_capacity * soil_layer_thickness_mm[0]
#     )
#     top_soil_moisture_residual = (
#         hydro_constants.soil_moisture_residual * soil_layer_thickness_mm[0]
#     )
#     soil_relative_humidity = (top_soil_moisture - top_soil_moisture_residual) / (
#         top_soil_moisture_capacity - top_soil_moisture_residual
#     )

#     temperature_average_air_ground = (ground_temperature + air_temperature_ref) / 2
#     ground_temperature_new = energy_balance.calculate_surface_temperature(
#         total_absorbed_radiation=ground_total_absorption,
#         heat_conductivity=air_heat_conductivity,  # TODO micropoint uses gHa
#         vapour_conductivity=air_heat_conductivity,  # not sure why ??
#         surface_temperature=ground_temperature,
#         temperature_average_air_surface=temperature_average_air_ground,
#         atmospheric_pressure=atmospheric_pressure_ref,
#         effective_vapour_pressure_air=effective_vapour_pressure_air,
#         surface_emissivity=abiotic_constants.ground_emissivity,
#         ground_heat_flux=ground_heat_flux,
#         relative_humidity=soil_relative_humidity / soil_layer_thickness_mm[0],
#         stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#         latent_heat_vap_equ_factors=(abiotic_constants.latent_heat_vap_equ_factors),
#         molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#         specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#         saturation_vapour_pressure_factors=(
#             abiotic_simple_constants.saturation_vapour_pressure_factors
#         ),
#     )
#     ground_temperature_new = np.where(
#         ground_temperature_new > dewpoint_temperature,
#         ground_temperature_new,
#         dewpoint_temperature,
#     )

#     # Cap values
#     difference_canopy_air_temperature = canopy_temperature_new - air_temperature_ref
#     difference_ground_air_temperature = ground_temperature_new - air_temperature_ref
#     difference_canopy_air_temperature = np.where(
#         np.abs(difference_canopy_air_temperature) > 5.0,  # dTmax, input variable
#         5.0,
#         difference_canopy_air_temperature,
#     )
#     difference_ground_air_temperature = np.where(
#         np.abs(difference_ground_air_temperature) > 5.0,
#         5.0,
#         difference_ground_air_temperature,
#     )
#     canopy_temperature_new = air_temperature_ref + difference_canopy_air_temperature
#     ground_temperature_new = air_temperature_ref + difference_ground_air_temperature

#     # TODO Run convergence test, not implemented

#     # TODO Reassign canopy_temperature and ground_temperature using bwgt (backward
#     # weighting to apply when iteratively running the model (default 0.5))
#     bwgt = 0.5
#     canopy_temperature_mean = (
#         bwgt * canopy_temperature_mean + (1 - bwgt) * canopy_temperature_new
#     )
#     ground_temperature = (
# bwgt * ground_temperature + (1 - bwgt) * ground_temperature_new)

#     # Recalculate variables
#     temperature_average_air_canopy = (canopy_temperature_mean + air_temperature_ref)
# / 2
#     temperature_average_air_canopy_kelvin = (
#         core_constants.zero_Celsius + temperature_average_air_canopy
#     )
#     temperature_average_air_ground = (
#         canopy_temperature_mean + temperature_average_air_ground
#     ) / 2
#     molar_density_air = abiotic_tools.calculate_molar_density_air(
#         temperature=temperature_average_air_canopy,
#         atmospheric_pressure=atmospheric_pressure_ref,
#         standard_mole=core_constants.standard_mole,
#         standard_pressure=core_constants.standard_pressure,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#     )
#     specific_heat_air = abiotic_tools.calculate_specific_heat_air(
#         temperature=temperature_average_air_canopy,
#         molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#         specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#     )

#     # Calculate sensible heat flux
#     sensible_heat_flux = bwgt * sensible_heat_flux + (1 - bwgt) * (
#         air_heat_conductivity
#         * specific_heat_air
#         * (canopy_temperature_new - air_temperature_ref)
#     )

#     # Set limits to sensible heat flux
#     net_radiation = (
#         canopy_total_absorption
#         - core_constants.stefan_boltzmann_constant
#         * abiotic_constants.leaf_emissivity
#         * (canopy_temperature_new + 273.15) ** 4
#     )
#     sensible_heat_flux = np.where(
#         sensible_heat_flux > net_radiation, net_radiation, sensible_heat_flux
#     )

#     # Recalculate stability variables
#     monin_obukov_length = wind.calculate_monin_obukov_length(
#         air_temperature=temperature_average_air_canopy_kelvin,
#         friction_velocity=friction_velocity,
#         sensible_heat_flux=sensible_heat_flux,
#         zero_degree=core_constants.zero_Celsius,
#         specific_heat_air=specific_heat_air,
#         density_air=molar_density_air,
#         von_karman_constant=core_constants.von_karmans_constant,
#         gravity=core_constants.gravity,
#     )

#     stability_parameter = wind.calculate_stability_parameter(
#         reference_height=reference_height,
#         zero_plance_displacement=zero_plane_displacement,
#         monin_obukov_length=monin_obukov_length,
#     )

#     diabatic_factors = wind.calculate_diabatic_correction_factors(
#         stability_parameter=stability_parameter,
#         stability_formulation="Businger_1971",  # TODO
#     )

#     phih = wind.calculate_diabatic_influence_heat(
#         stability_parameter=stability_parameter,
#     )

#     # Set limits to diabatic coefficients
#     ln1 = np.log(
#         (reference_height - zero_plane_displacement) / roughness_length_momentum
#     )
#     ln2 = np.log(
#         (reference_height - zero_plane_displacement)
#         / (abiotic_constants.drag_coefficient * roughness_length_momentum)
#     )
#     diabatic_factors["psi_m"] = np.clip(
#         diabatic_factors["psi_m"], -0.9 * ln1, 0.9 * ln1
#     )
#     diabatic_factors["psi_h"] = np.clip(
#         diabatic_factors["psi_h"], -0.9 * ln2, np.minimum(0.9 * ln2, 0.9 * drag_limit)
#     )
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
#     output = {
#         "canopy_temperature": canopy_temperature_mean,
#         "ground_temperature": ground_temperature,
#         "sensible_heat_flux": sensible_heat_flux,
#         "ground_heat_flux": ground_heat_flux,
#         "net_radiation": net_radiation,
#         "psih": diabatic_factors["psi_h"],
#         "psim": diabatic_factors["psi_m"],
#         "phih": phih,
#         "monin_obukov_length": monin_obukov_length,
#         "friction_velocity": friction_velocity,
#         "canopy_shortwave_absorption": absorbed_shortwave_radiation[
#             "canopy_shortwave_absorption"
#         ],
#         "ground_shortwave_absorption": absorbed_shortwave_radiation[
#             "ground_shortwave_absorption"
#         ],
#         "albedo": absorbed_shortwave_radiation["albedo"],
#     }

#     return output


# r"""The ``models.abiotic.conductivities`` module calculates the conductivities for the
# energy balance of the Virtual Ecosystem based on :cite:t:`maclean_microclimc_2021`.
# """

# import numpy as np
# from numpy.typing import NDArray
# from xarray import DataArray

# from virtual_ecosystem.core.core_components import LayerStructure


# def interpolate_along_heights(
#     start_height: NDArray[np.float32],
#     end_height: NDArray[np.float32],
#     target_heights: NDArray[np.float32],
#     start_value: float | NDArray[np.float32],
#     end_value: float | NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Linear interpolation for given start and end values along a height axis.

#     This function can be used to lineraly interpolate atmospheric or soil variables
# such
#     as temperature or humidity for a set of user specified heights based on the top
# and
#     bottom values. Note that the start value has to be the surface and the end value
# has
#     to be above ground.

#     Args:
#         start_height: Starting heights of the interpolation range, [m].
#         end_height: Ending heights of the interpolation range, [m]
#         target_heights: Array of target heights with the first column representing
#             heights and subsequent columns representing additional dimensions, here
#             `cell_id`.
#         start_value: The value at the starting height.
#         end_value: The value at the ending height.

#     Returns:
#         Interpolated values corresponding to the target heights
#     """
#     # Ensure the target heights are within the range [start_height, end_height]
#     target_heights = np.clip(target_heights, start_height, end_height)

#     # Calculate the interpolation slope and intercept
#     slope = (end_value - start_value) / (end_height - start_height)
#     intercept = start_value - slope * start_height

#     # Interpolate values at the target heights
#     interpolated_values = slope * target_heights + intercept

#     return interpolated_values


# def initialise_conductivities(
#     layer_structure: LayerStructure,
#     layer_heights: DataArray,
#     initial_air_conductivity: float,
#     top_leaf_vapour_conductivity: float,
#     bottom_leaf_vapour_conductivity: float,
#     top_leaf_air_conductivity: float,
#     bottom_leaf_air_conductivity: float,
# ) -> dict[str, DataArray]:
#     r"""Initialise conductivities for first model time step, [mol m-2 s-1].

#     Air heat conductivity by turbulent convection (:math:`g_{t}`) is scaled by canopy
#     height and number of canopy layers (and hence distance between nodes). Leaf-air
#     vapour conductivity (:math:`g_{v}`) and leaf-air heat conductivity
# (:math:`g_{Ha}`)
#     are linearly interpolated between intial values.

#     The first value in each output represents conductivity between the air at 2m above
#     canopy and the highest canopy layer. The last (above ground) value represents
#     conductivity between the ground and the lowest canopy node.
#     TODO account for variable layer depths

#     Args:
#         layer_structure: the model layer structure instance.
#         layer_heights: layer heights, [m]
#         initial_air_conductivity: Initial value for heat conductivity by turbulent
#             convection in air, [mol m-2 s-1]
#         top_leaf_vapour_conductivity: Initial leaf vapour conductivity at the top of
# the
#             canopy, [mol m-2 s-1]
#         bottom_leaf_vapour_conductivity: Initial leaf vapour conductivity at the
#  bottom
#             of the canopy, [mol m-2 s-1]
#         top_leaf_air_conductivity: Initial leaf air heat conductivity at the top of
#  the
#             canopy, [mol m-2 s-1]
#         bottom_leaf_air_conductivity: Initial leaf air heat conductivity at the
#  surface,
#             [mol m-2 s-1]

#     Returns:
#         Heat conductivity in air of each canopy layer node, [mol m-2 s-1],
#         Leaf conductivity to vapour loss for each canopy layer node, [mol m-2 s-1],
#         Heat conductivity between air and leaf for each canopy layer node, [mol m-2
#  s-1]
#     """

#     # TODO - this [1] indexes the first canopy layer - that's poorly defined at the
#     #        moment (canopy top? first canopy layer closure? representative midpoint
#     #        height of the first canopy layer) and we don't have a firm structure to
#     #        index this properly yet.
#     canopy_height = layer_heights[1].to_numpy()
#     atmosphere_layers = layer_heights[layer_structure.index_atmosphere]
#     canopy_layers = layer_heights[layer_structure.index_canopy]
#     soil_layers = layer_heights[layer_structure.index_all_soil]

#     output = {}

#     # Initialise conductivity between air layers
#     air_conductivity = (
#         np.full((len(atmosphere_layers), len(canopy_height)),
# initial_air_conductivity)
#         * (len(atmosphere_layers) / canopy_height)
#         * 2
#         / len(atmosphere_layers)
#     )
#     air_conductivity[-1] *= 2
#     air_conductivity[0] *= (canopy_height / len(atmosphere_layers)) * 0.5

#     output["air_heat_conductivity"] = layer_structure.from_template()
#     output["air_heat_conductivity"][layer_structure.index_atmosphere] =
# air_conductivity

#     # Initialise leaf vapour conductivity
#     leaf_vapour_conductivity = interpolate_along_heights(
#         start_height=layer_heights[-(len(soil_layers) + 1)].to_numpy(),
#         end_height=layer_heights[0].to_numpy(),
#         target_heights=layer_heights[canopy_layers.indexes].to_numpy(),
#         start_value=top_leaf_vapour_conductivity,
#         end_value=bottom_leaf_vapour_conductivity,
#     )
#     output["leaf_vapour_conductivity"] = layer_structure.from_template()
#     output["leaf_vapour_conductivity"][layer_structure.index_canopy] = (
#         leaf_vapour_conductivity
#     )

#     # Initialise leaf air heat conductivity
#     leaf_air_conductivity = interpolate_along_heights(
#         start_height=layer_heights[-(len(soil_layers) + 1)].to_numpy(),
#         end_height=layer_heights[0].to_numpy(),
#         target_heights=layer_heights[canopy_layers.indexes].to_numpy(),
#         start_value=top_leaf_air_conductivity,
#         end_value=bottom_leaf_air_conductivity,
#     )
#     output["leaf_air_heat_conductivity"] = layer_structure.from_template()
#     output["leaf_air_heat_conductivity"][layer_structure.index_canopy] = (
#         leaf_air_conductivity
#     )

#     return output


# def calculate_air_heat_conductivity_above(
#     height_above_canopy: NDArray[np.float32],
#     zero_displacement_height: NDArray[np.float32],
#     canopy_height: NDArray[np.float32],
#     friction_velocity: NDArray[np.float32],
#     molar_density_air: NDArray[np.float32],
#     diabatic_correction_heat: NDArray[np.float32],
#     von_karmans_constant: float,
# ) -> NDArray[np.float32]:
#     r"""Calculate air heat conductivity by turbulent convection above canopy.

#     Heat conductance, :math:`g_{t}` between any two heights :math:`z_{1}` and
#     :math:`z_{0}` above-canopy is given by

#     .. math::
#       g_{t} = \frac {0.4 \hat{\rho} u^{*}}{ln(\frac{z_{1} - d}{z_{0} - d}) + \Psi_{H}}

#    where :math:`\hat{\rho}` is the molar density or air, :math:`u^{*}` is the friction
#     velocity, :math:`d` is the zero displacement height, and :math:`\Psi_{H}` is the
#     diabatic correction factor for heat.

#     Args:
#         height_above_canopy: Height above canopy, [m]
#         zero_displacement_height: Zero displacement height, [m]
#         canopy_height: Canopy height, [m]
#         friction_velocity: Friction velocity, dimensionless
#         molar_density_air: Molar density of air, [mole m-3]
#         diabatic_correction_heat: Diabatic correction factor for heat, dimensionless
#         von_karmans_constant: Von Karman constant, unitless

#     Returns:
#         Air heat conductivity by turbulent convection above canopy, [mol m-2 s-1]
#     """

#     return (von_karmans_constant * molar_density_air * friction_velocity) / (
#         np.log(height_above_canopy - zero_displacement_height)
#         / (canopy_height - zero_displacement_height)
#         + diabatic_correction_heat
#     )


# def calculate_molar_conductance_above_canopy(
#     friction_velocity: NDArray[np.float32],
#     zero_plane_displacement: NDArray[np.float32],
#     roughness_length_momentum: NDArray[np.float32],
#     reference_height: NDArray[np.float32],
#     molar_density_air: NDArray[np.float32],
#     diabatic_correction_heat: NDArray[np.float32],
#     minimum_conductance: float,
#     von_karmans_constant: float,
# ) -> NDArray[np.float32]:
#     r"""Calculate molar conductance above canopy, gt.

#     Heat conductance, :math:`g_{t}` between any two heights :math:`z_{1}` and
#     :math:`z_{0}` above-canopy is given by
#     .. math::
#         g_{t} = \frac {0.4 \hat{\rho} u^{*}}{ln(\frac{z_{1} - d}{z_{0} - d}) +
#  \Psi_{H}}
#     where :math:`\hat{\rho}` is the molar density or air, :math:`u^{*}` is the
# friction
#     velocity, :math:`d` is the zero displacement height, and :math:`\Psi_{H}` is the
#     diabatic correction factor for heat.

#     Args:
#         friction_velocity: Friction velocity[m s-1]
#         zero_plane_displacement: Zero-plane displacement height, [m]
#         roughness_length_momentum: Roughness length momenturm, [m]
#         reference_height: Reference height, [m]
#         molar_density_air: Molar density of air
#         diabatic_correction_heat: Stability correction factor for heat, []
#         minimum_conductance: Minimum conductance, [m s-1]
#         von_karmans_constant: Von Karman constant, unitless

#     Returns:
#         molar conductance above canopy, [m s-1]
#     """
#     # Heat exchange surface height
#     z0 = 0.2 * roughness_length_momentum + zero_plane_displacement
#     ln = np.log(
#         (reference_height - zero_plane_displacement) / (z0 - zero_plane_displacement)
#     )
#     molar_conductance = (
#         von_karmans_constant * molar_density_air * friction_velocity
#     ) / (ln + diabatic_correction_heat)

#     # Ensure conductance is not less than minimum_conductance
#     return np.maximum(molar_conductance, minimum_conductance)


# def calculate_free_convection(
#     leaf_dimension: float,
#     sensible_heat_flux: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate free convection, gha.

#     Args:
#         leaf_dimension: Leaf dimension (characteristic length), [m]
#         sensible_heat_flux: Sensible heat flux, [W m-2]

#     Returns:
#         free convection coefficient, gha
#     """
#     d = 0.71 * leaf_dimension
#     dt = 0.7045388 * np.power((d * np.power(sensible_heat_flux, 4)), 0.2)
#     gha = 0.0375 * np.power(dt / d, 0.25)

#     # Ensure gha is not less than 0.1
#     return np.maximum(gha, 0.1)


# def calculate_stomatal_conductance(
#     shortwave_radiation: NDArray[np.float32],
#     maximum_stomatal_conductance: float,
#     half_saturation_stomatal_conductance: float,
# ) -> NDArray[np.float32]:
#     """Calculate the stomatal conductance.

#     Args:
#         shortwave_radiation: Shortwave radiation absorbed by the leaves, [W m-2]
#         maximum_stomatal_conductance: Maximum stomatal conductance, [mol m-2 s-1]
#         half_saturation_stomatal_conductance: Half-saturation point for stomatal
#             conductance, [W m-2]

#     Returns:
#         Stomatal conductance (gs), [mol m-2 s-1]
#     """

#     rpar = shortwave_radiation * 4.6  # Photosynthetically active radiation (PAR)
#     return (maximum_stomatal_conductance * rpar) / (
#         rpar + half_saturation_stomatal_conductance
#     )


# def calculate_air_heat_conductivity_canopy(
#     attenuation_coefficient: NDArray[np.float32],
#     mean_mixing_length: NDArray[np.float32],
#     molar_density_air: NDArray[np.float32],
#     upper_height: NDArray[np.float32],
#     lower_height: NDArray[np.float32],
#     relative_turbulence_intensity: NDArray[np.float32],
#     top_of_canopy_wind_speed: NDArray[np.float32],
#     diabatic_correction_momentum: NDArray[np.float32],
#     canopy_height: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#   r"""Calculate air heat conductivity by turbulent convection in canopy,[mol m-2 s-1].

#   Within-canopy heat conductance (:math:`g_{t}`) between any two heights :math:`z_{1}`
#     and :math:`z_{0}` below-canopy is given by

#     .. math::
#         g_{t} = \frac{u_{h}l_{m}i_{w}a}
#         {(exp(\frac{-a_{z_{0}}}{h-1}) - exp(\frac{-a_{z_{1}}}{h-1})) \Phi_{H}}


#     where :math:`u_{h}` is wind speed at the top of the canopy at height :math:`h`,
#     :math:`a` is a wind attenuation coefficient, :math:`i_{w}` is a coefficient
#     describing relative turbulence intensity, :math:`l_{m}` is the mean mixing length,
#   equivalent to the free space between the leaves and stems, and :math:`\Phi_{H}` is a
#     within-canopy diabatic correction factor for heat.

#     TODO better tests for different conditions

#     Args:
#         attenuation_coefficient: Wind attenuation coefficient, dimensionless
#         mean_mixing_length: Mixing length for canopy air transport, [m]
#         molar_density_air: Molar density of air, [mol m-3]
#         upper_height: Height of upper layer, [m]
#         lower_height: Height of lower layer, [m]
#         relative_turbulence_intensity: Relative turbulence intensity, dimensionless
#         top_of_canopy_wind_speed: Top of canopy wind speed, [m s-1]
#         diabatic_correction_momentum: Diabatic correction factor for momentum,
#             dimensionless
#         canopy_height: Canopy height, [m]

#     Returns:
#        air heat conductivity by turbulent convection in the canopy, [mol m-2 s-1]
#     """
#     term1 = (
#         mean_mixing_length
#         * relative_turbulence_intensity
#         * molar_density_air
#         * top_of_canopy_wind_speed
#         * attenuation_coefficient
#     ) / diabatic_correction_momentum

#     term2 = np.exp(-attenuation_coefficient * (lower_height / canopy_height - 1))
#     term3 = np.exp(-attenuation_coefficient * (upper_height / canopy_height - 1))
#     return term1 / (term2 - term3)


# def calculate_leaf_air_heat_conductivity(
#     temperature: NDArray[np.float32],
#     wind_speed: NDArray[np.float32],
#     characteristic_dimension_leaf: float | NDArray[np.float32],
#     temperature_difference: NDArray[np.float32],
#     molar_density_air: NDArray[np.float32],
#     kinematic_viscosity_parameters: list[float],
#     thermal_diffusivity_parameters: list[float],
#     grashof_parameter: float,
#     forced_conductance_parameter: float,
#     positive_free_conductance_parameter: float,
#     negative_free_conductance_parameter: float,
# ) -> NDArray[np.float32]:
#   r"""Calculate forced or free laminer conductance between leaf and air,[mol m-2 s-1].

#     When wind speeds are moderate to high, conduction between the leaf and air
#     :math:`g_{Ha}` is predominantly under laminar forced convection and from e.g.
#     :cite:t:`campbell_introduction_2012` is given by

#     .. math:: g_{Ha} = \frac {0.664 \hat{\rho} D_{H} R_{e}^{0.5} P_{r}^{0.5}}{x_{d}}

#     where :math:`D_{H}` is thermal diffusivity, :math:`x_{d}` is the characteristic
#     dimension of the leaf, :math:`\hat{\rho}` is the molar density of air,
#     :math:`R_{e}` is the Reynolds number, and :math:`P_{r}` is the Prandtl number.

#     When wind speeds are low, an expression that is adequate for leaves is given by
#     (Campbell and Norman, 2012)

#     .. math:: g_{Ha} = \frac{0.54 \hat{\rho} D_{H} (G_{r}P_{r})^{0.25}}{x_{d}}

#   where :math:`G_{r}` is the Grashof number. When the leaf is cooler than the air, the
#     heat transfer is only half as efficient so the constant 0.54 becomes 0.26.

#     TODO better tests for different conditions

#     Args:
#         temperature: Temperature, [C]
#         wind_speed: Wind speed, [m s-1]
#        characteristic_dimension_leaf: Chacteristic dimension of leaf, typically around
#             0.7 * leaf width, [m]. This parameter can be a float, a 2D-array with one
#             value per grid cell, or a 3D-array with one value for each layer.
#        temperature_difference: Estimate of temperature differences of surface and air,
#           e.g. from previous time step, see notes in :cite:t:`maclean_microclimc_2021`
#        molar_density_air: Molar density of air, [mol m-3]
#       kinematic_viscosity_parameters: Parameters in calculation of kinematic viscosity
#       thermal_diffusivity_parameters: Parameters in calculation of thermal diffusivity
#         grashof_parameter: Parameter in calculation of Grashof number
#         forced_conductance_parameter: Parameter in calculation of forced conductance
#         positive_free_conductance_parameter: Parameter in calculation of free
#             conductance for positive temperature difference
#         negative_free_conductance_parameter: Parameter in calculation of free
#             conductance for negative temperature difference

#     Returns:
#         Leaf air heat conductance, [mol m-2 s-1]
#     """

#     temperature_k = temperature + 273.15
#     kinematic_viscosity = (
#         kinematic_viscosity_parameters[0] * temperature_k
#         - kinematic_viscosity_parameters[1]
#     ) / 10**6
#     thermal_diffusivity = (
#         thermal_diffusivity_parameters[0] * temperature_k
#         - thermal_diffusivity_parameters[1]
#     ) / 10**6
#     grashof_number = (
#         grashof_parameter
#         * characteristic_dimension_leaf**3
#         * np.abs(temperature_difference)
#     ) / (temperature_k * kinematic_viscosity**2)
#     reyolds_number = wind_speed * characteristic_dimension_leaf / kinematic_viscosity
#     prandtl_number = kinematic_viscosity / thermal_diffusivity

#     # Forced conductance
#     forced_conductance = (
#         forced_conductance_parameter
#         * thermal_diffusivity
#         * molar_density_air
#         * reyolds_number**0.5
#         * prandtl_number ** (1 / 3)
#     ) / characteristic_dimension_leaf

#     # Free conductance
#     m = np.where(
#         temperature_difference > 0,
#         positive_free_conductance_parameter,
#         negative_free_conductance_parameter,
#     )
#     free_conductance = (
#         m
#         * molar_density_air
#         * thermal_diffusivity
#         * (grashof_number * prandtl_number) ** (1 / 4)
#     ) / characteristic_dimension_leaf

#     # Set to whichever is higher
#     conductance = np.where(
#         forced_conductance > free_conductance, forced_conductance, free_conductance
#     )

#     return conductance


# def calculate_leaf_vapour_conductivity(
#     leaf_air_conductivity: NDArray[np.float32],
#     stomatal_conductance: float | NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     r"""Calculate leaf air conductivity for vapour, [mol m-2 s-1].

#       The conductance for vapour loss from leaves :math:`g_{v}` depends on stomatal
#     conductance :math:`g_{c}` and heat conductivity between air and leaf
#  :math:`g_{Ha}`:

#       .. math:: g_{v} = \frac{1}{(\frac{1}{g_{Ha}} + \frac{1}{g_{c}})

#       :cite:p:`maclean_microclimc_2021`.

#     Args:
#           leaf_air_conductivity: Heat conductivity between air and leaf, [mol m-2 s-1]
#           stomatal_conductance: Stomatal conductance, [mol m-2 s-1]

#     Returns:
#           Leaf vapour conductivity, [mol m-2 s-1]
#     """
#     return 1 / ((1 / leaf_air_conductivity) + (1 / stomatal_conductance))


# def calculate_current_conductivities(
#     data: Data,
#     characteristic_dimension_leaf: float | NDArray[np.float32],
#     von_karmans_constant: float,
#     abiotic_constants: AbioticConsts,
# ) -> dict[str, NDArray[np.float32]]:
#     """Calculate conductivities based on current reference data.

#     This function calculates the conductivites for heat and vapour between air layers
#     and the leaf and surrounding atmosphere for the current time step. The first value
#   on the vertical axis is 2m above the canopy, the second value corresponds to the top
#     of the canopy.

#     The data object must provide the following variables:

#     * layer_heights: layer heights, [m]
#     * air_temperature, [C]
#     * canopy_temperature, [C]
#     * attenuation_coefficient: Wind attenuation coefficient, dimensionless
#     * mean_mixing_length: Mixing length for canopy air transport, [m]
#     * molar_density_air: Molar density of air, [mol m-3]
#     * relative_turbulence_intensity: Relative turbulence intensity, dimensionless
#     * wind_speed: wind speed, [m s-1]
#     * stomatal_conductance: Stomatal conductance, [mmol m-2 s-1]
#     * zero_displacement_height: Zero displacement height, [m]
#     * friction_velocity: Friction velocity
#     * diabatic_correction_heat: Diabatic correction for heat in canopy

#     Args:
#         data: The core data object.
#       characteristic_dimension_leaf: Chacteristic dimension of leaf, typically around
#             0.7 * leaf width, [m]. This parameter can be a float, a 2D-array with one
#             value per grid cell, or a 3D-array with one value for each layer.
#         von_karmans_constant: Von Karman constant
#         abiotic_constants: set of abiotic constants

#     Returns:
#         dictionnary of conductivities, [mol m-2 s-1]
#     """

#     output = {}

#     # Air heat conductivity, gt
#     air_heat_conductivity_above = calculate_air_heat_conductivity_above(
#         height_above_canopy=data["layer_heights"].isel(layers=0).to_numpy(),
#         zero_displacement_height=data["zero_displacement_height"].to_numpy(),
#         canopy_height=data["layer_heights"].isel(layers=1).to_numpy(),
#         friction_velocity=data["friction_velocity"].to_numpy(),
#         molar_density_air=data["molar_density_air"][0].to_numpy(),
#         diabatic_correction_heat=data["diabatic_correction_heat_canopy"].to_numpy(),
#         von_karmans_constant=von_karmans_constant,
#     )
#     current_air_heat_conductivity = []
#     for layer in np.arange(0, len(data["layer_heights"]) - 1):
#         result = calculate_air_heat_conductivity_canopy(
#             attenuation_coefficient=data["attenuation_coefficient"][layer].to_numpy(),
#             mean_mixing_length=data["mean_mixing_length"].to_numpy(),
#             molar_density_air=data["molar_density_air"][layer].to_numpy(),
#             upper_height=data["layer_heights"].isel(layers=layer).to_numpy(),
#             lower_height=data["layer_heights"].isel(layers=layer + 1).to_numpy(),
#             relative_turbulence_intensity=(
#                 data["relative_turbulence_intensity"][layer].to_numpy()
#             ),
#             top_of_canopy_wind_speed=data["wind_speed"].isel(layers=1).to_numpy(),
#             diabatic_correction_momentum=(
#                 data["diabatic_correction_momentum_canopy"].to_numpy()
#             ),
#             canopy_height=data["layer_heights"].isel(layers=1).to_numpy(),
#         )
#         current_air_heat_conductivity.append(result)

#     output["air_heat_conductivity"] = np.vstack(
#         [air_heat_conductivity_above, np.vstack(current_air_heat_conductivity)]
#     )

#     # Air heat conductivity between layers and reference height
#     current_air_heat_conductivity_ref = []
#     for layer in np.arange(0, len(data["layer_heights"]) - 1):
#         result = calculate_air_heat_conductivity_canopy(
#             attenuation_coefficient=data["attenuation_coefficient"][layer].to_numpy(),
#             mean_mixing_length=data["mean_mixing_length"].to_numpy(),
#             molar_density_air=data["molar_density_air"][layer].to_numpy(),
#             upper_height=data["layer_heights"].isel(layers=0).to_numpy(),
#             lower_height=data["layer_heights"].isel(layers=layer + 1).to_numpy(),
#             relative_turbulence_intensity=(
#                 data["relative_turbulence_intensity"][layer].to_numpy()
#             ),
#             top_of_canopy_wind_speed=data["wind_speed"].isel(layers=1).to_numpy(),
#             diabatic_correction_momentum=(
#                 data["diabatic_correction_momentum_canopy"].to_numpy()
#             ),
#             canopy_height=data["layer_heights"].isel(layers=1).to_numpy(),
#         )
#         current_air_heat_conductivity_ref.append(result)

#     output["conductivity_from_ref_height"] = np.vstack(
#         [
#             np.repeat(np.nan, data.grid.n_cells),
#             np.vstack(current_air_heat_conductivity_ref),
#         ]
#     )

#     # Leaf air heat conductivity, gha
#     current_leaf_air_heat_conductivity = calculate_leaf_air_heat_conductivity(
#         temperature=data["air_temperature"].to_numpy(),
#         wind_speed=data["wind_speed"].to_numpy(),
#         characteristic_dimension_leaf=characteristic_dimension_leaf,
#         temperature_difference=(
#             data["canopy_temperature"] - data["air_temperature"]
#         ).to_numpy(),
#         molar_density_air=data["molar_density_air"].to_numpy(),
#       kinematic_viscosity_parameters=abiotic_constants.kinematic_viscosity_parameters,
#       thermal_diffusivity_parameters=abiotic_constants.thermal_diffusivity_parameters,
#         grashof_parameter=abiotic_constants.grashof_parameter,
#         forced_conductance_parameter=abiotic_constants.forced_conductance_parameter,
#         positive_free_conductance_parameter=(
#             abiotic_constants.positive_free_conductance_parameter
#         ),
#         negative_free_conductance_parameter=(
#             abiotic_constants.negative_free_conductance_parameter
#         ),
#     )
#     output["leaf_air_heat_conductivity"] = current_leaf_air_heat_conductivity

#     # Leaf vapour conductivity, gv
#     current_leaf_vapour_conductivity = calculate_leaf_vapour_conductivity(
#         leaf_air_conductivity=current_leaf_air_heat_conductivity,
#         stomatal_conductance=data["stomatal_conductance"].to_numpy(),
#     )
#     output["leaf_vapour_conductivity"] = current_leaf_vapour_conductivity

#     return output

# r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
# Virtual Ecosystem. Given that the time increments of the model are an hour or longer,
# we can assume that below-canopy heat and vapour exchange attain steady state and heat
# storage in the canopy does not need to be simulated explicitly.
# (For application where very fine-temporal resolution data might be needed, heat and
# vapour exchange must be modelled as transient processes, and heat storage by the
#  canopy,
# and the exchange of heat between different layers of the canopy, must be considered
# explicitly, see :cite:t:`maclean_microclimc_2021`. This is currently not implemented.)

# Under steady-state, the balance equation for the leaves in each canopy layer is as
# follows (after :cite:t:`maclean_microclimc_2021`):

# .. math::
#     R_{abs} - R_{em} - H - \lambda E
#     = R_{abs} - \epsilon_{s} \sigma T_{L}^{4} - c_{P}g_{Ha}(T_{L} - T_{A})
#     - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{A}} = 0

# where :math:`R_{abs}` is absorbed radiation, :math:`R_{em}` emitted radiation,
#  :math:`H`
# the sensible heat flux, :math:`\lambda E` the latent heat flux, :math:`\epsilon_{s}`
#  the
# emissivity of the leaf, :math:`\sigma` the Stefan-Boltzmann constant, :math:`T_{L}`
#  the
# absolute temperature of the leaf, :math:`T_{A}` the absolute temperature of the air
# surrounding the leaf, :math:`\lambda` the latent heat of vapourisation of water,
# :math:`e_{L}` the effective vapour pressure of the leaf, :math:`e_{A}` the vapour
# pressure of air and :math:`p_{A}` atmospheric pressure. :math:`g_{Ha}` is the heat
# conductance between leaf and atmosphere, :math:`g_{v}` represents the conductance
# for vapour loss from the leaves as a function of the stomatal conductance
#  :math:`g_{c}`.

# A challenge in solving this equation is the dependency of latent heat and emitted
# radiation on leaf temperature. We use a linearisation approach to solve the equation
#  for
# leaf temperature and air temperature simultaneously after
# :cite:t:`maclean_microclimc_2021`.

# The soil energy balance functions are described in
# :mod:`~virtual_ecosystem.models.abiotic.soil_energy_balance`.

# The conductivities are calculated as described in
# :mod:`~virtual_ecosystem.models.abiotic.conductivities`.
# """

# import numpy as np
# from numpy.typing import NDArray
# from xarray import DataArray

# from virtual_ecosystem.core.core_components import LayerStructure
# from virtual_ecosystem.models.abiotic.abiotic_tools import (
#     calculate_latent_heat_vapourisation,
#     calculate_specific_heat_air,
# )


# def initialise_absorbed_radiation(
#     topofcanopy_radiation: NDArray[np.float32],
#     leaf_area_index: NDArray[np.float32],
#     layer_heights: NDArray[np.float32],
#     light_extinction_coefficient: float,
# ) -> NDArray[np.float32]:
#     r"""Calculate initial light absorption profile.

#     This function calculates the fraction of radiation absorbed by a multi-layered
#     canopy based on its leaf area index (:math:`LAI`) and extinction coefficient
#     (:math:`k`) at each layer, the depth of each measurement (:math:`z`), and the
#     incoming light intensity at the top of the canopy (:math:`I_{0}`). The
#     implementation based on Beer's law:

#     .. math:: I(z) = I_{0} * e^{(-k * LAI * z)}

#     Args:
#         topofcanopy_radiation: Top of canopy radiation shortwave radiation, [W m-2]
#         leaf_area_index: Leaf area index of each canopy layer, [m m-1]
#         layer_heights: Layer heights, [m]
#         light_extinction_coefficient: Light extinction coefficient, [m-1]

#     Returns:
#         Shortwave radiation absorbed by canopy layers, [W m-2]
#     """
#     # Calculate the depth of each layer, [m]
#     layer_depths = np.abs(np.diff(layer_heights, axis=0, append=0))

#     # Calculate the light extinction for each layer
#     layer_extinction = np.exp(
#         -0.01 * light_extinction_coefficient * layer_depths * leaf_area_index
#     )

#     # Calculate how much light penetrates through the canopy, [W m-2]
#     cumulative_extinction = np.cumprod(layer_extinction, axis=0)
#     penetrating_radiation = cumulative_extinction * topofcanopy_radiation

#     # Calculate how much light is absorbed in each layer, [W m-2]
#     absorbed_radiation = np.abs(
#         np.diff(
#             penetrating_radiation,
#             prepend=np.expand_dims(topofcanopy_radiation, axis=0),
#             axis=0,
#         )
#     )

#     return absorbed_radiation


# def initialise_canopy_temperature(
#     air_temperature: NDArray[np.float32],
#     absorbed_radiation: NDArray[np.float32],
#     canopy_temperature_ini_factor: float,
# ) -> NDArray[np.float32]:
#     """Initialise canopy temperature.

#     Args:
#         air_temperature: Air temperature, [C]
#         canopy_temperature_ini_factor: Factor used to initialise canopy temperature
#  as a
#             function of air temperature and absorbed shortwave radiation
#         absorbed_radiation: Shortwave radiation absorbed by canopy, [W m-2]

#     Returns:
#         Initial canopy temperature, [C]
#     """
#     return air_temperature + canopy_temperature_ini_factor * absorbed_radiation


# def initialise_canopy_and_soil_fluxes(
#     air_temperature: DataArray,
#     topofcanopy_radiation: DataArray,
#     leaf_area_index: DataArray,
#     layer_heights: DataArray,
#     layer_structure: LayerStructure,
#     light_extinction_coefficient: float,
#     canopy_temperature_ini_factor: float,
# ) -> dict[str, DataArray]:
#     """Initialise canopy temperature and energy fluxes.

#     This function initializes the following variables to run the first step of the
#     energy balance routine: absorbed radiation (canopy), canopy temperature, sensible
#     and latent heat flux (canopy and soil), and ground heat flux.

#     Args:
#         air_temperature: Air temperature, [C]
#         topofcanopy_radiation: Top of canopy radiation, [W m-2]
#         leaf_area_index: Leaf area index, [m m-2]
#         layer_heights: Layer heights, [m]
#         layer_structure: Instance of LayerStructure
#         light_extinction_coefficient: Light extinction coefficient for canopy
#         canopy_temperature_ini_factor: Factor used to initialise canopy temperature
#  as a
#             function of air temperature and absorbed shortwave radiation

#     Returns:
#         Dictionary with absorbed radiation (canopy), canopy temperature, sensible
#             and latent heat flux (canopy and soil), and ground heat flux [W m-2].
#     """

#     output = {}

#     # Get variables within filled canopy layers
#     leaf_area_index_true = leaf_area_index[layer_structure.index_filled_canopy]
#     layer_heights_canopy = layer_heights[layer_structure.index_filled_canopy]
#     air_temperature_canopy = air_temperature[layer_structure.index_filled_canopy]

#     # Initialize absorbed radiation DataArray
#     absorbed_radiation = DataArray(
#         np.full_like(layer_heights, np.nan),
#         dims=layer_heights.dims,
#         coords=layer_heights.coords,
#         name="canopy_absorption",
#     )

#     # Calculate absorbed radiation
#     initial_absorbed_radiation = initialise_absorbed_radiation(
#         topofcanopy_radiation=topofcanopy_radiation.to_numpy(),
#         leaf_area_index=leaf_area_index_true.to_numpy(),
#         layer_heights=layer_heights_canopy.to_numpy(),
#         light_extinction_coefficient=light_extinction_coefficient,
#     )

#     # Replace np.nan with new values and write in output dict
#     absorbed_radiation[layer_heights_canopy.indexes] = initial_absorbed_radiation
#     output["canopy_absorption"] = absorbed_radiation

#     # Initialize canopy temperature DataArray
#     canopy_temperature = DataArray(
#         np.full_like(layer_heights, np.nan),
#         dims=layer_heights.dims,
#         coords=layer_heights.coords,
#         name="canopy_temperature",
#     )

#     # Calculate initial temperature and write in output dict
#     initial_canopy_temperature = initialise_canopy_temperature(
#         air_temperature=air_temperature_canopy.to_numpy(),
#         absorbed_radiation=initial_absorbed_radiation,
#         canopy_temperature_ini_factor=canopy_temperature_ini_factor,
#     )
#     canopy_temperature[layer_structure.index_filled_canopy] =
# initial_canopy_temperature
#     output["canopy_temperature"] = canopy_temperature

#     # Initialise sensible heat flux with zeros and write in output dict
#     sensible_heat_flux = DataArray(
#         np.full_like(layer_heights, np.nan),
#         dims=layer_heights.dims,
#         coords=layer_heights.coords,
#         name="sensible_heat_flux",
#     )
#     sensible_heat_flux[layer_structure.index_filled_canopy] = 0.001
#     sensible_heat_flux[layer_structure.index_topsoil] = 0.001
#     output["sensible_heat_flux"] = sensible_heat_flux

#     # Initialise latent heat flux with zeros and write in output dict
#     output["latent_heat_flux"] = sensible_heat_flux.copy().rename("latent_heat_flux")

#     # Initialise latent heat flux with zeros and write in output dict
#     ground_heat_flux = DataArray(
#         np.full_like(layer_heights, np.nan),
#         dims=layer_heights.dims,
#         coords=layer_heights.coords,
#         name="ground_heat_flux",
#     )
#     ground_heat_flux[layer_structure.index_topsoil] = 0.001
#     output["ground_heat_flux"] = ground_heat_flux

#     return output


# def calculate_longwave_emission(
#     temperature: NDArray[np.float32],
#     emissivity: float | NDArray[np.float32],
#     stefan_boltzmann: float,
# ) -> NDArray[np.float32]:
#     """Calculate longwave emission using the Stefan Boltzmann law, [W m-2].

#     According to the Stefan Boltzmann law, the amount of radiation emitted per unit
# time
#     from the area of a black body at absolute temperature is directly proportional to
#     the fourth power of the temperature. Emissivity (which is equal to absorptive
# power)
#     lies between 0 to 1.

#     Args:
#         temperature: Temperature, [K]
#         emissivity: Emissivity, dimensionless
#         stefan_boltzmann: Stefan Boltzmann constant, [W m-2 K-4]

#     Returns:
#         Longwave emission, [W m-2]
#     """
#     return emissivity * stefan_boltzmann * temperature**4


# def calculate_slope_of_saturated_pressure_curve(
#     temperature: NDArray[np.float32],
#     saturated_pressure_slope_parameters: list[float],
# ) -> NDArray[np.float32]:
#     r"""Calculate slope of the saturated pressure curve.

#     Args:
#         temperature: Temperature, [C]
#         saturated_pressure_slope_parameters: List of parameters to calcualte
#             the slope of the saturated vapour pressure curve

#     Returns:
#         Slope of the saturated pressure curve, :math:`\Delta_{v}`
#     """

#     return (
#         saturated_pressure_slope_parameters[0]
#         * (
#             saturated_pressure_slope_parameters[1]
#             * np.exp(
#                 saturated_pressure_slope_parameters[2]
#                 * temperature
#                 / (temperature + saturated_pressure_slope_parameters[3])
#             )
#         )
#         / (temperature + saturated_pressure_slope_parameters[3]) ** 2
#     )


# def calculate_surface_temperature(
#     total_absorbed_radiation: NDArray[np.float32],
#     heat_conductivity: NDArray[np.float32],
#     vapour_conductivity: NDArray[np.float32],
#     surface_temperature: NDArray[np.float32],
#     temperature_average_air_surface: NDArray[np.float32],
#     atmospheric_pressure: NDArray[np.float32],
#     effective_vapour_pressure_air: NDArray[np.float32],
#     surface_emissivity: float,
#     ground_heat_flux: NDArray[np.float32],
#     relative_humidity: NDArray[np.float32],
#     stefan_boltzmann_constant: float,
#     celsius_to_kelvin: float,
#     latent_heat_vap_equ_factors: list[float],
#     molar_heat_capacity_air: float,
#     specific_heat_equ_factors: list[float],
#     saturation_vapour_pressure_factors: list[float],
# ) -> float:
#     """Calculate soil or canopy temperature with Penman-Montheith equation.

#     Args:
#         total_absorbed_radiation: Absorbed shortwave and longwave radiation, [W m-2]
#         heat_conductivity: Heat conductivity of surface
#         vapour_conductivity: Vapour conductivity of surface
#         surface_temperature: Surface temperature, [C]
#         temperature_average_air_surface: Average between air temperature and surface
#             temperature, [C]  # tair+tleaf/2
#         atmospheric_pressure: Atmospheric pressure, [kPa]
#         effective_vapour_pressure_air: Effective vapour pressure of air
#         surface_emissivity: Surface emissivity
#         ground_heat_flux: Ground heat flux, [W m-2]
#         relative_humidity: Relative humidity
#         stefan_boltzmann_constant: Stefan Boltzmann constant
#         celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
#             temperature in Kelvin
#         latent_heat_vap_equ_factors: Factors in calculation of latent heat of
#             vapourisation
#         molar_heat_capacity_air: Molar heat capacity of air, [J mol-1 K-1]
#         specific_heat_equ_factors: Factors in calculation of molar specific heat of
# air
#         saturation_vapour_pressure_factors: factors in calculation of saturation
# vapour
#             pressure

#     Returns:
#         surface temperature, [C]
#     """

#     emitted_radiation = (
#         surface_emissivity
#         * stefan_boltzmann_constant
#         * (surface_temperature + celsius_to_kelvin) ** 4
#     )
#     latent_heat_vapourization = calculate_latent_heat_vapourisation(
#         temperature=temperature_average_air_surface,
#         celsius_to_kelvin=celsius_to_kelvin,
#         latent_heat_vap_equ_factors=latent_heat_vap_equ_factors,
#     )

#     specific_heat_air = calculate_specific_heat_air(
#         temperature=temperature_average_air_surface,
#         molar_heat_capacity_air=molar_heat_capacity_air,
#         specific_heat_equ_factors=specific_heat_equ_factors,
#     )
#     saturation_vapour_pressure = calculate_saturation_vapour_pressure(
#         temperature=DataArray(surface_temperature),
#         saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
#     )
#     vapour_pressure_deficit = saturation_vapour_pressure -
# effective_vapour_pressure_air
#     radiative_transfer = (
#         4
#         * surface_emissivity
#         * stefan_boltzmann_constant
#         * (temperature_average_air_surface + celsius_to_kelvin) ** 3
#     ) / specific_heat_air

#     saturation_vapour_pressure_plus = calculate_saturation_vapour_pressure(
#         temperature=DataArray(temperature_average_air_surface + 0.5),
#         saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
#     )
#     saturation_vapour_pressure_minus = calculate_saturation_vapour_pressure(
#         temperature=DataArray(temperature_average_air_surface - 0.5),
#         saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
#     )
#     slope_saturation_vapour_pressure_curve = (
#         saturation_vapour_pressure_plus - saturation_vapour_pressure_minus
#     )
#     new_surface_temperature = surface_temperature + (
#         (
#             total_absorbed_radiation
#             - emitted_radiation
#             - latent_heat_vapourization
#             * (vapour_conductivity / atmospheric_pressure)
#             * vapour_pressure_deficit
#             * relative_humidity
#             - ground_heat_flux
#         )
#         / (
#             specific_heat_air * (heat_conductivity + radiative_transfer)
#             + latent_heat_vapourization
#             * (vapour_conductivity / atmospheric_pressure)
#             * slope_saturation_vapour_pressure_curve
#             * relative_humidity
#         )
#     )
#     return new_surface_temperature


# def calculate_leaf_and_air_temperature(
#     data: Data,
#     time_index: int,
#     layer_structure: LayerStructure,
#     abiotic_constants: AbioticConsts,
#     abiotic_simple_constants: AbioticSimpleConsts,
#     core_constants: CoreConsts,
# ) -> dict[str, DataArray]:
#     r"""Calculate leaf and air temperature under steady state.

#     The air temperature surrounding the leaf :math:`T_{A}` is assumed to be influenced
#     by leaf temperature :math:`T_{L}`, soil temperature :math:`T_{0}`, and reference
# air
#     temperature :math:`T_{R}` as follows:

#     .. math::
#         g_{tR} c_{p} (T_{R} - T_{A})
#         + g_{t0} c_{p} (T_{0} - T_{A})
#         + g_{L} c_{p} (T_{L} - T_{A}) = 0

#     where :math:`c_{p}` is the specific heat of air at constant pressure and
#     :math:`g_{tR}`, :math:`g_{t0}` and :math:`g_{L}` are conductance from reference
#     height, the ground and from the leaf, respectively.
#     :math:`g_{L} = 1/(1/g_{HA} + 1/g_{z})` where :math:`g_{HA}` is leaf boundary layer
#     conductance and :math:`g_{z}` is the sub-canopy turbulent conductance at the
# height
#     of the leaf over the mean distance between the leaf and the air.

#     Defining :math:`T_{L} - T_{A}` as :math:`\Delta T` and rearranging gives:

#     .. math:: T_{A} = a_{A} + b_{A} \Delta T_{L}

#     where :math:`a_{A} = \frac{(g_{tR} T_{R} + g_{t0} T_{0})}{(g_{tR} + g_{t0})}` and
#     :math:`b_{A} = \frac{g_{L}}{(g_{tR} + g_{t0})}` .

#     The sensible heat flux between the leaf and the air is given by

#     .. math:: g_{Ha} c_{p} (T_{L} - T_{A}) = b_{H} \Delta T_{L}

#     where :math:`b_{H} = g_{Ha} c_{p}`. The equivalent vapour flux equation is

#     .. math:: g_{tR}(e_{R} - e_{a}) + g_{t0} (e_{0} - e_{a}) + g_{v} (e_{L} - e_{a})
# = 0

#     where :math:`e_{L}`, :math:`e_{A}`, :math:`e_{0}` and :math:`e_{R}` are the vapour
#     pressure of the leaf, air, soil and air at reference height, respectively, and
#     :math:`g_{v}` is leaf conductance for vapour given by
#     :math:`g_{v} = \frac{1}{(\frac{1}{g_{c} + g_{L})}}` where :math:`g_{c}` is
# stomatal
#     conductance. Assuming the leaf to be saturated, and approximated by
#     :math:`e_{s} [T_{R}]+\Delta_{v} [T_{R}]\Delta T_{L}` where :math:`\Delta_{v}` is
# the
#     slope of the saturated pressure curve at temperature :math:`T_{R}`, and
# rearranging
#     gives

#     .. math:: e_{a} = a_{E} + b_{E} \Delta T_{L}

#     where :math:`a_{E} = \frac{(g_{tR} e_{R} + g_{t0} e_{0} + g_{v} e_{s}[T_{R}])}
#     {(g_{tR} + g_{t0} + g_{v})}` and
#     :math:`b_{E} = \frac{\Delta_{V} [T_{R}])}{(g_{tR} + g_{t0} + g_{v})}`.

#     The latent heat term is given by

#     .. math:: \lambda E = \frac{\lambda g_{v}}{p_{a}} (e_{L} - e_{A})

#     Substituting :math:`e_{A}` for its linearized form, again assuming :math:`e_{L}`
#     is approximated by :math:`e_{s} [T_{R}]+\Delta_{v} [T_{R}]\Delta T_{L}`, and
#     rearranging gives:

#     .. math:: \lambda E = a_{L} + b_{L} \Delta T_{L},

#     where :math:`a_{L} = \frac{\lambda g_{v}}{p_{a}} (e_{s} [T_{R}] - a_{E})` and
#     :math:`b_{L} = \frac{\lambda g_{v}}{p_{a}} (\Delta_{V} [T_{R}] - b_{E})`.

#     The radiation emitted by the leaf :math:`R_{em}` is given by the Stefan Boltzmann
#     law and can be linearised as follows:

#     .. math:: R_{em} = a_{R} + b_{R} \Delta T_{L}

#     where :math:`a_{R} = \epsilon_{s} \sigma a_{A}^{4}` and
#     :math:`b_{R} = 4 \epsilon_{s} \sigma (a_{A}^{3} b_{A} + T_{R}^{3})`.

#     The full heat balance equation for the difference between leaf and canopy air
#     temperature becomes

#     .. math:: \Delta T_{L} = \frac{R_{abs} - a_{R} - a_{L}}{(1 + b_{R} + b_{L}
# + b_{H})}

#     The equation is then used to calculate air and leaf temperature as follows:

#     .. math:: T_{A} = a_{A} + b_{A} \Delta T_{L}

#     and

#     .. math:: T_{L} = T_{A} + \Delta T_{L}.

#     the data object has to contain the previous and current values for the following:

#     * air_temperature_ref: Air temperature at reference height 2m above canopy, [C]
#     * vapour_pressure_ref: vapour pressure at reference height 2m above canopy, [kPa]
#     * soil_temperature: Soil temperature, [C]
#     * soil_moisture: Soil moisture, [mm]
#     * layer_heights: Layer heights, [mm]
#     * atmospheric_pressure_ref: Atmospheric pressure at reference height, [kPa]
#     * air_temperature: Air temperature, [C]
#     * canopy_temperature: Leaf temperature, [C]
#     * latent_heat_vapourisation: Latent heat of vapourisation, [J kg-1]
#     * absorbed_radiation: Absorbed radiation, [W m-2]
#     * specific_heat_air: Specific heat of air, [J mol-1 K-1]

#     Todo:
#     * add latent heat flux from soil to atmosphere (-> VPD)
#     * check time integration
#     * set limits to temperature and VPD

#     Args:
#         data: Instance of data object
#         time_index: Time index
#         layer_structure: Instance of LayerStructure that countains details about
# layers
#         abiotic_constants: Set of abiotic constants
#         abiotic_simple_constants: Set of abiotic constants
#         core_constants: Set of core constants

#     Returns:
#         air temperature, [C], canopy temperature, [C], vapour pressure [kPa], vapour
#         pressure deficit, [kPa]
#     """

#     output = {}

#     # Select variables for current time step and relevant layers
#     topsoil_temperature = data["soil_temperature"]
# [layer_structure.index_topsoil_scalar]
#     topsoil_moisture = (
#         data["soil_moisture"][layer_structure.index_topsoil_scalar]
#         / -data["layer_heights"][layer_structure.index_topsoil_scalar]
#         / core_constants.meters_to_mm
#     )
#     air_temperature_ref = data["air_temperature_ref"].isel(time_index=time_index)
#     vapour_pressure_ref = data["vapour_pressure_ref"].isel(time_index=time_index)
#     atmospheric_pressure_ref = data["atmospheric_pressure_ref"].isel(
#         time_index=time_index
#     )

#     # Calculate vapour pressures
#     soil_saturated_vapour_pressure = calculate_saturation_vapour_pressure(
#         temperature=topsoil_temperature,
#         saturation_vapour_pressure_factors=(
#             abiotic_simple_constants.saturation_vapour_pressure_factors
#         ),
#     )
#     soil_vapour_pressure = topsoil_moisture * soil_saturated_vapour_pressure
#     saturated_vapour_pressure_ref = calculate_saturation_vapour_pressure(
#         temperature=air_temperature_ref,
#         saturation_vapour_pressure_factors=(
#             abiotic_simple_constants.saturation_vapour_pressure_factors
#         ),
#     )

#     # Calculate current conductivities for atmosphere and soil
#     current_conductivities = calculate_current_conductivities(
#         data=data,
#         characteristic_dimension_leaf=core_constants.characteristic_dimension_leaf,
#         von_karmans_constant=core_constants.von_karmans_constant,
#         abiotic_constants=abiotic_constants,
#     )

#     conductivity_from_soil = (
#         topsoil_moisture * soil_saturated_vapour_pressure
#     ).to_numpy()

#     # Factors from leaf and air temperature linearisation
#     a_A, b_A = leaf_and_air_temperature_linearisation(
#         conductivity_from_ref_height=(
#             current_conductivities["conductivity_from_ref_height"][
#                 layer_structure.index_filled_canopy
#             ]
#         ),
#         conductivity_from_soil=conductivity_from_soil,
#         leaf_air_heat_conductivity=(
#             current_conductivities["leaf_air_heat_conductivity"][
#                 layer_structure.index_filled_canopy
#             ]
#         ),
#         air_temperature_ref=air_temperature_ref.to_numpy(),
#         top_soil_temperature=topsoil_temperature.to_numpy(),
#     )

#     # Factors from longwave radiative flux linearisation
#     a_R, b_R = longwave_radiation_flux_linearisation(
#         a_A=a_A,
#         b_A=b_A,
#         air_temperature_ref=air_temperature_ref.to_numpy(),
#         leaf_emissivity=abiotic_constants.leaf_emissivity,
#         stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
#     )

#     # Factors from vapour pressure linearisation
#     delta_v_ref = calculate_slope_of_saturated_pressure_curve(
#         air_temperature_ref.to_numpy(),
#         saturated_pressure_slope_parameters=(
#             abiotic_constants.saturated_pressure_slope_parameters
#         ),
#     )

#     a_E, b_E = vapour_pressure_linearisation(
#         vapour_pressure_ref=vapour_pressure_ref.to_numpy(),
#         saturated_vapour_pressure_ref=saturated_vapour_pressure_ref.to_numpy(),
#         soil_vapour_pressure=soil_vapour_pressure.to_numpy(),
#         conductivity_from_soil=conductivity_from_soil,
#         leaf_vapour_conductivity=(
#             current_conductivities["leaf_vapour_conductivity"][
#                 layer_structure.index_filled_canopy
#             ]
#         ),
#         conductivity_from_ref_height=(
#             current_conductivities["conductivity_from_ref_height"][
#                 layer_structure.index_filled_canopy
#             ]
#         ),
#         delta_v_ref=delta_v_ref,
#     )

#     # Factors from latent heat flux linearisation
#     a_L, b_L = latent_heat_flux_linearisation(
#         latent_heat_vapourisation=(
#             data["latent_heat_vapourisation"][
#                 layer_structure.index_filled_canopy
#             ].to_numpy()
#         ),
#         leaf_vapour_conductivity=(
#             current_conductivities["leaf_vapour_conductivity"][
#                 layer_structure.index_filled_canopy
#             ]
#         ),
#         atmospheric_pressure_ref=atmospheric_pressure_ref.to_numpy(),
#         saturated_vapour_pressure_ref=saturated_vapour_pressure_ref.to_numpy(),
#         a_E=a_E,
#         b_E=b_E,
#         delta_v_ref=delta_v_ref,
#     )

#     # Factor from sensible heat flux linearisation
#     b_H = (
#         current_conductivities["leaf_air_heat_conductivity"][
#             layer_structure.index_filled_canopy
#         ]
#         * data["specific_heat_air"][layer_structure.index_filled_canopy].to_numpy()
#     )

#     # Calculate new leaf and air temperature
#     delta_canopy_temperature = calculate_delta_canopy_temperature(
#         absorbed_radiation=data["absorbed_radiation"][
#             layer_structure.index_filled_canopy
#         ].to_numpy(),
#         a_R=a_R,
#         a_L=a_L,
#         b_R=b_R,
#         b_L=b_L,
#         b_H=b_H,
#     )
#     new_air_temperature = a_A + b_A * delta_canopy_temperature
#     new_canopy_temperature = (
#         (data["air_temperature"][layer_structure.index_filled_canopy]).to_numpy()
#         + delta_canopy_temperature
#     )

#     # Interpolate temperature below canopy

#     # TODO - This only uses the index of the _last_ filled layer, which works with the
#     #        current test where the canopy layers are consistent across cells, but
# will
#     #        break with uneven canopy layers.

#     target_heights = data["layer_heights"][layer_structure.index_surface].to_numpy()

#     below_canopy_temperature = interpolate_along_heights(
#         start_height=np.repeat(0.0, data.grid.n_cells),
#         end_height=data["layer_heights"][
#             layer_structure.n_canopy_layers_filled
#         ].to_numpy(),
#         target_heights=target_heights,
#         start_value=topsoil_temperature.to_numpy(),
#         end_value=new_air_temperature[-1],
#     )

#     # Create arrays and return for data object
#     new_temperature_profile = layer_structure.from_template()
#     new_temperature_profile[layer_structure.index_filled_atmosphere] = np.vstack(
#         [
#             air_temperature_ref.to_numpy(),
#             new_air_temperature,
#             below_canopy_temperature,
#         ]
#     )
#     output["air_temperature"] = new_temperature_profile

#     canopy_temperature = layer_structure.from_template()
#     canopy_temperature[layer_structure.index_filled_canopy] = new_canopy_temperature
#     output["canopy_temperature"] = canopy_temperature

#     # Calculate vapour pressure
#     vapour_pressure_mean = a_E + b_E * delta_canopy_temperature
#     vapour_pressure_new = vapour_pressure_ref.to_numpy() + 2 * (
#         vapour_pressure_mean - vapour_pressure_ref.to_numpy()
#     )

#     saturation_vapour_pressure_new = calculate_saturation_vapour_pressure(
#         DataArray(new_temperature_profile),
#         saturation_vapour_pressure_factors=(
#             abiotic_simple_constants.saturation_vapour_pressure_factors
#         ),
#     )
#     saturation_vapour_pressure_new_canopy = (
#         saturation_vapour_pressure_new[layer_structure.index_filled_canopy]
#     ).to_numpy()

#     canopy_vapour_pressure = np.where(
#         vapour_pressure_new > saturation_vapour_pressure_new_canopy,
#         saturation_vapour_pressure_new_canopy,
#         vapour_pressure_new,
#     )
#     below_canopy_vapour_pressure = interpolate_along_heights(
#         start_height=np.repeat(0.0, data.grid.n_cells),
#         end_height=data["layer_heights"][
#             layer_structure.n_canopy_layers_filled
#         ].to_numpy(),
#         target_heights=target_heights,
#         start_value=soil_vapour_pressure.to_numpy(),
#         end_value=canopy_vapour_pressure[-1],
#     )
#     output["vapour_pressure"] = DataArray(
#         np.vstack(
#             [
#                 vapour_pressure_ref.to_numpy(),
#                 canopy_vapour_pressure,
#                 np.full((7, data.grid.n_cells), np.nan),
#                 below_canopy_vapour_pressure,
#                 np.full((2, data.grid.n_cells), np.nan),
#             ]
#         ),
#         dims=["layers", "cell_id"],
#     )

#     output["vapour_pressure_deficit"] = output["vapour_pressure"] / DataArray(
#         saturation_vapour_pressure_new, dims=["layers", "cell_id"]
#     )

#     # Return current conductivities as DataArrays
#     for var in [
#         "conductivity_from_ref_height",
#         "leaf_air_heat_conductivity",
#         "leaf_vapour_conductivity",
#     ]:
#         output[var] = DataArray(
#             current_conductivities[var],
#             dims=data["air_temperature"].dims,
#             coords=data["air_temperature"].coords,
#             name=var,
#         )

#     # Return latent and sensible heat flux from canopy
#     sensible_heat_flux = data["sensible_heat_flux"].copy()
#     sensible_heat_flux_canopy = b_H * delta_canopy_temperature
#     sensible_heat_flux[layer_structure.index_topsoil] =
# data["sensible_heat_flux_soil"]
#     sensible_heat_flux[layer_structure.index_filled_canopy] =
# sensible_heat_flux_canopy
#     output["sensible_heat_flux"] = sensible_heat_flux

#     latent_heat_flux = data["latent_heat_flux"].copy()
#     latent_heat_flux_canopy = a_L + b_L * delta_canopy_temperature
#     latent_heat_flux[layer_structure.index_topsoil] = data["latent_heat_flux_soil"]
#     latent_heat_flux[layer_structure.index_filled_canopy] = latent_heat_flux_canopy
#     output["latent_heat_flux"] = latent_heat_flux

#     return output


# def leaf_and_air_temperature_linearisation(
#     conductivity_from_ref_height: NDArray[np.float32],
#     conductivity_from_soil: NDArray[np.float32],
#     leaf_air_heat_conductivity: NDArray[np.float32],
#     air_temperature_ref: NDArray[np.float32],
#     top_soil_temperature: NDArray[np.float32],
# ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
#     """Calculate factors for leaf and air temperature linearisation.

#     Args:
#         conductivity_from_ref_height: Conductivity from reference height,[mol m-2 s-1]
#         conductivity_from_soil: Conductivity from soil, [mol m-2 s-1]
#         leaf_air_heat_conductivity: Leaf air heat conductivity, [mol m-2 s-1]
#         air_temperature_ref: Air temperature at reference height 2m above the canopy,
# [C]
#         top_soil_temperature: Top soil temperature, [C]

#     Returns:
#         Factors a_A and b_A for leaf and air temperature linearisation
#     """

#     a_A = (
#         (conductivity_from_ref_height * air_temperature_ref)
#         + (conductivity_from_soil * top_soil_temperature)
#     ) / (conductivity_from_ref_height + conductivity_from_soil)

#     b_A = leaf_air_heat_conductivity / (
#         conductivity_from_ref_height + conductivity_from_soil
#     )
#     return a_A, b_A


# def longwave_radiation_flux_linearisation(
#     a_A: NDArray[np.float32],
#     b_A: NDArray[np.float32],
#     air_temperature_ref: NDArray[np.float32],
#     leaf_emissivity: float,
#     stefan_boltzmann_constant: float,
# ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
#     """Calculate factors for longwave radiative flux linearisation.

#     Args:
#         a_A: Factor for leaf and air temperature linearisation
#         b_A: Factor for leaf and air temperature linearisation
#         air_temperature_ref: Air temperature at reference height 2m above the canopy,
# [C]
#         leaf_emissivity: Leaf emissivity, dimensionless
#         stefan_boltzmann_constant: Stefan Boltzmann constant, [W m-2 K-4]

#     Returns:
#         Factors a_R and b_R for longwave radiative flux linearisation
#     """

#     a_R = leaf_emissivity * stefan_boltzmann_constant * a_A**4

#     b_R = (
#         4
#         * leaf_emissivity
#         * stefan_boltzmann_constant
#         * (a_A**3 * b_A + air_temperature_ref**3)
#     )
#     return a_R, b_R


# def vapour_pressure_linearisation(
#     vapour_pressure_ref: NDArray[np.float32],
#     saturated_vapour_pressure_ref: NDArray[np.float32],
#     soil_vapour_pressure: NDArray[np.float32],
#     conductivity_from_soil: NDArray[np.float32],
#     leaf_vapour_conductivity: NDArray[np.float32],
#     conductivity_from_ref_height: NDArray[np.float32],
#     delta_v_ref: NDArray[np.float32],
# ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
#     """Calculate factors for vapour pressure linearisation.

#     Args:
#         vapour_pressure_ref: Vapour pressure at reference height 2 m above canopy,
# [kPa]
#         saturated_vapour_pressure_ref: Saturated vapour pressure at reference height
# 2 m
#             above canopy, [kPa]
#         soil_vapour_pressure: Soil vapour pressure, [kPa]
#         conductivity_from_soil: Conductivity from soil, [mol m-2 s-1]
#         leaf_vapour_conductivity: Leaf vapour conductivity, [mol m-2 s-1]
#         conductivity_from_ref_height: Conductivity frm reference height, [mol m-2 s-1]
#         delta_v_ref: Slope of saturated vapour pressure curve

#     Returns:
#         Factors a_E and b_E for vapour pressure linearisation
#     """

#     a_E = (
#         conductivity_from_ref_height * vapour_pressure_ref
#         + conductivity_from_soil * soil_vapour_pressure
#         + leaf_vapour_conductivity * saturated_vapour_pressure_ref
#     ) / (
#         conductivity_from_ref_height + conductivity_from_soil +
# leaf_vapour_conductivity
#     )

#     b_E = delta_v_ref / (
#         conductivity_from_ref_height + conductivity_from_soil +
# leaf_vapour_conductivity
#     )
#     return a_E, b_E


# def latent_heat_flux_linearisation(
#     latent_heat_vapourisation: NDArray[np.float32],
#     leaf_vapour_conductivity: NDArray[np.float32],
#     atmospheric_pressure_ref: NDArray[np.float32],
#     saturated_vapour_pressure_ref: NDArray[np.float32],
#     a_E: NDArray[np.float32],
#     b_E: NDArray[np.float32],
#     delta_v_ref: NDArray[np.float32],
# ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
#     """Calculate factors for latent heat flux linearisation.

#     Args:
#         latent_heat_vapourisation: latent heat of vapourisation
#         leaf_vapour_conductivity: leaf vapour conductivity, [mol m-2 s-1]
#         atmospheric_pressure_ref: Atmospheric pressure at reference height 2 m above
#             canopy, [kPa]
#         saturated_vapour_pressure_ref: Satuated vapour pressure at reference height
# 2 m
#             above canopy, [kPa]
#         a_E: Factor for vapour pressure linearisation
#         b_E: Factor for vapour pressure linearisation
#         delta_v_ref: Slope of saturated vapour pressure curve

#     Returns:
#         Factors a_L and b_L for latent heat flux linearisation
#     """

#     a_L = (latent_heat_vapourisation * leaf_vapour_conductivity) / (
#         atmospheric_pressure_ref * (saturated_vapour_pressure_ref - a_E)
#     )

#     b_L = (latent_heat_vapourisation * leaf_vapour_conductivity) / (
#         atmospheric_pressure_ref * (delta_v_ref - b_E)
#     )

#     return a_L, b_L


# def calculate_delta_canopy_temperature(
#     absorbed_radiation: NDArray[np.float32],
#     a_R: NDArray[np.float32],
#     a_L: NDArray[np.float32],
#     b_R: NDArray[np.float32],
#     b_L: NDArray[np.float32],
#     b_H: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate change in canopy temperature (delta).

#     Args:
#         absorbed_radiation: Radiation (shortwave) absorved by canopy, [W m-2]
#         a_R: Factor for longwave radiation emission linearisation
#         a_L: Factor for latent heat flux linearisation
#         b_R: Factor for longwave radiation emission linearisation
#         b_L: Factor for latent heat flux linearisation
#         b_H: Factor for sensible heat flux linearisation

#     Returns:
#         Change in canopy temperature, [C]
#     """

#     return (absorbed_radiation - a_R - a_L) / (1 + b_R + b_L + b_H)

# """The radiation model calculates the radiation balance of the Virtual Ecosystem. This
# incluses direct and diffuse radiation components, shortwave and longwave radiation
# within the canopy and at the surface. The implementation is based on the 'micropoint'
# package, see https://github.com/ilyamaclean/micropoint.

# Part of this module will likely be replaced by pyrealm functions in the future to
#  better
# integrate with the plant component.
# """

# import numpy as np
# from numpy.typing import NDArray


# # Shortwave radiation
# def calculate_julian_day(year: int, month: int, day: int) -> int:
#     """Calculate Astronomical Julian day.

#     Args:
#         year: Year
#         month: Month
#         day: Day

#     Returns:
#         Julian day
#     """
#     day_adjusted = day + 0.5
#     month_adjusted = month + (month < 3) * 12
#     year_adjusted = year + (month < 3) * -1
#     julian = (
#         np.trunc(365.25 * (year_adjusted + 4716))
#         + np.trunc(30.6001 * (month_adjusted + 1))
#         + day_adjusted
#         - 1524.5
#     )
#     correction_factor = (
#         2 - np.trunc(year_adjusted / 100) + np.trunc(np.trunc(year_adjusted / 100) /
# 4)
#     )
#     julian_day = int(julian + (julian > 2299160) * correction_factor)
#     return julian_day


# def calculate_solar_time(
#     julian_day: int, local_time: float, longitude: NDArray[np.float32]
# ) -> float:
#     """Calculate solar time.

#     Args:
#         julian_day: Julian day, e.g. for September 4, 2023 julian_day=2460192
#         local_time: Local time, e.g. noon local_time=12.0
#         longitude: Longitude, decimal degrees

#     Returns:
#         solar time
#     """
#     # Calculate the mean anomaly of the Sun
#     mean_anomaly = 6.24004077 + 0.01720197 * (julian_day - 2451545)

#     # Calculate the equation of time (EoT)
#     equation_of_time = -7.659 * np.sin(mean_anomaly) + 9.863 * np.sin(
#         2 * mean_anomaly + 3.5932
#     )

#     # Calculate the solar time
#     solar_time = local_time + (4 * longitude + equation_of_time) / 60

#     return solar_time


# def calculate_solar_position(
#     latitude: NDArray[np.float32],
#     longitude: NDArray[np.float32],
#     year: int,
#     month: int,
#     day: int,
#     local_time: float,
# ) -> list[NDArray[np.float32]]:
#     """Calculate solar position.

#     Args:
#         latitude: Latitude, decimal degrees
#         longitude: Longitude, decimal degrees
#         year: Year
#         month: Month
#         day: Day
#         local_time: Local time

#     Returns:
#         solar zenith angle and solar azimuth angle in degree
#     """
#     # Calculate Julian day and solar time
#     julian_day = calculate_julian_day(year=year, month=month, day=day)
#     solar_time = calculate_solar_time(
#         julian_day=julian_day, local_time=local_time, longitude=longitude
#     )

#     # Convert latitude to radians
#     latitude_rad = np.radians(latitude)

#     # Calculate solar declination
#     solar_declination = np.radians(23.5) * np.cos(
#         (2 * np.pi * julian_day - 159.5) / 365.25
#     )

#     # Calculate Solar hour angle
#     solar_hour_angle = np.radians(0.261799 * (solar_time - 12))

#     # Calculate solar zenith angle
#     coh = np.sin(solar_declination) * np.sin(latitude_rad) + np.cos(
#         solar_declination
#     ) * np.cos(latitude_rad) * np.cos(solar_hour_angle)
#     solar_zenith_angle = np.degrees(np.acos(coh))

#     # Calculate solar azimuth angle
#     sh = np.sin(solar_declination) * np.sin(latitude_rad) + np.cos(
#         solar_declination
#     ) * np.cos(latitude_rad) * np.cos(solar_hour_angle)
#     hh = np.atan(sh / np.sqrt(1 - sh * sh))
#     sazi = np.cos(solar_declination) * np.sin(solar_hour_angle) / np.cos(hh)
#     cazi = (
#         np.sin(latitude_rad) * np.cos(solar_declination) * np.cos(solar_hour_angle)
#         - np.cos(latitude_rad) * np.sin(solar_declination)
#     ) / np.sqrt(
#         np.pow(np.cos(solar_declination) * np.sin(solar_hour_angle), 2)
#         + np.pow(
#             np.sin(latitude_rad) * np.cos(solar_declination) * np.cos(
# solar_hour_angle)
#             - np.cos(latitude_rad) * np.sin(solar_declination),
#             2,
#         )
#     )

#     sqt = np.maximum(1 - sazi**2, 0)

#     solar_azimuth_angle = 180 + (180 * np.atan(sazi / np.sqrt(sqt))) / np.pi

#     solar_azimuth_angle = np.where(
#         cazi < 0,
#         np.where(sazi < 0, 180 - solar_azimuth_angle, 540 - solar_azimuth_angle),
#         solar_azimuth_angle,
#     )

#     return [solar_zenith_angle, solar_azimuth_angle]


# def calculate_solar_index(
#     slope: NDArray[np.float32],
#     aspect: NDArray[np.float32],
#     zenith: NDArray[np.float32],
#     azimuth: NDArray[np.float32],
#     shadowmask=bool,
# ) -> NDArray[np.float32]:
#     """Calculate the solar index.

#     Parameters:
#         slope: The slope angle in decimal degrees from horizontal
#         aspect: The aspect angle in decimal degrees from horizontal
#         zenith: The solar zenith angle in decimal degrees
#         azimuth: The solar azimuth angle in decimal degrees
#         shadowmask: If True, the index is set to 0 if the zenith angle is greater than
#             90 degrees

#     Returns:
#         The solar index
#     """

#     if not shadowmask:
#         zenith = np.where(zenith > 90.0, 0.0, zenith)

#     zenith_rad = np.radians(zenith)
#     slope_rad = np.radians(slope)
#     azimuth_minus_aspect_rad = np.radians(azimuth - aspect)

#     # Check for slope == 0.0 element-wise
#     solar_index_value = np.where(
#         slope == 0.0,
#         np.cos(zenith_rad),  # If slope is 0, use cos(zenith_rad)
#         (
#             np.cos(zenith_rad) * np.cos(slope_rad)
#             + np.sin(zenith_rad) * np.sin(slope_rad) * np.cos(
# azimuth_minus_aspect_rad)
#         ),
#     )

#     return np.maximum(solar_index_value, 0.0)


# def calculate_clear_sky_radiation(
#     solar_zenith_angle: NDArray[np.float32],
#     temperature: NDArray[np.float32],
#     relative_humidity: NDArray[np.float32],
#     atmospheric_pressure: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate the clear sky radiation for a given set of dates and locations.

#     Parameters:
#         solar_zenith_angle: Solar zenith angle in degree
#         temperature: Temperature, [C]
#         relative_humidity: Relative humidity in percent
#         atmospheric_pressure: Atmospheric pressures, [hPa]

#     Returns:
#         List of clear sky radiation values
#     """

#     solar_zenith_angle_rad = np.radians(solar_zenith_angle)

#     # Vectorized condition: apply formula only where solar_zenith_angle <= 90
#     optical_thickness = np.where(
#         solar_zenith_angle <= 90.0,
#         35
#         * np.cos(solar_zenith_angle_rad)
#         * (1224 * np.cos(solar_zenith_angle_rad) ** 2 + 1) ** -0.5,
#         0.0,  # Set to 0 where condition is false
#     )

#     transmittance_to_zenith = np.where(
#         solar_zenith_angle <= 90.0,
#         1.021
#         - 0.084 * np.sqrt(optical_thickness * 0.00949 * atmospheric_pressure + 0.051),
#         0.0,
#     )

#     log_relative_humidity = np.log(relative_humidity / 100)
#     temperature_factor = (17.27 * temperature) / (237.3 + temperature)
#     dew_point_temperature = (237.3 * (log_relative_humidity + temperature_factor)) / (
#         17.27 - (log_relative_humidity + temperature_factor)
#     )

#     humidity_adjustment_factor = np.exp(
#         0.1133 - np.log(3.78) + 0.0393 * dew_point_temperature
#     )

#     water_vapor_adjustment = np.where(
#         solar_zenith_angle <= 90.0,
#         1 - 0.077 * (humidity_adjustment_factor * optical_thickness) ** 0.3,
#         0.0,
#     )

#     aerosol_optical_depth = np.where(
#         solar_zenith_angle <= 90.0, 0.935 * optical_thickness, 0.0
#     )

#     clear_sky_optical_depth = (
#         transmittance_to_zenith * water_vapor_adjustment * aerosol_optical_depth
#     )

#     clear_sky_radiation = np.where(
#         solar_zenith_angle <= 90.0,
#         1352.778 * np.cos(solar_zenith_angle_rad) * clear_sky_optical_depth,
#         0.0,
#     )

#     return clear_sky_radiation


# def calculate_canopy_extinction_coefficients(
#     solar_zenith_angle: NDArray[np.float32],
#     leaf_inclination_angle_coefficient: float,
#     solar_index: NDArray[np.float32],
# ) -> list[NDArray[np.float32]]:
#     """Calculate the canopy extinction coefficients for sloped ground surfaces.

#     Parameters:
#         solar_zenith_angle: Solar zenith angle in degrees
#         leaf_inclination_angle_coefficient: Leaf inclination angle coefficient
#         solar_index: Solar index value

#     Returns:
#         List of canopy extinction coefficients [k, kd, k0]
#     """
#     # Ensure solar zenith angles don't exceed 90 degrees
#     solar_zenith_angle = np.where(solar_zenith_angle > 90.0, 90.0, solar_zenith_angle)
#     zenith_angle_rad = np.radians(solar_zenith_angle)

#     # Calculate normal canopy extinction coefficient k
#     extinction_coefficient_k = np.where(
#         leaf_inclination_angle_coefficient == 1.0,
#         1 / (2 * np.cos(zenith_angle_rad)),
#         np.where(
#             np.isinf(leaf_inclination_angle_coefficient),
#             1.0,
#             np.sqrt(
#                 leaf_inclination_angle_coefficient**2 + np.tan(zenith_angle_rad) ** 2
#             )
#             / (
#                 leaf_inclination_angle_coefficient
#                 + 1.774 * (leaf_inclination_angle_coefficient + 1.182) ** -0.733
#             ),
#         ),
#     )

#     # Cap extinction coefficient k
#     extinction_coefficient_k = np.where(
#         extinction_coefficient_k > 6000.0, 6000.0, extinction_coefficient_k
#     )

#     # Calculate adjusted k0
#     extinction_coefficient_k0 = np.where(
#         leaf_inclination_angle_coefficient == 1.0,
#         0.5,
#         np.where(
#             np.isinf(leaf_inclination_angle_coefficient),
#             1.0,
#             np.sqrt(leaf_inclination_angle_coefficient**2)
#             / (
#                 leaf_inclination_angle_coefficient
#                 + 1.774 * (leaf_inclination_angle_coefficient + 1.182) ** -0.733
#             ),
#         ),
#     )

#     # Calculate kd (adjusted extinction coefficient)
#     extinction_coefficient_kd = np.where(
#         solar_index == 0,
#         1.0,
#         extinction_coefficient_k * np.cos(zenith_angle_rad) / solar_index,
#     )

#     return [
#         extinction_coefficient_k,  # k
#         extinction_coefficient_kd,  # kd
#         extinction_coefficient_k0,  # k0
#     ]


# def calculate_diffuse_radiation_parameters(
#     adjusted_plant_area_index: NDArray[np.float32],
#     scatter_absorption_coefficient: float,
#     backward_scattering_coefficient: float,
#     diffuse_scattering_coefficient: float,
#     ground_reflectance: float,  # gref TODO could be array with variable soil types
# ) -> list[float]:
#     """Calculates parameters for diffuse radiation using two-stream model.

#     Args:
#         adjusted_plant_area_index: Plant area index adjusted by clumping factor,
#             [m2 m-2]  # reference: pait, with(vegp,(pai/(1-clump)))
#         scatter_absorption_coefficient: Absorption coefficient for incoming diffuse
#             radiation per unit leaf area   # reference: a, a<-1-om
#         backward_scattering_coefficient: Backward scattering coefficient  # reference:
#             gma, gma<-0.5*(om+J*del)
#         diffuse_scattering_coefficient: Constant diffuse radiation related coefficient
#           # reference: , h<-sqrt(a^2+2*a*gma)
#         ground_reflectance: Ground reflectance (0-1)

#     Returns:
#         List of diffuse radiation parameters [p1, p2, p3, p4]
#     """

#     # Handle division by zero for ground reflectance
#     if ground_reflectance == 0.0:
#         ground_reflectance = 0.001

#     # Calculate base parameters
#     leaf_extinction_factor = np.exp(
#         -diffuse_scattering_coefficient * adjusted_plant_area_index
#     )
#     u1 = scatter_absorption_coefficient + backward_scattering_coefficient * (
#         1 - 1 / ground_reflectance
#     )
#     u2 = scatter_absorption_coefficient + backward_scattering_coefficient * (
#         1 - ground_reflectance
#     )
#     d1 = (
#         scatter_absorption_coefficient
#         + backward_scattering_coefficient
#         + diffuse_scattering_coefficient
#     ) * (u1 - diffuse_scattering_coefficient) * 1 / leaf_extinction_factor - (
#         scatter_absorption_coefficient
#         + backward_scattering_coefficient
#         - diffuse_scattering_coefficient
#     ) * (u1 + diffuse_scattering_coefficient) * leaf_extinction_factor
#     d2 = (u2 + diffuse_scattering_coefficient) * 1 / leaf_extinction_factor - (
#         u2 - diffuse_scattering_coefficient
#     ) * leaf_extinction_factor

#     # Calculate parameters
#     parameter_1 = (backward_scattering_coefficient / (d1 * leaf_extinction_factor))
# * (
#         u1 - diffuse_scattering_coefficient
#     )
#     parameter_2 = (-backward_scattering_coefficient * leaf_extinction_factor / d1) * (
#         u1 + diffuse_scattering_coefficient
#     )
#     parameter_3 = (1 / (d2 * leaf_extinction_factor)) * (
#         u2 + diffuse_scattering_coefficient
#     )
#     parameter_4 = (-leaf_extinction_factor / d2) * (u2 -
# diffuse_scattering_coefficient)

#     return [parameter_1, parameter_2, parameter_3, parameter_4]


# def calculate_direct_radiation_parameters(
#     adjusted_plant_area_index: NDArray[np.float32],
#     scattering_albedo: float,
#     scatter_absorption_coefficient: float,
#     backward_scattering_coefficient: float,
#     diffuse_scattering_coefficient: float,
#     ground_reflectance: float,
#     inclination_distribution: float,
#     delta_reflectance_transmittance: float,
#     extinction_coefficient_k: NDArray[np.float32],
#     extinction_coefficient_kd: NDArray[np.float32],
#     sigma: float,
# ) -> list[float | NDArray[np.float32]]:
#     """Calculates parameters for direct radiation using two-stream model.

#     Args:
#         adjusted_plant_area_index: Plant area index adjusted by clumping factor
#             # reference: pait, with(vegp,(pai/(1-clump)))
#         scattering_albedo: Single scattering albedo of individual canopy elements
#             # reference: om, om<-with(vegp,lref+ltra)
#         scatter_absorption_coefficient: Absorption coefficient for incoming diffuse
#             radiation per unit leaf area  # reference: a, a<-1-om
#         backward_scattering_coefficient: Backward scattering coefficient  # reference:
#             gma, gma<-0.5*(om+J*del)
#         diffuse_scattering_coefficient: Constant diffuse radiation related coefficient
#           # reference: , h<-sqrt(a^2+2*a*gma)
#         ground_reflectance: Ground reflectance (0-1)
#         inclination_distribution: Integral function of the inclination distribution of
#             canopy elements
#         delta_reflectance_transmittance: Difference between canopy element reflectance
#             and canopy element transmittance
#         extinction_coefficient_k: Normal canopy extinction coefficient
#         extinction_coefficient_kd: Adjusted canopy extinction coefficient
#         sigma: sigma

#     Returns:
#         List of direct radiation parameters [parameter_5 to parameter_10]
#     """

#     # Calculate base parameters
#     ss = (
#         0.5
#         * (
#             scattering_albedo
#             + inclination_distribution
#             * delta_reflectance_transmittance
#             / extinction_coefficient_k
#         )
#         * extinction_coefficient_k
#     )
#     sstr = scattering_albedo * extinction_coefficient_k - ss

#     # Calculate intermediate parameters
#     leaf_extinction_factor_1 = np.exp(
#         -diffuse_scattering_coefficient * adjusted_plant_area_index
#     )
#     leaf_extinction_factor_2 = np.exp(
#         -extinction_coefficient_kd * adjusted_plant_area_index
#     )

#     # Calculate parameters
#     u1 = scatter_absorption_coefficient + backward_scattering_coefficient * (
#         1 - 1 / ground_reflectance
#     )
#     u2 = scatter_absorption_coefficient + backward_scattering_coefficient * (
#         1 - ground_reflectance
#     )
#     d1 = (
#         scatter_absorption_coefficient
#         + backward_scattering_coefficient
#         + diffuse_scattering_coefficient
#     ) * (u1 - diffuse_scattering_coefficient) * 1 / leaf_extinction_factor_1 - (
#         scatter_absorption_coefficient
#         + backward_scattering_coefficient
#         - diffuse_scattering_coefficient
#     ) * (u1 + diffuse_scattering_coefficient) * leaf_extinction_factor_1
#     d2 = (u2 + diffuse_scattering_coefficient) * 1 / leaf_extinction_factor_1 - (
#         u2 - diffuse_scattering_coefficient
#     ) * leaf_extinction_factor_1

#     parameter_5 = (
#         -ss
#         * (
#             scatter_absorption_coefficient
#             + backward_scattering_coefficient
#             - extinction_coefficient_kd
#         )
#         - backward_scattering_coefficient * sstr
#     )
#     v1 = (
#         ss
#         - (
#             parameter_5
#             * (
#                 scatter_absorption_coefficient
#                 + backward_scattering_coefficient
#                 + extinction_coefficient_kd
#             )
#         )
#         / sigma
#     )
#     v2 = (
#         ss
#         - backward_scattering_coefficient
#         - (parameter_5 / sigma) * (u1 + extinction_coefficient_kd)
#     )

#     parameter_6 = (1 / d1) * (
#         (v1 / leaf_extinction_factor_1) * (u1 - diffuse_scattering_coefficient)
#         - (
#             scatter_absorption_coefficient
#             + backward_scattering_coefficient
#             - diffuse_scattering_coefficient
#         )
#         * leaf_extinction_factor_2
#         * v2
#     )

#     parameter_7 = (-1 / d1) * (
#         (v1 * leaf_extinction_factor_1) * (u1 + diffuse_scattering_coefficient)
#         - (
#             scatter_absorption_coefficient
#             + backward_scattering_coefficient
#             + diffuse_scattering_coefficient
#         )
#         * leaf_extinction_factor_2
#         * v2
#     )

#     parameter_8 = (
#         sstr
#         * (
#             scatter_absorption_coefficient
#             + backward_scattering_coefficient
#             + extinction_coefficient_kd
#         )
#         - backward_scattering_coefficient * ss
#     )
#     v3 = (
#         sstr
#         + backward_scattering_coefficient * ground_reflectance
#         - (parameter_8 / sigma) * (u2 - extinction_coefficient_kd)
#     ) * leaf_extinction_factor_2

#     parameter_9 = (-1 / d2) * (
#         (parameter_8 / (sigma * leaf_extinction_factor_1))
#         * (u2 + diffuse_scattering_coefficient)
#         + v3
#     )

#     parameter_10 = (1 / d2) * (
#         ((parameter_8 * leaf_extinction_factor_1) / sigma)
#         * (u2 - diffuse_scattering_coefficient)
#         + v3
#     )

#     return [
#         parameter_5,
#         parameter_6,
#         parameter_7,
#         parameter_8,
#         parameter_9,
#         parameter_10,
#     ]


# def calculate_absorbed_shortwave_radiation(
#     plant_area_index_sum: NDArray[np.float32],
#     leaf_orientation_coefficient: float,
#     leaf_reluctance_shortwave: float,
#     leaf_transmittance_shortwave: float,
#     clumping_factor: float,
#     ground_reflectance: float,
#     slope: NDArray[np.float32],
#     aspect: NDArray[np.float32],
#     latitude: NDArray[np.float32],
#     longitude: NDArray[np.float32],
#     year: int,
#     month: int,
#     day: int,
#     local_time: float,
#     topofcanopy_shortwave_radiation: NDArray[np.float32],
#     topofcanopy_diffuse_radiation: NDArray[np.float32],
#     leaf_inclination_angle_coefficient: float,
# ) -> dict[str, NDArray[np.float32]]:
#     """Calculate absorbed shortwave radiation for ground and canopy.

#     The initial model (micropoint, Maclean) is for a time series and includes a loop.
#     Here, only for one time step at the moement.

#     Args:
#         plant_area_index_sum: Plant area index vertically summed, [m2 m-2]
#         leaf_orientation_coefficient: Coefficient that represents how vertically or
#             horizontally the leaves of the canopy are orientated and controls how much
#             direct radiation is transmitted through the canopy at a given solar angle
#             (when the sun is low above the horizon, less radiation is transmitted
#             through vertically orientated leaves)
#         leaf_reluctance_shortwave: Leaf reluctance of shortwave radiation (0-1)
#         leaf_transmittance_shortwave: Leaf transmittance od shortwave radiation (0-1)
#         clumping_factor: Canopy clumping factor
#         ground_reflectance: Ground reflectance (0-1)
#         slope: Slope of the ground surface (decimal degrees from horizontal)
#         aspect: Aspect of the ground surface (decimal degrees from north)
#         latitude: Latitude in decimal degree
#         longitude: Longitude in decimal degree
#         year: Year
#         month: Month
#         day: Day
#         local_time: Local time
#         topofcanopy_shortwave_radiation: Shortwave radiation, [W m-2]
#         topofcanopy_diffuse_radiation: Diffuse radiation, [W m-2]
#         leaf_inclination_angle_coefficient: Leaf inclination angle coefficient

#     Returns:
#         dictionary with ground and canopy absorbed radiation and albedo
#     """

#     absorbed_shortwave_radiation = {}

#     # Calculate time-invariant variables
#     adjusted_plant_area_index = plant_area_index_sum / (1 - clumping_factor)

#     scattering_albedo = leaf_reluctance_shortwave + leaf_transmittance_shortwave
#     scatter_absorption_coefficient = 1 - scattering_albedo
#     delta_reflectance_transmittance = (
#         leaf_reluctance_shortwave - leaf_transmittance_shortwave
#     )

#     # Calculate mean_inclination_angle where leaf orientation coefficient is not = 1.0
#     mean_inclination_angle_full = np.where(
#         leaf_orientation_coefficient != 1.0,
#         9.65 * np.power((3 + leaf_orientation_coefficient), -1.65),
#         1.0 / 3.0,  # note: value from micropoint
#     )
#     # Clip mean_inclination_angle values to be at most π/2
#     mean_inclination_angle = np.minimum(mean_inclination_angle_full, np.pi / 2)

#     # Calculate inclination distribution
#     inclination_distribution = np.cos(mean_inclination_angle) ** 2

#     # Calculate scattering coefficients
#     backward_scattering_coefficient = 0.5 * (
#         scattering_albedo + inclination_distribution * delta_reflectance_transmittance
#     )
#     diffuse_scattering_coefficient = np.sqrt(
#         scatter_absorption_coefficient**2
#         + 2 * scatter_absorption_coefficient * backward_scattering_coefficient
#     )

#     # Calculate two-stream parameters (diffuse)
#     diffuse_radiation_parameters = calculate_diffuse_radiation_parameters(
#         adjusted_plant_area_index=adjusted_plant_area_index,
#         scatter_absorption_coefficient=scatter_absorption_coefficient,
#         backward_scattering_coefficient=backward_scattering_coefficient,
#         diffuse_scattering_coefficient=diffuse_scattering_coefficient,
#         ground_reflectance=ground_reflectance,
#     )
#     p1, p2, p3, p4 = diffuse_radiation_parameters

#     # Downward diffuse stream
#     clumping_factor_diffuse = clumping_factor**2
#     diffuse_downward_radiation_full = (
#         (1 - clumping_factor_diffuse)
#         * (
#             p3 * np.exp(-diffuse_scattering_coefficient * adjusted_plant_area_index)
#             + p4 * np.exp(diffuse_scattering_coefficient * adjusted_plant_area_index)
#         )
#         + clumping_factor_diffuse,
#     )
#     diffuse_downward_radiation = np.minimum(diffuse_downward_radiation_full, 1.0)

#     # Calculate solar variables
#     solar_position = calculate_solar_position(
#         latitude=latitude,
#         longitude=longitude,
#         year=year,
#         month=month,
#         day=day,
#         local_time=local_time,
#     )
#     zenith, azimuth = solar_position
#     solar_index = calculate_solar_index(
#         slope=slope,
#         aspect=aspect,
#         zenith=zenith,
#         azimuth=azimuth,
#     )
#     zenith = np.minimum(zenith, 90.0)

#     # Calculate canopy extinction coefficients
#     canopy_extinction_coefficients = calculate_canopy_extinction_coefficients(
#         solar_zenith_angle=zenith,
#         leaf_inclination_angle_coefficient=leaf_inclination_angle_coefficient,
#         solar_index=solar_index,
#     )
#     k, kd, k0 = canopy_extinction_coefficients
#     kc = kd / k0

#     # Calculate two-stream parameters (direct)
#     sigma = (
#         kd**2
#         + backward_scattering_coefficient**2
#         - (scatter_absorption_coefficient + backward_scattering_coefficient) ** 2
#     )

#     direct_radiation_parameters = calculate_direct_radiation_parameters(
#         adjusted_plant_area_index=adjusted_plant_area_index,
#         scattering_albedo=scattering_albedo,
#         scatter_absorption_coefficient=scatter_absorption_coefficient,
#         backward_scattering_coefficient=backward_scattering_coefficient,
#         inclination_distribution=inclination_distribution,
#         delta_reflectance_transmittance=delta_reflectance_transmittance,
#         diffuse_scattering_coefficient=diffuse_scattering_coefficient,
#         ground_reflectance=ground_reflectance,
#         extinction_coefficient_k=k,
#         extinction_coefficient_kd=kd,
#         sigma=sigma,
#     )
#     p5, p6, p7, p8, p9, p10 = direct_radiation_parameters

#     # Calculate albedo
#     albedo_diffuse = (1 - clumping_factor_diffuse) * (
#         p1 + p2
#     ) + clumping_factor_diffuse * ground_reflectance
#     clumping_factor_beam = clumping_factor**kc
#     albedo_beam = (1 - clumping_factor_beam) * (
#         p5 / sigma + p6 + p7
#     ) + clumping_factor_beam * ground_reflectance
#     albedo_beam = np.where(np.isinf(albedo_beam), albedo_diffuse, albedo_beam)

#     beam_radiation = (
#         topofcanopy_shortwave_radiation - topofcanopy_diffuse_radiation
#     ) / np.cos(zenith * np.pi / 180)

#     # Contribution of direct to downward diffuse stream
#     diffuse_beam_radiation = (1 - clumping_factor_beam) * (
#         (p8 / sigma) * np.exp(-kd * adjusted_plant_area_index)
#         + p9 * np.exp(-diffuse_scattering_coefficient * adjusted_plant_area_index)
#         + p10 * np.exp(diffuse_scattering_coefficient * adjusted_plant_area_index)
#     )
#     diffuse_beam_radiation = np.clip(diffuse_beam_radiation, 0.0, 1.0)

#     # Downward direct stream
#     downward_direct_stream = (1 - clumping_factor_beam) * np.exp(
#         -kd * adjusted_plant_area_index
#     ) + clumping_factor_beam
#     downward_direct_stream = np.minimum(downward_direct_stream, 1)

#     # Radiation absorbed by ground
#     diffuse_radiation_ground = (1 - ground_reflectance) * (
#         diffuse_beam_radiation * beam_radiation
#         + diffuse_downward_radiation * topofcanopy_diffuse_radiation
#     )

#     direct_radiation_ground = (1 - ground_reflectance) * (
#         downward_direct_stream * beam_radiation * solar_index
#     )

#     ground_shortwave_absorption_veg = diffuse_radiation_ground +
# direct_radiation_ground

#     # Radiation absorbed by canopy TODO coordinate with plants model
#     diffuse_radiation_canopy = (1 - albedo_diffuse) * topofcanopy_diffuse_radiation
#     direct_radiation_canopy = (1 - albedo_beam) * beam_radiation * solar_index
#     canopy_shortwave_absorption_veg = diffuse_radiation_canopy +
# direct_radiation_canopy

#     albedo_veg = np.clip(
#         1 - (canopy_shortwave_absorption_veg / topofcanopy_shortwave_radiation),
#         0.01,
#         0.99,
#     )

#     # where plant area index not >0
#     ground_shortwave_absorption_no_veg = (1 - ground_reflectance) * (
#         topofcanopy_diffuse_radiation + solar_index * beam_radiation
#     )

#     ground_shortwave_absorption = np.where(
#         plant_area_index_sum > 0,
#         ground_shortwave_absorption_veg,
#         ground_shortwave_absorption_no_veg,
#     )
#     canopy_shortwave_absorption = np.where(
#         plant_area_index_sum > 0,
#         canopy_shortwave_absorption_veg,
#         ground_shortwave_absorption_no_veg,
#     )
#     albedo = np.where(plant_area_index_sum > 0, albedo_veg, ground_reflectance)

#     # return values for positive shortwave radiation, else 0.
#     absorbed_shortwave_radiation["ground_shortwave_absorption"] = np.where(
#         topofcanopy_shortwave_radiation > 0,
#         ground_shortwave_absorption,
#         0.0,
#     ).squeeze()  # TODO for some reason I have extra dimension here
#     absorbed_shortwave_radiation["canopy_shortwave_absorption"] = np.where(
#         topofcanopy_shortwave_radiation > 0,
#         canopy_shortwave_absorption,
#         0.0,
#     )

#     absorbed_shortwave_radiation["albedo"] = np.where(
#         topofcanopy_shortwave_radiation > 0, albedo, leaf_reluctance_shortwave
#     )

#     return absorbed_shortwave_radiation


# # longwave radiation
# def calculate_canopy_longwave_emission(
#     leaf_emissivity: float,
#     canopy_temperature: NDArray[np.float32],
#     stefan_boltzmann_constant: float,
#     zero_Celsius: float,
# ) -> NDArray[np.float32]:
#     """Calculate mean canopy longwave emission.

#     Args:
#         leaf_emissivity: leaf emissivity, dimensionless
#         canopy_temperature: Canopy temperature, [C]
#         stefan_boltzmann_constant: Stefan boltzmann constant
#         zero_Celsius: Celsius to Kelvin conversion factor

#     Returns:
#         longwave emission from canopy, [W m-2]
#     """

#     return (
#         leaf_emissivity
#         * stefan_boltzmann_constant
#         * (canopy_temperature + zero_Celsius) ** 4
#     )


# def calculate_longwave_emission_ground(
#     ground_emissivity: float,
#     radiation_transmission_coefficient: NDArray[np.float32],
#     longwave_downward_radiation_sky: NDArray[np.float32],
#     canopy_longwave_emission: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate longwave emission from ground surface.

#     Args:
#         ground_emissivity: Ground emissivity, dimensionless
#         radiation_transmission_coefficient: Radiation transmission coefficient
#         longwave_downward_radiation_sky: Longwave downward radiation from sky, [W m-2]
#         canopy_longwave_emission: longwave emission from canopy, [W m-2]

#     Returns:
#         longwave emission from ground surface, [W m-2]
#     """
#     return ground_emissivity * (
#         radiation_transmission_coefficient * longwave_downward_radiation_sky
#         + (1 - radiation_transmission_coefficient) * canopy_longwave_emission
#     )


# r"""The ``models.abiotic.soil_energy_balance`` module calculates the soil energy
#  balance
# for the Virtual Ecosystem.

# The first part of this module determines the energy balance at the surface.
# :func:`~virtual_ecosystem.models.abiotic.
# soil_energy_balance.calculate_soil_heat_balance`
# calculates how incoming solar radiation that reaches the surface is partitioned in
# sensible, latent, and ground heat flux. Further, longwave emission is calculated and
#  the
# topsoil temperature is updated.

# The second part determines the soil temperature profile at different depths. We
# divide the soil into discrete layers to numerically solve the time-dependent
# differential equation that describes soil temperature as a function of depth
# and time (see TODO THIS FUNCTION for details).
# """

# import numpy as np
# from numpy.typing import NDArray
# from pint import Quantity

# from virtual_ecosystem.core.constants import CoreConsts
# from virtual_ecosystem.core.core_components import LayerStructure
# from virtual_ecosystem.core.data import Data
# from virtual_ecosystem.models.abiotic.constants import AbioticConsts
# from virtual_ecosystem.models.abiotic.energy_balance import
# calculate_longwave_emission


# def calculate_soil_absorption(
#     shortwave_radiation_surface: NDArray[np.float32],
#     surface_albedo: float | NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate soil absorption of shortwave radiation.

#     The amount of shortwave radiation that is absorbed by the topsoil layer is a
#     function of incoming radiation and  surface albedo. In reality, surface albedo is
#     modulated by soil moisture. The current implementation of soil absorption assumes
#     constant albedo within each grid cell because the radiation that reaches the
# surface
#     below the canopy is typically quite small (<5%).

#     Args:
#         shortwave_radiation_surface: Shortwave radiation that reaches surface, [W m-2]
#         surface_albedo: Surface albedo, dimensionless.

#     Returns:
#         shortwave radiation absorbed by soil surface, [W m-2]
#     """

#     return shortwave_radiation_surface * (1 - surface_albedo)


# def calculate_sensible_heat_flux_soil(
#     air_temperature_surface: NDArray[np.float32],
#     topsoil_temperature: NDArray[np.float32],
#     molar_density_air: NDArray[np.float32],
#     specific_heat_air: NDArray[np.float32],
#     aerodynamic_resistance: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     r"""Calculate sensible heat flux from soil surface.

#     The sensible heat flux from the soil surface is given by:

#     :math:`H_{S} = \frac {\rho_{air} C_{air} (T_{S} - T_{b}^{A})}{r_{A}}`

#     Where :math:`T_{S}` is the soil surface temperature, :math:`T_{b}^{A}` is the
#     temperature of the bottom air layer and :math:`r_{A}` is the aerodynamic
# resistance
#     of the soil surface, given by

#     :math:`r_{A} = \frac {C_{S}}{u_{b}}`

#     Where :math:`u_{b}` is the wind speed in the bottom air layer and :math:`C_{S}` is
#     the soil surface heat transfer coefficient.

#     Args:
#         air_temperature_surface: Air temperature near the surface, [K]
#         topsoil_temperature: Topsoil temperature, [K]
#         molar_density_air: Molar density of air, [mol m-3]
#         specific_heat_air: Specific heat of air, [J mol-1 K-1]
#         aerodynamic_resistance: Aerodynamic resistance near the surface

#     Returns:
#         Sensible heat flux from topsoil, [W m-2]
#     """

#     return (
#         molar_density_air
#         * specific_heat_air
#         * (topsoil_temperature - air_temperature_surface)
#     ) / aerodynamic_resistance


# def calculate_latent_heat_flux_from_soil_evaporation(
#     soil_evaporation: NDArray[np.float32],
#     latent_heat_vapourisation: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate latent heat flux from soil evaporation.

#     We assume that 1 mm of evaporated water is equivalent to 1 kg of water.

#     Args:
#         soil_evaporation: Soil evaporation, [mm]
#         latent_heat_vapourisation: Latent heat of vapourisation, [J kg-1]

#     Returns:
#         latent heat flux from topsoil, [W m-2]
#     """

#     return soil_evaporation * latent_heat_vapourisation


# def calculate_ground_heat_flux(
#     soil_absorbed_radiation: NDArray[np.float32],
#     topsoil_longwave_emission: NDArray[np.float32],
#     topsoil_sensible_heat_flux: NDArray[np.float32],
#     topsoil_latent_heat_flux: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate ground heat flux.

#     The ground heat flux is calculated as the residual of splitting incoming raditaion
#     into emitted longwave radiation, and sensible and latent heat flux. A positive
#     ground heat flux means a warming of the soil, a negative flux indicates a
# cooling of
#     the soil.

#     Args:
#         soil_absorbed_radiation: Shortwave radiation absorbed by topsoil, [W m-2]
#         topsoil_longwave_emission: Longwave radiation emitted by topsoil, [W m-2]
#         topsoil_sensible_heat_flux: Sensible heat flux from topsoil, [W m-2]
#         topsoil_latent_heat_flux: Latent heat flux from topsoil, [W m-2]

#     Returns:
#         ground heat flux, [W m-2]
#     """

#     return (
#         soil_absorbed_radiation
#         - topsoil_longwave_emission
#         - topsoil_sensible_heat_flux
#         - topsoil_latent_heat_flux
#     )


# def update_surface_temperature(
#     topsoil_temperature: NDArray[np.float32],
#     surface_net_radiation: NDArray[np.float32],
#     surface_layer_depth: float | NDArray[np.float32],
#     grid_cell_area: float,
#     update_interval: Quantity,
#     specific_heat_capacity_soil: float | NDArray[np.float32],
#     volume_to_weight_conversion: float | NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Update surface temperature after exchange of radiation.

#     This function calculates the surface temperature after absorption of
#     shortwave radiation, emission of longwave radiation, and surface fluxes. This
#     process usually happens in the top few centimeters of the soil column, which is
# much
#     less than the thickness of the upper soil layer of the current layer
# implementation.
#     In the simulation flow, we therefore set the topsoil layer depth to 0.05, TODO
# merge
#     this into temperature profile.

#     Args:
#         topsoil_temperature: Topsoil temperature
#         surface_net_radiation: Longwave or shortwave radiation that enters
#             (positive) or leaves (negative) the topsoil, [W m-2]
#         surface_layer_depth: Topsoil layer depth, [m]
#         grid_cell_area: Grid cell area, [m2]
#         update_interval: Update interval to convert between W and J, [s]
#         specific_heat_capacity_soil: Soil specific heat capacity, [J kg-1 K-1]
#         volume_to_weight_conversion: Factor to convert between soil volume and weight
#  in
#             kilograms

#     Returns:
#         topsoil temperature, [C]
#     """
#     # Calculate the mass of the soil that is absorbing the radiation
#     topsoil_mass = surface_layer_depth * grid_cell_area * volume_to_weight_conversion

#     # Convert radiation to energy stored in soil in Kelvin
#     temperature_change = (surface_net_radiation * update_interval) / (
#         topsoil_mass * specific_heat_capacity_soil
#     )

#     # Add temperature change to current top soil temperature
#     return topsoil_temperature + temperature_change


# def calculate_soil_heat_balance(
#     data: Data,
#     time_index: int,
#     layer_structure: LayerStructure,
#     update_interval: Quantity,
#     abiotic_consts: AbioticConsts,
#     core_consts: CoreConsts,
# ) -> dict[str, NDArray[np.float32]]:
#     """Calculate soil heat balance.

#     This function performs a series of calculations to solve the energy balance at the
#     surface at the interface between soil and atmoshere:

#     * calculate soil absorption (:math:`R_{N{} * (1-albedo)`)
#     * calculate sensible heat flux (convective flux from soil to atmosphere above)
#     * calculate latent heat flux (conversion of soil evaporation)
#     * calculate ground heat flux (conductive flux)
#     * update topsoil temperature

#     The function takes an instance of data object, AbioticConsts and CoreConsts which
#     must provide the following inputs:

#     * soil_temperature: Soil temperature, [C]
#     * air_temperature: Air temperature, [C]
#     * topofcanopy_radiation: Shortwave radiation that reaches canopy, [W m-2]
#     * soil_evaporation: Soil evaporation, [mm]
#     * soil_emissivity: Soil emissivity, dimensionless
#     * surface_albedo: Surface albedo, dimensionless
#     * molar_density_air: Molar density of air, [mol m-3]
#     * specific_heat_air: Specific heat of air, [J mol-1 K-1]
#     * aerodynamic_resistance_surface: Aerodynamic resistance near the surface
#     * stefan_boltzmann: Stefan Boltzmann constant, [W m-2 K-4]
#     * latent_heat_vapourisation: Latent heat of vapourisation, [kJ kg-1]
#     * surface_layer_depth: Topsoil layer depth, [m]
#     * grid_cell_area: Grid cell area, [m2]
#     * specific_heat_capacity_soil: Soil specific heat capacity, [J kg-1 K-1]
#     * volume_to_weight_conversion: Factor to convert between soil volume and weight
#  [kg]

#     Args:
#         data: The core data object
#         time_index: time index
#         update_interval: Update interval, [s]
#         layer_structure: The LayerStructure instance for the simulation.
#         abiotic_consts: set of constants specific to abiotic model
#         core_consts: set of constants that are shared across the model

#     Returns:
#         A dictionary with soil shortwave absorption, soil longwave emission, sensible
#         and latent heat flux from the soil, ground heat flux, and updated topsoil
#         temperature
#     """

#     topsoil_layer_index = layer_structure.index_topsoil
#     surface_layer_index = layer_structure.index_surface

#     output = {}

#     # Calculate soil absorption of shortwave radiation, [W m-2]
#     shortwave_radiation_surface = data["topofcanopy_radiation"].isel(
#         time_index=time_index
#     ) - (data["canopy_absorption"].sum(dim="layers"))
#     soil_absorption = calculate_soil_absorption(
#         shortwave_radiation_surface=shortwave_radiation_surface.to_numpy(),
#         surface_albedo=abiotic_consts.surface_albedo,
#     )
#     output["soil_absorption"] = soil_absorption
#     output["shortwave_radiation_surface"] = shortwave_radiation_surface.to_numpy()

#     # Calculate longwave emission from topsoil, [W m-2]; note that this is the soil
#     # temperature of the previous time step
#     # VIVI - all of the subsets extract a 2D (1, n_cells) array, and they are intended
#     # to end up as a 1D (n_cells) array in the data, so I'm using squeeze() to
# simplify
#     # them to 1D. Could use [0] - it's shorter and maybe more efficient, but it's less
#     # obvious?
#     longwave_emission_soil = calculate_longwave_emission(
#         temperature=data["soil_temperature"][
# topsoil_layer_index].to_numpy().squeeze(),
#         emissivity=abiotic_consts.soil_emissivity,
#         stefan_boltzmann=core_consts.stefan_boltzmann_constant,
#     )
#     output["longwave_emission_soil"] = longwave_emission_soil

#     # Calculate sensible heat flux from soil to lowest atmosphere layer, [W m-2]
#     sensible_heat_flux_soil = calculate_sensible_heat_flux_soil(
#         air_temperature_surface=data["air_temperature"][surface_layer_index]
#         .to_numpy()
#         .squeeze(),
#         topsoil_temperature=data["soil_temperature"][topsoil_layer_index]
#         .to_numpy()
#         .squeeze(),
#         molar_density_air=data["molar_density_air"][surface_layer_index]
#         .to_numpy()
#         .squeeze(),
#         specific_heat_air=data["specific_heat_air"][surface_layer_index]
#         .to_numpy()
#         .squeeze(),
#         aerodynamic_resistance=data["aerodynamic_resistance_surface"].to_numpy(),
#     )
#     output["sensible_heat_flux_soil"] = sensible_heat_flux_soil

#     # Convert soil evaporation to latent heat flux to lowest atmosphere layer, [W m-2]
#     latent_heat_flux_soil = calculate_latent_heat_flux_from_soil_evaporation(
#         soil_evaporation=data["soil_evaporation"].to_numpy(),
#         latent_heat_vapourisation=(
#             data["latent_heat_vapourisation"][surface_layer_index].to_numpy(
# ).squeeze()
#         ),
#     )
#     output["latent_heat_flux_soil"] = latent_heat_flux_soil

#     # Determine ground heat flux as the difference as
#     # incoming radiation -  sensible and latent heat flux - longwave emission
#     ground_heat_flux = calculate_ground_heat_flux(
#         soil_absorbed_radiation=soil_absorption,
#         topsoil_longwave_emission=longwave_emission_soil,
#         topsoil_sensible_heat_flux=sensible_heat_flux_soil,
#         topsoil_latent_heat_flux=latent_heat_flux_soil,
#     )
#     output["ground_heat_flux"] = ground_heat_flux

#     # Calculate net surface radiation, [W m-2]
#     surface_net_radiation = (
#         data["shortwave_radiation_surface"].to_numpy()
#         - longwave_emission_soil
#         - sensible_heat_flux_soil
#         - latent_heat_flux_soil
#         - ground_heat_flux
#     )

#     # Update surface temperature, [C]
#     new_surface_temperature = update_surface_temperature(
#         topsoil_temperature=data["soil_temperature"][topsoil_layer_index]
#         .to_numpy()
#         .squeeze(),
#         surface_net_radiation=surface_net_radiation,
#         surface_layer_depth=abiotic_consts.surface_layer_depth,
#         grid_cell_area=data.grid.cell_area,
#         update_interval=update_interval,
#         specific_heat_capacity_soil=abiotic_consts.specific_heat_capacity_soil,
#         volume_to_weight_conversion=abiotic_consts.volume_to_weight_conversion,
#     )
#     output["new_surface_temperature"] = new_surface_temperature

#     return output


# def calculate_soil_temperature_profile():
#     r"""
#     Each layer
#     is assigned a node, :math:`i`, at depth, :math:`z_{i}`, and with heat storage,
#     :math:`C_{h_{i}}`, and nodes are numbered sequentially downward such that node
#    :math:`i+1` represents the node for the soil layer immediately below. Conductivity,
#     :math:`k_{i}`, represents conductivity between nodes :math:`i` and :math:`i+1`.
#     The energy balance equation for node :math:`i` is then given by

#     .. math::
#         \kappa_{i}(T_{i+1} - T_{i})- \kappa_{i-1}(T_{i} - T_{i-1})
#         = \frac{C_{h_{i}}(T_{i}^{j+1} - T_{i}^{j})(z_{i+1} - z_{i-1})}{2 \Delta t}

#     where :math:`\Delta t` is the time increment, conductance,
#     :math:`\kappa_{i}=k_{i}/(z_{i+1} - z_{i})`, and superscript :math:`j` indicates
#     the time at which temperature is determined. This equation can be re-arranged and
#     solved for :math:`T_{j+1}` by Gaussian elimination using the Thomas algorithm."""

# r"""The wind module calculates the above- and within-canopy wind profile for the
# Virtual Ecosystem. The wind profile determines the exchange of heat, water, and
# :math:`CO_{2}` between soil and atmosphere below the canopy as well as the exchange
# with
# the atmosphere above the canopy.

# TODO replace leaf area index by plant area index when we have more info about vertical
# distribution of leaf and woody parts
# TODO change temperatures to Kelvin
# """

# import numpy as np
# from numpy.typing import NDArray

# from virtual_ecosystem.core.logger import LOGGER


# def calculate_zero_plane_displacement(
#     canopy_height: NDArray[np.float32],
#     leaf_area_index: NDArray[np.float32],
#     zero_plane_scaling_parameter: float,
# ) -> NDArray[np.float32]:
#     """Calculate zero plane displacement height, [m].

#     The zero plane displacement height is a concept used in micrometeorology to
# describe
#     the flow of air near the ground or over surfaces like a forest canopy or crops. It
#     represents the height above the actual ground where the wind speed is
# theoretically
#     reduced to zero due to the obstruction caused by the roughness elements (like
# trees
#     or buildings). Implementation after :cite:t:`maclean_microclimc_2021`.

#     Args:
#         canopy_height: Canopy height, [m]
#         leaf_area_index: Total leaf area index, [m m-1]
#         zero_plane_scaling_parameter: Control parameter for scaling d/h, dimensionless
#             :cite:p:`raupach_simplified_1994`

#     Returns:
#         Zero plane displacement height, [m]
#     """

#     # Select grid cells where vegetation is present
#     displacement = np.where(leaf_area_index > 0, leaf_area_index, np.nan)

#     # Calculate zero displacement height
#     scale_displacement = np.sqrt(zero_plane_scaling_parameter * displacement)
#     zero_plane_displacement = (
#         (1 - (1 - np.exp(-scale_displacement)) / scale_displacement) * canopy_height,
#     )

#     # No displacement in absence of vegetation
#     return np.nan_to_num(zero_plane_displacement, nan=0.0).squeeze()


# def calculate_roughness_length_momentum(
#     canopy_height: NDArray[np.float32],
#     plant_area_index: NDArray[np.float32],
#     zero_plane_displacement: NDArray[np.float32],
#     diabatic_correction_heat: NDArray[np.float32],
#     substrate_surface_drag_coefficient: float,
#     drag_coefficient: float,
#     min_roughness_length: float,
#     von_karman_constant: float,
# ) -> NDArray[np.float32]:
#     """Calculate roughness length governing momentum transfer, [m].

#     Roughness length is defined as the height at which the mean velocity is zero due
# to
#     substrate roughness. Real surfaces such as the ground or vegetation are not smooth
#     and often have varying degrees of roughness. Roughness length accounts for that
#     effect. Implementation after :cite:t:`maclean_microclimc_2021`.

#     Args:
#         canopy_height: Canopy height, [m]
#         plant_area_index: Total plant area index, [m m-1]
#         zero_plane_displacement: Height above ground within the canopy where the wind
#             profile extrapolates to zero, [m]
#         diabatic_correction_heat: Diabatic correction factor for heat
#         substrate_surface_drag_coefficient: Substrate-surface drag coefficient,
#             dimensionless
#         drag_coefficient: drag coefficient
#         min_roughness_length: Minimum roughness length, [m]
#         von_karman_constant: Von Karman's constant, dimensionless constant describing
#             the logarithmic velocity profile of a turbulent fluid near a no-slip
#             boundary.

#     Returns:
#         Momentum roughness length, [m]
#     """

#     # Calculate ratio of wind velocity to friction velocity
#     ratio_wind_to_friction_velocity = np.sqrt(
#         substrate_surface_drag_coefficient + (drag_coefficient * plant_area_index) / 2
#     )

#     # calculate initial roughness length
#     initial_roughness_length = (
#         (canopy_height - zero_plane_displacement)
#         * np.exp(-von_karman_constant / ratio_wind_to_friction_velocity)
#         * np.exp(diabatic_correction_heat)
#     )

#     # If roughness smaller than the substrate surface drag coefficient, set to value
#  to
#     # the substrate surface drag coefficient
#     roughness_length = np.where(
#         initial_roughness_length < substrate_surface_drag_coefficient,
#         substrate_surface_drag_coefficient,
#         initial_roughness_length,
#     )
#     # If roughness length in nan, zero or below sero, set to minimum value
#     roughness_length = np.nan_to_num(roughness_length, nan=min_roughness_length)
#     return np.where(roughness_length <= 0, min_roughness_length, roughness_length)


# def calculate_monin_obukov_length(
#     air_temperature: NDArray[np.float32],
#     friction_velocity: NDArray[np.float32],
#     sensible_heat_flux: NDArray[np.float32],
#     specific_heat_air: NDArray[np.float32],
#     density_air: NDArray[np.float32],
#     zero_degree: float,
#     von_karman_constant: float,
#     gravity: float,
# ) -> NDArray[np.float32]:
#     r"""Calculate Monin-Obukov length.

#     The Monin-Obukhov length (:math:`L`) is given by:

#     :math:`L = -(\rho cp u_{*}^{3} T_{air})/(k g H)`

#     Foken, T, 2008: Micrometeorology. Springer, Berlin, Germany.

#     Note that :math:`L` gets very small for very low ustar values with implications
#     for subsequent functions using :math:`L` as input. It is recommended to filter
#     data and exclude low ustar values (:math:`u_{*}` < ~0.2) beforehand.

#     Args:
#         air_temperature: Air temperature, [C]
#         friction_velocity: Friction velocity, [m s-1]
#         sensible_heat_flux: Sensible heat flux, [W m-2]
#         specific_heat_air: Specific heat of air, [J K-1 kg-1]
#         density_air: Sensity of air, [kg m-3]
#         zero_degree: Celsius to Kelvin conversion
#         von_karman_constant: Von Karman constant, dimensionless
#         gravity: Gravitational acceleration, [m s-2]

#     Returns:
#         Monin-Obukov length, [m]
#     """
#     if np.any(sensible_heat_flux == 0):
#         to_raise = ValueError("The sensible heat flux must not be zero!")
#         LOGGER.error(to_raise)
#         raise to_raise

#     temperature_kelvin = air_temperature + zero_degree
#     return -(
#         density_air * specific_heat_air * friction_velocity**3 * temperature_kelvin
#     ) / (von_karman_constant * gravity * sensible_heat_flux)


# def calculate_stability_parameter(
#     reference_height: NDArray[np.float32],
#     zero_plance_displacement: NDArray[np.float32],
#     monin_obukov_length: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate stability parameter zeta.

#     Zeta is a parameter in Monin-Obukov Theory that characterizes stratification in
#     the lower atmosphere:

#     zeta = (reference_height - zero_plance_displacenemt)/ monin-obukov_length

#     Args:
#         reference_height: Reference height, [m]
#         zero_plance_displacement: Zero plance displacement height, [m]
#         monin_obukov_length: Monin-Obukov length, [m]

#     Returns:
#         stability parameter zeta
#     """
#     return (reference_height - zero_plance_displacement) / monin_obukov_length


# def calculate_diabatic_correction_factors(
#     stability_parameter: NDArray[np.float32],
#     stability_formulation: str,
# ) -> dict[str, NDArray[np.float32]]:
#     r"""Integrated Stability Correction Functions for Heat and Momentum.

#     Dimensionless stability functions needed to correct deviations from the
# exponential
#     wind profile under non-neutral conditions. The functions give the integrated form
#  of
#     the universal functions. They depend on the value of the stability parameter
#     :math:`\zeta`.

#     The integration of the universal functions is:

#     :math:`\Psi = -x * \zeta`

#     for stable atmospheric conditions (:math:`\zeta >= 0`), and

#     :math:`\Psi = 2 * log( (1 + y) / 2)`

#     for unstable atmospheric conditions (:math:`\zeta < 0`).

#     The different formulations differ in their value of x and y.

#     References:
#     Dyer, A.J., 1974: A review of flux-profile relationships.
#     Boundary-Layer Meteorology 7, 363-372.

#     Dyer, A. J., Hicks, B.B., 1970: Flux-Gradient relationships in the
#     constant flux layer. Quart. J. R. Meteorol. Soc. 96, 715-721.

#     Businger, J.A., Wyngaard, J. C., Izumi, I., Bradley, E. F., 1971:
#     Flux-Profile relationships in the atmospheric surface layer.
#     J. Atmospheric Sci. 28, 181-189.

#     Paulson, C.A., 1970: The mathematical representation of wind speed
#     and temperature profiles in the unstable atmospheric surface layer.
#     Journal of Applied Meteorology 9, 857-861.

#     Foken, T, 2008: Micrometeorology. Springer, Berlin, Germany.

#     Args:
#         stability_parameter: Stability parameter zeta (-)
#         stability_formulation: Formulation for the stability function. Either
# Dyer_1970
#             or Businger_1971

#     Returns:
#         psi_h, the value of the stability function for heat and water vapor (-), and
#         psi_m, the value of the stability function for momentum (-)
#     """

#     # Choose formulation
#     if stability_formulation == "Businger_1971":
#         x_h, x_m = -7.8, -6
#         y_h = 0.95 * np.sqrt(1 - 11.6 * stability_parameter)
#         y_m = np.power(1 - 19.3 * stability_parameter, 0.25)

#     elif stability_formulation == "Dyer_1970":
#         x_h, x_m = -5, -5
#         y_h = np.sqrt(1 - 16 * stability_parameter)
#         y_m = np.power(1 - 16 * stability_parameter, 0.25)

#     else:
#         raise ValueError(f"Unknown formulation: {stability_formulation}")

#     psi_h = np.where(
#         stability_parameter >= 0, x_h * stability_parameter, 2 * np.log((1 + y_h) / 2)
#     )
#     psi_m = np.where(
#         stability_parameter >= 0,
#         x_m * stability_parameter,
#         (
#             2 * np.log((1 + y_m) / 2)
#             + np.log((1 + y_m**2) / 2)
#             - 2 * np.arctan(y_m)
#             + np.pi / 2
#         ),
#     )

#     return {"psi_h": psi_h, "psi_m": psi_m}


# def calculate_diabatic_influence_heat(
#     stability_parameter: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate the diabatic influencing factor for heat.

#     Args:
#         stability_parameter: Stability parameter zeta

#     Returns:
#         Diabatic influencing factor for heat (phih)
#     """
#     # Initialize `phih` with zeros
#     phih = np.zeros_like(stability_parameter)

#     # Apply the calculation where stability_parameter < 0
#     phim = np.where(
#         stability_parameter < 0,
#         1 / np.power((1.0 - 16.0 * stability_parameter), 0.25),
#         1,  # Default value for non-negative stability_parameter to avoid indexing
# issue
#     )
#     phih_non_negative = 1 + (6.0 * stability_parameter) / (1.0 + stability_parameter)
#     phih = np.where(stability_parameter < 0, np.power(phim, 2.0), phih_non_negative)

#     # Clip the values of `phih` to be between 0.5 and 1.5
#     return np.clip(phih, 0.5, 1.5)


# def calculate_diabatic_correction_above(
#     molar_density_air: float | NDArray[np.float32],
#     specific_heat_air: float | NDArray[np.float32],
#     temperature: NDArray[np.float32],
#     sensible_heat_flux: NDArray[np.float32],
#     friction_velocity: NDArray[np.float32],
#     wind_heights: NDArray[np.float32],
#     zero_plane_displacement: NDArray[np.float32],
#     celsius_to_kelvin: float,
#     von_karmans_constant: float,
#     yasuda_stability_parameters: list[float],
#     diabatic_heat_momentum_ratio: float,
# ) -> dict[str, NDArray[np.float32]]:
#     r"""Calculate the diabatic correction factors for momentum and heat above canopy.

#     Diabatic correction factors for heat and momentum are used to adjust wind profiles
#    for surface heating and cooling :cite:p:`maclean_microclimc_2021`. When the surface
#     is strongly heated, the diabatic correction factor for momentum :math:`\Psi_{M}`
#     becomes negative and drops to values of around -1.5. In contrast, when the surface
#     is much cooler than the air above it, it increases to values around 4.

#     Args:
#         molar_density_air: Molar density of air above canopy, [mol m-3]
#         specific_heat_air: Specific heat of air above canopy, [J mol-1 K-1]
#         temperature: 2 m temperature above canopy, [C]
#        sensible_heat_flux: Sensible heat flux from canopy to atmosphere above, [W m-2]
#         friction_velocity: Friction velocity above canopy, [m s-1]
#         wind_heights: Height for which wind speed is calculated, [m]
#         zero_plane_displacement: Height above ground within the canopy where the wind
#             profile extrapolates to zero, [m]
#         celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
#             temperature in Kelvin
#         von_karmans_constant: Von Karman's constant, dimensionless constant describing
#             the logarithmic velocity profile of a turbulent fluid near a no-slip
#             boundary.
#         yasuda_stability_parameters: Parameters to approximate diabatic correction
#             factors for heat and momentum after :cite:t:`yasuda_turbulent_1988`
#         diabatic_heat_momentum_ratio: Factor that relates diabatic correction
#             factors for heat and momentum after :cite:t:`yasuda_turbulent_1988`

#     Returns:
#         Diabatic correction factors for heat :math:`\Psi_{H}` and momentum
#         :math:`\Psi_{M}` transfer
#     """

#     # Calculate atmospheric stability
#     stability = (
#         von_karmans_constant
#         * (wind_heights - zero_plane_displacement)
#         * sensible_heat_flux
#     ) / (
#         molar_density_air
#         * specific_heat_air
#         * (temperature + celsius_to_kelvin)
#         * friction_velocity
#     )

#     stable_condition = yasuda_stability_parameters[0] * np.log(1 - stability)
#     unstable_condition = -yasuda_stability_parameters[1] * np.log(
#         (1 + np.sqrt(1 - yasuda_stability_parameters[2] * stability)) / 2
#     )

#     # Calculate diabatic correction factors for stable and unstable conditions
#     diabatic_correction_heat = np.where(
#         sensible_heat_flux < 0, stable_condition, unstable_condition
#     )

#     diabatic_correction_momentum = np.where(
#         sensible_heat_flux < 0,
#         diabatic_correction_heat,
#         diabatic_heat_momentum_ratio * diabatic_correction_heat,
#     )

#     return {"psi_m": diabatic_correction_momentum, "psi_h": diabatic_correction_heat}


# def calculate_diabatic_correction_canopy(
#     air_temperature: NDArray[np.float32],
#     wind_speed: NDArray[np.float32],
#     layer_heights: NDArray[np.float32],
#     mean_mixing_length: NDArray[np.float32],
#     stable_temperature_gradient_intercept: float,
#     stable_wind_shear_slope: float,
#     yasuda_stability_parameters: list[float],
#     richardson_bounds: list[float],
#     gravity: float,
#     celsius_to_kelvin: float,
# ) -> dict[str, NDArray[np.float32]]:
#     r"""Calculate diabatic correction factors for momentum and heat in canopy.

#    This function calculates the diabatic correction factors for heat and momentum used
#    in adjustment of wind profiles and calculation of turbulent conductivity within the
#     canopy. Momentum and heat correction factors should be greater than or equal to 1
#     under stable conditions and smaller than 1 under unstable conditions. From
#     :cite:t:`goudriaan_crop_1977` it is assumed that :math:`\Phi_{H}` remains
#     relatively constant within the canopy. Thus, the function returns a mean value for
#    the whole canopy and below. Implementation after :cite:t:`maclean_microclimc_2021`.

#     Args:
#         air_temperature: Air temperature, [C]
#         wind_speed: Wind speed, [m s-1]
#         layer_heights: Layer heights, [m]
#         mean_mixing_length: Mean mixing length, [m]
#         stable_temperature_gradient_intercept: Temperature gradient intercept under
#             stable athmospheric conditions after :cite:t:`goudriaan_crop_1977`.
#         stable_wind_shear_slope: Wind shear slope under stable atmospheric conditions
#             after :cite:t:`goudriaan_crop_1977`.
#         richardson_bounds: Minimum and maximum value for Richardson number
#         yasuda_stability_parameters: Parameters to approximate diabatic correction
#             factors for heat and momentum after :cite:t:`yasuda_turbulent_1988`
#         gravity: Newtonian constant of gravitation, [m s-1]
#         celsius_to_kelvin: Factor to convert between Celsius and Kelvin

#     Returns:
#         diabatic correction factor for momentum :math:`\Phi_{M}` and heat
#         :math:`\Phi_{H}` transfer
#     """

#     # Calculate differences between consecutive elements along the vertical axis
#     temperature_differences = np.diff(air_temperature, axis=0)
#     height_differences = np.diff(layer_heights, axis=0)
#     temperature_gradient = temperature_differences / height_differences

#     # Calculate mean temperature in Kelvin
#     mean_temperature_kelvin = np.mean(air_temperature, axis=0) + celsius_to_kelvin
#     mean_wind_speed = np.mean(wind_speed, axis=0)

#     # Calculate Richardson number
#     richardson_number = (
#         (gravity / mean_temperature_kelvin)
#         * temperature_gradient
#         * (mean_mixing_length / mean_wind_speed) ** 2
#     )
#     richardson_number[richardson_number > richardson_bounds[0]] = richardson_bounds[0]
#    richardson_number[richardson_number <= richardson_bounds[1]] = richardson_bounds[1]

#     # Calculate stability term
#     stability_factor = (
#         4
#         * stable_wind_shear_slope
#         * (1 - stable_temperature_gradient_intercept)
#         / (stable_temperature_gradient_intercept) ** 2
#     )
#     stability_term = (
#         stable_temperature_gradient_intercept
#         * (1 + stability_factor * richardson_number) ** 0.5
#         + 2 * stable_wind_shear_slope * richardson_number
#         - stable_temperature_gradient_intercept
#     ) / (
#        2 * stable_wind_shear_slope * (1 - stable_wind_shear_slope * richardson_number)
#     )
#     sel = np.where(temperature_gradient <= 0)  # Unstable conditions
#     stability_term[sel] = richardson_number[sel]

#     # Initialize phi_m and phi_h with values for stable conditions
#   phi_m = 1 + (yasuda_stability_parameters[0] * stability_term) / (1 + stability_term)
#     phi_h = phi_m.copy()

#     # Adjust for unstable conditions
#    phi_m[sel] = 1 / (1 - yasuda_stability_parameters[2] * stability_term[sel]) ** 0.25
#     phi_h[sel] = phi_m[sel] ** 2

#     # Calculate mean values across the vertical axis for phi_m and phi_h
#     phi_m_mean = np.mean(phi_m, axis=0)
#     phi_h_mean = np.mean(phi_h, axis=0)

#     return {"phi_m": phi_m_mean, "phi_h": phi_h_mean}


# def calculate_mean_mixing_length(
#     canopy_height: NDArray[np.float32],
#     zero_plane_displacement: NDArray[np.float32],
#     roughness_length_momentum: NDArray[np.float32],
#     mixing_length_factor: float,
# ) -> NDArray[np.float32]:
#     """Calculate mixing length for canopy air transport, [m].

#   The mean mixing length is used to calculate turbulent air transport inside vegetated
#   canopies. It is made equivalent to the above canopy value at the canopy surface. In
#     absence of vegetation, it is set to zero. Implementation after
#     :cite:t:`maclean_microclimc_2021`.

#     Args:
#         canopy_height: Canopy height, [m]
#         zero_plane_displacement: Height above ground within the canopy where the wind
#             profile extrapolates to zero, [m]
#         roughness_length_momentum: Momentum roughness length, [m]
#       mixing_length_factor: Factor in calculation of mean mixing length, dimensionless

#     Returns:
#         Mixing length for canopy air transport, [m]
#     """

#     mean_mixing_length = (
#         mixing_length_factor * (canopy_height - zero_plane_displacement)
#     ) / np.log((canopy_height - zero_plane_displacement) / roughness_length_momentum)

#     return np.nan_to_num(mean_mixing_length, nan=0)


# def generate_relative_turbulence_intensity(
#     layer_heights: NDArray[np.float32],
#     min_relative_turbulence_intensity: float,
#     max_relative_turbulence_intensity: float,
#     increasing_with_height: bool,
# ) -> NDArray[np.float32]:
#     """Generate relative turbulence intensity profile, dimensionless.

#     At the moment, default values are for a maize crop Shaw et al (1974)
#     Agricultural Meteorology, 13: 419-425. TODO adjust default to environment

#     Args:
#         layer_heights: Heights of above ground layers, [m]
#         min_relative_turbulence_intensity: Minimum relative turbulence intensity,
#             dimensionless
#         max_relative_turbulence_intensity: Maximum relative turbulence intensity,
#             dimensionless
#         increasing_with_height: Increasing logical indicating whether turbulence
#             intensity increases (TRUE) or decreases (FALSE) with height

#     Returns:
#         Relative turbulence intensity for each node, dimensionless
#     """

#     direction = 1 if increasing_with_height else -1

#     return (
#         min_relative_turbulence_intensity
#         + direction
#         * (max_relative_turbulence_intensity - min_relative_turbulence_intensity)
#         * layer_heights
#     )


# def calculate_wind_attenuation_coefficient(
#     canopy_height: NDArray[np.float32],
#     leaf_area_index: NDArray[np.float32],
#     mean_mixing_length: NDArray[np.float32],
#     drag_coefficient: float,
#     relative_turbulence_intensity: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate wind attenuation coefficient, dimensionless.

#     The wind attenuation coefficient describes how wind is slowed down by the presence
#     of vegetation. In absence of vegetation, the coefficient is set to zero.
#     Implementation after :cite:t:`maclean_microclimc_2021`.

#     Args:
#         canopy_height: Canopy height, [m]
#         leaf_area_index: Leaf area index, [m m-1]
#         mean_mixing_length: Mixing length for canopy air transport, [m]
#         drag_coefficient: Drag coefficient, dimensionless
#         relative_turbulence_intensity: Relative turbulence intensity, dimensionless

#     Returns:
#         Wind attenuation coefficient, dimensionless
#     """

#     # VIVI - this is operating on inputs containing all true aboveground rows. Because
#     # LAI is only defined for the canopy layers, the result of this operation is
#     # undefined for the top and bottom row and so can just be filled in rather than
#     # having to concatenate. We _could_ subset the inputs and then concatenate - those
#     # are more intuitive inputs - but handling those extra layers maintains the same
#     # calculation shape throughout the wind calculation stack.
#     attenuation_coefficient = (drag_coefficient * leaf_area_index * canopy_height) / (
#         2 * mean_mixing_length * relative_turbulence_intensity
#     )

#     # Above the canopy is set to zero and the surface layer is set to the last valid
#     # canopy value
#     attenuation_coefficient[0] = 0
#     attenuation_coefficient[-1] = find_last_valid_row(attenuation_coefficient)

#     return attenuation_coefficient


# def wind_log_profile(
#     height: float | NDArray[np.float32],
#     zeroplane_displacement: float | NDArray[np.float32],
#     roughness_length_momentum: float | NDArray[np.float32],
#     diabatic_correction_momentum: float | NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate logarithmic wind profile.

#    Note that this function can return NaN, this is not corrected here because it might
#     cause division by zero later on in the work flow.

#     Args:
#         height: Array of heights for which wind speed is calculated, [m]
#         zeroplane_displacement: Height above ground within the canopy where the wind
#             profile extrapolates to zero, [m]
#         roughness_length_momentum: Momentum roughness length, [m]
#         diabatic_correction_momentum: Diabatic correction factor for momentum

#     Returns:
#         logarithmic wind profile
#     """

#     wind_profile = (
#         np.log((height - zeroplane_displacement) / roughness_length_momentum)
#         + diabatic_correction_momentum,
#     )

#     return np.where(wind_profile == 0.0, np.nan, wind_profile).squeeze()


# def calculate_friction_velocity(
#     wind_speed_ref: NDArray[np.float32],
#     canopy_height: NDArray[np.float32],
#     zeroplane_displacement: NDArray[np.float32],
#     roughness_length_momentum: NDArray[np.float32],
#     diabatic_correction_momentum: float | NDArray[np.float32],
#     von_karmans_constant: float,
#     min_friction_velocity: float,
# ) -> NDArray[np.float32]:
#     """Calculate friction velocity from wind speed at reference height, [m s-1].

#     Args:
#         wind_speed_ref: Wind speed at reference height, [m s-1]
#         canopy_height: Canopy height, [m]
#         zeroplane_displacement: Height above ground within the canopy where the wind
#             profile extrapolates to zero, [m]
#         roughness_length_momentum: Momentum roughness length, [m]
#         diabatic_correction_momentum: Diabatic correction factor for momentum
#         von_karmans_constant: Von Karman's constant, dimensionless constant describing
#             the logarithmic velocity profile of a turbulent fluid near a no-slip
#             boundary.
#         min_friction_velocity: Minimum friction velocity, [m s-1]

#     Returns:
#         Friction velocity, [m s-1]
#     """
#     friction_velocity = (von_karmans_constant * wind_speed_ref) / (
#         np.log((canopy_height - zeroplane_displacement) / roughness_length_momentum)
#         + diabatic_correction_momentum
#     )
#     return np.where(
#         friction_velocity < min_friction_velocity,
#         min_friction_velocity,
#         friction_velocity,
#     )


# def calculate_wind_above_canopy(
#     friction_velocity: NDArray[np.float32],
#     wind_height_above: NDArray[np.float32],
#     zeroplane_displacement: NDArray[np.float32],
#     roughness_length_momentum: NDArray[np.float32],
#     diabatic_correction_momentum: NDArray[np.float32],
#     von_karmans_constant: float,
#     min_wind_speed_above_canopy: float,
# ) -> NDArray[np.float32]:
#     """Calculate wind speed above canopy from wind speed at reference height, [m s-1].

#     Wind speed above the canopy dictates heat and vapour exchange between the canopy
#     and the air above it, and therefore ultimately determines temperature and vapour
#     profiles.
#    The wind profile above canopy typically follows a logarithmic height profile, which
#     extrapolates to zero roughly two thirds of the way to the top of the canopy. The
#     profile itself is thus dependent on the height of the canopy, but also on the
#     roughness of the vegetation layer, which causes wind shear. We follow the
#     implementation by :cite:t:`campbell_introduction_1998` as described in
#     :cite:t:`maclean_microclimc_2021`.

#     Args:
#         friction_velocity: friction velocity, [m s-1]
#         wind_height_above: Heights above canopy for which wind speed is required, [m].
#             For use in the calculation of the full wind profiles, this typically
#             includes two values: the height of the first layer ('above') and the first
#             canopy layer which corresponds to the canopy height.
#         zeroplane_displacement: Height above ground within the canopy where the wind
#             profile extrapolates to zero, [m]
#         roughness_length_momentum: Momentum roughness length, [m]
#         diabatic_correction_momentum: Diabatic correction factor for momentum as
#             returned by
#     :func:`~virtual_ecosystem.models.abiotic.wind.calculate_diabatic_correction_above`
#         von_karmans_constant: Von Karman's constant, dimensionless constant describing
#             the logarithmic velocity profile of a turbulent fluid near a no-slip
#             boundary.
#         min_wind_speed_above_canopy: Minimum wind speed above canopy, [m s-1]

#     Returns:
#         wind speed at required heights above canopy, [m s-1]
#     """

#     wind_profile_above = wind_log_profile(
#         height=wind_height_above,
#         zeroplane_displacement=zeroplane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         diabatic_correction_momentum=diabatic_correction_momentum,
#     )
#     wind_profile = (friction_velocity / von_karmans_constant) * wind_profile_above

#     return np.where(
#         wind_profile < min_wind_speed_above_canopy,
#         min_wind_speed_above_canopy,
#         wind_profile,
#     )


# def calculate_wind_canopy(
#     top_of_canopy_wind_speed: NDArray[np.float32],
#     wind_layer_heights: NDArray[np.float32],
#     canopy_height: NDArray[np.float32],
#     attenuation_coefficient: NDArray[np.float32],
# ) -> NDArray[np.float32]:
#     """Calculate wind speed in a multi-layer canopy, [m s-1].

#     This function can be extended to account for edge distance effects.

#     Args:
#         top_of_canopy_wind_speed: Wind speed at top of canopy layer, [m s-1]
#         wind_layer_heights: Heights of canopy layers, [m]
#         canopy_height: Height to top of canopy layer, [m]
#         attenuation_coefficient: Mean attenuation coefficient based on the profile
#             calculated by
#  :func:`~virtual_ecosystem.models.abiotic.wind.calculate_wind_attenuation_coefficient`
#      min_windspeed_below_canopy: Minimum wind speed below the canopy or in absence of
#             vegetation, [m/s]. This value is set to avoid dividion by zero.

#     Returns:
#         wind speed at height of canopy layers, [m s-1]
#     """

#     zero_displacement = top_of_canopy_wind_speed * np.exp(
#         attenuation_coefficient * ((wind_layer_heights / canopy_height) - 1)
#     )
#     return zero_displacement


# def calculate_wind_profile(
#     canopy_height: NDArray[np.float32],
#     wind_height_above: NDArray[np.float32],
#     wind_layer_heights: NDArray[np.float32],
#     leaf_area_index: NDArray[np.float32],
#     air_temperature: NDArray[np.float32],
#     atmospheric_pressure: NDArray[np.float32],
#     sensible_heat_flux_topofcanopy: NDArray[np.float32],
#     wind_speed_ref: NDArray[np.float32],
#     wind_reference_height: float | NDArray[np.float32],
#     abiotic_constants: AbioticConsts,
#     core_constants: CoreConsts,
# ) -> dict[str, NDArray[np.float32]]:
#     r"""Calculate wind speed above and below the canopy, [m s-1].

#     The wind profile above the canopy is described as follows (based on
#     :cite:p:`campbell_introduction_1998` as implemented in
#     :cite:t:`maclean_microclimc_2021`):

#     :math:`u_z = \frac{u^{*}}{0.4} ln \frac{z-d}{z_M} + \Psi_M`

#     where :math:`u_z` is wind speed at height :math:`z` above the canopy, :math:`d` is
#     the height above ground within the canopy where the wind profile extrapolates to
#     zero, :math:`z_m` the roughness length for momentum, :math:`\Psi_M` is a diabatic
#     correction for momentum and :math:`u^{*}` is the friction velocity, which gives
# the
#     wind speed at height :math:`d + z_m`.

#     The wind profile below canopy is derived as follows:

#     :math:`u_z = u_h exp(a(\frac{z}{h} - 1))`

#     where :math:`u_z` is wind speed at height :math:`z` within the canopy, :math:`u_h`
#     is wind speed at the top of the canopy at height :math:`h`, and :math:`a` is a
# wind
#     attenuation coefficient given by :math:`a = 2 l_m i_w`, where :math:`c_d` is a
# drag
#     coefficient that varies with leaf inclination and shape, :math:`i_w` is a
#     coefficient describing relative turbulence intensity and :math:`l_m` is the mean
#     mixing length, equivalent to the free space between the leaves and stems. For
#     details, see :cite:t:`maclean_microclimc_2021`.

#     The following variables are returned:

#     * wind_speed
#     * friction_velocity
#     * molar_density_air
#     * specific_heat_air
#     * zero_plane_displacement
#     * roughness_length_momentum
#     * mean_mixing_length
#     * relative_turbulence_intensity
#     * attenuation_coefficient

#     Args:
#         canopy_height: Canopy height, [m]
#         wind_height_above: Heights above canopy for which wind speed is required, [m].
#             For use in the calculation of the full wind profiles, this typically
#             includes two values: the height of the first layer ('above') and the first
#             canopy layer which corresponds to the canopy height.
#         wind_layer_heights: Layer heights above ground, [m]
#         leaf_area_index: Leaf area index, [m m-1]
#         air_temperature: Air temperature, [C]
#         atmospheric_pressure: Atmospheric pressure, [kPa]
#         sensible_heat_flux_topofcanopy: Sensible heat flux from the top of the canopy
# to
#             the atmosphere, [W m-2],
#         wind_speed_ref: Wind speed at reference height, [m s-1]
#         wind_reference_height: Reference height for wind measurement, [m]
#         diabatic_correction_parameters: Set of parameters for diabatic correction
#             calculations in canopy
#         abiotic_constants: Specific constants for the abiotic model
#         core_constants: Universal constants shared across all models

#     Returns:
#         Dictionary that contains wind related outputs
#     """

#     output = {}

#     # Calculate molar density of air, [mol m-3]
#     molar_density_air = calculate_molar_density_air(
#         temperature=air_temperature,
#         atmospheric_pressure=atmospheric_pressure,
#         standard_mole=core_constants.standard_mole,
#         standard_pressure=core_constants.standard_pressure,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#     )
#     output["molar_density_air"] = molar_density_air

#     # Calculate specific heat of air, [J mol-1 K-1]
#     specific_heat_air = calculate_specific_heat_air(
#         temperature=air_temperature,
#         molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
#         specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
#     )
#     output["specific_heat_air"] = specific_heat_air

#     # Calculate the total leaf area index, [m2 m-2]
#     leaf_area_index_sum = np.nansum(leaf_area_index, axis=0)

#     zero_plane_displacement = calculate_zero_plane_displacement(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index_sum,
#         zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
#     )
#     output["zero_plane_displacement"] = zero_plane_displacement

#     # Calculate zero plane displacement height, [m]
#     roughness_length_momentum = calculate_roughness_length_momentum(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index_sum,
#         zero_plane_displacement=zero_plane_displacement,
#         substrate_surface_drag_coefficient=(
#             abiotic_constants.substrate_surface_drag_coefficient
#         ),
#         roughness_element_drag_coefficient=(
#             abiotic_constants.roughness_element_drag_coefficient
#         ),
#         roughness_sublayer_depth_parameter=(
#             abiotic_constants.roughness_sublayer_depth_parameter
#         ),
#         max_ratio_wind_to_friction_velocity=(
#             abiotic_constants.max_ratio_wind_to_friction_velocity
#         ),
#         min_roughness_length=abiotic_constants.min_roughness_length,
#         von_karman_constant=core_constants.von_karmans_constant,
#     )
#     output["roughness_length_momentum"] = roughness_length_momentum

#     friction_velocity_uncorrected = calculate_friction_velocity_reference_height(
#         wind_speed_ref=wind_speed_ref,
#         reference_height=wind_reference_height,
#         zeroplane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         diabatic_correction_momentum=0.0,
#         von_karmans_constant=core_constants.von_karmans_constant,
#         min_friction_velocity=abiotic_constants.min_friction_velocity,
#     )

#     # Calculate diabatic correction factor above canopy (Psi)
#     diabatic_correction_above = calculate_diabatic_correction_above(
#         molar_density_air=molar_density_air[0],
#         specific_heat_air=specific_heat_air[0],
#         temperature=air_temperature[0],
#         sensible_heat_flux=sensible_heat_flux_topofcanopy,
#         friction_velocity=friction_velocity_uncorrected,
#         wind_heights=wind_layer_heights[0],
#         zero_plane_displacement=zero_plane_displacement,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#         von_karmans_constant=core_constants.von_karmans_constant,
#         yasuda_stability_parameters=abiotic_constants.yasuda_stability_parameters,
#         diabatic_heat_momentum_ratio=abiotic_constants.diabatic_heat_momentum_ratio,
#     )
#     output["diabatic_correction_heat_above"] = diabatic_correction_above["psi_h"]
#     output["diabatic_correction_momentum_above"] = diabatic_correction_above["psi_m"]

#     # Update friction velocity with diabatic correction factor
#     friction_velocity = calculate_friction_velocity_reference_height(
#         wind_speed_ref=wind_speed_ref,
#         reference_height=wind_reference_height,
#         zeroplane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         diabatic_correction_momentum=diabatic_correction_above["psi_m"],
#         von_karmans_constant=core_constants.von_karmans_constant,
#         min_friction_velocity=abiotic_constants.min_friction_velocity,
#     )
#     output["friction_velocity"] = friction_velocity

#     # Calculate mean mixing length, [m]
#     mean_mixing_length = calculate_mean_mixing_length(
#         canopy_height=canopy_height,
#         zero_plane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         mixing_length_factor=abiotic_constants.mixing_length_factor,
#     )
#     output["mean_mixing_length"] = mean_mixing_length

#     # Calculate profile of turbulent mixing intensities, dimensionless
#     relative_turbulence_intensity = generate_relative_turbulence_intensity(
#         layer_heights=wind_layer_heights,
#         min_relative_turbulence_intensity=(
#             abiotic_constants.min_relative_turbulence_intensity
#         ),
#         max_relative_turbulence_intensity=(
#             abiotic_constants.max_relative_turbulence_intensity
#         ),
#         increasing_with_height=abiotic_constants.turbulence_sign,
#     )
#     output["relative_turbulence_intensity"] = relative_turbulence_intensity

#     # Calculate profile of attenuation coefficients, dimensionless
#     # VIVI - This might be wildly wrong, but at the moment this is taking in the full
#     # set of true aboveground rows and then appending a row above and below. I think
# it
#     # should operate by taking only the canopy data (dropping two rows) and then
#     # replacing them.
#     attennuation_coefficient = calculate_wind_attenuation_coefficient(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index,
#         mean_mixing_length=mean_mixing_length,
#         drag_coefficient=abiotic_constants.drag_coefficient,
#         relative_turbulence_intensity=relative_turbulence_intensity,
#     )
#     output["attennuation_coefficient"] = attennuation_coefficient

#     # Calculate wind speed above canopy (2m above and top of canopy), [m s-1]
#     wind_speed_above_canopy = calculate_wind_above_canopy(
#         friction_velocity=friction_velocity,
#         wind_height_above=wind_height_above,
#         zeroplane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         diabatic_correction_momentum=diabatic_correction_above["psi_m"],
#         von_karmans_constant=core_constants.von_karmans_constant,
#         min_wind_speed_above_canopy=abiotic_constants.min_wind_speed_above_canopy,
#     )

#     # Calculate wind speed in and below canopy, [m s-1]
#     wind_speed_canopy = calculate_wind_canopy(
#         top_of_canopy_wind_speed=wind_speed_above_canopy[1],
#         wind_layer_heights=wind_layer_heights,
#         canopy_height=canopy_height,
#         attenuation_coefficient=attennuation_coefficient,
#     )

#     # Combine wind speed above and in canopy to full profile
#     wind_speed_canopy[0:2] = wind_speed_above_canopy
#     output["wind_speed"] = wind_speed_canopy

#     # Calculate diabatic correction factors for heat and momentum below canopy
#     # (required for the calculation of conductivities)
#     diabatic_correction_canopy = calculate_diabatic_correction_canopy(
#         air_temperature=air_temperature,
#         wind_speed=wind_speed_canopy,
#         layer_heights=wind_layer_heights,
#         mean_mixing_length=mean_mixing_length,
#         stable_temperature_gradient_intercept=(
#             abiotic_constants.stable_temperature_gradient_intercept
#         ),
#         stable_wind_shear_slope=abiotic_constants.stable_wind_shear_slope,
#         yasuda_stability_parameters=abiotic_constants.yasuda_stability_parameters,
#         richardson_bounds=abiotic_constants.richardson_bounds,
#         gravity=core_constants.gravity,
#         celsius_to_kelvin=core_constants.zero_Celsius,
#     )
#     output["diabatic_correction_heat_canopy"] = diabatic_correction_canopy["phi_h"]
#     output["diabatic_correction_momentum_canopy"] = diabatic_correction_canopy
# ["phi_m"]

#     return output
