r"""The wind module calculates the above- and within-canopy wind profile for the
Virtual Ecosystem. The wind profile determines the exchange of heat, water, and
:math:`CO_{2}` between soil and atmosphere below the canopy as well as the exchange with
the atmosphere above the canopy.
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray


def calculate_zero_plane_displacement(
    canopy_height: NDArray[np.floating],
    leaf_area_index: NDArray[np.floating],
    zero_plane_scaling_parameter: float,
) -> NDArray[np.floating]:
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
    canopy_height: NDArray[np.floating],
    leaf_area_index: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    substrate_surface_drag_coefficient: float,
    roughness_element_drag_coefficient: float,
    roughness_sublayer_depth_parameter: float,
    max_ratio_wind_to_friction_velocity: float,
    min_roughness_length: float,
    von_karman_constant: float,
) -> NDArray[np.floating]:
    """Calculate roughness length governing momentum transfer, [m].

    Roughness length is defined as the height at which the mean velocity is zero due to
    substrate roughness. Real surfaces such as the ground or vegetation are not smooth
    and often have varying degrees of roughness. Roughness length accounts for that
    effect. Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: Canopy height, [m]
        leaf_area_index: Total leaf area index, [m m-1]
        zero_plane_displacement: Height above the actual ground where the wind speed is
            theoretically reduced to zero due to the obstruction caused by the roughness
            elements (like trees or buildings), [m]
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
    reference_wind_speed: NDArray[np.floating],
    reference_height: float | NDArray[np.floating],
    wind_heights: NDArray[np.floating],
    roughness_length: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    min_wind_speed: float,
) -> NDArray[np.floating]:
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
        zero_plane_displacement: Height above the actual ground where the wind speed is
            theoretically reduced to zero due to the obstruction caused by the roughness
            elements (like trees or buildings), [m]
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
    reference_wind_speed: NDArray[np.floating],
    reference_height: NDArray[np.floating],
    roughness_length: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    von_karman_constant: float,
) -> NDArray[np.floating]:
    r"""Calculate friction velocity, [m s-1].

    Friction velocity is a measure of the shear stress exerted by the wind on the
    Earth's surface, representing the velocity scale that relates to turbulent energy
    transfer near the surface.

    The friction velocity (:math:`u_{*}`, [m s-1]) is calculated as

    :math:`u_{*} = \frac{\kappa u}{\ln{(\frac{z - d}{z_0})}}`

    Where :math:`\kappa` is the von Kármán constant, :math:`u` is the reference wind
    speed, :math:`z` is the reference height, :math:`d` is the zero plane displacement
    height, and :math:`z_{0}` is the roughness length.

    Args:
        reference_wind_speed: Reference wind speed above the canopy [m s-1].
        reference_height: Reference height above the canopy, [m].
        roughness_length: Momentum roughness length, [m]
        zero_plane_displacement: Height above the actual ground where the wind speed is
            theoretically reduced to zero due to the obstruction caused by the roughness
            elements (like trees or buildings), [m]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        Friction velocity, [m s-1].
    """

    return (von_karman_constant * reference_wind_speed) / np.log(
        (reference_height - zero_plane_displacement) / roughness_length
    )


def calculate_ventilation_rate(
    aerodynamic_resistance: float | NDArray[np.floating],
    characteristic_height: float | NDArray[np.floating],
) -> float | NDArray[np.floating]:
    """Calculate ventilation rate from the top of the canopy to atmosphere above.

    This function calculates the rate of water and heat exchange between the top of the
    canopy and the atmosphere above.

    Args:
        aerodynamic_resistance: Aerodynamic resistance, [s m-1]
        characteristic_height: Vertical scale of exchange, [m]

    Returns:
        Ventilation rate [s-1]
    """

    denominator = np.maximum(aerodynamic_resistance * characteristic_height, 1e-3)
    return 1.0 / denominator


def calculate_mixing_coefficients_canopy(
    layer_midpoints: NDArray[np.floating],
    canopy_height: NDArray[np.floating],
    friction_velocity: NDArray[np.floating],
    von_karman_constant: float,
) -> NDArray[np.floating]:
    r"""Calculate turbulent mixing coefficients within canopy.

    This function calculates turbulent mixing coefficients for heat (:math:`k_H`) and
    momentum (:math:`k_M`) that are used to mix water and energy in the canopy. Inside
    the canopy, turbulence is strongly damped by vegetation drag, and a simple linear
    profile like used for the top of the canopy like
    :math:`k_{H,M} = \kappa u_{*}(z-d)` :cite:p:`raupach_coherent_1996`
    does not match observed eddy diffusivity well. Instead, empirical profiles based on
    measurements are used, and these often take parabolic or other non-linear forms like
    :

    .. math::

        k_{H,M}(z)=\kappa u_{*}z(1-z h_c)^{2}

    where :math:`\kappa` is the von Karman constant (dimensionless), :math:`u_{*}` is
    the friction velocity (m s-1), :math:`z` is the height (m) for which coefficients
    are calculated, and :math:`h_c` is the canopy height (m).

    This particular form goes to zero at both z=0 and z=h and peaks somewhere within the
    canopy.

    Args:
        layer_midpoints: The midpoints of all air layers, [m]
        canopy_height: Canopy height, [m]
        friction_velocity: Friction velocity, [m s-1]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        turbulent mixing coefficients, [m2 s-1]
    """
    heights = np.clip(layer_midpoints, 1e-3, canopy_height - 1e-3)  # avoid zero/edge
    mixing_coefficients = (
        von_karman_constant
        * friction_velocity
        * heights
        * (1 - heights / canopy_height) ** 2
    )
    return mixing_coefficients


