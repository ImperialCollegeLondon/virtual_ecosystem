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
{class}`~virtual_rainforest.core.data.Data` class to provide access to the different
forcing and internal variables used in the simulation. As they are loaded, all variables
are validated and then  added to an {class}`xarray.Dataset` object, which provides a
consistent indexing and data manipulation for the underlying arrays of data.

In many cases, a user will simply provide a configuration file to set up the data that
will be validated and loaded when a simulation runs, but the main functionality for
working with data using Python are shown below.

## Validation

One of the main functions of the {mod}`~virtual_rainforest.core.data` module is to
automatically validate data before it is added to the `Data` instance. Validation is
applied along a set of **core axes** used in the simulation. Each core axis has a set of
validators: each validator in the set detects a possible data configuration and then
runs code to validate data in that configuration. The validation process is primarily
intended to check that provided data is congruent with the configuration of a particular
simulation.

The validators use the dimension names of input data to detect if that data should be
validated on a particular axis. For example, the `x` and `y` dimension names are used to
trigger validation on the `spatial` core axis.

### Core axes

The table below show the dimension names that are used to trigger validation on core
axes in a simulation. If an input data set uses **any** of the dimension names
associated with a given core axes, then that data must past validation on the axis.

```{list-table}
:header-rows: 1

* - Axis name
  - Dimension names
* - `spatial`
  - `x`, `y`, `cell_id`
```

## Creating a `Data` instance

A  {class}`~virtual_rainforest.core.data.Data` instance is created using information
that provides information on the core configuration of the simulation. At present, this
is just the spatial grid being used.

```{code-cell} ipython3
from virtual_rainforest.core.grid import Grid
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.axes import *
from xarray import DataArray
import numpy as np

# Create a simple default grid and a Data instance
grid = Grid()
data = Data(grid=grid)

data
```

## Adding data to a Data instance

Data can be added to a {class}`~virtual_rainforest.core.data.Data` instance using one of
three methods:

1. An existing DataArray object can be added to a
   {class}`~virtual_rainforest.core.data.Data` instance just using the standard
   dictionary assignment.

1. The  {meth}`~virtual_rainforest.core.data.Data.load_from_file` method loads data from
   a supported file format and then coerces it into a DataArray, which is then added to
   the `~virtual_rainforest.core.data.Data` instance.

1. The  {meth}`~virtual_rainforest.core.data.Data.load_from_config` method takes a
   loaded Data configuration - which is a set of named variables and source files - and
   then just uses {meth}`~virtual_rainforest.core.data.Data.load_from_file` to try and
   load each one.

### Adding a data array directly

Adding a  DataArray to a {class}`~virtual_rainforest.core.data.Data` method takes an
existing DataArray object and then uses the built in validation to match the data onto
core axes. So, for example, the grid used above has a spatial resolution and size:

```{code-cell} ipython3
grid
```

One of the validation routines for the core spatial axis takes a DataArray with `x` and
`y` coordinates and checks that the data covers all the cells in a square grid:

```{code-cell} ipython3
temperature_data = DataArray(
    np.random.normal(loc=20.0, size=(10, 10)),
    name="temperature",
    coords={"y": np.arange(5, 100, 10), "x": np.arange(5, 100, 10)},
)

temperature_data.plot();
```

That data array can then be added to the  loaded and validated:

```{code-cell} ipython3
data["temperature"] = temperature_data
```

The representation of the {class}`virtual_rainforest.core.data.Data` instance now shows
the loaded variables:

```{code-cell} ipython3
data
```

A variable can be accessed from the `data` object using the variable name as a key, and
the data is returned as an :class:`xarray.DataArray` object.

```{code-cell} ipython3
# Get the temperature data
loaded_temp = data["temperature"]

print(loaded_temp)
```

You can check whether a particular variable has been validated on a given core axis
using the {meth}`~virtual_rainforest.core.data.Data.on_core_axis` method:

```{code-cell} ipython3
data.on_core_axis("temperature", "spatial")
```
