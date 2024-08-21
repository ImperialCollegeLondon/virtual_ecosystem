"""The :mod:`~virtual_ecosystem.core.axes` module handles the validation of data being
loaded into the core data storage of the Virtual Ecosystem simulation. The main
functionality in this module is ensuring that any loaded data is congruent with the core
axes of the simulation and the configuration of a given simulation.

The AxisValidator class
=======================

The :class:`~virtual_ecosystem.core.axes.AxisValidator` abstract base class provides an
extensible framework for validating data arrays. Each subclass of the base class defines
a particular core axis along with the name or names of dimensions in the input array
that are expected to map onto that axis. So, for example, a validator can support the
``spatial`` axis using the ``x`` and ``y`` dimensions. Each individual subclass provides
bespoke methods to test whether that validator can be applied to an input data array and
then a validation routine to apply when it can.

When new :class:`~virtual_ecosystem.core.axes.AxisValidator` subclasses are defined,
they are automatically added to the
:attr:`~virtual_ecosystem.core.axes.AXIS_VALIDATORS` registry. This maintains a list of
the validators defined for each core axis.

Note that the set of validators defined for a specific core axis should be mutually
exclusive: only one should be applicable to any given dataset being tested on that axis.

DataArray validation
====================

The :func:`~virtual_ecosystem.core.axes.validate_dataarray` function takes an input
Data Array and applies validation where applicable across all the core axes. The
function returns the validated input (possibly altered to align with the core axes)
along with a dictionary using the set of core axes as names: the value associated with
each axis name is the name of the AxisValidator applied or None if the input did not
match a validator on that axis.

Core axes
=========

The 'spatial' axis
------------------

The :class:`~virtual_ecosystem.core.axes.AxisValidator` subclasses defined for the
'spatial' axis  standardise the spatial structure of the input data to use a single
``cell_id`` spatial axis, which maps data onto the cell IDs used for indexing in the
:class:`~virtual_ecosystem.core.grid.Grid` instance for the simulation. `x`
"""  # noqa: D205

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.logger import LOGGER


class AxisValidator(ABC):
    """The AxisValidator abstract base class.

    This abstract base class provides the structure for axis validators. These are used
    to check that a ``DataArray`` to be added to a ``Data`` instance is congruent with
    the configuration of a Virtual Ecosystem simulation. The base class provides
    abstract methods that provide the following functionality:

    * :meth:`~virtual_ecosystem.core.axes.AxisValidator.can_validate`: test that a
      given ``AxisValidator`` subclass can be applied to the inputs.
    * :meth:`~virtual_ecosystem.core.axes.AxisValidator.run_validation`: run
      appropriate validation and standardisation on the input ``DataArray``.

    The :meth:`~virtual_ecosystem.core.axes.AxisValidator.can_validate` method should
    be used first to check that a particular ``DataArray`` can be validated, and then
    the :meth:`~virtual_ecosystem.core.axes.AxisValidator.run_validation` method can be
    used to validate that input if appropriate.
    """

    core_axis: str
    """Class attribute giving the name of the core axis for an AxisValidator."""

    dim_names: frozenset[str]
    """Class attribute giving the dimension names for an AxisValidator."""

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def __init_subclass__(cls) -> None:
        """Adds new subclasses to the AxisValidator registry.

        When new subclasses are created this method automatically extends the
        :attr:`~virtual_ecosystem.core.axes.AXIS_VALIDATORS` registry. AxisValidators
        are arranged in the registry dictionary as lists keyed under core axis names,
        and the core axis name for a given subclass is set in the  subclass
        :attr:`~virtual_ecosystem.core.axes.AxisValidator.core_axis`
        class attribute.

        Raises:
            ValueError: if the subclass attributes are invalid.
        """

        if not hasattr(cls, "core_axis"):
            raise ValueError("Class attribute core_axis not set.")

        if not isinstance(cls.core_axis, str) or cls.core_axis == "":
            raise ValueError(
                "Class attribute core_axis is not a string or is an empty string."
            )

        if not hasattr(cls, "dim_names"):
            raise ValueError("Class attribute dim_names not set.")

        if not isinstance(cls.dim_names, frozenset) or any(
            [not isinstance(x, str) for x in cls.dim_names]
        ):
            raise ValueError("Class attribute dim_names is not a frozenset of strings.")

        if cls.core_axis in AXIS_VALIDATORS:
            AXIS_VALIDATORS[cls.core_axis].append(cls)
        else:
            AXIS_VALIDATORS[cls.core_axis] = [cls]

        LOGGER.debug("Adding '%s' AxisValidator: %s", cls.core_axis, cls.__name__)

    @abstractmethod
    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check if an AxisValidator subclass applies to inputs.

        A given AxisValidator subclass must provide a ``run_validation`` method that
        defines data validation that should be applied to the inputs. However, the
        validation for a particular subclass will only apply to inputs with particular
        features, such as an array with a given dimension name or a set grid type.

        In a subclass, the implementation of this method should check whether the
        validation implemented in ``run_validation`` **can** be applied to the inputs.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A boolean showing if the `run_validation` method of the subclass can be
            applied to the inputs.
        """

    @abstractmethod
    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Validate the input DataArray.

        The implementation for an AxisValidator subclass should define a set of checks
        on the inputs that are used to validate that the input DataArray value is
        congruent with the simulation configuration. The method can also perform
        standardisation and return a modified input value that has been aligned to the
        simulation structure.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A DataArray that passes validation, possibly modified to align with internal
            data structures.
        """


