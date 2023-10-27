r"""The wind module calculates the above- and within-canopy wind profiles for the
Virtual Rainforest. These profiles will determine the exchange of heat, water, and
:math:`CO_{2}` between soil and atmosphere below the canopy as well as the exchange with
the atmsophere above the canopy.
TODO: add sanity checks, errors and logging
TODO check equations for above profile, and howdoes it need adjustment for below
TODO add function that alls all the steps and returns info for data object
TODO select wind layer heights
"""  # noqa: D205, D415

from typing import Union

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.models.abiotic.abiotic_tools import (
    calculate_molar_density_air,
    calculate_specific_heat_air,
)


def calculate_zero_plane_displacement(
    canopy_height: NDArray[np.float32],
    plant_area_index: NDArray[np.float32],
    zero_plane_scaling_parameter: float,
) -> NDArray[np.float32]:
    """Calculate zero plane displacement.

    The zero plane displacement height of a vegetated surface is the height at which the
    wind speed would go to zero if the logarithmic wind profile was maintained from the
    outer flow all the way down to the surface (that is, in the absence of the
    vegetation when the value is set to zero). Implementation after
    :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        plant_area_index: leaf area index, [m m-1]
        zero_plane_scaling_parameter: Control parameter for scaling d/h
            :cite:p:`raupach_simplified_1994`

    Returns:
        zero place displacement height, [m]
    """

    # Calculate in presence of vegetation
    plant_area_index_displacement = np.where(
        plant_area_index > 0, plant_area_index, np.nan
    )

    scale_displacement = np.sqrt(
        zero_plane_scaling_parameter * plant_area_index_displacement
    )

    zero_place_displacement = (
        (1 - (1 - np.exp(-scale_displacement)) / scale_displacement) * canopy_height,
    )

    # no displacement in absence of vegetation
    return np.nan_to_num(zero_place_displacement, nan=0.0).squeeze()


def calculate_roughness_length_momentum(
    canopy_height: NDArray[np.float32],
    plant_area_index: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    substrate_surface_drag_coefficient: float,
    roughness_element_drag_coefficient: float,
    roughness_sublayer_depth_parameter: float,
    max_ratio_wind_to_friction_velocity: float,
    von_karman_constant: float,
) -> NDArray[np.float32]:
    """Calculate roughness length governing momentum transfer.

    Roughness length is defined as the height at which the mean velocity is zero due to
    substrate roughness. Real surfaces such as the ground or vegetation are not smooth
    and often have varying degrees of roughness. Roughness length accounts for that
    effect. Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        plant_area_index: plant area index, [m m-1]
        substrate_surface_drag_coefficient: substrate-surface drag coefficient
        zero_plane_displacement: height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_element_drag_coefficient: roughness-element drag coefficient
        roughness_sublayer_depth_parameter: parameter characterizes the roughness
            sublayer depth
        max_ratio_wind_to_friction_velocity: Maximum ratio of wind velocity to friction
            velocity

    Returns:
        momentum roughness length, [m]
    """

    # calculate ratio of wind velocity to friction velocity
    ratio_wind_to_friction_velocity = np.sqrt(
        substrate_surface_drag_coefficient
        + (roughness_element_drag_coefficient * plant_area_index) / 2
    )

    # if the ratio of wind velocity to friction velocity is larger than the set maximum,
    # set the value to set maximum
    set_maximum_ratio = np.where(
        ratio_wind_to_friction_velocity > max_ratio_wind_to_friction_velocity,
        max_ratio_wind_to_friction_velocity,
        ratio_wind_to_friction_velocity,
    )

    # calculate initial roughness length
    initial_roughness_length = (canopy_height - zero_plane_displacement) * np.exp(
        -von_karman_constant * (1 / set_maximum_ratio)
        - roughness_sublayer_depth_parameter
    )

    # if roughness smaller than the substrate surface drag coefficient, set to value to
    # the substrate surface drag coefficient
    roughness_length = np.where(
        initial_roughness_length < substrate_surface_drag_coefficient,
        substrate_surface_drag_coefficient,
        initial_roughness_length,
    )

    return np.where(roughness_length <= 0, 0.01, roughness_length)


