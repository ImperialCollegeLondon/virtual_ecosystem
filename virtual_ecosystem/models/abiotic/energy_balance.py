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

A challenge in solving this equation is the strong nonlinear dependence of emitted
longwave radiation and turbulent heat fluxes on leaf temperature. We therefore solve for
canopy temperature iteratively using a secant method. Because canopy and air
temperatures are coupled through sensible heat exchange, the surrounding air temperature
is also updated iteratively from canopy and soil fluxes, together with vertical mixing
between layers, until both canopy and air temperatures converge.

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
from virtual_ecosystem.core.logger import LOGGER
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
    energy balance routine: sensible and latent heat flux (canopy and soil), ground
    heat flux, and absorbed longwave radiation, all in [W m-2].

    Args:
        air_temperature: Air temperature, [C]
        layer_structure: Instance of LayerStructure
        light_extinction_coefficient: Light extinction coefficient for canopy, unitless
        initial_flux_value: Initial non-zero flux, [W m-2]

    Returns:
        Dictionary with sensible and latent heat flux (canopy and soil), [W m-2],
        ground heat flux, and absorbed longwave radiation [W m-2].
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
        "absorbed_longwave_radiation",
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


def normalised_source_fractions(
    cumulative_lai_above: NDArray[np.float64],
    cumulative_lai_below: NDArray[np.float64],
    longwave_extinction_coefficient: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Calculate normalised longwave source fractions from sky, soil, and vegetation.

    This helper estimates the relative contribution of three longwave radiation
    sources seen by a target layer:

    - sky radiation transmitted through vegetation above the layer,
    - soil radiation transmitted through vegetation below the layer,
    - surrounding vegetation radiation represented as the remaining fraction.

    The unnormalised sky and soil source terms are calculated as exponential
    transmissivities through the cumulative leaf area index above and below the
    target layer:

    - sky transmissivity decreases with increasing vegetation above,
    - soil transmissivity decreases with increasing vegetation below.

    The vegetation source fraction is then assigned as the remainder after sky
    and soil contributions, with all three fractions clipped to the range
    [0, 1]. Finally, the fractions are normalised so that, for each element,
    the sky, soil, and vegetation fractions sum to 1 whenever the total
    source weight is positive.

    Args:
        cumulative_lai_above: Cumulative leaf area index above the target layer,
            [m m-1]
        cumulative_lai_below: Cumulative leaf area index below the target layer,
            [m m-1]
        longwave_extinction_coefficient: Extinction coefficient controlling how
            quickly longwave transmissivity decreases with cumulative leaf area,
            dimensionless.

    Returns:
        A tuple containing three arrays of normalised source fractions for sky, soil,
        and surrounding vegetation
    """

    sky_source_fraction = np.exp(
        -longwave_extinction_coefficient * cumulative_lai_above
    )
    soil_source_fraction = np.exp(
        -longwave_extinction_coefficient * cumulative_lai_below
    )

    sky_source_fraction = np.clip(sky_source_fraction, 0.0, 1.0)
    soil_source_fraction = np.clip(soil_source_fraction, 0.0, 1.0)
    vegetation_source_fraction = np.clip(
        1.0 - sky_source_fraction - soil_source_fraction,
        0.0,
        1.0,
    )

    total_source_fraction = (
        sky_source_fraction + soil_source_fraction + vegetation_source_fraction
    )
    sky_source_fraction = np.divide(
        sky_source_fraction,
        total_source_fraction,
        out=np.zeros_like(sky_source_fraction),
        where=total_source_fraction > 0,
    )
    soil_source_fraction = np.divide(
        soil_source_fraction,
        total_source_fraction,
        out=np.zeros_like(soil_source_fraction),
        where=total_source_fraction > 0,
    )
    vegetation_source_fraction = np.divide(
        vegetation_source_fraction,
        total_source_fraction,
        out=np.zeros_like(vegetation_source_fraction),
        where=total_source_fraction > 0,
    )

    return (
        sky_source_fraction,
        soil_source_fraction,
        vegetation_source_fraction,
    )


def calculate_absorbed_longwave_radiation(
    downward_longwave: NDArray[np.floating],
    leaf_area_index: NDArray[np.floating],
    canopy_temperature: NDArray[np.floating],
    soil_temperature: NDArray[np.floating],
    leaf_emissivity: float,
    soil_emissivity: float,
    stefan_boltzmann_constant: float,
    zero_Celsius: float,
    extinction_coefficient_lw: float,
    idx: SimpleNamespace,
) -> NDArray[np.floating]:
    """Calculate absorbed longwave radiation with separate canopy and surface handling.

    Longwave absorption is estimated for canopy, surface, and topsoil layers by
    combining contributions from sky, soil, and surrounding vegetation using a
    simple diffuse view-factor approximation.

    The surface layer is treated as vegetated if it contains leaf area index and
    is therefore included in cumulative vegetation area used for longwave
    attenuation. However, it is excluded from the bulk background vegetation
    emission term so that ``lw_veg`` represents emission from the overlying canopy
    rather than the special near-ground surface layer.

    For each vegetated layer, absorbed longwave is approximated as

    ``leaf_emissivity * (f_sky * lw_sky + f_soil * lw_soil + f_veg * lw_veg)``

    where the source fractions are derived from cumulative vegetated leaf area
    above and below the target layer. The topsoil layer absorbs longwave from the
    sky and canopy above using a bulk transmissivity through the full vegetated
    column.

    Args:
        downward_longwave: Atmospheric downward longwave at canopy top [W m-2]
        leaf_area_index: Leaf area index, [m m-1]
        canopy_temperature: Canopy temperature, [C]
        soil_temperature: Soil temperature, [C]
        leaf_emissivity: Leaf emissivity, dimensionless
        soil_emissivity: Soil emissivity, dimensionless
        stefan_boltzmann_constant: Stefan-Boltzmann constant, [W m-2 K-4]
        zero_Celsius: Conversion from Celsius to Kelvin
        extinction_coefficient_lw: Longwave attenuation coefficient,
            dimensionless.
        idx: Namespace containing layer indices

    Returns:
        Absorbed longwave radiation, [W m-2]
    """
    n_layers, n_cells = leaf_area_index.shape
    absorbed = np.zeros_like(leaf_area_index, dtype=float)

    lai = np.nan_to_num(leaf_area_index, nan=0.0)

    # Create masks for canopy and vegetation layers
    canopy_layer_mask = np.zeros(n_layers, dtype=bool)
    canopy_layer_mask[np.atleast_1d(idx.canopy)] = True

    vegetation_mask = ~np.isnan(leaf_area_index)
    vegetation_mask[idx.topsoil, :] = False
    lai_vegetation = np.where(vegetation_mask, lai, 0.0)

    canopy_background_mask = np.zeros_like(leaf_area_index, dtype=bool)
    canopy_background_mask[canopy_layer_mask, :] = ~np.isnan(
        leaf_area_index[canopy_layer_mask, :]
    )

    # Calculate longwave emission from sky, soil, and canopy vegetation
    lw_sky = downward_longwave.astype(float)

    lw_soil = calculate_longwave_emission(
        temperature=soil_temperature[idx.topsoil] + zero_Celsius,
        emissivity=soil_emissivity,
        stefan_boltzmann=stefan_boltzmann_constant,
    )

    lw_canopy_emit = calculate_longwave_emission(
        temperature=canopy_temperature + zero_Celsius,
        emissivity=leaf_emissivity,
        stefan_boltzmann=stefan_boltzmann_constant,
    )

    # Mean canopy longwave seen as background vegetation source
    with np.errstate(invalid="ignore"):
        lw_veg = np.nanmean(
            np.where(canopy_background_mask, lw_canopy_emit, np.nan),
            axis=0,
        )

    # If there is no canopy in a cell, fall back to sky longwave
    lw_veg = np.where(np.isfinite(lw_veg), lw_veg, lw_sky)

    # Cumulative LAI above and below each layer
    cumulative_above = np.zeros((n_layers, n_cells), dtype=float)
    cumulative_below = np.zeros((n_layers, n_cells), dtype=float)

    running = np.zeros(n_cells, dtype=float)
    for i in range(n_layers):
        cumulative_above[i] = running
        running = running + lai_vegetation[i]

    running = np.zeros(n_cells, dtype=float)
    for i in range(n_layers - 1, -1, -1):
        cumulative_below[i] = running
        running = running + lai_vegetation[i]

    total_vegetation_lai = np.sum(lai_vegetation, axis=0)

    for i in range(n_layers):
        if i == idx.topsoil:
            # Soil sees some sky through the canopy and some canopy radiation

            f_sky = np.exp(-extinction_coefficient_lw * total_vegetation_lai)
            f_veg = 1.0 - f_sky
            absorbed[i] = soil_emissivity * (f_sky * lw_sky + f_veg * lw_veg)
            continue

        if i == idx.surface:
            # Surface layer between canopy and soil: use both sky and soil influence

            has_surface_vegetation = lai[i] > 0
            f_sky, f_soil, f_veg = normalised_source_fractions(
                cumulative_lai_above=cumulative_above[i],
                cumulative_lai_below=cumulative_below[i],
                longwave_extinction_coefficient=extinction_coefficient_lw,
            )
            surface_absorbed = leaf_emissivity * (
                f_sky * lw_sky + f_soil * lw_soil + f_veg * lw_veg
            )
            absorbed[i] = np.where(has_surface_vegetation, surface_absorbed, 0.0)
            continue

        if canopy_layer_mask[i]:
            # Canopy layer sees sky from above, soil from below, vegetation around it
            f_sky, f_soil, f_veg = normalised_source_fractions(
                cumulative_lai_above=cumulative_above[i],
                cumulative_lai_below=cumulative_below[i],
                longwave_extinction_coefficient=extinction_coefficient_lw,
            )
            canopy_absorbed = leaf_emissivity * (
                f_sky * lw_sky + f_soil * lw_soil + f_veg * lw_veg
            )
            absorbed[i] = np.where(lai[i] > 0, canopy_absorbed, 0.0)

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

    Raises:
        ValueError if soil temperature is nan or -inf
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

    if not np.all(np.isfinite(soil_temperature)):
        raise ValueError(
            "Soil temperature is not finite, consider reducing the initial ",
            "integration time step or the integration time modifier for air ",
            "temperature in secant method.",
        )

    return soil_temperature


def calculate_energy_balance_residual(
    canopy_temperature_initial: NDArray[np.floating],
    air_temperature: NDArray[np.floating],
    evapotranspiration: NDArray[np.floating],
    absorbed_shortwave_radiation: NDArray[np.floating],
    absorbed_longwave_radiation: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    density_air: NDArray[np.floating],
    aerodynamic_resistance: NDArray[np.floating],
    latent_heat_vapourisation: NDArray[np.floating],
    leaf_emissivity: float,
    stefan_boltzmann_constant: float,
    zero_Celsius: float,
    seconds_to_hour: float,
    return_fluxes: bool,
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

    if return_fluxes:
        energy_balance = {
            "longwave_emission": longwave_emission_canopy,
            "sensible_heat_flux": -sensible_heat_flux_canopy,
            "latent_heat_flux": -latent_heat_flux_canopy,
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
    integration_time_step: float,
) -> NDArray[np.floating]:
    r"""Update air temperature surrounding canopy in steady state.

    The new air temperature :math:`T_{a}^{new}` is updated following
    :cite:t:`bonan_climate_2019`:

    .. math ::
        H = \frac{\rho_a c_p}{r_a}(T_{l} - T_{a})

    and

    .. math::
        T_{a}^{new} = T_{a}^{old} + \frac{H \delta t}{\rho_a c_p z}

    where :math:`\rho_{a}` is the density of air, :math:`c_{p}` is the specific heat
    capacity of air at constant pressure, :math:`r_{a}` is the aerodynamic resistance of
    the surface, :math:`T_{s}` is the surface temperature, :math:`T_{a}` is the air
    temperature, and :math:`z` is the thickness of the air layer we are updating.
    \delta t is the integration time step.

    Args:
        air_temperature: Air temperature, [C]
        sensible_heat_flux: Sensible heat flux, [W m-2]
        specific_heat_air: Specific heat capacity of air, [J kg-1 K-1]
        density_air: Density of air, [kg m-3]
        mixing_layer_thickness: thickness of the air layer we are updating, [m]
        integration_time_step: Time step for integration, [s]

    Returns:
        updated air temperatures, [C]
    """

    # Update air temperature over a layer of height z (e.g., canopy height)
    new_air_temperature = air_temperature + (
        sensible_heat_flux
        * integration_time_step
        / (density_air * specific_heat_air * mixing_layer_thickness)
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
    """Vectorised secant solver for independent (layers, cell_id) root problems.

    The function returns solver diagnostics to the log file if the solution does not
    converge.

    Args:
        residual_function: Function f(T) returning residual with same shape as T.
        initial_guess: Initial guess canopy temperature with dims ('layers', 'cell_id').
        maxiter_secant: Maximum secant iterations.
        convergence_tolerance: Convergence tolerance on max absolute update.
        small_perturbation_second_guess: Small perturbation for second initial guess.
        denominator_tolerance: Small value to prevent division by zero in secant update.

    Returns:
        Root estimate canopy temperature solving f(T)=0 elementwise.
    """

    previous_temperature = initial_guess.copy()
    current_temperature = previous_temperature + small_perturbation_second_guess

    previous_residual = residual_function(previous_temperature)
    current_residual = residual_function(current_temperature)

    update = np.full_like(current_temperature, np.inf, dtype=float)

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

        update = np.abs(next_temperature - current_temperature)
        max_update = np.nanmax(update)

        if max_update < convergence_tolerance:
            return next_temperature

        previous_temperature, current_temperature = (
            current_temperature,
            next_temperature,
        )
        previous_residual, current_residual = current_residual, next_residual

    # Extract cells where solver did not fully converge with max iterations
    valid_mask = ~np.isnan(initial_guess)

    unconverged_mask = valid_mask & (
        (np.isfinite(update) & (update >= convergence_tolerance))
        | (
            np.isfinite(current_residual)
            & (np.abs(current_residual) >= convergence_tolerance)
        )
    )

    unconverged_layer_ids = np.where(np.any(unconverged_mask, axis=1))[0]
    unconverged_cell_ids = np.where(np.any(unconverged_mask, axis=0))[0]
    failed_layer_idx, failed_cell_idx = np.where(unconverged_mask)
    failed_pairs = [
        (int(layer_idx), int(cell_idx))
        for layer_idx, cell_idx in zip(failed_layer_idx, failed_cell_idx)
    ]

    LOGGER.info(
        "Secant solver did not fully converge within %d iterations. "
        "%d unconverged layer(s), %d unconverged cell(s), "
        "and %d unconverged (layer, cell_id) pair(s).",
        maxiter_secant,
        unconverged_layer_ids.size,
        unconverged_cell_ids.size,
        len(failed_pairs),
    )
    LOGGER.info("Unconverged cell IDs: %s", unconverged_cell_ids.tolist())
    LOGGER.info("Unconverged (layer, cell_id) pairs: %s", failed_pairs)

    return current_temperature


def make_canopy_residual(
    state: dict[str, Any],
    static: dict[str, Any],
    aerodynamic_resistance: NDArray[np.floating],
    abiotic_constants: AbioticConstants,
    core_constants: CoreConstants,
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
            specific_heat_air=state["specific_heat_air"],
            density_air=state["density_air"],
            aerodynamic_resistance=aerodynamic_resistance,
            latent_heat_vapourisation=state["latent_heat_vapourisation"],
            leaf_emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            zero_Celsius=core_constants.zero_Celsius,
            seconds_to_hour=core_constants.seconds_to_hour,
            return_fluxes=False,
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
    min_temperature_change: float,
    max_temperature_change: float,
    integration_time_modifier: float,
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

    The solver uses a flexible integration time step to prevent instability in the
    very thin surface layer.

    If the solver does not converge within max iterations, the last best guess is
    returned and solver diagnostics are added to the log file.

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
        min_temperature_change: Minimum temperature change for flexible integration time
            step, [C]
        max_temperature_change: Maximum temperature change for flexible integration time
            step, [C]
        integration_time_modifier: Factor to adjust integration time interval
        idx: Namespace containing indices for different layers.

    Returns:
        Tuple of canopy temperature, air temperature, and final fluxes.
    """

    # Local working state container
    state_local = state.copy()

    # Solver-owned working arrays
    air_temperature = state["air_temperature"].copy()
    canopy_temperature = state["canopy_temperature"].copy()
    air_temperature_above = state["air_temperature"][idx.above].copy()

    # Set initial conservative integration time step
    integration_time_step = abiotic_constants.integration_time_interval

    for _ in range(maxiter_air):
        state_local["air_temperature"] = air_temperature
        state_local["canopy_temperature"] = canopy_temperature

        residual_function = make_canopy_residual(
            state=state_local,
            static=static,
            aerodynamic_resistance=state_local["aerodynamic_resistance_canopy"],
            abiotic_constants=abiotic_constants,
            core_constants=core_constants,
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
                specific_heat_air=state_local["specific_heat_air"],
                density_air=state_local["density_air"],
                aerodynamic_resistance=state_local["aerodynamic_resistance_canopy"],
                latent_heat_vapourisation=state_local["latent_heat_vapourisation"],
                leaf_emissivity=abiotic_constants.leaf_emissivity,
                stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
                zero_Celsius=core_constants.zero_Celsius,
                seconds_to_hour=core_constants.seconds_to_hour,
                return_fluxes=True,
            ),
        )

        new_air_temperature = update_canopy_air_temperature(
            air_temperature=air_temperature,
            sensible_heat_flux=-fluxes["sensible_heat_flux"],  # type: ignore
            specific_heat_air=state_local["specific_heat_air"],
            density_air=state_local["density_air"],
            mixing_layer_thickness=static["geometry"]["thickness"],
            integration_time_step=integration_time_step,
        )

        canopy_change = np.nanmax(np.abs(new_canopy_temperature - canopy_temperature))
        air_change = np.nanmax(np.abs(new_air_temperature - air_temperature))

        # Safety net: if update is too large, reduce timestep and retry
        if (
            canopy_change > max_temperature_change
            or air_change > max_temperature_change
        ):
            integration_time_step *= 1 - integration_time_modifier
            continue

        # Accept update
        canopy_temperature = new_canopy_temperature
        air_temperature = new_air_temperature

        # The air temperature above the canopy is returned as nan, needs to be filled
        # with reference value again
        air_temperature[idx.above] = air_temperature_above

        # If solution is settling, cautiously increase timestep again
        if (
            canopy_change < min_temperature_change
            and air_change < min_temperature_change
        ):
            integration_time_step = min(
                integration_time_step * (1 + integration_time_modifier),
                abiotic_constants.integration_time_interval,
            )

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
            specific_heat_air=state_local["specific_heat_air"],
            density_air=state_local["density_air"],
            aerodynamic_resistance=state_local["aerodynamic_resistance_canopy"],
            latent_heat_vapourisation=state_local["latent_heat_vapourisation"],
            leaf_emissivity=abiotic_constants.leaf_emissivity,
            stefan_boltzmann_constant=core_constants.stefan_boltzmann_constant,
            zero_Celsius=core_constants.zero_Celsius,
            seconds_to_hour=core_constants.seconds_to_hour,
            return_fluxes=True,
        ),
    )

    return canopy_temperature, air_temperature, final_fluxes
