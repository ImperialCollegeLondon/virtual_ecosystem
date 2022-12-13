"""API documentation for the :mod:`core.axes` module.
************************************************** # noqa: D205

This module handles the definition of the axis validators and adding validators to the
AXIS_VALIDATORS registry.

Axis registry and validators
============================

A virtual rainforest simulation has a set of core axes - such as spatial, temporal and
soil depth axes - which have dimensions and possibly coordinates that are defined in the
model configuration.  Within a given axis - for example the 'Spatial' axis - there can
be several methods to map the data in a provided array onto the axis. The method
selection depends on matching the _signature_ of a provided array for a particular axis:
this is a combination of the named dimensions and whether the dimensions are associated
with coordinates.  As an example, an array with simple ``x`` and ``y`` dimensions and no
coordinates could be mapped onto a square grid, assuming that the lengths of each
dimension match.

The AXIS_VALIDATORS registry is a dictionary that provides sets of validator methods for
different axes. The list of validators for a given axis is then a mapping of data
signatures to the function that will handle that given signature. The individual
validation functions should take an input that matches the signature, validate it,
implement any internal standardisation and then return the valid, standardised data.

The set of validators provided in the AXIS_VALIDATORS registry can be extended using the
:func:`~virtual_rainforest.core.data.add_validator` decorator, which adds a new
pairing of a signature and method to the appropriate named axis in the registry. So, for
example:

.. code-block:: python

    @add_validator("spatial", (("x", "y"), ("x", "y"), ("square",)))

This adds a validator for the spatial axis that will map a :class:`~xarray.DataArray`
with ``x`` and ``y`` coordinates (and hence implicitly 'x' and 'y' dimensions) onto a
square grid.

.. code-block:: python

    @add_validator("spatial", (("cell_id",), (), ("any",)))

This adds a validator for the spatial axis that will map a :class:`~xarray.DataArray`
with the ``cell_id`` dimension (but no ``cell_id`` coordinates) onto _any_ spatial grid
type: the underlying ``cell_id``  attribute of the grid is defined for all grid.

Core axes
=========

The 'spatial' axis
------------------

At present, the signature also includes only the spatial
:attr:`~virtual_rainforest.core.grid.Grid.grid_type` used in the
:class:`~virtual_rainforest.core.data.Data` instance, but this will likely be expanded
to include configuration details for other core axes.

All spatial loader methods standardise the spatial structure of the input data to use a
single ``cell_id`` spatial axis, which maps data onto the cell IDs used for indexing in
the :class:`~virtual_rainforest.core.grid.Grid` instance for the simulation.
"""

from typing import Any, Callable, Optional

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.grid import GRID_REGISTRY
from virtual_rainforest.core.logger import LOGGER, log_and_raise

AXIS_VALIDATORS: dict[str, dict[tuple, Callable]] = {}
"""A registry for different axis validators

This dictionary is keyed by the name of a particular core axis (e.g. 'spatial'), and the
value for that key is then another dictionary that keys a particular data array
signature to a function that validates data with that signature.

Users can register their own functions to map data onto a core axis using the
:func:`~virtual_rainforest.core.data.register_axis_validator` decorator. The
function itself should have the following signature:

    func(data: Data, darray: DataArray) -> DataArray
"""


