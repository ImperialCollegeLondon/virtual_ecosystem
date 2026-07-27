r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Ecosystem. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly.
(For application where very fine-temporal resolution data might be needed, heat and
vapour exchange must be modelled as transient processes, and heat storage by the canopy,
and the exchange of heat between different layers of the canopy, must be considered
explicitly, see :cite:t:`maclean_microclimc_2021`. This is currently not implemented.)

Under steady-state, the balance equation :math:`\frac{dQ}{dt}` for the leaves in each
canopy layer is as
follows (after :cite:t:`maclean_microclimc_2021`):

.. math::
    \frac{dQ}{dt}
    = R_{abs} - R_{em} - H - \lambda E - PP
    = R_{abs} - \epsilon_{l} \sigma T_{l}^{4} - \frac{\rho_{a} c_p}{r_a}(T_{l} - T_{a})
    - \lambda g_{v} \frac {e_{l} - e_{a}}{p_{a}} - PP = 0

where :math:`R_{abs}` is absorbed shortwave and longwave radiation, :math:`R_{em}`
emitted radiation, :math:`H`
the sensible heat flux, :math:`\lambda E` the latent heat flux, :math:`\epsilon_{l}` the
emissivity of the leaf, :math:`\sigma` the Stefan-Boltzmann constant, :math:`T_{l}` the
absolute temperature of the leaf, :math:`T_{a}` the absolute temperature of the air
surrounding the leaf, :math:`\lambda` the latent heat of vapourisation of water,
:math:`e_{l}` the effective vapour pressure of the leaf, :math:`e_{a}` the vapour
pressure of air and :math:`p_{a}` atmospheric pressure. :math:`\rho_a` is the density of
air, :math:`c_{p}` is the specific heat capacity of air
at constant pressure, :math:`r_{a}` is the aerodynamic resistance of the surface (leaf
or soil), :math:`g_{v}` represents the conductivity for vapour loss from the leaves as a
function of the stomatal conductivity, :math:`PP` stands for primary productivity.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a secant method to iteratively solve the energy
balance for the canopy temperature. The air temperature is updated based on the
sensible heat flux from the canopy and soil in equilibrium, and vertical mixing of air
between layers.

Atmospheric humidity is also mixed vertically between atmospheric layers.
Advection at the top of the canopy is currently not considered as we don't have
have horizontal exchange between grid cells and air above canopy values would be
unrealistic.

"""  # noqa: D205, D415

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.model_config import CoreConstants
from virtual_ecosystem.models.abiotic.abiotic_tools import (
    compute_weights_from_absorbed_radiation,
    find_last_valid_row,
    set_unintended_nan_to_zero,
)
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants


def initialise_canopy_and_soil_fluxes(
    layer_structure: LayerStructure,
    initial_flux_value: float,
) -> dict[str, DataArray]:
    """Initialise canopy temperature and energy fluxes.

    This function initializes the following variables to run the first step of the
    energy balance routine: sensible and latent heat flux (canopy and soil), and ground
    heat flux, all in [W m-2].

    Args:
        air_temperature: Air temperature, [C]
        layer_structure: Instance of LayerStructure
        light_extinction_coefficient: Light extinction coefficient for canopy, unitless
        initial_flux_value: Initial non-zero flux, [W m-2]

    Returns:
        Dictionary with sensible and latent heat flux (canopy and soil), [W m-2],
        and ground heat flux, [W m-2].
    """

    output = {}

    # Base flux template (non-zero minimum)
    base_flux = layer_structure.from_template()
    base_flux[layer_structure.index_flux_layers] = initial_flux_value

    # Fluxes that share the same structure
    for name in (
        "sensible_heat_flux",
        "latent_heat_flux",
        "longwave_emission",
    ):
        output[name] = base_flux.copy()

    # 1D fluxes (cell-wise)
    output["ground_heat_flux"] = DataArray(
        np.full(base_flux.sizes["cell_id"], initial_flux_value),
        dims="cell_id",
    )
    return output


def calculate_longwave_emission(
    temperature: NDArray[np.floating],
    emissivity: float | NDArray[np.floating],
    stefan_boltzmann: float,
) -> NDArray[np.floating]:
    """Calculate longwave emission using the Stefan Boltzmann law.

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


def calculate_sensible_heat_flux(
    density_air: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    air_temperature: NDArray[np.floating],
    surface_temperature: NDArray[np.floating],
    aerodynamic_resistance: float | NDArray[np.floating],
) -> NDArray[np.floating]:
    r"""Calculate sensible heat flux.

    The sensible heat flux :math:`H` is calculated using the following equation:

    .. math::
        H = \frac{\rho_{a} c_{p}}{r_{a}} (T_{s} - T_{a})

    where :math:`\rho_{a}` is the density of air, :math:`c_{p}` is the specific heat
    capacity of air at constant pressure, :math:`r_{a}` is the aerodynamic resistance of
    the surface, :math:`T_{s}` is the surface temperature, and :math:`T_{a}` is the air
    temperature.

    Args:
        density_air: Density of air, [kg m-3]
        specific_heat_air: Specific heat of air, [J kg-1 K-1]
        air_temperature: Air temperature, [C]
        surface_temperature: Surface temperature (canopy or soil), [C]
        aerodynamic_resistance: Aerodynamic resistance, [s m-1]

    Returns:
        sensible heat flux, [W m-2]
    """
    return (density_air * specific_heat_air / aerodynamic_resistance) * (
        surface_temperature - air_temperature
    )


