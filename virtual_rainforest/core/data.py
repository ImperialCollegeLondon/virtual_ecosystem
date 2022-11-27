"""API documentation for the :mod:`core.data` module.
************************************************** # noqa: D205

This module handles the population and storage of data sources used to run Virtual
Rainforest simulations.

The Data class
==============

The core :class:`~virtual_rainforest.core.data.Data` class is a dictionary-like object
that can be used to access data simply as ``data['var_name']``. All of the entries in
the dictionary are :class:`~xarray.DataArray` objects, which provides a flexible
indexing system onto underlying :mod:`numpy` arrays. A
:class:`~virtual_rainforest.core.data.Data` instance is initalised using the core
configuration parameters for a simulation, currently a
:class:`~virtual_rainforest.core.grid.Grid`.

Adding data to a Data instance
------------------------------

The :class:`~virtual_rainforest.core.data.Data` class extends a simple dictionary to
provide validation methods for adding data to the dictionary. Only
:class:`~xarray.DataArray` objects can be added to an instance, using the
:meth:`~virtual_rainforest.core.data.Data.load_dataarray` method. When this is used, the
provided :class:`~xarray.DataArray` is checked via a configurable system of 'loader'
methods. These loaders are used to check that particular signatures of dimensions and
coordinates in input :class:`~xarray.DataArray` are congruent with the core
configuration parameters. A loader method should take an input that matches the
signature, validate it, implement any internal standardisation and then return the
valid, standardised data. At present, only the spatial loaders are implemented, but
temporal and other loaders such as soil depth may be added.

The standard dictionary ``__setitem__`` method is deliberately disabled to emphasize
that only data arrays may be added to :class:`~virtual_rainforest.core.data.Data`
instances.

..code-block:: python

    grid = Grid()
    data = Data(grid)
    # Not this
    data['varname'] = DataArray([1,2,3])
    # But this
    data.load_dataarray(DataArray([1,2,3], name='varname'))

The ``spatial_loaders`` system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :attr:`~virtual_rainforest.core.data.Data.spatial_loaders` attribute contains a
dictionary that maps :class:`~xarray.DataArray` signatures onto appropriate loader
methods. The set of loaders can be extended using the
:func:`~virtual_rainforest.core.data.add_spatial_loader` decorator, which adds a
new pairing of a signature and method to the :class:`~virtual_rainforest.core.data.Data`
class.

The signature for ``spatial_loaders`` is used to match tuples of the data array
dimensions, coordinates and the spatial grid type against the input data. So, for
example:

.. code-block:: python

    @add_spatial_loader((("x", "y"), ("x", "y"), ("square",)))

This adds a spatial loader that will map a :class:`~xarray.DataArray` with ``x`` and
``y`` coordinates (and hence implicitly 'x' and 'y' dimensions) onto a square grid.

.. code-block:: python

    @add_spatial_loader((("cell_id",), (), ("__any__",)))

This adds a spatial loader that will map a :class:`~xarray.DataArray` with the
``cell_id`` dimension (but no ``cell_id`` coordinats) onto _any_ spatial grid type: the
underlying ``cell_id``  attribute of the grid is defined for all grid.

All spatial loader methods standardise the spatial structure of the input data to use a
single ``cell_id`` spatial axis, which maps data onto the cell IDs used for indexing in
the :class:`~virtual_rainforest.core.grid.Grid` instance for the simulation.

Adding data from a file
-----------------------

The general solution for programmatically adding data from a file is to:

* manually open a data file using the appropriate reader packages for the format,
* coerce the data into a properly structured :class:`~xarray.DataArray` object, and then
* use the :class:`~virtual_rainforest.core.data.Data.load_dataarray` method.

However, the :meth:`~virtual_rainforest.core.data.Data.load_from_file` method
automatically loads data from known formats defined in the
:attr:`~virtual_rainforest.core.data.FILE_FORMAT_REGISTRY`.

The FILE_FORMAT_REGISTRY
~~~~~~~~~~~~~~~~~~~~~~~~

The :attr:`~virtual_rainforest.core.data.FILE_FORMAT_REGISTRY` is used to register the
set of known file formats for use in
:meth:`~virtual_rainforest.core.data.Data.load_from_file`. This registry is extendable,
so that new functions that implement the approach above for a given file format can be
added to those supported by :meth:`~virtual_rainforest.core.data.Data.load_from_file`.
This is done using the :func:`~virtual_rainforest.core.data.register_file_format_loader`
decorator, which needs to specify the file formats supported (as a tuple of file
suffixes) and then decorate a function that returns a :class:`~xarray.DataArray`
suitable for use in :meth:`~virtual_rainforest.core.data.Data.load_dataarray`. For
example:

.. code-block:: python

    @register_file_format_loader(('.tif', '.tiff'))
    def new_function_to_load_tif_data(...):

Using a data configuration
--------------------------

A :class:`~virtual_rainforest.core.data.Data` instance can also be populated using the
:meth:`~virtual_rainforest.core.data.Data.load_from_config` method. This is expecting to
take a properly validated configuration dictionary, loaded from a TOML file that
specifies data source files:

.. code-block:: toml

    [[core.data.variable]]
    name="precipitation"
    file="/path/to/file.nc"
    file_var="precip"
    [[core.data.variable]]
    name="temperature"
    file="/path/to/file.nc"
    file_var="temp"
    [[core.data.variable]]
    name="elevation"
    file="/path/to/file.csv"
    file_var="elev"

Note that the properties for each variable in the configuration file are just the
arguments for :meth:`~virtual_rainforest.core.data.Data.load_from_file`. The `replace`
argument is not supported: data configurations should not contain multiple definitions
of the same variable and so will fail with repeated variable names.
"""

