r"""The ``models.abiotic.energy_balance`` module calculates the energy balance for the
Virtual Ecosystem. Given that the time increments of the model are an hour or longer,
we can assume that below-canopy heat and vapour exchange attain steady state and heat
storage in the canopy does not need to be simulated explicitly.
(For application where very fine-temporal resolution data might be needed, heat and
vapour exchange must be modelled as transient processes, and heat storage by the canopy,
and the exchange of heat between different layers of the canopy, must be considered
explicitly, see :cite:t:`maclean_microclimc_2021`. This is currently not implemented.)

Under steady-state, the balance equation for the leaves in each canopy layer is as
follows (after :cite:t:`maclean_microclimc_2021`):

.. math::
    R_{abs} - R_{em} - H - Q_{LE}
    = R_{abs} - \epsilon_{s} \sigma T_{L}^{4} - \frac{\rho_a c_p}{r_a}(T_{L} - T_{A})
    - \lambda g_{v} \frac {e_{L} - e_{A}}{p_{a}} = 0

where :math:`R_{abs}` is absorbed radiation, :math:`R_{em}` emitted radiation, :math:`H`
the sensible heat flux, :math:`Q_{LE}` the latent heat flux, :math:`\epsilon_{s}` the
emissivity of the leaf, :math:`\sigma` the Stefan-Boltzmann constant, :math:`T_{L}` the
absolute temperature of the leaf, :math:`T_{A}` the absolute temperature of the air
surrounding the leaf, :math:`\lambda` the latent heat of vapourisation of water,
:math:`e_{L}` the effective vapour pressure of the leaf, :math:`e_{A}` the vapour
pressure of air and :math:`p_{a}` atmospheric pressure. :math:`\rho_a` is the density of
air, :math:`c_{p}` is the specific heat capacity of air
at constant pressure, :math:`r_a` is the aerodynamic resistance of the surface (leaf or
soil), :math:`g_{v}` represents the conductivity for vapour loss from the leaves as a
function of the stomatal conductivity.

A challenge in solving this equation is the dependency of latent heat and emitted
radiation on leaf temperature. We use a Newton-Raphson approximation to update
leaf temperature and air temperature.

TODO the units of fluxes are in W m-2 and we need to make sure that the input energy
over a time interval is coherent with the calculations of fluxes in that time interval.

"""  # noqa: D205, D415

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure


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
    # Calculate the depth of each layer, [m]
    layer_depths = np.abs(np.diff(layer_heights, axis=0, append=0))

    # Calculate the light extinction for each layer
    layer_extinction = np.exp(
        -0.01 * light_extinction_coefficient * layer_depths * leaf_area_index
    )

    # Calculate how much light penetrates through the canopy, [W m-2]
    cumulative_extinction = np.cumprod(layer_extinction, axis=0)
    penetrating_radiation = cumulative_extinction * topofcanopy_radiation

    # Calculate how much light is absorbed in each layer, [W m-2]
    absorbed_radiation = np.abs(
        np.diff(
            penetrating_radiation,
            prepend=np.expand_dims(topofcanopy_radiation, axis=0),
            axis=0,
        )
    )

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
        absorbed_radiation: Shortwave radiation absorbed by canopy, [W m-2]

    Returns:
        Initial canopy temperature, [C]
    """
    return air_temperature + canopy_temperature_ini_factor * absorbed_radiation


def initialise_canopy_and_soil_fluxes(
    air_temperature: DataArray,
    topofcanopy_radiation: DataArray,
    leaf_area_index: DataArray,
    layer_heights: DataArray,
    layer_structure: LayerStructure,
    light_extinction_coefficient: float,
    canopy_temperature_ini_factor: float,
    initial_flux_value: float,
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
        layer_structure: Instance of LayerStructure
        light_extinction_coefficient: Light extinction coefficient for canopy
        canopy_temperature_ini_factor: Factor used to initialise canopy temperature as a
            function of air temperature and absorbed shortwave radiation
        initial_flux_value: Initial non-zero flux, [W m-2]

    Returns:
        Dictionary with absorbed radiation (canopy), canopy temperature, sensible
            and latent heat flux (canopy and soil), and ground heat flux [W m-2].
    """

    output = {}

    # Get variables within filled canopy layers
    leaf_area_index_true = leaf_area_index[layer_structure.index_filled_canopy]
    layer_heights_canopy = layer_heights[layer_structure.index_filled_canopy]
    air_temperature_canopy = air_temperature[layer_structure.index_filled_canopy]

    # Initialize absorbed radiation DataArray
    absorbed_radiation = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="shortwave_absorption",
    )

    # Calculate absorbed radiation
    initial_absorbed_radiation = initialise_absorbed_radiation(
        topofcanopy_radiation=topofcanopy_radiation.to_numpy(),
        leaf_area_index=leaf_area_index_true.to_numpy(),
        layer_heights=layer_heights_canopy.to_numpy(),
        light_extinction_coefficient=light_extinction_coefficient,
    )

    # Replace np.nan with new values and write in output dict
    absorbed_radiation[layer_heights_canopy.indexes] = initial_absorbed_radiation
    absorbed_radiation[layer_structure.index_topsoil] = 0.0
    output["shortwave_absorption"] = absorbed_radiation

    # Initialize canopy temperature DataArray
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
    canopy_temperature[layer_structure.index_filled_canopy] = initial_canopy_temperature
    output["canopy_temperature"] = canopy_temperature

    # Initialise sensible heat flux with non-zero mimimum values and write in output
    sensible_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="sensible_heat_flux",
    )
    sensible_heat_flux[layer_structure.index_filled_canopy] = initial_flux_value
    sensible_heat_flux[layer_structure.index_topsoil] = initial_flux_value
    output["sensible_heat_flux"] = sensible_heat_flux

    # Initialise latent heat flux with non-zero mimimum values and write in output
    output["latent_heat_flux"] = sensible_heat_flux.copy().rename("latent_heat_flux")

    # Initialise latent heat flux with non-zero mimimum values and write in output
    ground_heat_flux = DataArray(
        np.full_like(layer_heights, np.nan),
        dims=layer_heights.dims,
        coords=layer_heights.coords,
        name="ground_heat_flux",
    )
    ground_heat_flux[layer_structure.index_topsoil] = initial_flux_value
    output["ground_heat_flux"] = ground_heat_flux

    return output


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


