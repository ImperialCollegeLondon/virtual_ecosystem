"""API documentation for the :mod:`core.axes` module.
************************************************** # noqa: D205

This module handles the validation of data being loaded into the core data storage of
the virtual rainforest simulation. The main functionality in this module is ensuring
that any loaded data is congruent with the core axes of the simulation and the
configuration of a given simulation.

The AxisValidator class
=======================

The :class:`~virtual_rainforest.core.axes.AxisValidator` abstract base class provides an
extensible framework for validating data arrays. Each subclass of the base class defines
a particular core axis along with the name or names of dimensions in the input array
that are expected to map onto that axis. So, for example, a validator can support the
`spatial` axis using the `x` and `y` dimensions. Each individual subclass provides
bespoke methods to test whether that validator can be applied to an input data array and
then a validation routine to apply when it can.

When new :class:`~virtual_rainforest.core.axes.AxisValidator` subclasses are defined,
they are automatically added to the AXIS_VALIDATORS registry. This maintains a list of
the validators define for each core axis.

Note that the set of validators defined for a specific core axis should be mutually
exclusive: only one should be applicable to any given dataset being tested on that axis.

DataArray validation
====================

The :func:`~virtual_rainforest.core.axes.validate_datarray` function takes an input Data
Array and applies validation where applicable across all the core axes. The function
returns the validated input (possibly altered to align with the core axes) along with a
dictionary recording which (if any) AxisValidator has been applied to each core axis.

Core axes
=========

The 'spatial' axis
------------------

The :class:`~virtual_rainforest.core.axes.AxisValidator` subclasses defined for the
'spatial' axis  standardise the spatial structure of the input data to use a single
``cell_id`` spatial axis, which maps data onto the cell IDs used for indexing in the
:class:`~virtual_rainforest.core.grid.Grid` instance for the simulation.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Type

import numpy as np
from xarray import DataArray

from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.logger import LOGGER, log_and_raise


class AxisValidator(ABC):
    """The AxisValidator abstract base class.

    This ABC provides the structure for axis validators. These are used to check that a
    DataArray to be added to a Data instance is congruent with the configuration of a
    virtual rainforest simulation. The base class provides abstract methods that provide
    the following functionality:

    * Test if the validator subclass can be applied to a particular DataArray
      (:meth:`~virtual_rainforest.core.axes.AxisValidator.can_validate`).
    * Run any appropriate validation on DataArrays that pass the validation test
      (:meth:`~virtual_rainforest.core.axes.AxisValidator.run_validation`).

    The :meth:`~virtual_rainforest.core.axes.AxisValidator.can_validate` method should
    be used first to check that a particular `DataArray` can be validated, and then the
    :meth:`~virtual_rainforest.core.axes.AxisValidator.run_validation` method can be
    used to validate that input if appropriate. The method also sets the attributes of
    validated DataArrays to record that validation has been passed on the core axis.
    """

    core_axis: str = ""
    dim_names: set[str] = {""}

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def __init_subclass__(cls) -> None:
        """Adds new subclasses to the AxisValidator registry.

        When new subclasses are created this method automatically extends the
        :var:`~virtual_rainforest.core.axes.AXIS_VALIDATORS` registry. The subclass is
        added to the list of AxisValidators that apply to the subclass core axis.
        """

        if cls.core_axis == "":
            raise ValueError("Core axis name cannot be an empty string.")

        if not cls.dim_names:
            raise ValueError("AxisValidator dim names cannot be an empty set.")

        if cls.core_axis in AXIS_VALIDATORS:
            AXIS_VALIDATORS[cls.core_axis].append(cls)
        else:
            AXIS_VALIDATORS[cls.core_axis] = [cls]

        # Copy ABC docstrings to the subclass
        cls.can_validate.__doc__ = AxisValidator.can_validate.__doc__
        cls.run_validation.__doc__ = AxisValidator.run_validation.__doc__

        LOGGER.debug("Adding '%s' AxisValidator: %s", cls.core_axis, cls.__name__)

    @abstractmethod
    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check the validator can validate a given DataArray.

        This method checks if the input DataArray includes dimensions mapping onto the
        core axis for this AxisValidator and any further checks on whether this specific
        validator for the core axis can be applied.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            kwargs: Other configuration details to be used.
        """

    @abstractmethod
    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Validate the input DataArray.

        This method defines the validation steps to be applied if the input DataArray
        can be validated by this AxisValidator.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            kwargs: Other configuration details to be used.
        """


AXIS_VALIDATORS: dict[str, list[Type[AxisValidator]]] = {}
"""A registry for different axis validators subclasses