AXIS_VALIDATORS: dict[str, list[type[AxisValidator]]] = {}
"""A registry for different axis validators subclasses

This registry contains a dictionary of lists of AxisValidator subclasses. Each list
contains all of AxisValidator subclasses that apply to a particular core axis, and the
core axis names are used as the key to these lists.

Users defined AxisValidator subclasses will be automatically added to this registry by
the ``__subclass_init__`` method.
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
        **kwargs: Further configuration details to be passed to AxisValidators

    Returns:
        The function returns the validated data array and a dictionary recording which
        AxisValidator classes were applied to each of the core axes.

    Raises:
        ValueError: If the input data array uses dimension names required for an axis
            without matching a registered validator.
        RuntimeError: If more than one validator reports that it can validate an input.
    """

    validation_dict: dict[str, str | None] = {}
    to_raise: Exception

    # Get the validators applying to each axis
    for axis in AXIS_VALIDATORS:
        validators: list[type[AxisValidator]] = AXIS_VALIDATORS[axis]

        # Get the set of dim names across all of the validators for this axis
        validator_dims = frozenset.union(*[v.dim_names for v in validators])

        # If the dataarray includes any of those dimension names, one of the validators
        # for that axis must be able to validate the array, otherwise we can skip
        # validation on this axis and return the input array.
        matching_dims = validator_dims.intersection(value.dims)
        if matching_dims:
            # There should be one and only validator that can validate for this axis.
            validator_found = [v for v in validators if v().can_validate(value, grid)]

            if len(validator_found) == 0:
                to_raise = ValueError(
                    f"DataArray uses '{axis}' axis dimension names but does "
                    f"not match a validator: {','.join(matching_dims)}"
                )
                LOGGER.critical(to_raise)
                raise to_raise

            if len(validator_found) > 1:
                to_raise = RuntimeError(
                    f"Validators on '{axis}' axis not mutually exclusive"
                )
                LOGGER.critical(to_raise)
                raise to_raise

            # Get the appropriate Validator class and then use it to update the data
            # array
            this_validator = validator_found[0]
            try:
                value = this_validator().run_validation(value, grid, **kwargs)
            except Exception as excep:
                LOGGER.critical(excep)
                raise

            validation_dict[axis] = this_validator.__name__

        else:
            validation_dict[axis] = None

    return value, validation_dict


