"""The ``models.hydrology.above_ground`` module simulates the above-ground hydrological
processes for the Virtual Rainforest. At the moment, this includes rain water
interception by the canopy, soil evaporation, and all functions related to surface
runoff.
"""  # noqa: D205, D415

from math import sqrt
from typing import Optional, Union

import numpy as np
from numpy.typing import NDArray

from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER


def calculate_soil_evaporation(
    temperature: NDArray[np.float32],
    relative_humidity: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
    soil_moisture: NDArray[np.float32],
    soil_moisture_residual: Union[float, NDArray[np.float32]],
    soil_moisture_capacity: Union[float, NDArray[np.float32]],
    leaf_area_index: NDArray[np.float32],
    wind_speed: Union[float, NDArray[np.float32]],
    celsius_to_kelvin: float,
    density_air: Union[float, NDArray[np.float32]],
    latent_heat_vapourisation: Union[float, NDArray[np.float32]],
    gas_constant_water_vapour: float,
    heat_transfer_coefficient: float,
    extinction_coefficient_global_radiation: float,
) -> NDArray[np.float32]:
    r"""Calculate soil evaporation based classical bulk aerodynamic formulation.

    This function uses the so-called 'alpha' method to estimate the evaporative flux
    :cite:p:`mahfouf_comparative_1991`.
    We here use the implementation by :cite:t:`barton_parameterization_1979`:

    :math:`\alpha = \frac{1.8 * \Theta}{\Theta + 0.3}`

    :math:`E_{g} = \frac{\rho_{air}}{R_{a}} * (\alpha * q_{sat}(T_{s}) - q_{g})`

    where :math:`\Theta` is the available top soil moisture (relative volumetric water
    content), :math:`E_{g}` is the evaporation flux (W m-2), :math:`\rho_{air}` is the
    density of air (kg m-3), :math:`R_{a}` is the aerodynamic resistance (unitless),
    :math:`q_{sat}(T_{s})` (unitless) is the saturated specific humidity, and
    :math:`q_{g}` is the surface specific humidity (unitless).

    In a final step, the bare soil evaporation is adjusted to shaded soil evaporation
    :cite:t:`supit_system_1994`:

    :math:`E_{act} = E_{g} * exp(-\kappa_{gb}*LAI)`

    where :math:`kappa_{gb}` is the extinction coefficient for global radiation, and
    :math:`LAI` is the total leaf area index.

    Args:
        temperature: air temperature at reference height, [C]
        relative_humidity: relative humidity at reference height, []
        atmospheric_pressure: atmospheric pressure at reference height, [kPa]
        soil_moisture: Volumetric relative water content, [unitless]
        soil_moisture_residual: residual soil moisture, [unitless]
        soil_moisture_capacity: soil moisture capacity, [unitless]
        wind_speed: wind speed at reference height, [m s-1]
        celsius_to_kelvin: factor to convert teperature from Celsius to Kelvin
        density_air: density if air, [kg m-3]
        latent_heat_vapourisation: latent heat of vapourisation, [J kg-1]
        gas_constant_water_vapour: gas constant for water vapour, [J kg-1 K-1]
        heat_transfer_coefficient: heat transfer coefficient of air
        extinction_coefficient_global_radiation: Extinction coefficient for global
            radiation, [unitless]

    Returns:
        soil evaporation, [mm]
    """

    # Convert temperature to Kelvin
    temperature_k = temperature + celsius_to_kelvin

    # Available soil moisture
    soil_moisture_free = np.clip(
        (soil_moisture - soil_moisture_residual),
        0.0,
        (soil_moisture_capacity - soil_moisture_residual),
    )

    # Estimate alpha using the Barton (1979) equation
    barton_ratio = (1.8 * soil_moisture_free) / (soil_moisture_free + 0.3)
    alpha = np.where(barton_ratio > 1, 1, barton_ratio)

    saturation_vapour_pressure = 0.6112 * np.exp(
        (17.67 * (temperature_k)) / (temperature_k + 243.5)
    )

    pressure_deficit = atmospheric_pressure - saturation_vapour_pressure
    saturated_specific_humidity = (
        gas_constant_water_vapour / latent_heat_vapourisation
    ) * (saturation_vapour_pressure / pressure_deficit)

    specific_humidity_air = (relative_humidity * saturated_specific_humidity) / 100

    aerodynamic_resistance = heat_transfer_coefficient / wind_speed**2

    evaporative_flux = (density_air / aerodynamic_resistance) * (  # W/m2
        alpha * saturation_vapour_pressure - specific_humidity_air
    )

    # Return surface evaporation, [mm]
    return (evaporative_flux / latent_heat_vapourisation).squeeze() * np.exp(
        -extinction_coefficient_global_radiation * leaf_area_index
    )


def find_lowest_neighbour(
    neighbours: list[np.ndarray],
    elevation: np.ndarray,
) -> list[int]:
    """Find lowest neighbour for each grid cell from digital elevation model.

    This function finds the cell IDs of the lowest neighbour for each grid cell. This
    can be used to determine in which direction surface runoff flows.

    Args:
        neighbours: list of neighbour IDs
        elevation: elevation, [m]

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
        lowest_neighbour: list of lowest neighbour cell_ids

    Returns:
        lists of all upstream IDs for each grid cell
    """
    upstream_ids: list = [[] for i in range(len(lowest_neighbour))]

    for down_s, up_s in enumerate(lowest_neighbour):
        upstream_ids[up_s].append(down_s)

    return upstream_ids


