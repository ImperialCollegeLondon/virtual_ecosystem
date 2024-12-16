r"""The ``models.abiotic_simple.microclimate`` module uses linear regressions from
:cite:t:`hardwick_relationship_2015` and :cite:t:`jucker_canopy_2018` to predict
atmospheric temperature, relative humidity, and vapour pressure deficit at ground level
(1.5 m) given the above canopy conditions and leaf area index of intervening canopy. A
within canopy profile is then interpolated using a logarithmic curve between the above
canopy observation and ground level prediction.
Soil temperature is interpolated between the surface layer and the soil temperature at
1 m depth which equals the mean annual temperature.
The module also provides a constant vertical profile of atmospheric pressure and
:math:`\ce{CO2}`.

TODO change temperatures to Kelvin
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)


def run_microclimate(
    data: Data,
    layer_structure: LayerStructure,
    time_index: int,  # could be datetime?
    constants: AbioticSimpleConsts,
    bounds: AbioticSimpleBounds,
) -> dict[str, DataArray]:
    r"""Calculate simple microclimate.

    This function uses empirical relationships between leaf area index (LAI) and
    atmospheric temperature, relative humidity, and vapour pressure deficit to derive
    logarithmic profiles of these variables from external climate data such as
    regional climate models or satellite observations. Note that these sources provide
    data at different heights and with different underlying assumptions which lead to
    different biases in the model output. For below canopy values (1.5 m),
    the implementation is based on :cite:t:`hardwick_relationship_2015` as

    :math:`y = m * LAI + c`

    where :math:`y` is the variable of interest, :math:`m` is the gradient
    (:data:`~virtual_ecosystem.models.abiotic_simple.constants.AbioticSimpleConsts`)
    and :math:`c` is the intersect which we set to the external data values. We assume
    that the gradient remains constant.

    The other atmospheric layers are calculated by logarithmic regression and
    interpolation between the input at the top of the canopy and the 1.5 m values.
    Soil temperature is interpolated between the surface layer and the temperature at
    1 m depth which which approximately equals the mean annual temperature, i.e. can
    assumed to be constant over the year.

    The function also broadcasts the reference values for atmospheric pressure and
    :math:`\ce{CO2}` to all atmospheric levels as they are currently assumed to remain
    constant during one time step.

    Th function calculates the wind speed at each layer within the canopy by applying
    the logarithmic wind profile equation, considering a reference wind speed at a
    specified height above the canopy.

    The `layer_roles` list is composed of the following layers (index 0 above canopy):

    * above canopy (canopy height + 2 m)
    * canopy layers
    * surface layer
    * soil layers

    The function expects a data object with the following variables:

    * air_temperature_ref [C]
    * relative_humidity_ref []
    * vapour_pressure_deficit_ref [kPa]
    * atmospheric_pressure_ref [kPa]
    * atmospheric_co2_ref [ppm]
    * wind_speed_ref [m s-1]
    * leaf_area_index [m m-1]
    * layer_heights [m]

    Args:
        data: Data object
        layer_structure: The LayerStructure instance for the simulation.
        time_index: Time index, integer
        constants: Set of constants for the abiotic simple model
        bounds: Upper and lower allowed values for vertical profiles, used to constrain
            log interpolation. Note that currently no conservation of water and energy!

    Returns:
        Dict of DataArrays for air temperature [C], relative humidity [-], vapour
        pressure deficit [kPa], soil temperature [C], atmospheric pressure [kPa],
        atmospheric :math:`\ce{CO2}` [ppm], wind speed [m s-1]
    """

    output = {}

    # Sum leaf area index over all canopy layers
    leaf_area_index_sum = data["leaf_area_index"].sum(dim="layers")

    # Interpolate atmospheric profiles
    for var in ["air_temperature", "relative_humidity", "vapour_pressure_deficit"]:
        lower, upper, gradient = getattr(bounds, var)

        output[var] = log_interpolation(
            reference_data=data[var + "_ref"].isel(time_index=time_index),
            leaf_area_index_sum=leaf_area_index_sum,
            layer_structure=layer_structure,
            layer_heights=data["layer_heights"],
            upper_bound=upper,
            lower_bound=lower,
            gradient=gradient,
        ).rename(var)

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

    # Calculate wind profile
    wind_speed = calculate_wind_profile(
        data=data,
        layer_structure=layer_structure,
        time_index=time_index,
        abiotic_simple_constants=constants,
        core_constants=CoreConsts(),
    )
    output["wind_speed"] = wind_speed

    # Calculate soil temperatures
    lower, upper = getattr(bounds, "soil_temperature")
    output["soil_temperature"] = interpolate_soil_temperature(
        layer_heights=data["layer_heights"],
        surface_temperature=output["air_temperature"].isel(
            layers=layer_structure.index_surface
        ),
        mean_annual_temperature=data["mean_annual_temperature"],
        layer_structure=layer_structure,
        upper_bound=upper,
        lower_bound=lower,
    )

    return output


def log_interpolation(
    reference_data: DataArray,
    leaf_area_index_sum: DataArray,
    layer_structure: LayerStructure,
    layer_heights: DataArray,
    upper_bound: float,
    lower_bound: float,
    gradient: float,
) -> DataArray:
    """LAI regression and logarithmic interpolation of variables above ground.

    Args:
        reference_data: Input variable at reference height
        leaf_area_index_sum: Leaf area index summed over all layers, [m m-1]
        layer_structure: The LayerStructure instance for the simulation.
        layer_heights: Vertical layer heights, [m]
        lower_bound: Minimum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        upper_bound: Maximum allowed value, used to constrain log interpolation.
        gradient: Gradient of regression from :cite:t:`hardwick_relationship_2015`

    Returns:
        vertical profile of provided variable
    """

    # Calculate microclimatic variable at 1.5 m as function of leaf area index
    lai_regression = DataArray(
        leaf_area_index_sum * gradient + reference_data, dims="cell_id"
    )

    # Calculate per cell slope and intercept for logarithmic within-canopy profile
    slope = (reference_data - lai_regression) / (
        np.log(layer_heights.isel(layers=0)) - np.log(1.5)
    )
    intercept = lai_regression - slope * np.log(1.5)

    # Calculate the values within cells by layer
    positive_layer_heights = np.where(layer_heights > 0, layer_heights, np.nan)
    layer_values = (
        np.log(positive_layer_heights) * slope.to_numpy() + intercept.to_numpy()
    )

    # set upper and lower bounds
    return_array = layer_structure.from_template()
    return_array[:] = np.clip(layer_values, lower_bound, upper_bound)

    return return_array


def calculate_saturation_vapour_pressure(
    temperature: DataArray,
    saturation_vapour_pressure_factors: list[float],
) -> DataArray:
    r"""Calculate saturation vapour pressure, kPa.

    Saturation vapour pressure :math:`e_{s} (T)` is here calculated as

    :math:`e_{s}(T) = 0.61078 exp(\frac{7.5 T}{T + 237.3})`

    where :math:`T` is temperature in degree C .

    Args:
        temperature: Air temperature, [C]
        saturation_vapour_pressure_factors: Factors in saturation vapour pressure
            calculation

    Returns:
        saturation vapour pressure, [kPa]
    """
    factor1, factor2, factor3 = saturation_vapour_pressure_factors
    return DataArray(
        factor1 * np.exp((factor2 * temperature) / (temperature + factor3))
    ).rename("saturation_vapour_pressure")


def calculate_vapour_pressure_deficit(
    temperature: DataArray,
    relative_humidity: DataArray,
    saturation_vapour_pressure_factors: list[float],
) -> dict[str, DataArray]:
    """Calculate vapour pressure and vapour pressure deficit, kPa.

    Vapor pressure deficit is defined as the difference between saturated vapour
    pressure and actual vapour pressure.

    Args:
        temperature: temperature, [C]
        relative_humidity: relative humidity, []
        saturation_vapour_pressure_factors: Factors in saturation vapour pressure
            calculation

    Return:
        vapour pressure, [kPa], vapour pressure deficit, [kPa]
    """

    output = {}
    saturation_vapour_pressure = calculate_saturation_vapour_pressure(
        temperature,
        saturation_vapour_pressure_factors=saturation_vapour_pressure_factors,
    )
    actual_vapour_pressure = saturation_vapour_pressure * (relative_humidity / 100)
    output["vapour_pressure"] = actual_vapour_pressure
    output["vapour_pressure_deficit"] = (
        saturation_vapour_pressure - actual_vapour_pressure
    )
    return output


def interpolate_soil_temperature(
    layer_heights: DataArray,
    surface_temperature: DataArray,
    mean_annual_temperature: DataArray,
    layer_structure: LayerStructure,
    upper_bound: float,
    lower_bound: float,
) -> DataArray:
    """Interpolate soil temperature using logarithmic function.

    Args:
        layer_heights: Vertical layer heights, [m]
        layer_roles: List of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        surface_temperature: Surface temperature, [C]
        mean_annual_temperature: Mean annual temperature, [C]
        layer_structure: The LayerStructure instance for the simulation.
        upper_bound: Maximum allowed value, used to constrain log interpolation. Note
            that currently no conservation of water and energy!
        lower_bound: Minimum allowed value, used to constrain log interpolation.

    Returns:
        soil temperature profile, [C]
    """

    # Select surface layer (atmosphere) and generate interpolation heights
    surface_layer = layer_heights[layer_structure.index_surface].to_numpy()
    soil_depths = layer_heights[layer_structure.index_all_soil].to_numpy()
    interpolation_heights = np.concatenate(
        [surface_layer, -1 * soil_depths + surface_layer]
    )

    # Calculate per cell slope and intercept for logarithmic soil temperature profile
    slope = (surface_temperature.to_numpy() - mean_annual_temperature.to_numpy()) / (
        np.log(interpolation_heights[0]) - np.log(interpolation_heights[-1])
    )
    intercept = surface_temperature.to_numpy() - slope * np.log(
        interpolation_heights[0]
    )

    # Calculate the values within cells by layer and clip by the bounds
    layer_values = np.clip(
        np.log(interpolation_heights) * slope + intercept, lower_bound, upper_bound
    )

    # return
    return_xarray = layer_structure.from_template()
    return_xarray[layer_structure.index_all_soil] = layer_values[1:]

    return return_xarray


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


def interpolate_windspeed(
    windspeed_reference_height: NDArray[np.float32],
    reference_height: NDArray[np.float32],
    layer_heights: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    roughness_length: NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Interpolates windspeed from reference height to vertical profile within canopy.

    This function calculates the wind speed at each layer within the canopy by applying
    the logarithmic wind profile equation, considering a reference wind speed at a
    specified height above the canopy. The equation assumes neutral stability conditions
    and accounts for the influence of the canopy structure through the zero-plane
    displacement and roughness length.

    The wind speed at a given height :math:`z` is calculated using the logarithmic wind
    profile:

    .. math::
        u(z) = u_{ref} \cdot
        \frac{\log((z - d) / z_0)}{
        \log((z_{ref} - d) / z_0)
        }

    where:

    - :math:`u(z)` is the wind speed at height `z` within the canopy, [m s-1].
    - :math:`u_{ref}` is the wind speed at the reference height `z_{ref}`, [m s-1].
    - :math:`z` is the height at which the wind speed is to be calculated, [m].
    - :math:`d` is the zero-plane displacement height, [m].
    - :math:`z_0` is the roughness length, [m].
    - :math:`z_{ref}` is the reference height above the canopy, [m].

    Args:
        windspeed_reference_height: The wind speed at the reference height
            `reference_height`, [m s-1]
        reference_height: The reference height above the canopy at which
            `windspeed_reference_height` is measured, [m]
        layer_heights: 2D array representing the heights of the canopy layers [m], with
            shape (m, n), where `m` represents the number of grid cells, and `n`
            represents the number of canopy layers
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length: The height at which the mean velocity is zero due to substrate
        roughness, [m]

    Returns:
        2D array of wind speed at each layer in the canopy, [m s-1]
    """
    # Calculate windspeed at each layer using the logarithmic wind profile
    wind_speed = windspeed_reference_height * np.log(
        ((layer_heights - zero_plane_displacement) / roughness_length)
        / np.log((reference_height - zero_plane_displacement) / roughness_length)
    )

    # Mask invalid values (e.g., heights below zero-plane displacement)
    wind_speed = np.where(layer_heights > zero_plane_displacement, wind_speed, 0)
    wind_speed = np.where(wind_speed < 0.0, 0.001, wind_speed)
    return wind_speed


