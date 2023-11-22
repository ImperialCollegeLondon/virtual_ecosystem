r"""The wind module calculates the above- and within-canopy wind profile for the
Virtual Rainforest. The wind profile determines the exchange of heat, water, and
:math:`CO_{2}` between soil and atmosphere below the canopy as well as the exchange with
the atmosphere above the canopy.

The wind profile above the canopy is described as follows (based on
:cite:p:`campbell_introduction_1998` as implemented in
:cite:t:`maclean_microclimc_2021`):

:math:`u_z = \frac{u^{*}}{0.4} ln \frac{z-d}{z_M} + \phi_M`

where :math:`u_z` is wind speed at height :math:`z` above the canopy, :math:`d` is
the height above ground within the canopy where the wind profile extrapolates to
zero, :math:`z_m` the roughness length for momentum, :math:`\phi_M` is a diabatic
correction for momentum and :math:`u^{*}` is the friction velocity, which gives the
wind speed at height :math:`d + z_m`.

The wind profile below canopy is derived as follows:

:math:`u_z = u_h exp(a(\frac{z}{h} - 1))`

where :math:`u_z` is wind speed at height :math:`z` within the canopy, :math:`u_h`
is wind speed at the top of the canopy at height :math:`h`, and :math:`a` is a wind
attenuation coefficient given by :math:`a = 2 l_m i_w`, where :math:`c_d` is a drag
coefficient that varies with leaf inclination and shape, :math:`i_w` is a
coefficient describing relative turbulence intensity and :math:`l_m` is the mean
mixing length, equivalent to the free space between the leaves and stems. For
details, see :cite:t:`maclean_microclimc_2021`.

TODO: add sanity checks, errors and logging
TODO add function that calls all the steps and returns info for data object
"""  # noqa: D205, D415

from typing import Union

import numpy as np
from numpy.typing import NDArray


