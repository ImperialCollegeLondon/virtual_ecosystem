"""The `models.animal.protocols` module contains a class provides eatability definition
used by AnimalCohorts, PlantResources, and Carcasses in the
:mod:`~virtual_ecosystem.models.animal` module.
"""  # noqa: D205

from collections.abc import Sequence
from typing import Protocol

from virtual_ecosystem.models.animal.functional_group import FunctionalGroup


class Consumer(Protocol):
    """This is the protocol for defining consumers (currently just AnimalCohort)."""

    functional_group: FunctionalGroup
    individuals: int
    mass_current: float

    def get_eaten(
        self,
        potential_consumed_mass: float,
        predator: "Consumer",
        carcass_pool: "DecayPool",
    ) -> float:
        """The get_eaten method partially defines a consumer."""
        ...


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
        self, consumed_mass: float, consumer: Consumer, pools: Sequence[DecayPool]
    ) -> float:
        """The get_eaten method defines a resource."""
        ...


class Territory(Protocol):
    """This is the protocol for defining territories.

    Currently, this is an intermediary to prevent circular reference between territories
    and cohorts.

    """

    grid_cell_keys: Sequence[int]

    def get_prey(self, consumer_cohort: Consumer) -> Sequence[Consumer]:
        """The get_prey method partially defines a territory."""
        ...

    def get_plant_resources(self) -> Sequence[Resource]:
        """The get_prey method partially defines a territory."""
        ...

    def get_excrement_pools(self) -> Sequence[DecayPool]:
        """The get_prey method partially defines a territory."""
        ...

    def get_carcass_pools(self) -> Sequence[DecayPool]:
        """The get_prey method partially defines a territory."""
        ...
