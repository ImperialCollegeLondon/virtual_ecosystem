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

For soils, the sensible and latent heat fluxes are given by:

:math:`H_{S} = \frac {\rho_{air} C_{air} (T_{S} - T_{b}^{A})}{r_{A}}`

:math:`Q_{S} = \frac {\rho_{air} \lambda (q_{*}(T_{b}^{A}) - q_{b}^{A})}{r_{A}}`

Where :math:`T_{S}` is the soil surface temperature, :math:`T_{b}^{A}` and
:math:`q_{b}^{A}` are the temperature and specific humidity of the bottom air layer and
:math:`r_{A}` is the aerodynamic resistance of the soil surface, given by

:math:`r_{A} = \frac {C_{S}}{u_{b}}`

Where :math:`u_{b}` is the wind speed in the bottom air layer and :math:`C_{S}` is the
soil surface heat transfer coefficient.

In the soil, heat storage is almost always significant. Thus, Fourier's Law is combined
with the continuity equation to obtain a time dependant differential equation that
describes soil temperature as a function of depth and time. A numerical solution can be
achieved by dividing the soil into discrete layers. Each layer is assigned a node,
:math:`i`, at depth, :math:`z_{i}`, and with heat storage, :math:`C_{h_{i}}`, and nodes
are numbered sequentially downward such that node :math:`i+1` represents the
node for the soil layer immediately below. Conductivity, :math:`k_{i}`, represents
conductivity between nodes :math:`i` and :math:`i+1`. The energy balance equation for
node :math:`i` is then given by

.. math::
    \kappa_{i}(T_{i+1} - T_{i})- \kappa_{i-1}(T_{i} - T_{i-1})
    = \frac{C_{h_{i}}(T_{i}^{j+1} - T_{i}^{j})(z_{i+1} - z_{i-1})}{2 \Delta t}

where :math:`\Delta t` is the time increment, conductance,
:math:`\kappa_{i}=k_{i}/(z_{i+1} - z_{i})`,  and superscript :math:`j` indicates the
time at which temperature is determined. This equation can be re-arranged and solved for
:math:`T_{j+1}` by Gaussian elimination using the Thomas algorithm.
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray

# from pint import Quantity
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
    """Initialise conductivities for first model time step.

    The initial values for all conductivities are typical for decidious woodland with
    wind above canopy at 2 m/s.
    Air conductivity is scaled by canopy height and `m` (and hence distance
    between nodes). leaf vapor conductivity and leaf air conductivity are linearly
    interpolated between intial values.
    The first value in each output represents conductivity between the air at 2 m above
    canopy and the highest canopy layer. The last value represents conductivity between
    the ground and the lowest canopy node.

    Args:
        layer_height: layer heights, [m]
        initial_air_conductivity: Initial value for conductivity in air, [mol m-2 s-1]
        top_leaf_vapor_conductivity: Initial leaf vapor conductivity at the top of the
            canopy, [mol m-2 s-1]
        bottom_leaf_vapor_conductivity: Initial leaf vapor conductivity at the bottom of
            the canopy, [mol m-2 s-1]
        top_leaf_air_conductivity: Initial leaf air heat conductivity at the top of the
            canopy, [mol m-2 s-1]
        bottom_leaf_air_conductivity: Initial leaf air heat conductivity at the surface,
            [mol m-2 s-1]

    Returns:
        Conductivity in air of each canopy layer node, [mol m-2 s-1]
        Leaf conductivity to vapour loss for each canopy layer node, [mol m-2 s-1]
        Conductivity between air and leaf for each canopy layer node, [mol m-2 s-1]
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


# Functions related to the soil energy balance
def calculate_soil_absorption(
    shortwave_radiation_surface: NDArray[np.float32],
    surface_albedo: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate soil absorption of shortwave radiation.

    The amount of shortwave radiation that is absorbed by the topsoil layer is a
    function of incoming radiation and  surface albedo. In reality, surface albedo is
    modulated by soil moisture. The current implementation of soil absorption assumes a
    constant albedo within each grid cell because the radiation that reaches the surface
    below the canopy is typically quite small (<5%).

    Args:
        shortwave_radiation_surface: Shortwave radiation that reaches the surface,
            [W m-2]
        surface_albedo: Surface albedo, dimensionless.

    Returns:
        shortwave radiation absorbed by soil surface, [W m-2]
    """

    return shortwave_radiation_surface * (1 - surface_albedo)


def calculate_soil_longwave_emission(
    topsoil_temperature: NDArray[np.float32],
    soil_emissivity: float | NDArray[np.float32],
    stefan_boltzmann: float,
) -> NDArray[np.float32]:
    """Calculate topsoil longwave emission.

    The emission of longwave radiation depends on the soil temperature and soil
    emissivity as in the Stefan Boltzmann law.

    Args:
        topsoil_temperature: temperature of top soil layer, [K]
        soil_emissivity: soil emissivity, dimensionless
        stefan_boltzmann_constant: Stefan Boltzmann constant, [W m-2 K-4]

    Returns:
        topsoil longwave emission, [W m-2]
    """
    return soil_emissivity * stefan_boltzmann * topsoil_temperature**4


def calculate_sensible_heat_flux_soil(
    air_temperature_surface: NDArray[np.float32],
    topsoil_temperature: NDArray[np.float32],
    molar_density_air: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    wind_speed_surface: NDArray[np.float32],
    soil_surface_heat_transfer_coefficient: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate sensible heat flux from soil surface.

    The sensible heat flux from the soil surface is given by:

    :math:`H_{S} = \frac {\rho_{air} C_{air} (T_{S} - T_{b}^{A})}{r_{A}}`

    Where :math:`T_{S}` is the soil surface temperature, :math:`T_{b}^{A}` is the
    temperature of the bottom air layer and :math:`r_{A}` is the aerodynamic resistance
    of the soil surface, given by

    :math:`r_{A} = \frac {C_{S}}{u_{b}}`

    Where :math:`u_{b}` is the wind speed in the bottom air layer and :math:`C_{S}` is
    the soil surface heat transfer coefficient.

    Args:
        air_temperature_surface: Air temperature near the surface, [K]
        topsoil_temperature: Topsoil temperature, [K]
        molar_density_air: Molar density of air, [mol m-3]
        specific_heat_air: Specific heat of air, [J mol-1 K-1]
        wind_speed_surface: Wind speed near the surface, [m s-1]
        soil_surface_heat_transfer_coefficient: Soil surface heat transfer coefficient

    Returns:
        Sensible heat flux from topsoil, [W m-2]
    """

    aerodynamic_resistance = soil_surface_heat_transfer_coefficient / wind_speed_surface
    return (
        molar_density_air
        * specific_heat_air
        * (topsoil_temperature - air_temperature_surface)
    ) / aerodynamic_resistance
