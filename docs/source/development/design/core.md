---
jupyter:
  jupytext:
    cell_metadata_filter: all,-trusted
    main_language: python
    notebook_metadata_filter: settings,mystnb,language_info
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.4
---

# Design notes for the `core` module

## Configuration

### Config file format

We need a system to configure the options used by the VR modules. There are a variety of
file formats for config storage.

The basic requirements are:

- **Human readable**. This rules out JSON, which is really for data serialisation and is
  unpleasant to read.
- **Allows comments**. Again, JSON falls foul of this. There are commented extensions of
  JSON but we've already ruled it out on other grounds.
- **Allows deep nested config**. Essentially, we want a config file to be able to
  specify - for example - `plant.functional_types.max_height`. This rules out INI files
  \- this is kind of a shame because the `configparser` module handles these elegantly,
  but INI files only allow a single level of nesting. We _could_ split up config files
  to ensure only one level is needed but that results in either having to reduce nesting
  or have odd and rather arbitrary sets of files.

At this point, the contenders are really `yaml` and `toml`. The `yaml` format is more
widely used but the complexities of `yaml` mean that it has some unusual behaviour and
security implications - there is a recommended `safe_loader` for example! So, for these
reasons make use of the `toml` file format for configuration of the Virtual Ecosystem.

### Configuration system

The config system should provide a way to:

- load a config file into a dictionary:
  config\['plant'\]\['functional_types'\]\['max_height'\]
- or possibly something like a dataclass for dotted notation:
  (config.plant.functional_types.max_height)
- validate the config against some kind of template
- It is likely that different configurations may re-use config subsections in different
  combinations, so the config system should be capable of loading configs from
  **multiple** files, so that a complete config can be built up or updated from multiple
  files, rather than having to compile a single monolithic file for each permutation.

### Design

The system should have:

- A `config_loader` function to read a particular file, optionally validating it
  against a matching config template.
- A central `Config` class, which can be built up using `ConfigLoader`.

## Data

We need a system for providing forcing data to the simulation. Although some forcing
variables are likely to be module specific, it seems better to avoid having arbitrary
locations and collect everything using configuration of `core.data`.

For the moment, let's assume a common NetCDF format for data inputs.

### Spatial indices

Data is (always?) associated with a grid cell, so the system needs to be able to match
data values to the cell id of grid cells. The following spatial indexing options seem
useful (and all of these could add a time dimension):

#### Two dimensial spatial indexing

- Simple indices (`idx_x` and `idx_y`) giving the index of a square grid. The data
  should match the configured grid size and only really works for square grids (it could
  just about work for a hex grid with alternate offsets!).
- Standard `x` and `y` coordinates (or `easting` and `northing`). This would require
  matching the coordinates of the NetCDF data to the grid definition (origin and
  resolution) as well as the grid size. This again only really works for square grids.

#### One dimensional spatial indexing

- Simply using a `cell_id` dimension in the NetCDF file to match data to grid cells.
  This is entirely agnostic about the grid shape - users just need to provide a
  dimension that covers all of the configure cell ids.

- A **mapping** of particular attributes to sets of cells. The obvious use case here is
  habitat type style data - for example different soil bulk densities or plant
  communities. To unpack that a bit:

### Defining mappings

A user can optionally configure mappings, which are loaded and validated before any
other data. These _have_ to use one of the methods that provides values to every cell,
so either of the 2D approaches or using `cell_id`. So for example, the array below might
define an arrangement of a gradient between different levels of forest cover: matrix to
logged to forest.

```toml
[core.data.forest_cover]
values  = [['M', 'M', 'L'],
          ['L', 'L', 'F'],
          ['L', 'F', 'F']]
```

Then you could have a separate variable that uses that variable to map values per class
onto the spatial grid. The config structure here is in _no way fixed_ - it is the
concept that matters!

```toml
[core.data.soil_depth]
values = {forest_cover.M=0.1, forest_cover.L=0.5, forest_cover.F=1.0}
```

