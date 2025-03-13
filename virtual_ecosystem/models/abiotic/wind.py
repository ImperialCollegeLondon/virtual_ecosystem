r"""The wind module calculates the above- and within-canopy wind profile for the
Virtual Ecosystem. The wind profile determines the exchange of heat, water, and
:math:`CO_{2}` between soil and atmosphere below the canopy as well as the exchange with
the atmosphere above the canopy.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray


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
    return np.where(
        roughness_length <= min_roughness_length, min_roughness_length, roughness_length
    )


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
        min_wind_speed: Minimum wind speed to avoid division by zero, [m s-1]

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
    return np.where(wind_speed >= min_wind_speed, wind_speed, min_wind_speed)


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
