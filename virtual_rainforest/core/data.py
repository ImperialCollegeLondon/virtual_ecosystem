"""The core.data module.

This module handles the initial loading and generation of input data used to run a
Virtual Rainforest simulation.

TODO - Currently, the grid object is passed as an argument, but this could be a global
variable?
"""

from typing import Callable, Optional, Sequence, Union

import numpy as np
from shapely.geometry import Point
from xarray import Dataset, load_dataset

from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER

DATA: dict = {}
"""The global data dictionary

This dictionary is intended to be populated using calls to add_data_source or
add_generated_data. Using a global dictionary here to store simulation state does not
feel like the right way to tackle this - proof of concept only for the moment.
"""


DATA_MAPPER_REGISTRY: dict[str, Callable] = {}
"""A registry for different data mapping functions

This dictionary maps grid geometry types (square, hex, etc) to a function that validates
the mapping of NetCDF format data onto the defined grid. Users can register their own
grid types using the `register_data_mapper` decorator.
"""


def register_data_mapper(grid_type: str) -> Callable:
    """Add data mapper function to the data mapper registry.

    This decorator is used to register a function that maps data in a NetCDF file onto
    a defined Grid object. The grid_type argument is used to identify the grid type
    (e.g. square) that the data mapper function applies to.

    Args:
        grid_type: The Grid.grid_type that a mapper function is used for.
    """

    def decorator_register_data_mapper(func: Callable) -> Callable:

        # Add the grid type to the registry
        if grid_type in DATA_MAPPER_REGISTRY:
            LOGGER.warning(
                "Grid type %s already exists and is being replaced", grid_type
            )
        DATA_MAPPER_REGISTRY[grid_type] = func

        return func

    return decorator_register_data_mapper


def add_data_source(file: str, var: str, grid: Grid, references: str = None) -> None:
    """Load data from a NetCDF source file.

    This class loads data from a NetCDF file for a given variable, checks that the
    data are congruent with an existing grid definition and then stores the data in the
    model global data.

    Simulations use standardised names to identify the different variables required by
    modules. If the variable name in the file is the standardised name, then the
    `references` argument can be used to link the variable to that standard name.

    Args:
        file: The path to a NetCDF file containing a variable to be used.
        var: The variable name in the NetCDF file.
        grid: A core grid that the data should match to.
        references: The standard name for the variable.
    """

    # Load the provided file
    dataset = load_dataset(file)

    # Retrieve the creator function from the grid registry and handle unknowns
    mapper = DATA_MAPPER_REGISTRY.get(grid.grid_type, None)
    if mapper is None:
        raise ValueError(
            f"The data mapper function for grid_type {grid.grid_type} is not defined."
        )

    data_names, permute = mapper(grid, dataset)

    # Look for the data variable
    if var not in data_names:
        raise ValueError(f"Variable {var} not found in file {file}")

    # Get the internal name that the variable references
    references = references or var
    if references in DATA:
        raise ValueError(f"Name {references} already defined in simulation data")

    # Store the permuted DataArray in the global DATA object
    # TODO - think about what format to store here. Need to retain axis dimension
    #        information for indexing, time in particular. How about interpolation?

    DATA[references] = dataset[var]


