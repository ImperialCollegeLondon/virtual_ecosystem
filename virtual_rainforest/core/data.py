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

## Data config

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

from collections import UserDict
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Type, Union

import numpy as np
from xarray import DataArray, load_dataset

from virtual_rainforest.core.grid import GRID_REGISTRY, Grid
from virtual_rainforest.core.logger import LOGGER, log_and_raise

FILE_FORMAT_REGISTRY: dict[Union[str, tuple[str]], Callable] = {}
"""A registry for different file format loaders

This dictionary maps a tuple of file format suffixes onto a function that allows the
data to be loaded. That loader function should coerce the data into an xarray DataArray
and then this is validated using the DataArrayLoader class.

Users can register their own functions to load from a particular file format using the
`file_format_mapper` decorator. The function itself should
have the following signature:

    func(file: Path, file_var: str, data_var: Optional[str])
"""


def register_file_format_loader(file_types: tuple[str]) -> Callable:
    """Adds a data loader function to the data loader registry.

    This decorator is used to register a function that loads data from a given file type
    and coerces it to a DataArray.

    TODO - How to ensure that grids are registered before this decorator is used.

    Args:
        file_types: A tuple of strings giving the file type that the function will map
            onto the Grid. The strings should match expected file suffixes for the file
            type.
    """

    def decorator_file_format_loader(func: Callable) -> Callable:

        # Ensure file_type is an iterable
        if isinstance(file_types, str):
            _file_types = (file_types,)
        else:
            _file_types = file_types

        # Register the mapper function for each combination of grid type and file type
        for this_ft in _file_types:

            if this_ft in FILE_FORMAT_REGISTRY:
                LOGGER.debug(
                    "Replacing existing data loader function for %s",
                    this_ft,
                )
            else:
                LOGGER.debug(
                    "Adding data loader function for %s",
                    this_ft,
                )

            FILE_FORMAT_REGISTRY[this_ft] = func

        return func

    return decorator_file_format_loader


