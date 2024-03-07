"""The ``models.abiotic_simple.constants`` module contains a set of dataclasses
containing parameters  required by the broader
:mod:`~virtual_ecosystem.models.abiotic_simple` model. These parameters are constants
in that they should not be changed during a particular simulation.
"""  # noqa: D205, D415

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticSimpleConsts(ConstantsDataclass):
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


@dataclass(frozen=True)
class AbioticSimpleBounds(ConstantsDataclass):
    """Upper and lower bounds for abiotic variables.

    When a values falls outside these bounds, it is set to the bound value. Note that
    this approach does not conserve energy and matter in the system. This will be
    implemented at a later stage.
    """

    air_temperature_min: float = -20.0
    """Minimum air tempertature, [C]."""

    air_temperature_max: float = 80.0
    """Maximum air tempertature, [C]."""

    relative_humidity_min: float = 0.0
    """Minimum relative humidity, dimensionless."""

    relative_humidity_max: float = 100.0
    """Maximum relative humidity, dimensionless."""

    vapour_pressure_deficit_min: float = 0.0
    """Minimum vapour pressure deficit, [kPa]."""

    vapour_pressure_deficit_max: float = 10.0
    """Maximum vapour pressure deficit, [kPa]."""

    soil_temperature_min: float = -10.0
    """Minimum soil temperature, [C]."""

    soil_temperature_max: float = 50.0
    """Maximum soil temperature, [C]."""
