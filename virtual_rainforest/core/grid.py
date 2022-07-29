"""The `core.grid` module.

The `core.grid` module is used to create the grid of cells underlying the simulation and
to set up the neighbourhood connections of cells.

TODO - set up neighbourhoods. ? store as graph (networkx - might only need a really
       lightweight graph description).
TODO - export of files to geojson
TODO - import of geojson grids? Way to link structured landscape into cells
"""

import fiona
import numpy as np
from pydantic import StrictInt
from pydantic.dataclasses import dataclass
from pydantic.typing import Literal


@dataclass
class CoreGridConfig:
    """Configure the `core.grid` module

    This data class is used to setup the arrangement of grid cells to be used in
    running a `virtual_rainforest` simulation.

    Attrs:
        grid_type:
        cell_contiguity:
        cell_area:
        cell_nx:
        cell_ny:
    """

    grid_type: Literal["hex", "square"] = "square"
    cell_contiguity: Literal["queen", "rook"] = "rook"
    cell_area: float = 100
    cell_nx: StrictInt = 10
    cell_ny: StrictInt = 10


class CoreGrid:
    """Define the grid of cells used in a virtual rainforest simulation

    Args:
        config: A CoreGridConfig instance used to setup the grid

    Attrs:
        config: The CoreGridConfig used to create an instance
        cell_dict: A dictionary, keyed by cell id, of dictionaries, containing the cell
            polygon, centroid and neighbours for each cell.
    """

    def __init__(self, config: CoreGridConfig) -> None:

        self.config = config

        # Set up the grid
        if config.grid_type == "square":
            self.cell_dict = self._make_square_grid(
                cell_area=config.cell_area,
                cell_nx=config.cell_nx,
                cell_ny=config.cell_ny,
            )
        elif config.grid_type == "hex":
            self.cell_dict = self._make_hex_grid(
                cell_area=config.cell_area,
                cell_nx=config.cell_nx,
                cell_ny=config.cell_ny,
            )

    def __repr__(self) -> str:

        return (
            "CoreGridConfig("
            f"grid_type={self.config.grid_type}, "
            f"cell_area={self.config.cell_area}, "
            f"cell_nx={self.config.cell_nx}, "
            f"cell_ny={self.config.cell_ny})"
        )

    @staticmethod
    def _make_square_grid(cell_area: float, cell_nx: int, cell_ny: int) -> dict:
        """Create a square grid

        Args:
            cell_area:
            cell_nx:
            cell_ny:
        """

        # Create the base object, with origin at 0,0
        side = np.sqrt(cell_area)
        base = np.array([[0, 0], [0, side], [side, side], [side, 0], [0, 0]])

        cell_dict = {}

        # Loop over columns and rows of cells, incrementing the base coordinates
        for y_idx in range(cell_ny):
            for x_idx in range(cell_nx):
                # Cell ID
                cell_id = f"{x_idx}-{y_idx}"
                # Shifted cell coordinates
                cell_coords = base + np.array([side * x_idx, side * y_idx])
                # Cell geometry
                cell_dict[cell_id] = {
                    "poly": cell_coords,
                    "centroid": cell_coords[0, :] + side / 2,
                }

        return cell_dict

    @staticmethod
    def _make_hex_grid(cell_area: float, cell_nx: int, cell_ny: int) -> dict:
        """Create a hexagon grid

        Args:
            cell_area:
            cell_nx:
            cell_ny:
        """

        # Calculate the side length and apothem of the hexagon and get the base hexagon
        # with origin at 0,0
        side = (2.0 / 3.0) * 3**0.75 * np.sqrt(cell_area / 6)
        apothem = np.sqrt(3) * side / 2
        base = np.array(
            [
                [apothem, 0],
                [0, side * 0.5],
                [0, side * 1.5],
                [apothem, side * 2],
                [2 * apothem, side * 1.5],
                [2 * apothem, side * 0.5],
                [apothem, 0],
            ]
        )

        cell_dict = {}

        # Loop over columns and rows of cells, incrementing the base coordinates
        for y_idx in range(cell_ny):
            for x_idx in range(cell_nx):
                # Cell ID
                cell_id = f"{x_idx}-{y_idx}"
                # Shifted cell coordinates
                cell_coords = base + np.array(
                    [2 * apothem * x_idx + apothem * (y_idx % 2), 1.5 * side * y_idx]
                )
                # Cell geometry
                cell_dict[cell_id] = {
                    "poly": cell_coords,
                    "centroid": cell_coords[0, :] + np.array([0, side]),
                }

        return cell_dict

    def export_geojson(self, outfile: str):
        """Export grid system as geojson file.


        Args:
            outfile: A self.cell_dict returned by a make_square_grid
                     or make_hex_grid call.
        """

        # Open a collection for writing.
        with fiona.open(
            outfile,
            "w",
            # crs=from_epsg(4326),
            driver="GeoJSON",
            schema={
                "geometry": "Polygon",
                "properties": {
                    "cell_id": "str:24",
                    "cell_cx": "float",
                    "cell_cy": "float",
                },
            },
        ) as output:

            def _feature(cell_tuple):
                """Convert a (key, val) tuple from iterating over the items in
                self.cell_dict into a fiona feature"""

                cell_id, cell_dict = cell_tuple

                poly = [tuple(x) for x in cell_dict["poly"].tolist()]
                geom = {"type": "Polygon", "coordinates": [poly]}

                props = {
                    "cell_id": cell_id,
                    "cell_cx": cell_dict["centroid"][0],
                    "cell_cy": cell_dict["centroid"][1],
                }
                return {"type": "Feature", "geometry": geom, "properties": props}

            # Write all of self.cell_dict to file
            output.writerecords(map(_feature, self.cell_dict.items()))
