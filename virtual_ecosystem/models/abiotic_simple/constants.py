"""The ``models.abiotic_simple.constants`` module contains a set of dataclasses
containing parameters required by the :mod:`~virtual_ecosystem.models.abiotic_simple`
model. These parameters are constants in that they should not be changed during a
particular simulation.
"""  # noqa: D205

from dataclasses import dataclass, field

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class AbioticSimpleConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `abiotic_simple` model."""

    saturation_vapour_pressure_factors: list[float] = field(
        default_factory=lambda: [0.61078, 7.5, 237.3]
    )
    """Factors for saturation vapour pressure calculation."""


@dataclass(frozen=True)
class AbioticSimpleBounds(ConstantsDataclass):
    """Upper and lower bounds for abiotic variables.

    When a values falls outside these bounds, it is set to the bound value.
    NOTE that this approach does not conserve energy and matter in the system.
    This will be implemented at a later stage.
    """

    air_temperature: tuple[float, float, float] = (-20.0, 80.0, -1.27)
    """Bounds and gradient for air temperature, [C].

    Gradient for linear regression to calculate air temperature as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`.
    """

    relative_humidity: tuple[float, float, float] = (0.0, 100.0, 5.4)
    """Bounds and gradient for relative humidity, dimensionless.

    Gradient for linear regression to calculate relative humidity as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`.
    """

    vapour_pressure_deficit: tuple[float, float, float] = (0.0, 10.0, -252.24)
    """Bounds and gradient for vapour pressure deficit, [kPa].
    
    Gradient for linear regression to calculate vapour pressure deficit as a function of
    leaf area index from :cite:t:`hardwick_relationship_2015`.
    """

    wind_speed: tuple[float, float, float] = (0.001, 100.0, -0.1)
    """Bounds and gradient for wind speed, [m s-1].
    
    Gradient for linear regression to calculate wind speed as a function of
    leaf area index. The value is choses arbitrarily and needs to be replaced with
    observations.
    """

    soil_temperature: tuple[float, float] = (-10.0, 50.0)
    """Bounds for soil temperature, [C]."""
