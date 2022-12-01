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

# Adding and using data with the Virtual Rainforest

A Virtual Rainforest simulation requires data to run. That includes the loading of
initial forcing data for the model - things like air temperature, elevation and
photosynthetically active radiation - but also  includes the storage of internal
variables calculated by the various models running within the simulation. The data
handling for simulations is managed by the {mod}`~virtual_rainforest.core.data` module
and the {class}`~virtual_rainforest.core.data.Data` class, which provides the data
loading and storage functions for the Virtual Rainforest. The data system is extendable
to provide support for different file formats and axis validation (see the [module API
docs](../../api/core/data.md)) but that is beyond the scope of this document.

A Virtual Rainforest simulation will have one instance of the
{class}`~virtual_rainforest.core.data.Data` class and this instance behaves as a
dictionary to provide access to the different forcing and internal variables used in the
simulation. All of the variables are stored as {class}`~xarray.DataArray` objects from
the {mod}`xarray` package, which provides a consistent indexing and data manipulation
for the underlying arrays of data.

In many cases, a user will simply provide a configuration file to set up the data that
will be validated and loaded when a simulation runs, but the main functionality for
working with data using Python are shown below.

## Validation

One of the main functions of the {mod}`~virtual_rainforest.core.data` module is to
validate data before it is added to the `Data` instance. This works by looking for
particular dimensions on the data that map onto core axes in the simulation and checking
that the dimensions in the input data are congruent with the model configuration. For
example, a data array with `x` and `y` dimensions should have the same number of rows
and columns as square grid.

## Creating a `Data` instance

A  {class}`~core.data.Data` instance is created using information that provides
information on the core configuration of the simulation. At present, this is just the
spatial grid being used.

```{code-cell}
from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.data import Data

# Create a simple default grid and a Data instance
grid = Grid()
data = Data(grid=grid)

print(data)
```

## Adding data to a Data instance

Data can be added to a {class}`~core.data.Data` instance using one of three methods:

1. The  {meth}`~core.data.Data.load_dataarray` method adds an existing DataArray object
   to the Data instance, validating it as it goes.

1. The  {meth}`~core.data.Data.load_from_file` method loads data from a supported file
   format and then coerces it into a DataArray, which is then loaded using
   {meth}`~core.data.Data.load_dataarray`.

1. The  {meth}`~core.data.Data.load_from_config` method takes a loaded Data
   configuration - which is a set of named variables and source files - and then just
   uses {meth}`~core.data.Data.load_from_file` to try and load each one.

### Using `load_dataarray`

The {meth}`~core.data.Data.load_dataarray` method takes an existing DataArray object and
then uses the built in validation to match the data onto core axes. So, for example, the
grid used above has a spatial resolution and size:

```{code-cell}
grid
```

One of the validation routines for the core spatial axis takes a DataArray with `x` and
`y` coordinates and checks that the data covers all the cells in a square grid:

```{code-cell}
grid_data = DataArray(
    np.random.normal(loc=20.0, size=(10, 10)),
    name="temperature",
    coords={"y": np.arange(5, 100, 10), "x": np.arange(5, 100, 10)},
)

print(grid_data.coords)
```

That data array can then be loaded and validated:

```{code-cell}
data.load_dataarray(grid_data)
```

```{code-cell}
print(data)
```

Note that the spatial validator methods map the input data array onto the underlying
`cell_id` used in the `Grid` object.

```{code-cell}
print(data["temperature"])
```