from collections import UserDict
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Union

import numpy as np
from xarray import DataArray, Dataset, load_dataset

from virtual_rainforest.core.config import ConfigurationError
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

    # Note that this deliberately doesn't contain any INFO logging messages to maintain
    # a simple logging sequence - load_from_file, load_dataarray - without unnecessary
    # logger noise about the specific format unless there is an exception.

    # Try and load the provided file
    try:
        dataset = load_dataset(file)
    except FileNotFoundError:
        log_and_raise(f"Data file not found: {file}", FileNotFoundError)
    except ValueError as err:
        log_and_raise(f"Could not load data from {file}: {err}.", ValueError)

    # Check if file var is in the dataset
    if file_var not in dataset:
        log_and_raise(f"Variable {file_var} not found in {file}", KeyError)

    return dataset[file_var]


class Data(UserDict):
    """The Virtual Rainforest data object.

    This class holds data for a Virtual Rainforest simulation. It functions like a
    dictionary but the class extends the dictionary methods to provide common methods
    for data validation etc and to hold key attributes, such as the underlying spatial
    grid.

    Args:
        grid: A Grid instance that loaded datasets with spatial structure must match.

    Attrs:
        grid: The grid instance
    """

    spatial_loaders: dict = {}

    def __init__(self, grid: Grid, fast_fail: bool = False) -> None:

        # Call the UserDict __init__ to set up the dictionary functionality, but the
        # Data class does not pass in data at __init__, so no arguments provided.
        super(Data, self).__init__()

        # Set up the extended instance properties
        if not isinstance(grid, Grid):
            log_and_raise("Data must be initialised with a Grid object", TypeError)
        self.grid = grid

    def __repr__(self) -> str:
        """Returns a representation of a Data instance."""

        if self.data:
            return f"Data: {list(self.keys())}"

        return "Data: no variables loaded"

    def __setitem__(self, key: str, value: Any) -> None:
        """The disabled Data.__setitem__ interface."""

        raise RuntimeError("Use 'load_dataarray' to add data to Data instances.")

    def load_dataarray(self, darray: DataArray, replace: bool = False) -> None:
        """Load a data array into a Data instance.

        This method takes an input DataArray object and then matches the dimension and
        coordinates signature of the array to find a loading routines given the grid
        used in the Data instance. That routine is used to validate the DataArray and
        then add the DataArray to the Data dictionary.

        Note that the DataArray name is expected to match the standard internal variable
        names used in Virtual Rainforest. By default, loading a data array will not
        replace an existing data array stored under the same key.

        Args:
            darray: A DataArray to add to the Data dictionary.
            replace: If the variable already exists, should it be replaced.
        """

        if isinstance(darray, Dataset):
            log_and_raise("Cannot add Dataset - extract required DataArray", TypeError)
        elif not isinstance(darray, DataArray):
            log_and_raise(
                "Only DataArray objects can be added to Data instances", TypeError
            )

        # Resolve name status
        if darray.name is None:
            log_and_raise("Cannot add data array with unnamed variable", TypeError)

        if darray.name not in self:
            LOGGER.info(f"Adding data array for '{darray.name}'")
        else:
            if replace:
                LOGGER.info(f"Replacing data array for '{darray.name}'")
            else:
                log_and_raise(
                    f"Data array for '{darray.name}' already loaded. Use replace=True",
                    KeyError,
                )

        # Identify the correct spatial loader routine from the data array signature
        da_dims = set(darray.dims)
        da_coords = set(darray.coords.variables)

        # Empty function name, to be overwritten if a matching signature is found.
        # String to avoid mypy issues with getattr(Data, matching_loader_fname)
        matching_loader_fname = ""

        # Loop over the available spatial loaders loooking for a congruent signature
        # - dims _cannot_ be empty on a DataArray (they default to dim_N strings) so are
        #   guaranteed to be non-empty and must then match.
        # - coords _can_ be empty: they just associate values with indices along the
        #   dimension. So, the signature should match _specified_ coords but not the
        #   empty set.
        for (ld_dims, ld_coords, ld_grid_type), ld_fnm in self.spatial_loaders.items():

            if (
                set(ld_dims).issubset(da_dims)
                and set(ld_coords).issubset(da_coords)
                and (
                    (self.grid.grid_type in ld_grid_type) or ("__any__" in ld_grid_type)
                )
            ):

                # Retrieve the method associated with the loader signature from the Data
                # object.
                matching_loader_fname = ld_fnm
                break

        if not matching_loader_fname:
            log_and_raise(
                "DataArray does not match a known spatial loader signature", KeyError
            )

        # Try and get the loader function
        try:
            spatial_loader_func = getattr(self, matching_loader_fname)
        except AttributeError:
            log_and_raise(
                f"Data array maps to unknown spatial loader '{matching_loader_fname}'",
                AttributeError,
            )

        # Load the data - using a generic Exception here simply to capture, log and then
        # reraise upstream exceptions.
        try:
            loaded = spatial_loader_func(darray)
        except Exception as excep:
            log_and_raise(str(excep), type(excep))

        # Store the data in the UserDict using super to bypass the disabled subclass
        # __setitem__ interface
        super(Data, self).__setitem__(darray.name, loaded)

    def load_from_file(
        self,
        file: Path,
        file_var: str,
        name: Optional[str] = None,
        replace: bool = False,
    ) -> None:
        """Adds a variable to the data object.

        This method is used to programatically populate a variable in a Data instance
        from a file. The appropriate data loader function is selected using the file
        suffix and the grid type used in the Data instance.

        Args:
            file: A Path for the file containing the variable to load.
            file_var: A string providing the name of the variable in the file.
            name: An optional replacement name to use in the Data instance.
            replace: If the variable already exists, should it be replaced.
        """

        # Detect file type
        file_type = file.suffix

        # Can the data mapper handle this grid and file type combination?
        if file_type not in FILE_FORMAT_REGISTRY:
            log_and_raise(f"No file format loader provided for {file_type}", ValueError)

        # If so, load the data
        LOGGER.info("Loading variable '%s' from file: %s", file_var, file)
        loader = FILE_FORMAT_REGISTRY[file_type]
        input_data = loader(file, file_var)

        # Replace the file variable name if requested
        if name is not None:
            LOGGER.info("Renaming file variable '%s' as '%s'", input_data.name, name)
            input_data.name = name

        # Add the data array
        self.load_dataarray(input_data, replace=replace)

    def load_data_config(self, data_config: dict) -> None:
        """Setup the simulation data from a user configuration.

        This is a method is used to validate a provided user data configuration and
        populate the Data instance object from the provided data sources. The
        data_config dictionary can contain lists of variables under the following
        keys:

        * `variable`: These are data elements loaded from a provided file. Each
          element in the list should be a dictionary providing the path to the file
          ('file'), the name of the variable within the file ('file_var') and optionally
          a different variable name to be used internally ('name').
        * `constant`: TODO
        * `generator`: TODO

        Args:
            data_config: A data configuration dictionary
        """

        LOGGER.info("Loading data from configuration")

        # Track errors in loading multiple files from a configuration
        clean_load = True

        # Handle variables
        if "variable" in data_config:

            # Load data from each data source
            for each_var in data_config["variable"]:

                # Get the name used in the file or None
                name = each_var.get("name", None)

                # Attempt to load the file, trapping exceptions as critical logger
                # messages and defer failure until the whole configuration has been
                # processed
                try:
                    self.load_from_file(
                        file=each_var["file"], file_var=each_var["file_var"], name=name
                    )
                except Exception as err:
                    LOGGER.critical(str(err))
                    clean_load = False

        if "constant" in data_config:
            raise NotImplementedError("Data config for constants not yet implemented.")

        if "generator" in data_config:
            raise NotImplementedError("Data config for generators not yet implemented.")

        if not clean_load:
            raise ConfigurationError(
                "Data configuration did not load cleanly - check log"
            )


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
                    ValueError,
                )

        # Add the function to the class and then register the signature -> function map
        LOGGER.debug("Adding spatial loader: %s", func.__name__)
        setattr(Data, func.__name__, wrapper)
        Data.spatial_loaders[signature] = func.__name__

        return func

    return decorator


