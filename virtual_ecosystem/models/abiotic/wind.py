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
    """Calculate zero plane displacement height.

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
        1 - (1 - np.exp(-scale_displacement)) / scale_displacement
    ) * canopy_height

    # No displacement in absence of vegetation
    return np.nan_to_num(zero_plane_displacement, nan=0.0)


def calculate_roughness_length_momentum(
    canopy_height: NDArray[np.floating],
    leaf_area_index: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    substrate_surface_roughness_length: float,
    roughness_element_drag_coefficient: float,
    roughness_sublayer_depth_parameter: float,
    max_ratio_wind_to_friction_velocity: float,
    min_roughness_length: float,
    von_karman_constant: float,
) -> NDArray[np.floating]:
    """Calculate roughness length governing momentum transfer.

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
        substrate_surface_roughness_length: Substrate-surface roughness length is the
            baseline roughness of the ground itself before adding vegetation, [m]
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
        substrate_surface_roughness_length
        + (roughness_element_drag_coefficient * leaf_area_index) / 2
    )

    # Set wind to friction velocity ratio
    ratio_wind_to_friction_velocity = np.minimum(
        ratio_wind_to_friction_velocity, max_ratio_wind_to_friction_velocity
    )

    # Calculate initial roughness length
    initial_roughness_length = (canopy_height - zero_plane_displacement) * np.exp(
        -von_karman_constant * (1 / ratio_wind_to_friction_velocity)
        - roughness_sublayer_depth_parameter
    )

    # If roughness smaller than the substrate surface drag coefficient, set to value to
    # the substrate surface drag coefficient
    roughness_length = np.maximum(
        initial_roughness_length, substrate_surface_roughness_length
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
    r"""Calculate wind speed profile.

    The wind speed at different heights is calculated using the following equation
    (based on :cite:t:`holmes_wind_2019`):

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
    r"""Calculate friction velocity.

    Friction velocity is a measure of the shear stress exerted by the wind on the
    Earth's surface, representing the velocity scale that relates to turbulent energy
    transfer near the surface.

    The friction velocity (:math:`u_{*}`, [m s-1]) is calculated as (based on
    :cite:t:`holmes_wind_2019`):

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
) -> NDArray[np.floating]:
    """Calculate ventilation rate from the top of the canopy to atmosphere above.

    This function calculates the rate of water and heat exchange between the top of the
    canopy and the atmosphere above after :cite:t:`wolfe_forest_2011`.

    Args:
        aerodynamic_resistance: Aerodynamic resistance, [s m-1]
        characteristic_height: Vertical scale of exchange, typically canopy height +
            zero plane displacement height [m]

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

        k_{H,M}(z)=\kappa u_{*}z(\frac{1-z}{h_c})^{2}

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


def clamp_variable_within_limits(
    variable: NDArray[np.floating], limits: tuple[float, float]
) -> NDArray[np.floating]:
    """Clamp an array of canopy data within limits.

    This function iterates from the bottom of the canopy, clamping the values of the
    input array within the limits. When a value is altered by clamping, the residual is
    added to the layer above to maintain the variable total within cells. Residual
    values may be redistributed across multiple layers and empty values (representing
    unoccupied canopy layers) are skipped.

    Note:
        If the vertical layers cannot absorb all of the accumulated residuals without
        themselves being clamped, then the values in the top layer can still fall
        outside the clamping limits.

    Args:
        variable: A numpy array containing canopy data.
        limits: A tuple giving the upper and lower bounds within which to clamp the data
    """

    # Get a map of nan values and initialise the out_of_limits array
    out_of_limits = np.zeros_like(variable[0])
    nan_map = np.isnan(variable)
    n_layers = variable.shape[0]

    # Loop up from the row index of lowest layer, stopping before the top layer
    for layer in np.arange(n_layers - 1, 0, -1):
        # Calculate the clamped values for the current layer
        in_limits = np.clip(variable[layer], *limits)

        # Add under and overshoots to the out_of_limits array, trapping cells that
        # contain no vegetation in the layer (np.nan)
        out_of_limits += np.where(nan_map[layer], 0, variable[layer] - in_limits)

        # Set the clamped data in the current layer
        variable[layer] = in_limits

        # Add out of limits to the layer above
        variable[layer - 1] += out_of_limits
        # Update out_of_limits
        # - np.nan cells carry over the current out_of_limits total
        # - otherwise the out_of_limits has been set into the layer above, so is zeroed
        out_of_limits = np.where(nan_map[layer - 1], out_of_limits, 0)

    return variable


def mix_and_ventilate(
    input_variable: NDArray[np.floating],
    layer_thickness: NDArray[np.floating],
    mixing_coefficient: NDArray[np.floating],
    ventilation_rate: NDArray[np.floating],
    limits: tuple[float, float],
    time_interval: float,
) -> NDArray[np.floating]:
    """Apply vertical mixing and top-layer ventilation across multiple vertical layers.

    This function simulates diffusion-like mixing between vertical layers based on local
    gradients of atmospheric variables (e.g. temperature, relative humidity) and
    layer-specific mixing coefficients. For each internal layer (excluding the top and
    bottom), it computes upward and downward fluxes using the nearest valid
    (finite) values above and below, respectively. The fluxes are scaled by the layer
    thickness and applied to update the variable.

    Additionally, the function applies a ventilation adjustment to the top layer of each
    column, representing heat or water exchange with the  above the canopy. This is
    based on the difference between the top and next valid layer, scaled by a
    user-provided ventilation rate, with optional limits to prevent overcorrection or
    negative concentrations.

    Advection is currently not implemented as everything is removed with time interval
    > 1h and horizontal transfer is not implemented.

    Args:
        input_variable: Input variable for all true atmospheric layers
        layer_thickness: Layer thickness, [m]
        mixing_coefficient: Turbulent mixing coefficients for canopy, [m2 s-1]
        ventilation_rate: Ventilation rate, [s-1]
        limits: Upper and lower limit for input variable, avoid overshoot when mixing
        time_interval: Time interval, [s]

    Returns:
        Vertically mixed input variable
    """

    # Copy the input to update with mixing
    input_variable_mixed = input_variable.copy()

    # Extract the layer thickness and current value for the canopy layers, excluding the
    # surface layer and above canopy values
    value_canopy = input_variable[1:-1]
    canopy_layer_thickness = layer_thickness[1:-1]

    # Get the value and mixing coefficients from the layer above.
    value_above = input_variable[0:-2]
    mix_above = mixing_coefficient[0:-2]

    # Get the value and mixing coefficients from the layer above.
    value_below = input_variable[2:]
    mix_below = mixing_coefficient[2:]

    # In-fill missing below values from the surface layer
    value_below = np.where(np.isnan(value_below), input_variable[-1], value_below)
    mix_below = np.where(np.isnan(mix_below), mix_below[-1], mix_below)

    # Calculate fluxes (positive upward, negative downward) and update variable
    flux_up = mix_above * (value_above - value_canopy) / canopy_layer_thickness
    flux_down = mix_below * (value_below - value_canopy) / canopy_layer_thickness

    value_change = (flux_up + flux_down) * time_interval / canopy_layer_thickness
    input_variable_mixed[1:-1] += value_change

    # Calculate ventilation using the value from the highest layer, which is either the
    # top canopy layer or the surface layer if no canopy is present
    vent_below = np.where(
        np.isnan(input_variable_mixed[1]),
        input_variable_mixed[-1],
        input_variable_mixed[1],
    )

    # Get the ventilation delta and change over time
    delta_vent = input_variable_mixed[0] - vent_below
    vent_change = ventilation_rate * delta_vent * time_interval

    # Clip the maximum ventilation rate to 10%
    vent_max_change = 0.1 * abs(input_variable[0])
    vent_change = np.clip(vent_change, -vent_max_change, vent_max_change)

    # Update the current values
    input_variable_mixed[0] += vent_change
    input_variable_mixed[1] -= vent_change

    # Redistribute overshoot/undershoot
    input_variable_mixed = clamp_variable_within_limits(
        variable=input_variable_mixed, limits=limits
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
        specific_humidity: Specific humidity in top layer, [kg kg-1]
        layer_thickness: Thickness of top layer, [m]
        density_air: Air density in top layer, [kg m-3]
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
    r"""Calculate aerodynamic resistance in canopy.

    The aerodynamic resistance :math:`r_{a}` is calculated as (based on
    :cite:t:`jansson_coupled_2004`):

    .. math::
        r_{a} = \frac{ln(\frac{z-d}{z_{m}})^{2}}{\kappa ^{2} u(z)}

    where :math:`z` is the height where the aerodynamic resistance needs to be
    calculated, :math:`d` is the zero plane displacement height, :math:`z_{m}` is the
    roughness length of momentum, :math:`\kappa` is the von Karman constant, and
    :math:`u(z)` is the wind speed at height :math:`z`.

    Args:
        wind_heights: Heights where wind speed is to be calculated, [m].
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
