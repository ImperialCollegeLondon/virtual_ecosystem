
# Implementation of the core components

The first stages in a simulation are the configuration and initialisation of the core
components.

## The configuration

The model core and each science model has a set of configuration options that set how
the simulation is set up and how the science models run. These configuration options are
defined by model schema files that: document the required elements for configuring the
core system or model; provide any default values and implement basic validation.

When a simulation starts, the Virtual Ecosystem takes the user-provided configuration
files, which are written in the `TOML` format, and loads them to create a single
configuration description. This is then validated against the core schema and the schema
of any model included in the configuration. This will fill in any missing default values
and will fail if options are duplicated or fail the validation.

Further details can be found in the [configuration
documentation](../../using_the_ve/configuration/config.md).

## The grid

Next, the spatial structure of the simulation is configured as a [`Grid`
object](../../using_the_ve/configuration/grid.md) that defines the area, coordinate system
and geometry of the individual cells that will be used in the simulation.

## The vertical layer structure

The vertical layer structure of the Virtual Ecosystem can be configured to change a
number of elements, including: the maximum number of canopy layers, the number and depths
of soil layers, and the maximum soil depth for microbial activity. The LayerStructure
core component resolves these settings into a vertical layer structure and provides the
model code with indexing to extract particular layers from within vertically structured
data.

:::{figure} ../../_static/images/layer_structure.svg
:name: fig_layer_structure
:alt: Vertical Layer Structure
:width: 650px

The vertical layer structure of a Virtual Ecosystem simulation (click to zoom).
:::

## Loading and validation of input data

All of the data required to initialise and run the simulation is then loaded into an
internal [`Data` object](../../using_the_ve/data/data.md). The model configuration sets the
locations of files containing required variables and this configuration is passed into
the {meth}`~virtual_ecosystem.core.data.Data.load_data_config` method, which ensures
that:

* the input files are valid and can be read, and
* that the data in files is congruent with the rest of the configuration, such as
  checking the dimensionality and shape of [core
  axes](../../using_the_ve/configuration/axes.md) like the spatial grid.

## Simulation timescale

The simulation runs between two dates with an update interval at which each science
model is recalculated. These values are defined in the `core` configuration and are
now validated to ensure that the start date, end date and update interval are sensible.

```{note}
The simulation uses 12 equal length months (30.4375 days) and equal length years (365.25
days), ignoring leap years.
```

## Core constants

TBD
