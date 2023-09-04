"""This submodule contains a set of dataclasses containing constants used in the
:mod:`~virtual_rainforest.models.plants` module.
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass(frozen=True)
class PlantsConsts:
    """Constants for the :mod:`~virtual_rainforest.models.plants`model."""

    placeholder: float = 1.0
    """Placeholder constant."""
