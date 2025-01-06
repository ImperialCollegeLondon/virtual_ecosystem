"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

import numpy as np
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
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConsts,
    core_constants: CoreConsts,
) -> dict[str, DataArray]:
    """Run microclimate model.

    Args:
        data: Data object
        time_index: Time index
        time_interval: Time interval, [s]
        layer_structure: Layer structure object
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models

    Returns:
        dictionary with updated microclimate variables
    """

    output = {}

    # Selection of often used subsets
    # NOTE Canopy height will likely become a separate variable, update as required
    canopy_height = data["layer_heights"][1].to_numpy()
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers").to_numpy()

    # Mean atmospheric pressure profile, [kPa]
    # TODO: #484 this should only be filled for filled/true above ground layers
    output["atmospheric_pressure"] = layer_structure.from_template()
    output["atmospheric_pressure"][layer_structure.index_atmosphere] = data[
        "atmospheric_pressure_ref"
    ].isel(time_index=time_index)

    # Mean atmospheric C02 profile, [ppm]
    # TODO: #484 this should only be filled for filled/true above ground layers
    output["atmospheric_co2"] = layer_structure.from_template()
    output["atmospheric_co2"][layer_structure.index_atmosphere] = data[
        "atmospheric_co2_ref"
    ].isel(time_index=time_index)

    #  Calculate atmospheric background variables
    molar_density_air = abiotic_tools.calculate_molar_density_air(
        temperature=np.nanmean(data["air_temperature"].to_numpy(), axis=0),
        atmospheric_pressure=(
            data["atmospheric_pressure_ref"].isel(time_index=time_index).to_numpy()
        ),
        standard_mole=core_constants.standard_mole,
        standard_pressure=core_constants.standard_pressure,
        celsius_to_kelvin=core_constants.zero_Celsius,
    )
    output["molar_density_air"] = DataArray(molar_density_air, dims="cell_id")

    specific_heat_air = abiotic_tools.calculate_specific_heat_air(
        temperature=np.nanmean(data["air_temperature"].to_numpy(), axis=0),
        molar_heat_capacity_air=core_constants.molar_heat_capacity_air,
        specific_heat_equ_factors=abiotic_constants.specific_heat_equ_factors,
    )
    output["specific_heat_air"] = DataArray(specific_heat_air, dims="cell_id")

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
    wind_reference_height = (
        data["layer_heights"][1].to_numpy() + abiotic_constants.wind_reference_height
    )
    wind_heights = data["layer_heights"][
        layer_structure.index_filled_atmosphere
    ].to_numpy()

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
    wind_speed = layer_structure.from_template()
    wind_speed[layer_structure.index_filled_atmosphere] = wind_profile
    output["wind_speed"] = wind_speed

    #   Friction velocity, [m s-1]
    # friction_velocity = wind.calculate_friction_velocity(
    #     reference_wind_speed=data["wind_speed_ref"]
    #     .isel(time_index=time_index)
    #     .to_numpy(),
    #     reference_height=wind_reference_height,
    #     roughness_length=roughness_length,
    #     zero_plane_displacement=zero_plane_displacement,
    #     von_karman_constant=core_constants.von_karmans_constant,
    # )

    #   TODO Aerodynamic resistance canopy, [s m-1]
    #  The current implementation of logarithmic wind profile breaks down when the
    #  canopy layer height falls below the zero displacement height. A more sophistcated
    #  implementation is needed, e.g. Monin-Obukov theory, or a constant value across
    #  the canopy. For now empirical value for homogenous canopy.
    #
    # aerodynamic_resistance_canopy = energy_balance.calculate_aerodynamic_resistance(
    #     wind_heights=data["layer_heights"][
    #         layer_structure.index_filled_canopy
    #     ].to_numpy(),
    #     roughness_length=roughness_length,
    #     zero_plane_displacement=zero_plane_displacement,
    #     friction_velocity=friction_velocity,
    #     von_karman_constant=core_constants.von_karmans_constant,
    # )
    aerodynamic_resistance_canopy = 100.0

    #   TODO  Aerodynamic resistance soil, [s m-1]
    # Currently not implemented, see canopy resistance above.
    aerodynamic_resistance_soil = 100.0

    # Longwave emission from canopy, [W m-2]
    longwave_emission_canopy = energy_balance.calculate_longwave_emission(
        temperature=data["canopy_temperature"].to_numpy() + core_constants.zero_Celsius,
        emissivity=abiotic_constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Longwave emission from soil, [W m-2]
    longwave_emission_soil = energy_balance.calculate_longwave_emission(
        temperature=data["soil_temperature"].to_numpy() + core_constants.zero_Celsius,
        emissivity=abiotic_constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Combine longwave emission in one variable
    # Assumption: accumulated emission in time interval based on accumulated input
    longwave_emission = layer_structure.from_template()
    longwave_emission[layer_structure.index_filled_canopy] = longwave_emission_canopy[
        layer_structure.index_filled_canopy
    ]
    longwave_emission[layer_structure.index_topsoil_scalar] = longwave_emission_soil[
        layer_structure.index_topsoil_scalar
    ]
    output["longwave_emission"] = longwave_emission

    # Net radiation canopy, [W m-2]
    net_radiation_canopy = energy_balance.calculate_net_radiation(
        incoming_radiation=data["topofcanopy_radiation"]
        .isel(time_index=time_index)
        .to_numpy(),
        absorbed_radiation=data["absorbed_radiation"].to_numpy(),
        longwave_emission=longwave_emission_canopy,
        albedo=abiotic_constants.leaf_albedo,
    )

    # Net radiation topsoil, [W m-2]
    absorbed_radiation_sum = np.nansum(data["absorbed_radiation"].to_numpy(), axis=0)
    net_radiation_soil = energy_balance.calculate_net_radiation(
        incoming_radiation=data["topofcanopy_radiation"]
        .isel(time_index=time_index)
        .to_numpy(),
        absorbed_radiation=absorbed_radiation_sum,
        longwave_emission=longwave_emission_soil[layer_structure.index_topsoil_scalar],
        albedo=abiotic_constants.surface_albedo,
    )

    # Combine net radiation in one variable
    # Assumption: accumulated emission in time interval based on accumulated input
    net_radiation = layer_structure.from_template()
    net_radiation[layer_structure.index_filled_canopy] = net_radiation_canopy[
        layer_structure.index_filled_canopy
    ]
    net_radiation[layer_structure.index_topsoil_scalar] = net_radiation_soil

    #  Sensible heat flux from canopy layers, [W m-2]
    sensible_heat_flux_canopy = energy_balance.calculate_sensible_heat_flux(
        density_air=molar_density_air / core_constants.standard_mole,
        specific_heat_air=specific_heat_air / core_constants.standard_mole,
        air_temperature=data["air_temperature"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        surface_temperature=data["canopy_temperature"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_canopy,
    )

    #  Sensible heat flux from topsoil, [W m-2]
    sensible_heat_flux_soil = energy_balance.calculate_sensible_heat_flux(
        density_air=molar_density_air / core_constants.standard_mole,
        specific_heat_air=specific_heat_air / core_constants.standard_mole,
        air_temperature=data["air_temperature"][
            layer_structure.index_topsoil_scalar - 1
        ].to_numpy(),
        surface_temperature=data["soil_temperature"][
            layer_structure.index_topsoil_scalar
        ].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_soil,
    )

    # Combine sensible heat flux in one variable
    sensible_heat_flux = layer_structure.from_template()
    sensible_heat_flux[layer_structure.index_filled_canopy] = sensible_heat_flux_canopy
    sensible_heat_flux[layer_structure.index_topsoil_scalar] = sensible_heat_flux_soil
    output["sensible_heat_flux"] = sensible_heat_flux * time_interval

    #   Latent heat of vapourisation, [kJ kg-1]
    latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
        temperature=np.nanmean(data["air_temperature"].to_numpy(), axis=0),
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
    )

    # Latent heat flux, [W m-2]
    #  The current implementation converts outputs from plant and hydrology model; the
    #  explicit equations don't quite work yet as we do not have leaf vapour pressure.

    #  Effective vapour pressure, [kPa]
    # effective_vapour_pressure_air = calculate_effective_vapour_pressure(
    #     air_temperature=data["air_temperature"],
    #     relative_humidity=data["relative_humidity"],
    #     saturation_vapour_pressure_factors=(
    #         abiotic_simple_constants.saturation_vapour_pressure_factors
    #     ),
    # )

    # effective_vapour_pressure_leaf = calculate_effective_vapour_pressure(
    #     air_temperature=data["canopy_temperature"],
    #     relative_humidity=data["relative_humidity"], # TODO rel humidity in canopy
    #     saturation_vapour_pressure_factors=(
    #         abiotic_simple_constants.saturation_vapour_pressure_factors
    #     ),
    # )

    # latent_heat_flux_canopy = calculate_latent_heat_flux(
    #     latent_heat_vapourisation=latent_heat_vapourisation,
    #     leaf_vapour_conductivity=leaf_vapour_conductivity,
    #     effective_vapour_pressure_leaf=effective_vapour_pressure_leaf,
    #     effective_vapour_pressure_air=effective_vapour_pressure_air,
    #     atmospheric_pressure=data["atmospheric_pressure"].to_numpy()
    # )

    # Latent heat flux canopy, [W m-2]
    # TODO cross-check with plant model, time step currently month to second
    latent_heat_flux_canopy = (
        data["evapotranspiration"][layer_structure.index_filled_canopy].to_numpy()
        / 2.628e6
    ) * latent_heat_vapourisation

    # Latent heat flux topsoil, [W m-2]
    # TODO cross-check with hydrology model, time step currently month to second
    latent_heat_flux_soil = (
        data["soil_evaporation"].to_numpy() / 2.628e6 * latent_heat_vapourisation
    )

    # Combine latent heat flux in one variable
    # TODO adjust to model timestep, currently per second
    latent_heat_flux = layer_structure.from_template()
    latent_heat_flux[layer_structure.index_filled_canopy] = latent_heat_flux_canopy
    latent_heat_flux[layer_structure.index_topsoil_scalar] = latent_heat_flux_soil
    output["latent_heat_flux"] = latent_heat_flux * time_interval

    # Ground heat flux

    # Update air/canopy/soil temperatures

    # Update humidity/VPD

    return output
