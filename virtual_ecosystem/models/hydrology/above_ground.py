"""The ``models.hydrology.above_ground`` module simulates the above-ground hydrological
processes for the Virtual Ecosystem. At the moment, this includes rain water
interception by the canopy, canopy evaporation and leaf drainage, soil evaporation,
and functions related to surface runoff, bypass flow, and river discharge.

TODO change temperatures to Kelvin

"""  # noqa: D205

from math import sqrt

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmConst
from pyrealm.core.hygro import calc_vp_sat

from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic.abiotic_tools import (
    calculate_slope_of_saturated_pressure_curve,
)


def potential_evaporation_leaf(
    net_radiation: NDArray[np.float32],
    vapour_pressure_deficit: NDArray[np.float32],
    air_temperature: NDArray[np.float32],
    density_air_kg: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    aerodynamic_resistance: NDArray[np.float32],
    stomatal_resistance: NDArray[np.float32],
    latent_heat_vapourisation: NDArray[np.float32],
    psychrometric_constant: NDArray[np.float32],
    saturated_pressure_slope_parameters: tuple[float, float, float, float],
):
    r"""Calculate canopy potential evaporation rate using Penman-Monteith equation.

    The potential evaporation rate :math:`EW_{0}` is calculated as follows:

    .. math::
        EW_{0} =
        \frac{\Delta R_n + \rho_a c_p \frac{D}{r_a}}
        {\lambda_v \left(\Delta + \gamma \left(1 + \frac{r_s}{r_a}\right)\right)}

    where :math:`\Delta` is the slope of the saturation vapour pressure curve,
    :math:`R_n` is the net radiation,
    :math:`\rho_a` is the density of air,
    :math:`c_p` is the specific heat of air,
    :math:`D` is the vapour pressure deficit,
    :math:`r_a` is the aerodynamic resistance,
    :math:`\lambda_v` is the latent heat of vapourization,
    :math:`\gamma` is the psychrometric constant, and
    :math:`r_s` is the stomatal resistance.

    Note that we do NOT include ground heat flux in the consideration of canopy
    evaporation; TODO discuss where we use instead the energy flux into NPP

    Args:
        net_radiation: Net radiation at leaf surface, [W m-2]
        vapour_pressure_deficit: Vapour pressure deficit, [kPa]
        air_temperature: Air temperature, [C]
        density_air_kg: Air density, [kg m-3]
        specific_heat_air: Specific heat of air, [kJ kg-1 K-1]
        aerodynamic_resistance: Aerodynamic resistance in canopy, [s m-1]
        stomatal_resistance: Stomatal resistance, [s m-1]
        latent_heat_vapourisation: Latent heat of vapourisation, [kJ kg-1]
        psychrometric_constant: Psychrometric constant, [kPa K-1]
        saturated_pressure_slope_parameters: List of parameters to calculate
            the slope of the saturated vapour pressure curve

    Returns:
        potential evaporation rate, [kg m-2 s-1]
    """

    # Slope of saturation vapour pressure curve (kPa/K)
    delta = calculate_slope_of_saturated_pressure_curve(
        temperature=air_temperature,
        saturated_pressure_slope_parameters=saturated_pressure_slope_parameters,
    )

    # Penman-Monteith equation
    potential_evaporation = (
        delta * net_radiation
        + density_air_kg
        * specific_heat_air
        * (vapour_pressure_deficit / aerodynamic_resistance)
    ) / (
        latent_heat_vapourisation
        * (
            delta
            + psychrometric_constant
            * (1 + stomatal_resistance / aerodynamic_resistance)
        )
    )

    return potential_evaporation


