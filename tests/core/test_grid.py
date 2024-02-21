"""Test module for grid.py.

This module tests the functionality of grid.py
"""

import json
from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO

import numpy as np
import numpy.linalg as LA
import pytest
from hypothesis import given, settings
from hypothesis.strategies import integers
from scipy.spatial.distance import euclidean  # type: ignore
from virtual_ecosystem.core.exceptions import ConfigurationError

from tests.conftest import log_check

# Local constants
# 10000 m2 hex: apothem = 53.73 m, side = 62.04 m
hxA = 10000
hxs = np.sqrt(hxA / (1.5 * np.sqrt(3)))
hxa = hxA / (3 * hxs)


@settings(deadline=None)
@given(integers(min_value=0, max_value=99))
def test_make_square_grid(cell_id):
    """Test make_square_grid()."""

    from virtual_ecosystem.core.grid import make_square_grid

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


@settings(deadline=None)
@given(integers(min_value=0, max_value=99))
def test_make_hex_grid(cell_id):
    """Test make_hex_grid()."""

    from virtual_ecosystem.core.grid import make_hex_grid

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


@pytest.mark.parametrize(
    argnames=["grid_type", "excep_type", "message"],
    argvalues=[
        ("penrose", ValueError, "The grid_type penrose is not defined."),
        (
            "square",
            ValueError,
            "The square creator function generated ids and polygons of unequal length.",
        ),
    ],
)
def test_grid_exceptions(mocker, grid_type, excep_type, message):
    """Test Grid init exceptions."""

    from virtual_ecosystem.core.grid import Grid

    # Mock the registered 'square' creator with something that returns unequal length
    # ids and polygons tuples.
    mocker.patch.dict(
        "virtual_ecosystem.core.grid.GRID_REGISTRY",
        {"square": lambda *args, **kwargs: ((1, 2, 3, 4), ("poly", "poly", "poly"))},
    )

    with pytest.raises(excep_type) as err:
        Grid(grid_type=grid_type)

    assert str(err.value) == message


@pytest.mark.parametrize(
    argnames=["grid_type", "exp_centroids", "exp_n_cells", "exp_bounds"],
    argvalues=[
        (
            "square",
            [
                [
                    [50, 250],
                    [150, 250],
                    [250, 250],
                    [50, 150],
                    [150, 150],
                    [250, 150],
                    [50, 50],
                    [150, 50],
                    [250, 50],
                ],
            ],
            9,
            (0, 0, 300, 300),
        ),
        (
            "hexagon",
            [
                [
                    [hxa, hxs * 4],
                    [hxa * 3, hxs * 4],
                    [hxa * 5, hxs * 4],
                    [hxa * 2, hxs * 2.5],
                    [hxa * 4, hxs * 2.5],
                    [hxa * 6, hxs * 2.5],
                    [hxa, hxs],
                    [hxa * 3, hxs],
                    [hxa * 5, hxs],
                ],
            ],
            9,
            (0, 0, hxa * 7, hxs * 5),
        ),
    ],
)
def test_grid_properties(grid_type, exp_centroids, exp_n_cells, exp_bounds):
    """Test properties calculated within Grid.__init__.

    Most properties are calculated by the individual grid type creator, not by the Grid
    __init__ argument itself. Those few ones are tested here.
    """

    from virtual_ecosystem.core.grid import Grid

    grid = Grid(grid_type=grid_type, cell_nx=3, cell_ny=3)

    assert np.allclose(grid.centroids, exp_centroids)
    assert grid.n_cells == exp_n_cells
    assert np.allclose(grid.bounds, exp_bounds)


