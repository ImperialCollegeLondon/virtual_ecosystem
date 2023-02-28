"""The ``models.abiotic.models`` module contains a set of general functions and
universal constants that are shared across submodels in the abiotic model.
"""  # noqa: D205, D415

from dataclasses import dataclass

from xarray import DataArray


@dataclass
class AbioticConstants:
    """Abiotic constants class."""

    celsius_to_kelvin = 273.15
    """Factor to convert temperature in Celsius to absolute temperature in Kelvin."""
    standard_mole = 44.6
    """Moles of ideal gas in 1 m3 air at standard atmosphere."""
    molar_heat_capacity_air = 29.19
    """Molar heat capacity of air, [J mol-1 C-1]."""
    gravity = 9.81
    """Gravitational acceleration constant, [m s-1]."""
    stefan_boltzmann_constant: float = 5.67e-8
    """Stefan-Boltzmann constant, [W m-2 K-4]"""


def calc_molar_density_air(
    temperature: DataArray,
    atmospheric_pressure: DataArray,
    standard_mole: float = AbioticConstants.standard_mole,
    celsius_to_kelvin: float = AbioticConstants.celsius_to_kelvin,
) -> DataArray:
    """Calculate temperature-dependent molar density of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: temperature, [C]
        atmospheric_pressure: atmospheric pressure, [kPa]
        celsius_to_kelvin: Factor to convert temperature in Celsius to absolute
            temperature in Kelvin

    Returns:
        molar density of air
    """

    temperature_kelvin = temperature + celsius_to_kelvin
    molar_density_air = (
        standard_mole
        * (temperature_kelvin / atmospheric_pressure)
        * (celsius_to_kelvin / temperature_kelvin)
    )
    return molar_density_air


def calc_specific_heat_air(
    temperature: DataArray,
    molar_heat_capacity_air: float = AbioticConstants.molar_heat_capacity_air,
) -> DataArray:
    """Calculate molar temperature-dependent specific heat of air.

    Implementation after :cite:t:`maclean_microclimc_2021`.

    Args:
        temperature: temperature, [C]
        molar_heat_capacity_air: molar heat capacity, [J mol-1 C-1]

    Returns:
        specific heat of air at constant pressure (J mol-1 K-1)
    """
    return 2e-05 * temperature**2 + 0.0002 * temperature + molar_heat_capacity_air
