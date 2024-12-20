"""The microclimate module contains the equations to solve the radiation and energy
balance in the Virtual Ecosystem.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic import abiotic_tools
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
    calculate_saturation_vapour_pressure,
)


def initialise_absorbed_radiation(
    topofcanopy_radiation: NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    layer_heights: NDArray[np.float32],
    light_extinction_coefficient: float,
) -> NDArray[np.float32]:
    r"""Calculate initial light absorption profile.

    This function calculates the fraction of radiation absorbed by a multi-layered
    canopy based on its leaf area index (:math:`LAI`) and extinction coefficient
    (:math:`k`) at each layer, the depth of each measurement (:math:`z`), and the
    incoming light intensity at the top of the canopy (:math:`I_{0}`). The
    implementation based on Beer's law:

    .. math:: I(z) = I_{0} * e^{(-k * LAI * z)}

    Args:
        topofcanopy_radiation: Top of canopy radiation shortwave radiation, [W m-2]
        leaf_area_index: Leaf area index of each canopy layer, [m m-1]
        layer_heights: Layer heights, [m]
        light_extinction_coefficient: Light extinction coefficient, [m-1]

    Returns:
        Shortwave radiation absorbed by canopy layers, [W m-2]
    """
    # Calculate the depth of each layer, [m]
    layer_depths = np.abs(np.diff(layer_heights, axis=0, append=0))

    # Calculate the light extinction for each layer
    layer_extinction = np.exp(
        -0.01 * light_extinction_coefficient * layer_depths * leaf_area_index
    )

    # Calculate how much light penetrates through the canopy, [W m-2]
    cumulative_extinction = np.cumprod(layer_extinction, axis=0)
    penetrating_radiation = cumulative_extinction * topofcanopy_radiation

    # Calculate how much light is absorbed in each layer, [W m-2]
    absorbed_radiation = np.abs(
        np.diff(
            penetrating_radiation,
            prepend=np.expand_dims(topofcanopy_radiation, axis=0),
            axis=0,
        )
    )

    return absorbed_radiation


def initialise_canopy_temperature(
    air_temperature: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    canopy_temperature_ini_factor: float,
) -> NDArray[np.float32]:
    """Initialise canopy temperature.

    Args:
        air_temperature: Air temperature, [C]
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation
        absorbed_radiation: Shortwave radiation absorbed by canopy, [W m-2]

    Returns:
        Initial canopy temperature, [C]
    """
    return air_temperature + canopy_temperature_ini_factor * absorbed_radiation


def initialise_canopy_and_soil_fluxes(
    air_temperature: DataArray,
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    layer_heights: DataArray,
    layer_structure: LayerStructure,
    light_extinction_coefficient: float,
    canopy_temperature_ini_factor: float,
) -> dict[str, DataArray]:
    """Initialise canopy temperature and energy fluxes.

    This function initializes the following variables to run the first step of the
    energy balance routine: absorbed radiation (canopy), canopy temperature, sensible
    and latent heat flux (canopy and soil), and ground heat flux.

    Args:
        air_temperature: Air temperature, [C]
        topofcanopy_radiation: Top of canopy radiation, [W m-2]
        leaf_area_index: Leaf area index, [m m-2]
        layer_heights: Layer heights, [m]
        layer_structure: Instance of LayerStructure
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation

    Returns:
        Dictionary with absorbed radiation (canopy), canopy temperature, sensible
            and latent heat flux (canopy and soil), and ground heat flux [W m-2].
    """

    output = {}

    # Get variables within filled canopy layers
    leaf_area_index_true = leaf_area_index[layer_structure.index_filled_canopy]
    layer_heights_canopy = layer_heights[layer_structure.index_filled_canopy]
    air_temperature_canopy = air_temperature[layer_structure.index_filled_canopy]

    # Initialize absorbed radiation DataArray
    absorbed_radiation = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_absorption",
    )

    # Calculate absorbed radiation
    initial_absorbed_radiation = initialise_absorbed_radiation(
        topofcanopy_radiation=topofcanopy_radiation.to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.to_numpy(),
        light_extinction_coefficient=light_extinction_coefficient,
    )

    # Replace np.nan with new values and write in output dict
    absorbed_radiation[layer_heights_canopy.indexes] = initial_absorbed_radiation
    output["canopy_absorption"] = absorbed_radiation

    # Initialize canopy temperature DataArray
    canopy_temperature = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_temperature",
    )

    # Calculate initial temperature and write in output dict
    initial_canopy_temperature = initialise_canopy_temperature(
        air_temperature=air_temperature_canopy.to_numpy(),
        absorbed_radiation=initial_absorbed_radiation,
        canopy_temperature_ini_factor=canopy_temperature_ini_factor,
    )
    canopy_temperature[layer_structure.index_filled_canopy] = initial_canopy_temperature
    output["canopy_temperature"] = canopy_temperature

    # Initialise sensible heat flux with zeros and write in output dict
    sensible_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="sensible_heat_flux",
    )
    sensible_heat_flux[layer_structure.index_filled_canopy] = 0.001
    sensible_heat_flux[layer_structure.index_topsoil] = 0.001
    output["sensible_heat_flux"] = sensible_heat_flux

    # Initialise latent heat flux with zeros and write in output dict
    output["latent_heat_flux"] = sensible_heat_flux.copy().rename("latent_heat_flux")

    # Initialise latent heat flux with zeros and write in output dict
    ground_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="ground_heat_flux",
    )
    ground_heat_flux[layer_structure.index_topsoil] = 0.001
    output["ground_heat_flux"] = ground_heat_flux

    return output


def calculate_slope_of_saturated_pressure_curve(
    temperature: NDArray[np.float32],
    saturated_pressure_slope_parameters: list[float],
) -> NDArray[np.float32]:
    r"""Calculate slope of the saturated pressure curve.

    Args:
        temperature: Temperature, [C]
        saturated_pressure_slope_parameters: List of parameters to calculate
            the slope of the saturated vapour pressure curve

    Returns:
        Slope of the saturated pressure curve, :math:`\Delta_{v}`
    """

    return (
        saturated_pressure_slope_parameters[0]
        * (
            saturated_pressure_slope_parameters[1]
            * np.exp(
                saturated_pressure_slope_parameters[2]
                * temperature
                / (temperature + saturated_pressure_slope_parameters[3])
            )
        )
        / (temperature + saturated_pressure_slope_parameters[3]) ** 2
    )


def calculate_longwave_emission(
    temperature: NDArray[np.float32],
    emissivity: float | NDArray[np.float32],
    stefan_boltzmann: float,
) -> NDArray[np.float32]:
    """Calculate longwave emission using the Stefan Boltzmann law, [W m-2].

    According to the Stefan Boltzmann law, the amount of radiation emitted per unit time
    from the area of a black body at absolute temperature is directly proportional to
    the fourth power of the temperature. Emissivity (which is equal to absorptive power)
    lies between 0 to 1.

    Args:
        temperature: Temperature, [K]
        emissivity: Emissivity, dimensionless
        stefan_boltzmann: Stefan Boltzmann constant, [W m-2 K-4]

    Returns:
        Longwave emission, [W m-2]
    """
    return emissivity * stefan_boltzmann * temperature**4


def calculate_net_radiation(
    incoming_radiation: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    longwave_emission: NDArray[np.float32],
    albedo: float,
) -> NDArray[np.float32]:
    """Calculate net radiation, [W m-2].

    This function calculates net radiation as the difference between incoming shortwave
    radiation, shortwave absorption, and longwave emission. The absorption of longwave
    radiation is currently not considered.

    Args:
        incoming_radiation: Incoming radiation, [W m-2]
        absorbed_radiation: Absorbed radiation, [W m-2]
        longwave_emission: Longwave emission, [W m-2]
        albedo: Albedo, [-]

    Returns:
        net radiation, [W m-2]
    """
    return incoming_radiation * (1 - albedo) - absorbed_radiation - longwave_emission


def calculate_sensible_heat_flux(
    density_air: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    air_temperature: NDArray[np.float32],
    surface_temperature: NDArray[np.float32],
    aerodynamic_resistance: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate sensible heat flux, [W m-2].

    The sensible heat flux :math:`H` is calculated using the following equation:

    .. math::
        H = \frac{\rho_a C_p}{r_a} (T_s - T_a)

    where ρₐ is the density of air, Cₚ is the specific heat capacity of air at constant
    pressure, rₐ is the aerodynamic resistance of the surface, Tₛ is the surface
    temperature, and Tₐ is the air temperature.

    Args:
        density_air: Density of air, [kg m-3]
        specific_heat_air: Specific heat of air, [J kg-1 K-1]
        air_temperature: Air temperature, [C]
        surface_temperature: Surface temperature (canopy or soil), [C]
        aerodynamic_resistance: Aerodynamic resistance, [s m-1]

    Returns:
        sensible heat flux, [W m-2]
    """
    return (
        density_air * specific_heat_air / aerodynamic_resistance
    ) * surface_temperature - air_temperature


