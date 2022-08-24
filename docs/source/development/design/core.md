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
security implications - there is a recommended `safe_loader` for example! So, `toml`
seems a good choice.

### Configuration system

The config system should provide a way to:

- load a config file into a dictionary:
  (config\['plant'\]\['functional_types'\]\['max_height'\]
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

- Simple indices (`idx_n` and `idx_y`) giving the index of a square grid. The data
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
other data. These use one of the first three approaches above, which index _individual_
cells, to provide the spatial layout of a categorical variable. For example, it could
use `x` and `y` coordinates to map `habitat` with values `forest`, `logged_forest` and
`matrix`.

When loading **data**, a variable could now use that mapping variable to unpack values
for each of the three categories into cells.

These are configured as an array of tables to support multiple mappings:

```toml
[[core.mappings]]
file = /path/to/netcdf.nc
var = habitat
```

### Loading data

Once any mappings have been established, then the configuration defines the source file
and variable name for required forcing variables. The dimension names are used to infer
how to spatially index the data and we have a restricted set of dimension names that
must be used to avoid ambiguity. We also need to have `time` and `depth` as reserved
dimension names but the spatial indexing uses:

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
file = /path/to/netcdf.nc
var = prec

[core.data.air_temperature]
file = /path/to/netcdf.nc
var = temp

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

These could get arbitrarily complex - so at some point we should just say, if you want
sufficiently complex generated data, just roll your own NetCDF files!

I think this can basically just use all the options of `numpy.random`, possibly with the
inclusion of interpolation along a time dimension at a given interval if a time axis is
present.

```python
class DataGenerator:

    def __init__(
        self,
        spatial_axis: str,
        temporal_axis: str,
        temporal_interpolation: np.timedelta64,
        seed: Optional[int],
        method: str, # one of the numpy.random.Generator methods
        **kwargs
        ) -> np.ndarray

```
