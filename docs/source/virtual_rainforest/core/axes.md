---
jupytext:
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

# Core axes

The Virtual Ecosystem uses a set of **core axes** which have dimensions and possibly
coordinates set by the configuration of a simulation.

* The **dimensions** of an axis set the shape of the axis. For example, a simulation
  might use a square 10 by 10 [grid](grid.md), so spatial data might be expected to
  have the same 10 by 10 shape along `x` and `y` dimensions.

* The **coordinates** of an axis set the values of the intervals along the dimension.
  For example, a spatial grid might be configured with [offsets](grid.md#grid-origin)
  to map data onto a projected coordinate system.

When data is loaded into the simulation as it is first converted into a
{class}`~xarray.DataArray` object. These objects also provide _dimension names_ for each
of the array dimensions and can also have _coordinate values_ assigned for the
dimension. This allows the axis validation to ensure that the dimensions and coordinates
of loaded data are congruent with the different core axes.

In general, validation for a given core axis will look for specific dimension names and
any coordinate values and attempts to map those dimensions onto the configured axis. The
validators for an axis all define sets of dimensions names that are used to match
dimensions to that axis.  If an input data set uses **any** of the dimension names
associated with a given core axes, then that data must pass validation on that axis.
Each core axis is defined below along with the validation used to map data onto a core
axis.

## The `spatial` core axis

```{admonition} Array dimensions
The validators for this axis check for variables with either a `cell_id` dimension or 
with `x` and `y` dimensions. 

Datasets that use `latitude` and `longitude` dimension names - or variants of those 
names - will not be validated on the `spatial` axis. This is because we expect Virtual 
Ecosystem to be used exclusively with projected coordinate systems and so spatial data 
on geographic coordinates must be projected onto appropriate local projected coordinates
before use.
```

Within a simulation, the Virtual Ecosystem uses a single spatial dimension along the
[grid](grid.md) cell ids, so a `cell_id` dimension can be used to directly map data onto
the grid. However, spatial data is often provided using two dimensional `x` and `y`
coordinates, which can then be used to map data onto polygon geometry of each of the
grid cells. The `spatial` validators cover the following cases.

The data has a `cell_id` dimension without coordinates, any grid geometry.
: The `cell_id` dimension must be of the same length as the number of cells in the
  configured grid and is assumed to be in the same order.

The data has a `cell_id` dimension with coordinate values, any grid geometry.
: In this case, the dataset associates `cell_id` values with positions along the
`cell_id` dimension. Those might simply be `0` to `ncells`, but could be in a different
order. Those values associated with the `cell_id` dimension must then provide a
one-to-one mapping onto the `cell_id` values defined in the configured grid. The data is
reordered to map onto the grid cell id values.

The data has `x` and `y` dimensions, square grid geometry.
: In this case, the `x` and `y` dimensions provide the shape of the grid - for example -
a 10 by 10 grid - but not `x` and `y` coordinates for each cell. The data grid must be
the same shape as the square grid dimensions and the data is assumed to be in the same
order as the grid. The data is then mapped onto the internal cell id dimension.

The data has `x` and `y` dimensions with coordinates, square grid geometry.
: The `x` and `y` coordinates must provide a one-to-one mapping of the data values onto
the cell geometries in the grid. This will fail if: more than one value falls in a cell,
the coordinates fall ambiguously on cell boundaries, or the data provide too few or too
many coordinates for the data. The data is reordered to map values onto the internal
cell id dimension.