def calculate_diabatic_correction_above(
    temperature: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
    sensible_heat_flux: NDArray[np.float32],
    friction_velocity: NDArray[np.float32],
    wind_heights_above_canopy: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    celsius_to_kelvin: float,
    standard_mole: float,
    standard_pressure: float,
    molar_heat_capacity_air: float,
    specific_heat_equ_factor_1: float,
    specific_heat_equ_factor_2: float,
    von_karmans_constant: float,
) -> dict[str, NDArray[np.float32]]:
    r"""Calculates the diabatic correction factors for momentum and heat above canopy.

    Diabatic correction factor for heat and momentum are used to adjust wind profiles
    for surface heating and cooling :cite:p:`maclean_microclimc_2021`. When the surface
    is strongly heated, the diabatic correction factor for momemtum :math:`psi_{m}`
    becomes negative and drops to values of around -1.5. In contrast, when the surface
    is much cooler than the air above it, it increases to values around 4.

    Args:
        temperature: 2m temperature
        atmospheric_pressure: atmospheric pressure, [kPa]
        sensible_heat_flux: sensible heat flux from canopy to atmosphere above,
            [W m-2], # TODO: could be the top entry of the general sensible heat flux
        friction_velocity: friction velocity
        wind_heights: vector of heights for which wind speed is calculated, [m]
        zero_plane_displacement: height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        standard_mole: Moles of ideal gas in 1 m^3 air at standard atmosphere
        standard_pressure: Standard atmospheric pressure, [kPa]
        molar_heat_capacity_air: molar heat capacity of air, [J mol-1 C-1]
        specific_heat_equ_factor_1: Factor in calculation of molar specific heat of air
        specific_heat_equ_factor_2: Factor in calculation of molar specific heat of air
        von_karmans_constant

    Returns:
        diabatic correction factors for heat (psi_h) and momentum (psi_m) transfer
    """

    molar_density_air = calculate_molar_density_air(
        temperature=temperature,
        atmospheric_pressure=atmospheric_pressure,
        standard_mole=standard_mole,
        standard_pressure=standard_pressure,
        celsius_to_kelvin=celsius_to_kelvin,
    )
    specific_heat_air = calculate_specific_heat_air(
        temperature=temperature,
        molar_heat_capacity_air=molar_heat_capacity_air,
        specific_heat_equ_factor_1=specific_heat_equ_factor_1,
        specific_heat_equ_factor_2=specific_heat_equ_factor_2,
    )

    # calculate atmospheric stability
    stability = (
        von_karmans_constant
        * (wind_heights_above_canopy - zero_plane_displacement)
        * sensible_heat_flux
    ) / (
        molar_density_air
        * specific_heat_air
        * (temperature + celsius_to_kelvin)
        * friction_velocity
    )

    stable_condition = 6 * np.log(1 - stability)
    unstable_condition = -2 * np.log((1 + np.sqrt(1 - 16 * stability)) / 2)

    diabatic_correction_heat = np.where(
        stability < 0, stable_condition, unstable_condition
    )

    diabatic_correction_momentum = np.where(
        stability < 0, diabatic_correction_heat, 0.6 * diabatic_correction_heat
    )

    # Apply upper threshold
    diabatic_correction_momentum = np.minimum(diabatic_correction_momentum, 5)
    diabatic_correction_heat = np.minimum(diabatic_correction_heat, 5)

    return {"psi_m": diabatic_correction_momentum, "psi_h": diabatic_correction_heat}


def calculate_mixing_length(
    canopy_height: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    roughness_length_momentum: NDArray[np.float32],
    mixing_length_factor: float,
) -> NDArray[np.float32]:
    """Calculate mixing length for canopy air transport.

    The mixing length is used to calculate turbulent air transport inside vegetated
    canopies. It is made equivalent to the above canopy value at the canopy surface. In
    absence of vegetation, it is set to zero.
    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        leaf_area_index: leaf area index, [m m-1]
        zero_plane_displacement: height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: momentum roughness length, [m]
        mixing_length_factor: Factor in calculation of mixing length

    Returns:
        mixing length for canopy air transport, [m]
    """

    mixing_length = (
        mixing_length_factor * (canopy_height - zero_plane_displacement)
    ) / np.log((canopy_height - zero_plane_displacement) / roughness_length_momentum)

    return np.nan_to_num(mixing_length, nan=0)