@pytest.mark.parametrize(
    argnames=["config", "expected_err", "expected_log"],
    argvalues=[
        pytest.param(
            {
                "core": {
                    "grid": {
                        "grid_type": "square",
                        "cell_area": 100,
                        "cell_nx": 10,
                        "cell_ny": 10,
                        "xoff": 0,
                        "yoff": 0,
                    }
                }
            },
            does_not_raise(),
            ((INFO, "Grid created from configuration."),),
            id="good_square",
        ),
        pytest.param(
            {
                "core": {
                    "grid": {
                        "grid_type": "hexagon",
                        "cell_area": 100,
                        "cell_nx": 10,
                        "cell_ny": 10,
                        "xoff": 0,
                        "yoff": 0,
                    }
                }
            },
            does_not_raise(),
            ((INFO, "Grid created from configuration."),),
            id="good_hex",
        ),
        pytest.param(
            {
                "core": {
                    "grid": {
                        "grid_type": "penrose",
                        "cell_area": 100,
                        "cell_nx": 10,
                        "cell_ny": 10,
                        "xoff": 0,
                        "yoff": 0,
                    }
                }
            },
            pytest.raises(ConfigurationError),
            (
                (ERROR, "The grid_type penrose is not defined."),
                (CRITICAL, "Grid creation from configuration failed."),
            ),
            id="fail_unknown_grid",
        ),
    ],
)
def test_grid_from_config(caplog, config, expected_err, expected_log):
    """Test the creation of a Grid object using the from_config factory method.

    NOTE: this does not use an actual Config object, just a dictionary
    """

    from virtual_ecosystem.core.grid import Grid

    with expected_err:
        _ = Grid.from_config(config)

    log_check(caplog, expected_log)


