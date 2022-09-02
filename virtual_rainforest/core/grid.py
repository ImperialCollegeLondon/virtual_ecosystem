"""The `core.grid` module.

The `core.grid` module is used to create the grid of cells underlying the simulation and
to identify the neighbourhood connections of cells.

TODO - set up neighbourhoods. ? store as graph (networkx - might only need a really
       lightweight graph description).
TODO - import of geojson grids? Way to link structured landscape into cells.  Can use
       data loading methods to assign values to grids? This would be a useful way of
       defining mappings though.
"""

import json
import logging
from functools import wraps
from typing import Callable

import numpy as np
from shapely.affinity import scale, translate
from shapely.geometry import Polygon

LOGGER = logging.getLogger("virtual_rainforest.core")

GRID_REGISTRY: dict[str, Callable] = {}
"""A registry for different grid geometries.

This dictionary maps grid geometry types (square, hex, etc) to a function generating a
grid of that type. Users can register their own grid types using the `register_grid`
decorator.
"""


def register_grid(grid_type: str):
    """Add a grid type and creator function to the grid registry.

    This decorator is used to add a function creating a grid layout to the registry of
    accepted grids. The function should return a dictionary of shapely.geometry.Polygon
    objects, keyed by a cell id str.

    The grid_type argument is used to identify the grid creation function to be used by
    the Grid class and in configuration files.

    Args:
        grid_type: A name to be used to identify the grid creation function.
    """

    def decorator_register_grid(func: Callable):

        # Add the grid type to the registry
        if grid_type in GRID_REGISTRY:
            LOGGER.warning(
                "Grid type %s already exists and is being replaced", grid_type
            )
        GRID_REGISTRY[grid_type] = func

        # Pass the function through for use, using @wraps to expose the original
        # function dunder attributes (__name__, __doc__ etc.)
        @wraps(func)
        def wrapper_register_grid(*args, **kwargs):

            return func(*args, **kwargs)

        return wrapper_register_grid

    return decorator_register_grid


