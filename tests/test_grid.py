import pytest
from scipy.spatial.distance import euclidean

from virtual_rainforest.core.grid import CoreGrid, CoreGridConfig


def test_CoreGridConfig():
    """test to Configure the `core.grid` module

    This data class is used to setup the arrangement of grid cells to be used in
    running a `virtual_rainforest` simulation.

    Attrs:
        grid_type:
        cell_contiguity:
        cell_area:
        cell_nx:
        cell_ny:
    """
    obj_1 = CoreGridConfig()
    assert obj_1.grid_type == "square"
    assert obj_1.cell_contiguity == "rook"
    assert obj_1.cell_area == 100
    assert obj_1.cell_nx == 10
    assert obj_1.cell_ny == 10


def test_make_square_grid():
    """test Create a square grid by comparing eucledian distance between corner points

    Args:
        cell_area:
        cell_nx:
        cell_ny:
    """
    test = CoreGrid._make_square_grid(100, 10, 10)
    distance = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][1])
    distance2 = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][3])
    assert distance == distance2


def test_make_hex_grid():
    """test Create a hex grid by comparing eucledian distance between corner points

    Args:
        cell_area:
        cell_nx:
        cell_ny:
    """
    test = CoreGrid._make_hex_grid(100, 10, 10)
    distance = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][1])
    distance2 = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][3])
    distance == pytest.approx(2 * distance2)