def calculate_net_radiation(
    incoming_radiation: NDArray[np.float32],
    absorbed_radiation: NDArray[np.float32],
    longwave_emission: NDArray[np.float32],
    albedo: float,
) -> NDArray[np.float32]:
    """Calculate net radiation, [W m-2].

    This function calculates net radiation as the difference between incoming shortwave
    radiation, shortwave absorption, and longwave emission. The absorption of longwave
    radiation is currently not considered.

    Args:
        incoming_radiation: Incoming radiation, [W m-2]
        absorbed_radiation: Absorbed radiation, [W m-2]
        longwave_emission: Longwave emission, [W m-2]
        albedo: Albedo, [-]

    Returns:
        net radiation, [W m-2]
    """
    return incoming_radiation * (1 - albedo) - absorbed_radiation - longwave_emission


def calculate_sensible_heat_flux(
    density_air: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    air_temperature: NDArray[np.float32],
    surface_temperature: NDArray[np.float32],
    aerodynamic_resistance: float | NDArray[np.float32],
) -> NDArray[np.float32]:
    r"""Calculate sensible heat flux, [W m-2].

    The sensible heat flux :math:`H` is calculated using the following equation:

    .. math::
        H = \frac{\rho_a c_p}{r_a} (T_S - T_A)

    where :math:`\rho_a` is the density of air, :math:`c_p` is the specific heat
    capacity of air at constant pressure, :math:`r_a` is the aerodynamic resistance of
    the surface, :math:`T_S` is the surface temperature, and :math:`T_A` is the air
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


def calculate_aerodynamic_resistance(
    wind_heights: NDArray[np.float32],
    roughness_length: NDArray[np.float32],
    zero_plane_displacement: NDArray[np.float32],
    friction_velocity: NDArray[np.float32],
    von_karman_constant: float,
) -> NDArray[np.float32]:
    r"""Calculate aerodynamic resistance in canopy, [s m-1].

    The aerodynamic resistance :math:`r_{a}` is calculated as:

    .. math::
        r_{a} = \frac{ln(\frac{z-d}{z_{m}})^{2}}{\kappa ^{2} u^{*}}

    where :math:`z` is the height where the wind speed needs to be calculated,
    :math:`d` is the zero plane displacement
    height, :math:`z_{m}` is the roughness length of momentum, :math:`\kappa` is the
    von Karman constant, and :math:`u^{*}` is the friction velocity.

    Args:
        wind_heights: Heights where wind speed is to be calculated [m].
        roughness_length: Momentum roughness length, [m]
        zero_plane_displacement: Height above ground within the canopy where the wind
            profile extrapolates to zero, [m]
        friction_velocity: Friction velocity, [m s-1]
        von_karman_constant: Von Karman's constant, dimensionless constant describing
            the logarithmic velocity profile of a turbulent fluid near a no-slip
            boundary.

    Returns:
        aerodynamic resistance in canopy, [s m-1]
    """

    # Compute only where valid
    valid_condition = wind_heights > zero_plane_displacement
    aero_resistance = np.where(
        valid_condition,
        (np.log((wind_heights - zero_plane_displacement) / roughness_length)) ** 2
        / (von_karman_constant**2 * friction_velocity),
        np.nan,
    )

    # Replace invalid values with a small fallback resistance
    aero_resistance_out = np.where(np.isnan(aero_resistance), 0.001, aero_resistance)
    return np.where(np.isnan(wind_heights), np.nan, aero_resistance_out)


def update_soil_temperature(
    ground_heat_flux: NDArray[np.float32],
    soil_temperature: NDArray[np.float32],
    soil_layer_thickness: NDArray[np.float32],
    soil_thermal_conductivity: float | NDArray[np.float32],
    soil_bulk_density: float | NDArray[np.float32],
    specific_heat_capacity_soil: float | NDArray[np.float32],
    time_interval: int,
) -> NDArray[np.float32]:
    r"""Update soil temperature using heat diffusion.

    The function applies an explicit finite-difference approach to update
    soil temperatures based on thermal diffusivity and heat flux.

    Governing equations:

    Soil thermal diffusivity:

    .. math::
        \alpha = \frac{\lambda}{\rho c}

    where :math:`\lambda` is the soil thermal conductivity [W m-1 K-1],
    :math:`\rho` is the soil bulk density [kg m-3], :math:`c` is the specific heat
    capacity of soil [J kg-1 K-1].

    Internal layer update:

    .. math::
        T_i^{t+\Delta t} = T_i^t + (\Delta t / \Delta z^2)
        * \alpha * (T_{i+1}^t - 2T_i^t + T_{i-1}^t)

    Top layer update with ground heat flux:

    .. math::
        T_0^{t+\Deltat} = T_0^t + (\Delta t / (\rho c \Delta z)) * G

    No-heat-flux bottom boundary condition:

    .. math::
        T_{n-1}^{t+\Delta t} = T_{n-1}^t + (\Delta t / \Delta z^2)
        * \alpha * (T_{n-2}^t - T_{n-1}^t)

    Args:
        ground_heat_flux: Ground heat flux at top soil, [W m-2]
        soil_temperature: Soil temperature for each soil layer, [C]
        soil_thermal_conductivity: Thermal conductivity of soil [W m-2 K-1]
        soil_bulk_density: Soil bulk density, [kg m-3]
        specific_heat_capacity_soil: Specific heat capacity of soil [J kg-1 K-1]
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