def accumulate_surface_runoff(
    drainage_map: dict[int, list[int]],
    surface_runoff: np.ndarray,
    accumulated_runoff: np.ndarray,
) -> np.ndarray:
    """Calculate accumulated surface runoff for each grid cell.

    This function takes the accumulated surface runoff from the previous timestep and
    adds all surface runoff of the current time step from upstream cell IDs.

    The function currently raises a `ValueError` if accumulated runoff is negative.

    Args:
        drainage_map: dict of all upstream IDs for each grid cell
        surface_runoff: surface runoff of the current time step, [mm]
        accumulated_runoff: accumulated surface runoff from previous time step, [mm]

    Returns:
        accumulated surface runoff, [mm]
    """

    for cell_id, upstream_ids in enumerate(drainage_map.values()):
        accumulated_runoff[cell_id] += np.sum(surface_runoff[upstream_ids])

    if (accumulated_runoff < 0.0).any():
        to_raise = ValueError("The accumulated surface runoff should not be negative!")
        LOGGER.error(to_raise)
        raise to_raise

    return accumulated_runoff


def calculate_drainage_map(grid: Grid, elevation: np.ndarray) -> dict[int, list[int]]:
    """Calculate drainage map based on digital elevation model.

    This function finds the lowest neighbour for each grid cell, identifies all upstream
    IDs and creates a dictionary that provides all upstream cell IDs for each grid
    cell. This function currently supports only square grids.

    Args:
        grid: grid object
        elevation: elevation, [m]

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
    intercept_param_1: float,
    intercept_param_2: float,
    intercept_param_3: float,
    veg_density_param: float,
) -> NDArray[np.float32]:
    r"""Estimate canopy interception.

    This function estimates canopy interception using the following storage-based
    equation after :cite:t:`aston_rainfall_1979` and :cite:t:`merriam_note_1960` as
    implemented in :cite:t:`van_der_knijff_lisflood_2010` :

    :math:`Int = S_{max} * [1 - e \frac{(-k*R*\delta t}{S_{max}})]`

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

    :math:`k=0.046 * LAI`

    Args:
        leaf_area_index: leaf area index summed over all canopy layers, [m2 m-2]
        precipitation: precipitation, [mm]
        intercept_parameter_1: Parameter in equation that estimates maximum canopy
            interception capacity
        intercept_parameter_2: Parameter in equation that estimates maximum canopy
            interception capacity
        intercept_parameter_3: Parameter in equation that estimates maximum canopy
            interception capacity
        veg_density_param: Parameter used to estimate vegetation density for maximum
            canopy interception capacity estimate

    Returns:
        interception, [mm]
    """

    capacity = (
        intercept_param_1
        + intercept_param_2 * leaf_area_index
        - intercept_param_3 * leaf_area_index**2
    )
    max_capacity = np.where(leaf_area_index > 0.1, capacity, 0)

    canopy_density_factor = veg_density_param * leaf_area_index

    return np.nan_to_num(
        max_capacity
        * (1 - np.exp(-canopy_density_factor * precipitation / max_capacity)),
        nan=0.0,
    )


def distribute_monthly_rainfall(
    total_monthly_rainfall: NDArray[np.float32],
    num_days: int,
    seed: Optional[int] = None,
) -> NDArray[np.float32]:
    """Distributes total monthly rainfall over the specified number of days.

    At the moment, this function allocates each millimeter of monthly rainfall to a
    randomly selected day. In the future, this allocation could be based on observed
    rainfall patterns.

    Args:
        total_monthly_rainfall: Total monthly rainfall, [mm]
        num_days: Number of days to distribute the rainfall over
        seed: seed for random number generator, optional

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
    infiltration_shape_parameter: float,
) -> NDArray[np.float32]:
    r"""Calculate preferential bypass flow.

    Bypass flow is here defined as the flow that bypasses the soil matrix and drains
    directly to the groundwater. During each time step, a fraction of the water that is
    available for infiltration is added to the groundwater directly (i.e. without first
    entering the soil matrix). It is assumed that this fraction is a power function of
    the relative saturation of the superficial and upper soil layers. This results in
    the following equation (after :cite:t:`van_der_knijff_lisflood_2010`):

    :math:`D_{pref, gw} = W_{av} * (\frac{w_{1}}{w_{s1}})^{c_{pref}}`

    where :math:`D_{pref, gw}` is the amount of preferential flow per time step [mm],
    :math:`W_{av}` is the amount of water that is available for infiltration, and
    :math:`c_{pref}` is an empirical shape parameter. This parameter affects how much of
    the water available for infiltration goes directly to groundwater via preferential
    bypass flow; a value of 0 means all surface water goes directly to groundwater, a
    value of 1 gives a linear relation between soil moisture and bypass flow.
    The equation returns a preferential flow component that becomes increasingly
    important as the soil gets wetter.

    Args:
        top_soil_moisture: soil moisture of top soil layer, [mm]
        sat_top_soil_moisture: soil moisture of top soil layer at saturation, [mm]
        available_water: amount of water available for infiltration, [mm]
        infiltration_shape_parameter: shape parameter for infiltration

    Returns:
        preferential bypass flow, [mm]
    """

    return (
        available_water
        * (top_soil_moisture / sat_top_soil_moisture) ** infiltration_shape_parameter
    )


def convert_mm_flow_to_m3_per_second(
    river_discharge_mm: NDArray[np.float32],
    area: Union[int, float],
    days: int,
    seconds_to_day: float,
) -> NDArray[np.float32]:
    """Convert channel flow from millimeters to m3/s.

    Args:
        channel_flow_mm: channel flow in [mm]
        area: area of each grid cell, [m2]
        days: number of days
        seconds_to_day: second to day conversion factor

    Returns:
        channel flow for each grid cell in m3/s
    """

    return river_discharge_mm / 100 / days / seconds_to_day * area