@add_spatial_loader((("cell_id",), ("cell_id",), ("__any__",)))
def spld_cellid_coord_any(self: Data, darray: DataArray) -> DataArray:
    """Spatial loader for cell id coordinates onto any grid.

    In this loader, the DataArray has a cell_id dimension with valued coordinates, which
    should map onto the grid cell ids, allowing for a subset of ids. Because this method
    simply maps data to grid cells by id, it should applies to _any_ arbitrary grid
    setup.
    """

    da_cell_ids = darray["cell_id"].values

    if len(np.unique(da_cell_ids)) != len(da_cell_ids):
        raise ValueError("The data cell ids contain duplicate values.")

    if not set(self.grid.cell_id).issubset(da_cell_ids):
        raise ValueError("The data cell ids are not a superset of grid cell ids.")

    # Now ensure sorting and any subsetting:
    # https://stackoverflow.com/questions/8251541
    da_sortorder = np.argsort(da_cell_ids)
    gridid_pos = np.searchsorted(da_cell_ids[da_sortorder], self.grid.cell_id)
    da_indices = da_sortorder[gridid_pos]

    return darray.isel(cell_id=da_indices)


@add_spatial_loader((("cell_id",), (), ("__any__",)))
def spld_cellid_dim_any(self: Data, darray: DataArray) -> DataArray:
    """Spatial loader for cell id dimension onto any grid.

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
def spld_xy_coord_square(self: Data, darray: DataArray) -> DataArray:
    """Spatial loader for XY coordinates onto a square grid."""

    # Get x and y coords to check the extents and cell coverage.
    #
    # TODO - Note that mapping all the cells here is a bit extreme with a square grid -
    # could just map one row and column to confirm the indexing into the data, but this
    # is a more general solution.

    # Use .stack() to convert the axis into stacked pairs of values
    xy_pairs = darray.stack(cell=("y", "x")).coords
    idx_pairs = darray.drop_vars(("x", "y")).stack(cell=("y", "x")).coords

    # Get the mapping of points onto the grid
    idx_x, idx_y = self.grid.map_xy_to_cell_indexing(
        x_coords=xy_pairs["x"].values,
        y_coords=xy_pairs["y"].values,
        x_idx=idx_pairs["x"].values,
        y_idx=idx_pairs["y"].values,
        strict=False,
    )

    # TODO - fine a way to enable strict = True - probably just kwargs.

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


@add_spatial_loader((("x", "y"), (), ("square",)))
def spld_xy_dim_square(self: Data, darray: DataArray) -> DataArray:
    """Spatial loader for XY dimensions onto a square grid."""

    # Otherwise the data array must be the same shape as the grid
    if self.grid.cell_nx != darray.sizes["x"] or self.grid.cell_ny != darray.sizes["y"]:
        raise ValueError("Data XY dimensions do not match square grid")

    # Use DataArray.stack to combine the x and y into a multiindex called cell_id, with
    # x varying fastest (cell_id goes from top left to top right, then down by rows),
    # and then use these stacked indices to map the 2D onto grid cell order, using
    # isel() to avoid issues with dimension ordering.
    darray_stack = darray.stack(cell_id=("y", "x"))
    darray = darray.isel(
        x=DataArray(darray_stack.coords["x"].values, dims=["cell_id"]),
        y=DataArray(darray_stack.coords["y"].values, dims=["cell_id"]),
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
