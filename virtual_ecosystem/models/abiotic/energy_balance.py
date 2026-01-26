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
radiation on leaf temperature. We use a Newton approximation to update
leaf temperature and air temperature iteratively.

After updating each layer, temperature and vapor are mixed vertically between
atmospheric layers.
Advection at the top of the canopy is currently not considered as we don't have
have horizontal exchange between grid cells and air above canopy values would be
unrealistic.

TODO plants use a fraction of the absorbed radiation of photosynthesis, this needs to be
subtracted from the energy balance

"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import newton
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic import wind
from virtual_ecosystem.models.abiotic.abiotic_tools import set_unintended_nan_to_zero


def initialise_canopy_and_soil_fluxes(
    air_temperature: DataArray,
    layer_structure: LayerStructure,
    initial_flux_value: float,
) -> dict[str, DataArray]:
    """Initialise canopy temperature and energy fluxes.

    This function initializes the following variables to run the first step of the
    energy balance routine: canopy temperature, [C], sensible
    and latent heat flux (canopy and soil), and ground heat flux, all in [W m-2].

    Args:
        air_temperature: Air temperature, [C]
        layer_structure: Instance of LayerStructure
        light_extinction_coefficient: Light extinction coefficient for canopy, unitless
        initial_flux_value: Initial non-zero flux, [W m-2]

    Returns:
        Dictionary with canopy temperature, [C], sensible and latent heat flux (canopy
        and soil), [W m-2], and ground heat flux, [W m-2].
    """

    output = {}

    # Initialise canopy temperature, equilibrium with surrounding air temperature, [C]
    canopy_temperature = layer_structure.from_template()
    canopy_temperature[layer_structure.index_filled_canopy] = air_temperature[
        layer_structure.index_filled_canopy
    ]
    canopy_temperature[layer_structure.index_surface_scalar] = air_temperature[
        layer_structure.index_surface_scalar
    ]
    output["canopy_temperature"] = canopy_temperature

    # Initialise sensible heat flux with non-zero minimum values
    sensible_heat_flux = layer_structure.from_template()
    sensible_heat_flux[layer_structure.index_flux_layers] = initial_flux_value
    output["sensible_heat_flux"] = sensible_heat_flux

    # Initialise latent heat flux with non-zero minimum values
    output["latent_heat_flux"] = sensible_heat_flux.copy()

    # Initialise ground heat flux with non-zero minimum values
    ground_heat_flux = layer_structure.from_template()
    ground_heat_flux[layer_structure.index_topsoil] = initial_flux_value
    output["ground_heat_flux"] = ground_heat_flux

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

    TODO PP to be separated from absorbed radiation and subtracted from the balance

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

    # Energy balance residual, [W m-2]
    energy_balance_residual = (
        absorbed_shortwave_radiation
        + absorbed_longwave_radiation
        - longwave_emission_canopy
        - sensible_heat_flux_canopy
        - latent_heat_flux_canopy
        # - absorption_par
    )

    if return_fluxes:
        energy_balance = {
            "longwave_emission_canopy": longwave_emission_canopy,
            "sensible_heat_flux_canopy": sensible_heat_flux_canopy,
            "latent_heat_flux_canopy": latent_heat_flux_canopy,
            "energy_balance_residual": energy_balance_residual,
        }
        return energy_balance
    else:
        return energy_balance_residual


