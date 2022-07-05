---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
---

# The `core.grid` module

This module is used to define the grid of cells used in a `virtual_rainforest`
simulation. Square and hexagon grids are currently supported.

```{code-cell}
import matplotlib.pyplot as plt

from virtual_rainforest.core.grid import CoreGrid, CoreGridConfig
```

## Square grids

A square grid is defined using the cell area, and the number of cells in the X and Y
directions to include in the simulation.

```{code-cell}
sq_config = CoreGridConfig(grid_type="square", cell_area=100, cell_nx=10, cell_ny=10)
square_grid = CoreGrid(config=sq_config)

square_grid
```

## Hexagon grids

A hexagon grid is defined in a very similar way - alternate rows of hexagons are offset
to correctly tesselate the individual cells.

```{code-cell}
hx_config = CoreGridConfig(grid_type="hex", cell_area=100, cell_nx=9, cell_ny=11)
hex_grid = CoreGrid(config=hx_config)

hex_grid
```

## Cell ID codes

Unique cell ID codes use the column and then row indices within the grid from an origin
in the lower left, as shown below.

```{code-cell}
# Side by side plots of the two grid systems
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

for this_ax, this_grid in zip(axes, [square_grid, hex_grid]):

    # Plot the boundary polygon of each cell and label at the centroid
    for cell_id, cell in this_grid.cell_dict.items():

        this_ax.plot(*cell["poly"].T, color="k")
        this_ax.text(
            x=cell["centroid"][0],
            y=cell["centroid"][1],
            s=cell_id,
            ha="center",
            va="center",
        )

    # 1:1 aspect ratio
    this_ax.set_aspect("equal")
```

## Export grid to GeoJSON

The created grid can be exported to a GeoJSON file:

```{code-cell}
hex_grid.export_geojson("test.geojson")
```
