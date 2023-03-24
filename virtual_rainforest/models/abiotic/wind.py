r"""The ``models.abiotic.wind`` module calculates the above- and within-canopy wind
profiles for the Virtual Rainforest. These profiles will determine the exchange of heat,
water, and CO2 between soil and atmosphere below the canopy as well as the exchange with
the atmsophere above the canopy.

The wind profile above the canopy is described as follows
(based on :cite:p:`campbell_introduction_1998` as implemented in
:cite:t:`maclean_microclimc_2021`):

:math:`u_z = \frac{u^{*}}{0.4} ln \frac{z-d}{z_M} + \phi_M`

where :math:`u_z` is wind speed at height :math:`z` above the canopy, :math:`d` is the
height above ground within the canopy where the wind profile extrapolates to zero,
:math:`z_m` the roughness length for momentum, :math:`\phi_M` is a diabatic correction
for momentum and :math:`u^{*}` is the friction velocity, which gives the wind speed at
height :math:`d + z_m`.

The wind profile below canopy is derived as follows:

:math:`u_z = u_h exp(a(\frac{z}{h} - 1))`

where :math:`u_z` is wind speed at height :math:`z` within the canopy, :math:`u_h` is
wind speed at the top of the canopy at height :math:`h`, and :math:`a` is a wind
attenuation coefficient given by :math:`a = 2 l_m i_w`, where :math:`c_d` is a drag
coefficient that varies with leaf inclination and shape, :math:`i_w` is a coefficient
describing relative turbulence intensity and :math:`l_m` is the mean mixing length,
equivalent to the free space between the leaves and stems. For details, see
:cite:t:`maclean_microclimc_2021`.

TODO: add sanity checks, errors and logging
TODO: vertical axis, currently "heights" and "wind_heights" above canopy and
"canopy_layers" and "canopy_node_heights" below canopy, might make sense to calculate
wind heights as a function of canopy height to avoid it being below canopy
"""  # noqa: D205, D415

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.models.abiotic.abiotic_tools import (
    AbioticConstants,
    calc_molar_density_air,
    calc_specific_heat_air,
)


@dataclass
class WindConstants:
    """Wind constants class."""

    zero_plane_scaling_parameter: float = 7.5
    """Control parameter for scaling zero displacement/height
        :cite:p:`raupach_simplified_1994`."""
    substrate_surface_drag_coefficient: float = 0.003
    """Substrate-surface drag coefficient :cite:p:`maclean_microclimc_2021`."""
    roughness_element_drag_coefficient: float = 0.3
    """Roughness-element drag coefficient :cite:p:`maclean_microclimc_2021`."""
    roughness_sublayer_depth_parameter: float = 0.193
    """Parameter characterizes the roughness sublayer depth
        :cite:p:`maclean_microclimc_2021`."""
    max_ratio_wind_to_friction_velocity: float = 0.3
    """Maximum ratio of wind velocity to friction velocity
        :cite:p:`maclean_microclimc_2021`."""
    drag_coefficient: float = 0.2
    """Drag coefficient :cite:p:`maclean_microclimc_2021`."""
    relative_turbulence_intensity: float = 0.5
    """Relative turbulence intensity :cite:p:`maclean_microclimc_2021`."""
    diabatic_correction_factor_below: float = 1
    "Diabatic correction factor below canopy."
    mixing_length_factor: float = 0.32
    """Factor in calculation of mixing length :cite:p:`maclean_microclimc_2021`."""


