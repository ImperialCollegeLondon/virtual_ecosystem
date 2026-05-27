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
    denominator_tolerance: float,
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
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        Zero plane displacement height, [m]
    """

    # Only compute where LAI > 0 — zero or negative LAI means no canopy
    has_canopy = leaf_area_index > 0

    displacement = np.where(has_canopy, leaf_area_index, np.nan)
    scale_displacement = np.sqrt(
        np.maximum(zero_plane_scaling_parameter * displacement, 0.0)
    )

    # Avoid division by zero in (1 - exp(-s)) / s when s approaches 0
    safe_scale = np.where(
        scale_displacement > denominator_tolerance, scale_displacement, np.nan
    )

    zero_plane_displacement = (
        1.0 - (1.0 - np.exp(-safe_scale)) / safe_scale
    ) * canopy_height

    # No canopy means zero displacement, no NaN in output
    return np.where(has_canopy, np.nan_to_num(zero_plane_displacement, nan=0.0), 0.0)


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
    denominator_tolerance: float,
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
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        Momentum roughness length, [m]
    """

    has_canopy = leaf_area_index > 0

    # Calculate ratio of wind velocity to friction velocity
    # Safe sqrt — argument is always >= substrate_surface_roughness_length > 0
    ratio_wind_to_friction_velocity = np.sqrt(
        np.maximum(
            substrate_surface_roughness_length
            + (roughness_element_drag_coefficient * leaf_area_index) / 2,
            denominator_tolerance,
        )
    )

    # Set wind to friction velocity ratio
    ratio_wind_to_friction_velocity = np.minimum(
        ratio_wind_to_friction_velocity, max_ratio_wind_to_friction_velocity
    )

    # Safe division — ratio is always positive after the sqrt above
    safe_ratio = np.maximum(ratio_wind_to_friction_velocity, denominator_tolerance)

    # Safe log — height above displacement must be positive
    height_above_displacement = np.maximum(
        canopy_height - zero_plane_displacement, denominator_tolerance
    )

    # Calculate initial roughness length
    initial_roughness_length = height_above_displacement * np.exp(
        -von_karman_constant / safe_ratio - roughness_sublayer_depth_parameter
    )

    # If roughness smaller than the substrate surface drag coefficient, set to value to
    # the substrate surface drag coefficient
    roughness_length = np.maximum(
        initial_roughness_length, substrate_surface_roughness_length
    )

    # If roughness length in nan, zero or below zero, set to minimum value

    roughness_length = np.where(has_canopy, roughness_length, min_roughness_length)

    # Final safety: replace any NaN, zero, or negative with min_roughness_length
    roughness_length = np.where(
        np.isfinite(roughness_length) & (roughness_length > 0),
        roughness_length,
        min_roughness_length,
    )

    return np.where(
        roughness_length < min_roughness_length,
        min_roughness_length,
        roughness_length,
    )


