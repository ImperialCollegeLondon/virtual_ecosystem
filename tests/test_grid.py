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

    # check if correct number of points were created
    assert len(test.keys()) == 100

    # check that distance between neighboring points is euqal for all integers
    # (this works but is a bit long)
    for x in range(9):
        for y in range(9):
            distance = euclidean(
                test[f"{x}-{y}"]["poly"][0], test[f"{x}-{y}"]["poly"][2]
            )
            distance2 = euclidean(
                test[f"{x}-{y}"]["poly"][1], test[f"{x}-{y}"]["poly"][3]
            )
            assert distance == pytest.approx(distance2)
    # TODO check that angle between points = 90 deg


def test_make_hex_grid():
    """Test _make_hex_grid()."""
    from scipy.spatial.distance import euclidean  # type: ignore

    from virtual_rainforest.core.grid import CoreGrid

    test = CoreGrid._make_hex_grid(100, 10, 10)

    # check if correct number of points were created
    assert len(test.keys()) == 100

    # check that distance between neighboring points is euqal for all integers
    # (this works but is a bit long)
    for x in range(9):
        for y in range(9):
            distance = euclidean(
                test[f"{x}-{y}"]["poly"][0], test[f"{x}-{y}"]["poly"][3]
            )
            distance2 = euclidean(
                test[f"{x}-{y}"]["poly"][1], test[f"{x}-{y}"]["poly"][4]
            )
            distance3 = euclidean(
                test[f"{x}-{y}"]["poly"][2], test[f"{x}-{y}"]["poly"][5]
            )
            assert distance == pytest.approx(distance2)
            assert distance == pytest.approx(distance3)

    # TODO check that angle between points = 120 deg
