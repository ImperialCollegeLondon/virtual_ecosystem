r"""The ``models.abiotic.conductivities`` module calculates the conductivities for the
energy balance of the Virtual Rainforest.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_rainforest.models.abiotic.constants import AbioticConsts


def interpolate_along_heights(
    start_height: NDArray[np.float32],
    end_height: NDArray[np.float32],
    target_heights: NDArray[np.float32],
    start_value: float,
    end_value: float,
) -> NDArray[np.float32]:
    """Vertical interpolation for given start and end values along a height axis.

    This function can be used to lineraly interpolate atmospheric or soil variables such
    as temperature or humidity for a set of user specified heights based on the top and
    bottom values.

    Args:
        start_height: Starting heights of the interpolation range, [m]
        end_height: Ending heights of the interpolation range, [m]
        target_heights: Array of target heights with the first column representing
            heights and subsequent columns representing additional dimensions, here
            `cell_id`.
        start_value: The value at the starting height.
        end_value: The value at the ending height.

    Returns:
        Interpolated values corresponding to the target heights
    """
    # Ensure the target heights are within the range [start_height, end_height]
    target_heights = np.clip(target_heights, start_height, end_height)

    # Calculate the interpolation slope and intercept
    slope = (end_value - start_value) / (end_height - start_height)
    intercept = start_value - slope * start_height

    # Interpolate values at the target heights
    interpolated_values = slope * target_heights + intercept

    return interpolated_values


def initialise_conductivities(
    layer_heights: DataArray,
    initial_air_conductivity: float,
    top_leaf_vapor_conductivity: float,
    bottom_leaf_vapor_conductivity: float,
    top_leaf_air_conductivity: float,
    bottom_leaf_air_conductivity: float,
) -> dict[str, DataArray]:
    r"""Initialise conductivities for first model time step, [mol m-2 s-1].

    The initial values for all conductivities are typical for decidious woodland with
    wind above canopy at 2 m/s.
    Air heat conductivity by turbulent convection (:math:`g_{t}`) is scaled by canopy
    height and `m` (and hence distance between nodes). Leaf-air vapor conductivity
    (:math:`g_{v}`) and leaf-air heat conductivity (:math:`g_{Ha}`) are linearly
    interpolated between intial values.
    The first value in each output represents conductivity between the air at 2 m above
    canopy and the highest canopy layer. The last value represents conductivity between
    the ground and the lowest canopy node.

    Args:
        layer_height: layer heights, [m]
        initial_air_conductivity: Initial value for heat conductivity by turbulent
            convection in air, [mol m-2 s-1]
        top_leaf_vapor_conductivity: Initial leaf vapor conductivity at the top of the
            canopy, [mol m-2 s-1]
        bottom_leaf_vapor_conductivity: Initial leaf vapor conductivity at the bottom of
            the canopy, [mol m-2 s-1]
        top_leaf_air_conductivity: Initial leaf air heat conductivity at the top of the
            canopy, [mol m-2 s-1]
        bottom_leaf_air_conductivity: Initial leaf air heat conductivity at the surface,
            [mol m-2 s-1]

    Returns:
        Heat conductivity in air of each canopy layer node, [mol m-2 s-1],
        Leaf conductivity to vapor loss for each canopy layer node, [mol m-2 s-1],
        Heat conductivity between air and leaf for each canopy layer node, [mol m-2 s-1]
    """

    canopy_height = layer_heights[1].to_numpy()
    atmosphere_layers = layer_heights[layer_heights["layer_roles"] != "soil"]
    soil_layers = layer_heights[layer_heights["layer_roles"] == "soil"]

    output = {}

    # Initialise conductivity between air layers
    air_conductivity = (
        np.full((len(atmosphere_layers), len(canopy_height)), initial_air_conductivity)
        * (len(atmosphere_layers) / canopy_height)
        * 2
        / len(atmosphere_layers)
    )
    air_conductivity[-1] *= 2
    air_conductivity[0] *= (canopy_height / len(atmosphere_layers)) * 0.5
    output["air_conductivity"] = DataArray(
        np.concatenate(
            [air_conductivity, np.full((len(soil_layers), len(canopy_height)), np.nan)],
            axis=0,
        ),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="air_conductivity",
    )

    # Initialise leaf vapor conductivity
    leaf_vapor_conductivity = (
        output["air_conductivity"].copy().rename("leaf_vapor_conductivity")
    )
    leaf_vapor_cond_interpolation = interpolate_along_heights(
        start_height=layer_heights[-(len(soil_layers) + 1)].to_numpy(),
        end_height=layer_heights[0].to_numpy(),
        target_heights=layer_heights[atmosphere_layers.indexes].to_numpy(),
        start_value=top_leaf_vapor_conductivity,
        end_value=bottom_leaf_vapor_conductivity,
    )
    leaf_vapor_conductivity[atmosphere_layers.indexes] = leaf_vapor_cond_interpolation
    output["leaf_vapor_conductivity"] = leaf_vapor_conductivity

    # Initialise leaf air heat conductivity
    leaf_air_conductivity = (
        output["air_conductivity"].copy().rename("leaf_air_conductivity")
    )
    leaf_air_cond_interpolation = interpolate_along_heights(
        start_height=layer_heights[-(len(soil_layers) + 1)].to_numpy(),
        end_height=layer_heights[0].to_numpy(),
        target_heights=layer_heights[atmosphere_layers.indexes].to_numpy(),
        start_value=top_leaf_air_conductivity,
        end_value=bottom_leaf_air_conductivity,
    )
    leaf_air_conductivity[atmosphere_layers.indexes] = leaf_air_cond_interpolation
    output["leaf_air_conductivity"] = leaf_air_conductivity

    return output


def calculate_air_heat_conductivity_above(
    height_above_canopy: NDArray[np.float32],
    zero_displacement_height: NDArray[np.float32],
    canopy_height: NDArray[np.float32],
    friction_velocity: NDArray[np.float32],
    molar_density_air: NDArray[np.float32],
    adiabatic_correction_heat: NDArray[np.float32],
    von_karmans_constant: float,
) -> NDArray[np.float32]:
    r"""Calculate air heat conductivity by turbulent convection above canopy.

    Heat conductance, :math:`g_{t}` between any two heights :math:`z_{1}` and
    :math:`z_{0}` above-canopy is given by

    .. math::
        g_{t} = \frac {0.4 \hat{\rho} u^{*}}{ln(\frac{z_{1} - d}{z_{0} - d}) + \Psi_{H}}

    where :math:`\hat{\rho}` is the molar density or air, :math:`u^{*}` is the friction
    velocity, :math:`d` is the zero displacement height, and :math:`\Psi_{H}` is the
    adiabatic correction factor for heat.

    Args:
        height_above_canopy: Height above canopy, [m]
        zero_displacement_height: Zero displacement height, [m]
        canopy_height: Canopy height, [m]
        friction_velocity: Friction velocity, dimensionless
        molar_density_air: Molar density of air, [mole m-3]
        adiabatic_correction_heat: Adiabatic correction factor for heat
        von_karmans_constant: Von Karman constant, unitless

    Returns:
        Air heat conductivity by turbulent convection above canopy, [mol m-2 s-1]
    """

    return (von_karmans_constant * molar_density_air * friction_velocity) / (
        np.log(height_above_canopy - zero_displacement_height)
        / (canopy_height - zero_displacement_height)
        + adiabatic_correction_heat
    )


def calculate_air_heat_conductivity_canopy(
    attenuation_coefficient: NDArray[np.float32],
    mean_mixing_length: NDArray[np.float32],
    molar_density_air: NDArray[np.float32],
    upper_height: NDArray[np.float32],
    lower_height: NDArray[np.float32],
    relative_turbulence_intensity: NDArray[np.float32],
    top_of_canopy_wind_speed: NDArray[np.float32],
    diabatic_correction_momentum: NDArray[np.float32],
    canopy_height: NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate air heat conductivity by turbulent convection in canopy,[mol m-2 s-1].

    Within-canopy heat conductance (:math:`g_{t}`) between any two heights :math:`z_{1}`
    and :math:`z_{0}` below-canopy is given by

    .. math::
        g_{t} = \frac{u_{h}l_{m}i_{w}a}
        {(exp(\frac{-a_{z_{0}}}{h-1}) - exp(\frac{-a_{z_{1}}}{h-1})) \Psi_{H}}


    where :math:`u_{h}` is wind speed at the top of the canopy at height :math:`h`,
    :math:`a` is a wind attenuation coefficient, :math:`i_{w}` is a coefficient
    describing relative turbulence intensity, :math:`l_{m}` is the mean mixing length,
    equivalent to the free space between the leaves and stems, and :math:`\Psi_{H}` is a
    within-canopy diabatic correction factor for heat.

    TODO better tests for different conditions

    Args:
        attenuation_coefficient: Wind attenuation coefficient, dimensionless
        mean_mixing_length: Mixing length for canopy air transport, [m]
        molar_density_air: Molar density of air, [mol m-3]
        upper_height: Height of upper layer, [m]
        lower_height: Height of lower layer, [m]
        relative_turbulence_intensity: Relative turbulence intensity, dimensionless
        top_of_canopy_wind_speed: Top of canopy wind speed, [m s-1]
        diabatic_correction_momentum: Diabatic correction factor for momentum
        canopy_height: Canopy height, [m]

    Returns:
       air heat conductivity by turbulent convection in the canopy, [mol m-2 s-1]
    """
    term1 = (
        mean_mixing_length
        * relative_turbulence_intensity
        * molar_density_air  # NOTE this should be the mean of the two layers
        * top_of_canopy_wind_speed
        * attenuation_coefficient
    ) / diabatic_correction_momentum

    term2 = np.exp(-attenuation_coefficient * (lower_height / canopy_height - 1))
    term3 = np.exp(-attenuation_coefficient * (upper_height / canopy_height - 1))
    return term1 / (term2 - term3)