@register_file_format_loader(file_types=(".nc",))
def load_netcdf(file: Path, file_var: str) -> DataArray:
    """Loads a DataArray from a NetCDF file.

    Args:
        file: A Path for a NetCDF file containing the variable to load.
        file_var: A string providing the name of the variable in the file.
    """

    # Try and load the provided file
    try:
        dataset = load_dataset(file)
    except FileNotFoundError:
        log_and_raise(f"Data file not found: {file}", FileNotFoundError)
    except ValueError as err:
        log_and_raise(f"Could not load data from {file}: {err}.", ValueError)

    LOGGER.info("Loading data from %s", file)

    # Check if file var is in the dataset
    if file_var not in dataset:
        log_and_raise(f"Variable '{file_var}' not found in {file}", KeyError)

    LOGGER.info("Loaded variable '%s' from %s", file_var, file)
    return dataset[file_var]


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

    spatial_loaders: dict = {}

    def __init__(self, grid: Grid, fast_fail: bool = False) -> None:

        # Call the UserDict __init__ to set up the dictionary functionality, but the
        # Data class does not pass in data at __init__, so no arguments provided.
        super(Data, self).__init__()

        # Set up the extended instance properties
        self.fast_fail = fast_fail
        self.grid = grid
        self.loading_errors = False

    def __repr__(self) -> str:
        """Returns a representation of a Data instance."""

        if self.data:
            return f"Data: {list(self.keys())}"

        return "Data: no variables loaded"

    def loader_fail(self, excep: Type[Exception], msg: str, *args: Any) -> None:
        """Emit and record a data loading fail.

        This helper method emits an error message and then updates the `loading_errors`
        attribute to record the failure. If the instance was created with `fast_fail`
        set to True, the provided Exception is raised instead.

        Args:
            excep: The exception class triggering the failure
            msg: An error or exception message to emit
        """

        if self.fast_fail:
            raise excep(msg % args)

        LOGGER.error(msg, *args)
        self.loading_errors = True

        return

    def load_dataarray(self, darray: DataArray) -> None:
        """Load a data array."""

        # Identify the correct loader routine from the data array signature
        da_dims = set(darray.dims)
        da_coords = set(darray.coords.dims)

        spatial_loader_func = None

        for (ld_dims, ld_coords, ld_grid_type), ld_func in self.spatial_loaders.items():

            if (
                da_dims.issubset([ld_dims])
                and da_coords.issubset([ld_coords])
                and ld_grid_type in [self.grid.grid_type, "__any__"]
            ):

                spatial_loader_func = ld_func
                break

        if not spatial_loader_func:
            raise AttributeError("Unknown loader signature")

        if darray.name in self:
            raise KeyError(f"Variable {darray.name} already loaded in data instance")

        # Load the data
        self[darray.name] = ld_func(darray)

    # def add_variable_from_file(
    #     self, file: Path, file_var: str, data_var: Optional[str] = None
    # ) -> None:
    #     """Adds a variable to the data object.

    #     This method is used to programatically populate a variable in a Data instance
    #     from a file. The appropriate data loader function is selected using the file
    #     suffix and the grid type used in the Data instance.

    #     Args:
    #         file: A Path for the file containing the variable to load.
    #         file_var: A string providing the name of the variable in the file.
    #         data_var: An optional replacement name to use in the Data instance.
    #     """

    #     # Detect file type
    #     file_type = file.suffix

    #     # Can the data mapper handle this grid and file type combination?
    #     if (self.grid.grid_type, file_type) not in DATA_LOADER_REGISTRY:
    #         LOGGER.error(
    #             "No data loader provided for %s files and %s grids",
    #             file_type,
    #             self.grid.grid_type,
    #         )

    #     # If so, load the data
    #     loader = DATA_LOADER_REGISTRY[(self.grid.grid_type, file_type)]

    #     # Get the data variable name
    #     data_var = data_var or file_var

    #     # Call the loader.
    #     LOGGER.info("Loading %s data from file: %s", file_var, file)

    #     loader(data=self, file=file, file_var=file_var, data_var=data_var)

    # def load_data_config(self, data_config: dict) -> None:
    #     """Setup the simulation data from a user configuration.

    #     This is a method is used to validate a provided user data configuration and
    #     populate the Data instance object from the provided data sources. The
    #     data_config dictionary can contain lists of variables under the following
    #     keys:

    #     * `variable`: These are data elements loaded from a provided file. Each
    #       element in the list should be a dictionary providing ...
    #     * `constant`: TODO
    #     * `generator`: TODO

    #     Args:
    #         data_config: A data configuration dictionary
    #     """

    #     LOGGER.info("Loading data configuration")

    #     # Handle variables
    #     if "variable" in data_config:

    #         # Extract the variable entries and restructure to group by data source.
    #         variables = copy.deepcopy(data_config["variable"])
    #         variables = [(Path(x.pop("file")), x) for x in variables]
    #         variables = sorted(variables, key=lambda x: x[0])
    #         var_groups = groupby(variables, key=lambda x: x[0])

    #         # Load data from each data source
    #         for data_src, data_vars in var_groups:

    #             # Detect file type
    #             file_type = data_src.suffix

    #             # Can the data mapper handle this grid and file type combination?
    #             if (self.grid.grid_type, file_type) not in DATA_LOADER_REGISTRY:
    #                 LOGGER.error(
    #                     "No data loader provided for %s files and %s grids",
    #                     file_type,
    #                     self.grid.grid_type,
    #                 )
    #                 continue

    #             # If so, load the data
    #             loader = DATA_LOADER_REGISTRY[(self.grid.grid_type, file_type)]

    #             for var in data_vars:
    #                 # Get the file and data variable name
    #                 file_var = var["file_var"]
    #                 data_var = var["data_var"] or file_var

    #                 # Call the loader.
    #                 LOGGER.info("Loading %s data from file: %s", file_var, data_src)
    #                 loader(
    #                     data=self, file=data_src, file_var=file_var, data_var=data_var
    #                 )

    #     if "constant" in data_config:
    #         pass

    #     if "generator" in data_config:
    #         pass

    #     return


