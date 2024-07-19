"""The `models.animal.protocols` module contains a class provides eatability definition
used by AnimalCohorts, PlantResources, and Carcasses in the
:mod:`~virtual_ecosystem.models.animal` module.
"""  # noqa: D205

from collections.abc import MutableSequence, Sequence
from typing import Protocol

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.functional_group import FunctionalGroup


class Community(Protocol):
    """This is the protocol for defining communities."""

    functional_groups: list[FunctionalGroup]
    data: Data
    community_key: int
    neighbouring_keys: list[int]
    carcass_pool: "DecayPool"
    excrement_pool: "DecayPool"
    plant_community: "Resource"
    occupancy: dict[str, dict["Consumer", float]]

    def get_community_by_key(self, key: int) -> "Community":
        """Method to return a designated Community by integer key."""
        ...

    def collect_prey(self, consumer_cohort: "Consumer") -> MutableSequence["Consumer"]:
        """Method to return a list of prey cohorts."""
        ...


class Consumer(Protocol):
    """This is the protocol for defining consumers (currently just AnimalCohort)."""

    functional_group: FunctionalGroup
    individuals: int
    mass_current: float
    territory: "Territory"

    def get_eaten(
        self,
        potential_consumed_mass: float,
        predator: "Consumer",
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
    territory_carcasses: Sequence[DecayPool]
    territory_excrement: Sequence[DecayPool]

    def get_prey(self, consumer_cohort: Consumer) -> MutableSequence[Consumer]:
        """The get_prey method partially defines a territory."""
        ...

    def get_plant_resources(self) -> MutableSequence[Resource]:
        """The get_prey method partially defines a territory."""
        ...

    def get_excrement_pools(self) -> MutableSequence[DecayPool]:
        """The get_prey method partially defines a territory."""
        ...

    def get_carcass_pools(self) -> MutableSequence[DecayPool]:
        """The get_prey method partially defines a territory."""
        ...

    def find_intersecting_carcass_pools(
        self, animal_territory: "Territory"
    ) -> MutableSequence[DecayPool]:
        """The find_intersecting_carcass_pools method partially defines a territory."""
        ...

    def abandon_communities(self, consumer_cohort: Consumer) -> None:
        """The abandon_communities method partially defines a territory."""
        ...