def calculate_wind_attenuation_coefficient(
    canopy_height: NDArray[np.float32],
    plant_area_index: NDArray[np.float32],
    mixing_length: NDArray[np.float32],
    drag_coefficient: float,
    relative_turbulence_intensity: float,
    diabatic_correction_factor_below: float,
) -> NDArray[np.float32]:
    """Calculate wind attenuation coefficient.

    The wind attenuation coefficient describes how wind is slowed down by the presence
    of vegetation. In absence of vegetation, the coefficient is set to zero.
    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        plant_area_index: plant area index, [m m-1]
        mixing_length: mixing length for canopy air transport, [m]
        drag_coefficient: drag coefficient
        relative_turbulence_intensity: relative turbulence intensity
        diabatic_correction_factor_below: diabatic correction factor below canopy

    Returns:
        wind attenuation coefficient
    """

    intermediate_coefficient1 = (
        (drag_coefficient * plant_area_index * canopy_height)
        / (2 * mixing_length * relative_turbulence_intensity),
    )

    intermediate_coefficient2 = np.power(intermediate_coefficient1, 0.5)

    atten_coeff = intermediate_coefficient2 * np.power(
        diabatic_correction_factor_below, 0.5
    )

    return np.nan_to_num(atten_coeff, nan=0).squeeze()


def wind_log_profile(
    height: Union[float, NDArray[np.float32]],
    zeroplane_displacement: Union[float, NDArray[np.float32]],
    roughness_length_momentum: Union[float, NDArray[np.float32]],
    diabatic_correction_momentum: Union[float, NDArray[np.float32]],
) -> NDArray[np.float32]:
    """Calculate logarithmic wind profile.

    Args:
        height: array of heights for which wind speed is calculated, [m]
        zeroplane_displacement: height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: momentum roughness length, [m]
        diabatic_correction_momentum: diabaric correction factor for momentum

    Returns:
        logarithmic wind profile, [m s-1]
    """

    wind_profile = (
        np.log((height - zeroplane_displacement) / roughness_length_momentum)
        + diabatic_correction_momentum,
    )

    return np.nan_to_num(wind_profile, nan=1).squeeze()