def update_air_canopy_temperature(
    canopy_temperature: NDArray[np.float32],
    air_temperature: NDArray[np.float32],
    absorbed_radiation_canopy: NDArray[np.float32],
    longwave_emission_canopy: NDArray[np.float32],
    sensible_heat_flux_canopy: NDArray[np.float32],
    latent_heat_flux_canopy: NDArray[np.float32],
    emissivity_leaf: float,
    specific_heat_air: NDArray[np.float32],
    density_air: NDArray[np.float32],
    aerodynamic_resistance: float | NDArray[np.float32],
    relaxation_factor: float,
    stefan_boltzmann_constant: float,
) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    r"""Update air and canopy temperature in steady state.

    TODO this needs to be revisited, there seems to be a term missing and we need to
    check if the linearisation needs to be applied in a wider context of the iteration.

    The method linearizes the energy balance of the canopy and air temperature updates
    using Newton-Raphson approximation for temperature adjustment.

    The energy balance (:math:`EB`) for the canopy is given by:

    .. math::
        EB = R_{abs} - \epsilon \sigma T_{c}^{4} - H - Q_{LE}

    Where :math:`R_abs` is the absorbed shortwave radiation by the canopy,
    :math:`\epsilon` is the leaf emissivity, :math:`\sigma` is the Stefan-Boltzmann
    constant, :math:`T_c` is the canopy temperature :math:`H` is the sensible heat
    flux from the canopy, and :math:`Q_{LE}` is the latent heat flux from the canopy.

    The Newton-Raphson linearization for canopy temperature update is:

    .. math::
        T^{new}_{c} = T_{c} - \frac{EB} {\frac{\delta EB}{\delta T_{c}}}

    with

    .. math::
        \frac{\delta EB}{\delta T_{c}}
        = -(4 \epsilon \sigma T_{c}^{3} + \frac{\rho_{a} c_{p}} {r_{a}})

    Where :math:`c_{p}` is the specific heat capacity of air, and :math:`\rho_{a}` is
    the density of air, and :math:`r_{a}` is the aerodynamic resistance.

    The new air temperature :math:`T^{new}_{a}` is given by:

    .. math::
        T^{new}_{a} = T_{a} + \alpha * (T_{c} - T_{a})

    Where the relaxation factor :math:`\alpha` is a weighting factor for air temperature
    update.

    Args:
        canopy_temperature: canopy temperatures for all true canopy layers, [K]
        air_temperature: Air temperature for all layers around true canopy, [K]
        absorbed_radiation_canopy: Absorbed shortwave radiation at all canopy layers,
            [W m-2]
        longwave_emission_canopy: Longwave emission from all canopy layers, [W m-2]
        sensible_heat_flux_canopy: Sensible heat flux from all canopy layers, [W m-2]
        latent_heat_flux_canopy: Latent heat flux from all canopy layers, [W m-2]
        emissivity_leaf: Leaf emissivity
        specific_heat_air: Specific heat capacity of air, [J kg-1 K-1]
        density_air: Density of air, [kg m-3]
        aerodynamic_resistance: Aerodynamic resistance, [s m-1]
        relaxation_factor: Weighting factor for air temperature update (default 0.1)
        stefan_boltzmann_constant: Stefan Boltzmann constant

    Returns:
        Updated canopy and air temperatures, [K]
    """

    # Energy balance for canopy
    energy_balance_canopy = (
        absorbed_radiation_canopy
        - longwave_emission_canopy
        - sensible_heat_flux_canopy
        - latent_heat_flux_canopy
    )

    derivative = -(
        4 * emissivity_leaf * stefan_boltzmann_constant * canopy_temperature**3
        + specific_heat_air * density_air / aerodynamic_resistance
    )

    # Newton-Raphson step
    new_canopy_temperature = canopy_temperature - energy_balance_canopy / derivative

    new_air_temperature = air_temperature + relaxation_factor * (
        canopy_temperature - air_temperature
    )

    return new_canopy_temperature, new_air_temperature