def calculate_absorbed_longwave_radiation(
    downward_longwave: NDArray[np.floating],
    leaf_area_index: NDArray[np.floating],
    leaf_emissivity: float,
    soil_emissivity: float,
    extinction_coefficient_lw: float,
    surface_index: int,
    topsoil_index: int,
) -> NDArray[np.floating]:
    """Calculate absorbed longwave radiation per layer using Beer-Lambert attenuation.

    Each canopy layer absorbs downward longwave attenuated from above. The surface
    layer receives the remainder after full canopy attenuation. The topsoil receives
    what the surface layer transmitted.

    Upward longwave from the soil is NOT included here — it is already accounted
    for in calculate_soil_fluxes via longwave_emission_soil, which drives the
    ground heat flux and soil sensible heat flux to the surface air layer.
    Including it here would double-count the soil longwave emission.

    Args:
        downward_longwave: Downward longwave at top of canopy [W m-2], shape (cells,)
        leaf_area_index: LAI per layer, shape (layers, cells), NaN for empty layers
        leaf_emissivity: Leaf emissivity, dimensionless
        soil_emissivity: Soil emissivity, dimensionless
        extinction_coefficient_lw: Longwave extinction coefficient, typically ~0.5
        surface_index: Row index of surface layer
        topsoil_index: Row index of topsoil layer

    Returns:
        Absorbed longwave radiation per layer, shape (layers, cells) [W m-2].
    """
    n_layers, n_cells = leaf_area_index.shape
    absorbed = np.zeros((n_layers, n_cells))

    cumulative_lai = np.zeros(n_cells)
    arriving = downward_longwave.copy().astype(float)

    for layer in range(n_layers):
        lai = np.nan_to_num(leaf_area_index[layer], nan=0.0)

        if layer == surface_index:
            # Downward sky LW attenuated through full canopy above
            transmittance = np.exp(-extinction_coefficient_lw * cumulative_lai)
            arriving_down = downward_longwave * transmittance
            absorbed[layer] = leaf_emissivity * arriving_down

            # What passes through to soil
            arriving = (1.0 - leaf_emissivity) * arriving_down

        elif layer == topsoil_index:
            # Soil absorbs what the surface layer transmitted
            absorbed[layer] = soil_emissivity * arriving

        else:
            transmittance_above = np.exp(-extinction_coefficient_lw * cumulative_lai)
            transmittance_below = np.exp(
                -extinction_coefficient_lw * (cumulative_lai + lai)
            )

            absorbed[layer] = np.where(
                lai > 0,
                leaf_emissivity
                * downward_longwave
                * (transmittance_above - transmittance_below),
                0.0,
            )

            cumulative_lai += lai

    return absorbed


