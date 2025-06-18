"""The `models.animal.protocols` module contains a class provides eatability definition
used by AnimalCohorts, PlantResources, and Carcasses in the
:mod:`~virtual_ecosystem.models.animal` module.
"""  # noqa: D205

from typing import Protocol, runtime_checkable

from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.cnp import CNP
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup


class Consumer(Protocol):
    """This is the protocol for defining consumers (currently just AnimalCohort)."""

    functional_group: FunctionalGroup
    individuals: int


class Pool(Protocol):
    """This is a protocol for defining dummy abiotic pools containing energy."""

    mass_current: float


class DecayPool(Protocol):
    """Defines biotic pools containing both accessible and inaccessible nutrients."""

    scavengeable_carbon: float

    decomposed_carbon: float

    scavengeable_nitrogen: float

    decomposed_nitrogen: float

    scavengeable_phosphorus: float

    decomposed_phosphorus: float


class Resource(Protocol):
    """This is the protocol for defining what classes work as trophic resources."""

    cell_id: int
    vertical_occupancy: VerticalOccupancy

    @property
    def mass_current(self) -> float:
        """The mass_current method defines current total mass."""
        ...

    def get_eaten(
        self,
        consumed_mass: float,
        consumer: Consumer,
    ) -> tuple[dict[str, float], dict[str, float]]:
        """The get_eaten method defines a resource."""
        ...


@runtime_checkable
class ScavengeableResource(Protocol):
    """The protocol for linking the get_eaten mixin with CNP."""

    scavengeable_cnp: CNP
    decomposed_cnp: CNP