def register_axis_validator(axis: str, signature: tuple) -> Callable:
    """Add a new validator and data signature to a core axis.

    This decorator adds the decorated method to the AXIS_VALIDATORS registry to extend
    or amend the available routines used to load and validate an array containing
    spatial information. The decorator adds the method to the list of validators
    provided for the given axis class attribute under the given signature.

    The signature consists of a tuple containing:

    * a tuple of dimension names required in the data array to use the function,
    * a tuple of coordinate names required in the data array to use the function - this
      can be an empty tuple if no coordinate names are required,
    * a tuple of grid types that the loader can be used with. The "any" grid type
      can be used to indicate that a loader will work with any grid type.

    Args:
        axis: The core axis that the validator applies to
        signature: A tuple of the validator signature.
    """

    def decorator(func: Callable) -> Callable:

        # Check the grid types are valid
        grid_types = signature[2]
        for gtype in grid_types:
            if (gtype not in GRID_REGISTRY) and (gtype != "any"):
                log_and_raise(
                    f"Unknown grid type '{gtype}' decorating {func.__name__}",
                    ValueError,
                )

        # Does the axis exist yet?
        if axis not in AXIS_VALIDATORS:
            AXIS_VALIDATORS[axis] = dict()

        # Register the signature -> function map under the given axis, checking if the
        # signature already exists
        if signature in AXIS_VALIDATORS[axis]:
            LOGGER.debug("Replacing existing %s validator: %s", axis, func.__name__)
        else:
            LOGGER.debug("Adding %s validator: %s", axis, func.__name__)

        # Add the validator
        AXIS_VALIDATORS[axis][signature] = func

        return func

    return decorator


def get_validator(axis: str, data: Data, darray: DataArray) -> Optional[Callable]:
    """Get the matching validator function for a data array on a given axis.

    This function iterates over the registered validator functions for a given core axis
    in the AXIS_VALIDATORS registry and matches the data array signatures against the
    provided signatures.

    If the input data array uses dimension names that have been registered to validate a
    particular axis, then a matching validator must be found and an exception is raised
    if no signature is matched. If the dimension names on the data array do not match
    any of the registered dimensions, then the function returns None.

    Args:
        axis: The core axis to get a validator for
        data: A Data object providing parameter information
        darray: The data to match to a validator signature

    Raises:
        ValueError if the input data array uses dimension names required for an axis
        without matching a registered validator.
    """

    # Check the axis exists
    if axis not in AXIS_VALIDATORS:
        raise ValueError(f"Unknown core axis: {axis}")

    # Identify the correct validator routine from the data array signature
    da_dims = set(darray.dims)
    da_coords = set(darray.coords.variables)

    # Track the dimension names used by the validators on this axis - data arrays should
    # not be allowed to use reserved dimension names
    registered_dim_names: set[str] = set()

    # Loop over the available validators loooking for a congruent signature
    # - dims _cannot_ be empty on a DataArray (they default to dim_N strings) so are
    #   guaranteed to be non-empty and must then match.
    # - coords _can_ be empty: they just associate values with indices along the
    #   dimension. So, the signature should match _specified_ coords but not the
    #   empty set.
    for (ld_dims, ld_coords, ld_grid_type), ld_fnm in AXIS_VALIDATORS[axis].items():

        # Compile a set of dimension names associated with this axis
        registered_dim_names.update(ld_dims)
        registered_dim_names.update(ld_coords)

        if (
            set(ld_dims).issubset(da_dims)
            and set(ld_coords).issubset(da_coords)
            and ((data.grid.grid_type in ld_grid_type) or ("any" in ld_grid_type))
        ):

            # Retrieve the method associated with the loader signature from the Data
            # object.
            return ld_fnm

    uses_registered = registered_dim_names.intersection(da_dims.union(da_coords))
    if uses_registered:
        log_and_raise(
            f"DataArray uses '{axis}' axis dimension names but does "
            f"not match a validator: {uses_registered}",
            ValueError,
        )

    return None


@register_axis_validator("spatial", (("cell_id",), ("cell_id",), ("any",)))
def spld_cellid_coord_any(data: Data, darray: DataArray) -> DataArray:
    """Spatial loader for cell id coordinates onto any grid.

    In this loader, the DataArray has a cell_id dimension with valued coordinates, which
    should map onto the grid cell ids, allowing for a subset of ids. Because this method
    simply maps data to grid cells by id, it should apply to _any_ arbitrary grid setup.

    Args:
        data: A Data instance used to access validation information
        darray: A data array containing spatial information to be validated

    Returns:
        A validated dataarray with a single cell id spatial dimension
    """

    da_cell_ids = darray["cell_id"].values

    if len(np.unique(da_cell_ids)) != len(da_cell_ids):
        raise ValueError("The data cell ids contain duplicate values.")

    if not set(data.grid.cell_id).issubset(da_cell_ids):
        raise ValueError("The data cell ids are not a superset of grid cell ids.")

    # Now ensure sorting and any subsetting:
    # https://stackoverflow.com/questions/8251541
    da_sortorder = np.argsort(da_cell_ids)
    gridid_pos = np.searchsorted(da_cell_ids[da_sortorder], data.grid.cell_id)
    da_indices = da_sortorder[gridid_pos]

    return darray.isel(cell_id=da_indices)


