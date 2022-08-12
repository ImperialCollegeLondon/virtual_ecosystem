"""Test module for grid.py.

NAME
test_grid.py

DESCRIPTION
This module tests the following functions from grid.py:
- CoreGridConfig()
- CoreGrid._make_square_grid(cell_area: float, cell_nx: int, cell_ny: int) -> dict:
- CoreGrid._make_hex_grid(cell_area: float, cell_nx: int, cell_ny: int) -> dict:
"""

import pytest


def test_CoreGridConfig():
    """Test CoreGridConfig()."""
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
    distance = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][1])
    distance2 = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][3])
    assert distance == distance2


def test_make_hex_grid():
    """Test _make_hex_grid()."""
    from scipy.spatial.distance import euclidean  # type: ignore

    from virtual_rainforest.core.grid import CoreGrid

    test = CoreGrid._make_hex_grid(100, 10, 10)
    distance = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][1])
    distance2 = euclidean(test["0-0"]["poly"][0], test["0-0"]["poly"][3])
    distance == pytest.approx(2 * distance2)
