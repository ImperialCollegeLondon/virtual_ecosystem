"""The ``models.soil.constants`` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.soil` module
"""  # noqa: D205, D415

from dataclasses import dataclass

# TODO - Need to check for the sources of all constants defined here as part of checking
# whether Abramoff et al.'s parameterisation works


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

MAX_UPTAKE_RATE_LABILE_C = 0.35
"""Maximum (theoretical) rate at which microbes can take up labile carbon. Units given
as [g C m^-2 day^-1], this definitely warrants investigation."""

NECROMASS_ADSORPTION_RATE = 0.025
"""Rate at which necromass is adsorbed by soil minerals [day^-1].

Taken from :cite:t:`abramoff_millennial_2018`, where it was obtained by calibration.
"""

HALF_SAT_MICROBIAL_ACTIVITY = 7.2
"""Half saturation constant for microbial activity (with increasing biomass density).

Units given as [g C m-2], this is a clear place where I need to look at units (and
parameterisation) more carefully"""


@dataclass
class CarbonUseEfficiency:
    """Collection of carbon use efficiency parameters.

    Taken from :cite:t:`abramoff_millennial_2018`, more investigation required in future
    """

    reference_cue = 0.6
    """Carbon use efficiency of community at the reference temperature [no units]"""
    reference_temp = 15.0
    """Reference temperature [degrees C]"""
    cue_with_temperature = -0.012
    """Change in carbon use efficiency with increasing temperature [degree C^-1]."""
