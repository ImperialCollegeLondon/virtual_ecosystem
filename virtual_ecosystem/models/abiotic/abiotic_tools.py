"""The ``models.abiotic.abiotic_tools`` module contains a set of general functions that
are shared across submodules in the
:mod:`~virtual_ecosystem.models.abiotic.abiotic_model` model.

TODO cross-check with pyrealm for duplication/ different implementation
TODO change temperatures to Kelvin
"""  # noqa: D205

import numpy as np
from numpy.typing import NDArray


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


def calculate_specific_heat_air(
    temperature: NDArray[np.float32],
    molar_heat_capacity_air: float,
    specific_heat_equ_factors: list[float],
) -> NDArray[np.float32]:
    """Calculate temperature-dependent specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: Air temperature, [C]
        molar_heat_capacity_air: Molar heat capacity of air, [J mol-1 C-1]
        specific_heat_equ_factors: Factors in calculation of molar specific heat of air

    Returns:
        specific heat of air at constant pressure, [J mol-1 K-1]
    """
    return (
        specific_heat_equ_factors[0] * temperature**2
        + specific_heat_equ_factors[1] * temperature
        + molar_heat_capacity_air
    )


def calculate_latent_heat_vapourisation(
    temperature: NDArray[np.float32],
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factors: list[float],
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
    return (
        latent_heat_vap_equ_factors[0]
        * (temperature_kelvin / (temperature_kelvin - latent_heat_vap_equ_factors[1]))
        ** 2
    ) / 1000.0


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