def calculate_leaf_air_heat_conductivity(
    temperature: NDArray[np.float32],
    wind_speed: NDArray[np.float32],
    characteristic_dimension_leaf: NDArray[np.float32],
    temperature_difference: NDArray[np.float32],
    molar_density_air: NDArray[np.float32],
    kinematic_viscosity_parameter1: float,
    kinematic_viscosity_parameter2: float,
    thermal_diffusivity_parameter1: float,
    thermal_diffusivity_parameter2: float,
    grashof_parameter: float,
    forced_conductance_parameter: float,
    positive_free_conductance_parameter: float,
    negative_free_conductance_parameter: float,
) -> NDArray[np.float32]:
    r"""Calculate forced or free laminer conductance between leaf and air,[mol m-2 s-1].

    When wind speeds are moderate to high, conduction between the leaf and air
    :math:`g_{Ha}` is predominantly under laminar forced convection and from e.g.
    :cite:t:`campbell_introduction_2012` is given by

    .. math:: g_{Ha} = \frac {0.664 \hat{\rho} D_{H} R_{e}^{0.5} P_{r}^{0.5}}{x_{d}}

    where :math:`D_{H}` is thermal diffusivity, :math:`x_{d}` is the characteristic
    dimension of the leaf, :math:`\hat{\rho}` is the molar density of air,
    :math:`R_{e}` is the Reynolds number, and :math:`P_{r}` is the Prandtl number.

    When wind speeds are low, an expression that is adequate for leaves is given by
    (Campbell and Norman, 2012)

    .. math:: g_{Ha} = \frac{0.54 \hat{\rho} D_{H} (G_{r}P_{r})^{0.25}}{x_{d}}

    where :math:`G_{r}` is the Grashof number. When the leaf is cooler than the air, the
    heat transfer is only half as efficient so the constant 0.54 becomes 0.26.

    TODO better tests for different conditions

    Args:
        temperature: Temperature, [C]
        wind_speed: Wind speed, [m s-1]
        characteristic_dimension_leaf: chacteristic dimension of leaf, typically around
            0.7*leaf width, [m]
        temperature_difference: Estimate of temperature differences of surface and air,
            e.g. from previous time step, see notes in :cite:t:`maclean_microclimc_2021`
        molar_density_air: Molar density of air, [mol m-3]
        kinematic_viscosity_parameter1: Parameter in calculation of kinematic viscosity
        kinematic_viscosity_parameter2: Parameter in calculation of kinematic viscosity
        thermal_diffusivity_parameter1: Parameter in calculation of thermal diffusivity
        thermal_diffusivity_parameter2: Parameter in calculation of thermal diffusivity
        grashof_parameter: Parameter in calculation of Grashof number
        forced_conductance_parameter: Parameter in calculation of forced conductance
        positive_free_conductance_parameter: Parameter in calculation of free
            conductance for positive temperature difference
        negative_free_conductance_parameter: Parameter in calculation of free
            conductance for negative temperature difference

    Returns:
        Leaf air heat conductance, [mol m-2 s-1]
    """

    temperature_k = temperature + 273.15
    kinematic_viscosity = (
        kinematic_viscosity_parameter1 * temperature_k - kinematic_viscosity_parameter2
    ) / 10**6
    thermal_diffusivity = (
        thermal_diffusivity_parameter1 * temperature_k - thermal_diffusivity_parameter2
    ) / 10**6
    grashof_number = (
        grashof_parameter
        * characteristic_dimension_leaf**3
        * np.abs(temperature_difference)
    ) / (temperature_k * kinematic_viscosity**2)
    reyolds_number = wind_speed * characteristic_dimension_leaf / kinematic_viscosity
    prandtl_number = kinematic_viscosity / thermal_diffusivity

    # Forced conductance
    forced_conductance = (
        forced_conductance_parameter
        * thermal_diffusivity
        * molar_density_air
        * reyolds_number**0.5
        * prandtl_number ** (1 / 3)
    ) / characteristic_dimension_leaf

    # Free conductance
    m = np.where(
        temperature_difference > 0,
        positive_free_conductance_parameter,
        negative_free_conductance_parameter,
    )
    free_conductance = (
        m
        * molar_density_air
        * thermal_diffusivity
        * (grashof_number * prandtl_number) ** (1 / 4)
    ) / characteristic_dimension_leaf

    # Set to whichever is higher
    conductance = np.where(
        forced_conductance > free_conductance, forced_conductance, free_conductance
    )

    return conductance


