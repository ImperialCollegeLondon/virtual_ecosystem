"""Collection of fixtures to assist the testing scripts."""
from typing import Any

import pytest
from xarray import DataArray

# An import of LOGGER is required for INFO logging events to be visible to tests
# This can be removed as soon as a script that imports logger is imported
import virtual_rainforest.core.logger  # noqa


def log_check(caplog: pytest.LogCaptureFixture, expected_log: tuple[tuple]) -> None:
    """Helper function to check that the captured log is as expected.

    Arguments:
        caplog: An instance of the caplog fixture
        expected_log: An iterable of 2-tuples containing the
            log level and message.
    """

    assert len(expected_log) == len(caplog.records)

    assert all(
        [exp[0] == rec.levelno for exp, rec in zip(expected_log, caplog.records)]
    )
    assert all(
        [exp[1] in rec.message for exp, rec in zip(expected_log, caplog.records)]
    )


# Shared fixtures


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


@pytest.fixture
def fixture_square_grid_simple():
    """Create a square grid fixture.

    A 2 x 2 grid centred on x=1,1,2,2 y=1,2,1,2
    """

    from virtual_rainforest.core.grid import Grid

    grid = Grid(
        grid_type="square",
        cell_area=1,
        cell_nx=2,
        cell_ny=2,
        xoff=0.5,
        yoff=0.5,
    )

    return grid


@pytest.fixture
def fixture_data(fixture_square_grid_simple):
    """A Data instance fixture for use in testing."""

    from virtual_rainforest.core.data import Data

    data = Data(fixture_square_grid_simple)

    # Create an existing variable to test replacement
    data["existing_var"] = DataArray([1, 2, 3, 4], dims=("cell_id",))

    return data


@pytest.fixture
def data_instance():
    """Creates an empty data instance."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid

    grid = Grid()
    return Data(grid)


@pytest.fixture
def new_axis_validators():
    """Create new axis validators to test methods and registration."""
    from virtual_rainforest.core.axes import AxisValidator
    from virtual_rainforest.core.grid import Grid

    # Create a new subclass.
    class TestAxis(AxisValidator):
        core_axis = "testing"
        dim_names = {"test"}

        def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
            return True if value.sum() > 10 else False

        def run_validation(
            self, value: DataArray, grid: Grid, **kwargs: Any
        ) -> DataArray:
            return value * 2

    # Create a new duplicate subclass to check mutual exclusivity test
    class TestAxis2(AxisValidator):
        core_axis = "testing"
        dim_names = {"test"}

        def can_validate(self, value: DataArray, grid: Grid, **kwargs: Any) -> bool:
            return True if value.sum() > 10 else False

        def run_validation(
            self, value: DataArray, grid: Grid, **kwargs: Any
        ) -> DataArray:
            return value * 2
