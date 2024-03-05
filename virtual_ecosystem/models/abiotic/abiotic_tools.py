"""The ``models.abiotic.abiotic_tools`` module contains a set of general functions that
are shared across submodules in the :mod:`~virtual_rainforest.models.abiotic` model.

TODO cross-check with pyrealm for duplication/ different implementation
TODO change temperatures to Kelvin
"""  # noqa: D205, D415

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
    specific_heat_equ_factor_1: float,
    specific_heat_equ_factor_2: float,
) -> NDArray[np.float32]:
    """Calculate temperature-dependent specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: Air temperature, [C]
        molar_heat_capacity_air: Molar heat capacity of air, [J mol-1 C-1]
        specific_heat_equ_factor_1: Factor in calculation of molar specific heat of air
        specific_heat_equ_factor_2: Factor in calculation of molar specific heat of air

    Returns:
        specific heat of air at constant pressure, [J mol-1 K-1]
    """
    return (
        specific_heat_equ_factor_1 * temperature**2
        + specific_heat_equ_factor_2 * temperature
        + molar_heat_capacity_air
    )


def calculate_latent_heat_vaporisation(
    temperature: NDArray[np.float32],
    celsius_to_kelvin: float,
    latent_heat_vap_equ_factor_1: float,
    latent_heat_vap_equ_factor_2: float,
) -> NDArray[np.float32]:
    """Calculate latent heat of vaporisation.

    Implementation after Eq. 8, :cite:t:`henderson-sellers_new_1984`.

    Args:
        temperature: Air temperature, [C]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin
        latent_heat_vap_equ_factor_1: Factor in calculation of latent heat of
            vaporisation
        latent_heat_vap_equ_factor_2: Factor in calculation of latent heat of
            vaporisation

    Returns:
        latent heat of vaporisation, [kJ kg-1]
    """
    temperature_kelvin = temperature + celsius_to_kelvin
    return (
        latent_heat_vap_equ_factor_1
        * (temperature_kelvin / (temperature_kelvin - latent_heat_vap_equ_factor_2))
        ** 2
    ) / 1000.0