def calculate_canopy_evaporation(
    leaf_area_index: NDArray[np.float32],
    interception: NDArray[np.float32],
    net_radiation: NDArray[np.float32],
    vapour_pressure_deficit: NDArray[np.float32],
    air_temperature: NDArray[np.float32],
    density_air_kg: NDArray[np.float32],
    specific_heat_air: NDArray[np.float32],
    aerodynamic_resistance: NDArray[np.float32],
    stomatal_resistance: NDArray[np.float32],
    latent_heat_vapourisation: NDArray[np.float32],
    psychrometric_constant: NDArray[np.float32],
    saturated_pressure_slope_parameters: tuple[float, float, float, float],
    time_interval: float,
    intercept_residence_time: float,
    extinction_coefficient_global_radiation: float,
) -> dict[str, NDArray[np.float32]]:
    r"""Calculate evaporation of intercepted water from the canopy, [mm].

    This function calculates evaporation of intercepted water from the canopy following
    the LISFLOOD model :cite:t:`van_der_knijff_lisflood_2010`.
    The maximum evaporation per time step :math:`EW_{max}` [mm] is proportional to the
    fraction of vegetated area:

    .. math :: EW_{max} = EW_{0} [1 - e^{(-\kappa_{gb} LAI)}] \Delta t

    where :math:`EW_{0}` is the potential evaporation rate,
    the dimensionless constant :math:`\kappa_{gb}` is the extinction coefficient
    for global solar radiation. In LISFLOOD, :math:`\kappa_{gb}` is given by the product
    :math:`0.75 \cdot \kappa_{df}`, where :math:`\kappa_{df}` is the extinction
    coefficient for diffuse visible light: its value is provided as input to the model
    and it varies between 0.4 and 1.1.

    The actual amount of evaporation :math:`EW_{int}` [mm] is limited by the amount of
    water stored on the leaves :math:`Int_{cum}`:

    .. math :: EW_{int} = min(EW_{max} \Delta t, Int_{cum})

    Another amount of water falls to the soil because of leaf drainage which is modelled
    as a linear reservoir:

    .. math :: D_{int} = \frac{1}{T_{int}} Int_{cum} \Delta t

    where :math:`D_{int}` is the amount of leaf drainage per time step [mm] and
    :math:`T_{int}` is a time constant (or residence time) of the interception store
    [days]. Setting :math:`T_{int} = 1` [day] is strongly recommended and means that all
    the water in the interception store Intcum evaporates or falls to the soil surface
    as leaf drainage within one day.

    Args:
        leaf_area_index: Leaf area index, [m m-1]
        interception: Interception of water in canopy, [mm]
        net_radiation: Net radiation in canopy, [W m-2]
        vapour_pressure_deficit: Vapour pressure deficit, [kPa]
        air_temperature: Air temperature in canopy, [C]
        density_air_kg: Density of air, [kg m-3]
        specific_heat_air: Specific heat of air, [kJ kg-1 K-1]
        aerodynamic_resistance: Aerodynamic resistance of air in the canopy, [s m-1]
        stomatal_resistance: Stomatal resistance, [s m-1]
        latent_heat_vapourisation: Latent heat of vapourisation, [kJ kg-1]
        psychrometric_constant: Psychrometric constant, [kPa K-1]
        saturated_pressure_slope_parameters: List of parameters to calculate
            the slope of the saturated vapour pressure curve
        time_interval: Time interval, [s]
        intercept_residence_time: Intercept residence time, [s]
        extinction_coefficient_global_radiation: Extinction coefficient for global
            radiation

    Returns:
        canopy evaporation [mm per time interval], leaf drainage [mm per time interval]
    """

    output = {}

    # Potential evaporation from open surface water, [kg m-2 s-1]
    potential_evaporation = potential_evaporation_leaf(
        net_radiation=net_radiation,
        vapour_pressure_deficit=vapour_pressure_deficit,
        air_temperature=air_temperature,
        density_air_kg=density_air_kg,
        specific_heat_air=specific_heat_air,
        aerodynamic_resistance=aerodynamic_resistance,
        stomatal_resistance=stomatal_resistance,
        latent_heat_vapourisation=latent_heat_vapourisation,
        psychrometric_constant=psychrometric_constant,
        saturated_pressure_slope_parameters=saturated_pressure_slope_parameters,
    )

    # Maximum evaporation from canopy interception pool, [mm day-1]
    maximum_evaporation = (
        potential_evaporation
        * (1.0 - np.exp(-extinction_coefficient_global_radiation * leaf_area_index))
        * time_interval
    )

    # Actual evaporation, [mm day-1]
    actual_evaporation = np.minimum(maximum_evaporation, interception)
    output["canopy_evaporation"] = actual_evaporation

    # Update interception pool after evaporation
    # Ensure no negative interception
    remaining_interception = np.maximum(interception - actual_evaporation, 0.0)

    leaf_drainage = np.minimum(
        (1.0 / intercept_residence_time) * remaining_interception * time_interval,
        remaining_interception,
    )
    output["leaf_drainage"] = leaf_drainage

    return output


