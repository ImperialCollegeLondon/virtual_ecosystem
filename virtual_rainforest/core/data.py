"""The core.data module.

This module handles the validation of data sources and the loading of data used to run
Virtual Rainforest simulations.

## Data sources

Data sources are the individual files containing data used in the simulation. The
validation process for loading data needs to check that:

* If the source data has spatial information, that this is congruent with the spatial
  grid being used for a simulation.
* If the source data has a temporal axis, that this is congruent with the temporal
  scope of the simulation.

When data is loaded, it is mapped onto a common internal representation. Individual
files such as NetCDF may contain multiple variables with the same dimensions and
mapping, and so it might be more efficient to re-use mappings, but at the moment each
variable is mapped one at a time.

### Data config

The configuration for populating a Data instance is a TOML-formatted document like this:

``` toml
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
```

"""

import copy
from collections import UserDict
from itertools import groupby
from pathlib import Path
from typing import Any, Callable, Optional, Type, Union

import numpy as np
from xarray import DataArray, load_dataset

from virtual_rainforest.core.grid import GRID_REGISTRY, Grid
from virtual_rainforest.core.logger import LOGGER


class Data(UserDict):
    """The Virtual Rainforest data object.

    This class holds data for a Virtual Rainforest simulation. It functions like a
    dictionary but the class extends the dictionary methods to provide common methods
    for data validation etc and to hold key attributes, such as the underlying spatial
    grid and flags to record loading errors.

    By default, failure to add a dataset to a Data instance does not raise an Exception,
    but sets the clean_load flag to False. This allows data loading to try multiple
    files and the `clean_load` attribute can then be checked to see if all went well. If
    `fast_fail` is set to True, the first failure will raise an Exception.

    Args:
        grid: A Grid instance that loaded datasets with spatial structure must match.
        fast_fail: A boolean setting the fast fail behaviour.

    Attrs:
        grid: The grid instance
        clean_load: A boolean indicating whether any data have failed to load cleanly.
    """

    def __init__(self, grid: Grid, fast_fail: bool = False) -> None:

        # Call the UserDict __init__ to set up the dictionary functionality, but the
        # Data class does not pass in data at __init__, so no arguments provided.
        super(Data, self).__init__()

        # Set up the extended instance properties
        self.fast_fail = fast_fail
        self.grid = grid
        self.clean_load = True

    def __repr__(self) -> str:
        """Returns a representation of a Data instance."""

        if self.data:
            return f"Data: {list(self.keys())}"

        return "Data: no variables loaded"

    def loader_fail(self, excep: Type[Exception], msg: str, *args: Any) -> None:
        """Emit and record a data loading fail.

        This helper method emits an error message and then updates the clean_load
        attribute to record the failure. If the instance `fast_fail` is set to True, the
        provided Exception is raised instead.

        Args:
            excep: The exception class triggering the failure
            msg: An error or exception message to emit
        """

        if self.fast_fail:
            # TODO - need to get this to handle the string formatting arguments in the
            #        same way that LOGGER.error does.
            raise excep(msg, *args)

        LOGGER.error(msg, *args)
        self.clean_load = False

        return

    def add_variable_from_file(
        self, file: Path, file_var: str, data_var: Optional[str] = None
    ) -> None:
        """Adds a variable to the data object.

        This method is used to programatically populate a variable in a Data instance
        from a file. The appropriate data loader function is selected using the file
        suffix and the grid type used in the Data instance.

        Args:
            file: A Path for the file containing the variable to load.
            file_var: A string providing the name of the variable in the file.
            data_var: An optional replacement name to use in the Data instance.
        """

        # Detect file type
        file_type = file.suffix

        # Can the data mapper handle this grid and file type combination?
        if (self.grid.grid_type, file_type) not in DATA_LOADER_REGISTRY:
            LOGGER.error(
                "No data loader provided for %s files and %s grids",
                file_type,
                self.grid.grid_type,
            )

        # If so, load the data
        loader = DATA_LOADER_REGISTRY[(self.grid.grid_type, file_type)]

        # Get the data variable name
        data_var = data_var or file_var

        # Call the loader.
        LOGGER.info("Loading %s data from file: %s", file_var, file)
        loader(data=self, file=file, file_var=file_var, data_var=data_var)


