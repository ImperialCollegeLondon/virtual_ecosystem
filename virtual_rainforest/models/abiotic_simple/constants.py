"""The ``models.abiotic_simple.constants`` module contains a set of dataclasses
containing parameters  required by the broader
:mod:`~virtual_rainforest.models.abiotic_simple` model. These parameters are constants
in that they should not be changed during a particular simulation.
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass(frozen=True)
class AbioticSimpleConsts:
    """Dataclass to store all constants for the `abiotic_simple` model."""

    air_temperature_gradient: float = -1.27
    """Gradient for linear regression to calculate air temperature as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`"""

    relative_humidity_gradient: float = 5.4
    """Gradient for linear regression to calculate relative humidity as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`"""

    vapour_pressure_deficit_gradient: float = -252.24
    """Gradient for linear regression to calculate vapour pressure deficit as a function
    of leaf area index from :cite:t:`hardwick_relationship_2015`"""

    saturation_vapour_pressure_factor1: float = 0.61078
    """factor 1 for saturation vapour pressure calculation."""
    saturation_vapour_pressure_factor2: float = 7.5
    """factor 2 for saturation vapour pressure calculation."""
    saturation_vapour_pressure_factor3: float = 237.3
    """factor 3 for saturation vapour pressure calculation."""