def update_soil_temperature(
    ground_heat_flux: NDArray[np.floating],
    soil_temperature: NDArray[np.floating],
    soil_layer_thickness: NDArray[np.floating],
    soil_thermal_conductivity: float | NDArray[np.floating],
    soil_bulk_density: float | NDArray[np.floating],
    specific_heat_capacity_soil: float | NDArray[np.floating],
    time_interval: float,
) -> NDArray[np.floating]:
    r"""Update soil temperature using heat diffusion.

    The function applies an explicit finite-difference approach to update
    soil temperatures based on thermal diffusivity and heat flux.

    Governing equations:

    Soil thermal diffusivity:

    .. math::
        \alpha = \frac{\lambda}{\rho_s c_s}

    where :math:`\lambda` is the soil thermal conductivity [W m-1 K-1],
    :math:`\rho_s` is the soil bulk density [kg m-3], :math:`c_s` is the specific heat
    capacity of soil [J kg-1 K-1].

    Internal layer update:

    .. math::
        T_i^{t+\Delta t} = T_i^t + (\Delta t / \Delta z^2)
        * \alpha * (T_{i+1}^t - 2T_i^t + T_{i-1}^t)

    Top layer update with ground heat flux:

    .. math::
        T_0^{t+\Delta t} = T_0^t + (\Delta t / (\rho_s c_s \Delta z)) * G

    No-heat-flux bottom boundary condition:

    .. math::
        T_{n-1}^{t+\Delta t} = T_{n-1}^t + (\Delta t / \Delta z^2)
        * \alpha * (T_{n-2}^t - T_{n-1}^t)

    Args:
        ground_heat_flux: Ground heat flux at top soil, [W m-2]
        soil_temperature: Soil temperature for each soil layer, [C]
        soil_thermal_conductivity: Thermal conductivity of soil, [W m-2 K-1]
        soil_bulk_density: Soil bulk density, [kg m-3]
        specific_heat_capacity_soil: Specific heat capacity of soil, [J kg-1 K-1]
        soil_layer_thickness: Thickness of each soil layer, [m]
        time_interval: Time interval, [s]

    Returns:
        Updated soil temperatures, [C]
    """

    n_layers = len(soil_temperature)

    # Soil thermal diffusivity, [m2 s-1]
    soil_thermal_diffusivity = soil_thermal_conductivity / (
        soil_bulk_density * specific_heat_capacity_soil
    )

    # Update internal layers using diffusion
    for i in range(1, n_layers - 1):
        soil_temperature[i, :] += (
            (time_interval / soil_layer_thickness[i] ** 2)
            * soil_thermal_diffusivity
            * (
                soil_temperature[i + 1, :]
                - 2 * soil_temperature[i, :]
                + soil_temperature[i - 1, :]
            )
        )

    # Update top layer with ground heat flux
    soil_temperature[0, :] += (
        time_interval
        / (soil_bulk_density * specific_heat_capacity_soil * soil_layer_thickness[0])
    ) * ground_heat_flux

    # No heat flux boundary at the bottom (insulation assumption)
    soil_temperature[-1, :] += (
        (time_interval / soil_layer_thickness[-1] ** 2)
        * soil_thermal_diffusivity
        * (soil_temperature[-2, :] - soil_temperature[-1, :])
    )

    return soil_temperature


def calculate_energy_balance_residual(
    canopy_temperature_initial: NDArray[np.floating],
    air_temperature: NDArray[np.floating],
    evapotranspiration: NDArray[np.floating],
    absorbed_shortwave_radiation: NDArray[np.floating],
    absorbed_longwave_radiation: NDArray[np.floating],
    longwave_emission_soil: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    density_air: NDArray[np.floating],
    aerodynamic_resistance: NDArray[np.floating],
    latent_heat_vapourisation: NDArray[np.floating],
    leaf_emissivity: float,
    stefan_boltzmann_constant: float,
    zero_Celsius: float,
    seconds_to_hour: float,
    return_fluxes: bool,
    idx: SimpleNamespace,
) -> NDArray[np.floating] | dict[str, NDArray[np.floating]]:
    r"""Calculate energy balance residual for canopy.

    The energy balance residual (:math:`\frac{dQ}{dt}`) for the canopy is given by:

    .. math::
        \frac{dQ}{dt} = R_{abs} - \epsilon_{l} \sigma T_{l}^{4} - H - \lambda E - PP

    Where :math:`R_abs` is the absorbed shortwave and longwave radiation by the canopy,
    :math:`\epsilon_{l}` is the leaf emissivity, :math:`\sigma` is the Stefan-Boltzmann
    constant, :math:`T_{l}` is the leaf temperature, :math:`H` is the sensible heat
    flux from the canopy, :math:`\lambda E` is the latent heat flux from the canopy,
    :math:`PP` is a fraction of the absorbed light is used in photosynthesis (PAR).

    Args:
        canopy_temperature_initial: Initial leaf temperature for all canopy layers, [C]
        air_temperature: Initial air temperature in canopy layers, [C]
        evapotranspiration: Evapotranspiration, [mm]
        absorbed_shortwave_radiation: Absorbed shortwave radiation for all canopy
            layers, [W m-2]
        absorbed_longwave_radiation: Absorbed longwave radiation for all canopy layers,
            [W m-2]
        longwave_emission_soil: Longwave emission from topsoil, [W m-2]
        specific_heat_air: Specific heat capacity of air, [J kg-1 K-1]
        density_air: Density of air, [kg m-3]
        aerodynamic_resistance: Aerodynamic resistance of canopy, [s m-1]
        latent_heat_vapourisation: Latent heat of vapourisation, [J kg-1]
        leaf_emissivity: Leaf emissivity, dimensionless
        stefan_boltzmann_constant: Stefan Boltzmann constant, [W m-2 K-4]
        zero_Celsius: Factor to convert between Celsius and Kelvin
        seconds_to_hour: Factor to convert between hours and seconds
        return_fluxes: Flag to indicate if all components of the energy balance should
            be returned. This is false for the newton approach to solve for canopy
            temperature, but true to create the outputs in a second call afterwards.
        idx: Namespace containing indices for different layers.

    Returns:
        full energy balance or energy balance residual, [W m-2]
    """

    # Longwave emission from canopy, [W m-2]
    longwave_emission_canopy = calculate_longwave_emission(
        temperature=canopy_temperature_initial + zero_Celsius,
        emissivity=leaf_emissivity,
        stefan_boltzmann=stefan_boltzmann_constant,
    )

    #  Sensible heat flux from canopy layers, [W m-2]
    sensible_heat_flux_canopy = calculate_sensible_heat_flux(
        density_air=density_air,
        specific_heat_air=specific_heat_air,
        air_temperature=air_temperature,
        surface_temperature=canopy_temperature_initial,
        aerodynamic_resistance=aerodynamic_resistance,
    )

    # Latent heat flux canopy, [W m-2]
    # The current implementation converts outputs from plant and hydrology model to
    # ensure energy conservation between modules for now.
    latent_heat_flux_canopy = calculate_latent_heat_flux(
        evapotranspiration=evapotranspiration,
        latent_heat_vapourisation=latent_heat_vapourisation,
        time_interval=seconds_to_hour,
    )

    # Net radiation, [W m-2]
    net_radiation = (
        absorbed_shortwave_radiation
        + absorbed_longwave_radiation
        - longwave_emission_canopy
    )
    # Energy balance residual, [W m-2]
    energy_balance_residual = (
        absorbed_shortwave_radiation
        + absorbed_longwave_radiation
        - longwave_emission_canopy
        - sensible_heat_flux_canopy
        - latent_heat_flux_canopy
    )
    # Add longwave_emission from surface to net radiation and energy balance residual
    net_radiation[idx.surface] += 0.5 * longwave_emission_soil
    energy_balance_residual[idx.surface] += 0.5 * longwave_emission_soil

    if return_fluxes:
        energy_balance = {
            "longwave_emission": longwave_emission_canopy,
            "sensible_heat_flux": sensible_heat_flux_canopy,
            "latent_heat_flux": latent_heat_flux_canopy,
            "energy_balance_residual": energy_balance_residual,
            "net_radiation": net_radiation,
        }
        return energy_balance
    else:
        return energy_balance_residual