@pytest.mark.parametrize(argnames=["preset_distances"], argvalues=[(True,), (False,)])
@pytest.mark.parametrize(
    argnames=["grid_type", "cfrom", "cto"],
    argvalues=[
        ("square", None, None),
        ("square", None, 99),
        ("square", None, [0, 9, 90, 99]),
        ("square", 99, None),
        ("square", [0, 9, 90, 99], None),
        ("square", 0, 99),
        ("square", [0, 9, 90, 99], 99),
        ("square", 0, [44, 45, 54, 55]),
        ("square", [0, 9, 90, 99], [44, 45, 54, 55]),
        ("hexagon", None, None),
        ("hexagon", None, 99),
        ("hexagon", None, [0, 9, 90, 99]),
        ("hexagon", 99, None),
        ("hexagon", [0, 9, 90, 99], None),
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

    from virtual_ecosystem.core.grid import Grid

    grid = Grid(grid_type=grid_type, cell_area=100)

    if preset_distances:
        grid.populate_distances()

    res = grid.get_distances(cfrom, cto)

    # Handle cfrom and cto argument types
    if cfrom is None:
        cfrom = np.arange(grid.n_cells)

    if cto is None:
        cto = np.arange(grid.n_cells)

    cfrom = [cfrom] if isinstance(cfrom, int) else cfrom
    cto = [cto] if isinstance(cto, int) else cto

    # calculate expected naively and slowly
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
            100,
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
            100 * 2**0.5,
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
            110,
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

    from virtual_ecosystem.core.grid import Grid

    grid = Grid(grid_type, cell_nx=3, cell_ny=3)
    grid.set_neighbours(distance=distance)

    for idx in range(grid.n_cells):
        assert np.allclose(grid.neighbours[idx], expected[idx])


def test_grid_dumps():
    """Test some basic properties of a dumped GeoJSON grid."""

    from virtual_ecosystem.core.grid import Grid

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


@pytest.mark.parametrize(
    argnames=["x_coord", "y_coord", "exp_exception", "exp_message", "exp_map"],
    argvalues=[
        (
            [0, 1, 2],
            [[0, 1], [0, 1]],
            pytest.raises(ValueError),
            "The x/y coordinate arrays are not 1 dimensional",
            None,
        ),
        (
            [0, 1, 2],
            [0, 1],
            pytest.raises(ValueError),
            "The x/y coordinates are of unequal length",
            None,
        ),
        (
            [0, 1, 2],
            [0, 1, 2],
            does_not_raise(),
            None,
            [[], [], []],
        ),
        (
            [500000, 500100, 500200],
            [200000, 200100, 200200],
            does_not_raise(),
            None,
            [[90], [80, 81, 90, 91], [71, 72, 81, 82]],
        ),
        (
            [500050, 500150, 500250],
            [200050, 200150, 200250],
            does_not_raise(),
            None,
            [[90], [81], [72]],
        ),
    ],
)
def test_map_xy_to_cell_ids(
    fixture_square_grid, x_coord, y_coord, exp_exception, exp_message, exp_map
):
    """Test coordinate checking.

    Tests the failure modes of coordinate mapping, along with return value on success.
    """

    with exp_exception as excep:
        cell_map = fixture_square_grid.map_xy_to_cell_id(
            np.array(x_coord), np.array(y_coord)
        )

    if exp_message is not None:
        assert str(excep.value) == exp_message

    if exp_map is not None:
        assert cell_map == exp_map


@pytest.mark.parametrize(
    argnames=[
        "x_coord",
        "y_coord",
        "x_idx",
        "y_idx",
        "exp_exception",
        "exp_message",
        "exp_idx",
    ],
    argvalues=[
        (
            np.array([0, 1, 2]),
            np.array([0, 1, 2]),
            None,
            None,
            pytest.raises(ValueError),
            "Mapped points fall outside grid.",
            None,
        ),
        (
            np.array([500000, 500100, 500200]),
            np.array([200000, 200100, 200200]),
            None,
            None,
            pytest.raises(ValueError),
            "Mapped points fall on cell boundaries.",
            None,
        ),
        (
            np.array([500050, 500150, 500250]),
            np.array([200050, 200150, 200250]),
            None,
            None,
            pytest.raises(ValueError),
            "Mapped points do not cover all cells.",
            None,
        ),
        (
            np.tile(np.arange(500050, 501000, 100), 10),
            np.repeat(np.arange(200950, 200000, -100), 10),
            None,
            None,
            does_not_raise(),
            None,
            tuple([np.arange(100), np.arange(100)]),
        ),
        (
            np.tile(np.arange(500050, 501000, 100), 10),
            np.repeat(np.arange(200950, 200000, -100), 10),
            np.arange(50),
            np.arange(50),
            pytest.raises(ValueError),
            "Dimensions of x/y indices do not match coordinates",
            None,
        ),
        (
            np.tile(np.arange(500050, 501000, 100), 10),
            np.repeat(np.arange(200950, 200000, -100), 10),
            np.arange(50),
            None,
            pytest.raises(ValueError),
            "Only one of x/y indices provided.",
            None,
        ),
        (
            np.tile(np.arange(500050, 501000, 100), 10),
            np.repeat(np.arange(200950, 200000, -100), 10),
            np.arange(100),
            np.arange(100),
            does_not_raise(),
            None,
            tuple([np.arange(100), np.arange(100)]),
        ),
        (
            np.concatenate([np.tile(np.arange(500050, 501000, 100), 10), [500050]]),
            np.concatenate([np.repeat(np.arange(200950, 200000, -100), 10), [200050]]),
            None,
            None,
            pytest.raises(ValueError),
            "Some cells contain more than one point.",
            None,
        ),
        (  # Grid covers but extends outside cells and strict = True
            np.tile(np.arange(500050, 501000, 100), 11),
            np.repeat(np.arange(200950, 199900, -100), 10),
            None,
            None,
            pytest.raises(ValueError),
            "Mapped points fall outside grid.",
            None,
        ),
    ],
)
def test_map_xy_to_cell_indexing(
    fixture_square_grid,
    x_coord,
    x_idx,
    y_idx,
    y_coord,
    exp_exception,
    exp_message,
    exp_idx,
):
    """Test coordinate checking.

    Tests the failure modes of coordinate mapping, along with return value on success.
    """

    with exp_exception as excep:
        x_idx, y_idx = fixture_square_grid.map_xy_to_cell_indexing(
            x_coord, y_coord, x_idx, y_idx
        )

    if exp_message is not None:
        assert str(excep.value) == exp_message

    if exp_idx is not None:
        assert np.allclose(exp_idx[0], x_idx)
        assert np.allclose(exp_idx[1], y_idx)


@pytest.mark.parametrize(
    argnames=["x_coord", "y_coord", "x_idx", "y_idx", "exp_x", "exp_y"],
    argvalues=[
        (
            np.array([1, 2, 1, 2]),
            np.array([2, 2, 1, 1]),
            None,
            None,
            np.array([0, 1, 2, 3]),
            np.array([0, 1, 2, 3]),
        ),
        (
            np.array([1, 2, 1, 2]),
            np.array([2, 2, 1, 1]),
            np.array([0, 1, 0, 1]),
            np.array([0, 0, 1, 1]),
            np.array([0, 1, 0, 1]),
            np.array([0, 0, 1, 1]),
        ),
    ],
)
def test_map_xy_to_cell_indexing_return(
    fixture_square_grid_simple, x_coord, y_coord, x_idx, y_idx, exp_x, exp_y
):
    """Test xy to cell id index return values.

    Uses a simple grid with easier to track return values
    """

    x_idx, y_idx = fixture_square_grid_simple.map_xy_to_cell_indexing(
        x_coord, y_coord, x_idx, y_idx
    )

    assert np.allclose(exp_x, x_idx)
    assert np.allclose(exp_y, y_idx)