This registry contains a dictionary of lists of AxisValidator subclasses. Each list
contains all of AxisValidator subclasses that apply to a particular core axis, and the
core axis names are used as the key to these lists.

Users defined AxisValidator subclasses will be automatically added to this registry by
the `__subclass_init__` method.
"""


def validate_dataarray(
    value: DataArray, grid: Grid, **kwargs: Any
) -> tuple[DataArray, dict]:
    """Validate a DataArray across the core axes.

    The AXIS_VALIDATORS registry provides a list of AxisValidators subclasses for each
    core axis. This function loops over the core axes, and checks whether to apply
    validation for that axis to the input DataArray.

    For each axis in turn, the function first checks if the dimension names of the input
    DataArray overlap with the set of dimension names used across the AxisValidators for
    that axis. If not, then the next axis is checked without altering the input array.
    If the dimension names do match the axis then the appropriate AxisValidator is then
    used to validate the input array and the validated array is passed on to the next
    axis for further validation.

    Args:
        value: An input DataArray for validation
        grid: A Grid object giving the spatial configuration.
        kwargs: Further configuration details to be passed to AxisValidators

    Returns:
        The function returns the validated data array and a dictionary recording which
        AxisValidator classes were applied to each of the core axes.

    Raises:
        ValueError: If the input data array uses dimension names required for an axis
            without matching a registered validator.
        RuntimeError: If more than one validator reports that it can validate an input.
    """

    validation_dict: dict[str, Optional[str]] = {}

    # Get the validators applying to each axis
    for axis in AXIS_VALIDATORS:

        validators: list[Type[AxisValidator]] = AXIS_VALIDATORS[axis]

        # Get the set of dim names across all of the validators for this axis
        validator_dims = set.union(*[v.dim_names for v in validators])

        # If the dataarray includes any of those dimension names, one of the validators
        # for that axis must be able to validate the array, otherwise we can skip
        # validation on this axis and return the input array.
        matching_dims = validator_dims.intersection(value.dims)
        if matching_dims:

            # There should be one and only validator that can validate for this axis.
            validator_found = [v for v in validators if v().can_validate(value, grid)]

            if len(validator_found) == 0:
                log_and_raise(
                    f"DataArray uses '{axis}' axis dimension names but does "
                    f"not match a validator: {','.join(matching_dims)}",
                    ValueError,
                )

            if len(validator_found) > 1:
                log_and_raise(
                    f"Validators on '{axis}' axis not mutually exclusive", RuntimeError
                )

            # Get the appropriate Validator class and then use it to update the data
            # array
            this_validator = validator_found[0]
            try:
                value = this_validator().run_validation(value, grid, **kwargs)
            except Exception as excep:
                log_and_raise(str(excep), excep.__class__)

            validation_dict[axis] = this_validator.__name__

        else:
            validation_dict[axis] = None

    return value, validation_dict


class Spat_CellId_Coord_Any(AxisValidator):
    """Spatial Axis Validator for cell id coordinates on any grid.

    This spatial axis validator applies to a DataArray that has a cell_id dimension with
    valued coordinates, which should map onto the grid cell ids, allowing for a subset
    of ids. Because this method simply maps data to grid cells by id, it should apply to
    _any_ arbitrary grid setup.
    """

    core_axis = "spatial"
    dim_names = {"cell_id"}

    def can_validate(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> bool:

        return self.dim_names.issubset(value.dims) and self.dim_names.issubset(
            value.coords
        )

    def run_validation(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> DataArray:

        da_cell_ids = value["cell_id"].values

        if len(np.unique(da_cell_ids)) != len(da_cell_ids):
            raise ValueError("The data cell ids contain duplicate values.")

        if not set(grid.cell_id).issubset(da_cell_ids):
            raise ValueError("The data cell ids are not a superset of grid cell ids.")

        # Now ensure sorting and any subsetting:
        # https://stackoverflow.com/questions/8251541
        da_sortorder = np.argsort(da_cell_ids)
        gridid_pos = np.searchsorted(da_cell_ids[da_sortorder], grid.cell_id)
        da_indices = da_sortorder[gridid_pos]

        return value.isel(cell_id=da_indices)


class Spat_CellId_Dim_Any(AxisValidator):
    """Spatial validator for cell id dimension onto any grid.

    This spatial axis validator applies to a DataArray that only has a cell_id
    dimension. It assumes that the values are provided in the same sequence as the grid
    cell ids. Because this method simply maps data to grid cells by id, it should apply
    to _any_ arbitrary grid setup.
    """

    core_axis = "spatial"
    dim_names = {"cell_id"}

    def can_validate(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> bool:
        return self.dim_names.issubset(value.dims) and not self.dim_names.issubset(
            value.coords
        )

    def run_validation(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> DataArray:

        # Cell ID is only a dimenson with a give length - assume the order correct and
        # check the right number of cells found
        n_found = value["cell_id"].size
        if grid.n_cells != n_found:
            raise ValueError(
                f"Grid defines {grid.n_cells} cells, data provides {n_found}"
            )

        return value


class Spat_XY_Coord_Square(AxisValidator):
    """Spatial validator for XY coordinates onto a square grid.

    This spatial axis validator applies to a  DataArray that has a x and y dimensions
    with valued coordinates, which should map onto the grid cell ids, allowing for a
    subset of ids.
    """

    core_axis = "spatial"
    dim_names = {"x", "y"}

    def can_validate(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> bool:
        return self.dim_names.issubset(value.dims) and self.dim_names.issubset(
            value.coords
        )

    def run_validation(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> DataArray:

        # Get x and y coords to check the extents and cell coverage.
        #
        # TODO - Note that mapping all the cells here is a bit extreme with a square
        # grid - could just map one row and column to confirm the indexing into the
        # data, but this is a more general solution.

        # Use .stack() to convert the axis into stacked pairs of values
        xy_pairs = value.stack(cell=("y", "x")).coords
        idx_pairs = value.drop_vars(("x", "y")).stack(cell=("y", "x")).coords

        # Get the mapping of points onto the grid
        idx_x, idx_y = grid.map_xy_to_cell_indexing(
            x_coords=xy_pairs["x"].values,
            y_coords=xy_pairs["y"].values,
            x_idx=idx_pairs["x"].values,
            y_idx=idx_pairs["y"].values,
            strict=False,
        )

        # TODO - fine a way to enable strict = True - probably just kwargs.

        # Now remap the grids from xy to cell_id - this uses the rather under described
        # vectorized indexing feature in xarray:
        #
        #   https://docs.xarray.dev/en/stable/user-guide/indexing.html
        #
        # Specifically using DataArray.isel to select indexed dimensions by name, which
        # avoids issues with different permutations of the axes - and map XY onto a
        # common cell_id

        return value.isel(
            x=DataArray(idx_x, dims=["cell_id"]), y=DataArray(idx_y, dims=["cell_id"])
        )


class Spat_XY_Dim_Square(AxisValidator):
    """Spatial validator for XY dimensions onto a square grid.

    This spatial axis validator applies to a  DataArray has x and y dimension but no
    coordinates along those dimensions. The assumption here is then that those spatial
    axes must describe the same array shape as the square grid.
    """

    core_axis = "spatial"
    dim_names = {"x", "y"}

    def can_validate(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> bool:
        return self.dim_names.issubset(value.dims) and not self.dim_names.issubset(
            value.coords
        )

    def run_validation(  # noqa: D102
        self, value: DataArray, grid: Grid, **kwargs: Any
    ) -> DataArray:

        # Otherwise the data array must be the same shape as the grid
        if grid.cell_nx != value.sizes["x"] or grid.cell_ny != value.sizes["y"]:
            raise ValueError("Data XY dimensions do not match square grid")

        # Use DataArray.stack to combine the x and y into a multiindex called cell_id,
        # with x varying fastest (cell_id goes from top left to top right, then down by
        # rows), and then use these stacked indices to map the 2D onto grid cell order,
        # using isel() to avoid issues with dimension ordering.
        darray_stack = value.stack(cell_id=("y", "x"))

        return value.isel(
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