def calculate_wind_profile(
    reference_wind_speed: NDArray[np.floating],
    reference_height: float | NDArray[np.floating],
    wind_heights: NDArray[np.floating],
    roughness_length: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    min_wind_speed: float,
    denominator_tolerance: float,
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
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        Wind speed, [m s-1]
    """

    # Guard against heights at or below roughness length or displacement
    # Both conditions must hold simultaneously — take the maximum of both floors
    height_floor = np.maximum(
        roughness_length + zero_plane_displacement + denominator_tolerance,
        zero_plane_displacement + roughness_length + denominator_tolerance,
    )
    heights = np.maximum(wind_heights, height_floor)

    # Safe log arguments — both must be strictly positive
    numerator = np.maximum(heights - zero_plane_displacement, denominator_tolerance)
    denominator_log = np.maximum(
        (reference_height - zero_plane_displacement) / roughness_length,
        denominator_tolerance,
    )

    wind_speed = (
        reference_wind_speed
        * np.log(numerator / roughness_length)
        / np.log(denominator_log)
    )

    clipped_wind_speed = np.maximum(wind_speed, min_wind_speed)

    # Preserve NaN for layers that do not exist
    return np.where(np.isnan(wind_heights), np.nan, clipped_wind_speed)


def calculate_friction_velocity(
    reference_wind_speed: NDArray[np.floating],
    reference_height: NDArray[np.floating],
    roughness_length: NDArray[np.floating],
    zero_plane_displacement: NDArray[np.floating],
    von_karman_constant: float,
    denominator_tolerance: float,
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
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        Friction velocity, [m s-1].
    """

    # Safe log argument — reference height must be above displacement + roughness
    safe_arg = np.maximum(
        (reference_height - zero_plane_displacement) / roughness_length,
        denominator_tolerance,
    )

    return (von_karman_constant * reference_wind_speed) / np.log(safe_arg)


def calculate_ventilation_rate(
    aerodynamic_resistance: float | NDArray[np.floating],
    characteristic_height: float | NDArray[np.floating],
    understorey_ventilation_rate: float,
    surface_layer_height: float,
    denominator_tolerance: float,
) -> NDArray[np.floating]:
    """Calculate ventilation rate from the top of the canopy to atmosphere above.

    This function calculates the rate of water and heat exchange between the top of the
    canopy and the atmosphere above after :cite:t:`wolfe_forest_2011`.

    If the canopy height is zero, the value is set to a default value for understorey
    ventilation.

    Args:
        aerodynamic_resistance: Aerodynamic resistance, [s m-1]
        characteristic_height: Vertical scale of exchange, typically canopy height +
            zero plane displacement height [m]
        understorey_ventilation_rate: Understorey ventilation rate, [s-1]. This is used
            in case there is no canopy.
        surface_layer_height: Height of the surface layer, [m]
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        Ventilation rate [s-1]
    """

    # Use a threshold rather than exact zero to catch near-zero canopy heights
    no_canopy = np.asarray(characteristic_height) < surface_layer_height

    denominator = np.maximum(
        aerodynamic_resistance * characteristic_height, denominator_tolerance
    )
    ventilation_rate = 1.0 / denominator

    return np.where(no_canopy, understorey_ventilation_rate, ventilation_rate)


def calculate_mixing_coefficients_canopy(
    layer_midpoints: NDArray[np.floating],
    canopy_height: NDArray[np.floating],
    friction_velocity: NDArray[np.floating],
    von_karman_constant: float,
    max_mixing_coefficient: float,
    denominator_tolerance: float,
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
        max_mixing_coefficient: Maximum mixing coefficient
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        turbulent mixing coefficients, [m2 s-1]
    """

    # Replace NaN midpoints with zero — NaN layers get zero mixing coefficient
    safe_midpoints = np.nan_to_num(layer_midpoints, nan=0.0)

    # Normalised height — clamp to [0, 1], zero where no canopy
    z_over_h = np.where(
        canopy_height > 0,
        np.clip(
            safe_midpoints / np.maximum(canopy_height, denominator_tolerance), 0.0, 1.0
        ),
        0.0,
    )

    mixing_coefficients = (
        von_karman_constant
        * np.maximum(friction_velocity, 0.0)  # friction velocity must be non-negative
        * safe_midpoints
        * (1.0 - z_over_h) ** 2
    )

    # Non-negative and capped
    mixing_coefficients = np.clip(mixing_coefficients, 0.0, max_mixing_coefficient)

    # Restore NaN for layers that do not exist
    return np.where(np.isnan(layer_midpoints), np.nan, mixing_coefficients)


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


def next_valid_above(array: NDArray[np.floating]) -> NDArray[np.int_]:
    """Index of nearest valid value above each layer.

    Args:
        array: A 2D array with vertical layers as the first dimension and columns as
            the second dimension. NaN values represent invalid or unoccupied layers.

    Returns:
        A 2D array of the same shape as the input, where each element contains the index
        of the nearest valid (non-NaN) value above it in the same column. If there is no
        valid value above, the element will be -1.
    """

    n_layers, n_cols = array.shape

    out = np.empty((n_layers, n_cols), dtype=int)
    last_valid = np.full(n_cols, -1, dtype=int)

    for i in range(n_layers):
        out[i] = last_valid
        last_valid[~np.isnan(array[i])] = i

    return out


def next_valid_below(array: NDArray[np.floating]) -> NDArray[np.int_]:
    """Index of nearest valid value below each layer.

    Args:
        array: A 2D array with vertical layers as the first dimension and columns as
            the second dimension. NaN values represent invalid or unoccupied layers.

    Returns:
        A 2D array of the same shape as the input, where each element contains the index
        of the nearest valid (non-NaN) value below it in the same column. If there is no
        valid value below, the element will be -1.
    """

    n_layers, n_cols = array.shape

    out = np.empty((n_layers, n_cols), dtype=int)
    last_valid = np.full(n_cols, -1, dtype=int)

    for i in range(n_layers - 1, -1, -1):
        out[i] = last_valid
        last_valid[~np.isnan(array[i])] = i

    return out


def mix_and_ventilate(
    input_variable: NDArray[np.floating],
    mixing_coefficient: NDArray[np.floating],
    ventilation_rate: NDArray[np.floating],
    limits: tuple[float, float],
    surface_index: int,
) -> NDArray[np.floating]:
    """Apply vertical mixing and top-layer ventilation across multiple vertical layers.

    This function simulates diffusion-like mixing between vertical layers based on local
    gradients of atmospheric variables (e.g. temperature, relative humidity) and
    layer-specific mixing coefficients. For each layer, it computes upward and
    downward fluxes using the nearest valid (finite) values above.

    Additionally, the function applies a ventilation adjustment to the top layer of each
    column, representing heat or water exchange with the  above the canopy. This is
    based on the difference between the top and next valid layer, scaled by a
    user-provided ventilation rate, with optional limits to prevent overcorrection or
    negative concentrations.

    Advection is currently not implemented as everything is removed with time interval
    > 1h and horizontal transfer is not implemented.

    Args:
        input_variable: Input variable for all true atmospheric layers
        mixing_coefficient: Turbulent mixing coefficients for canopy, [m2 s-1]
        ventilation_rate: Ventilation rate, [s-1]
        limits: Upper and lower limit for input variable, avoid overshoot when mixing
        surface_index: Surface layer index

    Returns:
        Vertically mixed input variable
    """

    current = input_variable.copy()
    n_layers, n_cols = current.shape

    # Copy to avoid in-place mutation
    k = mixing_coefficient.copy()

    above_idx = next_valid_above(current)
    cols = np.broadcast_to(np.arange(n_cols), (n_layers, n_cols))

    mix_flux = np.zeros_like(current)

    # Canopy mixing: rows 1 to n_layers-1
    # Row 0 is the above-canopy reference and is handled by ventilation below
    for layer in range(1, n_layers):
        a_idx = above_idx[layer]

        valid = (a_idx >= 0) & np.isfinite(current[layer])

        if not np.any(valid):
            continue

        src_layers = np.where(valid, a_idx, 0)
        above_vals = current[src_layers, cols[layer]]

        valid = valid & np.isfinite(above_vals)
        if not np.any(valid):
            continue

        flux = np.where(
            valid,
            k[layer] * (above_vals - current[layer]),
            0.0,
        )

        mix_flux[layer] += flux

        # Vectorised equal-and-opposite on donor layer
        # Scatter flux back to source rows using np.add.at for safety
        np.add.at(mix_flux, (src_layers, np.arange(n_cols)), -flux * valid)

    # Ventilation: exchange between row 0 and first valid canopy layer
    # For cells with canopy: mix top canopy layer toward above-canopy reference
    # For cells without canopy: mix surface layer toward above-canopy reference
    canopy_exists = np.isfinite(current[1, :])

    # Use ventilation rate to exchange row 0 with first canopy layer
    with_canopy = canopy_exists & np.isfinite(current[0, :])
    if np.any(with_canopy):
        # Find the topmost canopy layer for each cell
        top_canopy_idx = np.full(n_cols, -1, dtype=int)
        for layer in range(1, surface_index):
            valid_here = np.isfinite(current[layer, :]) & (top_canopy_idx == -1)
            top_canopy_idx = np.where(valid_here, layer, top_canopy_idx)

        for col in np.where(with_canopy)[0]:
            tc = top_canopy_idx[col]
            if tc < 0:
                continue
            v = ventilation_rate[col]
            diff = current[0, col] - current[tc, col]
            mix_flux[0, col] -= v * diff
            mix_flux[tc, col] += v * diff

    # Cells without canopy — direct exchange between row 0 and surface
    no_canopy = (
        ~canopy_exists
        & np.isfinite(current[0, :])
        & np.isfinite(current[surface_index, :])
    )
    if np.any(no_canopy):
        diff = current[0, no_canopy] - current[surface_index, no_canopy]
        v = ventilation_rate[no_canopy]
        mix_flux[0, no_canopy] -= v * diff
        mix_flux[surface_index, no_canopy] += v * diff

    result = current + mix_flux

    return clamp_variable_within_limits(result, limits)


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
    fallback_resistance: float,
    denominator_tolerance: float,
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
        fallback_resistance: Fallback aerodynamic resistance value, [s m-1]
        denominator_tolerance: Minimum value for denominator to avoid division by zero

    Returns:
        aerodynamic resistance in canopy, [s m-1]
    """

    # Compute only where valid
    valid_condition = wind_heights > (zero_plane_displacement + roughness_length)

    # Safe log and division
    safe_wind = np.maximum(wind_speed, denominator_tolerance)
    safe_arg = np.maximum(
        (wind_heights - zero_plane_displacement) / roughness_length,
        denominator_tolerance,
    )

    aero_resistance = np.where(
        valid_condition,
        np.log(safe_arg) ** 2 / (von_karman_constant**2 * safe_wind),
        fallback_resistance,
    )

    return np.where(np.isnan(wind_heights), np.nan, aero_resistance)


def calculate_aerodynamic_resistance_understorey(
    wind_speed_understorey: NDArray[np.floating],
    coefficient_aerodynamic_resistance_understorey: float,
    min_wind_speed: float,
) -> NDArray[np.floating]:
    """Calculate aerodynamic resistance in understorey.

    The aerodynamic resistance below the canopy is calculated using an empirical
    coefficient multiplied by the inverse of the wind speed within the understorey
    following :cite:t:`ogee_a_forest_2002`

    Args:
        wind_speed_understorey: Wind speed below the canopy, [m s-1]
        coefficient_aerodynamic_resistance_understorey: Empirical coefficient for
            calculating aerodynamic resistance below the canopy, [s m-2]
        min_wind_speed: Minimum wind speed to avoid division by zero, [m s-1]

    Returns:
        Aerodynamic resistance below the canopy, [s m-1]
    """

    # Avoid division by zero by setting a minimum wind speed
    wind_speed_clipped = np.maximum(wind_speed_understorey, min_wind_speed)

    aerodynamic_resistance_understorey = (
        coefficient_aerodynamic_resistance_understorey / wind_speed_clipped
    )

    return aerodynamic_resistance_understorey
