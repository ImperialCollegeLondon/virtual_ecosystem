"""The ``models.abiotic.abiotic_tools`` module contains a set of general functions that
are shared across submodules in the
:mod:`~virtual_ecosystem.models.abiotic.abiotic_model` model.

TODO cross-check with pyrealm for duplication/ different implementation
TODO change temperatures to Kelvin
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray
from pyrealm.constants import CoreConst as PyrealmConst
from pyrealm.core.hygro import calc_vp_sat
from xarray import DataArray


def calculate_molar_density_air(
    temperature: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
    standard_mole: float,
    standard_pressure: float,
    celsius_to_kelvin: float,
) -> NDArray[np.float32]:
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
    air_temperature: NDArray[np.float32],
    atmospheric_pressure: NDArray[np.float32],
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
    temperature: NDArray[np.float32],
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factors: tuple[float, float],
) -> NDArray[np.float32]:
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


def find_last_valid_row(array: NDArray[np.float32]) -> NDArray[np.float32]:
    """Find last valid value in array for each column.

    This function looks for the last valid value in each column of a 2-dimensional
    array. If the previous value is nan, it moved up the array. If all values are nan,
    the value is set to nan, too.

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
    temperature: NDArray[np.float32],
    saturated_pressure_slope_parameters: tuple[float, float, float, float],
) -> NDArray[np.float32]:
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
    pyrealm_const: PyrealmConst,
) -> DataArray:
    """Calculate actual vapour pressure, [kPa].

    Args:
        air_temperature: Air temperature, [C]
        relative_humidity: Relative humidity, [-]
        pyrealm_const: Set of constants from pyrealm

    Returns:
        actual vapour pressure, [kPa]
    """

    saturation_vapour_pressure_air = calc_vp_sat(
        ta=air_temperature.to_numpy(),
        core_const=pyrealm_const(),
    )
    return saturation_vapour_pressure_air * relative_humidity / 100.0
