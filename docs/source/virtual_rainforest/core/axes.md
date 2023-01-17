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

The Virtual Rainforest uses a set of **core axes** which have dimensions and possibly
coordinates set by the configuration of a simulation. Each core axis is defined below
along with the different validation routines used to map data onto a core axis.

Data is loaded into the simulation as {class}`~xarray.DataArray` object. Each of the
dimensions of a data array will have a _dimension name_ and may also have _coordinate
values_ assigned for the dimension. In general, validation for a given core axis will
look for specific dimension names and possibly coordinate values on those dimensions and
then attempts to map those dimensions onto the configured axis.  If an input data set
uses **any** of the dimension names associated with a given core axes, then that data
must past validation on that axis.

## The `spatial` core axis

```{admonition} Array dimensions
This core axis looks for: `cell_id`, `x` and `y`. We expect Virtual Rainforest to be 
used with projected coordinate systems and so `lat` and `long` dimensions do not cause 
data to be mapped onto the `spatial` axis.
```

Within a simulation, the Virtual Rainforest uses a single spatial dimension along the
[grid](grid.md) cell ids, but spatial data is often provided using two dimensional `x`
and `y` coordinates. The mapping of data onto the `spatial` core axis can also vary
depending on the geometry of the simulation grid.

The data has a `cell_id` dimension without coordinates, any grid geometry.
: The `cell_id` dimension must be of the same length as the number of cells in the
  configured grid and is assumed to be in the same order.

The data has a `cell_id` dimension with coordinate values, any grid geometry.
: The coordinate values associated with the `cell_id` dimension must include all of
cell_id values in the configured grid. The data is reordered to map onto the grid cell
id values and any additional cell id values in the data are dropped.

The data has `x` and `y` dimensions, square grid geometry.
: The `x` and `y` dimensions must both be of the same length as the corresponding square
grid dimensions and the data is assumed to be in order. The data is then mapped onto the
internal cell id dimension.

The data has `x` and `y` dimensions with coordinates, square grid geometry.
: The `x` and `y` coordinates for each cell must map data values uniquely onto all
cells in the grid. This will fail if more than one value falls in a cell or if the
coordinates fall ambiguously on cell boundaries but the data input can have a larger
spatial extent than the grid. The data is reordered to map values onto the internal cell
id dimension.