def add_spatial_loader(signature: tuple) -> Callable:
    """Extend the spatial loader functionality of Data.

    This decorator adds the decorated method to the Data class to extend or
    amend the available routines used to load and validate an array containing spatial
    information. The decorator adds the method and also extends the `spatial_loaders`
    class attribute: this dictionary provides a map to link the attributes of an input
    dataarray instance to a particular loader function.

    The signature consists of a tuple containing:

    * a tuple of dimension names required in the data array to use the function,
    * a tuple of coordinate names required in the data array to use the function - this
      can be an empty tuple if no coordinate names are required,
    * a tuple of grid types that the loader can be used with. The "__any__" grid type
      can be used to indicate that a loader will work with any grid type.

    Args:
        cls:
        signature: A tuple of the loader signature.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Mapping) -> Callable:
            return func(*args, **kwargs)

        # Check the grid types are valid
        grid_types = signature[2]
        for gtype in grid_types:
            if (gtype not in GRID_REGISTRY) and (gtype != "__any__"):
                log_and_raise(
                    f"Unknown grid type '{gtype}' decorating {func.__name__}",
                    AttributeError,
                )

        # Add the function to the class and then register the signature -> function map
        LOGGER.debug("Adding spatial loader: %s", func.__name__)
        setattr(Data, func.__name__, wrapper)
        Data.spatial_loaders[signature] = func.__name__

        return func

    return decorator


@add_spatial_loader((("cell_id",), ("cell_id",), ("__any__",)))
def any_cellid_coord_array(self: Data, darray: DataArray) -> DataArray:
    """Load a DataArray with cell id coordinates.

    In this loader, the DataArray has a cell_id dimension with valued coordinates, which
    should map onto the grid cell ids, allowing for a subset of ids. Because this method
    simply maps data to grid cells by id, it should applies to _any_ arbitrary grid
    setup.
    """

    if set(self.grid.cell_id).issubset(darray["cell_id"].values):
        raise ValueError("The data cell ids are not a superset of grid cell ids.")

    # TODO - Reorder and subset
    return darray


@add_spatial_loader((("cell_id",), (), ("__any__",)))
def any_cellid_dim_array(self: Data, darray: DataArray) -> DataArray:
    """Load a DataArray with cell id dimension.

    In this loader, the DataArray only has a cell_id dimension so assumes that the
    values are provided in the same sequence as the grid cell ids. Because this method
    simply maps data to grid cells by id, it should applies to _any_ arbitrary grid
    setup.
    """

    # Cell ID is only a dimenson with a give length - assume the order correct
    # and check the right number of cells found
    n_found = darray["cell_id"].size
    if self.grid.n_cells != n_found:
        raise ValueError(
            f"Grid defines {self.grid.n_cells} cells, data provides {n_found}"
        )

    return darray


@add_spatial_loader((("x", "y"), ("x", "y"), ("square",)))
def square_xy_coord_array(self: Data, darray: DataArray) -> DataArray:
    """Maps a DataArray with XY coordinates onto a grid."""

    # Get x and y coords to check the extents and cell coverage.
    #
    # Note that mapping all the cells here is a bit extreme with a square grid -
    # checking the x and y values alone would confirm - but that is only true for square
    # grids and for other grids the all polygons approach is robust. Maybe implement a
    # special case method if needed?

    grid_x, grid_y = np.meshgrid(darray["x"].values, darray["y"].values)
    grid_x = grid_x.flatten()
    grid_y = grid_y.flatten()

    idx_x, idx_y = np.indices([darray.sizes["x"], darray.sizes["y"]])
    idx_x = idx_x.flatten()
    idx_y = idx_y.flatten()

    # Get the mapping of points onto the grid
    idx_x, idx_y = self.grid.map_xy_to_cell_indexing(
        x_coords=grid_x, y_coords=grid_y, x_idx=idx_x, y_idx=idx_y, strict=False
    )

    # Now remap the grids from xy to cell_id - this uses the rather under
    # described vectorized indexing feature in xarray:
    #
    #   https://docs.xarray.dev/en/stable/user-guide/indexing.html
    #
    # Specifically using DataArray.isel to select indexed dimensions by name, which
    # avoids issues with different permutations of the axes - and map XY onto a common
    # cell_id

    darray = darray.isel(
        x=DataArray(idx_x, dims=["cell_id"]), y=DataArray(idx_y, dims=["cell_id"])
    )

    return darray


def _square_xy_dim_array(
    grid: Grid, darray: DataArray, file: Optional[Path] = None
) -> DataArray:
    """Maps a DataArray with XY dimensions onto a grid."""

    # Otherwise the data array must be the same shape as the grid
    if grid.cell_nx != darray.sizes["x"] or grid.cell_ny != darray.sizes["y"]:

        raise RuntimeError("Data XY dimensions do not match grid in: %s", file)

    # Get DataArrays containing integer indices for values on x and y dimensions
    # but mapping to a single common cell_id dimension.
    idx_x, idx_y = np.indices([darray.sizes["x"], darray.sizes["y"]])

    # Now use DataArray.isel to select indexing dimensions by name - avoiding
    # issues with different permutations of the axes - and map XY onto cell_id
    darray = darray.isel(
        x=DataArray(idx_x.flatten(), dims=["cell_id"]),
        y=DataArray(idx_y.flatten(), dims=["cell_id"]),
    )

    return darray


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
