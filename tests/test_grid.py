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

    # If AB and AC are numpy arrays that go from point A to B and point A to C
    # respectively, then they will form a ±90 deg angle if the inner product of the two
    # segments is zero.

    import numpy as np

    A = np.array(test[f"{x}-{y}"]["poly"][0])
    B = np.array(test[f"{x}-{y}"]["poly"][1])
    C = np.array(test[f"{x}-{y}"]["poly"][3])

    assert np.inner(B - A, C - A) == pytest.approx(0)


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

    # check that angle between points = 60 deg
    import numpy as np
    import numpy.linalg as LA

    a = np.array(test[f"{x}-{y}"]["poly"][0])
    b = np.array(test[f"{x}-{y}"]["poly"][1])
    c = np.array(test[f"{x}-{y}"]["poly"][3])

    inner = np.inner(a - b, a - c)
    norms = LA.norm(a - b) * LA.norm(a - c)

    cos = inner / norms
    rad = np.arccos(np.clip(cos, -1.0, 1.0))
    assert np.rad2deg(rad) == pytest.approx(60)
