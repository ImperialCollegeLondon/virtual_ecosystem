"""The :mod:`~virtual_ecosystem.core.grid` module is used to create the grid of cells
underlying the simulation and to identify the neighbourhood connections of cells.

- set up neighbourhoods. ? store as graph (networkx - might only need a really
  lightweight graph description).
- import of geojson grids? Way to link structured landscape into cells.  Can use
  data loading methods to assign values to grids? This would be a useful way of
  defining mappings though.
- maybe look at libpysal if we end up needing more weights/spatial analysis stuff?
  https://pysal.org/libpysal/
"""  # noqa: D205

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.distance import cdist, pdist, squareform  # type: ignore
from shapely.affinity import scale, translate  # type: ignore
from shapely.geometry import GeometryCollection, Point, Polygon  # type: ignore

from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.logger import LOGGER

GRID_REGISTRY: dict[str, Callable] = {}
"""A registry for different grid geometries.

This dictionary maps grid geometry types (square, hex, etc) to a function generating a
grid of that type. Users can register their own grid types using the `register_grid`
decorator.
"""

GRID_STRUCTURE_SIG: TypeAlias = tuple[list[int], list[Polygon]]
"""Type signature of the data structure to be returned from grid creator functions.

The first value is a list of integer cell ids, the second is a matching list of the
polygons for each cell id. Although cell ids could be a numpy array, the numpy int types
then need handling in arguments and json representation.
"""


def register_grid(grid_type: str) -> Callable:
    """Add a grid type and creator function to the grid registry.

    This decorator is used to add a function creating a grid layout to the registry of
    accepted grids. The function must return a numpy array of integer polygon ids and an
    equal length list of Polygon objects, following the GRID_STRUCTURE_SIG signature.

    The grid_type argument is used to identify the grid creation function to be used by
    the Grid class and in configuration files.

    Args:
        grid_type: A name to be used to identify the grid creation function.
    """

    def decorator_register_grid(func: Callable) -> Callable:
        # Add the grid type to the registry
        if grid_type in GRID_REGISTRY:
            LOGGER.warning(
                "Grid type %s already exists and is being replaced", grid_type
            )
        GRID_REGISTRY[grid_type] = func

        return func

    return decorator_register_grid


