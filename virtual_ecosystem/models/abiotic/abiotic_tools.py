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
