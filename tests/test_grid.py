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
from hypothesis import given, settings
from hypothesis.strategies import integers


def test_CoreGridConfig():
    """Test if CoreGridConfig().

    Check if function created an object with default values for the following
    properties: grid_type, cell_contiguity, cell_area, cell_nx, cell_ny.
    """
    from virtual_rainforest.core.grid import CoreGridConfig

    obj_1 = CoreGridConfig()
    assert obj_1.grid_type == "square"
    assert obj_1.cell_contiguity == "rook"
    assert obj_1.cell_area == 100
    assert obj_1.cell_nx == 10
    assert obj_1.cell_ny == 10


@settings(deadline=None)
@given(integers(min_value=0, max_value=9), integers(min_value=0, max_value=9))
def test_make_square_grid(x, y):
    """Test make_square_grid()."""
    from scipy.spatial.distance import euclidean  # type: ignore

    from virtual_rainforest.core.grid import CoreGrid

    test = CoreGrid._make_square_grid(100, 10, 10)

    # check if correct number of points were created
    assert len(test.keys()) == 100

    # check distance between corner points is the same
    distance = euclidean(test[f"{x}-{y}"]["poly"][0], test[f"{x}-{y}"]["poly"][2])
    distance2 = euclidean(test[f"{x}-{y}"]["poly"][1], test[f"{x}-{y}"]["poly"][3])
    assert distance == pytest.approx(distance2)

    # check angle between corner points is the same
    from math import atan2, degrees, pi

    def angle(A, B, C, /):
        Ax, Ay = A[0] - B[0], A[1] - B[1]
        Cx, Cy = C[0] - B[0], C[1] - B[1]
        a = atan2(Ay, Ax)
        c = atan2(Cy, Cx)
        if a < 0:
            a += pi * 2
        if c < 0:
            c += pi * 2
        return (pi * 2 + c - a) if a > c else (c - a)

    point1 = test[f"{x}-{y}"]["poly"][0]
    point2 = test[f"{x}-{y}"]["poly"][1]
    point3 = test[f"{x}-{y}"]["poly"][2]
    point4 = test[f"{x}-{y}"]["poly"][3]

    angle1 = angle(point1, point2, point3)
    angle2 = angle(point2, point3, point4)

    assert degrees(angle1) == pytest.approx(90)
    assert angle1 == pytest.approx(angle2)


@given(integers(min_value=0, max_value=9), integers(min_value=0, max_value=9))
def test_make_hex_grid(x, y):
    """Test make_hex_grid()."""
    from scipy.spatial.distance import euclidean  # type: ignore

    from virtual_rainforest.core.grid import CoreGrid

    test = CoreGrid._make_hex_grid(100, 10, 10)

    # check if correct number of points were created
    assert len(test.keys()) == 100

    # check distance between corner points is the same
    distance = euclidean(test[f"{x}-{y}"]["poly"][0], test[f"{x}-{y}"]["poly"][3])
    distance2 = euclidean(test[f"{x}-{y}"]["poly"][1], test[f"{x}-{y}"]["poly"][4])
    distance3 = euclidean(test[f"{x}-{y}"]["poly"][2], test[f"{x}-{y}"]["poly"][5])
    assert distance == pytest.approx(distance2)
    assert distance == pytest.approx(distance3)

    # check that angle between points = 120 deg
    # (this works but is a bit long)
    from math import atan2, degrees, pi

    def angle(A, B, C, /):
        Ax, Ay = A[0] - B[0], A[1] - B[1]
        Cx, Cy = C[0] - B[0], C[1] - B[1]
        a = atan2(Ay, Ax)
        c = atan2(Cy, Cx)
        if a < 0:
            a += pi * 2
        if c < 0:
            c += pi * 2
        return (pi * 2 + c - a) if a > c else (c - a)

    point1 = test[f"{x}-{y}"]["poly"][0]
    point2 = test[f"{x}-{y}"]["poly"][1]
    point3 = test[f"{x}-{y}"]["poly"][2]
    point4 = test[f"{x}-{y}"]["poly"][3]
    point5 = test[f"{x}-{y}"]["poly"][4]
    point6 = test[f"{x}-{y}"]["poly"][5]

    angle1 = angle(point1, point2, point3)
    angle2 = angle(point2, point3, point4)
    angle3 = angle(point3, point4, point5)
    angle4 = angle(point4, point5, point6)

    assert degrees(angle1) == pytest.approx(120)
    assert angle1 == pytest.approx(angle2)
    assert angle1 == pytest.approx(angle3)
    assert angle1 == pytest.approx(angle4)