def calculate_soil_evaporation(
    temperature: NDArray[np.float32],
    relative_humidity: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    soil_moisture_residual: float | NDArray[np.float32],
    soil_moisture_capacity: float | NDArray[np.float32],
    leaf_area_index: NDArray[np.float32],
    wind_speed_surface: NDArray[np.float32],
    density_air: float | NDArray[np.float32],
    latent_heat_vapourisation: float | NDArray[np.float32],
    gas_constant_water_vapour: float,
    drag_coefficient_evaporation: float,
    extinction_coefficient_global_radiation: float,
    time_interval: float,
    pyrealm_const: PyrealmConst,
) -> dict[str, NDArray[np.float32]]:
    r"""Calculate soil evaporation based on classical bulk aerodynamic formulation.

    This function uses the so-called 'alpha' method to estimate the evaporative flux
    :cite:p:`mahfouf_comparative_1991`.
    We here use the implementation by :cite:t:`barton_parameterization_1979`:

    .. math :: \alpha = \frac{1.8 \Theta}{\Theta + 0.3}

    .. math :: E_{g} = \frac{\rho_{air}}{R_{a}} (\alpha q_{sat}(T_{s}) - q_{g})

    where :math:`\Theta` is the available top soil moisture (relative volumetric water
    content), :math:`E_{g}` is the evaporation flux (W m-2), :math:`\rho_{air}` is the
    density of air (kg m-3), :math:`R_{a}=(C_{E} u_{a})^-1` is the aerodynamic
    resistance, with :math:`C_{E}` the drag coefficient for evaporation and
    :math:`u_{a}` the wind speed near the surface,
    :math:`q_{sat}(T_{s})` (unitless) is the saturated specific humidity, and
    :math:`q_{g}` is the surface specific humidity (unitless).

    In a final step, the bare soil evaporation is adjusted to shaded soil evaporation
    :cite:t:`supit_system_1994`:

    .. math :: E_{act} = E_{g} e^{(-\kappa_{gb} LAI)}

    where :math:`\kappa_{gb}` is the extinction coefficient for global radiation, and
    :math:`LAI` is the total leaf area index.

    Args:
        temperature: Air temperature at reference height, [C]
        relative_humidity: Relative humidity at reference height, []
        atmospheric_pressure: Atmospheric pressure at reference height, [kPa]
        soil_moisture: Volumetric relative water content, [unitless]
        soil_moisture_residual: Residual soil moisture, [unitless]
        soil_moisture_capacity: Soil moisture capacity, [unitless]
        wind_speed_surface: Wind speed in the bottom air layer, [m s-1]
        density_air: Density if air, [kg m-3]
        latent_heat_vapourisation: Latent heat of vapourisation, [kJ kg-1]
        leaf_area_index: Leaf area index [m m-1]
        gas_constant_water_vapour: Gas constant for water vapour, [kJ kg-1 K-1]
        drag_coefficient_evaporation: Drag coefficient for evaporation, dimensionless
        extinction_coefficient_global_radiation: Extinction coefficient for global
            radiation, [unitless]
        time_interval: Time interval, [s]
        pyrealm_const: Constants from pyrealm package

    Returns:
        soil evaporation, [mm per time interval], aerodynamic resistance surface [s m-1]
    """

    output = {}

    # Available soil moisture
    soil_moisture_free = np.clip(
        (soil_moisture - soil_moisture_residual),
        0.0,
        (soil_moisture_capacity - soil_moisture_residual),
    )

    # Estimate alpha using the Barton (1979) equation
    barton_ratio = (1.8 * soil_moisture_free) / (soil_moisture_free + 0.3)
    alpha = np.where(barton_ratio > 1, 1, barton_ratio)

    # Calculate saturation vapour pressure, kPa
    saturation_vapour_pressure = calc_vp_sat(
        ta=temperature,
        core_const=pyrealm_const(),
    )

    saturated_specific_humidity = (
        gas_constant_water_vapour * saturation_vapour_pressure
    ) / (
        atmospheric_pressure
        - (1 - gas_constant_water_vapour) * saturation_vapour_pressure
    )

    specific_humidity_air = (relative_humidity * saturated_specific_humidity) / 100

    aerodynamic_resistance = 1 / (wind_speed_surface * drag_coefficient_evaporation)
    output["aerodynamic_resistance_surface"] = aerodynamic_resistance

    evaporative_flux = (density_air / aerodynamic_resistance) * (
        alpha * saturation_vapour_pressure - specific_humidity_air
    )

    output["soil_evaporation"] = (
        (  # Return surface evaporation, [mm]
            evaporative_flux / latent_heat_vapourisation
        ).squeeze()
        * np.exp(-extinction_coefficient_global_radiation * leaf_area_index)
        * time_interval
    )

    return output