def solve_canopy_temperature(
    canopy_temperature_initial: NDArray[np.floating],
    air_temperature: NDArray[np.floating],
    evapotranspiration: NDArray[np.floating],
    absorbed_shortwave_radiation: NDArray[np.floating],
    absorbed_longwave_radiation: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    density_air: NDArray[np.floating],
    aerodynamic_resistance: NDArray[np.floating],
    latent_heat_vapourisation: NDArray[np.floating],
    emissivity_leaf: float,
    stefan_boltzmann_constant: float,
    zero_Celsius: float,
    seconds_to_hour: float,
    maxiter: int,
    return_fluxes: bool = False,
) -> NDArray[np.floating]:
    r"""Solve for canopy temperature where energy balance residual is zero.

    The method linearizes the energy balance of the canopy and air temperature updates
    using Newton approximation for temperature adjustment following
    :cite:t:`yang_scope_2021`. The function uses the scipy.optimise.newton method to
    solve the problem; the derivative is determined by the function.

    The energy balance for the canopy is given by:

    .. math::
        R_{abs} - \epsilon_{l} \sigma T_{l}^{4} - H - \lambda E - PP = 0

    Where :math:`R_{abs}` is the absorbed shortwave and longwave radiation by the canopy
    , :math:`\epsilon_{l}` is the leaf emissivity, :math:`\sigma` is the
    Stefan-Boltzmann constant, :math:`T_{l}` is the leaf temperature, :math:`H` is the
    sensible heat flux from the canopy, :math:`\lambda E` is the latent heat flux from
    the canopy, and :math:`PP` is a fraction of the absorbed light is used in
    photosynthesis (PAR).

    Note that the latent heat flux is currently a constant given by the plant model.
    PP is not considered explicitly but will also be treated as a constant.

    The Newton linearization for canopy temperature update is:

    .. math::
        T_{l}^{new} =
        T_{l}^{old} + W \cdot \frac{EB} {\frac{\delta EB}{\delta T_{l}^{old}}}

    where :math:`\frac{\delta EB}{\delta T_{l}^{old}}` is the first derivative of the
    energy balance closure error to temperature, and :math:`W` is a weighting for the
    step size to ensure numerical stability. The derivative is estimated analytically:

    .. math::
        \frac{\delta EB}{\delta T_{l}^{old}}
        = \frac{\rho_{a} c_{p}} {r_{a}}
        + \frac{\rho_{a} \Delta_{v}}{(r_{a} + r_{s})} \lambda
        + 4 \epsilon_{l} \sigma (T_{l}^{old} + 273.15)^{3}

    Where :math:`c_{p}` is the specific heat capacity of air, [J kg-1 K-1],
    :math:`\rho_{a}` is the density of air, [kg m-3], :math:`\Delta_{v}` is the slope of
    the saturation vapour pressure curve, :math:`\lambda` is the latent heat
    of vapourisation, [kJ kg-1], :math:`r_{a}` and :math:`r_{s}` are the aerodynamic and
    stomatal resistance, [s m-1], respectively.

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
        stomatal_resistance: Stomatal resistance, [s m-1]
        latent_heat_vapourisation: Latent heat of vapourisation, [J kg-1]
        emissivity_leaf: Leaf emissivity, dimensionless
        stefan_boltzmann_constant: Stefan Boltzmann constant, [W m-2 K-4]
        zero_Celsius: Factor to convert between Celsius and Kelvin
        seconds_to_hour: Factor to convert between hours and seconds
        saturated_pressure_slope_parameters: List of parameters to calculate
            the slope of the saturated vapour pressure curve
        maxiter: Maximum number of iterations
        return_fluxes: Flag to indicate if all components of the energy balance should
            be returned. This is false for the newton approach to solve for canopy
            temperature, but true to create the outputs in a second call afterwards.

    Returns:
        canopy temperature, [C]
    """

    nrows, ncols = canopy_temperature_initial.shape
    solved_temperature = np.empty_like(canopy_temperature_initial, dtype=np.float64)
    convergence_info = []

    # TODO this loop might be a potential performance bottleneck.
    # The function only takes scalar values
    for i in range(nrows):
        for j in range(ncols):

            def residual_func(canopy_temp_scalar):
                # Call the residual function with a 1x1 array input
                result = calculate_energy_balance_residual(
                    canopy_temperature_initial=np.array(
                        [[canopy_temp_scalar]], dtype=np.float64
                    ),
                    air_temperature=np.array(
                        [[air_temperature[i, j]]], dtype=np.float64
                    ),
                    evapotranspiration=np.array(
                        [[evapotranspiration[i, j]]], dtype=np.float64
                    ),
                    absorbed_shortwave_radiation=np.array(
                        [[absorbed_shortwave_radiation[i, j]]], dtype=np.float64
                    ),
                    absorbed_longwave_radiation=np.array(
                        [[absorbed_longwave_radiation[i]]], dtype=np.float64
                    ),
                    specific_heat_air=np.array(
                        [[specific_heat_air[i, j]]], dtype=np.float64
                    ),
                    density_air=np.array([[density_air[i, j]]], dtype=np.float64),
                    aerodynamic_resistance=np.array(
                        [[aerodynamic_resistance[i]]], dtype=np.float64
                    ),
                    latent_heat_vapourisation=np.array(
                        [[latent_heat_vapourisation[i, j]]], dtype=np.float64
                    ),
                    leaf_emissivity=emissivity_leaf,
                    stefan_boltzmann_constant=stefan_boltzmann_constant,
                    zero_Celsius=zero_Celsius,
                    seconds_to_hour=seconds_to_hour,
                    return_fluxes=return_fluxes,
                )

                # Extract scalar from 1x1 array or a single element array
                if isinstance(result, np.ndarray):
                    if result.size == 1:
                        return result.item()
                    else:
                        # Choose how to reduce the array to scalar, e.g. first element
                        return result.flat[0]
                return result

            x0 = canopy_temperature_initial[i, j]

            best_estimate = [x0]  # use a mutable object to track updates
            iteration_history = []

            # Wrapper to extract best estimate if function does not converge
            def tracked_func(x):
                iteration_history.append(x)
                best_estimate[0] = x  # update best estimate
                return residual_func(x)

            try:
                solved_temperature[i, j] = newton(
                    func=tracked_func,
                    x0=x0,
                    maxiter=maxiter,
                    tol=0.01,
                )
                converged = True

            except RuntimeError:
                solved_temperature[i, j] = best_estimate[0]  # use last known good value
                converged = False

    convergence_info.append(
        {
            "row": i,
            "col": j,
            "converged": converged,
            "final_value": solved_temperature[i, j],
            "best_estimate": best_estimate[0],
            "history": iteration_history,
        }
    )

    # Log a message based on whether all cells converged or not
    num_not_converged = sum(not c["converged"] for c in convergence_info)
    total_cells = nrows * ncols

    if num_not_converged == 0:
        LOGGER.info(f"Solver finished successfully: all {total_cells} cells converged.")
    else:
        LOGGER.warning(
            f"Solver finished with issues: {num_not_converged} / {total_cells} cells"
            " did not converge. Best estimates were used for those cells."
        )

    return solved_temperature


