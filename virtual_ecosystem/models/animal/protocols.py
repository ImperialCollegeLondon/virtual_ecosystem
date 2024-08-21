"""The `models.animal.protocols` module contains a class provides eatability definition
used by AnimalCohorts, PlantResources, and Carcasses in the
:mod:`~virtual_ecosystem.models.animal` module.
"""  # noqa: D205

from typing import Protocol

from virtual_ecosystem.models.animal.functional_group import FunctionalGroup


class Consumer(Protocol):
    """This is the protocol for defining consumers (currently just AnimalCohort)."""

    functional_group: FunctionalGroup
    individuals: int


class Pool(Protocol):
    """This is a protocol for defining dummy abiotic pools containing energy."""

    mass_current: float


class DecayPool(Protocol):
    """Defines biotic pools containing both accessible and inaccessible energy."""

    scavengeable_energy: float

    decomposed_energy: float


class Resource(Protocol):
    """This is the protocol for defining what classes work as trophic resources."""

    mass_current: float

    def get_eaten(
        self, consumed_mass: float, consumer: Consumer, pool: DecayPool
    ) -> float:
        """The get_eaten method defines a resource."""
        ...
