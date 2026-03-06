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

# Creating a site definition file

The notes given below were originally written by Dr. Lelavathy Samikan Mazilamani. They
are based on the script used to generate the Maliau site definition
[maliau_site_definition.py](https://github.com/ImperialCollegeLondon/ve_data_science/blob/main/data/sites/maliau_site_definition.py).

## General Notes

The site definition file specifies the spatial configuration used by the Virtual
Ecosystem (VE) model. It defines the model grid extent, projection, resolution, and
cell-centre coordinates required by all VE modules (abiotic, hydrology, soil, and
plants).

A site definition ensures that:

* All input datasets are aligned to a common spatial grid
* The model operates in a consistent projected coordinate system
* Grid resolution and spatial extent are explicitly defined
* Downstream preprocessing scripts (e.g., elevation, climate, soil, plant) can reference
  a single authoritative grid configuration

The site definition is exported as a TOML file, which can be read by other VE scripts to
ensure consistent spatial alignment across datasets.

The grid generation workflow typically:

* Defines the study area bounds (often starting from latitude/longitude in WGS84)
* Reprojects the bounds into an appropriate projected coordinate system (e.g., UTM)
* Defines a regular grid with a specified finer resolution (e.g., 90 m)
* Calculates lower-left and upper-right grid boundaries
* Generates cell centre coordinates
* Stores projection information, resolution, grid dimensions, and metadata
* Exports the configuration to a TOML file for reuse across the VE workflow

## Example: Maliau Basin

For the Maliau Basin configuration, the grid is defined in UTM Zone 50N (EPSG:32650) to
ensure accurate distance-based spatial representation. We want to generate a `TOML`
file, that contains the grid definition and acts as the authoritative spatial definition
for the Maliau Basin VE configuration. All subsequent preprocessing scripts (e.g.,
elevation, climate, soil, animal and plants) should use this file to ensure that
datasets are spatially aligned and compatible with the model grid.

The first thing to do is load the dependencies needed for this workflow.

```{code-cell} ipython3
import pyproj
import tomli_w
from shapely.geometry import box
from shapely.ops import transform
```

Then, reprojection functions between WGS84 and UTM50N should be defined.

```{code-cell} ipython3
wgs84_proj = pyproj.Proj("epsg:4326")
utm50N_proj = pyproj.Proj("epsg:32650")
wgs84_to_utm50N = pyproj.Transformer.from_proj(wgs84_proj, utm50N_proj)
utm50N_to_wgs84 = pyproj.Transformer.from_proj(utm50N_proj, wgs84_proj)
```

With these functions defined, the lat-long boundaries of the Maliau site can be
converted into the UTM50N coordinate system.

```{code-cell} ipython3
# Define boundary in lat-long
maliau_prototype_wgs84 = box(4.7170137, 116.9492683, 4.7569565, 116.9890846)
# Convert to UTM50N
maliau_prototype_utm50N = transform(wgs84_to_utm50N.transform, maliau_prototype_wgs84)
```

So, the bounds becomes

```{code-cell} ipython3
:tags: [remove-input]

maliau_prototype_utm50N.bounds
```

We now want to define a 50 x 50 grid at 90 m resolution (so ~ 4500m by 4500m). However,
the coordinate boundaries are awkward. What we want is a grid in UTM50N that uses actual
90m cells (not degree approximations, although at this spatial scale the approximation
is pretty good). To do this we round down the lower left corner to neat meter
coordinates and add a cell to maintain the approximate limits of the original grid.

```{note}
The process shown below was originally written for a 90 m grid resolution (i.e.
`res = 90`). However, it can be adjusted to any desired grid resolution (e.g., 100 m) by
modifying the `res` parameter.
```

```{code-cell} ipython3
ll_x_utm50N = 494300
ll_y_utm50N = 521300
cell_nx = 50
cell_ny = 50
res = 90
```

We then need to calculate the upper right bound for the neat meter coordinates.

```{code-cell} ipython3
ur_x_utm50N = ll_x_utm50N + cell_nx * res
ur_y_utm50N = ll_y_utm50N + cell_ny * res
```

These bounds should then be converted back to WGS84 to be used for reference and data
download purposes

```{code-cell} ipython3
maliau_grid_bounds_utm50N = box(ll_x_utm50N, ll_y_utm50N, ur_x_utm50N, ur_y_utm50N)
maliau_grid_bounds_wgs84 = transform(
    utm50N_to_wgs84.transform, maliau_grid_bounds_utm50N
)
```

The converted bounds are

```{code-cell} ipython3
:tags: [remove-input]

maliau_grid_bounds_wgs84.bounds
```

We now need to generate array of the cell centers

```{code-cell} ipython3
cell_x_centres = [(ll_x_utm50N + res / 2) + res * idx for idx in range(cell_nx)]
cell_y_centres = [(ll_y_utm50N + res / 2) + res * idx for idx in range(cell_ny)]
```

The full definition then gets combined into a single object

```{code-cell} ipython3
grid_definition = dict(
    epsg_code=32650,
    ll_x=ll_x_utm50N,
    ll_y=ll_y_utm50N,
    ur_x=ur_x_utm50N,
    ur_y=ur_y_utm50N,
    bounds=maliau_grid_bounds_utm50N.bounds,
    wgs84_bounds=maliau_grid_bounds_wgs84.bounds,
    cell_nx=cell_nx,
    cell_ny=cell_ny,
    cell_x_centres=cell_x_centres,
    cell_y_centres=cell_y_centres,
    res=res,
    core=dict(
        grid=dict(
            cell_area=res * res,
            cell_nx=cell_nx,
            cell_ny=cell_ny,
            grid_type="square",
            xoff=ll_x_utm50N + res / 2,
            yoff=ll_y_utm50N + res / 2,
        )
    ),
)
```

Finally, the grid definition should be saved (as a `TOML` file).

```{code-block} python
with open("maliau_grid_definition_90m.toml", "ab") as outfile:
    outfile.write(b"# Site definition file for Maliau Basin\n")
    tomli_w.dump(grid_definition, outfile)
```