def update_canopy_air_temperature(
    air_temperature: NDArray[np.floating],
    sensible_heat_flux: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    density_air: NDArray[np.floating],
    mixing_layer_thickness: NDArray[np.floating],
) -> NDArray[np.floating]:
    r"""Update air temperature surrounding canopy in steady state.

    The new air temperature :math:`T_{a}^{new}` is updated following
    :cite:t:`bonan_climate_2019`:

    .. math ::
        H = \frac{\rho_a c_p}{r_a}(T_{l} - T_{a})

    and

    .. math::
        T_{a}^{new} = T_{a}^{old} + \frac{H}{\rho_a c_p z}

    where :math:`\rho_{a}` is the density of air, :math:`c_{p}` is the specific heat
    capacity of air at constant pressure, :math:`r_{a}` is the aerodynamic resistance of
    the surface, :math:`T_{s}` is the surface temperature, :math:`T_{a}` is the air
    temperature, and :math:`z` is the thickness of the air layer we are updating.

    Args:
        air_temperature: Air temperature, [C]
        sensible_heat_flux: Sensible heat flux, [W m-2]
        specific_heat_air: Specific heat capacity of air, [J kg-1 K-1]
        density_air: Density of air, [kg m-3]
        mixing_layer_thickness: thickness of the air layer we are updating, [m]

    Returns:
        updated air temperatures, [C]
    """

    # Update air temperature over a layer of height z (e.g., canopy height)
    new_air_temperature = air_temperature + (
        sensible_heat_flux / (density_air * specific_heat_air * mixing_layer_thickness)
    )
    return new_air_temperature


def update_surface_air_temperature(
    canopy_air_temperature: NDArray[np.floating],
    state: dict[str, NDArray[np.floating]],
    idx: SimpleNamespace,
    denominator_tolerance: float,
):
    """Update surface air temperature in equilibrium with soil and canopy fluxes.

    The surface air temperature is diagnosed from the soil and canopy bottom
    conductances and temperatures, assuming equilibrium between the soil and canopy
    fluxes. This is necessary because the surface layer is too thin to be updated based
    on fluxes over a 1-hour timestep, and we want to avoid unrealistic surface air
    temperatures that would arise from a flux-based update.

    For cells with fewer canopy layers, the bottom canopy temperature is the last
    finite value in the canopy temperature array. For cells with no canopy, the
    above-canopy reference temperature is used instead.

    Args:
        canopy_air_temperature: Canopy air temperature, [C]
        state: Dictionary of state variables
        idx: Layer structure index
        denominator_tolerance: Small value to prevent division by zero

    Returns:
        Updated surface air temperature, [C]
    """

    # Last finite canopy temperature per cell — bottom-most occupied canopy layer
    # Returns NaN for cells with no canopy
    canopy_bottom_temperature = find_last_valid_row(canopy_air_temperature)

    # For cells with no canopy, fall back to above-canopy reference (row 0)
    has_canopy = np.isfinite(canopy_bottom_temperature)
    canopy_bottom_temperature = np.where(
        has_canopy,
        canopy_bottom_temperature,
        state["air_temperature"][0],  # above-canopy reference
    )

    # Conductance-weighted average of soil and canopy bottom temperatures
    g_soil = 1.0 / np.maximum(
        state["aerodynamic_resistance_soil"], denominator_tolerance
    )
    g_canopy = 1.0 / np.maximum(
        state["aerodynamic_resistance_canopy"], denominator_tolerance
    )

    surface_air_temperature = (
        g_soil * state["soil_temperature"][idx.topsoil]
        + g_canopy * canopy_bottom_temperature
    ) / (g_soil + g_canopy)

    return surface_air_temperature


