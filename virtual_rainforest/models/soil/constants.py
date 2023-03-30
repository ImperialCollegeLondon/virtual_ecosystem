"""The ``models.soil.constants`` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.soil` module
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class BindingWithPH:
    """From linear regression :cite:p:`mayes_relation_2012`."""

    slope: float = -0.186
    """Units of pH^-1."""
    intercept: float = -0.216
    """Unit less."""


@dataclass
class MaxSorptionWithClay:
    """From linear regression :cite:p:`mayes_relation_2012`."""

    slope: float = 0.483
    """Units of (% clay)^-1."""
    intercept: float = 2.328
    """Unit less."""


@dataclass
class MoistureScalar:
    """Used in :cite:t:`abramoff_millennial_2018`, can't find original source."""

    coefficient: float = 30.0
    """Value at zero relative water content (RWC) [unit less]."""
    exponent: float = 9.0
    """Units of (RWC)^-1"""


@dataclass
class TempScalar:
    """Used in :cite:t:`abramoff_millennial_2018`, can't find original source."""

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


MICROBIAL_TURNOVER_RATE = 0.036
"""Microbial turnover rate [day^-1], this isn't a constant but often treated as one."""