class Spat_CellId_Coord_Any(AxisValidator):
    """Validate *cell_id* coordinates on the *spatial* core axis.

    Applies to:
        An input DataArray that provides coordinate values along a ``cell_id`` dimension
        is assumed to map data onto the cells values defined in the
        :class:`~virtual_ecosystem.core.grid.Grid` configured for the simulation. The
        coordinate values are tested to check they provide a one-to-one map onto the
        ``cell_id`` values defined for each cell in the ``Grid``. Because ``cell_id``
        values are defined for cells in all grid types, this validator does not require
        a particular grid geometry.
    """

    core_axis = "spatial"
    dim_names = frozenset(["cell_id"])

    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check the validator applies to the inputs.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A boolean showing if this subclass can be applied to the inputs.
        """
        return self.dim_names.issubset(value.dims) and self.dim_names.issubset(
            value.coords
        )

    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Run validation on the inputs.

        Validation will fail if the ``cell_id`` coordinate values:

        * are not unique, or
        * do not provide a one-to-one mapping onto the set of ``cell_id`` values defined
          in the configured ``Grid`` object.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Raises:
            ValueError: when ``cell_id`` values are not congruent with the ``Grid``.

        Returns:
            A DataArray standardised to match the ``cell_id`` values in the ``Grid``
            object.
        """
        da_cell_ids = value["cell_id"].values

        if len(np.unique(da_cell_ids)) != len(da_cell_ids):
            raise ValueError("The data cell ids contain duplicate values.")

        if not set(grid.cell_id) == set(da_cell_ids):
            raise ValueError(
                "The data cell ids do not provide a one-to-one map onto grid cell ids."
            )

        # Now ensure sorting and any subsetting:
        # https://stackoverflow.com/questions/8251541
        da_sortorder = np.argsort(da_cell_ids)
        gridid_pos = np.searchsorted(da_cell_ids[da_sortorder], grid.cell_id)
        da_indices = da_sortorder[gridid_pos]

        return value.isel(cell_id=da_indices)


class Spat_CellId_Dim_Any(AxisValidator):
    """Validate *cell_id* dimension on the *spatial* core axis.

    Applies to:
        The input DataArray for this validator has a ``cell_id`` dimension but there are
        no ``cell_id`` values provided as coordinates along that dimension. The
        ``cell_id`` dimension name means that the array is assumed to provide data for
        the cells defined in the :class:`~virtual_ecosystem.core.grid.Grid` configured
        for the simulation. The data are then assumed to be in the same order as the
        cells in the ``Grid``.  As a one-dimensional array of cells is defined for all
        grid configurations, this validator does not require a particular grid geometry.
    """

    core_axis = "spatial"
    dim_names = frozenset(["cell_id"])

    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check the validator applies to the inputs.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A boolean showing if this subclass can be applied to the inputs.
        """

        return self.dim_names.issubset(value.dims) and not self.dim_names.issubset(
            value.coords
        )

    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Run validation on the inputs.

        Validation will fail when the ``cell_id`` dimension:

        * is not of exactly the same length as the list of cells defined in the
          configured ``Grid`` object.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Raises:
            ValueError: when ``cell_id`` values are not congruent with the ``Grid``.

        Returns:
            A DataArray standardised to match the ``cell_id`` values in the ``Grid``
            object.
        """
        # Cell ID is only a dimenson with a give length - assume the order correct and
        # check the right number of cells found
        n_found = value["cell_id"].size
        if grid.n_cells != n_found:
            raise ValueError(
                f"Grid defines {grid.n_cells} cells, data provides {n_found}"
            )

        return value