def update_specific_humidity(
    evapotranspiration: NDArray[np.floating],
    soil_evaporation: NDArray[np.floating],
    specific_humidity: NDArray[np.floating],
    layer_thickness: NDArray[np.floating],
    density_air: NDArray[np.floating],
    mm_to_kg: float,
    cell_area: float,
    time_interval: float,
    surface_index: int,
) -> NDArray[np.floating]:
    """Update specific humidity from evapotranspiration and soil evaporation.

    This function adds the water from soil evaporation and canopy evapotranspiration to
    each atmospheric layer. No limits are applied at this stage and no vertical mixing.

    Args:
        evapotranspiration: Evapotranspiration, [mm]
        soil_evaporation: Soil evaporation to surface layer, [mm]
        saturated_vapour_pressure: Saturated vapour pressure, [kPa]
        specific_humidity: Specific humidity, [kg kg-1]
        layer_thickness: Layer thickness, [m]
        density_air: Density of air, [kg m-3]
        mm_to_kg: Factor to convert variable unit from millimeters to kilograms of
            water per square meter
        cell_area: Grid cell area, [m2]
        time_interval: Time interval, [s]
        surface_index: Index of surface layer

    Returns:
        update specific_humidity, [kg kg-1]
    """

    # Convert evapotranspiration and soil evaporation [mm] to [kg m2 s-1] time interval
    evapotranspiration_kg_m2 = evapotranspiration * mm_to_kg / time_interval
    soil_evap_kg_m2 = soil_evaporation * mm_to_kg / time_interval

    # Calculate air layer volumes [m3]
    layer_volumes = layer_thickness * cell_area
    air_mass_per_layer = layer_volumes * density_air

    # Add ET and soil evaporation as mass flux [kg]
    added_mass = np.zeros_like(layer_thickness)
    added_mass += evapotranspiration_kg_m2 * cell_area * time_interval
    added_mass[surface_index] += soil_evap_kg_m2 * cell_area * time_interval

    # Update water mass in air
    water_mass_in_air = specific_humidity * air_mass_per_layer
    water_mass_in_air += added_mass

    # Convert back to specific humidity and fill layer above with reference value
    specific_humidity_out = water_mass_in_air / air_mass_per_layer
    specific_humidity_out[0, :] = specific_humidity[0, :]

    return specific_humidity_out


