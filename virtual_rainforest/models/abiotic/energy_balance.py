r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Rainforest. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
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
:math:`e_{L}` the effective vapour pressure of the leaf, :math:`e_{A}` the vapor
pressure of air and :math:`p_{A}` atmospheric pressure. :math:`g_{Ha}` is the heat
conductance between leaf and atmosphere, :math:`g_{v}` represents the conductance
for vapor loss from the leaves as a function of the stomatal conductance.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a linearisation approach to solve the equation for
leaf temperature and air temperature simultaneously, see
:cite:t:`maclean_microclimc_2021`.

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

    :math:`I(z) = I_{0} * e^{(-k * LAI * z)}`

    Args:
        topofcanopy_radiation: top of canopy radiation shortwave radiation, [W m-2]
        leaf_area_index: leaf area index of each canopy layer, [m m-1]
        layer_heights: layer heights, [m]
        light_extinction_coefficient: light extinction coefficient, [m-1]

    Returns:
        shortwave radiation absorbed by canopy layers, [W m-2]
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
        air_temperature: air temperature, [C]
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation
        absorbed_radiation: shortwave radiation absorbed by canopy

    Returns:
        initial canopy temperature, [C]
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
        air_temperature: air temperature, [C]
        topofcanopy_radiation: top of canopy radiation, [W m-2]
        leaf_area_index: Leaf area index, [m m-2]
        layer_heights: Layer heights, [m]
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation

    Returns:
        dictionnary with absorbed radiation (canopy), canopy temperature, sensible
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
    r"""Initialise conductivities for first model time step.

    The initial values for all conductivities are typical for decidious woodland with
    wind above canopy at 2 m/s.
    Air heat conductivity by turbulent convection (:math:`g_{t}`is scaled by canopy
    height and `m` (and hence distance between nodes). Leaf-air vapor conductivity
    :math:`g_{v}` and leaf-air heat conductivity :math:`g_{ha}` are linearly
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
        Heat conductivity in air of each canopy layer node, [mol m-2 s-1]
        Leaf conductivity to vapour loss for each canopy layer node, [mol m-2 s-1]
        heat conductivity between air and leaf for each canopy layer node, [mol m-2 s-1]
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

    # Initialise leaf vapour conductivity
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

    Args:
        start_height: The starting heights of the interpolation range, [m]
        end_height: The ending heights of the interpolation range, [m]
        target_heights: array of target heights with the first column representing
            heights and subsequent columns representing additional dimensions, here
            `cell_id`.
        start_value: The value at the starting height.
        end_value: The value at the ending height.

    Returns:
        interpolated values corresponding to the target heights
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
    """Calculate longwave emission using the Stefan Boltzmann law..

    According to Stefan Boltzmann law, the amount of radiation emitted per unit time
    from area of a black body at absolute temperature is directly proportional to the
    fourth power of the temperature. Emissivity (which is equal to absorptive power)
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
    """Calculate air heat conductivity by turbulent convection above canopy.

    Args:
        height_above_canopy: Height above canopy, [m]
        zero_displacement_height: Zero displacement height, [m]
        canopy_height: canopy height, [m]
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


# def calculate_leaf_air_vapour_conductivity():

# def calculate_leaf_air_heat_conductivity():