def find_lowest_neighbour(
    neighbours: list[np.ndarray],
    elevation: np.ndarray,
) -> list[int]:
    """Find lowest neighbour for each grid cell from digital elevation model.

    This function finds the cell IDs of the lowest neighbour for each grid cell. This
    can be used to determine in which direction surface runoff flows.

    Args:
        neighbours: List of neighbour IDs
        elevation: Elevation, [m]

    Returns:
        list of lowest neighbour IDs
    """
    lowest_neighbour = []
    for cell_id, neighbors_id in enumerate(neighbours):
        downstream_id_loc = np.argmax(elevation[cell_id] - elevation[neighbors_id])
        lowest_neighbour.append(neighbors_id[downstream_id_loc])

    return lowest_neighbour


def find_upstream_cells(lowest_neighbour: list[int]) -> list[list[int]]:
    """Find all upstream cell IDs for all grid cells.

    This function identifies all cell IDs that are upstream of each grid cell. This can
    be used to calculate the water flow that goes though a grid cell.

    Args:
        lowest_neighbour: List of lowest neighbour cell IDs

    Returns:
        lists of all upstream IDs for each grid cell
    """
    upstream_ids: list = [[] for i in range(len(lowest_neighbour))]

    for down_s, up_s in enumerate(lowest_neighbour):
        upstream_ids[up_s].append(down_s)

    return upstream_ids


def accumulate_horizontal_flow(
    drainage_map: dict[int, list[int]],
    current_flow: np.ndarray,
    previous_accumulated_flow: np.ndarray,
) -> np.ndarray:
    """Calculate accumulated above-/belowground horizontal flow for each grid cell.

    This function takes the accumulated above-/belowground horizontal flow from the
    previous timestep and adds all (sub-)surface flow of the current time step from
    upstream cell IDs.

    The function currently raises a `ValueError` if accumulated flow is negative.

    Args:
        drainage_map: Dict of all upstream IDs for each grid cell
        current_flow: (Sub-)surface flow of the current time step, [mm]
        previous_accumulated_flow: Accumulated flow from previous time step, [mm]

    Returns:
        accumulated (sub-)surface flow, [mm]
    """

    current_flow_true = np.nan_to_num(current_flow, nan=0.0)
    for cell_id, upstream_ids in enumerate(drainage_map.values()):
        previous_accumulated_flow[cell_id] += np.sum(current_flow_true[upstream_ids])

    if (previous_accumulated_flow < 0.0).any():
        to_raise = ValueError("The accumulated flow should not be negative!")
        LOGGER.error(to_raise)
        raise to_raise

    return previous_accumulated_flow


