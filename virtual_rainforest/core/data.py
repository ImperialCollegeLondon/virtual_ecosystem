"""The core.data module.

This module handles the validation of data sources and the loading of data used to run
Virtual Rainforest simulations.

## Data sources

Data sources are the individual files containing data used in the simulation. These will
contain coordinates that map values for variables onto a Virtual Rainforest Grid
definition. They can contain multiple variables, so the validation of the mapping from
coordinates in the data source to the Grid definition should only be done once. That
validation should also generate the permutation to map the coordinate system in the data
source to a standard internal representation.

## Data

Any variable in a validated DataSource object can then be loaded into the DATA
dictionary in standard form.


[data]
[[data.source]]
file="/path/to/file.nc"
[[data.source.variables]]
var_name="precip"
var_reference="precipitation"
[[data.source.variables]]
var_name="temp"
var_reference="temperature"
[[data.source]]
file="/path/to/file.csv"
[[data.source.variables]]
var_name="elev"
var_reference="elevation"

[data.precipitation]
file="/path/to/file.nc"
var_name="precip"
[data.temperature]
file="/path/to/file.nc"
var_name="temperature"
[data.elevation]
file="/path/to/file.csv"
var_name="elevation"



[[data.variable]]
var="precipitation"
file="/path/to/file.nc"
file_var="precip"
[[data.variable]]
var="temperature"
file="/path/to/file.nc"
file_var="temp"
[[data.variable]]
var="elevation"
file="/path/to/file.csv"
file_var="elev"



[data.preciptation]
file="/path/to/file.nc"
var_name="precip"
[data.temperature]
file="/path/to/file.nc"
var_name="temperature"
[data.elevation]
file="/path/to/file.csv"
var_name="temperature"





TODO - Currently, the grid object is passed as an argument, but this could be a global
variable?
"""

import copy
from itertools import groupby
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

import numpy as np
from shapely.geometry import Point
from xarray import load_dataset

from virtual_rainforest.core.grid import GRID_REGISTRY, Grid
from virtual_rainforest.core.logger import LOGGER

DATA: dict = {}
"""The global data dictionary

This dictionary is intended to be populated using calls to add_data_source or
add_generated_data. Using a global dictionary here to store simulation state does not
feel like the right way to tackle this - proof of concept only for the moment.
"""

DATA_LOADER_REGISTRY: dict[tuple[str, str], Callable] = {}
"""A registry for different data loader functions

This dictionary references the combination of grid geometry types (square, hex, etc) and
a given file format to a function that validates the mapping of data source in the
format onto the defined grid and then loads the data.

Users can register their own functions mapping data from a particular file format onto a
given grid types using the `register_data_mapper` decorator. The function should have
the following arguments: grid, file and vars.
"""


def register_data_loader(grid_type: str, file_type: Union[str, tuple[str]]) -> Callable:
    """Adds a data loader function to the data loader registry.

    This decorator is used to register a function that loads data from a given file type
    onto a defined Grid type.

    Args:
        grid_type: A valid Grid.grid_type that the mapper function applies to.
        file_type: A string or tuple of strings giving the file type that the function
            will map onto the Grid. The strings should match expected file suffixes for
            the file type.
    """

    def decorator_register_data_mapper(func: Callable) -> Callable:

        # Ensure file_type is an iterable
        if isinstance(file_type, str):
            _file_type = tuple(file_type)
        else:
            _file_type = file_type

        # Check the grid type is known and - if not - log a critical issue and return
        # the decorated function without extending the data mapper registry.
        #
        # TODO - How to ensure that grids are registered before this decorator is used.

        if grid_type not in GRID_REGISTRY:
            LOGGER.critical(
                "Unknown grid type %s used with register_data_mapper", grid_type
            )
            return func

        # Register the mapper function for each combination of grid type and file type
        for this_ft in _file_type:

            if (grid_type, this_ft) in DATA_LOADER_REGISTRY:
                LOGGER.warning(
                    "The data mapper for (%s, %s) already exists and is being replaced",
                    grid_type,
                    this_ft,
                )

            DATA_LOADER_REGISTRY[(grid_type, this_ft)] = func

        return func

    return decorator_register_data_mapper