def update_humidity_vpd(
    saturated_vapour_pressure: NDArray[np.floating],
    specific_humidity_mixed: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    layer_thickness: NDArray[np.floating],
    molecular_weight_ratio_water_to_dry_air: float,
    dry_air_factor: float,
    density_air: NDArray[np.floating],
    cell_area: float,
    limits_relative_humidity: tuple[float, float, float],
    limits_vapour_pressure_deficit: tuple[float, float, float],
    denominator_tolerance: float,
) -> dict[str, NDArray[np.floating]]:
    """Update atmospheric humidity and vapour pressure deficit.

    Args:
        saturated_vapour_pressure: Saturated vapour pressure, [kPa]
        specific_humidity_mixed: Specific humidity vertically mixed, [kg kg-1]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        layer_thickness: Layer thickness, [m]
        molecular_weight_ratio_water_to_dry_air: Molecular weight ratio of water to dry
            air, dimensionless
        dry_air_factor: Complement of water_to_air_mass_ratio, accounting for dry air
        density_air: Density of air, [kg m-3]
        cell_area: Grid cell area, [m2]
        limits_relative_humidity: Realistic bounds of relative humidity, []
        limits_vapour_pressure_deficit: Realistic bounds for vapour pressure deficit,
            [kPa]
        denominator_tolerance: Small value to prevent division by zero


    Returns:
      A dictionary containing arrays of updated ``relative_humidity``,
      ``specific_humidity``, ``vapour_pressure`` and ``vapour_pressure_deficit`` values.
    """

    # Create a mask of where the input was NaN (no true canopy)
    input_nan_mask = np.isnan(specific_humidity_mixed)

    # Calculate air layer volumes [m3]
    layer_volumes = layer_thickness * cell_area
    air_mass_per_layer = layer_volumes * density_air

    # Saturation constraint and condensation
    # Saturation specific humidity
    saturation_specific_humidity = (
        molecular_weight_ratio_water_to_dry_air
        + dry_air_factor * saturated_vapour_pressure
    ) / np.maximum(
        atmospheric_pressure - saturated_vapour_pressure, denominator_tolerance
    )

    # Negative values mean supersaturation
    specific_humidity_deficit = saturation_specific_humidity - specific_humidity_mixed

    # Excess humidity available for condensation, [kg kg-1]
    excess_specific_humidity = np.where(
        specific_humidity_deficit > 0,
        0.0,
        specific_humidity_deficit,
    )

    # Convert excess to condensed water, [mm]
    condensed_water_mass = -excess_specific_humidity * air_mass_per_layer

    # Convert to equivalent water depth, [mm]
    condensation_mm = condensed_water_mass / cell_area

    # Remove excess from air, not the sign of the excess is negative
    specific_humidity_updated = specific_humidity_mixed + excess_specific_humidity

    # Vapour pressure [kPa]
    vapour_pressure_updated = (specific_humidity_updated * atmospheric_pressure) / (
        molecular_weight_ratio_water_to_dry_air
        + dry_air_factor * specific_humidity_updated
    )

    # Compute new relative humidity (%)
    relative_humidity_updated = (
        vapour_pressure_updated
        / np.maximum(saturated_vapour_pressure, denominator_tolerance)
    ) * 100

    relative_humidity_updated = np.minimum(
        relative_humidity_updated, limits_relative_humidity[1]
    )

    # Compute new VPD (Vapour Pressure Deficit) [kPa], ensure non-zero
    vpd_updated = saturated_vapour_pressure - vapour_pressure_updated
    vpd_updated = np.maximum(vpd_updated, limits_vapour_pressure_deficit[0])

    # Map variable names to arrays
    raw_outputs = {
        "relative_humidity": relative_humidity_updated,
        "vapour_pressure": vapour_pressure_updated,
        "vapour_pressure_deficit": vpd_updated,
        "specific_humidity": specific_humidity_updated,
        "condensation": condensation_mm,
    }

    # Clean outputs while preserving intended NaNs
    cleaned_outputs = {
        key: set_unintended_nan_to_zero(arr, input_nan_mask)
        for key, arr in raw_outputs.items()
    }

    return cleaned_outputs


def calculate_latent_heat_flux(
    evapotranspiration: NDArray[np.floating],
    latent_heat_vapourisation: NDArray[np.floating],
    time_interval: float,
) -> NDArray[np.floating]:
    """Calculate latent heat flux from evapotranspiration.

    Args:
        evapotranspiration: Evapotranspiration per unit area, [kg m-2]
            (1 kg m-2 of water = 1 mm of water)
        latent_heat_vapourisation: Latent heat of vaporisation of water, [J kg-1]
        time_interval: Time interval over which flux is computed, [s]

    Returns:
        Latent heat flux, [W m-2]
    """
    # Energy transferred as latent heat [J m-2] over the time interval
    energy_j_per_m2 = evapotranspiration * latent_heat_vapourisation

    # Convert to flux [W m-2] by dividing by time interval [s]
    latent_heat_flux = energy_j_per_m2 / time_interval

    return latent_heat_flux


def calculate_total_absorbed_shortwave_radiation(
    downward_shortwave_radiation: NDArray[np.floating],
    shortwave_absorption_by_canopy: NDArray[np.floating],
    fraction_par_used: float,
    leaf_absorptance_non_par: float,
    par_fraction: float,
) -> NDArray[np.floating]:
    """Compute total absorbed shortwave radiation contributing to leaf energy balance.

    Shortwave (SW) radiation is partitioned into:
      - PAR (photosynthetically active radiation)
      - non-PAR (primarily near-infrared, NIR)

    The plant model provides absorbed PAR. A fraction of this PAR is used
    in photosynthesis, while the remainder contributes to heat. Non-PAR radiation
    is assumed not to be used in photosynthesis and contributes entirely to heat
    after accounting for leaf absorptance.

    This function calculates the total absorbed shortwave radiation that contributes to
    the leaf energy balance by combining the absorbed PAR (adjusted for photosynthesis)
    and the absorbed non-PAR radiation (adjusted for leaf absorptance and vertical
    distribution).

    Args:
        downward_shortwave_radiation: Incoming shortwave radiation [W m-2]
        shortwave_absorption_by_canopy: Absorbed PAR by canopy [W m-2]
        fraction_par_used: Fraction of absorbed PAR used in photosynthesis (0-1).
        leaf_absorptance_non_par: Fraction of non-PAR radiation absorbed by the leaf
            (0-1).
        par_fraction: Fraction of total shortwave radiation that is PAR (0-1).

    Returns:
        Total absorbed shortwave radiation contributing to heat [W m-2]
    """

    # Compute vertical distribution weights based on absorbed PAR
    weights = compute_weights_from_absorbed_radiation(
        radiation=shortwave_absorption_by_canopy
    )

    # Calculate the portion of absorbed non-PAR that contributes to heat, assuming the
    # same vertical decay as PAR absorption (weights to distribute cross layers)
    shortwave_non_par = downward_shortwave_radiation * (1 - par_fraction)
    shortwave_non_par_absorbed = leaf_absorptance_non_par * shortwave_non_par * weights

    # Calculate the portion of absorbed PAR that contributes to heat after accounting
    # for photosynthesis
    # TODO: #1533 we want to use light use efficiency from the plant model to determine
    # the fraction of absorbed PAR used in photosynthesis; for now we use a constant
    # fraction.
    par_heat = shortwave_absorption_by_canopy * (1 - fraction_par_used)

    # Total absorbed shortwave radiation contributing to heat
    total_abs = par_heat + shortwave_non_par_absorbed

    return total_abs


