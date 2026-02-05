---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
language_info:
  codemirror_mode:
    name: ipython
    version: 3
  file_extension: .py
  mimetype: text/x-python
  name: python
  nbconvert_exporter: python
  pygments_lexer: ipython3
  version: 3.11.9
mystnb:
  render_markdown_format: myst
---

# The Virtual Ecosystem core configuration

The core configuration of the Virtual Ecosystem sets up the following parts of the
simulation, which are shared across all of the science models. Each of these parts is
configured in its own configuration section:

* the [spatial grid](#the-spatial-grid) (`[core.grid]`),
* the [temporal extent and resolution](#the-temporal-extent-and-resolution)
  (`[core.timing]`),
* the [vertical layer structure](#the-vertical-layer-structure) (`[core.layers]`),
* the [core constants](#core-constants) (`[core.constants]`), and
* the [data output settings](#data-output-settings) for a simulation
  (`[core.data_output_options]`),

The core configuration section is also used to set the location of data input files for
required forcing variables for the simulation, but the `[core.data]` section is
discussed in the [model data inputs](./model_data_inputs.md) documentation.

```{tip}
You may find it useful to create the core TOML configuration for your system as the
first step in developing your own simulations. You can then load the TOML settings into
data preparation scripts used to create other VE inputs. This can help keep the various
data settings aligned across your project.
```

## Validation of the core configuration

Each of the model configuration option has specific validation settings that are
enforced when a configuration is loaded. These constraints should be described in the
documentation of each setting. If configuration data contains invalid values, then the
simulation will exit and the log will contain a detailed breakdown of any configuration
validation issues.

## The spatial grid

The `[core.grid]` configuration section is central to a Virtual Ecosystem simulation and
defines a set of grid cells within which the simulation will run. Each cell can have its
own climate and elevation and may contain different plant and animal communities. The
relative elevations of the cells will also define the hydrology of the simulation.

At present, simulations only support rectangular arrays of square grid cells: you can
set the number of cells and their area in square metres. You can also set an offset for
the origin coordinates of the grid. This can be useful if you want to match your
simulation coordinates to incoming data that has real world coordinates from a projected
coordinate system.

```{code-cell} ipython3
:tags: [remove-input]

from config_display import (
    dump_config_toml,
    model_config_to_deflist,
)
from virtual_ecosystem.core.model_config import GridConfiguration
from virtual_ecosystem.core.grid import Grid
import matplotlib.pyplot as plt
import numpy as np

config_object = GridConfiguration()
dump_config_toml("core.grid", config_object)
model_config_to_deflist("core.grid", config_object)
```

When running a simulation, the Virtual Ecosystem assigns a unique numeric cell id to
each cell and these cell ids are widely used in data outputs. They are simply increasing
integers starting from zero in the top left and increase across rows first ['row major'
order](https://en.wikipedia.org/wiki/Row-_and_column-major_order). The default values
above result in the grid layout, coordinates and cell id values shown below: a 9x9 grid
of 90m resolution cells, with the coordinate origin in the centre of the lower left
cell.

```{code-cell} ipython3
:tags: [remove-input]

square_grid = Grid(**GridConfiguration().model_dump())

# Side by side plots of the two grid systems
fig, ax = plt.subplots(1, 1, figsize=(4, 4))

# Plot the boundary polygon of each cell and label at the centroid
for cell_id in square_grid.cell_id:

    poly = square_grid.polygons[cell_id]
    centroid = square_grid.centroids[cell_id]

    cx, cy = poly.exterior.coords.xy
    ax.plot(cx, cy, color="k", linewidth=0.5)
    ax.text(
        x=centroid[0],
        y=centroid[1],
        c="red",
        s=cell_id,
        ha="center",
        va="center",
    )

# 1:1 aspect ratio
ax.set_aspect("equal")
ticks = np.arange(0, 90 * 9, 90)
ax.set_xticks(ticks)
ax.set_yticks(ticks)
plt.tight_layout()
```

```{important}
You need to make sure that all spatially structured input data - which is nearly all of
the required starting variables for a simulation - is congruent with the grid
configuration you use. That might be using the unique cell id codes or providing data
as spatial grids in NetCDF format using the cell coordinates from your configuration.
```

## The temporal extent and resolution

The `[core.timing]` configuration section sets the temporal resolution of the simulation
and the total number of time steps. You need to provide a start date, the time interval
of updates and the total run length. The update interval and total run length can be
provided as string descriptions.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.model_config import TimingConfiguration

model_object = TimingConfiguration()
dump_config_toml("core.timing", model_object)
model_config_to_deflist("core.timing", model_object)
```

```{important}
You need to make sure that all temporally structured input data is congruent with the
timing configuration you use. That will typically be providing a time axis within a
NetCDF file that matches the number of time steps defined above.
```

## The vertical layer structure

The `[core.layers]` configuration section defines the vertical layer structure of the
simulation. The model uses a fixed number of layers along the vertical height axis: this
configuration is used to set the actual heights of layers - sometimes relative to the
canopy layer heights - and the number of layers. See the [vertical structure
implementation](../virtual_ecosystem/implementation/core_components_overview.md#the-vertical-layer-structure)
page for more details.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.model_config import LayersConfiguration

model_object = LayersConfiguration()
dump_config_toml("core.layers", model_object)
model_config_to_deflist("core.layers", model_object)
```

## Data output settings

The `[core.data_output_options]` section is used to control when data is exported from
the simulation.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.model_config import DataOutputConfiguration

model_object = DataOutputConfiguration()
dump_config_toml("core.data_output_options", model_object)
model_config_to_deflist("core.data_output_options", model_object)
```

## Core constants

The `[core.constants]` section defines a set of constants values that are shared across
the whole simulation. This includes some global constants, as well as some values
that are required across multiple models.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.model_config import CoreConstants

model_object = CoreConstants()
dump_config_toml("core.constants", model_object)
model_config_to_deflist("core.constants", model_object)
```
