"""The :mod:`~virtual_rainforest.models.animals.carcasses_and_poo` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. And the moment this consists of animal carcasses and excrement.
"""  # noqa: #D205, D415


from dataclasses import dataclass


@dataclass
class CarcassPool:
    """This is a class of carcass pools."""

    stored_energy: float
    """The amount of energy in the carcass pool [J]."""
    position: int
    """The grid position of the carcass pool."""


@dataclass
class ExcrementPool:
    """This class store information about the amount of excrement in each grid cell."""

    stored_energy: float
    """The amount of energy in the excrement pool [J]."""
    position: int
    """The grid position of the excrement pool."""
