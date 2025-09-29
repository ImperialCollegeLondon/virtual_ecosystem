---
jupytext:
  formats: md:myst,ipynb
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

<!--
This notebook presents the usage of the `ve_run` command to run the example data.
We want the notebook to be dynamic - so that updates to the model get included
automatically but we don't want to expose a new user to a load of tricky code from
running the model within the notebook.

So - the notebook uses `code-block` entries to show the code and then contains
`code-cell` blocks with 'remove-cell' tags to run the actual model building in the
background. This cells will only execute successfully on systems with a bash shell.
-->

# Using the Virtual Ecosystem

This page provides a brief demonstration of the Virtual Ecosystem model in operation.
Once you have [installed the Virtual Ecosystem](./installing_ve.md), you should be able
to replicate this example on your own computer using the commands below.

## Example model data

The demonstration requires an [installation of the example data](./example_data.md)
provided with the Virtual Ecosystem package. If you have previously attempted to run
this example then the simulation will refuse to overwrite existing output files. You can
either:

* delete the existing example data folder and reinstall it,
* create a fresh installation using a different location, or
* create and use a new output directory with the existing example data folder.

It is worth re-reading the [example data page](./example_data.md) to get an overview of
the directory structure and the configuration and data files.

```{code-cell} ipython3
:tags: [remove-cell]

%%bash
# Remove any existing VE data directory in the execution directory
if [ -d ve_example ]; then
  rm -r ve_example
fi

export PYTHONUNBUFFERED=1
ve_run --install-example .
```

## The `ve_run` command

You've already used this command to install the example data but most of the options to
the `ve_run` command are used to run the simulation. The `--help` option can be used to
show the various arguments that can be used to set how a model runs:

`````{tab-set}
:sync-group: operating_system

````{tab-item} macOS/Linux
:sync: macoslinux

```{code-block} shell
ve_run --help
```
````

````{tab-item} Windows
:sync: windows

```{code-block} powershell
ve_run --help
```
````
`````

```{code-cell} ipython3
:tags: [remove-input]

%%bash
# Code to actually get the command line help
export PYTHONUNBUFFERED=1
ve_run --help
```

## Running the example model

The code below runs a simulation using the example data. The command uses the command
line options to set three things:

1. It points to the `config` directory containing the configuration files for the
   simulation: all the configuration files in this location will be compiled to
   configure the model.

1. It sets the output directory to be used by the simulation to `out`. You could create
   a new output directory (e.g. `out_test_2`) and change this to run a new simulation
   using the existing data.

1. It redirects the model logging to a file in the output directory, rather than
   printing it all to screen.

When the detailed logging is redirected to a file, the command generates a short
progress report to show the model running. This can be made shorter or completely muted
by using the `-q` argument: repeat the argument to remove more details (e.g. `-qq` or
`-qqq`).

`````{tab-set}
:sync-group: operating_system

````{tab-item} macOS/Linux
:sync: macoslinux

```{code-block} shell
ve_run /tmp/ve_example/config \
    --out /tmp/ve_example/out \
    --logfile /tmp/ve_example/out/logfile.log
```
````

````{tab-item} Windows
:sync: windows

```{code-block} powershell
ve_run C:\tmp\ve_example\config ,
    --out C:\tmp\ve_example\out ,
    --logfile C:\tmp\ve_example\logfile.log
```
````

`````

```{code-cell} ipython3
:tags: [remove-input]

%%script bash --err discarded_stderr
# Code to actually run the model in bash in the local directory, using the cell magic
# to swallow any standard error output warnings.
export PYTHONUNBUFFERED=1
ve_run ve_example/config \
    --out ve_example/out \
    --logfile ve_example/out/logfile.log

# Retain a truncated chunk of the log file locally to use within include directive
(head -n 20; echo "--- many lines omitted ---"; tail -n 20;) < \
ve_example/out/logfile.log > truncated_logfile.log
```

The log file is very long and shows the step by step process of running the model - it
is primarily used for diagnosing problems with the model. You can view a sample of the
contents in the dropdown below:

````{dropdown} Partial log output
```{literalinclude} truncated_logfile.log
```
````

## Looking at the results

The Virtual Ecosystem writes out a number of data files:

* `initial_state.nc`: A single compiled file of the initial input data.
* `all_continuous_data.nc`: An optional record of time series data of the variables
  updated at each time step.
* `final_state.nc`: The model data state at the end of the final step.

These files are written to the standard NetCDF data file format: below, we use the
`xarray` and `matplotlib` Python packages to load and visualise this data. You may need
to install these to replicate these outputs on your own computer.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import xarray

# Load the generated data files
initial_state = xarray.load_dataset("ve_example/out/initial_state.nc")
continuous_data = xarray.load_dataset("ve_example/out/all_continuous_data.nc")
final_state = xarray.load_dataset("ve_example/out/final_state.nc")
```

### Initial state and input data

The `initial_state.nc` file contains all of the data required to run the model. For some
variables - such as elevation and soil pH - this just provides the initial or constant
values across the grid cells to be calculated.  Other variables - such as precipitation
and temperature - provide a time series of data at a reference height above the canopy
that are used to that drive (or force) the behaviour of the model through time.

```{code-cell} ipython3
extent = [
    float(initial_state.x.min()),
    float(initial_state.x.max()),
    float(initial_state.y.min()),
    float(initial_state.y.max()),
]