These use one of the first three approaches above, which index _individual_
cells, to provide the spatial layout of a categorical variable. For example, it could
use `x` and `y` coordinates to map `habitat` with values `forest`, `logged_forest` and
`matrix`.

When loading **data**, a variable could now use that mapping variable to unpack values
for each of the three categories into cells.

These are configured as an array of tables to support multiple mappings:

```toml
[[core.mappings]]
file = '/path/to/netcdf.nc'
var = "habitat"
```

### Loading data

Once any mappings have been established, then the configuration defines the source file
and variable name for required forcing variables. The dimension names are used to infer
how to spatially index the data and we have a restricted set of dimension names that
must be used to avoid ambiguity. We also need to have other reserved dimension names
(for example, `time`, `depth`, `height`) but spatial indexing expects the following
dimension names to define particular indexing approaches:

- `x`, `y`: use coordinates to match data to cells,
- `idx_x`, `idx_y`: just use indices to match data to cells,
- `cell_id`: use cell ids,
- Otherwise, the dimension should be a previously defined mapping.

If a variable only has a `time` or `depth` dimension, it is assumed to be spatially
constant.

These are configured directly to defined input slots. The config should also accept
values directly to avoid having to create NetCDF files with trivial variables.

```toml
[core.data.precipitation]
file = '/path/to/netcdf.nc'
var = "prec"

[core.data.air_temperature]
file = '/path/to/netcdf.nc'
var = "temp"

[core.data.ambient_co2]
values = 400

[core.data.elevation]
values = [[1,2,3], [2,3,4], [3,4,5]]
```

### Data Generator

It seems useful to have a `DataGenerator` class that can be used via the configuration
to provide random or constant data.

The basic idea would be something that defines:

- a spatial structure,
- a range or central value,
- optionally some kind of variation,
- optionally a time axis,
- optionally some kind of cycle,
- optionally some kind of probability of different states.

It would be good if these could be set via configuration but also use the same
functionality to create a NetCDF output. That _should_ effectively be the same as
configuring the data generator with a set random number generator seed.

I think this can basically just use all the options of `numpy.random`, possibly with the
inclusion of interpolation along a time dimension at a given interval if a time axis is
present.

<!-- markdownlint-disable MD012 # jupytext adds a line that markdownlint dislikes -->


```{code-cell} ipython3
class DataGenerator:

    def __init__(
        self,
        spatial_axis: str,
        temporal_axis: str,
        temporal_interpolation: np.timedelta64,
        seed: Optional[int],
        method: str,  # one of the numpy.random.Generator methods
        **kwargs
    ) -> np.ndarray:

        pass
```

<!-- markdownlint-enable MD012 -->

The model I have in my head is based around the `numpy.random` methods
[](https://numpy.org/doc/stable/reference/random/generator.html).

A user could provide a scalar (so a global value) or an array (matching a spatial grid
or mapping) that stipulates a method and keyword arguments. So here a DataGenerator
might be:

```{code-cell} ipython3
# Global value varying as a normal distribution around 5
ex1 = DataGenerator(loc=5, scale=2, distribution="normal")
# A 2x2 grid with lognormal values with mean varying by cell, but constant variation.
ex2 = DataGenerator(mean=[[5, 6], [7, 8]], sigma=2, distribution="lognormal")
```

More advanced would be providing a time series of values with variation. Here, you'd
need a time axis giving the temporal location of the sampling points, which could be
interpolated if necessary. So for example, a 2 x 2 grid with normally distributed values
that increase in location and scale over a year.

```{code-cell} ipython3
loc = [[[1, 2], [3, 4]], [[2, 3], [4, 5]]]

scale = [[[1, 1], [1, 1]], [[1.2, 1.2], [1.2, 1.2]]]

time = ["2020-01-01", "2020-12-31"]

ex3 = DataGenerator(loc=loc, scale=scale, method="normal", time=time, time_axis=2)
```

We could provide ways to provide sequences of generators to provide more complex
scenarios or probabilistic switching between generators (El Niño years?). However, this
could end up being a deep rabbit hole so at some point we should just say, if you want
sufficiently complex scenarios, just roll your own NetCDF files! We could provide
examples of that.
