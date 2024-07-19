"""The ''animal'' module provides animal module functionality."""  # noqa: #D205, D415

from collections.abc import Callable, MutableSequence, Sequence

from virtual_ecosystem.models.animal.protocols import (
    Community,
    Consumer,
    DecayPool,
    Resource,
    Territory,
)


class AnimalTerritory:
    """This class defines a territory occupied by an animal cohort.

    The purpose of this class is to function as an intermediary between cohorts
    and the plants, pools, and prey of the grid cells that the cohort occupies. It
    should have a total area, a list of the specific grid cells within it, and lists of
    the plants, pools, and prey.

    The key assumption is that an animal cohort is equally distributed across its
    territory for the time-step.



    Args:
        grid_cell_keys: A list of grid cell ids that make up the territory.
        get_community_by_key: A function to return an AnimalCommunity for a given
        integer key.
    """

    def __init__(
        self,
        centroid: int,
        grid_cell_keys: list[int],
        get_community_by_key: Callable[[int], Community],
    ) -> None:
        # The constructor of the AnimalTerritory class.
        self.centroid = centroid
        """The centroid community of the territory (not technically a centroid)."""
        self.grid_cell_keys = grid_cell_keys
        """A list of grid cells present in the territory."""
        self.get_community_by_key = get_community_by_key
        """A list of animal communities present in the territory."""
        self.territory_prey: Sequence[Consumer] = []
        """A list of animal prey present in the territory."""
        self.territory_plants: Sequence[Resource] = []
        """A list of plant resources present in the territory."""
        self.territory_excrement: Sequence[DecayPool] = []
        """A list of excrement pools present in the territory."""
        self.territory_carcasses: Sequence[DecayPool] = []
        """A list of carcass pools present in the territory."""

    def update_territory(self, consumer_cohort: Consumer) -> None:
        """Update territory details at initialization and after migration.

        Args:
            consumer_cohort: The AnimalCohort possessing the territory.

        """

        self.territory_prey = self.get_prey(consumer_cohort)
        self.territory_plants = self.get_plant_resources()
        self.territory_excrement = self.get_excrement_pools()
        self.territory_carcasses = self.get_carcass_pools()

    def get_prey(self, consumer_cohort: Consumer) -> MutableSequence[Consumer]:
        """Collect suitable prey from all grid cells in the territory.

        TODO: This is probably not the best way to go about this. Maybe alter collect
        prey to take the animal community list instead. Prey is probably too dynamic to
        store in this way.

        Args:
            consumer_cohort: The AnimalCohort for which a prey list is being collected.

        Returns:
            A list of AnimalCohorts that can be preyed upon.
        """
        prey: MutableSequence = []
        for cell_id in self.grid_cell_keys:
            community = self.get_community_by_key(cell_id)
            prey.extend(community.collect_prey(consumer_cohort))
        return prey

    def get_plant_resources(self) -> MutableSequence[Resource]:
        """Collect plant resources from all grid cells in the territory.

        TODO: Update internal plant resource generation with a real link to the plant
        model.

        Returns:
            A list of PlantResources available in the territory.
        """
        plant_resources: MutableSequence = []
        for cell_id in self.grid_cell_keys:
            community = self.get_community_by_key(cell_id)
            plant_resources.append(community.plant_community)
        return plant_resources

    def get_excrement_pools(self) -> MutableSequence[DecayPool]:
        """Combine excrement pools from all grid cells in the territory.

        Returns:
            A list of ExcrementPools combined from all grid cells.
        """
        total_excrement: MutableSequence = []
        for cell_id in self.grid_cell_keys:
            community = self.get_community_by_key(cell_id)
            total_excrement.append(community.excrement_pool)
        return total_excrement

    def get_carcass_pools(self) -> MutableSequence[DecayPool]:
        """Combine carcass pools from all grid cells in the territory.

        Returns:
            A list of CarcassPools combined from all grid cells.
        """
        total_carcass: MutableSequence = []
        for cell_id in self.grid_cell_keys:
            community = self.get_community_by_key(cell_id)
            total_carcass.append(community.carcass_pool)
        return total_carcass

    def find_intersecting_carcass_pools(
        self, animal_territory: "Territory"
    ) -> MutableSequence[DecayPool]:
        """Find the carcass pools of the intersection of two territories.

        Args:
            animal_territory: Another AnimalTerritory to find the intersection with.

        Returns:
            A list of CarcassPools in the intersecting grid cells.
        """
        intersecting_keys = set(self.grid_cell_keys) & set(
            animal_territory.grid_cell_keys
        )
        intersecting_carcass_pools = []
        for cell_id in intersecting_keys:
            community = self.get_community_by_key(cell_id)
            intersecting_carcass_pools.append(community.carcass_pool)
        return intersecting_carcass_pools


def bfs_territory(
    centroid_key: int, target_cell_number: int, cell_nx: int, cell_ny: int
) -> list[int]:
    """Performs breadth-first search (BFS) to generate a list of territory cells.

    BFS does some slightly weird stuff on a grid of squares but behaves properly on a
    graph. As we are talking about moving to a graph anyway, I can leave it like this
    and make adjustments for diagonals if we decide to stay with squares/cells.

    TODO: Revise for diagonals if we stay on grid squares/cells.
    TODO: might be able to save time with an ifelse for small territories

    Args:
        centroid_key: The community key anchoring the territory.
        target_cell_number: The number of grid cells in the territory.
        cell_nx: Number of cells along the x-axis.
        cell_ny: Number of cells along the y-axis.

    Returns:
        A list of grid cell keys representing the territory.
    """

    # Convert centroid key to row and column indices
    row, col = divmod(centroid_key, cell_nx)

    # Initialize the territory cells list with the centroid key
    territory_cells = [centroid_key]

    # Define the possible directions for BFS traversal: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Set to keep track of visited cells to avoid revisiting
    visited = set(territory_cells)

    # Queue for BFS, initialized with the starting position (row, col)
    queue = [(row, col)]

    # Perform BFS until the queue is empty or we reach the target number of cells
    while queue and len(territory_cells) < target_cell_number:
        # Dequeue the next cell to process
        r, c = queue.pop(0)

        # Explore all neighboring cells in the defined directions
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # Check if the new cell is within grid bounds
            if 0 <= nr < cell_ny and 0 <= nc < cell_nx:
                new_cell = nr * cell_nx + nc
                # If the cell hasn't been visited, mark it as visited and add to the
                # territory
                if new_cell not in visited:
                    visited.add(new_cell)
                    territory_cells.append(new_cell)
                    queue.append((nr, nc))
                    # If we have reached the target number of cells, exit the loop
                    if len(territory_cells) >= target_cell_number:
                        break

    return territory_cells
