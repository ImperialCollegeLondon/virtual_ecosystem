"""Testing the data validators."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, DEBUG
from typing import Callable

import numpy as np
import pytest
from xarray import DataArray

from .conftest import log_check


@pytest.mark.parametrize(
    argnames=["axis", "signature", "exp_err", "expected_log"],
    argvalues=[
        (  # Unknown singleton
            "spatial",
            (("zzz",), ("zzz",), ("penrose",)),
            pytest.raises(ValueError),
            ((CRITICAL, "Unknown grid type 'penrose' decorating mock_function"),),
        ),
        (  # Unknown grid in 2 tuple
            "spatial",
            (("zzz",), ("zzz",), ("square", "penrose")),
            pytest.raises(ValueError),
            ((CRITICAL, "Unknown grid type 'penrose' decorating mock_function"),),
        ),
        (  # Succesful singleton
            "spatial",
            (("zzz",), ("zzz",), ("square",)),
            does_not_raise(),
            ((DEBUG, "Adding spatial validator: mock_function"),),
        ),
        (  # Succesful 2 tuple
            "spatial",
            (("zzz",), ("zzz",), ("square", "hexagon")),
            does_not_raise(),
            ((DEBUG, "Adding spatial validator: mock_function"),),
        ),
        (  # Replace validator
            "spatial",
            (("yyy",), ("yyy",), ("square",)),
            does_not_raise(),
            ((DEBUG, "Replacing existing spatial validator: mock_function"),),
        ),
    ],
)
def test_register_axis_validator(caplog, axis, signature, exp_err, expected_log):
    """Tests the register_axis_validator decorator.

    TODO - Note that the test here is actually changing the live AXIS_VALIDATORS,
           so that the order of execution of the parameterisation for the tests are not
           independent of one another.
    """

    # Import register_axis_validator - this triggers various registration messages, so
    # need to use caplog.clear()

    from virtual_rainforest.core.axes import register_axis_validator
    from virtual_rainforest.core.logger import LOGGER

    # Capture debug/setup messages
    LOGGER.setLevel("DEBUG")

    # Create an existing validator to clash with
    @register_axis_validator("spatial", (("yyy",), ("yyy",), ("square",)))
    def mock_function_existing():
        return

    caplog.clear()

    # Decorate a mock function to test the failure modes
    with exp_err:

        @register_axis_validator(axis, signature)
        def mock_function():
            return

    # Check the error reports
    log_check(caplog, expected_log)


@pytest.mark.parametrize(
    argnames=["axis", "darray", "exp_err", "exp_msg", "exp_type", "exp_name"],
    argvalues=[
        pytest.param(
            "xy",
            DataArray(data=np.arange(100), dims=("cell_id")),
            pytest.raises(ValueError),
            "Unknown core axis: xy",
            type(None),
            None,
            id="Bad axis name",
        ),
        pytest.param(
            "spatial",
            DataArray(data=np.arange(100), dims=("cell_id")),
            does_not_raise(),
            None,
            Callable,
            "vldr_spat_cellid_dim_any",
            id="Match found",
        ),
        pytest.param(
            "spatial",
            DataArray(data=np.arange(100), dims=("x")),
            pytest.raises(ValueError),
            "DataArray uses 'spatial' axis dimension names but "
            "does not match a validator: x",
            type(None),
            None,
            id="Uses dims, no match",
        ),
        pytest.param(
            "spatial",
            DataArray(data=np.arange(100), dims=("cell_identities")),
            does_not_raise(),
            None,
            type(None),
            None,
            id="No match found",
        ),
    ],
)
def test_get_validator(
    fixture_data, axis, darray, exp_err, exp_msg, exp_type, exp_name
):
    """Test the get_validator function."""

    from virtual_rainforest.core.axes import get_validator

    # Decorate a mock function to test the failure modes
    with exp_err as err:
        val_func = get_validator(axis, fixture_data, darray)

    if err is not None:
        assert str(err.value) == exp_msg
    else:
        assert isinstance(val_func, exp_type)

        if val_func is not None:
            assert val_func.__name__ == exp_name


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (
            {"grid_type": "square"},
            DataArray(data=np.arange(50), dims=("cell_id")),
            pytest.raises(ValueError),
            "Grid defines 100 cells, data provides 50",
            None,
        ),
        (
            {"grid_type": "square"},
            DataArray(data=np.arange(100), dims=("cell_id")),
            does_not_raise(),
            None,
            np.arange(100),
        ),
    ],
)
def test_vldr_spat_cellid_dim_any(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.axes import vldr_spat_cellid_dim_any
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)

    with exp_err as excep:
        darray = vldr_spat_cellid_dim_any(darray, grid=grid)
        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (  # grid cell ids not covered by data
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(data=np.arange(6), coords={"cell_id": [1, 2, 3, 4, 5, 9]}),
            pytest.raises(ValueError),
            "The data cell ids are not a superset of grid cell ids.",
            None,
        ),
        (  # Duplicate ids in data
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(data=np.arange(6), coords={"cell_id": [0, 1, 2, 5, 4, 5]}),
            pytest.raises(ValueError),
            "The data cell ids contain duplicate values.",
            None,
        ),
        (  # - same size and order
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(data=np.arange(6), coords={"cell_id": [0, 1, 2, 3, 4, 5]}),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
        (  # - same order but more ids in cell data
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(
                data=np.arange(9), coords={"cell_id": [0, 1, 2, 3, 4, 5, 6, 7, 8]}
            ),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
        (  # - different order
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(
                data=np.array([5, 3, 1, 0, 4, 2]),
                coords={"cell_id": [5, 3, 1, 0, 4, 2]},
            ),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
        (  # - different order and subsetting
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 2},
            DataArray(
                data=np.array([6, 5, 7, 3, 1, 0, 4, 2, 8]),
                coords={"cell_id": [6, 5, 7, 3, 1, 0, 4, 2, 8]},
            ),
            does_not_raise(),
            None,
            [0, 1, 2, 3, 4, 5],
        ),
    ],
)
def test_vldr_spat_cellid_coord_any(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.axes import vldr_spat_cellid_coord_any
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)

    with exp_err as excep:
        darray = vldr_spat_cellid_coord_any(darray, grid=grid)

        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (  # Wrong size
            {"grid_type": "square", "cell_nx": 2, "cell_ny": 3},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]), dims=("y", "x")
            ),
            pytest.raises(ValueError),
            "Data XY dimensions do not match square grid",
            None,
        ),
        (  # All good
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]), dims=("y", "x")
            ),
            does_not_raise(),
            None,
            np.arange(9),
        ),
    ],
)
def test_vldr_spat_xy_dim_square(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.axes import vldr_spat_xy_dim_square
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)

    with exp_err as excep:
        darray = vldr_spat_xy_dim_square(darray, grid)
        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message


@pytest.mark.parametrize(
    argnames=["grid_args", "darray", "exp_err", "exp_message", "exp_vals"],
    argvalues=[
        (  # Coords on cell boundaries
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
                coords={"y": [2, 1, 0], "x": [2, 1, 0]},
            ),
            pytest.raises(ValueError),
            "Mapped points fall on cell boundaries.",
            None,
        ),
        (  # Does not cover cells
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5]]),
                coords={"y": [2.5, 1.5], "x": [2.5, 1.5, 0.5]},
            ),
            pytest.raises(ValueError),
            "Mapped points do not cover all cells.",
            None,
        ),
        (  # Irregular sampling on y axis gives multiple points in bottom row
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]]),
                coords={"y": [2.5, 1.5, 0.5, 0.4], "x": [0.5, 1.5, 2.5]},
            ),
            pytest.raises(ValueError),
            "Some cells contain more than one point.",
            None,
        ),
        (  # All good
            {"grid_type": "square", "cell_nx": 3, "cell_ny": 3, "cell_area": 1},
            DataArray(
                data=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
                coords={"y": [2.5, 1.5, 0.5], "x": [0.5, 1.5, 2.5]},
            ),
            does_not_raise(),
            None,
            np.arange(9),
        ),
    ],
)
def test_vldr_spat_xy_coord_square(grid_args, darray, exp_err, exp_message, exp_vals):
    """Test the netdcf variable loader."""

    from virtual_rainforest.core.axes import vldr_spat_xy_coord_square
    from virtual_rainforest.core.grid import Grid

    grid = Grid(**grid_args)

    with exp_err as excep:
        darray = vldr_spat_xy_coord_square(darray, grid=grid)
        assert isinstance(darray, DataArray)
        assert np.allclose(darray.values, exp_vals)

    if excep is not None:
        assert str(excep.value) == exp_message
