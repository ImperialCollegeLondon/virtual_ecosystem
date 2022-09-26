"""Test data loading and validation."""

import os
from contextlib import contextmanager
from typing import Generator

import pytest
from xarray import load_dataset


@contextmanager
def does_not_raise() -> Generator:
    """Handle inputs that do not raise exceptions in context managers.

    The pytest structure of `with pytest.raises(ErrorType) as excep:` is a standard way
    of testing for expected errors. With parameterised tests, the expected error (e.g.
    `pytest.raises(ValueError)`) can be passed in as a parameter. _This_ function
    provides a parameter value that behaves as a similar context manager for inputs
    that do _not_ raise an exception, so that passing and failing inputs can be used in
    the same test.

    Note that the output of str(does_not_raise) is 'None'.
    """

    # TODO - look at sharing does_not_raise() - and probably other helpers - across test
    #        files: see https://stackoverflow.com/questions/33508060/

    yield


@pytest.fixture
def fixture_square_grid():
    """Create a square grid fixture.

    A 10 x 10 grid of 1 hectare cells, with non-zero origin.
    """

    # TODO - can't type the return  value without a top level import of Grid
    from virtual_rainforest.core.grid import Grid

    grid = Grid(
        grid_type="square",
        cell_area=10000,
        cell_nx=10,
        cell_ny=10,
        xoff=500000,
        yoff=200000,
    )

    return grid


@pytest.mark.parametrize(
    argnames=["x_coord", "y_coord", "exp_exception", "exp_message"],
    argvalues=[
        (
            [0, 1, 2],
            [0, 1],
            pytest.raises(ValueError),
            "The x and y coordinates are of unequal length.",
        ),
        (
            [0, 1, 2],
            [0, 1, 2],
            pytest.raises(ValueError),
            "Data coordinates do not align with grid coordinates.",
        ),
        (
            [500000, 500100, 500200],
            [200000, 200100, 200200],
            pytest.raises(ValueError),
            "Data coordinates fall on cell edges: use cell centre coordinates in data.",
        ),
        (
            [500050, 500150, 500250],
            [200050, 200150, 200250],
            does_not_raise(),
            "None",
        ),
    ],
)
def test_check_coordinates_in_grid(
    fixture_square_grid, x_coord, y_coord, exp_exception, exp_message
):
    """Test coordinate checking.

    Tests the failure modes of coordinate checking, along with return value on success.
    """
    from virtual_rainforest.core.data import check_coordinates_in_grid

    with exp_exception as excep:

        check_coordinates_in_grid(fixture_square_grid, x_coord, y_coord)

        assert str(excep) == exp_message


@pytest.mark.parametrize(
    argnames=["filename", "expected_outcome", "expected_outcome_msg"],
    argvalues=[
        ("two_dim_xy.nc", does_not_raise(), "None"),
        (
            "two_dim_xy_6by10.nc",
            pytest.raises(ValueError),
            "Data xy dimensions do not match grid",
        ),
        (
            "two_dim_xy_lowx.nc",
            pytest.raises(ValueError),
            "Data coordinates do not align with grid coordinates.",
        ),
        ("two_dim_idx.nc", does_not_raise(), "None"),
        (
            "two_dim_idx_6by10.nc",
            pytest.raises(ValueError),
            "Data xy dimensions do not match grid",
        ),
        ("one_dim_cellid.nc", does_not_raise(), "None"),
        (
            "one_dim_cellid_lown.nc",
            pytest.raises(ValueError),
            "Grid defines 100 cells, data provides 60",
        ),
        ("one_dim_points_xy.nc", does_not_raise(), "None"),
        (
            "one_dim_points_xy_xney.nc",
            pytest.raises(ValueError),
            "The cell_ids in the data do not match grid cell ids.",
        ),
        (
            "one_dim_cellid_badid.nc",
            pytest.raises(ValueError),
            "The x and y data have different dimensions",
        ),
        ("one_dim_points_order_only.nc", does_not_raise(), "None"),
    ],
    ids=[
        "two_dim_xy",
        "two_dim_xy_6by10",
        "two_dim_xy_lowx",
        "two_dim_idx",
        "two_dim_idx_6by10",
        "one_dim_cellid",
        "one_dim_cellid_lown",
        "one_dim_cellid_badid",
        "one_dim_points_xy",
        "one_dim_points_xy_xney",
        "one_dim_points_order_only",
    ],
)
def test_map_dataset_onto_square_grid(
    fixture_square_grid, datadir, filename, expected_outcome, expected_outcome_msg
):
    """Test ability to map NetCDF files.

    The test parameters include both passing and failing files, stored in test_data.
    """
    from virtual_rainforest.core.data import map_dataset_onto_square_grid

    datafile = os.path.join(datadir, filename)
    dataset = load_dataset(datafile)

    with expected_outcome as outcome:

        map_dataset_onto_square_grid(fixture_square_grid, dataset)

        assert str(outcome) == expected_outcome_msg