def secant_solve_cells_layers(
    residual_function: Callable[[NDArray[np.floating]], NDArray[np.floating]],
    initial_guess: NDArray[np.floating],
    maxiter_secant: int,
    convergence_tolerance: float,
    small_perturbation_second_guess: float,
    denominator_tolerance: float,
) -> NDArray[np.floating]:
    """Vectorised secant solver for independent (cell, layer) root problems.

    Args:
        residual_function: Function f(T) returning residual with same shape as T.
        initial_guess: Initial guess canopy temperature, shape (n_cells, n_layers).
        maxiter_secant: Maximum secant iterations.
        convergence_tolerance: Convergence tolerance on max absolute update.
        small_perturbation_second_guess: Small perturbation for second initial guess.
        denominator_tolerance: Small value to prevent division by zero in secant update.

    Returns:
        Root estimate canopy temperature solving f(T)=0 elementwise.
    """

    previous_temperature = initial_guess.copy()
    current_temperature = initial_guess + small_perturbation_second_guess

    previous_residual = residual_function(previous_temperature)
    current_residual = residual_function(current_temperature)

    for _ in range(maxiter_secant):
        denom = current_residual - previous_residual

        # Ensure no division by zero and sign conserved
        safe_denom = np.where(
            np.abs(denom) < denominator_tolerance,
            np.copysign(denominator_tolerance, denom),
            denom,
        )

        denom = np.where(np.isnan(safe_denom), np.nan, safe_denom)

        next_temperature = (
            current_temperature
            - current_residual * (current_temperature - previous_temperature) / denom
        )

        next_residual = residual_function(next_temperature)

        max_update = np.nanmax(np.abs(next_temperature - current_temperature))

        if max_update < convergence_tolerance:
            return next_temperature

        previous_temperature, current_temperature = (
            current_temperature,
            next_temperature,
        )
        previous_residual, current_residual = (
            current_residual,
            next_residual,
        )

    return current_temperature


def make_canopy_residual(
    state: dict[str, Any],
    static: dict[str, Any],
    aerodynamic_resistance: NDArray[np.floating],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    idx: SimpleNamespace,
) -> Callable[[NDArray[np.floating]], NDArray[np.floating]]:
    """Creates a residual function for canopy temperature to be used in root finding.

    Args:
        state: Dictionary containing state variables needed for the energy balance
            residual.
        static: Dictionary containing static variables needed for the energy balance
            residual.
        aerodynamic_resistance: Aerodynamic resistance of canopy, [s m-1]
        abiotic_constants: Constants related to abiotic processes.
        core_constants: Core constants.
        idx: Namespace containing indices for different layers.

    Returns:
        A function that takes canopy_temperature as input and returns the energy balance
        residual.
    """

    def residual(canopy_temperature):
        return calculate_energy_balance_residual(
            canopy_temperature_initial=canopy_temperature,
            air_temperature=state["air_temperature"],
            evapotranspiration=state["evapotranspiration"],
            absorbed_shortwave_radiation=state["shortwave_absorption"],
            absorbed_longwave_radiation=static["absorbed_longwave_radiation"],
            longwave_emission_soil=state["longwave_emission"][idx.topsoil],
            specific_heat_air=state["specific_heat_air"],
            density_air=state["density_air"],
            aerodynamic_resistance=aerodynamic_resistance,
            latent_heat_vapourisation=state["latent_heat_vapourisation"],
            leaf_emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            zero_Celsius=core_constants.zero_Celsius,
            seconds_to_hour=core_constants.seconds_to_hour,
            return_fluxes=False,
            idx=idx,
        )

    return residual


