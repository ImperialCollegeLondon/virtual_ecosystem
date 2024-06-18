"""This submodule contains a set of dataclasses containing constants used
in the :mod:`~virtual_ecosystem.models.plants` module.
"""  # noqa: D205

from dataclasses import dataclass

from virtual_ecosystem.core.constants_class import ConstantsDataclass


@dataclass(frozen=True)
class PlantsConsts(ConstantsDataclass):
    """Constants for the :mod:`~virtual_ecosystem.models.plants` model."""

    placeholder: float = 1.0
    """Placeholder constant."""