def update_humidity_vpd(
    evapotranspiration: NDArray[np.float32],
    soil_evaporation: NDArray[np.float32],
    saturated_vapour_pressure: NDArray[np.float32],
    specific_humidity: NDArray[np.float32],
    layer_thickness: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
    water_to_air_mass_ratio: float,
    dry_air_factor: float,
    cell_area: float,
) -> dict[str, NDArray[np.float32]]:
    """Update specific humidity and vapour pressure deficit for a multilayer canopy.

    TODO at the moment we get 100% relative humididty and VPD=0, likely because the
    timestep is not taken into account and there is no mixing and removal of water.
    This should be added in a separate function in a following step.

    Args:
        evapotranspiration: Evapotranspiration, [mm]
        soil_evaporation: Soil evaporation to surface layer, [mm]
        saturated_vapour_pressure: Saturated vapour pressure, [kPa]
        specific_humidity: specific humidity, [kg kg-1]
        layer_thickness: Layer thickness, [m]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        water_to_air_mass_ratio: Ratio of water vapour to dry air mass
        dry_air_factor: Complement of water_to_air_mass_ratio, accounting for dry air
        cell_area: Grid cell area, [m2]

    Returns:
      A dictionary containing arrays of updated ``specific_humidity``,
      ``vapour_pressure`` and ``vapour_pressure_deficit`` values.
    """

    # Convert evapotranspiration and soil evaporation from [mm] to [kg/m^3]
    cell_area_in_ha = cell_area / 10000  # convert m2 to hectares
    additional_water = np.zeros_like(layer_thickness)
    additional_water[1 : len(evapotranspiration) + 1] = (
        evapotranspiration * 1000 / cell_area_in_ha
    )  # [kg m^-3]
    additional_water[-1] = soil_evaporation * 1000 / cell_area_in_ha  # [kg m^-3]

    # Volume of air for each layer [m^3]
    layer_volumes = layer_thickness * cell_area

    # Water mass in air before update [kg m^-3]
    water_mass_in_air = specific_humidity * layer_volumes

    # Update water mass in air by adding evapotranspiration and soil evaporation
    new_water_mass_in_air = water_mass_in_air + additional_water * layer_volumes

    # Update specific humidity [kg/kg]
    specific_humidity_updated = new_water_mass_in_air / layer_volumes

    # Compute new vapor pressure [kPa]
    # Vapor pressure is limited by the saturated vapor pressure
    vapour_pressure_updated = (specific_humidity_updated * atmospheric_pressure) / (
        water_to_air_mass_ratio * dry_air_factor + specific_humidity_updated
    )

    # Ensure vapor pressure doesn't exceed the saturated vapor pressure
    # NOTE we need to make sure that we do not loose water here
    vapour_pressure_updated = np.minimum(
        vapour_pressure_updated, saturated_vapour_pressure
    )

    # Compute new relative humidity (%)
    relative_humidity_updated = (
        vapour_pressure_updated / saturated_vapour_pressure
    ) * 100

    # Compute new VPD (Vapor Pressure Deficit) [kPa]
    vpd_updated = saturated_vapour_pressure - vapour_pressure_updated

    # Return results
    return {
        "relative_humidity": relative_humidity_updated,
        "vapour_pressure": vapour_pressure_updated,
        "vapour_pressure_deficit": vpd_updated,
    }