@register_data_mapper("square")
def map_dataset_onto_square_grid(grid: Grid, dataset: Dataset) -> bool:
    """Maps data in an xarray dataset onto a square grid.

    Args:
        grid: A Grid object defining the simulation spatial arrangement.
        dataset: An xarray dataset.

    Returns:
        Not quite sure yet - possible an nd.array indexing the provided data onto the
        standard internal representation.
    """

    # Get the dimensions, coords and variables
    # - dim gives the dimension names and lengths
    dim_names = list(dataset.dims)
    # - dimensions can have associated coordinates, where coord_names _must_ be a
    #   subset of dim_names
    coord_names = list(dataset.coords)
    # - coordinates and 'data' are _both_ variables
    variable_names = list(dataset.variables)
    # - So variables containing data are the difference between the two
    data_names = set(variable_names) - set(coord_names)

    # Use dimension names to identify spatial layout
    # - look for xy in dimensions first (+- coords on those dimensions),
    # - then xy in variables (dataframe style)
    # - then cell_id in dimensions (+- coords on those dimensions).
    expected_n_cells = grid.cell_nx * grid.cell_ny

    if "x" in dim_names and "y" in dim_names:

        # Should be the same shape as the grid
        if grid.cell_nx != dataset.dims["x"] or grid.cell_ny != dataset.dims["y"]:
            raise ValueError("Data xy dimensions do not match grid")

        # If x and y have coordinates, they should match the data grid.
        if "x" in coord_names and "y" in coord_names:

            # Get x and y coords for an L of grid cells along two edges to check the
            # extents and cell coverage.
            x_check = np.concatenate(
                [np.repeat(dataset["x"].values[0], grid.cell_nx), dataset["x"].values]
            )
            y_check = np.concatenate(
                [dataset["y"].values, np.repeat(dataset["y"].values[0], grid.cell_nx)]
            )
            check_coordinates_in_grid(grid, x_check, y_check)

    elif "x" in data_names and "y" in data_names:

        # Check the datasets have the same dimensions (having identical dim name tuples
        # guarantees that data has the same shape and order.)
        if dataset["x"].dims != dataset["y"].dims:
            raise ValueError("The x and y data have different dimensions")

        # Check the expected number of cells are provided
        n_found = dataset["x"].size
        if expected_n_cells != n_found:
            raise ValueError(
                f"Grid defines {expected_n_cells} cells, data provides {n_found}"
            )

        # Now check they are actually in the cells
        check_coordinates_in_grid(grid, dataset["x"].values, dataset["y"].values)

    elif "cell_id" in dim_names:

        # Check the right number of cells are found
        n_found = dataset["cell_id"].size
        if expected_n_cells != n_found:
            raise ValueError(
                f"Grid defines {expected_n_cells} cells, data provides {n_found}"
            )

        if "cell_id" in coord_names and (
            set(grid.cell_dict) != set(dataset["cell_id"].values)
        ):

            raise ValueError("The cell_ids in the data do not match grid cell ids.")

    return True


def check_coordinates_in_grid(
    grid: Grid,
    x_coords: Union[Sequence, np.ndarray],
    y_coords: Union[Sequence, np.ndarray],
) -> None:
    """Check a set of coordinates occur in a Grid.

    This function loops over points defined by pairs of x and y coordinates and checks
    to see that each point intersects only one of the cell polygons defined in the grid.
    Points that intersect no cells falls outside the grid and points that intersect more
    than one cell fall ambiguously on cell borders.

    The function either raises an error or returns None on success.

    Args:
        grid: The simulation grid.
        x_coords: The x coordinates of points that should occur within grid cells.
        y_coords: The same for y coordinates.
    """

    if len(x_coords) != len(y_coords):
        raise ValueError("The x and y coordinates are of unequal length.")

    # Get shapely points for the coordinates
    xyp = [Point(x, y) for x, y in zip(x_coords, y_coords)]

    # Count how many cells each point intersects.
    cell_counts = [sum([c.intersects(p) for c in grid.cell_dict.values()]) for p in xyp]

    # Not all coords in a grid cell
    if 0 in cell_counts:
        raise ValueError("Data coordinates do not align with grid coordinates.")

    # Values greater than 1 indicate coordinates on cell edges
    if any(c > 1 for c in cell_counts):
        raise ValueError(
            "Data coordinates fall on cell edges: use cell centre coordinates in data."
        )

    return


class DataGenerator:
    """Generate artificial data."""

    def __init__(
        self,
        # grid: GRID,
        spatial_axis: str,
        temporal_axis: str,
        temporal_interpolation: np.timedelta64,
        seed: Optional[int],
        method: str,  # one of the numpy.random.Generator methods
        **kwargs,
    ) -> None:

        pass
