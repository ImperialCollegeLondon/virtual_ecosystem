"""The ``models.microclimate.constants`` module contains a set of dataclasses
containing parameters required by the :mod:`~virtual_ecosystem.models.microclimate`
model. These parameters are constants in that they should not be changed during a
particular simulation.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class MicroclimateConsts(ConstantsDataclass):
    """Dataclass to store all constants for the `microclimate` model."""

    canopy_temperature_ini_factor: float = 0.01
    """Factor used to initialise canopy temperature as a function of air temperature and
    absorbed shortwave radiation."""

    light_extinction_coefficient: float = 0.01
    """Light extinction coefficient for canopy."""