def calculate_drainage_map(grid: Grid, elevation: np.ndarray) -> dict[int, list[int]]:
    """Calculate drainage map based on digital elevation model.

    This function finds the lowest neighbour for each grid cell, identifies all upstream
    cell IDs and creates a dictionary that provides all upstream cell IDs for each grid
    cell. This function currently supports only square grids.

    Args:
        grid: Grid object
        elevation: Elevation, [m]

    Returns:
        dictionary of cell IDs and their upstream neighbours

    TODO move this to core.grid once we decided on common use
    """

    if grid.grid_type != "square":
        to_raise = ValueError("This grid type is currently not supported!")
        LOGGER.error(to_raise)
        raise to_raise

    grid.set_neighbours(distance=sqrt(grid.cell_area))
    lowest_neighbours = find_lowest_neighbour(grid.neighbours, elevation)
    upstream_ids = find_upstream_cells(lowest_neighbours)

    return dict(enumerate(upstream_ids))


def calculate_interception(
    leaf_area_index: NDArray[np.float32],
    precipitation: NDArray[np.float32],
    intercept_parameters: tuple[float, float, float],
    veg_density_param: float,
) -> NDArray[np.float32]:
    r"""Estimate canopy interception.

    This function estimates canopy interception using the following storage-based
    equation after :cite:t:`aston_rainfall_1979` and :cite:t:`merriam_note_1960` as
    implemented in :cite:t:`van_der_knijff_lisflood_2010` :

    .. math :: Int = S_{max} [1 - e^{\frac{-k R \Delta t}{S_{max}}}]

    where :math:`Int` [mm] is the interception per time step, :math:`S_{max}` [mm] is
    the maximum interception, :math:`R` is the rainfall intensity per time step [mm] and
    the factor :math:`k` accounts for the density of the vegetation.

    :math:`S_{max}` is calculated using an empirical equation
    :cite:p:`von_hoyningen-huene_interzeption_1981`:

      .. math::
        :nowrap:

        \[
            S_{max} =
                \begin{cases}
                    0.935 + 0.498 \cdot \text{LAI} - 0.00575 \cdot \text{LAI}^{2},
                      & \text{LAI} > 0.1 \\
                    0, &  \text{LAI} \le 0.1,
                \end{cases}
        \]

    where LAI is the average Leaf Area Index [m2 m-2]. :math:`k` is estimated as:

    :math:`k=0.046 \cdot LAI`

    Args:
        leaf_area_index: Leaf area index summed over all canopy layers, [m m-1]
        precipitation: Precipitation, [mm]
        intercept_parameters: Parameters for equation estimating maximum canopy
            interception capacity.
        veg_density_param: Parameter used to estimate vegetation density for maximum
            canopy interception capacity estimate

    Returns:
        interception, [mm]
    """

    capacity = (
        intercept_parameters[0]
        + intercept_parameters[1] * leaf_area_index
        - intercept_parameters[2] * leaf_area_index**2
    )
    max_capacity = np.where(leaf_area_index > 0.1, capacity, 0.001)

    canopy_density_factor = veg_density_param * leaf_area_index

    return np.nan_to_num(
        max_capacity
        * (1 - np.exp(-canopy_density_factor * precipitation / max_capacity)),
        nan=0.0,
    )


def distribute_monthly_rainfall(
    total_monthly_rainfall: NDArray[np.float32],
    num_days: int,
    seed: int | None = None,
) -> NDArray[np.float32]:
    """Distributes total monthly rainfall over the specified number of days.

    At the moment, this function allocates each millimeter of monthly rainfall to a
    randomly selected day. In the future, this allocation could be based on observed
    rainfall patterns.

    Args:
        total_monthly_rainfall: Total monthly rainfall, [mm]
        num_days: Number of days to distribute the rainfall over
        seed: Seed for random number generator, optional

    Returns:
        An array containing the daily rainfall amounts, [mm]
    """
    rng = np.random.default_rng(seed)

    daily_rainfall_data = []
    for rainfall in total_monthly_rainfall:
        daily_rainfall = np.zeros(num_days)

        for _ in range(int(rainfall)):
            day = rng.integers(0, num_days, seed)  # Randomly select a day
            daily_rainfall[day] += 1.0  # Add 1.0 mm of rainfall to the selected day

        daily_rainfall *= rainfall / np.sum(daily_rainfall)
        daily_rainfall_data.append(daily_rainfall)

    return np.nan_to_num(np.array(daily_rainfall_data), nan=0.0)