DATA_LOADER_REGISTRY: dict[tuple[str, str], Callable] = {}
"""A registry for different data loader functions

This dictionary references the combination of grid geometry types (square, hex, etc) and
a given file format to a function that validates the mapping of data source in the
format onto the defined grid and then loads the data.

Users can register their own functions mapping data from a particular file format onto a
given grid types using the `register_data_mapper` decorator. The function itself should
have the following signature:

    loader_function(data: Data, file: Path, file_var: str, data_var: Optional[str])
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

        # Check the grid type is known and - if not - log a critical issue and return
        # the decorated function without extending the data mapper registry.
        #
        # TODO - How to ensure that grids are registered before this decorator is used.

        if grid_type not in GRID_REGISTRY:
            LOGGER.critical(
                "Unknown grid type %s used with register_data_mapper", grid_type
            )
            return func

        # Ensure file_type is an iterable
        if isinstance(file_type, str):
            _file_type = (file_type,)
        else:
            _file_type = file_type

        # Register the mapper function for each combination of grid type and file type
        for this_ft in _file_type:

            if (grid_type, this_ft) in DATA_LOADER_REGISTRY:
                LOGGER.warning(
                    "Replacing existing data mapper function for (%s, %s)",
                    grid_type,
                    this_ft,
                )
            else:
                LOGGER.info(
                    "Adding data mapper function for (%s, %s)",
                    grid_type,
                    this_ft,
                )

            DATA_LOADER_REGISTRY[(grid_type, this_ft)] = func

        return func

    return decorator_register_data_mapper


@register_data_loader(grid_type="square", file_type=".nc")
def load_netcdf_to_square_grid(
    data: Data, file: Path, file_var: str, data_var: Optional[str] = None
) -> None:
    """Loads data from a NetCDF file onto a square grid.

    This function loads data from a NetCDF file, checks that the data are congruent with
    an existing grid definition, restructures to the standard internal format and then
    stores the loaded data the provided data instance.

    Args:
        data: A Data instance to add the data into.
        file: A Path for a NetCDF file containing the variable to load.
        file_var: A string providing the name of the variable in the file.
        data_var: An optional replacement name to use in the Data instance.
    """

    # Set the internal name for this variable
    data_var = data_var or file_var

    # Check we're not overloading existing data.
    if data_var in data:
        data.loader_fail(
            AttributeError, "The variable %s has already been loaded", data_var
        )
        return

    # Try and load the provided file
    try:
        dataset = load_dataset(file)
    except FileNotFoundError:
        data.loader_fail(FileNotFoundError, "The %s data file is not found", file)
        return
    except ValueError:
        data.loader_fail(ValueError, "Could not load %s: possible format issue", file)
        return

    # Xarray datasets have dimensions, coords and variables
    # - dim gives the dimension names and lengths
    # - dimensions can have associated coordinates, where coord_names _must_ be a
    #   subset of dim_names
    # - coordinates and 'data' are _both_ variables
    # - So variables containing data are the difference between the two

    # First check if file var is a variable at all
    if file_var not in dataset:
        data.loader_fail(AttributeError, "Variable %s not found in %s", file_var, file)
        return

    # Now drop down to the data array for the variable
    darray = dataset[file_var]
    LOGGER.info("Loading %s from %s", file_var, file)

    # Use dimension names to identify spatial layout
    # - look for xy in dimensions first (+- coords on those dimensions),
    # - then xy in variables (dataframe style)
    # - then cell_id in dimensions (+- coords on those dimensions).

    if "x" in darray.dims and "y" in darray.dims:

        if "x" in darray.coords and "y" in darray.coords:
            # If x and y have coordinates, use them to match onto the grid.
            try:
                retdata = _square_xy_coord_array(data.grid, darray, file)
            except RuntimeError as err:
                data.loader_fail(excep=type(err), msg=str(err))
                return

        else:
            # Otherwise the data array must be the same shape as the grid
            try:
                retdata = _square_xy_dim_array(data.grid, darray, file)
            except RuntimeError as err:
                data.loader_fail(excep=type(err), msg=str(err))
                return

    # elif "x" in data_names and "y" in data_names:

    #     # Check the datasets have the same dimensions (having identical dim name
    #     # tuples
    #     # guarantees that data has the same shape and order.)
    #     if dataset["x"].dims != dataset["y"].dims:
    #         LOGGER.error("X and Y data have different dimensions in: %s", file)
    #         return

    #     # Check the expected number of cells are provided
    #     n_found = dataset["x"].size
    #     if data.grid.n_cells != n_found:
    #         LOGGER.error(
    #             "Grid defines %s cells, data provides %s in: %s",
    #             data.grid.n_cells,
    #             n_found,
    #             file,
    #         )
    #         return

    #     # Now check they are actually in the cells
    #     cell_id_map = data.grid.map_coordinates(
    #         dataset["x"].values, dataset["y"].values
    #     )

    # elif "cell_id" in dim_names:

    #     # Check the right number of cells are found
    #     n_found = dataset["cell_id"].size
    #     if data.grid.n_cells != n_found:
    #         raise ValueError(
    #             f"Grid defines {data.grid.n_cells} cells, data provides {n_found}"
    #         )

    #     if "cell_id" in coord_names and (
    #         set(data.grid.cell_id) != set(dataset["cell_id"].values)
    #     ):

    #         raise ValueError("The cell_ids in the data do not match grid cell ids.")
    # else:
    #     raise ValueError("Unknown mapping to grid - but what about other axes!?")

    # Store the data.
    data[data_var] = retdata

    return


def _square_xy_coord_array(
    grid: Grid, darray: DataArray, file: Optional[Path] = None
) -> DataArray:
    """Maps a DataArray with XY coordinates onto a grid."""

    # Get x and y coords to check the extents and cell coverage.
    #
    # Note that mapping all the cells here is a bit extreme with a square grid -
    # checking the x and y values alone would confirm - but that is only true for square
    # grids and for other grids the all polygons approach is robust. Maybe implement a
    # special case method if needed?

    # TODO - this feels all around the houses. Must be a cleaner implementation.

    grid_x, grid_y = np.meshgrid(darray["x"].values, darray["y"].values)
    grid_x = grid_x.flatten()
    grid_y = grid_y.flatten()

    # Get the grid to cell id map - which can raise errors.
    cell_id_map = grid.map_coverage(grid_x, grid_y, strict=False)

    # Now remap the grids from xy to cell_id - this uses the rather under
    # described vectorized indexing feature in xarray:
    #   https://docs.xarray.dev/en/stable/user-guide/indexing.html

    idx_x, idx_y = np.indices([darray.sizes["x"], darray.sizes["y"]])
    idx_x = idx_x.flatten()
    idx_y = idx_y.flatten()

    # Reduce to matching cells in cell_id order
    cells = [
        (mp, x, y) for (mp, x, y) in zip(cell_id_map, idx_x, idx_y) if mp is not None
    ]
    cells.sort()
    _, idx_x, idx_y = zip(*cells)

    # Get DataArrays containing integer indices for values on x and y dimensions
    # but mapping to a single common cell_id dimension.
    ind_x = DataArray(list(idx_x), dims=["cell_id"])
    ind_y = DataArray(list(idx_y), dims=["cell_id"])

    # Now use DataArray.isel to select indexing dimensions by name - avoiding
    # issues with different permutations of the axes
    darray = darray.isel(x=ind_x, y=ind_y)

    return darray


def _square_xy_dim_array(
    grid: Grid, darray: DataArray, file: Optional[Path] = None
) -> DataArray:
    """Maps a DataArray with XY dimensions onto a grid."""

    # Otherwise the data array must be the same shape as the grid
    if grid.cell_nx != darray.sizes["x"] or grid.cell_ny != darray.sizes["y"]:

        raise RuntimeError("Data XY dimensions do not match grid in: %s", file)

    return darray


def load_data_config(
    data: Data,
    data_config: dict,
) -> None:
    """Setup the simulation data from a user configuration.

    This is a high level function used to validate a provided user data configuration
    and populate a Data instance object from the provided data sources. The data_config
    dictionary can contain lists of variables under the following keys:

    * `variable`: These are data elements loaded from a provided file. Each element in
      the list should be a dictionary providing ...
    * `constant`: TODO
    * `generator`: TODO

    Args:
        data_config: A data configuration dictionary
        data: An Data instance that will hold the resulting data.
    """

    # TODO - this could be a method of Data. Is there any practical reason to prefer one
    #        of these:
    #
    #        data.load_data_config(config)
    #        load_data_config(data, config)

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
            file_type = data_src.suffix

            # Can the data mapper handle this grid and file type combination?
            if (data.grid.grid_type, file_type) not in DATA_LOADER_REGISTRY:
                LOGGER.error(
                    "No data loader provided for %s files and %s grids",
                    file_type,
                    data.grid.grid_type,
                )
                continue

            # If so, load the data
            loader = DATA_LOADER_REGISTRY[(data.grid.grid_type, file_type)]

            for var in data_vars:
                # Get the file and data variable name
                file_var = var["file_var"]
                data_var = var["data_var"] or file_var

                # Call the loader.
                LOGGER.info("Loading %s data from file: %s", file_var, data_src)
                loader(data=data, file=data_src, file_var=file_var, data_var=data_var)

    if "constant" in data_config:
        pass

    if "generator" in data_config:
        pass

    return


class DataGenerator:
    """Generate artificial data.

    Currently just a signature sketch.
    """

    def __init__(
        self,
        # grid: GRID,
        spatial_axis: str,
        temporal_axis: str,
        temporal_interpolation: np.timedelta64,
        seed: Optional[int],
        method: str,  # one of the numpy.random.Generator methods
        **kwargs: Any,
    ) -> None:

        pass