def calculate_zero_plane_displacement(
    canopy_height: NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    zero_plane_scaling_parameter: float,
) -> NDArray[np.float32]:
    """Calculate zero plane displacement height, [m].

    The zero plane displacement height is a concept used in micrometeorology to describe
    the flow of air near the ground or over surfaces like a forest canopy or crops. It
    represents the height above the actual ground where the wind speed is theoretically
    reduced to zero due to the obstruction caused by the roughness elements (like trees
    or buildings). Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        leaf_area_index: Total leaf area index, [m m-1]
        zero_plane_scaling_parameter: Control parameter for scaling d/h, dimensionless
            :cite:p:`raupach_simplified_1994`

    Returns:
        Zero plane displacement height, [m]
    """

    # Select grid cells where vegetation is present
    displacement = np.where(leaf_area_index > 0, leaf_area_index, np.nan)

    # Calculate zero displacement height
    scale_displacement = np.sqrt(zero_plane_scaling_parameter * displacement)
    zero_plane_displacement = (
        (1 - (1 - np.exp(-scale_displacement)) / scale_displacement) * canopy_height,
    )

    # No displacement in absence of vegetation
    return np.nan_to_num(zero_plane_displacement, nan=0.0).squeeze()


def calculate_roughness_length_momentum(
    canopy_height: NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    substrate_surface_drag_coefficient: float,
    roughness_element_drag_coefficient: float,
    roughness_sublayer_depth_parameter: float,
    max_ratio_wind_to_friction_velocity: float,
    min_roughness_length: float,
    von_karman_constant: float,
) -> NDArray[np.float32]:
    """Calculate roughness length governing momentum transfer, [m].

    Roughness length is defined as the height at which the mean velocity is zero due to
    substrate roughness. Real surfaces such as the ground or vegetation are not smooth
    and often have varying degrees of roughness. Roughness length accounts for that
    effect. Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        leaf_area_index: Total leaf area index, [m m-1]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        substrate_surface_drag_coefficient: Substrate-surface drag coefficient,
            dimensionless
        roughness_element_drag_coefficient: Roughness-element drag coefficient
        roughness_sublayer_depth_parameter: Parameter that characterizes the roughness
            sublayer depth, dimensionless
        max_ratio_wind_to_friction_velocity: Maximum ratio of wind velocity to friction
            velocity, dimensionless
        min_roughness_length: Minimum roughness length, [m]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        Momentum roughness length, [m]
    """

    # Calculate ratio of wind velocity to friction velocity
    ratio_wind_to_friction_velocity = np.sqrt(
        substrate_surface_drag_coefficient
        + (roughness_element_drag_coefficient * leaf_area_index) / 2
    )

    # If the ratio of wind velocity to friction velocity is larger than the set maximum,
    # set the value to set maximum
    set_maximum_ratio = np.where(
        ratio_wind_to_friction_velocity > max_ratio_wind_to_friction_velocity,
        max_ratio_wind_to_friction_velocity,
        ratio_wind_to_friction_velocity,
    )

    # Calculate initial roughness length
    initial_roughness_length = (canopy_height - zero_plane_displacement) * np.exp(
        -von_karman_constant * (1 / set_maximum_ratio)
        - roughness_sublayer_depth_parameter
    )

    # If roughness smaller than the substrate surface drag coefficient, set to value to
    # the substrate surface drag coefficient
    roughness_length = np.where(
        initial_roughness_length < substrate_surface_drag_coefficient,
        substrate_surface_drag_coefficient,
        initial_roughness_length,
    )

    # If roughness length in nan, zero or below sero, set to minimum value
    roughness_length = np.nan_to_num(roughness_length, nan=min_roughness_length)
    return np.where(roughness_length <= 0, min_roughness_length, roughness_length)


