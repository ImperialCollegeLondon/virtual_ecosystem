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
kernelspec:
  display_name: vr_python3
  language: python
  name: vr_python3
---

# The `core.grid` module

This module is used to define the grid of cells used in a `virtual_rainforest`
simulation. Square and hexagon grids are currently supported.

```{code-cell} ipython3
import matplotlib.pyplot as plt

from virtual_rainforest.core.grid import Grid
```

## Square grids

A square grid is defined using the cell area, and the number of cells in the X and Y
directions to include in the simulation.

```{code-cell} ipython3
square_grid = Grid(grid_type="square", cell_area=100, cell_nx=10, cell_ny=10)

square_grid
```

## Hexagon grids

A hexagon grid is defined in a very similar way - alternate rows of hexagons are offset
to correctly tesselate the individual cells.

```{code-cell} ipython3
hex_grid = Grid(grid_type="hexagon", cell_area=100, cell_nx=9, cell_ny=11)

hex_grid
```

## Cell ID codes

Cells are identified by unique sequential integer ID values, which are stored in the
`Grid.cell_id` attribute. These ID values provide an index to other cell attributes
stored within a `Grid` instance:

* `Grid.polygon[cell_id]`: This retrieves a `Polygon` object for the cell boundaries.
* `Grid.centroid[cell_id]`: This retrieves a numpy array giving the coordinates of cell
  centroids.

These `Grid` attributes are used in the code below to show the default cell ID numbering
scheme.

```{code-cell} ipython3
# Side by side plots of the two grid systems
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

for this_ax, this_grid in zip(axes, [square_grid, hex_grid]):

    # Plot the boundary polygon of each cell and label at the centroid
    for cell_id in this_grid.cell_id:
        
        poly = this_grid.polygons[cell_id]
        centroid = this_grid.centroids[cell_id]
        
        cx, cy = poly.exterior.coords.xy
        this_ax.plot(cx, cy, color="k", linewidth=0.5)
        this_ax.text(
            x=centroid[0],
            y=centroid[1],
            s=cell_id,
            ha="center",
            va="center",
        )

    # 1:1 aspect ratio
    this_ax.set_aspect("equal")

```

## Neighbours

The `set_neighbours` method can be used to populate the `neighbours` attribute. This
contains a list of the same length as `cell_id`, containing arrays of the cell ids of
neighbouring cells. At present, only a distance-based neighbourhood calculation is used.
The neighbours of a specific cell can then be retrieved using its cell id as an index.

```{code-cell} ipython3
square_grid.set_neighbours(distance = 10)
square_grid.neighbours[45]
```

```{code-cell} ipython3
hex_grid.set_neighbours(distance = 15)
hex_grid.neighbours[40]
```

## Distances

The `get_distance` method can be used to calculate pairwise distances between lists of
cell ids. A single cell id can also be used.

```{code-cell} ipython3
square_grid.get_distances(45, square_grid.neighbours[45])
```

```{code-cell} ipython3
hex_grid.get_distances([1, 40], hex_grid.neighbours[40])
```

```{code-cell} ipython3
square_grid.set_distances()
square_grid.get_distances(45, square_grid.neighbours[45])
```

## Export grid to GeoJSON

A created grid can also be exported as GeoJSON using the `dumps` and `dump` methods:

```{code-cell} ipython3
simple = Grid('square', cell_nx=2, cell_ny=2, cell_area=1)
simple.dumps()
```
