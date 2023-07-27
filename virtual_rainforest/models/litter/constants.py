"""The :mod:`~virtual_rainforest.models.litter.constants` module contains
constants and parameters for the
:mod:`~virtual_rainforest.models.litter.litter_model`. These parameters are constants
in that they should not be changed during a particular simulation.
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass(frozen=True)
class LitterConsts:
    """Dataclass to store all constants for the `litter` model."""