def calculate_wind_profile(
    data: Data,
    time_index: int,
    layer_structure: LayerStructure,
    abiotic_simple_constants: AbioticSimpleConsts,
    core_constants: CoreConsts,
) -> DataArray:
    """Calculate vertical wind profile.

    TODO value near ground seems high, needs to be fixed

    Args:
        data: Data object
        time_index: Time index
        layer_structure: Layer structure
        abiotic_simple_constants: Set of constants for the abiotic simple model
        core_constants: Set of constants shared across all models

    Returns:
        vertical profile of wind speed, [m s-1]
    """

    # Calculate zero plane displacement height, [m]
    zero_plane_displacement = calculate_zero_plane_displacement(
        canopy_height=data["layer_heights"][1].to_numpy(),
        leaf_area_index=data["leaf_area_index"].to_numpy(),
        zero_plane_scaling_parameter=(
            abiotic_simple_constants.zero_plane_scaling_parameter
        ),
    )

    #  Calculate roughness length for momentum, [m]
    roughness_length = calculate_roughness_length_momentum(
        canopy_height=data["layer_heights"][1].to_numpy(),
        leaf_area_index=data["leaf_area_index"].to_numpy(),
        zero_plane_displacement=zero_plane_displacement,
        substrate_surface_drag_coefficient=(
            abiotic_simple_constants.substrate_surface_drag_coefficient
        ),
        roughness_element_drag_coefficient=(
            abiotic_simple_constants.roughness_element_drag_coefficient
        ),
        roughness_sublayer_depth_parameter=(
            abiotic_simple_constants.roughness_sublayer_depth_parameter
        ),
        max_ratio_wind_to_friction_velocity=(
            abiotic_simple_constants.max_ratio_wind_to_friction_velocity
        ),
        min_roughness_length=abiotic_simple_constants.min_roughness_length,
        von_karman_constant=core_constants.von_karmans_constant,
    )

    wind_profile = interpolate_windspeed(
        windspeed_reference_height=(
            data["wind_speed_ref"].isel(time_index=time_index).to_numpy()
        ),
        reference_height=(
            data["layer_heights"][1] + abiotic_simple_constants.wind_reference_height
        ).to_numpy(),
        layer_heights=data["layer_heights"].to_numpy(),
        zero_plane_displacement=zero_plane_displacement,
        roughness_length=roughness_length,
    )

    true_wind_profile = layer_structure.from_template()
    true_wind_profile[layer_structure.index_filled_atmosphere] = wind_profile[
        layer_structure.index_filled_atmosphere
    ]

    return true_wind_profile