def calculate_wind_profile(
    wind_heights: DataArray,
    canopy_node_heights: DataArray,
    data: Data,
    wind_const: WindConstants = WindConstants(),
    abiotic_const: AbioticConstants = AbioticConstants(),
) -> Tuple[DataArray, DataArray]:
    """Calculate wind profile above and below canopy.

    This function takes a :class:`~virtual_rainforest.core.data.Data` object as ``data``
    argument that contains the following variables:

    * friction velocity
    * 10m wind speed
    * 2m temperature
    * atmospheric pressure
    * canopy height
    * leaf area index
    * sensible heat flux at the top of the canopy

    The ``wind_const`` argument takes an instance of class
    :class:`~virtual_rainforest.models.abiotic.wind.WindConstants`, which
    provides a user modifiable set of required constants.

    The ``abiotic_const`` argument takes an instance of class
    :class:`~virtual_rainforest.models.abiotic.abiotic_tools.AbioticConstants`, which
    provides a set of universal constants that are used across the abiotic module.

    Args:
        wind_heights: vector of heights above canopy for which wind speed is calculated,
            [m]
        canopy_node_heights: height of canopy nodes, [m]; initialised by the
            :class:`~virtual_rainforest.models.abiotic.energy_balance.EnergyBalance`
            class.
        data: A Virtual Rainforest Data object.
        wind_const: A WindConstants instance.
        abiotic_const: An AbioticConstants instance.

    Returns:
        vertical wind profile above canopy, [m -1]
        vertical wind profile within canopy, [m -1]
    """

    # preparatory calculations for wind profiles
    zero_plane_displacement = calculate_zero_plane_displacement(
        canopy_height=data["canopy_height"],
        leaf_area_index=data["leaf_area_index"],
        zero_plane_scaling_parameter=wind_const.zero_plane_scaling_parameter,
    )
    roughness_length_momentum = calculate_roughness_length_momentum(
        canopy_height=data["canopy_height"],
        leaf_area_index=data["leaf_area_index"],
        zero_plane_displacement=zero_plane_displacement,
        substrate_surface_drag_coefficient=(
            wind_const.substrate_surface_drag_coefficient
        ),
        roughness_element_drag_coefficient=(
            wind_const.roughness_element_drag_coefficient
        ),
        roughness_sublayer_depth_parameter=(
            wind_const.roughness_sublayer_depth_parameter
        ),
        max_ratio_wind_to_friction_velocity=(
            wind_const.max_ratio_wind_to_friction_velocity
        ),
    )

    diabatic_correction_momentum_above = calculate_diabatic_correction_momentum_above(
        temperature=data["temperature_2m"],
        atmospheric_pressure=data["atmospheric_pressure"],
        sensible_heat_flux=data["sensible_heat_flux"],
        friction_velocity=data["friction_velocity"],
        wind_heights=wind_heights,
        zero_plane_displacement=zero_plane_displacement,
        celsius_to_kelvin=abiotic_const.celsius_to_kelvin,
        gravity=abiotic_const.gravity,
    )

    mixing_length = calculate_mixing_length(
        canopy_height=data["canopy_height"],
        zero_plane_displacement=zero_plane_displacement,
        roughness_length_momentum=roughness_length_momentum,
        mixing_length_factor=wind_const.mixing_length_factor,
    )

    wind_attenuation_coefficient = calculate_wind_attenuation_coefficient(
        canopy_height=data["canopy_height"],
        leaf_area_index=data["leaf_area_index"],
        mixing_length=mixing_length,
        drag_coefficient=wind_const.drag_coefficient,
        relative_turbulence_intensity=wind_const.relative_turbulence_intensity,
        diabatic_correction_factor_below=wind_const.diabatic_correction_factor_below,
    )

    # Calculate wind profiles and return as Tuple
    wind_profile_above = calculate_wind_above_canopy(
        wind_heights=wind_heights,
        zero_plane_displacement=zero_plane_displacement,
        roughness_length_momentum=roughness_length_momentum,
        diabatic_correction_momentum_above=diabatic_correction_momentum_above,
        friction_velocity=data["friction_velocity"],
    )

    wind_profile_canopy = calculate_wind_below_canopy(
        canopy_node_heights=canopy_node_heights,
        wind_profile_above=wind_profile_above,
        wind_attenuation_coefficient=wind_attenuation_coefficient,
        canopy_height=data["canopy_height"],
    )

    return wind_profile_above, wind_profile_canopy


def calculate_wind_above_canopy(
    wind_heights: DataArray,
    zero_plane_displacement: DataArray,
    roughness_length_momentum: DataArray,
    diabatic_correction_momentum_above: DataArray,
    friction_velocity: DataArray,
) -> DataArray:
    """Calculate wind profile above canopy.

    Wind profiles above the canopy dictate heat and vapor exchange between the canopy
    and air above it, and therefore ultimately determine temperature and vapor profiles.
    We follow the implementation by :cite:t:`campbell_introduction_1998` as described in
    :cite:t:`maclean_microclimc_2021`.

    Args:
        wind_heights: vector of heights above canopy for which wind speed is calculated,
            [m]
        zero_plane_displacement: height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        roughness_length_momentum: roughness length for momentum, [m]
        diabatic_correction_momentum_above: diabatic correction for momentum above
            canopy
        friction_velocity: friction velocity, [m s-1]

    Returns:
        vertical wind profile above canopy, [m s-1]

    # TODO: find correct fill value
    """

    return (
        (friction_velocity / 0.4)
        * np.log((wind_heights - zero_plane_displacement) / roughness_length_momentum)
        + diabatic_correction_momentum_above
    ).fillna(0)


