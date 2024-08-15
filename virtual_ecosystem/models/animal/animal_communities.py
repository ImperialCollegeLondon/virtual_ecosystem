"""The ''animal'' module provides animal module functionality."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import chain

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
from virtual_ecosystem.models.animal.constants import AnimalConsts
from virtual_ecosystem.models.animal.decay import CarcassPool, ExcrementPool
from virtual_ecosystem.models.animal.functional_group import (
    FunctionalGroup,
)
from virtual_ecosystem.models.animal.plant_resources import PlantResources


class AnimalCommunity:
    """This is a class for the animal community of a grid cell.

    This class manages the animal cohorts present in a grid cell and provides methods
    that need to loop over all cohorts, move cohorts to new grids, or manage an
    interaction between two cohorts.

    Args:
        functional_groups: A list of FunctionalGroup objects
        data: The core data object
        community_key: The integer key of the cell id for this community
        neighbouring_keys: A list of cell id keys for neighbouring communities
        get_community_by_key: A function to return a designated AnimalCommunity by
            integer key.
    """

    def __init__(
        self,
        functional_groups: list[FunctionalGroup],
        data: Data,
        community_key: int,
        neighbouring_keys: list[int],
        get_community_by_key: Callable[[int], AnimalCommunity],
        constants: AnimalConsts = AnimalConsts(),
    ) -> None:
        # The constructor of the AnimalCommunity class.
        self.data = data
        """A reference to the core data object."""
        self.functional_groups = tuple(functional_groups)
        """A list of all FunctionalGroup types in the model."""
        self.community_key = community_key
        """Integer designation of the community in the model grid."""
        self.neighbouring_keys = neighbouring_keys
        """List of integer keys of neighbouring communities."""
        self.get_community_by_key = get_community_by_key
        """Callable get_community_by_key from AnimalModel."""
        self.constants = constants
        """Animal constants."""
        self.animal_cohorts: dict[str, list[AnimalCohort]] = {
            k.name: [] for k in self.functional_groups
        }
        """A dictionary of lists of animal cohorts keyed by functional group, containing
        only those cohorts having their territory centroid in this community."""
        self.occupancy: dict[str, dict[AnimalCohort, float]] = {
            k.name: {} for k in self.functional_groups
        }
        """A dictionary of dictionaries of animal cohorts keyed by functional group and 
        cohort, with the value being the occupancy percentage."""
        self.carcass_pool: CarcassPool = CarcassPool(10000.0, 0.0)
        """A pool for animal carcasses within the community."""
        self.excrement_pool: ExcrementPool = ExcrementPool(10000.0, 0.0)
        """A pool for excrement within the community."""
        self.plant_community: PlantResources = PlantResources(
            data=self.data,
            cell_id=self.community_key,
            constants=self.constants,
        )

    @property
    def all_animal_cohorts(self) -> Iterable[AnimalCohort]:
        """Get an iterable of all animal cohorts w/ proportion in the community.

        This property provides access to all the animal cohorts contained
        within this community class.

        Returns:
            Iterable[AnimalCohort]: An iterable of AnimalCohort objects.
        """
        return chain.from_iterable(self.animal_cohorts.values())

    @property
    def all_occupying_cohorts(self) -> Iterable[AnimalCohort]:
        """Get an iterable of all occupying cohorts w/ proportion in the community.

        This property provides access to all the animal cohorts contained
        within this community class.

        Returns:
            Iterable[AnimalCohort]: An iterable of AnimalCohort objects.
        """
        return chain.from_iterable(
            cohort_dict.keys() for cohort_dict in self.occupancy.values()
        )
