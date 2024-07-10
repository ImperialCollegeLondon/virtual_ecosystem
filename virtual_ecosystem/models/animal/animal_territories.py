"""The ''animal'' module provides animal module functionality."""  # noqa: #D205, D415

from collections.abc import Callable

from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
from virtual_ecosystem.models.animal.animal_communities import AnimalCommunity
from virtual_ecosystem.models.animal.decay import CarcassPool, ExcrementPool
from virtual_ecosystem.models.animal.plant_resources import PlantResources


class AnimalTerritory:
    """This class defines a territory occupied by an animal cohort.

    The purpose of this class is to function as an intermediary between cohorts
    and the plants, pools, and prey of the grid cells that the cohort occupies. It
    should have a total area, a list of the specific grid cells within it, and lists of
    the plants, pools, and prey.

    The key assumption is that an animal cohort is equally distributed across its
    territory for the time-step.



    Args:
        grid_cells: A list of grid cell ids that make up the territory.
        get_animal_community: A function to return an AnimalCommunity for a given grid
          cell id.
    """

    def __init__(
        self,
        grid_cells: list[int],
        get_animal_community: Callable[[int], AnimalCommunity],
    ) -> None:
        # The constructor of the AnimalTerritory class.
        self.grid_cells = grid_cells
        """A list of grid cells present in the territory."""
        self.get_animal_community = get_animal_community
        """A list of animal communities present in the territory."""
        self.territory_prey: list[AnimalCohort] = []
        """A list of animal prey present in the territory."""
        self.territory_plants: list[PlantResources] = []
        """A list of plant resources present in the territory."""
        self.territory_excrement: list[ExcrementPool] = []
        """A list of excrement pools present in the territory."""
        self.territory_carcasses: list[CarcassPool] = []
        """A list of carcass pools present in the territory."""

    def update_territory(self, consumer_cohort: AnimalCohort) -> None:
        """Update territory details at initialization and after migration.

        Args:
            consumer_cohort: The AnimalCohort possessing the territory.

        """

        self.territory_prey = self.get_prey(consumer_cohort)
        self.territory_plants = self.get_plant_resources()
        self.territory_excrement = self.get_excrement_pools()
        self.territory_carcasses = self.get_carcass_pool()

    def get_prey(self, consumer_cohort: AnimalCohort) -> list[AnimalCohort]:
        """Collect suitable prey from all grid cells in the territory.

        TODO: This is probably not the best way to go about this. Maybe alter collect
        prey to take the animal community list instead. Prey is probably too dynamic to
        store in this way.

        Args:
            consumer_cohort: The AnimalCohort for which a prey list is being collected.

        Returns:
            A list of AnimalCohorts that can be preyed upon.
        """
        prey = []
        for cell_id in self.grid_cells:
            community = self.get_animal_community(cell_id)
            prey.extend(community.collect_prey(consumer_cohort))
        return prey

    def get_plant_resources(self) -> list[PlantResources]:
        """Collect plant resources from all grid cells in the territory.

        TODO: Update internal plant resource generation with a real link to the plant
        model.

        Returns:
            A list of PlantResources available in the territory.
        """
        plant_resources = []
        for cell_id in self.grid_cells:
            community = self.get_animal_community(cell_id)
            plant_resources.append(
                PlantResources(
                    data=community.data, cell_id=cell_id, constants=community.constants
                )
            )
        return plant_resources

    def get_excrement_pools(self) -> list[ExcrementPool]:
        """Combine excrement pools from all grid cells in the territory.

        Returns:
            A list of ExcrementPools combined from all grid cells.
        """
        total_excrement = []
        for cell_id in self.grid_cells:
            community = self.get_animal_community(cell_id)
            total_excrement.append(community.excrement_pool)
        return total_excrement

    def get_carcass_pool(self) -> list[CarcassPool]:
        """Combine carcass pools from all grid cells in the territory.

        Returns:
            A list of CarcassPools combined from all grid cells.
        """
        total_carcass = []
        for cell_id in self.grid_cells:
            community = self.get_animal_community(cell_id)
            total_carcass.append(community.carcass_pool)
        return total_carcass
