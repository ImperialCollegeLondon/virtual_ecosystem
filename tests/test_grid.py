"""Test module for grid.py.

NAME
test_grid.py

DESCRIPTION
This module tests the following functions from grid.py:

- class CoreGridConfig:
    Configure the `core.grid` module.
    This data class is used to setup the arrangement of grid cells to be used in
    running a `virtual_rainforest` simulation.

- CoreGrid._make_square_grid(cell_area: float, cell_nx: int, cell_ny: int) -> dict:
    Create a square grid.

- CoreGrid._make_hex_grid(cell_area: float, cell_nx: int, cell_ny: int) -> dict:
    Create a hexagonal grid.

- TODO CoreGrid.export geojson
    Export grid system as geojson file.
    outfile: A self.cell_dict returned by a make_square_grid or make_hex_grid call.

- TODO Once it is extracted from where it is, _feature.

"""

import pytest


def test_CoreGridConfig():
    """Test if CoreGridConfig().

    Check if function created an object with properties: grid_type,
    cell_contiguity, cell_area, cell_nx, cell_ny.
    """
    from virtual_rainforest.core.grid import CoreGridConfig

    obj_1 = CoreGridConfig()
    assert obj_1.grid_type == "square"
    assert obj_1.cell_contiguity == "rook"
    assert obj_1.cell_area == 100
    assert obj_1.cell_nx == 10
    assert obj_1.cell_ny == 10


def test_make_square_grid():
    """Test _make_square_grid()."""
    from scipy.spatial.distance import euclidean  # type: ignore

    from virtual_rainforest.core.grid import CoreGrid

    test = CoreGrid._make_square_grid(100, 10, 10)

    # TODO check if correct number of points were created

    # TODO check that distance between neighboring points is euqal for all integers
    distance = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][1])
    distance2 = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][3])
    assert distance == distance2
    # TODO check that angle between points = 90 deg


def test_make_hex_grid():
    """Test _make_hex_grid()."""
    from scipy.spatial.distance import euclidean  # type: ignore

    from virtual_rainforest.core.grid import CoreGrid

    # TODO check if correct number of points were created
    # TODO check that distance between neighboring points is euqal for all integers
    test = CoreGrid._make_hex_grid(100, 10, 10)
    distance = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][1])
    distance2 = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][3])
    distance == pytest.approx(2 * distance2)
    # TODO check that angle between points = 120 deg
