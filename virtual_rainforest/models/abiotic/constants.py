"""The ``models.abiotic.constants`` module contains a set of dataclasses which contain
parameters required by the broader :mod:`~virtual_rainforest.models.abiotic` model.
These parameters are constants in that they should not be changed during a particular
simulation.
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_rainforest.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `abiotic` model."""

    celsius_to_kelvin: float = 273.15
    """Factor to convert temperature in Celsius to absolute temperature in Kelvin."""
    standard_pressure: float = 101.3
    """Standard atmospheric pressure, [kPa]"""
    standard_mole: float = 44.6
    """Moles of ideal gas in 1 m^3 air at standard atmosphere."""
    molar_heat_capacity_air: float = 29.19
    """Molar heat capacity of air, [J mol-1 K-1]."""
    gravity: float = 9.81
    """Gravitational acceleration constant, [m s-1]."""
    stefan_boltzmann_constant: float = 5.67e-8
    """Stefan-Boltzmann constant, [W m-2 K-4]"""
    von_karmans_constant: float = 0.4
    """Von Karman's constant, unitless constant describing the logarithmic velocity
    profile of a turbulent fluid near a no-slip boundary."""
    specific_heat_equ_factor_1: float = 2e-05
    """Factor in calculation of molar specific heat of air."""
    specific_heat_equ_factor_2: float = 0.0002
    """Factor in calculation of molar specific heat of air."""
    latent_heat_vap_equ_factor_1: float = 1.91846e6
    """Factor in calculation of latent heat of vaporisation, (Henderson-Sellers, 1984).
    """
    latent_heat_vap_equ_factor_2: float = 33.91
    """Factor in calculation of latent heat of vaporisation, (Henderson-Sellers, 1984).
    """

    zero_plane_scaling_parameter: float = 7.5
    """Control parameter for scaling zero displacement/height
        :cite:p:`raupach_simplified_1994`."""
    substrate_surface_drag_coefficient: float = 0.003
    """Substrate-surface drag coefficient :cite:p:`maclean_microclimc_2021`."""
    roughness_element_drag_coefficient: float = 0.3
    """Roughness-element drag coefficient :cite:p:`maclean_microclimc_2021`."""
    roughness_sublayer_depth_parameter: float = 0.193
    """Parameter characterizes the roughness sublayer depth
        :cite:p:`maclean_microclimc_2021`."""
    max_ratio_wind_to_friction_velocity: float = 0.3
    """Maximum ratio of wind velocity to friction velocity
        :cite:p:`maclean_microclimc_2021`."""
    drag_coefficient: float = 0.2
    """Drag coefficient :cite:p:`maclean_microclimc_2021`."""
    relative_turbulence_intensity: float = 0.5
    """Relative turbulence intensity :cite:p:`maclean_microclimc_2021`."""
    diabatic_correction_factor_below: float = 1
    "Diabatic correction factor below canopy."
    mixing_length_factor: float = 0.32
    """Factor in calculation of mixing length :cite:p:`maclean_microclimc_2021`."""
    min_relative_turbulence_intensity: float = 0.36
    """minimum relative turbulence intensity, default value from Shaw et al (1974)
    Agricultural Meteorology, 13: 419-425. """
    max_relative_turbulence_intensity: float = 0.9
    """maximum relative turbulence intensity, default value from Shaw et al (1974)
        Agricultural Meteorology, 13: 419-425."""
    min_wind_speed_above_canopy: float = 0.55
    """Minimum wind speed above the canopy, [m/s]."""
    min_roughness_length: float = 0.05
    """Minimum roughness length, [m]."""
