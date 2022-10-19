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

import json

import numpy as np
import numpy.linalg as LA
import pytest
from hypothesis import given, settings
from hypothesis.strategies import integers
from scipy.spatial.distance import euclidean  # type: ignore


@settings(deadline=None)
@given(integers(min_value=0, max_value=99))
def test_make_square_grid(cell_id):
    """Test make_square_grid()."""

    from virtual_rainforest.core.grid import make_square_grid

    cids, cpolys = make_square_grid(cell_area=100, cell_nx=10, cell_ny=10)

    # check if correct number of cells were created
    assert len(cids) == 100

    # check number of vertices in outer ring is correct
    xy = np.array(cpolys[cell_id].exterior.coords)
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


@given(integers(min_value=0, max_value=99))
def test_make_hex_grid(cell_id):
    """Test make_hex_grid()."""

    from virtual_rainforest.core.grid import make_hex_grid

    cids, cpolys = make_hex_grid(cell_area=100, cell_nx=10, cell_ny=10)

    # check if correct number of points were created
    assert len(cids) == 100

    # check number of vertices in outer ring is correct
    xy = np.array(cpolys[cell_id].exterior.coords)
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


@pytest.mark.parametrize(argnames=["preset_distances"], argvalues=[(True,), (False,)])
@pytest.mark.parametrize(
    argnames=["grid_type", "cfrom", "cto"],
    argvalues=[
        ("square", 0, 99),
        ("square", [0, 9, 90, 99], 99),
        ("square", 0, [44, 45, 54, 55]),
        ("square", [0, 9, 90, 99], [44, 45, 54, 55]),
        ("hexagon", 0, 99),
        ("hexagon", [0, 9, 90, 99], 99),
        ("hexagon", 0, [44, 45, 54, 55]),
        ("hexagon", [0, 9, 90, 99], [44, 45, 54, 55]),
    ],
)
def test_get_distances(preset_distances, grid_type, cfrom, cto):
    """Test grid.get_distances().

    This is essentially comparing two very similar implementations, which is a test of
    sorts, but not as independent as it could be. It would be very tedious to hard code
    the expected values, but that would give more robustness.
    """

    from virtual_rainforest.core.grid import Grid

    grid = Grid(grid_type=grid_type, cell_area=100)

    if preset_distances:
        grid.populate_distances()

    res = grid.get_distances(cfrom, cto)

    # calculate expected naively and slowly
    cfrom = [cfrom] if isinstance(cfrom, int) else cfrom
    cto = [cto] if isinstance(cto, int) else cto
    expected = np.ndarray((len(cfrom), len(cto)))

    assert res.shape == expected.shape

    for x_idx, ff in enumerate(cfrom):
        for y_idx, tt in enumerate(cto):
            exp = np.sqrt(np.sum((grid.centroids[ff] - grid.centroids[tt]) ** 2))
            expected[x_idx, y_idx] = exp

    assert np.allclose(res, expected)


@pytest.mark.parametrize(
    argnames=["grid_type", "distance", "expected"],
    argvalues=[
        (
            "square",
            10,
            [
                [0, 1, 3],
                [0, 1, 2, 4],
                [1, 2, 5],
                [0, 3, 4, 6],
                [1, 3, 4, 5, 7],
                [2, 4, 5, 8],
                [3, 6, 7],
                [4, 6, 7, 8],
                [5, 7, 8],
            ],
        ),
        (
            "square",
            10 * 2**0.5,
            [
                [0, 1, 3, 4],
                [0, 1, 2, 3, 4, 5],
                [1, 2, 4, 5],
                [0, 1, 3, 4, 6, 7],
                [0, 1, 2, 3, 4, 5, 6, 7, 8],
                [1, 2, 4, 5, 7, 8],
                [3, 4, 6, 7],
                [3, 4, 5, 6, 7, 8],
                [4, 5, 7, 8],
            ],
        ),
        (
            "hexagon",
            11,
            [
                [0, 1, 3],
                [0, 1, 2, 3, 4],
                [1, 2, 4, 5],
                [0, 1, 3, 4, 6, 7],
                [1, 2, 3, 4, 5, 7, 8],
                [2, 4, 5, 8],
                [3, 6, 7],
                [3, 4, 6, 7, 8],
                [4, 5, 7, 8],
            ],
        ),
    ],
)
def test_set_neighbours(grid_type, distance, expected):
    """Test the neighbourhood methods.

    Uses small grids and hand-derived neighbourhood lists.
    """

    from virtual_rainforest.core.grid import Grid

    grid = Grid(grid_type, cell_nx=3, cell_ny=3)
    grid.set_neighbours(distance=distance)

    for idx in range(grid.n_cells):
        assert np.allclose(grid.neighbours[idx], expected[idx])


def test_grid_dumps():
    """Test some basic properties of a dumped GeoJSON grid."""

    from virtual_rainforest.core.grid import Grid

    grid = Grid()
    geojson = grid.dumps()

    try:
        parsed = json.loads(geojson)
    except json.JSONDecodeError as exc:
        assert False, f"JSON load failed. {exc}"

    type = parsed.get("type")
    assert type is not None and type == "FeatureCollection"

    features = parsed.get("features")
    assert features is not None and len(features) == 100