def setup_data(data_config: dict, grid: Grid) -> None:
    """Setup the simulation data from a user configuration.

    This is a high level function used to validate a provided user data configuration
    and populate the core DATA object from the provided data sources. The data_config
    dictionary can contain lists of variables under the following keys:

    * `variable`: These are data elements loaded from a provided file. Each element in
      the list should be a dictionary providing ...
    * `constant`: TODO
    * `generator`: TODO

    Args:
        data_config: A data configuration dictionary
        grid: An Grid instance that the data should map onto.
    """

    # Handle variables
    if "variable" in data_config:

        # Extract the variable entries and restructure to group by data source.
        variables = copy.deepcopy(data_config["variable"])
        variables = [(Path(x.pop("file")), x) for x in variables]
        variables = sorted(variables, key=lambda x: x[0])
        var_groups = groupby(variables, key=lambda x: x[0])

        # Load data from each data source
        for data_src, data_vars in var_groups:

            # Detect file type
            LOGGER.info("Loading data from file: %s", data_src)
            file_type = data_src.suffix

            # Can the data mapper handle this grid and file type combination?
            if (grid.grid_type, file_type) not in DATA_LOADER_REGISTRY:
                LOGGER.error(
                    "No data loader provided for %s files and %s grids",
                    grid.grid_type,
                    file_type,
                )
                continue

            # If so, load the data
            loader = DATA_LOADER_REGISTRY[(grid.grid_type, file_type)]
            loader(grid=grid, file=data_src, vars=data_vars)

    if "constant" in data_config:
        pass

    if "generator" in data_config:
        pass

    return


@register_data_loader(grid_type="square", file_type=".nc")
def load_netcdf_to_square_grid(grid: Grid, file: Path, vars: list) -> None:
    """Loads data from a NetCDF file onto a square grid.

    This function loads data from a NetCDF file, checks that the data are congruent with
    an existing grid definition and then stores requested variables in the model global
    data.


    Args:
        grid: A Grid instance that the data should map on to.
        file: A Path for a NetCDF file containing variables to be used.
        vars: A list of dictionaries specifying which variables to load.
    """

    # Try and load the provided file
    try:
        dataset = load_dataset(file)
    except FileNotFoundError:
        LOGGER.error("The %s data file is not found", file)
        return
    except ValueError:
        LOGGER.error("Could not load %s: possible format issue", file)
        return

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
            LOGGER.error("Data XY dimensions do not match grid in: %s", file)
            return

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
            LOGGER.error("X and Y data have different dimensions in: %s", file)
            return

        # Check the expected number of cells are provided
        n_found = dataset["x"].size
        if expected_n_cells != n_found:
            LOGGER.error(
                "Grid defines %s cells, data provides %s in: %s",
                expected_n_cells,
                n_found,
                file,
            )
            return

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

    # data_names, permute = mapper(grid, dataset)

    # Now loop over the variables from this file
    for this_var in vars:

        file_var = this_var["file_var"]
        model_var = this_var.get("model_var") or file_var

        # Look for the data variable
        if file_var not in data_names:
            LOGGER.error("Variable %s not found in file %s", file_var, file)
            continue

        # Get the internal name that the variable references
        if model_var in DATA:
            LOGGER.error("Variable %s already defined in model %s", model_var)
            continue

        # Store the permuted DataArray in the global DATA object
        # TODO - think about what format to store here. Need to retain axis dimension
        #        information for indexing, time in particular. How about interpolation?

        DATA[model_var] = dataset[file_var]

    return


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

    The function returns

    Args:
        grid: A core Grid instance.
        x_coords: The x coordinates of points that should occur within grid cells.
        y_coords: The same for y coordinates.

    Raises:
        If the x and y coordinates are not compatible with the grid, a ValueError is
        raised.
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
