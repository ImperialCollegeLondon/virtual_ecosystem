"""The ``models.abiotic.abiotic_tools`` module contains a set of general functions and
universal constants that are shared across submodules in the
:mod:`~virtual_rainforest.models.abiotic` model.
"""  # noqa: D205, D415

from dataclasses import dataclass
from typing import List

import numpy as np
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
    von_karmans_constant: float = 0.4
    """Von Karman's constant, unitless constant describing the logarithmic velocity
    profile of a turbulent fluid near a no-slip boundary."""


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
        molar density of air, [kg m-3]
    """

    temperature_kelvin = temperature + celsius_to_kelvin

    return (
        standard_mole
        * (temperature_kelvin / atmospheric_pressure)
        * (celsius_to_kelvin / temperature_kelvin)
    ).rename("molar_density_air")


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
        specific heat of air at constant pressure, [J mol-1 K-1]
    """
    return (
        2e-05 * temperature**2 + 0.0002 * temperature + molar_heat_capacity_air
    ).rename("specific_heat_air")


def calculate_latent_heat_vaporisation(temperature: DataArray) -> DataArray:
    """Calculate latent heat of vaporisation.

    Args:
        temperature: temperature, [C]

    Returns:
        latent heat of vaporisation, [J kg-1]
    """

    latent_heat_vaporisation = (-42.575 * temperature + 44994).rename(
        "latent_heat_vaporisation"
    )
    return latent_heat_vaporisation


def calculate_aero_resistance(
    wind_speed: DataArray,
    heat_transfer_coefficient: float,
) -> DataArray:
    """Calculate aerodynamic resistance.

    Args:
        wind_speed: wind speed at each canopy height, [m s-1]
        heat_transfer_coefficient: factor that describes heat capacity of medium

    Returns:
        aerodynamic resistance
    """

    return DataArray(heat_transfer_coefficient / np.sqrt(wind_speed)).rename(
        "areo_resistance"
    )


def set_layer_roles(canopy_layers: int, soil_layers: int) -> List[str]:
    """Define a list of layer roles.

    Args:
        canopy_layers: number of canopy layers
        soil_layers: number of soil layers

    Returns:
        List of canopy layer roles
    """
    return (
        ["soil"] * soil_layers
        + ["surface"]
        + ["below"]
        + ["canopy"] * canopy_layers
        + ["above"]
    )