@register_axis_validator("spatial", (("cell_id",), (), ("any",)))
def spld_cellid_dim_any(data: Data, darray: DataArray) -> DataArray:
    """Spatial loader for cell id dimension onto any grid.

    In this loader, the DataArray only has a cell_id dimension so assumes that the
    values are provided in the same sequence as the grid cell ids. Because this method
    simply maps data to grid cells by id, it should apply to _any_ arbitrary grid setup.

    Args:
        data: A Data instance used to access validation information
        darray: A data array containing spatial information to be validated

    Returns:
        A validated dataarray with a single cell id spatial dimension

    """

    # Cell ID is only a dimenson with a give length - assume the order correct
    # and check the right number of cells found
    n_found = darray["cell_id"].size
    if data.grid.n_cells != n_found:
        raise ValueError(
            f"Grid defines {data.grid.n_cells} cells, data provides {n_found}"
        )

    return darray


@register_axis_validator("spatial", (("x", "y"), ("x", "y"), ("square",)))
def spld_xy_coord_square(data: Data, darray: DataArray) -> DataArray:
    """Spatial loader for XY coordinates onto a square grid.

    In this loader, the DataArray has a x and y dimensions with valued coordinates,
    which should map onto the grid cell ids, allowing for a subset of ids.

    Args:
        data: A Data instance used to access validation information
        darray: A data array containing spatial information to be validated

    Returns:
        A validated dataarray with a single cell id spatial dimension
    """

    # Get x and y coords to check the extents and cell coverage.
    #
    # TODO - Note that mapping all the cells here is a bit extreme with a square grid -
    # could just map one row and column to confirm the indexing into the data, but this
    # is a more general solution.

    # Use .stack() to convert the axis into stacked pairs of values
    xy_pairs = darray.stack(cell=("y", "x")).coords
    idx_pairs = darray.drop_vars(("x", "y")).stack(cell=("y", "x")).coords

    # Get the mapping of points onto the grid
    idx_x, idx_y = data.grid.map_xy_to_cell_indexing(
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

    return darray.isel(
        x=DataArray(idx_x, dims=["cell_id"]), y=DataArray(idx_y, dims=["cell_id"])
    )


@register_axis_validator("spatial", (("x", "y"), (), ("square",)))
def spld_xy_dim_square(data: Data, darray: DataArray) -> DataArray:
    """Spatial loader for XY dimensions onto a square grid.

    In this loader, the DataArray has x and y dimension but no coordinates along those
    dimensions. The assumption here is then that those spatial axes must describe the
    same array shape as the square grid.

    Args:
        data: A Data instance used to access validation information
        darray: A data array containing spatial information to be validated

    Returns:
        A validated dataarray with a single cell id spatial dimension
    """

    # Otherwise the data array must be the same shape as the grid
    if data.grid.cell_nx != darray.sizes["x"] or data.grid.cell_ny != darray.sizes["y"]:
        raise ValueError("Data XY dimensions do not match square grid")

    # Use DataArray.stack to combine the x and y into a multiindex called cell_id, with
    # x varying fastest (cell_id goes from top left to top right, then down by rows),
    # and then use these stacked indices to map the 2D onto grid cell order, using
    # isel() to avoid issues with dimension ordering.
    darray_stack = darray.stack(cell_id=("y", "x"))

    return darray.isel(
        x=DataArray(darray_stack.coords["x"].values, dims=["cell_id"]),
        y=DataArray(darray_stack.coords["y"].values, dims=["cell_id"]),
    )


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