def calculate_bypass_flow(
    top_soil_moisture: NDArray[np.float32],
    sat_top_soil_moisture: NDArray[np.float32],
    available_water: NDArray[np.float32],
    bypass_flow_coefficient: float,
) -> NDArray[np.float32]:
    r"""Calculate preferential bypass flow.

    Bypass flow is here defined as the flow that bypasses the soil matrix and drains
    directly to the groundwater. During each time step, a fraction of the water that is
    available for infiltration is added to the groundwater directly (i.e. without first
    entering the soil matrix). It is assumed that this fraction is a power function of
    the relative saturation of the superficial and upper soil layers. This results in
    the following equation (after :cite:t:`van_der_knijff_lisflood_2010`):

    .. math :: D_{pref, gw} = W_{av} (\frac{w_{1}}{w_{s1}})^{c_{pref}}

    where :math:`D_{pref, gw}` is the amount of preferential flow per time step [mm],
    :math:`W_{av}` is the amount of water that is available for infiltration, and
    :math:`c_{pref}` is an empirical shape parameter. This parameter affects how much of
    the water available for infiltration goes directly to groundwater via preferential
    bypass flow; a value of 0 means all surface water goes directly to groundwater, a
    value of 1 gives a linear relation between soil moisture and bypass flow.
    The equation returns a preferential flow component that becomes increasingly
    important as the soil gets wetter.

    Args:
        top_soil_moisture: Soil moisture of top soil layer, [mm]
        sat_top_soil_moisture: Soil moisture of top soil layer at saturation, [mm]
        available_water: Amount of water available for infiltration, [mm]
        bypass_flow_coefficient: Bypass flow coefficient, dimensionless

    Returns:
        preferential bypass flow, [mm]
    """

    return (
        available_water
        * (top_soil_moisture / sat_top_soil_moisture) ** bypass_flow_coefficient
    )


def convert_mm_flow_to_m3_per_second(
    river_discharge_mm: NDArray[np.float32],
    area: int | float,
    days: int,
    seconds_to_day: float,
    meters_to_millimeters: float,
) -> NDArray[np.float32]:
    """Convert river discharge from millimeters to m3 s-1.

    Args:
        river_discharge_mm: Total river discharge, [mm]
        area: Area of each grid cell, [m2]
        days: Number of days
        seconds_to_day: Second to day conversion factor
        meters_to_millimeters: Factor to convert between millimeters and meters

    Returns:
        river discharge rate for each grid cell, [m3 s-1]
    """

    return river_discharge_mm / meters_to_millimeters / days / seconds_to_day * area


def calculate_surface_runoff(
    precipitation_surface: NDArray[np.float32],
    top_soil_moisture: NDArray[np.float32],
    top_soil_moisture_capacity: NDArray[np.float32],
) -> NDArray[np.float32]:
    """Calculate surface runoff, [mm].

    Surface runoff is calculated with a simple bucket model based on
    :cite:t:`davis_simple_2017`: if precipitation exceeds top soil moisture capacity
    , the excess water is added to runoff and top soil moisture is set to soil
    moisture capacity value; if the top soil is not saturated, precipitation is
    added to the current soil moisture level and runoff is set to zero.

    TODO adjust capacity to account for new set of soil layers #535

    Args:
        precipitation_surface: Precipitation that reaches surface, [mm]
        top_soil_moisture: Water content of top soil layer, [mm]
        top_soil_moisture_capacity: Soil mositure capacity of top soil layer, [mm]
    """

    # Calculate how much water can be added to soil before capacity is reached, [mm]
    free_capacity_mm = top_soil_moisture_capacity - top_soil_moisture

    # Calculate daily surface runoff of each grid cell, [mm]; replace by SPLASH
    return np.where(
        precipitation_surface > free_capacity_mm,
        precipitation_surface - free_capacity_mm,
        0,
    )
