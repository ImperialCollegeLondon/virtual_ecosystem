"""The ``models.abiotic_simple.constants`` module contains a set of dataclasses
containing parameters  required by the broader
:mod:`~virtual_ecosystem.models.abiotic_simple` model. These parameters are constants
in that they should not be changed during a particular simulation.
"""  # noqa: D205, D415

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
    """Upper/lower bounds for abiotic variables and gradients for linear regression.

    Bounds are set following `pyrealm`. When a values falls outside these bounds, it is
    set to the bound value. Note that this approach does not conserve energy and matter
    in the system. This will be implemented at a later stage.

    Gradients for linear regression to calculate air temperature, relative humidity, and
    vapour pressure deficit as a function of leaf area index taken from
    :cite:t:`hardwick_relationship_2015`.
    """

    air_temperature: tuple[float, float, float] = (-25.0, 80.0, -1.27)
    """Bounds and gradients for air temperature, [C]."""

    relative_humidity: tuple[float, float, float] = (0.0, 100.0, 5.4)
    """Bounds and gradients for relative humidity, dimensionless."""

    vapour_pressure_deficit: tuple[float, float, float] = (0.0, 10.0, -252.24)
    """Bounds and gradients for vapour pressure deficit, [kPa]."""

    soil_temperature: tuple[float, float] = (-25.0, 50.0)
    """Bounds for soil temperature, [C]."""