def calculate_wind_profile(
    reference_wind_speed: NDArray[np.float32],
    reference_height: float | NDArray[np.float32],
    wind_heights: NDArray[np.float32],
    roughness_length: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    min_wind_speed: float,
) -> NDArray[np.float32]:
    r"""Calculate wind speed profile, [m s-1].

    The wind speed at different heights is calculated using the following equation:

    .. math::
        u(z) = u_{ref} \times \frac{ \ln \left( \frac{z - d}{z_0} \right) }
                                { \ln \left( \frac{z_{ref} - d}{z_0} \right) }

    where :math:`u(z)` is the wind speed at height :math:`z`, :math:`u_{ref}` is the
    reference wind speed at reference height :math:`z_{ref}`, :math:`z` is the height at
    which the wind speed is calculated, :math:`z_0` is the roughness length, and
    :math:`d` is the zero plane displacement.

    Args:
        reference_wind_speed: Reference wind speed above the canopy, [m s-1].
        reference_height: Reference height above the canopy, [m].
        wind_heights: Heights where wind speed is to be calculated, [m].
        roughness_length: Momentum roughness length, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        min_wind_speed: Minimum wind speed, [m s-1]

    Returns:
        Wind speed, [m s-1]
    """

    # Ensure that heights are greater than roughness length and zero_plane_displacement
    # to avoid division by zero or negative logarithm
    heights = np.maximum(wind_heights, roughness_length + 1e-5)
    heights = np.maximum(wind_heights, zero_plane_displacement + 1e-5)

    wind_speed = (
        reference_wind_speed
        * np.log((heights - zero_plane_displacement) / roughness_length)
        / np.log((reference_height - zero_plane_displacement) / roughness_length)
    )
    return np.where(wind_speed >= 0, wind_speed, min_wind_speed)