def calculate_wind_below_canopy(
    canopy_node_heights: DataArray,
    wind_profile_above: DataArray,
    wind_attenuation_coefficient: DataArray,
    canopy_height: DataArray,
) -> DataArray:
    """Calculate wind profile below canopy.

    Implementation after :cite:t:`maclean_microclimc_2021`.
    The top of canopy windspeed is taken from the above canopy wind profile, which must
    be ordered from highest to lowest level. The lowest level is used here as the
    top-of-canopy wind speed.

    Args:
        copy_node_heights: heights of canopy nodes, [m]
        wind_profile_above: wind profile above canopy, [m s-1]
        wind_attenuation_coefficient: wind attenuation coefficient, dimensionless
        canopy_height: canopy height, [m]

    Returns:
        wind profile below canopy, [m s-1]

    # TODO: find correct fill value
    """
    top_of_canopy_wind_speed = wind_profile_above[:, -1]

    return (
        top_of_canopy_wind_speed
        * np.exp(
            wind_attenuation_coefficient * ((canopy_node_heights / canopy_height) - 1)
        )
    ).fillna(0)


def calculate_zero_plane_displacement(
    canopy_height: DataArray,
    leaf_area_index: DataArray,
    zero_plane_scaling_parameter: float = WindConstants.zero_plane_scaling_parameter,
) -> DataArray:
    """Calculate zero plane displacement.

    The zero plane displacement height of a vegetated surface is the height at which the
    wind speed would go to zero if the logarithmic wind profile was maintained from the
    outer flow all the way down to the surface (that is, in the absence of the
    vegetation when the value is set to zero). Implementation after
    :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        leaf_area_index: leaf area index, [m m-1]
        zero_plane_scaling_parameter: Control parameter for scaling d/h
            :cite:p:`raupach_simplified_1994`

    Returns:
        zero place displacement height, [m]
    """
    plant_area_index = leaf_area_index.sum(dim="canopy_layers")

    # calculate in presence of vegetation
    plant_area_index_displacement = plant_area_index.where(plant_area_index > 0)

    scale_displacement = np.sqrt(
        zero_plane_scaling_parameter * plant_area_index_displacement
    )

    zero_place_displacement = DataArray(
        (1 - (1 - np.exp(-scale_displacement)) / scale_displacement) * canopy_height,
        dims="cell_id",
    )

    return zero_place_displacement.fillna(0)  # no displacement in absence of vegetation


