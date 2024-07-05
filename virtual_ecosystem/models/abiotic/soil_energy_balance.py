r"""The ``models.abiotic.soil_energy_balance`` module calculates the soil energy balance
for the Virtual Ecosystem.

The first part of this module determines the energy balance at the surface.
:func:`~virtual_ecosystem.models.abiotic.soil_energy_balance.calculate_soil_heat_balance`
calculates how incoming solar radiation that reaches the surface is partitioned in
sensible, latent, and ground heat flux. Further, longwave emission is calculated and the
topsoil temperature is updated.

The second part determines the soil temperature profile at different depths. We
divide the soil into discrete layers to numerically solve the time-dependent
differential equation that describes soil temperature as a function of depth
and time (see TODO THIS FUNCTION for details).
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from pint import Quantity

from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.abiotic.constants import AbioticConsts
from virtual_ecosystem.models.abiotic.energy_balance import calculate_longwave_emission


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
        shortwave_radiation_surface: Shortwave radiation that reaches surface, [W m-2]
        surface_albedo: Surface albedo, dimensionless.

    Returns:
        shortwave radiation absorbed by soil surface, [W m-2]
    """

    return shortwave_radiation_surface * (1 - surface_albedo)


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
    latent_heat_vapourisation: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate latent heat flux from soil evaporation.

    We assume that 1 mm of evaporated water is equivalent to 1 kg of water.

    Args:
        soil_evaporation: Soil evaporation, [mm]
        latent_heat_vapourisation: Latent heat of vapourisation, [J kg-1]

    Returns:
        latent heat flux from topsoil, [W m-2]
    """

    return soil_evaporation * latent_heat_vapourisation


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
    In the simulation flow, we therefore set the topsoil layer depth to 0.05, TODO merge
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
        topsoil temperature, [C]
    """
    # Calculate the mass of the soil that is absorbing the radiation
    topsoil_mass = surface_layer_depth * grid_cell_area * volume_to_weight_conversion

    # Convert radiation to energy stored in soil in Kelvin
    temperature_change = (surface_net_radiation * update_interval) / (
        topsoil_mass * specific_heat_capacity_soil
    )

    # Add temperature change to current top soil temperature
    return topsoil_temperature + temperature_change


