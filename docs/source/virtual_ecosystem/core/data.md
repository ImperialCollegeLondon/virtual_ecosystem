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
  display_name: python3
  language: python
  name: python3
---

# Adding and using data with the Virtual Ecosystem

A Virtual Ecosystem simulation requires data to run. That includes the loading of
initial forcing data for the model - things like air temperature, elevation and
photosynthetically active radiation - but also  includes the storage of internal
variables calculated by the various models running within the simulation. The data
handling for simulations is managed by the {mod}`~virtual_ecosystem.core.data` module
and the {class}`~virtual_ecosystem.core.data.Data` class, which provides the data
loading and storage functions for the Virtual Ecosystem. The data system is extendable
to provide support for different file formats and axis validation (see the [module API
docs](../../api/core/data.md)) but that is beyond the scope of this document.

A Virtual Ecosystem simulation will have one instance of the
{class}`~virtual_ecosystem.core.data.Data` class to provide access to the different
forcing and internal variables used in the simulation. As they are loaded, all variables
are validated and then  added to an {class}`xarray.Dataset` object, which provides a
consistent indexing and data manipulation for the underlying arrays of data.

In many cases, a user will simply provide a configuration file to set up the data that
will be validated and loaded when a simulation runs, but the main functionality for
working with data using Python are shown below.

## Validation

One of the main functions of the {mod}`~virtual_ecosystem.core.data` module is to
automatically validate data before it is added to the `Data` instance. Validation is
applied along a set of **core axes** used in the simulation. For a given core axis:

* The dimension names of a dataset are used to identify if data should be validated on
  that axis. For example, a dataset with `x` and `y` dimensions will be validated
  on the `spatial` core axis.

* The axis will have a set of defined validators, which are provided to handles different
  possible data configurations. For example, there is a specific `spatial` validator
  used to handle a dataset with `x` and `y` dimensions but no coordinate values.

* When a dataset is checked against a core axis, the validation checks to see that one
  of those validators applies to the actual configuration of the data, and then runs the
  specific validation for that configuration.

The validation process is primarily intended to check that the sizes or coordinates of
the dimensions of provided datasets are congruent with the configuration of a particular
simulation. Validators may also standardise or subset input datasets to map them onto a
particular axis configuration.

For more details on the different core axes and the alternative mappings applied by
validators see the [core axis](axes.md) documentation.

## Creating a `Data` instance

A  {class}`~virtual_ecosystem.core.data.Data` instance is created using information
that provides information on the core configuration of the simulation. At present, this
is just the spatial grid being used.

```{code-cell}
from pathlib import Path

import numpy as np
from xarray import DataArray

from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.axes import *
from virtual_ecosystem.core.readers import load_to_dataarray

# Create a grid with square 100m2 cells in a 10 by 10 lattice and a Data instance
grid = Grid(grid_type='square', cell_area=100, cell_nx=10, cell_ny=10)
data = Data(grid=grid)

data
```

## Adding data to a Data instance

Data can be added to a {class}`~virtual_ecosystem.core.data.Data` instance using one of
two methods:

1. An existing DataArray object can be added to a
   {class}`~virtual_ecosystem.core.data.Data` instance just using the standard
   dictionary assignment: ``data['var_name'] = data_array``. The Virtual Ecosystem
   {mod}`~virtual_ecosystem.core.readers` module provides the
   function {func}`~virtual_ecosystem.core.readers.load_to_dataarray` to read data into
   a DataArray from supported file formats. This can then be added directly to a Data
   instance:

```python
data['var_name'] = load_to_dataarray('path/to/file.nc', var='temperature')
```

1. The  {meth}`~virtual_ecosystem.core.data.Data.load_data_config` method takes a
   loaded Data configuration - which is a set of named variables and source files - and
   then just uses {func}`~virtual_ecosystem.core.readers.load_to_dataarray` to try and
   load each one.

### Adding a data array directly

Adding a  DataArray to a {class}`~virtual_ecosystem.core.data.Data` method takes an
existing DataArray object and then uses the built in validation to match the data onto
core axes. So, for example, the grid used above has a spatial resolution and size:

```{code-cell}
grid
```

One of the validation routines for the core spatial axis takes a DataArray with `x` and
`y` coordinates and checks that the data covers all the cells in a square grid:

```{code-cell}
temperature_data = DataArray(
    np.random.normal(loc=20.0, size=(10, 10)),
    name="temperature",
    coords={"y": np.arange(5, 100, 10), "x": np.arange(5, 100, 10)},
)

temperature_data.plot();
```

That data array can then be added to the  loaded and validated:

```{code-cell}
data["temperature"] = temperature_data
```

The representation of the {class}`virtual_ecosystem.core.data.Data` instance now shows
the loaded variables:

```{code-cell}
data
```

A variable can be accessed from the `data` object using the variable name as a key, and
the data is returned as an :class:`xarray.DataArray` object.

Note that the `x` and `y` coordinates have been mapped onto the internal `cell_id`
dimension used to label the different grid cells (see the [Grid](./grid.md)
documentation for details).

```{code-cell}
# Get the temperature data
loaded_temp = data["temperature"]

print(loaded_temp)
```

You can check whether a particular variable has been validated on a given core axis
using the {meth}`~virtual_ecosystem.core.data.Data.on_core_axis` method:

```{code-cell}
data.on_core_axis("temperature", "spatial")
```

### Loading data from a file

Data can be loaded directly from a file by providing a path to a supported file
format and the name of a variable stored in the file. In this example below, the
NetCDF file contains a variable `temp` with dimensions `x` and `y`, both of which
are of length 10: it contains a 10 by 10 grid that maps onto the shape of the
configured grid.

```{code-cell}
# Load data from a file
file_path = Path("../../data/xy_dim.nc")
data['temp'] = load_to_dataarray(file_path, var_name="temp")
```

```{code-cell}
data
```

```{code-cell}
data.on_core_axis("temp", "spatial")
```

### Loading data from a configuration

The configuration files for a Virtual Ecosystem simulation can include a data
configuration section. This can be used to automatically load multiple datasets into
a Data object. The configuration file is TOML formatted and should contain an entry
like the example below for each variable to be loaded.

```toml
[[core.data.variable]]
file="'../../data/xy_dim.nc'"
var_name="temp"
```

**NOTE**: At the moment,
`core.data.variable` tags cannot be used across multiple toml config files without
causing `ConfigurationError: Duplicated entries in config files: core.data.variable` to
be raised. This means that all variables need to be combined in one `config` file.

To load configuration data , you will typically use the `cfg_paths` argument
to pass one or more TOML formatted configuration files to create a
{class}`~virtual_ecosystem.core.config.Config` object. You can also use a string
containing TOML formatted text or a list of TOML strings to create a configuration
object:

```{code-cell}
data_toml = '''[[core.data.variable]]
file="../../data/xy_dim.nc"
var_name="temp"
'''

config = Config(cfg_strings=data_toml)
```

The `Config` object can then be passed to the `load_data_config` method:

```{code-cell}
data.load_data_config(config)
```

```{code-cell}
data
```

## Data output

The entire contents of the `Data` object can be output using the
{meth}`~virtual_ecosystem.core.data.Data.save_to_netcdf` method:

```python
data.save_to_netcdf(output_file_path)
```

Alternatively, a smaller netCDF can be output containing only variables of interest.
This is done by providing a list specifying what those variables are to the function.

```python
variables_to_save = ["variable_a", "variable_b"]
data.save_to_netcdf(output_file_path, variables_to_save)
```