def mix_and_ventilate(
    input_variable: NDArray[np.floating],
    layer_thickness: NDArray[np.floating],
    mixing_coefficient: NDArray[np.floating],
    ventilation_rate: float | NDArray[np.floating],
    time_interval: float,
) -> NDArray[np.floating]:
    """Mix and ventilate vertically.

    This function takes an atmospheric variable such as temperature or specific
    humidity, mixed vertically between layers and ventilates at the top of the canopy.

    Args:
        input_variable: Input variable for all true atmospheric layers
        layer_thickness: Layer thickness, [m]
        mixing_coefficient: Turbulent mixing coefficients for canopy, [m2 s-1]
        ventilation_rate: Ventilation rate, [s-1]
        time_interval: Time interval, [s]

    Returns:
        Vertically mixed input variable
    """

    input_variable_mixed = input_variable.copy()
    for i in range(2, len(input_variable) - 1):
        flux_up = (
            mixing_coefficient[i - 1]
            * (input_variable[i - 1] - input_variable[i])
            / layer_thickness[i]
        )
        flux_down = (
            mixing_coefficient[i + 1]
            * (input_variable[i + 1] - input_variable[i])
            / layer_thickness[i]
        )
        change_input_variable = (
            (flux_up + flux_down) * time_interval / layer_thickness[i]
        )
        input_variable_mixed[i] += change_input_variable

    # Ventilation at top
    input_variable_mixed[0] += (
        ventilation_rate * (input_variable[0] - input_variable[1]) * time_interval
    )

    return input_variable_mixed


def advect_water_from_toplayer(
    specific_humidity: NDArray[np.floating],
    layer_thickness: NDArray[np.floating],
    density_air: NDArray[np.floating],
    wind_speed: NDArray[np.floating],
    characteristic_length: float,
    time_interval: float,
) -> NDArray[np.floating]:
    """Remove water by advection from above canopy layer.

    Args:
        specific_humidity: Specific humidity in each layer, [kg kg-1]
        layer_thickness: Thickness of each layer, [m]
        density_air: Air density in each layer, [kg m-3]
        wind_speed: Horizontal wind speed above canopy, [m s-1]
        characteristic_length: Horizontal length scale of the grid cell, [m]
        time_interval: Time step, [s]

    Returns:
        Updated specific humidity array after advection from the top layer.
    """

    # Copy to avoid in-place mutation
    specific_humidity_updated = specific_humidity.copy()

    # Air mass in the layer [kg/m²]
    air_mass = density_air * layer_thickness

    # Water mass in the layer [kg/m²]
    water_mass = specific_humidity * air_mass

    # Compute loss due to advection
    advection_rate = wind_speed / characteristic_length
    advected_fraction = np.clip(advection_rate * time_interval, 0, 1)
    water_mass -= water_mass * advected_fraction

    # Update specific humidity
    specific_humidity_updated = water_mass / air_mass

    return specific_humidity_updated


def calculate_aerodynamic_resistance(
    wind_heights: NDArray[np.floating],
    roughness_length: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    wind_speed: NDArray[np.floating],
    von_karman_constant: float,
) -> NDArray[np.floating]:
    r"""Calculate aerodynamic resistance in canopy, [s m-1].

    The aerodynamic resistance :math:`r_{a}` is calculated as:

    .. math::
        r_{a} = \frac{ln(\frac{z-d}{z_{m}})^{2}}{\kappa ^{2} u(z)}

    where :math:`z` is the height where the aerodynamic resistance needs to be
    calculated, :math:`d` is the zero plane displacement height, :math:`z_{m}` is the
    roughness length of momentum, :math:`\kappa` is the von Karman constant, and
    :math:`u(z)` is the wind speed at height :math:`z`.

    Args:
        wind_heights: Heights where wind speed is to be calculated [m].
        roughness_length: Momentum roughness length, [m]
        zero_plane_displacement: Height above the actual ground where the wind speed is
            theoretically reduced to zero due to the obstruction caused by the roughness
            elements (like trees or buildings), [m]
        wind_speed: Wind speed, [m s-1]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        aerodynamic resistance in canopy, [s m-1]
    """

    # Compute only where valid
    valid_condition = wind_heights > zero_plane_displacement
    aero_resistance = np.where(
        valid_condition,
        (np.log((wind_heights - zero_plane_displacement) / roughness_length)) ** 2
        / (von_karman_constant**2 * wind_speed),
        np.nan,
    )

    # Replace invalid values with a small fallback resistance
    aero_resistance_out = np.where(np.isnan(aero_resistance), 0.001, aero_resistance)
    return np.where(np.isnan(wind_heights), np.nan, aero_resistance_out)