class Spat_XY_Coord_Square(AxisValidator):
    """Validate *x* and *y* coordinates on the *spatial* core axis for a square grid.

    Applies to:
        An input DataArray that provides coordinates along ``x`` and ``y`` dimensions is
        assumed to map data onto the cells defined in a
        :class:`~virtual_ecosystem.core.grid.Grid` configured for the simulation with a
        ``square`` cell geometry. The pairwise combinations of ``x`` and ``y``
        coordinates in the data are expected to provide a one-to-one mapping onto  grid
        cell geometries.

    This validator also remaps ``x`` and ``y`` dimensions onto the internal ``cell_id``
    dimension used in the :mod:`~virtual_ecosystem.core.grid` module.
    """

    core_axis = "spatial"
    dim_names = frozenset(["x", "y"])

    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check the validator applies to the inputs.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A boolean showing if this subclass can be applied to the inputs.
        """
        return self.dim_names.issubset(value.dims) and self.dim_names.issubset(
            value.coords
        )

    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Run validation on the inputs.

        Validation will fail when the ``x`` and ``y`` coordinates:

        * Fall on cell geometry boundaries: unambiguous coordinates within the geometry,
          such as cell centroids, should be used.
        * The coordinate pairs do not provide a one-to-one mapping onto the cells:
          multiple coordinates map onto a single cell, there is not a coordinate pair
          for each cell, or some coordinate pairs do not map onto a cell.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Raises:
            ValueError: when ``x`` and ``y`` values are not congruent with the ``Grid``.

        Returns:
            A DataArray with the ``x`` and ``y`` dimensions remapped onto the internal
            ``cell_id`` dimension used in the :mod:`~virtual_ecosystem.core.grid`
            module.
        """
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
        )

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
    """Validate *x* and *y* dimensions on the *spatial* core axis on a square grid.

    Applies to:
        An input DataArray with ``x`` and ``y`` dimensions specifies the size of the
        array along those dimensions but does not provide coordinates for the cells. The
        input is then  assumed to provide an array with the same shape as a the cell
        grid of a :class:`~virtual_ecosystem.core.grid.Grid` configured for the
        simulation with a ``square`` cell geometries.

    This validator also remaps ``x`` and ``y`` dimensions onto the internal ``cell_id``
    dimension used in the :mod:`~virtual_ecosystem.core.grid` module.
    """

    core_axis = "spatial"
    dim_names = frozenset(["x", "y"])

    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check the validator applies to the inputs.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A boolean showing if this subclass can be applied to the inputs.
        """
        return self.dim_names.issubset(value.dims) and not self.dim_names.issubset(
            value.coords
        )

    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Run validation on the inputs.

        Validation will fail when the ``x`` and ``y`` dimensions:

        * do not have exactly the same shape - numbers of rows (``y``) and columns
          (``x``) as the configured square ``Grid``.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Raises:
            ValueError: when ``x`` and ``y`` values are not congruent with the ``Grid``.

        Returns:
            A DataArray with the ``x`` and ``y`` dimensions remapped onto the internal
            ``cell_id`` dimension used in the :mod:`~virtual_ecosystem.core.grid`
            module.
        """
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


class Time(AxisValidator):
    """Validate temporal coordinates on the *time* core axis.

    Applies to:
        An input DataArray that provides coordinate values along a ``time`` dimension.

    TODO: this is just a placeholder at present to establish the ``time`` axis name.

    """

    core_axis = "time"
    dim_names = frozenset(["time"])

    def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
        """Check the validator applies to the inputs.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Returns:
            A boolean showing if this subclass can be applied to the inputs.
        """
        return self.dim_names.issubset(value.dims) and self.dim_names.issubset(
            value.coords
        )

    def run_validation(self, value: DataArray, grid: Grid, **kwargs: Any) -> DataArray:
        """Run validation on the inputs.

        Does nothing at present.

        Args:
            value: An input DataArray to check
            grid: A Grid object giving the spatial configuration of the simulation.
            **kwargs: Other configuration details to be used.

        Raises:
            ValueError: when the time coordinates are not congruent with the model
                timing steps.

        Returns:
            A DataArray, possibly truncated to the steps defined in the model timing.
        """

        return value