def calculate_wind_profile(
    wind_speed_ref: NDArray[np.float32],
    reference_height: float,
    wind_layer_heights: NDArray[np.float32],
    attenuation_coefficient: NDArray[np.float32],
    plant_area_index: NDArray[np.float32],
    canopy_height: NDArray[np.float32],
    diabatic_correction_momentum: NDArray[np.float32],
    ground_layer_vegetation_height: Union[float, NDArray[np.float32]],
    roughness_sublayer_depth_parameter: float,
    zero_plane_scaling_parameter: float,
    substrate_surface_drag_coefficient: float,
    roughness_element_drag_coefficient: float,
    max_ratio_wind_to_friction_velocity: float,
    von_karmans_constant: float,
) -> NDArray[np.float32]:
    """Calculate wind speed at any given height from wind speed at reference height.

    Wind profile above the canopy dictates heat and vapor exchange between the canopy
    and air above it, and therefore ultimately determine temperature and vapor profiles.
    The wind profile above canopy typically follows a logarithmic height profile, which
    extrapolates to zero roughly two thirds of the way to the top of the canopy. The
    profile itself is thus dependent on the height of the canopy, but also on the
    roughness of the vegetation layer, which causes wind shear. We follow the
    implementation by :cite:t:`campbell_introduction_1998` as described in
    :cite:t:`maclean_microclimc_2021`.

    Args:
        wind_speed_ref: Wind speed at reference height, [m s-1]
        reference_height: Height of wind measurement, [m]
        wind_layer_heights: Heights for which wind speed is required, [m]
        attenuation_coefficient: Attenuation coefficient as returned by
            :func:`~virtual_rainforest.models.abiotic.wind.calculate_wind_attenuation_coefficient`
        plant_area_index: Plant area index, [m m-1]
        canopy_height: Canopy height, [m]
        diabatic_correction_momentum: Diabatic correction factor for momentum as
            returned by
            :func:`~virtual_rainforest.models.abiotic.wind.calculate_diabatic_correction_above`
        ground_layer_vegetation_height: Height of ground vegetation layer below canopy,
            [m]
        roughness_sublayer_depth_parameter: parameter characterizes the roughness
           sublayer depth, [m]
        zero_plane_scaling_parameter: Control parameter for scaling zero
            displacement/height
        substrate_surface_drag_coefficient: Substrate-surface drag coefficient
        roughness_element_drag_coefficient: Roughness-element drag coefficient
        max_ratio_wind_to_friction_velocity: Maximum ratio of wind velocity to friction
            velocity
        von_karmans_constant: Von Karman's constant, unitless, describes the logarithmic
            velocity profile of a turbulent fluid near a no-slip boundary

    Returns:
        wind speed at required heights above and below canopy, [m s-1]
    """

    # Calculate zero-plane displacement
    zeroplane_displacement = calculate_zero_plane_displacement(
        canopy_height=canopy_height,
        plant_area_index=plant_area_index,
        zero_plane_scaling_parameter=zero_plane_scaling_parameter,
    )

    # Calculate roughness length for momentum, [m]
    roughness_length = calculate_roughness_length_momentum(
        canopy_height=canopy_height,
        plant_area_index=plant_area_index,
        zero_plane_displacement=zeroplane_displacement,
        substrate_surface_drag_coefficient=substrate_surface_drag_coefficient,
        roughness_element_drag_coefficient=roughness_element_drag_coefficient,
        roughness_sublayer_depth_parameter=roughness_sublayer_depth_parameter,
        max_ratio_wind_to_friction_velocity=max_ratio_wind_to_friction_velocity,
        von_karman_constant=von_karmans_constant,
    )

    roughness_length_ground_vegetation = 0.1 * ground_layer_vegetation_height

    # reference wind profile
    wind_profile_reference = wind_log_profile(
        height=reference_height,
        zeroplane_displacement=zeroplane_displacement,
        roughness_length_momentum=roughness_length,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )

    friction_velocity = von_karmans_constant * (wind_speed_ref / wind_profile_reference)

    wind_profile_above = wind_log_profile(
        height=wind_layer_heights,
        zeroplane_displacement=zeroplane_displacement,
        roughness_length_momentum=roughness_length,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )
    wind_profile_above[wind_profile_above < 0.55] = 0.55

    wind_profile_below = wind_log_profile(
        height=wind_layer_heights,
        zeroplane_displacement=zeroplane_displacement,
        roughness_length_momentum=roughness_length,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )

    wind_profile = np.where(
        wind_layer_heights > canopy_height, wind_profile_above, wind_profile_below
    )
    wind_speed = (friction_velocity / von_karmans_constant) * wind_profile

    # Required height above 10% of canopy hgt, but below top of canopy
    wind_10percent_above = wind_speed * np.exp(
        attenuation_coefficient * ((wind_layer_heights / canopy_height) - 1)
    )

    wind_speed = np.where(
        (wind_layer_heights > (0.1 * canopy_height))
        & (wind_layer_heights < canopy_height),
        wind_10percent_above,
        wind_speed,
    )

    # Required height below 10% of canopy hgt
    wind_10percent_below = wind_speed * np.exp(
        attenuation_coefficient * (((0.1 * canopy_height) / canopy_height) - 1)
    )

    wind_profile_reference_below = wind_log_profile(
        height=0.1 * canopy_height,
        zeroplane_displacement=0.0,
        roughness_length_momentum=roughness_length_ground_vegetation,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )

    friction_velocity_below = von_karmans_constant * (
        wind_10percent_below / wind_profile_reference_below
    )

    wind_profile_10percent_below = wind_log_profile(
        height=wind_layer_heights,
        zeroplane_displacement=zeroplane_displacement,
        roughness_length_momentum=roughness_length_ground_vegetation,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )

    wind_speed_10percent_below = (
        friction_velocity_below / von_karmans_constant
    ) * wind_profile_10percent_below

    complete_wind_profile = np.where(
        wind_layer_heights <= (0.1 * canopy_height),
        wind_speed_10percent_below,
        wind_speed,
    )

    return complete_wind_profile


# def update_wind_profile( TODO this is outdated
#     wind_heights_above_canopy: NDArray[np.float32],
#     wind_heights_below_canopy: NDArray[np.float32],
#     temperature: NDArray[np.float32],
#     atmospheric_pressure: NDArray[np.float32],
#     friction_velocity: NDArray[np.float32],
#     canopy_height: NDArray[np.float32],
#     leaf_area_index: NDArray[np.float32],
#     sensible_heat_topofcanopy: NDArray[np.float32],
#     abiotic_const: AbioticConsts,
# ) -> Tuple[DataArray, DataArray]:
#     r"""Calculate wind profile above and below canopy.

#     The wind profile above the canopy is described as follows
#     (based on :cite:p:`campbell_introduction_1998` as implemented in
#     :cite:t:`maclean_microclimc_2021`):

#     :math:`u_z = \frac{u^{*}}{0.4} ln \frac{z-d}{z_M} + \phi_M`