# Make two side by side plots
fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(10, 5))

# Elevation
im1 = ax1.imshow(initial_state["elevation"].to_numpy().reshape((9, 9)), extent=extent)
ax1.set_title("Elevation (m)")
fig.colorbar(im1, ax=ax1, shrink=0.7)

# Initial soil carbon
im2 = ax2.imshow(initial_state["pH"].to_numpy().reshape((9, 9)), extent=extent)
ax2.set_title("Soil pH (-)")
fig.colorbar(im2, ax=ax2, shrink=0.7)

plt.tight_layout()
```

For some variables, it may be useful to visualise spatial structure in 3 dimensions.
The obvious candidate is elevation.

```{code-cell} ipython3
# Extract the elevation data for a 3D plot
top = initial_state["elevation"].to_numpy()
x = continuous_data["x"].to_numpy()
y = continuous_data["y"].to_numpy()
bottom = np.zeros_like(top)
width = depth = 90
```

```{code-cell} ipython3
# Make a 3D barplot of the elevation
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection="3d")
colors = plt.cm.turbo(top.flatten() / float(top.max()))

poly = ax.bar3d(x, y, bottom, width, depth, top, shade=True, color=colors)
ax.set_title("Elevation (m)")

cell_bounds = range(0, 811, 90)
ax.set_xticks(cell_bounds)
_ = ax.set_yticks(cell_bounds)
```

For other variables, such as air temperature and precipitation, the initial data
also provides time series data at reference height that are used to force the
simulation across the configured time period.

```{code-cell} ipython3
initial_state
```

```{code-cell} ipython3
# Make two side by side plots
fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 5))

# Air temperature
ax1.plot(initial_state["time_index"], initial_state["air_temperature_ref"])
ax1.set_title("Air temperature forcing across grid cells")
ax1.set_ylabel("Air temperature (°C)")
ax1.set_xlabel("Time step (months)")

# Precipitation
ax2.plot(initial_state["time_index"], initial_state["precipitation"])
ax2.set_title("Precipitation forcing across grid cells")
ax2.set_ylabel("Total monthly precipitation (mm)")
_ = ax2.set_xlabel("Time step (months)")
```

### Model outputs

The continuous data and final state datasets contain variables describing the
model state through the simulation process. These can be visualised as
spatial grids, individual time series within grid cells and as the three
dimensional structure of the vertical layers within the simulation.

#### Spatial data

Using the soil carbon  held as **mineral-associated organic matter** as an example:

```{code-cell} ipython3
# Make three side by side plots
fig, axes = plt.subplots(ncols=3, figsize=(10, 5))

# Plot start and end MAOM
val_min = continuous_data["soil_c_pool_maom"].min()
val_max = continuous_data["soil_c_pool_maom"].max()

# Plot 3 time slices
for idx, ax in zip([0, 10, 23], axes):
    im = ax.imshow(
        continuous_data["soil_c_pool_maom"][idx, :].to_numpy().reshape((9, 9)),
        extent=extent,
        vmax=val_max,
        vmin=val_min,
    )
    ax.set_title(f"Time step: {idx}")

fig.colorbar(im, ax=axes, orientation="vertical", shrink=0.5)
_ = plt.suptitle("Soil carbon: mineral-associated organic matter", y=0.78, x=0.45)
```

#### Temporal data

The plot below shows the **mineral-associated organic matter** data as a time series
showing the values in each cell across time.

```{code-cell} ipython3
plt.plot(continuous_data["time_index"], continuous_data["soil_c_pool_maom"])
plt.xlabel("Time step")
_ = plt.ylabel("Soil carbon as MAOM")
```

#### Vertical structure

The Virtual Ecosystem creates a vertical dimension that is used to record canopy
heights and soil depths across the grid.

```{code-cell} ipython3
# Extract the x and y location of the grid cell centres and layer heights
# for all observations at a given time step.
time_index = 0

x_3d = (
    continuous_data["x"]
    .broadcast_like(continuous_data["layer_heights"][time_index])
    .to_numpy()
    .flatten()
    + 45
)
y_3d = (
    continuous_data["y"]
    .broadcast_like(continuous_data["layer_heights"][time_index])
    .to_numpy()
    .flatten()
    + 45
)
z_3d = continuous_data["layer_heights"][time_index].to_numpy().flatten()

# Extract the air temperature for those points to colour the 3D data.
temp_vals = continuous_data["air_temperature"][time_index].to_numpy().flatten()
```

```{code-cell} ipython3
# Generate a 3 dimensional plot of layer heights showing temperature.

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection="3d")

cmap = plt.get_cmap("turbo")
paths = ax.scatter(x_3d, y_3d, z_3d, c=temp_vals, cmap=cmap)
fig.colorbar(
    paths,
    ax=ax,
    orientation="vertical",
    shrink=0.6,
    label="Air temperature (°C)",
    pad=0.1,
)

ax.set_xlabel("Easting (m)")
ax.set_ylabel("Northing (m)")
ax.set_zlabel("Layer height (m)")

ax.set_xticks(cell_bounds)
_ = ax.set_yticks(cell_bounds)
```

```{code-cell} ipython3
:tags: [remove-cell]

%%bash
# Remove the example directory
rm -r ve_example
```

```{code-cell} ipython3

```