@register_grid(grid_type="square")
def make_square_grid(
    cell_area: float,
    cell_nx: int,
    cell_ny: int,
    xoff: float = 0,
    yoff: float = 0,
) -> dict:
    """Create a square grid.

    Args:
        cell_area: The area of each hexagon cell
        cell_nx: The number of grid cells in the X direction.
        cell_ny: The number of grid cells in the Y direction.
        xoff: An offset to use for the grid origin in the X direction.
        yoff: An offset to use for the grid origin in the Y direction.
    """

    # Create the polygon prototype object, with origin at 0,0 and area 1
    # Note coordinate order is anti-clockwise - right hand rule.
    prototype = Polygon([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])

    # Scale to requested size and origin
    scale_factor = np.sqrt(cell_area)
    prototype = scale(prototype, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    prototype = translate(prototype, xoff=xoff, yoff=yoff)

    # Tile the prototypes to create the grid
    cell_dict = {}

    # Loop over columns and rows of cells, incrementing the base coordinates
    for y_idx in range(cell_ny):
        for x_idx in range(cell_nx):
            # Define the cell id as "row_col"
            cell_id = f"{x_idx}-{y_idx}"
            # Store shifted geometry under cell id
            cell_dict[cell_id] = translate(
                prototype, xoff=scale_factor * x_idx, yoff=scale_factor * y_idx
            )

    return cell_dict


@register_grid(grid_type="hexagon")
def make_hex_grid(
    cell_area: float,
    cell_nx: int,
    cell_ny: int,
    xoff: float = 0,
    yoff: float = 0,
) -> dict:
    """Create a hexagonal grid.

    Args:
        cell_area: The area of each hexagon cell
        cell_nx: The number of grid cells in the X direction.
        cell_ny: The number of grid cells in the Y direction.
        xoff: An offset to use for the grid origin in the X direction.
        yoff: An offset to use for the grid origin in the Y direction.
    """

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

    # Tile the prototypes to create the grid
    cell_dict = {}

    # Loop over columns and rows of cells, incrementing the base coordinates
    for y_idx in range(cell_ny):
        for x_idx in range(cell_nx):
            # Define the cell id as "row_col"
            cell_id = f"{x_idx}-{y_idx}"
            # Store shifted geometry under cell id
            cell_dict[cell_id] = translate(
                prototype,
                xoff=2 * apothem * x_idx + apothem * (y_idx % 2),
                yoff=1.5 * side_length * y_idx,
            )

    return cell_dict


@register_grid(grid_type="triangle")
def make_triangular_grid(
    cell_area: float,
    cell_nx: int,
    cell_ny: int,
    xoff: float = 0,
    yoff: float = 0,
) -> dict:
    """Create a equilateral triangular grid.

    Args:
        cell_area: The area of each triangular cell
        cell_nx: The number of grid cells in the X direction.
        cell_ny: The number of grid cells in the Y direction.
        xoff: An offset to use for the grid origin in the X direction.
        yoff: An offset to use for the grid origin in the Y direction.
    """

    # Note shapely.affinity.rotate for inversion

    raise NotImplementedError()


# @dataclass
# class CoreGridConfig:
#     """Configure the `core.grid` module.

#     This data class is used to setup the arrangement of grid cells to be used in
#     running a `virtual_rainforest` simulation.

#     Attrs:
#         grid_type:
#         cell_contiguity:
#         cell_area:
#         cell_nx:
#         cell_ny:
#     """

#     grid_type: Literal["hex", "square"] = "square"
#     cell_contiguity: Literal["queen", "rook"] = "rook"
#     cell_area: float = 100
#     cell_nx: StrictInt = 10
#     cell_ny: StrictInt = 10


class Grid:
    """Define the grid of cells used in a Virtual Rainforest simulation.

    The simulation grid used in a Virtual Rainforest simulation is assumed to be a
    projected coordinate system with linear dimensions in metres. Grid cell sizes are
    set using their area in square metres and users can specify offsets to align a
    simulation grid to a particular projected coordinate system. However, the Virtual
    Rainforest codebase makes no attempt to manage or validate projection information:
    we assume that users maintain a common coordinate system across inputs.

    Args:
        grid_type: The grid type to be used, which must identify a grid creation
            function in the virtual_rainforest.core.grid.GRID_REGISTRY dictionary.
        cell_area: The area of each grid cell, in square metres.
        cell_nx: The number of cells in the grid along the x (easting) axis
        cell_ny: The number of cells in the grid along the y (northing) axis
        xoff: An offset for the grid x origin
        yoff: An offset for the grid y origin

    Attrs:
        In addition to the arguments above:

        cell_dict: A dictionary, keyed by cell id, of shapely.geometry.Polygon objects.
    """

    def __init__(
        self,
        grid_type: str = "square",
        cell_area: float = 100,
        cell_nx: int = 10,
        cell_ny: int = 10,
        xoff: float = 0,
        yoff: float = 0,
    ) -> None:

        # Populate the attributes
        self.grid_type = grid_type
        self.cell_area = cell_area
        self.cell_nx = cell_nx
        self.cell_ny = cell_ny
        self.xoff = xoff
        self.yoff = yoff

        # Retrieve the creator function from the grid registry and handle unknowns
        creator = GRID_REGISTRY.get(self.grid_type, None)
        if creator is None:
            raise ValueError(f"The grid_type {self.grid_type} is not defined.")

        # Run the grid creation
        self.cell_dict = creator(
            cell_area=self.cell_area,
            cell_nx=self.cell_nx,
            cell_ny=self.cell_ny,
            xoff=self.xoff,
            yoff=self.yoff,
        )

    def __repr__(self) -> str:
        """Represent a CoreGrid as a string."""
        return (
            "CoreGrid("
            f"grid_type={self.grid_type}, "
            f"cell_area={self.cell_area}, "
            f"cell_nx={self.cell_nx}, "
            f"cell_ny={self.cell_ny})"
        )

    def dumps(self, dp: int = 2, **kwargs) -> str:
        """Export a grid as a GeoJSON string.

        The virtual_rainforest.core.Grid object assumes an unspecified projected
        coordinate system. As a result, GeoJSON files created by this export method do
        not strictly obey the GeoJSON specification
        (https://www.rfc-editor.org/rfc/rfc7946), which requires WGS84 coordinates to
        describe locations.

        Args:
            dp: The decimal place precision for exported coordinates
            kwargs: Arguments to json.dumps
        """

        content = self._get_geojson(dp=dp)
        return json.dumps(obj=content, **kwargs)

    def dump(self, outfile: str, dp: int = 2, **kwargs) -> None:
        """Export a grid as a GeoJSON file.

        The virtual_rainforest.core.Grid object assumes an unspecified projected
        coordinate system. As a result, GeoJSON files created by this export method do
        not strictly obey the GeoJSON specification
        (https://www.rfc-editor.org/rfc/rfc7946), which requires WGS84 coordinates to
        describe locations.

        Args:
            outfile: A path used to export GeoJSON data.
            dp: The decimal place precision for exported coordinates
            kwargs: Arguments to json.dump
        """

        content = self._get_geojson(dp=dp)

        with open(outfile, "w") as outf:
            json.dump(obj=content, fp=outf, **kwargs)

    def _get_geojson(self, dp):
        """Convert the grid to a GeoJSON structured dictionary.

        Args:
            dp: The number of decimal places to use in reporting locations
        """

        # Create the output feature list
        features = []

        for key, poly in self.cell_dict.items():

            # Get the coordinates of the outer ring - we are not expecting any holes in
            # grid cell polygons - and wrap in a list to provide Polygon structure.
            coords = [np.round(list(poly.exterior.coords), decimals=dp).tolist()]

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coords,
                },
                "properties": {
                    "cell_id": key,
                    "cell_cx": np.round(poly.centroid.x, decimals=dp),
                    "cell_cy": np.round(poly.centroid.y, decimals=dp),
                },
            }

            features.append(feature)

        return {"type": "FeatureCollection", "features": features}

    def find_neighbours(
        self, edges: bool = True, vertices: bool = False, distance: float = None
    ) -> dict:
        """Find the network of neighbours for a Grid object.

        This method generates a dictionary giving the neighbours of each cell in the
        grid.  The edges and vertices arguments are used to include neighbouring cells
        that share edges or vertices with a focal cell. Alternatively, a distance in
        metres from the focal cell centroid can be used to include neighbouring cells
        within that distance.

        Args:
            edges: Include cells with shared edges as neighbours.
            vertices: Include cells with shared vertices as neighbours.
            distance: A distance in metres.
        """

        raise NotImplementedError()
