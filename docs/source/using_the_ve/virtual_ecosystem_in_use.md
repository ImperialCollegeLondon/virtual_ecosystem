---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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
  version: 3.12.0rc3
---

# Exploring the Virtual Ecosystem outputs

The code below provides a walkthrough of some basic plots for the input and output of
the Virtual Ecosystem simulation.

## Run the simulation

Before exploring the outputs you will need to run the simulation using the example data
or your own input data. If you have already run the simulation and generated outtput
data, you can skip to the
[Initial state and input data](#initial-state-and-input-data) section below.

The following commands allow you to run the simulation from a Jupyter Notebook.
However, you can also run the script from the command line following the [Getting
Started](getting_started.md) instructions.

```{code-cell} ipython3
%%bash
# Remove any existing VE data directory in the /tmp/ directory
if [ -d /tmp/ve_example ]; then
  rm -r /tmp/ve_example
fi
```

```{code-cell} ipython3
%%bash
# Install the example data directory from the Virtual Ecosystem package
ve_run --install-example /tmp/
```

```{code-cell} ipython3
%%bash
ve_run /tmp/ve_example/config \
    --out /tmp/ve_example/out \
    --logfile /tmp/ve_example/out/logfile.log \
    --progress \
```

## Loading the data

Once the simulation is run you can load the data files into python.

The Virtual Ecosystem writes out a number of data files:

* `initial_state.nc`: A single compiled file of the initial input data.
* `all_continuous_data.nc`: An optional record of time series data of the variables
  updated at each time step.
* `final_state.nc`: The model data state at the end of the final step.

These files are written to the standard NetCDF data file format.

```{code-cell} ipython3
# Dependencies for the data and graphing
import pathlib

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import xarray
```

```{code-cell} ipython3
# Load the generated data files
initial_state = xarray.load_dataset("/tmp/ve_example/out/initial_state.nc")
continuous_data = xarray.load_dataset("/tmp/ve_example/out/all_continuous_data.nc")
final_state = xarray.load_dataset("/tmp/ve_example/out/final_state.nc")
```

```{code-cell} ipython3
# Print the name of each variable in the final state
for key in list(final_state.keys()):
    print(key)
```

+++ {"editable": true, "slideshow": {"slide_type": ""}, "tags": []}

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
plt.plot()
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
ax.set_yticks(cell_bounds)

plt.show()
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
ax2.set_xlabel("Time step (months)")

plt.plot()
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
plt.suptitle("Soil carbon: mineral-associated organic matter", y=0.78, x=0.45)

plt.plot()
```

#### Temporal data

The plot below shows the **mineral-associated organic matter** data as a time series
showing the values in each cell across time.

```{code-cell} ipython3
plt.plot(continuous_data["time_index"], continuous_data["soil_c_pool_maom"])
plt.xlabel("Time step")
plt.ylabel("Soil carbon as MAOM")

plt.plot()
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

plt.show(cell_bounds, cell_bounds)
```