def solve_canopy_temperature_with_air_coupling(
    state: dict[str, Any],
    static: dict[str, Any],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
    maxiter_air: int,
    air_temperature_tolerance: float,
    maxiter_secant: int,
    convergence_tolerance: float,
    small_perturbation_second_guess: float,
    denominator_tolerance: float,
    idx: SimpleNamespace,
) -> tuple[
    NDArray[np.floating],
    NDArray[np.floating],
    dict[str, NDArray[np.floating]],
]:
    """Solve canopy temperature with iterative air temperature coupling.

    The canopy temperature is solved with a secant method for fixed air temperature.
    Air temperature is then updated from sensible heat flux, and the process is
    repeated until both canopy and air temperatures converge.

    Args:
        state: Dictionary containing state variables needed for the energy balance
            residual.
        static: Dictionary containing static variables needed for the energy balance
            residual.
        abiotic_constants: Constants related to abiotic processes.
        core_constants: Core constants.
        maxiter_air: Maximum number of outer iterations for air temperature coupling.
        air_temperature_tolerance: Convergence tolerance on max absolute canopy/air
            temperature change, [C].
        maxiter_secant: Maximum secant iterations.
        convergence_tolerance: Convergence tolerance on max absolute secant update.
        small_perturbation_second_guess: Small perturbation for second initial guess.
        denominator_tolerance: Small value to prevent division by zero.
        idx: Namespace containing indices for different layers.

    Returns:
        Tuple of canopy temperature, air temperature, and final fluxes.
    """

    # Local working state container
    state_local = state.copy()

    # Solver-owned working arrays
    air_temperature = state["air_temperature"].copy()
    canopy_temperature = state["canopy_temperature"].copy()

    for _ in range(maxiter_air):
        # Update local state seen by the canopy residual for this outer iteration
        # state_local["air_temperature"] = air_temperature
        # state_local["canopy_temperature"] = canopy_temperature

        residual_function = make_canopy_residual(
            state=state_local,
            static=static,
            aerodynamic_resistance=state_local["aerodynamic_resistance_canopy"],
            abiotic_constants=abiotic_constants,
            core_constants=core_constants,
            idx=idx,
        )

        new_canopy_temperature = secant_solve_cells_layers(
            residual_function=residual_function,
            initial_guess=canopy_temperature,
            maxiter_secant=maxiter_secant,
            convergence_tolerance=convergence_tolerance,
            small_perturbation_second_guess=small_perturbation_second_guess,
            denominator_tolerance=denominator_tolerance,
        )

        fluxes = cast(
            dict[str, NDArray[np.floating]],
            calculate_energy_balance_residual(
                canopy_temperature_initial=new_canopy_temperature,
                air_temperature=air_temperature,
                evapotranspiration=state_local["evapotranspiration"],
                absorbed_shortwave_radiation=state_local["shortwave_absorption"],
                absorbed_longwave_radiation=static["absorbed_longwave_radiation"],
                longwave_emission_soil=state_local["longwave_emission"][idx.topsoil],
                specific_heat_air=state_local["specific_heat_air"],
                density_air=state_local["density_air"],
                aerodynamic_resistance=state_local["aerodynamic_resistance_canopy"],
                latent_heat_vapourisation=state_local["latent_heat_vapourisation"],
                leaf_emissivity=abiotic_constants.leaf_emissivity,
                stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
                zero_Celsius=core_constants.zero_Celsius,
                seconds_to_hour=core_constants.seconds_to_hour,
                return_fluxes=True,
                idx=idx,
            ),
        )

        new_air_temperature = update_canopy_air_temperature(
            air_temperature=air_temperature,
            sensible_heat_flux=fluxes["sensible_heat_flux"],  # type: ignore
            specific_heat_air=state_local["specific_heat_air"],
            density_air=state_local["density_air"],
            mixing_layer_thickness=static["geometry"]["thickness"],
        )

        canopy_change = np.nanmax(np.abs(new_canopy_temperature - canopy_temperature))
        air_change = np.nanmax(np.abs(new_air_temperature - air_temperature))

        canopy_temperature = new_canopy_temperature
        air_temperature = new_air_temperature

        if max(canopy_change, air_change) < air_temperature_tolerance:
            break

    # Final flux calculation at converged temperatures
    final_fluxes = cast(
        dict[str, NDArray[np.floating]],
        calculate_energy_balance_residual(
            canopy_temperature_initial=canopy_temperature,
            air_temperature=air_temperature,
            evapotranspiration=state_local["evapotranspiration"],
            absorbed_shortwave_radiation=state_local["shortwave_absorption"],
            absorbed_longwave_radiation=static["absorbed_longwave_radiation"],
            longwave_emission_soil=state_local["longwave_emission"][idx.topsoil],
            specific_heat_air=state_local["specific_heat_air"],
            density_air=state_local["density_air"],
            aerodynamic_resistance=state_local["aerodynamic_resistance_canopy"],
            latent_heat_vapourisation=state_local["latent_heat_vapourisation"],
            leaf_emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            zero_Celsius=core_constants.zero_Celsius,
            seconds_to_hour=core_constants.seconds_to_hour,
            return_fluxes=True,
            idx=idx,
        ),
    )

    return canopy_temperature, air_temperature, final_fluxes
