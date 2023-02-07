"""The `models.soil.carbon` module  simulates the soil carbon cycle for the Virtual
Rainforest. At the moment only two pools are modelled, these are low molecular weight
carbon (LMWC) and mineral associated organic matter (MAOM). More pools and their
interactions will be added at a later date.
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class BindingWithPH:
    """From linear regression (Mayes et al. (2012))."""

    slope: float = -0.186
    """Units of pH^-1."""
    intercept: float = -0.216
    """Unit less."""


@dataclass
class MaxSorptionWithClay:
    """From linear regression (Mayes et al. (2012))."""

    slope: float = 0.483
    """Units of (% clay)^-1."""
    intercept: float = 2.328
    """Unit less."""


@dataclass
class MoistureScalar:
    """Used in Abramoff et al. (2018), but can't trace it back to anything concrete."""

    coefficient: float = 30.0
    """Value at zero relative water content (RWC) [unit less]."""
    exponent: float = 9.0
    """Units of (RWC)^-1"""


@dataclass
class TempScalar:
    """Used in Abramoff et al. (2018), but can't trace it back to anything concrete."""

    t_1: float = 15.4
    """Unclear exactly what this parameter is [degrees C]"""
    t_2: float = 11.75
    """Unclear exactly what this parameter is [units unclear]"""
    t_3: float = 29.7
    """Unclear exactly what this parameter is [units unclear]"""
    t_4: float = 0.031
    """Unclear exactly what this parameter is [units unclear]"""
    ref_temp: float = 30.0
    """Reference temperature [degrees C]"""