def calculate_friction_velocity(
    reference_wind_speed: NDArray[np.float32],
    reference_height: NDArray[np.float32],
    roughness_length: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    von_karman_constant: float,
) -> NDArray[np.float32]:
    r"""Calculate friction velocity, [m s-1].

    Friction velocity is a measure of the shear stress exerted by the wind on the
    Earth's surface, representing the velocity scale that relates to turbulent energy
    transfer near the surface.

    The friction velocity (:math:`u^{*}`, [m s-1]) is calculated as

    :math:`u^{*} = \frac{\kappa u}{\ln{(\frac{z - d}{z_0})}}`

    Where :math:`\kappa` is the von Kármán constant, :math:`u` is the reference wind
    speed, :math:`z` is the reference height, :math:`d` is the zero plane displacement
    height, and :math:`z_{0}` is the roughness length.

    Args:
        reference_wind_speed: Reference wind speed above the canopy [m s-1].
        reference_height: Reference height above the canopy, [m].
        roughness_length: Momentum roughness length, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        Friction velocity, [m s-1].
    """

    return (von_karman_constant * reference_wind_speed) / np.log(
        (reference_height - zero_plane_displacement) / roughness_length
    )


def calculate_aerodynamic_resistance(
    wind_heights: NDArray[np.float32],
    roughness_length: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    friction_velocity: NDArray[np.float32],
    von_karman_constant: float,
) -> NDArray[np.float32]:
    """Calculate aerodynamic resistance, [s m-1].

    Args:
        wind_heights: Heights below the canopy where wind speed is to be calculated [m].
        roughness_length: Momentum roughness length, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        friction_velocity: Friction velocity [m s-1]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        aerodynamic resistance, [s m-1]
    """

    aero_resistance = np.log(
        (wind_heights - zero_plane_displacement) / roughness_length
    ) / (von_karman_constant * friction_velocity)

    return np.where(
        np.isinf(aero_resistance) | (aero_resistance <= 0), np.nan, aero_resistance
    )


