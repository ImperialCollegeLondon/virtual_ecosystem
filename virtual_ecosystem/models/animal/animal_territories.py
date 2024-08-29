"""The ''animal'' module provides animal module functionality."""  # noqa: #D205, D415

from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
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
        grid_cell_keys: A list of grid cell ids that make up the territory.
        get_community_by_key: A function to return an AnimalCommunity for a given
        integer key.
    """

    def __init__(
        self,
        centroid: int,
        grid_cell_keys: list[int],
    ) -> None:
        # The constructor of the AnimalTerritory class.
        self.centroid = centroid
        """The centroid community of the territory (not technically a centroid)."""
        self.grid_cell_keys = grid_cell_keys
        """A list of grid cells present in the territory."""

    def update_territory(self, new_grid_cell_keys: list[int]) -> None:
        """Update territory details at initialization and after migration.

        Args:
            new_grid_cell_keys: The new list of grid cell keys the territory occupies.

        """

        self.grid_cell_keys = new_grid_cell_keys

    def get_prey(
        self,
        communities: dict[int, list["AnimalCohort"]],
        consumer_cohort: "AnimalCohort",
    ) -> list["AnimalCohort"]:
        """Collect suitable prey for a given consumer cohort.

        This method filters suitable prey from the list of animal cohorts across the
        territory defined by the cohort's grid cells.

        Args:
            communities: A dictionary mapping cell IDs to sets of Consumers
              (animal cohorts).
            consumer_cohort: The Consumer for which a prey list is being collected.

        Returns:
            A sequence of Consumers that can be preyed upon.
        """
        prey_list: list[AnimalCohort] = []

        # Iterate over the grid cells in the consumer cohort's territory
        for cell_id in consumer_cohort.territory.grid_cell_keys:
            potential_prey_cohorts = communities[cell_id]

            # Iterate over each Consumer (potential prey) in the current community
            for prey_cohort in potential_prey_cohorts:
                # Skip if this cohort is not a prey of the current predator
                if prey_cohort.functional_group not in consumer_cohort.prey_groups:
                    continue

                # Get the size range of the prey this predator eats
                min_size, max_size = consumer_cohort.prey_groups[
                    prey_cohort.functional_group.name
                ]

                # Filter the potential prey cohorts based on their size
                if (
                    min_size <= prey_cohort.mass_current <= max_size
                    and prey_cohort.individuals != 0
                    and prey_cohort is not consumer_cohort
                ):
                    prey_list.append(prey_cohort)

        return prey_list

    def get_plant_resources(
        self, plant_resources: dict[int, list[PlantResources]]
    ) -> list[PlantResources]:
        """Returns a list of plant resources in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the plant resources available in those grid cells.

        Args:
            plant_resources: A dictionary of plants where keys are grid cell IDs.

        Returns:
            A list of PlantResources objects in this territory.
        """
        plant_resources_in_territory: list[PlantResources] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.grid_cell_keys:
            # Check if the cell_id is within the provided plant resources
            if cell_id in plant_resources:
                plant_resources_in_territory.extend(plant_resources[cell_id])

        return plant_resources_in_territory

    def get_excrement_pools(
        self, excrement_pools: dict[int, list[ExcrementPool]]
    ) -> list[ExcrementPool]:
        """Returns a list of excrement pools in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the excrement pools available in those grid cells.

        Args:
            excrement_pools: A dictionary of excrement pools where keys are grid
              cell IDs.

        Returns:
            A list of ExcrementPool objects in this territory.
        """
        excrement_pools_in_territory: list[ExcrementPool] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.grid_cell_keys:
            # Check if the cell_id is within the provided excrement pools
            if cell_id in excrement_pools:
                excrement_pools_in_territory.extend(excrement_pools[cell_id])

        return excrement_pools_in_territory

    def get_carcass_pools(
        self, carcass_pools: dict[int, list[CarcassPool]]
    ) -> list[CarcassPool]:
        """Returns a list of carcass pools in this territory.

        This method checks which grid cells are within this territory
        and returns a list of the carcass pools available in those grid cells.

        Args:
            carcass_pools: A dictionary of carcass pools where keys are grid
              cell IDs.

        Returns:
            A list of CarcassPool objects in this territory.
        """
        carcass_pools_in_territory: list[CarcassPool] = []

        # Iterate over all grid cell keys in this territory
        for cell_id in self.grid_cell_keys:
            # Check if the cell_id is within the provided carcass pools
            if cell_id in carcass_pools:
                carcass_pools_in_territory.extend(carcass_pools[cell_id])

        return carcass_pools_in_territory

    def find_intersecting_carcass_pools(
        self,
        prey_territory: "AnimalTerritory",
        carcass_pools: dict[int, list[CarcassPool]],
    ) -> list[CarcassPool]:
        """Find the carcass pools of the intersection of two territories.

        Args:
            prey_territory: Another AnimalTerritory to find the intersection with.
            carcass_pools: A dictionary mapping cell IDs to CarcassPool objects.

        Returns:
            A list of CarcassPools in the intersecting grid cells.
        """
        intersecting_keys = set(self.grid_cell_keys) & set(
            prey_territory.grid_cell_keys
        )
        intersecting_carcass_pools: list[CarcassPool] = []
        for cell_id in intersecting_keys:
            intersecting_carcass_pools.extend(carcass_pools[cell_id])
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
