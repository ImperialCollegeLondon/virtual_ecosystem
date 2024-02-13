r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Rainforest. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapor exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly. Under steady-state,
the balance equation for the leaves in each canopy layer is as follows (after
:cite:t:`maclean_microclimc_2021`):

.. math::
    R_{abs} - R_{em} - H - \lambda E
    = R_{abs} - \epsilon_{s} \sigma T_{L}^{4} - c_{P}g_{Ha}(T_{L} - T_{A})
    - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{A}} = 0

where :math:`R_{abs}` is absorbed radiation, :math:`R_{em}` emitted radiation, :math:`H`
the sensible heat flux, :math:`\lambda E` the latent heat flux, :math:`\epsilon_{s}` the
emissivity of the leaf, :math:`\sigma` the Stefan-Boltzmann constant, :math:`T_{L}` the
absolute temperature of the leaf, :math:`T_{A}` the absolute temperature of the air
surrounding the leaf, :math:`\lambda` the latent heat of vaporisation of water,
:math:`e_{L}` the effective vapor pressure of the leaf, :math:`e_{A}` the vapor
pressure of air and :math:`p_{A}` atmospheric pressure. :math:`g_{Ha}` is the heat
conductance between leaf and atmosphere, :math:`g_{v}` represents the conductance
for vapor loss from the leaves as a function of the stomatal conductance :math:`g_{c}`.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a linearisation approach to solve the equation for
leaf temperature and air temperature simultaneously after
:cite:t:`maclean_microclimc_2021`, see TODO put name of equation here.

The soil energy balance functions are described in
:mod:`~virtual_rainforest.models.abiotic.soil_energy_balance`.

TODO check equations for consistency re naming
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray


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

    absorbed_radiation = np.zeros_like(leaf_area_index)
    penetrating_radiation = np.zeros_like(leaf_area_index)
    layer_depths = np.abs(np.diff(layer_heights, axis=1, append=0))
    for i in range(len(layer_heights[0])):
        penetrating_radiation[:, i] = topofcanopy_radiation * (
            np.exp(
                -light_extinction_coefficient
                * leaf_area_index[:, i]
                * layer_depths[:, i]
            )
        )
        absorbed_radiation[:, i] = topofcanopy_radiation - penetrating_radiation[:, i]
        topofcanopy_radiation -= topofcanopy_radiation - penetrating_radiation[:, i]

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
        absorbed_radiation: Shortwave radiation absorbed by canopy

    Returns:
        Initial canopy temperature, [C]
    """
    return air_temperature + canopy_temperature_ini_factor * absorbed_radiation


def initialise_canopy_and_soil_fluxes(
    air_temperature: DataArray,
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    layer_heights: DataArray,
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
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation

    Returns:
        Dictionary with absorbed radiation (canopy), canopy temperature, sensible
            and latent heat flux (canopy and soil), and ground heat flux.
    """

    output = {}
    # select canopy layers with leaf area index != nan
    leaf_area_index_true = leaf_area_index[
        leaf_area_index["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    layer_heights_canopy = layer_heights[
        leaf_area_index["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")
    air_temperature_canopy = air_temperature[
        leaf_area_index["layer_roles"] == "canopy"
    ].dropna(dim="layers", how="all")

    # Initialize absorbed radiation DataArray
    absorbed_radiation = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_absorption",
    )

    # calculate absorbed radiation
    initial_absorbed_radiation = initialise_absorbed_radiation(
        topofcanopy_radiation=topofcanopy_radiation.to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.T.to_numpy(),  # TODO check if .T is needed
        light_extinction_coefficient=light_extinction_coefficient,
    )

    # Replace np.nan with new values and write in output dict
    absorbed_radiation[layer_heights_canopy.indexes] = initial_absorbed_radiation
    output["canopy_absorption"] = absorbed_radiation

    # Initialize canopy temperature
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
    canopy_temperature[layer_heights_canopy.indexes] = initial_canopy_temperature
    output["canopy_temperature"] = canopy_temperature

    # Initialise sensible heat flux with zeros and write in output dict
    sensible_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="canopy_temperature",
    )
    sensible_heat_flux[layer_heights_canopy.indexes] = 0
    sensible_heat_flux[layer_heights["layer_roles"] == "surface"] = 0
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
    ground_heat_flux[layer_heights["layer_roles"] == "surface"] = 0
    output["ground_heat_flux"] = ground_heat_flux

    return output


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
        relative_turbulence_intensity: relative turbulence intensity, dimensionless
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
    characteristic_dimension_surface: NDArray[np.float32],
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
        characteristic_dimension_surface: chacteristic dimension of surface, [m]
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
        * characteristic_dimension_surface**3
        * np.abs(temperature_difference)
    ) / (temperature_k * kinematic_viscosity**2)
    reyolds_number = wind_speed * characteristic_dimension_surface / kinematic_viscosity
    prandtl_number = kinematic_viscosity / thermal_diffusivity

    # Forced conductance
    forced_conductance = (
        forced_conductance_parameter
        * thermal_diffusivity
        * molar_density_air
        * reyolds_number**0.5
        * prandtl_number ** (1 / 3)
    ) / characteristic_dimension_surface

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
    ) / characteristic_dimension_surface

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