def calculate_soil_heat_balance(
    data: Data,
    time_index: int,
    layer_structure: LayerStructure,
    update_interval: Quantity,
    abiotic_consts: AbioticConsts,
    core_consts: CoreConsts,
) -> dict[str, NDArray[np.float32]]:
    """Calculate soil heat balance.

    This function performs a series of calculations to solve the energy balance at the
    surface at the interface between soil and atmoshere:

    * calculate soil absorption (:math:`R_{N{} * (1-albedo)`)
    * calculate sensible heat flux (convective flux from soil to atmosphere above)
    * calculate latent heat flux (conversion of soil evaporation)
    * calculate ground heat flux (conductive flux)
    * update topsoil temperature

    The function takes an instance of data object, AbioticConsts and CoreConsts which
    must provide the following inputs:

    * soil_temperature: Soil temperature, [C]
    * air_temperature: Air temperature, [C]
    * topofcanopy_radiation: Shortwave radiation that reaches canopy, [W m-2]
    * soil_evaporation: Soil evaporation, [mm]
    * soil_emissivity: Soil emissivity, dimensionless
    * surface_albedo: Surface albedo, dimensionless
    * molar_density_air: Molar density of air, [mol m-3]
    * specific_heat_air: Specific heat of air, [J mol-1 K-1]
    * aerodynamic_resistance_surface: Aerodynamic resistance near the surface
    * stefan_boltzmann: Stefan Boltzmann constant, [W m-2 K-4]
    * latent_heat_vapourisation: Latent heat of vapourisation, [kJ kg-1]
    * surface_layer_depth: Topsoil layer depth, [m]
    * grid_cell_area: Grid cell area, [m2]
    * specific_heat_capacity_soil: Soil specific heat capacity, [J kg-1 K-1]
    * volume_to_weight_conversion: Factor to convert between soil volume and weight [kg]

    Args:
        data: The core data object
        time_index: time index
        update_interval: Update interval, [s]
        layer_structure: The LayerStructure instance for the simulation.
        abiotic_consts: set of constants specific to abiotic model
        core_consts: set of constants that are shared across the model

    Returns:
        A dictionary with soil shortwave absorption, soil longwave emission, sensible
        and latent heat flux from the soil, ground heat flux, and updated topsoil
        temperature
    """

    topsoil_layer_index = layer_structure.index_topsoil
    surface_layer_index = layer_structure.index_surface

    output = {}

    # Calculate soil absorption of shortwave radiation, [W m-2]
    shortwave_radiation_surface = data["topofcanopy_radiation"].isel(
        time_index=time_index
    ) - (data["canopy_absorption"].sum(dim="layers"))
    soil_absorption = calculate_soil_absorption(
        shortwave_radiation_surface=shortwave_radiation_surface.to_numpy(),
        surface_albedo=abiotic_consts.surface_albedo,
    )
    output["soil_absorption"] = soil_absorption
    output["shortwave_radiation_surface"] = shortwave_radiation_surface.to_numpy()

    # Calculate longwave emission from topsoil, [W m-2]; note that this is the soil
    # temperature of the previous time step
    # VIVI - all of the subsets extract a 2D (1, n_cells) array, and they are intended
    # to end up as a 1D (n_cells) array in the data, so I'm using squeeze() to simplify
    # them to 1D. Could use [0] - it's shorter and maybe more efficient, but it's less
    # obvious?
    longwave_emission_soil = calculate_longwave_emission(
        temperature=data["soil_temperature"][topsoil_layer_index].to_numpy().squeeze(),
        emissivity=abiotic_consts.soil_emissivity,
        stefan_boltzmann=core_consts.stefan_boltzmann_constant,
    )
    output["longwave_emission_soil"] = longwave_emission_soil

    # Calculate sensible heat flux from soil to lowest atmosphere layer, [W m-2]
    sensible_heat_flux_soil = calculate_sensible_heat_flux_soil(
        air_temperature_surface=data["air_temperature"][surface_layer_index]
        .to_numpy()
        .squeeze(),
        topsoil_temperature=data["soil_temperature"][topsoil_layer_index]
        .to_numpy()
        .squeeze(),
        molar_density_air=data["molar_density_air"][surface_layer_index]
        .to_numpy()
        .squeeze(),
        specific_heat_air=data["specific_heat_air"][surface_layer_index]
        .to_numpy()
        .squeeze(),
        aerodynamic_resistance=data["aerodynamic_resistance_surface"].to_numpy(),
    )
    output["sensible_heat_flux_soil"] = sensible_heat_flux_soil

    # Convert soil evaporation to latent heat flux to lowest atmosphere layer, [W m-2]
    latent_heat_flux_soil = calculate_latent_heat_flux_from_soil_evaporation(
        soil_evaporation=data["soil_evaporation"].to_numpy(),
        latent_heat_vapourisation=(
            data["latent_heat_vapourisation"][surface_layer_index].to_numpy().squeeze()
        ),
    )
    output["latent_heat_flux_soil"] = latent_heat_flux_soil

    # Determine ground heat flux as the difference as
    # incoming radiation -  sensible and latent heat flux - longwave emission
    ground_heat_flux = calculate_ground_heat_flux(
        soil_absorbed_radiation=soil_absorption,
        topsoil_longwave_emission=longwave_emission_soil,
        topsoil_sensible_heat_flux=sensible_heat_flux_soil,
        topsoil_latent_heat_flux=latent_heat_flux_soil,
    )
    output["ground_heat_flux"] = ground_heat_flux

    # Calculate net surface radiation, [W m-2]
    surface_net_radiation = (
        data["shortwave_radiation_surface"].to_numpy()
        - longwave_emission_soil
        - sensible_heat_flux_soil
        - latent_heat_flux_soil
        - ground_heat_flux
    )

    # Update surface temperature, [C]
    new_surface_temperature = update_surface_temperature(
        topsoil_temperature=data["soil_temperature"][topsoil_layer_index]
        .to_numpy()
        .squeeze(),
        surface_net_radiation=surface_net_radiation,
        surface_layer_depth=abiotic_consts.surface_layer_depth,
        grid_cell_area=data.grid.cell_area,
        update_interval=update_interval,
        specific_heat_capacity_soil=abiotic_consts.specific_heat_capacity_soil,
        volume_to_weight_conversion=abiotic_consts.volume_to_weight_conversion,
    )
    output["new_surface_temperature"] = new_surface_temperature

    return output


# def calculate_soil_temnperature_profile():
#     r"""
#     Each layer
#     is assigned a node, :math:`i`, at depth, :math:`z_{i}`, and with heat storage,
#     :math:`C_{h_{i}}`, and nodes are numbered sequentially downward such that node
#    :math:`i+1` represents the node for the soil layer immediately below. Conductivity,
#     :math:`k_{i}`, represents conductivity between nodes :math:`i` and :math:`i+1`.
#     The energy balance equation for node :math:`i` is then given by

#     .. math::
#         \kappa_{i}(T_{i+1} - T_{i})- \kappa_{i-1}(T_{i} - T_{i-1})
#         = \frac{C_{h_{i}}(T_{i}^{j+1} - T_{i}^{j})(z_{i+1} - z_{i-1})}{2 \Delta t}

#     where :math:`\Delta t` is the time increment, conductance,
#     :math:`\kappa_{i}=k_{i}/(z_{i+1} - z_{i})`, and superscript :math:`j` indicates
#     the time at which temperature is determined. This equation can be re-arranged and
#     solved for :math:`T_{j+1}` by Gaussian elimination using the Thomas algorithm."""
