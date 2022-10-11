"""Test module for grid.py.

NAME
test_grid.py

DESCRIPTION
This module tests the following functions from grid.py:

- grid.make_square_grid
    Create a square grid.

- grid.make_hex_grid
    Create a hexagonal grid.

- TODO The grid.Grid class.

- TODO grid.Grid.dump and grid.Grid.dumps for0 geojson

"""

import numpy as np
import numpy.linalg as LA
import pytest
from hypothesis import given, settings
from hypothesis.strategies import integers
from scipy.spatial.distance import euclidean  # type: ignore


@settings(deadline=None)
@given(integers(min_value=0, max_value=9), integers(min_value=0, max_value=9))
def test_make_square_grid(x, y):
    """Test make_square_grid()."""

    from virtual_rainforest.core.grid import make_square_grid

    test = make_square_grid(cell_area=100, cell_nx=10, cell_ny=10)

    # check if correct number of cells were created
    assert len(test.keys()) == 100

    # check number of vertices in outer ring is correct
    xy = np.array(test[f"{x}-{y}"].exterior.coords)
    assert xy.shape == (5, 2)

    # check that distance between corner points is the same
    distance = euclidean(xy[0], xy[2])
    distance2 = euclidean(xy[1], xy[3])

    np.testing.assert_allclose(distance, distance2)

    # If AB and AC are numpy arrays that go from point A to B and point A to C
    # respectively, then they will form a ±90 deg angle if the inner product of the two
    # segments is zero.

    iprod = np.inner(xy[1] - xy[0], xy[3] - xy[0])
    assert iprod == pytest.approx(0)


@given(integers(min_value=0, max_value=9), integers(min_value=0, max_value=9))
def test_make_hex_grid(x, y):
    """Test make_hex_grid()."""

    from virtual_rainforest.core.grid import make_hex_grid

    test = make_hex_grid(cell_area=100, cell_nx=10, cell_ny=10)

    # check if correct number of points were created
    assert len(test.keys()) == 100

    # check number of vertices in outer ring is correct
    xy = np.array(test[f"{x}-{y}"].exterior.coords)
    assert xy.shape == (7, 2)

    # check that distance between corner points is the same
    distance = euclidean(xy[0], xy[3])
    distance2 = euclidean(xy[1], xy[4])
    distance3 = euclidean(xy[2], xy[5])
    np.testing.assert_allclose(distance, distance2, distance3)

    # check that angle between points = 60 deg
    inner = np.inner(xy[0] - xy[1], xy[0] - xy[3])
    norms = LA.norm(xy[0] - xy[1]) * LA.norm(xy[0] - xy[3])

    cos = inner / norms
    rad = np.arccos(np.clip(cos, -1.0, 1.0))
    assert np.rad2deg(rad) == pytest.approx(60)
