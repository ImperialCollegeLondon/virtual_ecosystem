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
import numpy as np

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

## Grid centroids

The centroids of the grid cell polygons are available via the `centroids` attribute as a
`numpy` array of ($x$, $y$) pairs: these can be indexed by cell id:

```{code-cell} ipython3
square_grid.centroids[0:5]
```

## Grid origin

Grid types can take optional offset arguments (`offx` and `offy`) to set the origin of
the grid. This can be useful for aligning a simulation grid with data in real projected
coordinate systems, rather than having to move the origin in multiple existing data
files.

```{code-cell} ipython3
offset_grid = Grid(
  grid_type="square",
  cell_area=100,
  cell_nx=10,
  cell_ny=10,
  xoff=500000,
  yoff=200000
)

offset_grid
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

By default, cell-to-cell distances are calculated on demand, because the size of the
complete pairwise distance matrix scales as the square of the grid size. However, the
`populate_distances` method can be used to populate that matrix, and it is then used by
`get_distance` for faster lookup of distances.

```{code-cell} ipython3
square_grid.populate_distances()
square_grid.get_distances(45, square_grid.neighbours[45])
```

## Mapping points to grid cells

The `Grid` class also provides methods to map coordinates onto grid cells.

### Mapping coordinates

The `map_coordinates` method is more general and simply returns the cell ids (if any)
of the grid cells that intersect pairs of coordinates. Note that points that lie on
cell boundaries will intersect **all** of the cells sharing a boundary.

The method returns a list of lists, giving the cell_ids for each pair of points in turn.

```{code-cell} ipython3
# A simple small grid
simple = Grid('square', cell_nx=2, cell_ny=2, cell_area=1, xoff=1, yoff=1)

# Points that lie outside, within and on cell boundaries
points_x = [0.75, 1.25, 1.5, 2, 2.25, 3.25]
points_y = [0.75, 1.25, 2, 2, 2.25, 3.25]

# Plot the data
for cell_id in simple.cell_id:

    poly = simple.polygons[cell_id]
    centroid = simple.centroids[cell_id]

    cx, cy = poly.exterior.coords.xy
    plt.plot(cx, cy, color="k", linewidth=0.5)
    plt.text(
        x=centroid[0],
        y=centroid[1],
        s=cell_id,
        ha="center",
        va="center",
    )

plt.plot(points_x, points_y, 'rx')

# 1:1 aspect ratio
plt.gca().set_aspect('equal')
```

```{code-cell} ipython3
# Recover the cells under each pair of points.
simple.map_coordinates(points_x, points_y)
```

### Mapping point coverage of grid

The `map_coverage` method does the same thing but then additionally checks that the
points provide a one-to-one mapping to the grid cells. This is primarily used to check
that a provided dataset completely covers the grid.

The function will raise `ValueError` exceptions if:

* any points ambiguously lie on cell boundaries,
* if more than one point falls in any cell,
* if no points fall in any cell, or
* any points fall outside all the grid cell. This check can be turned off using
  `strict=False` to provide mappings where a grid lies entirely within a dataset.

The method returns a list of cell ids for the points. Where `strict=False`, points
falling outside the grid get `None` within the list.

```{code-cell} ipython3
# A set of four points that covers the grid
points_x = [1.5, 2.5, 1.5, 2.5]
points_y = [1.5, 1.5, 2.5, 2.5]

# Validate and recover the mapping 
simple.map_coverage(points_x, points_y)
```

```{code-cell} ipython3
:tags: ["raises-exception"]
# A set of points that extend beyond the grid
points_x = np.tile([0.5, 1.5, 2.5, 3.5], 4)
points_y = np.repeat([0.5, 1.5, 2.5, 3.5], 4)

# Fails because points extend outside the grid
simple.map_coverage(points_x, points_y)
```

```{code-cell} ipython3
# Allow point coverage to extend beyond grid
simple.map_coverage(points_x, points_y, strict=False)
```

## Export grid to GeoJSON

A created grid can also be exported as GeoJSON using the `dumps` and `dump` methods:

```{code-cell} ipython3
simple = Grid('square', cell_nx=2, cell_ny=2, cell_area=1)

simple.dumps()
```