def calculate_leaf_vapor_conductivity(
    leaf_air_conductivity: NDArray[np.float32],
    stomatal_conductance: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate leaf air conductivity for vapor, [mol m-2 s-1].

    The conductance for vapor loss from leaves :math:`g_{v}` depends on stomatal
    conductance :math:`g_{c}` and heat conductivity between air and leaf :math:`g_{Ha}`:

    .. math:: g_{v} = \frac{1}{(\frac{1}{g_{Ha}} + \frac{1}{g_{c}})

    :cite:p:`maclean_microclimc_2021`.

    Args:
        leaf_air_conductivity: Heat conductivity between air and leaf, [mol m-2 s-1]
        stomatal_conductance: Stomatal conductance, [mol m-2 s-1]

    Returns:
        Leaf vapor conductivity, [mol m-2 s-1]
    """
    return 1 / ((1 / leaf_air_conductivity) + (1 / stomatal_conductance))


def calculate_current_conductivities(
    above_ground_heights: DataArray,
    attenuation_coefficient: NDArray[np.float32],
    mean_mixing_length: NDArray[np.float32],
    molar_density_air: NDArray[np.float32],
    relative_turbulence_intensity: NDArray[np.float32],
    top_of_canopy_wind_speed: NDArray[np.float32],
    diabatic_correction_momentum: NDArray[np.float32],
    air_temperature_canopy: NDArray[np.float32],
    wind_speed_canopy: NDArray[np.float32],
    characteristic_dimension_leaf: NDArray[np.float32],
    estimated_temperature_difference: NDArray[np.float32],
    stomatal_conductance: NDArray[np.float32],
    zero_displacement_height: NDArray[np.float32],
    friction_velocity: NDArray[np.float32],
    adiabatic_correction_heat: NDArray[np.float32],
    von_karmans_constant: float,
    abiotic_constants: AbioticConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate conductivities based on current reference data.

    Args:
        above_ground_heights: heights above ground, from reference height 2m above the
            canopy to the surface layer, [m]
        attenuation_coefficient: Wind attenuation coefficient, dimensionless
        mean_mixing_length: Mixing length for canopy air transport, [m]
        molar_density_air: Molar density of air, [mol m-3]
        relative_turbulence_intensity: Relative turbulence intensity
        top_of_canopy_wind_speed: Top of canopy wind speed, [m s-1]
        diabatic_correction_momentum: Diabatic correction for momentum
        air_temperature_canopy: Air temperature suppronding the canopy, [C]
        wind_speed_canopy: Wind speed within the canopy, [m s-1]
        characteristic_dimension_leaf: Characteristic dimension of leaf
        estimated_temperature_difference: Estimated temperature difference, usually from
            previous time step
        stomatal_conductance: Stomatal conductance
        zero_displacement_height: Zero displacement height, [m]
        friction_velocity: Friction velocity
        adiabatic_correction_heat: Adiabatic correction for heat
        von_karmans_constant: Von Karman constant
        abiotic_constants: set of abiotic constants

    Returns:
        dictionnary of conductances, [mol m-2 s-1]
    """

    output = {}

    # Air heat conductivity, gt
    air_heat_conductivity_above = calculate_air_heat_conductivity_above(
        height_above_canopy=above_ground_heights.isel(layers=0).to_numpy(),
        zero_displacement_height=zero_displacement_height,
        canopy_height=above_ground_heights.isel(layers=1).to_numpy(),
        friction_velocity=friction_velocity[0],
        molar_density_air=molar_density_air[0],
        adiabatic_correction_heat=adiabatic_correction_heat[0],
        von_karmans_constant=von_karmans_constant,
    )
    current_air_heat_conductivity = []
    for layer in np.arange(0, len(above_ground_heights) - 1):
        result = calculate_air_heat_conductivity_canopy(
            attenuation_coefficient=attenuation_coefficient[layer],
            mean_mixing_length=mean_mixing_length,
            molar_density_air=molar_density_air[layer],
            upper_height=above_ground_heights.isel(layers=layer).to_numpy(),
            lower_height=above_ground_heights.isel(layers=layer + 1).to_numpy(),
            relative_turbulence_intensity=relative_turbulence_intensity[layer],
            top_of_canopy_wind_speed=top_of_canopy_wind_speed,
            diabatic_correction_momentum=diabatic_correction_momentum[layer],
            canopy_height=above_ground_heights.isel(layers=1).to_numpy(),
        )
        current_air_heat_conductivity.append(result)

    output["current_air_heat_conductivity"] = np.vstack(
        [air_heat_conductivity_above, np.vstack(current_air_heat_conductivity)]
    )

    # Leaf air heat conductivity, gha
    current_leaf_air_heat_conductivity = calculate_leaf_air_heat_conductivity(
        temperature=air_temperature_canopy,
        wind_speed=wind_speed_canopy,
        characteristic_dimension_leaf=characteristic_dimension_leaf,
        temperature_difference=estimated_temperature_difference,
        molar_density_air=molar_density_air[0:3],
        kinematic_viscosity_parameter1=abiotic_constants.kinematic_viscosity_parameter1,
        kinematic_viscosity_parameter2=abiotic_constants.kinematic_viscosity_parameter1,
        thermal_diffusivity_parameter1=abiotic_constants.thermal_diffusivity_parameter1,
        thermal_diffusivity_parameter2=abiotic_constants.thermal_diffusivity_parameter2,
        grashof_parameter=abiotic_constants.grashof_parameter,
        forced_conductance_parameter=abiotic_constants.forced_conductance_parameter,
        positive_free_conductance_parameter=(
            abiotic_constants.positive_free_conductance_parameter
        ),
        negative_free_conductance_parameter=(
            abiotic_constants.negative_free_conductance_parameter
        ),
    )
    output["current_leaf_air_heat_conductivity"] = current_leaf_air_heat_conductivity

    # Leaf vapor conductivity, gv
    current_leaf_vapor_conductivity = calculate_leaf_vapor_conductivity(
        leaf_air_conductivity=current_leaf_air_heat_conductivity,
        stomatal_conductance=stomatal_conductance,
    )
    output["current_leaf_vapor_conductivity"] = current_leaf_vapor_conductivity

    return output
