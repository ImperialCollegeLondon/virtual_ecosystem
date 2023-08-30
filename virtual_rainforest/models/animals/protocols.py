"""The `models.animals.protocols` module contains a class provides eatability definition
used by AnimalCohorts, PlantCommunity, and Carcasses in the
:mod:`~virtual_rainforest.models.animals` module.
"""  # noqa: D205, D415

from typing import Protocol

from virtual_rainforest.models.animals.functional_group import FunctionalGroup


class Consumer(Protocol):
    """This is the protocol for defining consumers (currently just AnimalCohort)."""

    intake_rate: float
    functional_group: FunctionalGroup
    individuals: int


class Pool(Protocol):
    """This is a protocol for defining dummy abiotic pools containing energy."""

    stored_energy: float


class DecayPool(Protocol):
    """Defines biotic pools containing both accessible and inaccessible energy."""

    scavengeable_energy: float

    decomposed_energy: float


class Resource(Protocol):
    """This is the protocol for defining what classes work as trophic resources."""

    stored_energy: float

    def get_eaten(self, consumer: Consumer, pool: DecayPool) -> float:
        """The get_eaten method defines a resource."""
        ...