#     where :math:`u_z` is wind speed at height :math:`z` above the canopy, :math:`d` is
#     the height above ground within the canopy where the wind profile extrapolates to
#     zero, :math:`z_m` the roughness length for momentum, :math:`\phi_M` is a diabatic
#    correction for momentum and :math:`u^{*}` is the friction velocity, which gives the
#     wind speed at height :math:`d + z_m`.

#     The wind profile below canopy is derived as follows:

#     :math:`u_z = u_h exp(a(\frac{z}{h} - 1))`

#     where :math:`u_z` is wind speed at height :math:`z` within the canopy, :math:`u_h`
#    is wind speed at the top of the canopy at height :math:`h`, and :math:`a` is a wind
#    attenuation coefficient given by :math:`a = 2 l_m i_w`, where :math:`c_d` is a drag
#    coefficient that varies with leaf inclination and shape, :math:`i_w` is a
#     coefficient describing relative turbulence intensity and :math:`l_m` is the mean
#     mixing length, equivalent to the free space between the leaves and stems. For
#     details, see :cite:t:`maclean_microclimc_2021`.

#     Args:
#         wind_heights_above_canopy: array of heights above canopy for which wind speed
#             is calculated, [m]
#         wind_heights_below_canopy: array of heights below canopy for which wind speed
#             is calculated, [m], base on 'layer_heights' variable
#         temperature: Air temperature, [C]
#         atmospheric_pressure: Atmospheric pressure, [kPa]
#         friction_velocity: friction velocity, TODO
#         canopy_height: Canopy height, [m]
#         leaf_area_index: leaf area index, [m m-1]
#         sensible_heat_topofcanopy: Sensible heat flux at the top of the canopy, TODO
#         abiotic_const: An AbioticConsts instance

#     Returns:
#         vertical wind profile above canopy, [m s-1]
#         vertical wind profile within canopy, [m s-1]
#     """

#     # preparatory calculations for wind profiles
#     zero_plane_displacement = calculate_zero_plane_displacement(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index,
#         zero_plane_scaling_parameter=abiotic_const.zero_plane_scaling_parameter,
#     )
#     roughness_length_momentum = calculate_roughness_length_momentum(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index,
#         zero_plane_displacement=zero_plane_displacement,
#         substrate_surface_drag_coefficient=(
#             abiotic_const.substrate_surface_drag_coefficient
#         ),
#         roughness_element_drag_coefficient=(
#             abiotic_const.roughness_element_drag_coefficient
#         ),
#         roughness_sublayer_depth_parameter=(
#             abiotic_const.roughness_sublayer_depth_parameter
#         ),
#         max_ratio_wind_to_friction_velocity=(
#             abiotic_const.max_ratio_wind_to_friction_velocity
#         ),
#     )

#     diabatic_correction_momentum_above = calculate_diabatic_correction_momentum_above(
#         temperature=temperature,
#         atmospheric_pressure=atmospheric_pressure,
#         sensible_heat_flux=sensible_heat_topofcanopy,
#         friction_velocity=friction_velocity,
#         wind_heights=wind_heights_above_canopy,
#         zero_plane_displacement=zero_plane_displacement,
#         celsius_to_kelvin=abiotic_const.celsius_to_kelvin,
#         gravity=abiotic_const.gravity,
#     )

#     mixing_length = calculate_mixing_length(
#         canopy_height=canopy_height,
#         zero_plane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         mixing_length_factor=abiotic_const.mixing_length_factor,
#     )

#     wind_attenuation_coefficient = calculate_wind_attenuation_coefficient(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index,
#         mixing_length=mixing_length,
#         drag_coefficient=abiotic_const.drag_coefficient,
#         relative_turbulence_intensity=abiotic_const.relative_turbulence_intensity,
#         diabatic_correction_factor_below=abiotic_const.diabatic_correction_factor_below,
#     )

#     # Calculate wind profiles and return as Tuple
#     wind_profile_above = calculate_wind_above_canopy(
#         wind_heights_above_canopy=wind_heights_above_canopy,
#         zero_plane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         diabatic_correction_momentum_above=diabatic_correction_momentum_above,
#         friction_velocity=friction_velocity,
#     )

#     wind_profile_canopy = calculate_wind_below_canopy(
#         canopy_node_heights=wind_heights_below_canopy,
#         wind_profile_above=wind_profile_above,
#         wind_attenuation_coefficient=wind_attenuation_coefficient,
#         canopy_height=canopy_height,
#     )

#     return wind_profile_above, wind_profile_canopy
