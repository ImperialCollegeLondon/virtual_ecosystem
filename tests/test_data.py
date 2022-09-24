"""Test data loading and validation."""

from contextlib import contextmanager

import pytest

# TODO - look at sharing does_not_raise() - and probably other helpers - across test
#        files: see https://stackoverflow.com/questions/33508060/


@contextmanager
def does_not_raise():
    """Handle inputs that do not raise exceptions in context managers.

    The common structure of `with pytest.raises() as excep:` is really useful for
    setting up paramaterised tests of failure modes. This function behaves as a similar
    context manager for inputs that do _not_ raise an exception, so that passing and
    failing inputs can be used in the same test.
    """

    yield


@pytest.fixture
def fixture_square_grid():
    """Create a square grid fixture.

    A 10 x 10 grid of 1 hectare cells, with non-zero origin.
    """

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