def calculate_zero_plane_displacement(
    canopy_height: NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    zero_plane_scaling_parameter: float,
) -> NDArray[np.float32]:
    """Calculate zero plane displacement.

    The zero plane displacement height of a vegetated surface is the height at which the
    wind speed would go to zero if the logarithmic wind profile was maintained from the
    outer flow all the way down to the surface (that is, in the absence of the
    vegetation when the value is set to zero). Implementation after
    :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        leaf_area_index: Total leaf area index, [m m-1]
        zero_plane_scaling_parameter: Control parameter for scaling d/h
            :cite:p:`raupach_simplified_1994`

    Returns:
        zero place displacement height, [m]
    """

    # Calculate in presence of vegetation
    leaf_area_index_displacement = np.where(
        leaf_area_index > 0, leaf_area_index, np.nan
    )

    scale_displacement = np.sqrt(
        zero_plane_scaling_parameter * leaf_area_index_displacement
    )

    zero_place_displacement = (
        (1 - (1 - np.exp(-scale_displacement)) / scale_displacement) * canopy_height,
    )

    # no displacement in absence of vegetation
    return np.nan_to_num(zero_place_displacement, nan=0.0).squeeze()


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
    """Calculate roughness length governing momentum transfer.

    Roughness length is defined as the height at which the mean velocity is zero due to
    substrate roughness. Real surfaces such as the ground or vegetation are not smooth
    and often have varying degrees of roughness. Roughness length accounts for that
    effect. Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        leaf_area_index: Total leaf area index, [m m-1]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        substrate_surface_drag_coefficient: Substrate-surface drag coefficient
        roughness_element_drag_coefficient: Roughness-element drag coefficient
        roughness_sublayer_depth_parameter: Parameter that characterizes the roughness
            sublayer depth
        max_ratio_wind_to_friction_velocity: Maximum ratio of wind velocity to friction
            velocity
        min_roughness_length: Minimum roughness length, [m]
        von_karman_constant: Von Karman's constant, unitless constant describing the
            logarithmic velocity profile of a turbulent fluid near a no-slip boundary.

    Returns:
        momentum roughness length, [m]
    """

    # calculate ratio of wind velocity to friction velocity
    ratio_wind_to_friction_velocity = np.sqrt(
        substrate_surface_drag_coefficient
        + (roughness_element_drag_coefficient * leaf_area_index) / 2
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

    return np.where(roughness_length <= 0, min_roughness_length, roughness_length)


def calculate_diabatic_correction_above(
    molar_density_air: Union[float, NDArray[np.float32]],
    specific_heat_air: Union[float, NDArray[np.float32]],
    temperature: NDArray[np.float32],
    sensible_heat_flux: NDArray[np.float32],
    friction_velocity: NDArray[np.float32],
    wind_heights: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    celsius_to_kelvin: float,
    von_karmans_constant: float,
) -> dict[str, NDArray[np.float32]]:
    r"""Calculates the diabatic correction factors for momentum and heat above canopy.

    Diabatic correction factor for heat and momentum are used to adjust wind profiles
    for surface heating and cooling :cite:p:`maclean_microclimc_2021`. When the surface
    is strongly heated, the diabatic correction factor for momemtum :math:`psi_{m}`
    becomes negative and drops to values of around -1.5. In contrast, when the surface
    is much cooler than the air above it, it increases to values around 4.

    Args:
        molar_density_air: molar density of air, [mol m-3]
        specific_heat_air: specific heat of air, [J mol-1 K-1]
        temperature: 2m temperature
        sensible_heat_flux: Sensible heat flux from canopy to atmosphere above,
            [W m-2], # TODO: could be the top entry of the general sensible heat flux
        friction_velocity: Friction velocity
        wind_heights: Vector of heights for which wind speed is calculated, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        von_karmans_constant

    Returns:
        diabatic correction factors for heat (psi_h) and momentum (psi_m) transfer
    """

    # calculate atmospheric stability
    stability = (
        von_karmans_constant
        * (wind_heights - zero_plane_displacement)
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


def calculate_mean_mixing_length(
    canopy_height: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    roughness_length_momentum: NDArray[np.float32],
    mixing_length_factor: float,
) -> NDArray[np.float32]:
    """Calculate mixing length for canopy air transport.

    The mean mixing length is used to calculate turbulent air transport inside vegetated
    canopies. It is made equivalent to the above canopy value at the canopy surface. In
    absence of vegetation, it is set to zero. Implementation after
    :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: Momentum roughness length, [m]
        mixing_length_factor: Factor in calculation of mean mixing length

    Returns:
        mixing length for canopy air transport, [m]
    """

    mean_mixing_length = (
        mixing_length_factor * (canopy_height - zero_plane_displacement)
    ) / np.log((canopy_height - zero_plane_displacement) / roughness_length_momentum)

    return np.nan_to_num(mean_mixing_length, nan=0)


def generate_relative_turbulence_intensity(
    layer_heights: NDArray[np.float32],
    min_relative_turbulence_intensity: float,
    max_relative_turbulence_intensity: float,
    increasing_with_height: bool,
) -> NDArray[np.float32]:
    """Generate relative turbulence intensity profile.

    At the moment, default values are for a maize crop Shaw et al (1974)
    Agricultural Meteorology, 13: 419-425. TODO adjust to environment

    Args:
        layer_heights: heights of above ground layers, m
        min_relative_turbulence_intensity: minimum relative turbulence intensity
        max_relative_turbulence_intensity: maximum relative turbulence intensity
        increasing_with_height: increasing logical indicating whether turbulence
            intensity increases (TRUE) or decreases (FALSE) with height

    Returns:
        relative turbulence intensity for each node
    """

    if increasing_with_height:
        turbulence_intensity = (
            min_relative_turbulence_intensity
            + (max_relative_turbulence_intensity - min_relative_turbulence_intensity)
            * layer_heights
        )
    else:
        turbulence_intensity = (
            max_relative_turbulence_intensity
            - (max_relative_turbulence_intensity - min_relative_turbulence_intensity)
            * layer_heights
        )
    return turbulence_intensity


def calculate_wind_attenuation_coefficient(
    canopy_height: NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    mean_mixing_length: NDArray[np.float32],
    drag_coefficient: float,
    relative_turbulence_intensity: NDArray[np.float32],
    diabatic_correction_factor_below: float,
) -> NDArray[np.float32]:
    """Calculate wind attenuation coefficient.

    The wind attenuation coefficient describes how wind is slowed down by the presence
    of vegetation. In absence of vegetation, the coefficient is set to zero.
    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        leaf_area_index: Total leaf area index, [m m-1]
        mean_mixing_length: Mixing length for canopy air transport, [m]
        drag_coefficient: Drag coefficient
        relative_turbulence_intensity: Relative turbulence intensity
        diabatic_correction_factor_below: Diabatic correction factor for momentum

    Returns:
        wind attenuation coefficient
    """

    intermediate_coefficient1 = (
        (drag_coefficient * leaf_area_index * canopy_height)
        / (2 * mean_mixing_length * relative_turbulence_intensity),
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
        height: Array of heights for which wind speed is calculated, [m]
        zeroplane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: Momentum roughness length, [m]
        diabatic_correction_momentum: Diabatic correction factor for momentum

    Returns:
        logarithmic wind profile, [m s-1]
    """

    wind_profile = (
        np.log((height - zeroplane_displacement) / roughness_length_momentum)
        + diabatic_correction_momentum,
    )

    return np.nan_to_num(wind_profile, nan=1).squeeze()


def calculate_fricition_velocity(
    wind_speed_ref: NDArray[np.float32],
    reference_height: float,
    zeroplane_displacement: NDArray[np.float32],
    roughness_length_momentum: NDArray[np.float32],
    diabatic_correction_momentum: NDArray[np.float32],
    von_karmans_constant: float,
) -> NDArray[np.float32]:
    """Calculate friction velocity from wind speed at reference height.

    Args:
        wind_speed_ref: Wind speed at reference height, [m s-1]
        reference_height: Height of wind measurement, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: Momentum roughness length, [m]
        diabatic_correction_momentum: Diabatic correction factor for momentum as
            returned by
            :func:`~virtual_rainforest.models.abiotic.wind.calculate_diabatic_correction_above`
        von_karmans_constant: Von Karman's constant, unitless, describes the logarithmic
            velocity profile of a turbulent fluid near a no-slip boundary

    Returns:
        friction velocity
    """

    wind_profile_reference = wind_log_profile(
        height=reference_height,
        zeroplane_displacement=zeroplane_displacement,
        roughness_length_momentum=roughness_length_momentum,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )

    return von_karmans_constant * (wind_speed_ref / wind_profile_reference)


def calculate_wind_above_canopy(
    friction_velocity: NDArray[np.float32],
    wind_layer_heights: NDArray[np.float32],
    zeroplane_displacement: NDArray[np.float32],
    roughness_length_momentum: NDArray[np.float32],
    diabatic_correction_momentum: NDArray[np.float32],
    von_karmans_constant: float,
    min_wind_speed_above_canopy: float,
) -> NDArray[np.float32]:
    """Calculate wind speed above canopy from wind speed at reference height.

    Wind speed above the canopy dictates heat and vapor exchange between the canopy
    and the air above it, and therefore ultimately determines temperature and vapor
    profiles.
    The wind profile above canopy typically follows a logarithmic height profile, which
    extrapolates to zero roughly two thirds of the way to the top of the canopy. The
    profile itself is thus dependent on the height of the canopy, but also on the
    roughness of the vegetation layer, which causes wind shear. We follow the
    implementation by :cite:t:`campbell_introduction_1998` as described in
    :cite:t:`maclean_microclimc_2021`.

    Args:
        friction_velocity: friction velocity
        wind_layer_heights: Heights for which wind speed is required, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: Momentum roughness length, [m]
        diabatic_correction_momentum: Diabatic correction factor for momentum as
            returned by
            :func:`~virtual_rainforest.models.abiotic.wind.calculate_diabatic_correction_above`
        von_karmans_constant: Von Karman's constant, unitless, describes the logarithmic
            velocity profile of a turbulent fluid near a no-slip boundary

    Returns:
        wind speed at required heights above canopy, [m s-1]
    """

    wind_profile_above = wind_log_profile(
        height=wind_layer_heights,
        zeroplane_displacement=zeroplane_displacement,
        roughness_length_momentum=roughness_length_momentum,
        diabatic_correction_momentum=diabatic_correction_momentum,
    )
    np.where(
        wind_profile_above < min_wind_speed_above_canopy,
        min_wind_speed_above_canopy,
        wind_profile_above,
    )

    return (friction_velocity / von_karmans_constant) * wind_profile_above


def calculate_wind_canopy(
    top_of_canopy_wind_speed: NDArray[np.float32],
    wind_layer_heights: NDArray[np.float32],
    canopy_height: NDArray[np.float32],
    attenuation_coefficient: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate wind profile for individual canopy layers with variable leaf area.

    This function can be extended to account for edge distance effects.

    Args:
        top_of_canopy_wind_speed: Wind speed at top of canopy layer, [m /s]
        wind_layer_heights: Height of canopy layer node, [m]
        canopy_height: Height to top of canopy layer, [m]
        attenuation_coefficient: Attenuation coefficient as returned by
            :func:`~virtual_rainforest.models.abiotic.wind.calculate_wind_attenuation_coefficient`

    Returns:
        wind speed at height of canopy node, [m/s]
    """

    return np.nan_to_num(
        top_of_canopy_wind_speed
        * np.exp(attenuation_coefficient * ((wind_layer_heights / canopy_height) - 1)),
        nan=0,
    ).squeeze()


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

#     mean_mixing_length = calculate_mean_mixing_length(
#         canopy_height=canopy_height,
#         zero_plane_displacement=zero_plane_displacement,
#         roughness_length_momentum=roughness_length_momentum,
#         mixing_length_factor=abiotic_const.mixing_length_factor,
#     )

#     wind_attenuation_coefficient = calculate_wind_attenuation_coefficient(
#         canopy_height=canopy_height,
#         leaf_area_index=leaf_area_index,
#         mean_mixing_length=mean_mixing_length,
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