def calculate_roughness_length_momentum(
    canopy_height: DataArray,
    leaf_area_index: DataArray,
    zero_plane_displacement: DataArray,
    substrate_surface_drag_coefficient: float = (
        WindConstants.substrate_surface_drag_coefficient
    ),
    roughness_element_drag_coefficient: float = (
        WindConstants.roughness_element_drag_coefficient
    ),
    roughness_sublayer_depth_parameter: float = (
        WindConstants.roughness_sublayer_depth_parameter
    ),
    max_ratio_wind_to_friction_velocity: float = (
        WindConstants.max_ratio_wind_to_friction_velocity
    ),
) -> DataArray:
    """Calculate roughness length governing momentum transfer.

    Roughness length is defined as the height at which the mean velocity is zero due to
    substrate roughness. Real surfaces such as the ground or vegetation are not smooth
    and often have varying degrees of roughness. Roughness length accounts for that
    effect. Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        leaf_area_index: leaf area index, [m m-1]
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

    plant_area_index = leaf_area_index.sum(dim="canopy_layers")

    # calculate ratio of wind velocity to friction velocity
    ratio_wind_to_friction_velocity = DataArray(
        np.sqrt(
            substrate_surface_drag_coefficient
            + (roughness_element_drag_coefficient * plant_area_index) / 2
        )
    )

    # if the ratio of wind velocity to friction velocity is larger than the set maximum,
    # set the value to set maximum
    set_maximum_ratio = ratio_wind_to_friction_velocity.where(
        ratio_wind_to_friction_velocity < max_ratio_wind_to_friction_velocity
    )
    adjusted_ratio_wind_to_friction_velocity = set_maximum_ratio.fillna(
        max_ratio_wind_to_friction_velocity
    )

    # calculate initial roughness length
    initial_roughness_length = (canopy_height - zero_plane_displacement) * np.exp(
        -0.4 * (1 / adjusted_ratio_wind_to_friction_velocity)
        - roughness_sublayer_depth_parameter
    )

    # if roughness smaller than the substrate surface drag coefficient, set to value to
    # the substrate surface drag coefficient
    set_min_roughness_length = initial_roughness_length.where(
        initial_roughness_length > substrate_surface_drag_coefficient
    )
    roughness_length = set_min_roughness_length.fillna(
        substrate_surface_drag_coefficient
    )

    return roughness_length


def calculate_diabatic_correction_momentum_above(
    temperature: DataArray,
    atmospheric_pressure: DataArray,
    sensible_heat_flux: DataArray,
    friction_velocity: DataArray,
    wind_heights: DataArray,
    zero_plane_displacement: DataArray,
    celsius_to_kelvin: float = AbioticConstants.celsius_to_kelvin,
    gravity: float = AbioticConstants.gravity,
) -> DataArray:
    """Calculates the diabatic correction factors.

    Diabatic correction factor for momentum isused in adjustment of wind profiles after
    :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: 2m temperature
        atmospheric_pressure: atmospheric pressure, [kPa]
        sensible_heat_flux: sensible heat flux from canopy to atmosphere above,
            [J m-2], # TODO: could be the top entry of the general sensible heat flux
        friction_velocity: friction velocity
        wind_heights: vector of heights for which wind speed is calculated, [m]
        zero_plane_displacement: height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        gravity: Gravity

    Returns:
        diabatic correction factor for momentum transfer
    """

    temperature_kelvin = temperature * celsius_to_kelvin

    molar_density_air = calc_molar_density_air(
        temperature=temperature, atmospheric_pressure=atmospheric_pressure
    )
    specific_heat_air = calc_specific_heat_air(temperature=temperature)

    # calculate atmospheric stability
    stability = -(
        0.4 * gravity * (wind_heights - zero_plane_displacement) * sensible_heat_flux
    ) / (
        molar_density_air
        * specific_heat_air
        * temperature_kelvin
        * np.power(friction_velocity, 3)
    )

    stable = stability.where(stability > 0)
    diabatic_correction_momentum_above = DataArray(6 * np.log(1 + stable))

    # Unstable
    unstable = stability.where(stability < 0)
    unstable_coefficient = DataArray(
        -2 * np.log((1 + np.power((1 - 16 * unstable), 0.5)) / 2)
    )
    diabatic_correction_momentum_above.fillna(1) + unstable_coefficient.fillna(1)

    # set upper threshold
    diabatic_correction_momentum_above = DataArray(
        np.minimum(diabatic_correction_momentum_above, 5)
    )

    return diabatic_correction_momentum_above.fillna(1)


def calculate_mixing_length(
    canopy_height: DataArray,
    zero_plane_displacement: DataArray,
    roughness_length_momentum: DataArray,
    mixing_length_factor: float = WindConstants.mixing_length_factor,
) -> DataArray:
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

    return DataArray(
        (mixing_length_factor * (canopy_height - zero_plane_displacement))
        / np.log((canopy_height - zero_plane_displacement) / roughness_length_momentum),
        dims="cell_id",
    ).fillna(0)


def calculate_wind_attenuation_coefficient(
    canopy_height: DataArray,
    leaf_area_index: DataArray,
    mixing_length: DataArray,
    drag_coefficient: float = WindConstants.drag_coefficient,
    relative_turbulence_intensity: float = WindConstants.relative_turbulence_intensity,
    diabatic_correction_factor_below: float = (
        WindConstants.diabatic_correction_factor_below
    ),
) -> DataArray:
    """Calculate wind attenuation coefficient.

    The wind attenuation coefficient describes how wind is slowed down by the presence
    of vegetation. In absence of vegetation, the coefficient is set to zero.
    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        canopy_height: canopy height, [m]
        leaf_area_index: leaf area index, [m m-1]
        mixing_length: mixing length for canopy air transport, [m]
        drag_coefficient: drag coefficient
        relative_turbulence_intensity: relative turbulence intensity
        diabatic_correction_factor_below: diabatic correction factor below canopy

    Returns:
        wind attenuation coefficient
    """

    plant_area_index = leaf_area_index.sum(dim="canopy_layers")

    intermediate_coefficient1 = DataArray(
        (drag_coefficient * plant_area_index * canopy_height)
        / (2 * mixing_length * relative_turbulence_intensity),
        dims="cell_id",
    )

    intermediate_coefficient2 = DataArray(
        np.power(intermediate_coefficient1, 0.5), dims="cell_id"
    )

    return DataArray(
        (intermediate_coefficient2 * np.power(diabatic_correction_factor_below, 0.5)),
        dims="cell_id",
    ).fillna(0)