def update_air_temperature(
    air_temperature: NDArray[np.floating],
    sensible_heat_flux: NDArray[np.floating],
    specific_heat_air: NDArray[np.floating],
    density_air: NDArray[np.floating],
    mixing_layer_thickness: NDArray[np.floating],
) -> NDArray[np.floating]:
    r"""Update air temperature in steady state.

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


def update_humidity_vpd(
    canopy_evapotranspiration: NDArray[np.floating],
    understorey_evapotranspiration: NDArray[np.floating],
    soil_evaporation: NDArray[np.floating],
    saturated_vapour_pressure: NDArray[np.floating],
    specific_humidity: NDArray[np.floating],
    layer_thickness: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    density_air: NDArray[np.floating],
    mixing_coefficient: NDArray[np.floating],
    ventilation_rate: NDArray[np.floating],
    molecular_weight_ratio_water_to_dry_air: float,
    dry_air_factor: float,
    cell_area: float,
    limits: tuple[float, float],
    time_interval: float,
) -> dict[str, NDArray[np.floating]]:
    """Update specific humidity and vapour pressure deficit for a multilayer canopy.

    This function adds the water from soil evaporation and canopy evapotranspiration to
    each atmospheric layer, mixes between the layers and with the atmosphere above.

    Args:
        canopy_evapotranspiration: Evapotranspiration from canopy layers, [mm]
        understorey_evapotranspiration: Understorey evapotranspiration, [mm]
        soil_evaporation: Soil evaporation to surface layer, [mm]
        saturated_vapour_pressure: Saturated vapour pressure, [kPa]
        specific_humidity: Specific humidity, [kg kg-1]
        layer_thickness: Layer thickness, [m]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        density_air: Density of air, [kg m-3]
        mixing_coefficient: Turbulent mixing coefficient, [m2 s-1]
        ventilation_rate: Ventilation rate, [s-1]
        molecular_weight_ratio_water_to_dry_air: Molecular weight ratio of water to dry
            air, dimensionless
        dry_air_factor: Complement of water_to_air_mass_ratio, accounting for dry air
        cell_area: Grid cell area, [m2]
        limits: Realistic bounds of specific humidity
        time_interval: Time interval, [s]

    Returns:
      A dictionary containing arrays of updated ``relative_humidity``,
      ``specific_humidity``, ``vapour_pressure`` and ``vapour_pressure_deficit`` values.
    """

    # Create a mask of where the input was NaN (no true canopy)
    input_nan_mask = np.isnan(specific_humidity)

    # Convert evapotranspiration and soil evaporation [mm] to [kg m2 s-1] time interval
    canopy_et_kg_m2 = canopy_evapotranspiration * 1e-3 / time_interval
    understorey_et_kg_m2 = understorey_evapotranspiration * 1e-3 / time_interval
    soil_evap_kg_m2 = soil_evaporation * 1e-3 / time_interval

    # Calculate air layer volumes [m3]
    layer_volumes = layer_thickness * cell_area
    air_mass_per_layer = layer_volumes * density_air

    # Add ET and soil evaporation as mass flux [kg]
    added_mass = np.zeros_like(layer_thickness)
    added_mass[1 : len(canopy_et_kg_m2) + 1] += (
        canopy_et_kg_m2 * cell_area * time_interval
    )
    added_mass[-1] += (
        (soil_evap_kg_m2 + understorey_et_kg_m2) * cell_area * time_interval
    )

    # Update water mass in air
    water_mass_in_air = specific_humidity * air_mass_per_layer
    water_mass_in_air += added_mass

    # Vertical mixing
    specific_humidity = water_mass_in_air / air_mass_per_layer
    specific_humidity_updated = wind.mix_and_ventilate(
        input_variable=specific_humidity,
        mixing_coefficient=mixing_coefficient,
        ventilation_rate=ventilation_rate,
        limits=limits,
    )

    # NOTE Advection not implemented as everything is removed with time interval > 1h
    # and horizontal transfer is not implemented
    # specific_humidity_advected = wind.advect_water_from_toplayer(
    #     specific_humidity=specific_humidity_updated[0],
    #     layer_thickness=layer_thickness[0],
    #     density_air=density_air[0],
    #     wind_speed=wind_speed,
    #     characteristic_length=np.sqrt(cell_area),
    #     time_interval=time_interval,
    # )
    # specific_humidity_updated[0] = specific_humidity_advected

    # Vapour pressure [kPa]
    vapour_pressure_updated = (specific_humidity_updated * atmospheric_pressure) / (
        molecular_weight_ratio_water_to_dry_air * dry_air_factor
        + specific_humidity_updated
    )

    # Ensure vapor pressure doesn't exceed the saturated vapor pressure
    # TODO we need to make sure that we do not loose water here
    vapour_pressure_updated = np.minimum(
        vapour_pressure_updated, saturated_vapour_pressure
    )

    # Compute new relative humidity (%)
    relative_humidity_updated = (
        vapour_pressure_updated / saturated_vapour_pressure
    ) * 100

    # Compute new VPD (Vapor Pressure Deficit) [kPa]
    vpd_updated = saturated_vapour_pressure - vapour_pressure_updated

    # Map variable names to arrays
    raw_outputs = {
        "relative_humidity": relative_humidity_updated,
        "vapour_pressure": vapour_pressure_updated,
        "vapour_pressure_deficit": vpd_updated,
        "specific_humidity": specific_humidity_updated,
    }

    # Clean outputs while preserving intended NaNs
    cleaned_outputs = {
        key: set_unintended_nan_to_zero(arr, input_nan_mask)
        for key, arr in raw_outputs.items()
    }

    return cleaned_outputs


def calculate_understorey_effective_heat_capacity(
    layer_thickness: NDArray[np.floating],
    leaf_area_index: NDArray[np.floating],
    leaf_mass_per_area: float,
    leaf_specific_heat: float,
    air_volumetric_heat_capacity: float,
) -> NDArray[np.floating]:
    """Calculates the effective heat capacity of the understorey layer.

    This function calculates the effective heat capacity of the understorey layer
    combining volumetric heat capacity of the air/vegetation mixture and
    the thermal mass of leaves scaled by LAI.

    Args:
        layer_thickness: Thickness of the understorey layer, [m]
        leaf_area_index: Leaf area index, [m2 m-2].
        leaf_mass_per_area: Leaf mass per leaf area, [kg m-2]
        leaf_specific_heat: Specific heat capacity of leaf tissue, [J kg-1 K-1].
        air_volumetric_heat_capacity: Volumetric heat capacity of air, [J m-3 K-1].

    Returns:
        Effective heat capacity per ground area, [J m-2 K-1].
    """

    # Compute vegetation bulk density from LAI
    vegetation_density = (leaf_area_index * leaf_mass_per_area) / layer_thickness

    # Volumetric heat capacity of vegetation (dominant term)
    vegetation_volumetric_heat_capacity = vegetation_density * leaf_specific_heat

    # Add air (optional)
    total_volumetric_heat_capacity = (
        vegetation_volumetric_heat_capacity + air_volumetric_heat_capacity
    )

    # Convert to per-ground-area
    heat_capacity_per_area = total_volumetric_heat_capacity * layer_thickness

    return heat_capacity_per_area


def update_understorey_temperature(
    current_temperature: NDArray[np.floating],
    net_radiation: NDArray[np.floating],
    sensible_heat_flux: NDArray[np.floating],
    conductive_flux: NDArray[np.floating],
    effective_heat_capacity: NDArray[np.floating],
    time_step_seconds: float,
    latent_heat_flux: NDArray[np.floating] | None,
    max_delta_temperature: float,
) -> NDArray[np.floating]:
    """Updates the understorey temperature using a simple energy balance.

    Note: This function warns if the computed temperature change exceeds
    `max_delta_temperature`, which often indicates that the effective heat capacity is
    underestimated.

    Implementation based on :cite:t:`ogee_a_forest_2002`.

    Args:
        current_temperature: Current understorey temperature, [C or K].
        net_radiation: Net radiation flux into the understorey layer, [W m-2].
        sensible_heat_flux: Sensible heat flux from/to the understorey, [W m-2].
        conductive_flux: Conductive flux from/to the soil, [W m-2].
        effective_heat_capacity: Effective heat capacity per ground area, [J m-2 K-1].
        time_step_seconds: Time step for the update [s], default is 3600 (1 hour).
        latent_heat_flux: Latent heat flux from/to the understorey [W m-2], optional
        max_delta_temperature: Maximum allowed temperature change per time step [K]
            before warning, default 10 K.

    Returns:
        Updated understorey temperature [C or K].

    """
    # Start with net energy flux
    total_flux = net_radiation - sensible_heat_flux - conductive_flux

    # Include latent heat flux if provided
    if latent_heat_flux is not None:
        total_flux -= latent_heat_flux

    # Temperature change [K]
    delta_temperature = total_flux * time_step_seconds / effective_heat_capacity

    # Sanity check for unrealistic temperature jumps
    if np.any(np.abs(delta_temperature) > max_delta_temperature):
        LOGGER.warning(
            "Warning: Large temperature change detected! "
            "Check effective heat capacity or flux magnitudes."
        )

    # Update temperature
    return current_temperature + delta_temperature


def calculate_conductive_flux_understorey(
    soil_temperature: NDArray[np.floating],
    understorey_temperature: NDArray[np.floating],
    understorey_layer_thickness: NDArray[np.floating],
    soil_thermal_conductivity: float,
    understorey_thermal_conductivity: float,
) -> np.ndarray:
    """Calculates the conductive heat flux from understorey vegetation to the soil.

    Positive flux means heat flows into the soil.

    Args:
        soil_temperature : Soil temperatures at the interface, [°C or K]
        understorey_temperature : Temperatures of the understorey vegetation, [°C or K]
        understorey_layer_thickness : Thickness of the understorey layer, [m]
        soil_thermal_conductivity : Soil thermal conductivity, [W m-1 K-1]
        understorey_thermal_conductivity : Thermal conductivity of understorey
            vegetation layer, [W m-1 K-1]

    Returns:
        Conductive flux from understorey to soil, [W m-2]
    """
    effective_conductivity = np.sqrt(
        soil_thermal_conductivity * understorey_thermal_conductivity
    )
    flux = (
        -effective_conductivity
        * (soil_temperature - understorey_temperature)
        / understorey_layer_thickness
    )
    return flux


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