@register_grid(grid_type="square")
def make_square_grid(
    cell_area: float,
    cell_nx: int,
    cell_ny: int,
    xoff: float = 0,
    yoff: float = 0,
) -> GRID_STRUCTURE_SIG:
    """Create a square grid.

    Args:
        cell_area: The area of each hexagon cell in m2
        cell_nx: The number of grid cells in the X direction.
        cell_ny: The number of grid cells in the Y direction.
        xoff: An offset to use for the grid origin in the X direction in metres.
        yoff: An offset to use for the grid origin in the Y direction in metres.

    Returns:
        Equal-length tuples of integer polygon ids and Polygon objects
    """

    # Create the polygon prototype object, with origin at 0,0 and area 1
    # Note coordinate order is anti-clockwise - right hand rule.
    prototype = Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])

    # Scale to requested size and origin
    scale_factor = np.sqrt(cell_area)
    prototype = scale(prototype, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    prototype = translate(prototype, xoff=xoff, yoff=yoff)

    # Get the cell ids and centres of the cells
    idx_y, idx_x = np.indices((cell_ny, cell_nx))
    cell_ids = idx_x + idx_y * cell_nx
    cell_x = idx_x * scale_factor
    cell_y = np.flipud(idx_y) * scale_factor

    # Get the list of polygons
    cell_polygon_list: list[Polygon] = [
        translate(prototype, xoff=xf, yoff=yf)
        for xf, yf in zip(cell_x.flatten(), cell_y.flatten())
    ]

    # Get list of ids
    cell_ids_list: list[int] = cell_ids.flatten().tolist()

    return cell_ids_list, cell_polygon_list


@register_grid(grid_type="hexagon")
def make_hex_grid(
    cell_area: float,
    cell_nx: int,
    cell_ny: int,
    xoff: float = 0,
    yoff: float = 0,
) -> GRID_STRUCTURE_SIG:
    """Create a hexagonal grid.

    Args:
        cell_area: The area of each hexagon cell in m2.
        cell_nx: The number of grid cells in the X direction.
        cell_ny: The number of grid cells in the Y direction.
        xoff: An offset to use for the grid origin in the X direction in metres.
        yoff: An offset to use for the grid origin in the Y direction in metres.

    Returns:
        Equal-length tuples of integer polygon ids and Polygon objects
    """

    # TODO - implement grid orientation and kwargs passing
    #        https://www.redblobgames.com/grids/hexagons/

    # Create the polygon prototype object, with origin at 0,0 and area 1
    # Note coordinate order is anti-clockwise - right hand rule
    side_length_a1 = 3 ** (1 / 4) * np.sqrt(2 / 9)
    apothem_a1 = np.sqrt(3) * side_length_a1 / 2
    prototype = Polygon(
        [
            [apothem_a1, 0],
            [2 * apothem_a1, side_length_a1 * 0.5],
            [2 * apothem_a1, side_length_a1 * 1.5],
            [apothem_a1, side_length_a1 * 2],
            [0, side_length_a1 * 1.5],
            [0, side_length_a1 * 0.5],
            [apothem_a1, 0],
        ]
    )

    # Scale to requested size and origin and get side length and apothem for translation
    # when tiling the grid
    scale_factor = np.sqrt(cell_area)
    side_length = 3 ** (1 / 4) * np.sqrt(2 * (cell_area / 9))
    apothem = np.sqrt(3) * side_length / 2
    prototype = scale(prototype, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    prototype = translate(prototype, xoff=xoff, yoff=yoff)

    # Get the cell ids and centres of the cells
    idx_y, idx_x = np.indices((cell_ny, cell_nx))
    cell_ids = idx_x + idx_y * cell_nx
    cell_x = 2 * apothem * idx_x + apothem * (idx_y % 2)
    cell_y = 1.5 * side_length * np.flipud(idx_y)

    # Get the list of polygons
    cell_polygon_list: list[Polygon] = [
        translate(prototype, xoff=xf, yoff=yf)
        for xf, yf in zip(cell_x.flatten(), cell_y.flatten())
    ]

    # Get list of ids
    cell_ids_list: list[int] = cell_ids.flatten().tolist()

    return cell_ids_list, cell_polygon_list


class Grid:
    """Define the grid of cells used in a Virtual Ecosystem simulation.

    The simulation grid used in a Virtual Ecosystem simulation is assumed to be a
    projected coordinate system with linear dimensions in metres. Grid cell sizes are
    set using their area in square metres and users can specify offsets to align a
    simulation grid to a particular projected coordinate system. However, the Virtual
    Ecosystem codebase makes no attempt to manage or validate projection information:
    we assume that users maintain a common coordinate system across inputs.

    Args:
        grid_type: The grid type to be used, which must identify a grid creation
            function in the :data:`~virtual_ecosystem.core.grid.GRID_REGISTRY`
            dictionary.
        cell_area: The area of each grid cell, in square metres.
        cell_nx: The number of cells in the grid along the x (easting) axis
        cell_ny: The number of cells in the grid along the y (northing) axis
        xoff: An offset for the grid x origin in metres
        yoff: An offset for the grid y origin in metres
    """

    def __init__(
        self,
        grid_type: str = "square",
        cell_area: float = 10000,
        cell_nx: int = 10,
        cell_ny: int = 10,
        xoff: float = 0,
        yoff: float = 0,
    ) -> None:
        # Populate the attributes
        self.grid_type = grid_type
        """The grid type used to create the instance"""
        self.cell_area = cell_area
        """The area of the grid cells"""
        self.cell_nx = cell_nx
        """The number of cells in the grid in the X dimension"""
        self.cell_ny = cell_ny
        """The number of cells in the grid in the Y dimension"""
        self.xoff = xoff
        """An offset for the cell X coordinates"""
        self.yoff = yoff
        """An offset for the cell Y coordinates"""

        self.cell_id: list[int]
        """A list of unique integer ids for each cell."""
        self.polygons: list[Polygon]
        """A list of of the cell polygon geometries, as shapely.geometry.Polygon
        objects, in cell_id order"""
        self.ncells: int
        """The total number of cells in the grid."""
        self.centroids: np.ndarray
        """A list of the centroid of each cell as shapely.geometry.Point objects, in
        cell_id order."""

        # Retrieve the creator function from the grid registry and handle unknowns
        creator = GRID_REGISTRY.get(self.grid_type, None)
        if creator is None:
            raise ValueError(f"The grid_type {self.grid_type} is not defined.")

        # Run the grid creation
        self.cell_id, self.polygons = creator(
            cell_area=self.cell_area,
            cell_nx=self.cell_nx,
            cell_ny=self.cell_ny,
            xoff=self.xoff,
            yoff=self.yoff,
        )

        if len(self.cell_id) != len(self.polygons):
            raise ValueError(
                f"The {self.grid_type} creator function generated ids and polygons of "
                "unequal length."
            )

        self.n_cells = len(self.cell_id)

        # Get the centroids as a numpy array
        centroids = [cell.centroid for cell in self.polygons]
        self.centroids = np.array([(gm.xy[0][0], gm.xy[1][0]) for gm in centroids])

        # Get the bounds as a 4 tuple
        self.bounds: GeometryCollection = GeometryCollection(self.polygons).bounds
        """A GeometryCollection providing the bounds of the cell polygons."""

        # Define other attributes set by methods
        # TODO - this might become a networkx graph
        self._neighbours: list[NDArray[np.int_]] | None = None

        # Do not by default store the full distance matrix
        self._distances: NDArray | None = None

    @property
    def neighbours(self) -> list[NDArray[np.int_]]:
        """Return the neighbours property."""

        if self._neighbours is None:
            raise AttributeError("Neighbours not yet defined: use set_neighbours.")

        return self._neighbours

    def __repr__(self) -> str:
        """Represent a CoreGrid as a string."""
        return (
            "CoreGrid("
            f"{self.grid_type}, "
            f"A={self.cell_area}, "
            f"nx={self.cell_nx}, "
            f"ny={self.cell_ny}, "
            f"n={self.n_cells}, "
            f"bounds={self.bounds})"
        )

    @classmethod
    def from_config(cls, config: Config) -> Grid:
        """Factory function to generate a Grid instance from a configuration dict.

        Args:
            config: A validated Virtual Ecosystem model configuration object.
        """

        try:
            grid = Grid(**config["core"]["grid"])
        except Exception as err:
            LOGGER.error(err)
            to_raise = ConfigurationError("Grid creation from configuration failed.")
            LOGGER.critical(to_raise)
            raise to_raise

        LOGGER.info("Grid created from configuration.")
        return grid

    def dumps(self, dp: int = 2, **kwargs: Any) -> str:
        """Export a grid as a GeoJSON string.

        The virtual_ecosystem.core.Grid object assumes an unspecified projected
        coordinate system. As a result, GeoJSON files created by this export method do
        not strictly obey the GeoJSON specification
        (https://www.rfc-editor.org/rfc/rfc7946), which requires WGS84 coordinates to
        describe locations.

        Args:
            dp: The decimal place precision for exported coordinates
            **kwargs: Arguments to json.dumps
        """

        content = self._get_geojson(dp=dp)
        return json.dumps(obj=content, **kwargs)

    def dump(self, outfile: str, dp: int = 2, **kwargs: Any) -> None:
        """Export a grid as a GeoJSON file.

        The virtual_ecosystem.core.Grid object assumes an unspecified projected
        coordinate system. As a result, GeoJSON files created by this export method do
        not strictly obey the GeoJSON specification
        (https://www.rfc-editor.org/rfc/rfc7946), which requires WGS84 coordinates to
        describe locations.

        Args:
            outfile: A path used to export GeoJSON data.
            dp: The decimal place precision for exported coordinates
            **kwargs: Arguments to json.dump
        """

        content = self._get_geojson(dp=dp)

        with open(outfile, "w") as outf:
            json.dump(obj=content, fp=outf, **kwargs)

    def _get_geojson(self, dp: int) -> dict:
        """Convert the grid to a GeoJSON structured dictionary.

        Args:
            dp: The number of decimal places to use in reporting locations
        """

        # Create the output feature list
        features = []

        for idx, poly in zip(self.cell_id, self.polygons):
            # Get the coordinates of the outer ring - we are not expecting any holes in
            # grid cell polygons - and wrap in a list to provide Polygon structure.
            coords = [np.round(poly.exterior.coords, decimals=dp).tolist()]

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coords,
                },
                "properties": {
                    "cell_id": idx,
                    "cell_cx": np.round(self.centroids[idx][0], decimals=dp),
                    "cell_cy": np.round(self.centroids[idx][1], decimals=dp),
                },
            }

            features.append(feature)

        return {"type": "FeatureCollection", "features": features}

    def set_neighbours(
        self,
        edges: bool = True,
        vertices: bool = False,
        distance: float | None = None,
    ) -> None:
        """Populate the neighbour list for a Grid object.

        This method generates a list giving the neighbours of each cell in the grid.
        The edges and vertices arguments are used to include neighbouring cells that
        share edges or vertices with a focal cell. Alternatively, a distance in metres
        from the focal cell centroid can be used to include neighbouring cells
        within that distance.

        Args:
            edges: Include cells with shared edges as neighbours.
            vertices: Include cells with shared vertices as neighbours.
            distance: A distance in metres.
        """

        # This is a lot more irritating to implement than expected. Using geometry
        # operations (as in Shapely.touches and pysal.weights.Queen/etc) turns out to be
        # unreliable for hexagon grids simply due to floating point differences. For the
        # moment, just implementing distance.

        self._neighbours = [
            np.where(self.get_distances(idx, self.cell_id) <= distance)[1]
            for idx in self.cell_id
        ]

    def get_distances(
        self,
        cell_from: int | Sequence[int] | None,
        cell_to: int | Sequence[int] | None,
    ) -> np.ndarray:
        """Calculate euclidean distances between cell centroids.

        This method returns a two dimensional np.array containing the Euclidean
        distances between two sets of cell ids.

        Args:
            cell_from: Either a single integer cell_id or a list of ids.
            cell_to: Either a single integer cell_id or a list of ids.

        Returns:
            A 2D np.array of Euclidean distances
        """

        if cell_from is None:
            _cell_from = np.arange(self.n_cells)
        else:
            _cell_from = np.array(
                [cell_from] if isinstance(cell_from, int) else cell_from
            )

        if cell_to is None:
            _cell_to = np.arange(self.n_cells)
        else:
            _cell_to = np.array([cell_to] if isinstance(cell_to, int) else cell_to)

        if self._distances is None:
            return cdist(self.centroids[_cell_from], self.centroids[_cell_to])

        return self._distances[np.ix_(_cell_from, _cell_to)]

    def populate_distances(
        self,
    ) -> None:
        """Populate the complete cell distance matrix for the grid.

        This stores the full distance matrix in the Grid instance, which is then used
        for quick lookup by the get_distance method. However for large grids, this
        requires a lot of memory, and so calculating distances on demand may be more
        reasonable.
        """

        self._distances = squareform(pdist(self.centroids))

    def map_xy_to_cell_id(
        self,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
    ) -> list[list[int]]:
        """Map a set of coordinates onto grid cells.

        This function loops over points defined by pairs of x and y coordinates and maps
        the coordinates onto the cell_ids of the grid. The method also checks to see
        that each point intersects one and only one of the cell polygons defined in the
        grid. Points that intersect no cells fall outside the grid polygons and points
        that intersect more than one cell fall ambiguously on cell borders.

        Args:
            x_coords: A numpy array of x coordinates of points that should occur within
                grid cells.
            y_coords: A similar and equal-length array providing y coordinates.

        Returns:
            A list of lists showing the cell ids that map onto each point. The list for
            a given point can be empty - when the point falls in no cell - or of length
            > 1 when a point falls on adjoining cell boundaries.
        """

        if (x_coords.ndim != 1) or (y_coords.ndim != 1):
            raise ValueError("The x/y coordinate arrays are not 1 dimensional")

        if x_coords.shape != y_coords.shape:
            raise ValueError("The x/y coordinates are of unequal length")

        # Get shapely points for the coordinates
        xyp = [Point(x, y) for x, y in zip(x_coords, y_coords)]

        # Map the Cell ID of each point - this is doing all pairs of points and cells,
        # which is a computational choke point. Might be able to use a spatial search
        # option, if this gets problematic, possibly including an STRTree in the grid
        #    object https://shapely.readthedocs.io/en/latest/strtree.html

        return [
            [id for id, ply in zip(self.cell_id, self.polygons) if ply.intersects(pt)]
            for pt in xyp
        ]

    def map_xy_to_cell_indexing(
        self,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
        x_idx: np.ndarray | None,
        y_idx: np.ndarray | None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Returns indexing to map xy coordinates a single cell_id axis.

        This function maps the provided one-dimensional set of x and y points onto the
        grid (using `~virtual_ecosystem.core.grid.Grid.map_xy_to_cell_id`) and then
        checks that the mapped points provide a one-to-one mapping onto the grid cells.

        The function then returns a pair of arrays that give indices on the original
        x and y data to extract data along a single cell id axis. Because the inputs are
        expected to be flattened onto a single dimension, the function also accepts x
        and y index values that allow the cells to be mapped back into original
        dimensions. If these are not provided, the coordinates are are assumed to have
        come from a one-dimensional structure and so these indices are simple sequences
        along  `x_coords` and `y_coords`.

        Args:
            x_coords: A numpy array of x coordinates of points that should occur within
                grid cells.
            y_coords: A similar and equal-length array providing y coordinates.
            x_idx: A numpy array providing original indices along the x-axis
            y_idx: A numpy array providing original indices along the y-axis

        Returns:
            A list giving the integer cell id for each pair of points.
        """

        # Get the coordinate mapping to cell ids
        cell_map = self.map_xy_to_cell_id(x_coords=x_coords, y_coords=y_coords)

        # Set indexing to sequence along coords if missing
        if (x_idx is None) ^ (y_idx is None):  # Note: ^ is xor
            raise ValueError("Only one of x/y indices provided.")

        # Generate internal x and y indices.
        if (x_idx is not None) and (y_idx is not None):
            _x_idx = x_idx
            _y_idx = y_idx
        else:
            _x_idx = np.arange(x_coords.shape[0])
            _y_idx = np.arange(y_coords.shape[0])

        # Check the shapes of the indices.
        if (_x_idx.shape != x_coords.shape) or (_y_idx.shape != y_coords.shape):
            raise ValueError("Dimensions of x/y indices do not match coordinates")

        # Find the set of total number of cell mappings per point
        cell_counts = {len(mp) for mp in cell_map}

        # Raise an exception where not all coords fall in a grid cell
        if 0 in cell_counts:
            raise ValueError("Mapped points fall outside grid.")

        # Values greater than 1 indicate coordinates on cell edges
        if any([c > 1 for c in cell_counts]):
            raise ValueError("Mapped points fall on cell boundaries.")

        # Now all points are 1 to 1 with cells so collapse down to list of ints
        cell_id_map = [c[0] for c in cell_map]

        # Get a list of all mapped cell ids.
        cells_found = [v for v in cell_id_map]

        # Now check for cells with more than one point and cells with no points.
        if set(cells_found) != set(self.cell_id):
            raise ValueError("Mapped points do not cover all cells.")

        if len(cells_found) != self.n_cells:
            raise ValueError("Some cells contain more than one point.")

        # Sort indices into cell map order
        cell_order = np.argsort(cell_id_map)
        return _x_idx[cell_order], _y_idx[cell_order]
