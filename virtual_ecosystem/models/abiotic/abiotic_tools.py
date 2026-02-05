"""The ``models.abiotic.abiotic_tools`` module contains a set of general functions that
are shared across submodules in the
:mod:`~virtual_ecosystem.models.abiotic.abiotic_model` model.

TODO cross-check with pyrealm for duplication/ different implementation
TODO change temperatures to Kelvin
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmCoreConst
from pyrealm.core.hygro import calc_vp_sat
from xarray import DataArray

from virtual_ecosystem.core.core_components import LayerStructure
from virtual_ecosystem.core.data import Data


def calculate_molar_density_air(
    temperature: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    standard_mole: float,
    standard_pressure: float,
    celsius_to_kelvin: float,
) -> NDArray[np.floating]:
    """Calculate temperature-dependent molar density of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: Air temperature, [C]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        standard_mole: Moles of ideal gas in 1 m^3 air at standard atmosphere
        standard_pressure: Standard atmospheric pressure, [kPa]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin

    Returns:
        molar density of air, [mol m-3]
    """

    temperature_kelvin = temperature + celsius_to_kelvin

    return (
        standard_mole
        * (atmospheric_pressure / standard_pressure)
        * (celsius_to_kelvin / temperature_kelvin)
    )


def calculate_air_density(
    air_temperature: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    specific_gas_constant_dry_air: float,
    celsius_to_kelvin: float,
):
    """Calculate the density of air using the ideal gas law.

    Args:
        air_temperature: Air temperature, [C]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        specific_gas_constant_dry_air: Specific gas constant for dry air, [J kg-1 K-1]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin

    Returns:
        density of air, [kg m-3].
    """
    # Convert temperature from Celsius to Kelvin
    temperature_k = air_temperature + celsius_to_kelvin

    # Calculate density using the ideal gas law
    return (
        atmospheric_pressure * 1000.0 / (temperature_k * specific_gas_constant_dry_air)
    )


def calculate_latent_heat_vapourisation(
    temperature: NDArray[np.floating],
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factors: tuple[float, float],
) -> NDArray[np.floating]:
    """Calculate latent heat of vapourisation.

    Implementation after Eq. 8, :cite:t:`henderson-sellers_new_1984`.

    Args:
        temperature: Air temperature, [C]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        latent_heat_vap_equ_factors: Factors in calculation of latent heat of
            vapourisation

    Returns:
        latent heat of vapourisation, [kJ kg-1]
    """
    temperature_kelvin = temperature + celsius_to_kelvin
    a, b = latent_heat_vap_equ_factors
    return (a * (temperature_kelvin / (temperature_kelvin - b)) ** 2) / 1000.0


def find_last_valid_row(array: NDArray[np.floating]) -> NDArray[np.floating]:
    """Find last valid value in array for each column.

    This function looks for the last valid value in each column of a 2-dimensional
    array. If the previous value is nan, it moved up the array. If all values are NaN,
    the value is set to NaN, too.

    Args:
        array: Two-dimesional array for which last valid values should be found

    Returns:
        Array that contains last valid values
    """
    # Initialize an empty list to store the last valid value from each column
    new_row = []

    # Loop through each column
    for column in range(array.shape[1]):
        # Scan from the last row to the first in the current column
        for i in range(array.shape[0] - 1, -1, -1):
            if not np.isnan(array[i, column]):
                # Append the last valid value found in the column to the new_row list
                new_row.append(array[i, column])
                break
        else:
            # If no valid value is found in the column, append NaN
            new_row.append(np.nan)

    return np.array(new_row)


def calculate_slope_of_saturated_pressure_curve(
    temperature: NDArray[np.floating],
    saturated_pressure_slope_parameters: tuple[float, float, float, float],
) -> NDArray[np.floating]:
    r"""Calculate slope of the saturated pressure curve.

    Args:
        temperature: Temperature, [C]
        saturated_pressure_slope_parameters: List of parameters to calculate
            the slope of the saturated vapour pressure curve

    Returns:
        Slope of the saturated pressure curve, :math:`\Delta_{v}`
    """

    a, b, c, d = saturated_pressure_slope_parameters
    return (
        a * (b * np.exp(c * temperature / (temperature + d))) / (temperature + d) ** 2
    )


def calculate_actual_vapour_pressure(
    air_temperature: DataArray,
    relative_humidity: DataArray,
    pyrealm_core_constants: PyrealmCoreConst,
) -> DataArray:
    """Calculate actual vapour pressure, [kPa].

    Args:
        air_temperature: Air temperature, [C]
        relative_humidity: Relative humidity, [-]
        pyrealm_core_constants: Set of constants from pyrealm

    Returns:
        actual vapour pressure, [kPa]
    """

    saturation_vapour_pressure_air = calc_vp_sat(
        ta=air_temperature.to_numpy(),
        core_const=pyrealm_core_constants,
    )
    return saturation_vapour_pressure_air * relative_humidity / 100.0


def set_unintended_nan_to_zero(
    input_array: NDArray[np.floating],
    input_nan_mask: NDArray[np.bool],
) -> NDArray[np.floating]:
    """Clean up outputs: set unintended NaNs to 0, preserve intended NaNs.

    Args:
        input_array: Input array that may contain NaN
        input_nan_mask: A mask of intended NaN

    Returns:
        Array with unintended NaN set to zero
    """
    arr_clean = np.where(np.isnan(input_array), 0.0, input_array)
    arr_clean[input_nan_mask] = np.nan
    return arr_clean


def compute_layer_thickness_for_varying_canopy(
    heights: NDArray[np.floating],
) -> NDArray[np.floating]:
    """Calculate layer thickness for varying canopy layers.

    Calculate layer thickness by subtracting from the next valid layer below (skipping
    NaNs), and for the last valid layer in each column subtract from zero (ground level)
    .

    Args:
        heights: 2D array of layer heights, [m]

    Returns:
        2D array of layer thickness, [m], same shape as input
    """
    n_layers, n_cols = heights.shape
    thickness = np.full_like(heights, np.nan)

    for col in range(n_cols):
        for row in range(n_layers):
            current = heights[row, col]
            if np.isnan(current):
                continue

            # Find next valid (non-NaN) layer below
            next_valid_found = False
            for lower_row in range(row + 1, n_layers):
                below = heights[lower_row, col]
                if not np.isnan(below):
                    thickness[row, col] = current - below
                    next_valid_found = True
                    break

            # If no valid lower layer found, thickness = current - 0 (ground)
            if not next_valid_found:
                thickness[row, col] = current - 0.0

    return thickness


def calculate_specific_humidity(
    air_temperature: NDArray[np.floating],
    relative_humidity: NDArray[np.floating],
    atmospheric_pressure: NDArray[np.floating],
    molecular_weight_ratio_water_to_dry_air: float,
    pyrealm_core_constants: PyrealmCoreConst,
) -> NDArray[np.floating]:
    """Calculate specific humidity.

    Args:
        air_temperature: Air temperature, [C]
        relative_humidity: Relative humidity, [%]
        atmospheric_pressure: Atmospheric pressure, [kPa]
        molecular_weight_ratio_water_to_dry_air: The ratio of the molar mass of water
            vapour to the molar mass of dry air
        pyrealm_core_constants: Pyrealm core constants

    Returns:
        Specific humidity, [kg kg-1]
    """
    # Saturation vapor pressure
    saturation_vapour_pressure = calc_vp_sat(
        ta=air_temperature,
        core_const=pyrealm_core_constants,
    )

    # Actual vapor pressure (hPa)
    actual_vapour_pressure = (relative_humidity / 100.0) * saturation_vapour_pressure

    # Specific humidity formula
    specific_humidity = (
        molecular_weight_ratio_water_to_dry_air * actual_vapour_pressure
    ) / (
        atmospheric_pressure
        - ((1 - molecular_weight_ratio_water_to_dry_air) * actual_vapour_pressure)
    )

    return specific_humidity


def update_profile_from_reference(
    layer_structure: LayerStructure,
    mask_variable: DataArray,
    variable_name: DataArray,
    time_index: int,
) -> DataArray:
    """Update a layer-based profile for a given time index using a reference variable.

    This function

      - extracts a mask from air temperature to determine valid atmosphere layers
      - reads the reference variable at the given time index
      - applies the mask to keep only valid layers
      - fills the profile template for those layers

    Args:
        layer_structure: LayerStructure object defining the layer setup
        mask_variable: DataArray used to create the atmospheric mask
        variable_name: Reference variable (e.g. data["atmospheric_pressure_ref"])
        time_index: Index of the current time step

    Returns:
        Updated layer profile as a DataArray
    """

    # Create atmospheric mask for filling constant values
    atm_mask = ~np.isnan(
        mask_variable.isel(layers=layer_structure.index_filled_atmosphere)
    )

    # Mean atmospheric pressure profile, [kPa]
    profile_out = layer_structure.from_template()
    reference_values = variable_name.isel(time_index=time_index)
    valid_values = reference_values.where(atm_mask)
    profile_out[layer_structure.index_filled_atmosphere] = valid_values

    return profile_out


def calculate_atmospheric_layer_geometry(data: Data, layer_structure: LayerStructure):
    """Calculate heights, thickness, layer tops, and midpoints for atmospheric layers.

    Args:
        data: Data object
        layer_structure: LayerStructure object

    Returns:
        dict containing heights, thickness, layer_top, layer_midpoints
    """

    # Extract above-ground layer heights
    heights = data["layer_heights"][layer_structure.index_filled_atmosphere].to_numpy()

    # Compute thickness
    thickness = compute_layer_thickness_for_varying_canopy(heights=heights)

    # Compute cumulative thickness excluding current layer
    layer_top = np.cumsum(thickness, axis=1) - thickness

    # Compute midpoints
    midpoints = layer_top + thickness / 2

    return {
        "heights": heights,
        "thickness": thickness,
        "layer_top": layer_top,
        "layer_midpoints": midpoints,
    }


def generate_diurnal_cycle_from_monthly_data(
    monthly_air_temperature: NDArray[np.floating],
    monthly_shortwave_absorption: NDArray[np.floating],
    monthly_relative_humidity: NDArray[np.floating],
    monthly_evapotranspiration: NDArray[np.floating],
    monthly_soil_evaporation: NDArray[np.floating],
    latitude_deg: float,
    month: int,
    daily_temp_amplitude: float = 5.0,
) -> dict[str, NDArray[np.floating]]:
    """Generate synthetic hourly forcing for one day from monthly averages.

    Args:
        monthly_air_temperature: Monthly mean air temperature [C]
        monthly_shortwave_absorption: Monthly mean daily shortwave absorption [W m-2]
        monthly_relative_humidity: Monthly mean relative humidity [%]
        monthly_evapotranspiration: Monthly total evapotranspiration [mm/month]
        monthly_soil_evaporation: Monthly total soil evaporation [mm/month]
        latitude_deg: Latitude for daylength calculation [deg]
        month: Month number [1-12]
        daily_temp_amplitude: typical diurnal temperature swing [C]

    Returns:
        dict of arrays air_temperature_hourly, shortwave_absorption_hourly,
        relative_humidity_hourly, evapotranspiration_hourly, soil_evaporation_hourly
    """

    hours = np.arange(24)

    # Air temperature (sine wave, max at 14:00), (24, cell)
    air_temperature_hourly = monthly_air_temperature[
        None, :
    ] + daily_temp_amplitude * np.sin(2 * np.pi * (hours[:, None] - 8) / 24)

    # Daylength (simple climatology)
    daylength = 12 + 4 * np.cos((month - 1) * np.pi / 6) * np.cos(
        np.radians(latitude_deg)
    )
    daylength = np.clip(daylength, 6.0, 18.0)

    sunrise = 12 - daylength / 2
    sunset = 12 + daylength / 2

    # Shortwave radiation (half-sine over daylight)
    hour_fraction = np.zeros(24)

    for h in range(24):
        if sunrise <= h <= sunset:
            hour_fraction[h] = np.sin(np.pi * (h - sunrise) / daylength)

    if hour_fraction.sum() > 0:
        hour_fraction /= hour_fraction.sum()

    # Shortwave absorption (distributed like radiation), (24, layer, cell)
    shortwave_absorption_hourly = (
        monthly_shortwave_absorption[None, :, :] * hour_fraction[:, None, None]
    )

    # Relative humidity (constant vapor pressure)
    e_s_mean = calc_vp_sat(monthly_air_temperature)  # (cell,)
    e_a = monthly_relative_humidity / 100.0 * e_s_mean  # (cell,)

    e_s_hourly = calc_vp_sat(air_temperature_hourly)  # (24, cell)
    relative_humidity_hourly = 100.0 * e_a[None, :] / e_s_hourly
    relative_humidity_hourly = np.clip(relative_humidity_hourly, 0.0, 100.0)

    # Evapotranspiration (distributed like radiation)
    sw_sum = shortwave_absorption_hourly.sum(axis=0, keepdims=True)

    evapotranspiration_hourly = np.where(
        sw_sum > 0,
        monthly_evapotranspiration[None, :, :] * shortwave_absorption_hourly / sw_sum,
        monthly_evapotranspiration[None, :, :] / 24.0,
    )

    # Soil evaporation (distributed like radiation)
    soil_evaporation_hourly = np.where(
        shortwave_absorption_hourly.sum(axis=1).sum(axis=0)[None, :] > 0,
        monthly_soil_evaporation[None, :]
        * shortwave_absorption_hourly.sum(axis=1)
        / shortwave_absorption_hourly.sum(axis=1).sum(axis=0)[None, :],
        monthly_soil_evaporation[None, :] / 24.0,
    )

    return {
        "air_temperature_hourly": air_temperature_hourly,
        "relative_humidity_hourly": relative_humidity_hourly,
        "shortwave_absorption_hourly": shortwave_absorption_hourly,
        "evapotranspiration_hourly": evapotranspiration_hourly,
        "soil_evaporation_hourly": soil_evaporation_hourly,
    }


def fill_layer_template(
    layer_structure: LayerStructure,
    assignments: list[tuple],
) -> NDArray[np.floating]:
    """Fill layer template with index values.

    Args:
        layer_structure: LayerStructure
        assignments: list of variable names, indices and values

    Returns:
        array with updated indices
    """
    out = layer_structure.from_template().to_numpy()

    for indices, values in assignments:
        out[indices, :] = values

    return out


def record_hourly_output(
    hour: int,
    data_record: dict,
    layer_structure: LayerStructure,
    hourly_values: dict,
):
    """Record hourly data.

    Args:
        hour: Hour of the day
        data_record: dict that contains all hourly data
        layer_structure: LayerStructure object
        hourly_values: Hourly values

    Returns:
        updated dict with hour values
    """
    for var, value in hourly_values.items():
        if var not in data_record:
            continue

        # 1D (cells)
        if isinstance(value, np.ndarray) and value.ndim == 1:
            data_record[var][hour] = value

        # 2D layered variable
        else:
            full = fill_layer_template(layer_structure, value)
            data_record[var][hour] = full

    return data_record


def mean_to_layers(
    var: str, index: list[int], data_record: dict, layer_structure: LayerStructure
) -> DataArray:
    """Return mean value over time for given variable and fill into layer structure.

    Args:
        var: Variable name
        index: List of layer indices to fill
        data_record: Data record dict
        layer_structure: LayerStructure object

    Returns:
        DataArray with mean values filled into layer structure
    """
    out = layer_structure.from_template()
    mean_vals = np.nanmean(data_record[var], axis=0)
    out[index] = mean_vals[index]
    return out