def calculate_leaf_vapour_conductivity(
    air_heat_conductivity: NDArray[np.float32],
    stomatal_conductivity: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate leaf vapour conductivity, [mol m-2 s-1].

    Args:
        air_heat_conductivity: Air heat conductivity, [mol m-2 s-1]
        stomatal_conductivity: Stomatal conductivity, [mol m-2 s-1]

    Returns:
        leaf vapour conductivity, [mol m-2 s-1]
    """
    leaf_vapour_conductivity = 1 / (
        1 / air_heat_conductivity + 1 / stomatal_conductivity
    )

    return np.where(stomatal_conductivity == 0, 0, leaf_vapour_conductivity)


def calculate_effective_vapour_pressure(
    air_temperature: DataArray,
    relative_humidity: DataArray,
    saturation_vapour_pressure_factors: list[float],
) -> DataArray:
    """Calculate effective vapour pressure, [kPa].

    Args:
        air_temperature: Air temperature, [C]
        relative_humidity: Relative humidity, [-]
        saturation_vapour_pressure_factors: Factors in saturation vapour pressure
            calculation

    Returns:
        effective vapour pressure, [kPa]
    """

    saturation_vapour_pressure_air = calculate_saturation_vapour_pressure(
        temperature=air_temperature,
        saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
    )
    return saturation_vapour_pressure_air * relative_humidity / 100.0


def calculate_latent_heat_flux(
    latent_heat_vapourisation: NDArray[np.float32],
    leaf_vapour_conductivity: NDArray[np.float32],
    effective_vapour_pressure_leaf: NDArray[np.float32],
    effective_vapour_pressure_air: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate latent heat flux from canopy or soil, [W m-2].

    The latent heat flux :math:`Q_{LE}` is calculated using the following equation:

    .. math::
        Q_{LE} = L_v \cdot c_v \cdot
        \left( \frac{e_{leaf} - e_{air}}{p_{atm}} \right)

    where :math:`L_v` is the latent heat of vapourization, :math:`c_v` is the leaf
    vapour conductivity, :math:`e_{leaf}` is the effective vapour pressure at the leaf
    surface, :math:`e_{air}` is the effective vapour pressure in the air, and
    :math:`p_{atm}` is the atmospheric pressure.

    Args:
        latent_heat_vapourisation: Latent heat of vapourisation
        leaf_vapour_conductivity: Conductance for vapour loss from leaves as a function
            of stomatal conductance
        effective_vapour_pressure_leaf: Effective vapour pressure in the leaf, [kPa]
        effective_vapour_pressure_air: Effective vapour pressure in the air, [kPa]
        atmospheric_pressure: Atmospheric pressure, [kPa]

    Returns:
        Latent heat flux, [W m-2]
    """

    return (
        latent_heat_vapourisation
        * leaf_vapour_conductivity
        * (
            (effective_vapour_pressure_leaf - effective_vapour_pressure_air)
            / atmospheric_pressure
        )
    )


def run_microclimate(
    data: Data,
    time_index: int,
    layer_structure: LayerStructure,
    abiotic_constants: AbioticConsts,
    core_constants: CoreConsts,
) -> dict[str, DataArray]:
    """Run microclimate model.

    Args:
        data: Data object
        time_index: Time index
        layer_structure: layer structure object
        abiotic_constants: Set of constants for abiotic model
        core_constants: Set of constants that are shared across all models

    Returns:
        dictionary with updated microclimate variables
    """

    output = {}

    # Selection of often used subsets
    canopy_height = data["layer_heights"][1].to_numpy()
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers").to_numpy()

    # Mean atmospheric pressure profile, [kPa]
    # TODO: this should only be filled for filled/true above ground layers
    output["atmospheric_pressure"] = layer_structure.from_template()
    output["atmospheric_pressure"][layer_structure.index_atmosphere] = data[
        "atmospheric_pressure_ref"
    ].isel(time_index=time_index)

    # Mean atmospheric C02 profile, [ppm]
    # TODO: this should only be filled for filled/true above ground layers
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

    #   Zero plane displacement, [m]
    zero_plane_displacement = calculate_zero_plane_displacement(
        canopy_height=canopy_height,
        leaf_area_index=leaf_area_index_sum,
        zero_plane_scaling_parameter=abiotic_constants.zero_plane_scaling_parameter,
    )

    #   Roughness length, [m]
    roughness_length = calculate_roughness_length_momentum(
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
    wind_profile = calculate_wind_profile(
        reference_wind_speed=data["wind_speed_ref"]
        .isel(time_index=time_index)
        .to_numpy(),
        reference_height=(
            data["layer_heights"][0].to_numpy()
            + abiotic_constants.wind_reference_height
        ),
        wind_heights=data["layer_heights"][
            layer_structure.index_filled_atmosphere
        ].to_numpy(),
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        min_wind_speed=abiotic_constants.min_windspeed_below_canopy,
    )
    wind_speed = layer_structure.from_template()
    wind_speed[layer_structure.index_filled_atmosphere] = wind_profile
    output["wind_speed"] = wind_speed

    #   Friction velocity, [m s-1]
    friction_velocity = calculate_friction_velocity(
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

    #   TODO Aerodynamic resistance canopy, [s m-1], too much nan!
    # aerodynamic_resistance_canopy = 100.0
    aerodynamic_resistance_canopy = calculate_aerodynamic_resistance(
        wind_heights=data["layer_heights"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        roughness_length=roughness_length,
        zero_plane_displacement=zero_plane_displacement,
        friction_velocity=friction_velocity,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    #   TODO  Aerodynamic resistance soil, [s m-1]
    aerodynamic_resistance_soil = 100.0

    # Longwave emission from canopy, [W m-2]
    longwave_emission_canopy = calculate_longwave_emission(
        temperature=data["canopy_temperature"].to_numpy() + core_constants.zero_Celsius,
        emissivity=abiotic_constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Longwave emission from soil, [W m-2]
    longwave_emission_soil = calculate_longwave_emission(
        temperature=data["soil_temperature"].to_numpy() + core_constants.zero_Celsius,
        emissivity=abiotic_constants.leaf_emissivity,
        stefan_boltzmann=core_constants.stefan_boltzmann_constant,
    )

    # Combine longwave emission in one variable
    longwave_emission = layer_structure.from_template()
    longwave_emission[layer_structure.index_filled_canopy] = longwave_emission_canopy[
        layer_structure.index_filled_canopy
    ]
    longwave_emission[layer_structure.index_topsoil_scalar] = longwave_emission_soil[
        layer_structure.index_topsoil_scalar
    ]
    output["longwave_emission"] = longwave_emission

    # Net radiation canopy, [W m-2]
    net_radiation_canopy = calculate_net_radiation(
        incoming_radiation=data["topofcanopy_radiation"]
        .isel(time_index=time_index)
        .to_numpy(),
        absorbed_radiation=data["absorbed_radiation"].to_numpy(),
        longwave_emission=longwave_emission_canopy,
        albedo=abiotic_constants.leaf_albedo,
    )

    # Net radiation topsoil, [W m-2]
    absorbed_radiation_sum = np.nansum(data["absorbed_radiation"].to_numpy(), axis=0)
    net_radiation_soil = calculate_net_radiation(
        incoming_radiation=data["topofcanopy_radiation"]
        .isel(time_index=time_index)
        .to_numpy(),
        absorbed_radiation=absorbed_radiation_sum,
        longwave_emission=longwave_emission_soil[layer_structure.index_topsoil_scalar],
        albedo=abiotic_constants.surface_albedo,
    )

    # Combine net radiation in one variable
    net_radiation = layer_structure.from_template()
    net_radiation[layer_structure.index_filled_canopy] = net_radiation_canopy[
        layer_structure.index_filled_canopy
    ]
    net_radiation[layer_structure.index_topsoil_scalar] = net_radiation_soil

    #  Sensible heat flux from canopy layers, [W m-2]
    sensible_heat_flux_canopy = calculate_sensible_heat_flux(
        density_air=molar_density_air / core_constants.standard_mole,
        specific_heat_air=specific_heat_air,
        air_temperature=data["air_temperature"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        surface_temperature=data["canopy_temperature"][
            layer_structure.index_filled_canopy
        ].to_numpy(),
        aerodynamic_resistance=aerodynamic_resistance_canopy,
    )

    #  Sensible heat flux from topsoil, [W m-2]
    sensible_heat_flux_soil = calculate_sensible_heat_flux(
        density_air=molar_density_air / core_constants.standard_mole,
        specific_heat_air=specific_heat_air,
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
    output["sensible_heat_flux"] = sensible_heat_flux

    #   Latent heat of vapourisation, [kJ kg-1]
    latent_heat_vapourisation = abiotic_tools.calculate_latent_heat_vapourisation(
        temperature=np.nanmean(data["air_temperature"].to_numpy(), axis=0),
        celsius_to_kelvin=core_constants.zero_Celsius,
        latent_heat_vap_equ_factors=abiotic_constants.latent_heat_vap_equ_factors,
    )

    #  TODO Effective vapour pressure, [kPa]
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

    # Latent heat flux canopy, [W m-2]
    # TODO cross-check with plant model, time step
    latent_heat_flux_canopy = (
        data["evapotranspiration"][layer_structure.index_filled_canopy].to_numpy()
        / 86400.0
    ) * latent_heat_vapourisation
    # latent_heat_flux_canopy = calculate_latent_heat_flux(
    #     latent_heat_vapourisation=latent_heat_vapourisation,
    #     leaf_vapour_conductivity=leaf_vapour_conductivity,
    #     effective_vapour_pressure_leaf=effective_vapour_pressure_leaf,
    #     effective_vapour_pressure_air=effective_vapour_pressure_air,
    #     atmospheric_pressure=data["atmospheric_pressure"].to_numpy()
    # )

    # Latent heat flux topsoil, [W m-2]
    # TODO cross-check with hydrology model, time step
    latent_heat_flux_soil = (
        data["soil_evaporation"].to_numpy() / 86400 * latent_heat_vapourisation
    )

    # Combine latent heat flux in one variable
    latent_heat_flux = layer_structure.from_template()
    latent_heat_flux[layer_structure.index_filled_canopy] = latent_heat_flux_canopy
    latent_heat_flux[layer_structure.index_topsoil_scalar] = latent_heat_flux_soil
    output["latent_heat_flux"] = latent_heat_flux

    # Ground heat flux

    # Update air/canopy/soil temperatures

    # Update humidity/VPD

    return output
