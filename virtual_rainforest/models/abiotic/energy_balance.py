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

TODO check equations for consistency re naming
"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.core.data import Data
from virtual_rainforest.models.abiotic.constants import AbioticConsts


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


def calculate_sensible_heat_flux_soil(
    air_temperature_surface: NDArray[np.float32],
    topsoil_temperature: NDArray[np.float32],
    molar_density_air: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    aerodynamic_resistance: NDArray[np.float32],
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
        aerodynamic_resistance: Aerodynamic resistance near the surface

    Returns:
        Sensible heat flux from topsoil, [W m-2]
    """

    return (
        molar_density_air
        * specific_heat_air
        * (topsoil_temperature - air_temperature_surface)
    ) / aerodynamic_resistance


def calculate_latent_heat_flux_from_soil_evaporation(
    soil_evaporation: NDArray[np.float32],
    latent_heat_vaporisation: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate latent heat flux from soil evaporation.

    We assume that 1 mm of evaporated water is equivalent to 1 kg of water.

    Args:
        soil_evaporation: Soil evaporation, [mm]
        latent_heat_vaporisation: Latent heat of vaporisation, [J kg-1]

    Returns:
        latent heat flux from topsoil, [W m-2]
    """

    return soil_evaporation * latent_heat_vaporisation


def calculate_ground_heat_flux(
    soil_absorbed_radiation: NDArray[np.float32],
    topsoil_longwave_emission: NDArray[np.float32],
    topsoil_sensible_heat_flux: NDArray[np.float32],
    topsoil_latent_heat_flux: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate ground heat flux.

    The ground heat flux is calculated as the residual of splitting incoming raditaion
    into emitted longwave radiation, and sensible and latent heat flux. A positive
    ground heat flux means a warming of the soil, a negative flux indicates a cooling of
    the soil.

    Args:
        soil_absorbed_radiation: Shortwave radiation absorbed by topsoil, [W m-2]
        topsoil_longwave_emission: Longwave radiation emitted by topsoil, [W m-2]
        topsoil_sensible_heat_flux: Sensible heat flux from topsoil, [W m-2]
        topsoil_latent_heat_flux: Latent heat flux from topsoil, [W m-2]

    Returns:
        ground heat flux, [W m-2]
    """

    return (
        soil_absorbed_radiation
        - topsoil_longwave_emission
        - topsoil_sensible_heat_flux
        - topsoil_latent_heat_flux
    )


def update_surface_temperature(
    topsoil_temperature: NDArray[np.float32],
    surface_net_radiation: NDArray[np.float32],
    surface_layer_depth: float | NDArray[np.float32],
    grid_cell_area: float,
    update_interval: Quantity,
    specific_heat_capacity_soil: float | NDArray[np.float32],
    volume_to_weight_conversion: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    """Update surface temperature after exchange of radiation.

    This function calculates the surface temperature after absorption of
    shortwave radiation, emission of longwave radiation, and surface fluxes. This
    process usually happens in the top few centimeters of the soil column, which is much
    less than the thickness of the upper soil layer of the current layer implementation.
    In the simulation flow, we therefor set the topsoil layer depth to 0.05, TODO merge
    this into temperature profile.

    Args:
        topsoil_temperature: Topsoil temperature
        surface_net_radiation: Longwave or shortwave radiation that enters
            (positive) or leaves (negative) the topsoil, [W m-2]
        surface_layer_depth: Topsoil layer depth, [m]
        grid_cell_area: Grid cell area, [m2]
        update_interval: Update interval to convert between W and J, [s]
        specific_heat_capacity_soil: Soil specific heat capacity, [J kg-1 K-1]
        volume_to_weight_conversion: Factor to convert between soil volume and weight in
            kilograms

    Returns:
        topsoil temperature
    """
    topsoil_mass = surface_layer_depth * grid_cell_area * volume_to_weight_conversion

    temperature_change = (surface_net_radiation * update_interval) / (
        topsoil_mass * specific_heat_capacity_soil
    )
    return topsoil_temperature + temperature_change


def calculate_soil_heat_balance(
    data: Data,
    topsoil_layer_index: int,
    update_interval: Quantity,
    abiotic_consts: AbioticConsts,
    core_consts: CoreConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate soil heat balance.

    * calculate soil absorption (RN * (1-albedo))
    * calculate sensible heat flux (convective flux from soil to atmosphere above)
    * calculate latent heat flux (conversion of soil evaporation)
    * calculate ground heat flux (conductive flux)
    * update topsoil temperature

    The function takes an instance of data object, AbioticConsts and CoreConsts which
    must provide the following inputs:

    * soil_temperature: Soil temperature
    * air_temperature: Air temperature
    * shortwave_radiation_surface: Shortwave radiation that reaches the surface below
        the canopy, [W m-2]
    * soil_evaporation: Soil evaporation, [mm]
    * soil_emissivity: Soil emissivity, dimensionless
    * surface_albedo: Surface albedo, dimensionless
    * molar_density_air: Molar density of air, [mol m-3]
    * specific_heat_air: Specific heat of air, [J mol-1 K-1]
    * aerodynamic_resistance_surface: Aerodynamic resistance near the surface
    * stefan_boltzmann: Stefan Boltzmann constant, [W m-2 K-4]
    * latent_heat_vaporisation: Latent heat of vaporisation, [kJ kg-1]
    * surface_layer_depth: Topsoil layer depth, [m]
    * grid_cell_area: Grid cell area, [m2]
    * specific_heat_capacity_soil: Soil specific heat capacity, [J kg-1 K-1]
    * volume_to_weight_conversion: Factor to convert between soil volume and weight in
        kilograms

    Args:
        data: instance if a data object
        update_interval: Update interval, [s]
        AbioticConsts: set of constants specific to abiotic model
        CoreConsts: set of constants that are shared across the model

    Returns:
        dictionnary with soil shortwave absorption, soil longwave emission, sensible and
            latent heat flux from the soil, ground heat flux, and updated topsoil
            temperature
    """

    output = {}

    soil_absorption = calculate_soil_absorption(
        shortwave_radiation_surface=data["shortwave_radiation_surface"].to_numpy(),
        surface_albedo=abiotic_consts.surface_albedo,
    )
    output["soil_absorption"] = soil_absorption

    longwave_emission_soil = calculate_longwave_emission(
        temperature=data["soil_temperature"][topsoil_layer_index].to_numpy(),
        emissivity=abiotic_consts.soil_emissivity,
        stefan_boltzmann=core_consts.stefan_boltzmann_constant,
    )
    output["longwave_emission_soil"] = longwave_emission_soil

    sensible_heat_flux_soil = calculate_sensible_heat_flux_soil(
        air_temperature_surface=(
            data["air_temperature"][topsoil_layer_index - 1].to_numpy()
        ),
        topsoil_temperature=data["soil_temperature"][topsoil_layer_index].to_numpy(),
        molar_density_air=data["molar_density_air"][topsoil_layer_index - 1].to_numpy(),
        specific_heat_air=data["specific_heat_air"][topsoil_layer_index - 1].to_numpy(),
        aerodynamic_resistance=data["aerodynamic_resistance_surface"].to_numpy(),
    )
    output["sensible_heat_flux_soil"] = sensible_heat_flux_soil

    latent_heat_flux_soil = calculate_latent_heat_flux_from_soil_evaporation(
        soil_evaporation=data["soil_evaporation"].to_numpy(),
        latent_heat_vaporisation=(
            data["latent_heat_vaporisation"][topsoil_layer_index - 1].to_numpy()
        ),
    )
    output["latent_heat_flux_soil"] = latent_heat_flux_soil

    ground_heat_flux = calculate_ground_heat_flux(
        soil_absorbed_radiation=soil_absorption,
        topsoil_longwave_emission=longwave_emission_soil,
        topsoil_sensible_heat_flux=sensible_heat_flux_soil,
        topsoil_latent_heat_flux=latent_heat_flux_soil,
    )
    output["ground_heat_flux"] = ground_heat_flux

    surface_net_radiation = (
        data["shortwave_radiation_surface"].to_numpy()
        - longwave_emission_soil
        - sensible_heat_flux_soil
        - latent_heat_flux_soil
        - ground_heat_flux
    )

    new_surface_temperature = update_surface_temperature(
        topsoil_temperature=data["soil_temperature"][topsoil_layer_index].to_numpy(),
        surface_net_radiation=surface_net_radiation,
        surface_layer_depth=abiotic_consts.surface_layer_depth,
        grid_cell_area=data.grid.cell_area,
        update_interval=update_interval,
        specific_heat_capacity_soil=abiotic_consts.specific_heat_capacity_soil,
        volume_to_weight_conversion=abiotic_consts.volume_to_weight_conversion,
    )
    output["new_surface_temperature"] = new_surface_temperature

    return output
