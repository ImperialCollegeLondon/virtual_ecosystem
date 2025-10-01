---
jupytext:
  cell_metadata_filter: all,-trusted
  notebook_metadata_filter: settings,mystnb,language_info,execution
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
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

<!-- markdownlint-disable MD041-->

```{code-cell} ipython3
:tags: [remove-cell]

# This cell defines some Python tools used to render the page
from pathlib import Path
from importlib import resources
from IPython.display import display, Markdown
import xarray

# Path to the example_data resources
example_dir = resources.files("virtual_ecosystem.example_data")


def data_section_markdown(section: str, ds_path: Path) -> Markdown:
    """Data section Markdown generator

    This function generates markdown to display a section for a NetCDF data file in the
    example data directory. This is basically just a section heading, a short dataset
    description and then a simple table of data variables in a given NetCDF file.
    We could use the builtin IPython display of xarray  datasets but it is much more
    complex - we just want to show the data variables.

    It looks for "dataset_description" in the dataset attributes and then "description"
    and "units" in each data variables attributes, so generates the descriptions
    automatically from the current file contents.

    Args:
      ds_path: Path to the NetCDF dataset
    """

    ds = xarray.open_dataset(ds_path)

    # Build a list-table row for each data variable using the variable name, description
    # and units attributes and the variable dimensions
    var_list = []
    for var_name in ds.data_vars:
        var = ds[var_name]
        var_list.append(
            f"* - `{var_name}`\n  - {var.attrs.get('description', 'Missing attribute')}\n"
            f"  - {var.attrs.get('units', 'Missing attribute')}\n  - {var.dims}"
        )

    # Wrap the rows up in the list-table declaration
    var_rows = "\n".join(var_list)
    table = (
        f"```{{list-table}}\n:align: left\n\n* - Variable\n  - Description\n"
        f"  - Units\n  - Axes\n{var_rows}\n```"
    )

    ds_desc = ds.attrs.get("dataset_description", "Missing description")
    return Markdown("### " + section + "\n\n" + ds_desc + "\n\n" + table)
```

# Installing the example data

The Virtual Ecosystem model package includes example data to run a model. This page
provides:

* a guide to installing the example model data,
* an introduction to the example model file structure,
* an overview of the configuration and data files in the example model.

## Installing the example model data

The first step before running the example model is to install the data. You will need to
open a terminal (e.g. `bash` or Powershell) to run the installation command below. The
command creates a new directory called `ve_example` inside the directory you specify:

`````{tab-set}
:sync-group: operating_system

````{tab-item} macOS/Linux
:sync: macoslinux

```{code-block} shell
ve_run --install-example /install/path/
```
````

````{tab-item} Windows
:sync: windows

```{code-block} powershell
ve_run --install-example C:\install\path\
```
````
`````

The following sections describe the sub-directories in the example data and their
contents.

## Configuration files

The `config` directory contains configuration files that combine to provide a basic
complete configuration for the example data. The example configuration files are:

* The **`ve_run.toml`** configures the models to be used in the simulation and the order
  in which they are initialised and updated.

* The **`data_config.toml`** file configures the initial variables to be loaded and sets
  the paths to the source files providing those variables.

* The **`animal_functional_groups.toml`** file provides basic configuration for the
  `animal` model to set functional group definitions.

* The **`plant_config.toml`** file provides basic configuration for the
  `plants` model to set functional group definitions.

* The **`soil_microbial_groups.toml`** file provides basic configuration for the
  `soil` model to set microbial functional group definitions.

The dropdown boxes below reveal the contents of these files, so you can see what the
configuration format and example settings look like in practice.

````{dropdown} config/ve_run.toml
```{literalinclude} ../../../virtual_ecosystem/example_data/config/ve_run.toml
```
````

````{dropdown} config/data_config.toml
```{literalinclude} ../../../virtual_ecosystem/example_data/config/data_config.toml
```
````

````{dropdown} config/animal_functional_groups.toml
```{literalinclude} ../../../virtual_ecosystem/example_data/config/animal_functional_groups.toml
```
````

````{dropdown} config/plant_config.toml
```{literalinclude} ../../../virtual_ecosystem/example_data/config/plant_config.toml
```
````

````{dropdown} config/soil_microbial_groups.toml
```{literalinclude} ../../../virtual_ecosystem/example_data/config/soil_microbial_groups.toml
```
````

## Data files

```{warning}
All of these data files currently contain artificial data to test the program flow and
data handling of the Virtual Ecosystem simulation. Although some values are taken from
real source data, this is **not yet a meaningful real world example dataset**.
```

The `data` directory contains files containing the variables required to initialise the
model and then iterate over a time series.

### Array data

Most of the data required by the Virtual Ecosystem is organised on well defined axes and
so is imported into a central data store (see [the data object](./data/data.md) for
details). These input data are typically stored in NetCDF format files, which is a
format designed around array data on defined axes.

The data in the files then needs to be linked into the variables required by the Virtual
Ecosystem model. This is set in the configuration TOML files using the
``core.data.variable`` option, which identifies the NetCDF file containing a particular
variable. For example:

```toml
[[core.data.variable]]
file_path = "../data/example_litter_data.nc"
var_name = "litter_pool_above_metabolic"
```

The configuration setting needs to be provided which for every variable required by
a given simulation setup - see the example TOML contents above for more examples.

Within the Virtual Ecosystem, the data system is used to load and track these variables.
The system also checks that the axes of loaded data are congruent with the following
expected data axis definitions from the core model settings.

* The `x`, `y` and `cell_id` axes all record the spatial location of input cells. All
  cells have an `x` and `y` coordinate, but we also map cells onto a unique `cell_id`
  axis to make it easier to calculate values across cells.
* The `time_index` axis is used to store variables that vary in time through a
  simulation - the simulation updates iterate along this axis to change the conditions
  within the model.
* The `pft` axis is used to separate outputs within cells that come from different plant
  functional types.

The NetCDF files provided in the example data provide a long set of required variables and
the sections below show the data variables defined in each of the NetCDF files:

* the variable name used within model,
* a short description,
* the units for the variable, and
* a list of the axes that apply to the input variable.

```{code-cell} ipython3
:tags: [remove-input]

# Define the data file section names and paths
sections = (
    ("Elevation data", "data/example_elevation_data.nc"),
    ("Climate data", "data/example_climate_data.nc"),
    ("Soil data", "data/example_soil_data.nc"),
    ("Litter data", "data/example_litter_data.nc"),
    ("Plant data", "data/example_plant_data.nc"),
)

for section, dataset in sections:
    display(data_section_markdown(section, example_dir / dataset))
```

### Other data files

The `data` directory also provides some model specific files that are required to
initialise a simulation:

### Plant functional type definitions

The `plants_pft.csv` file is a CSV file that contains a set of plant functional types.
It defines a set of named PFTs and then provides a set of traits that define the
behaviour of individuals in each PFT.

### Initial plant cohort data

The `example_plant_cohorts.csv` file is a CSV file that defines the initial plant
communities found in each cell. It provides a set of rows identifying size structured
cohorts of PFTs occurring in each cell.

### Animal functional group definitions

The `animal_functional_groups.csv` file is a CSV file that defines the animal functional
groups to be used within the simulation. Each row defines a uniquely named functional
group along with key traits such as the adult body mass and diet.

<!--

Original text and partial tables, to be moved into NetCDF attributes

### Soil data

The `example_soil_data.nc` file provides:

```{list-table}
* - Variable
  - Name
  - Unit
  - Dims
* - pH
  - `pH`
  - unitless
  - XY
* - Soil clay fraction
  - `clay_fraction`
  - unitless
  - XY
* - Soil low molecular weight carbon pool
  - `soil_c_pool_lmwc`
  - kg C $\textrm{m}^{-3}$
  - XY
* - Soil mineral associated organic matter carbon pool
  - `soil_c_pool_maom`
  - kg C $\textrm{m}^{-3}$
  - XY
* - Soil microbial carbon pool
  - `soil_c_pool_microbe`
  - kg C $\textrm{m}^{-3}$
  - XY
* - Soil particulate organic matter carbon pool
  - `soil_c_pool_pom`
  - kg C $\textrm{m}^{-3}$
  - XY
* - Soil particulate organic matter enzyme pool
  - `soil_enzyme_pom`
  - kg C $\textrm{m}^{-3}$
  - XY
* - Soil mineral associated organic matter enzyme pool
  - `soil_enzyme_maom`
  - kg C $\textrm{m}^{-3}$
  - XY
```

This code creates a set of plausible values for the [soil
pools](../virtual_ecosystem/theory/soil/summary.md) that absolutely must be defined for
the {mod}`~virtual_ecosystem.models.soil.soil_model`  to function sensibly.

### Litter data

The `example_litter_data.nc` file provides:

```{list-table}
* - Variable
  - Name
  - Unit
  - Dims
* - above ground metabolic litter pools
  - `litter_pool_above_metabolic`
  - kg C $\textrm{m}^{-2}$
  - XY
* - above ground structural litter pools
  - `litter_pool_above_structural`
  - kg C $\textrm{m}^{-2}$
  - XY
* - woody litter pools
  - `litter_pool_woody`
  - kg C $\textrm{m}^{-2}$
  - XY
* - below ground metabolic litter pools
  - `litter_pool_below_metabolic`
  - kg C $\textrm{m}^{-2}$
  - XY
* - below ground structural litter pools
  - `litter_pool_below_structural`
  - kg C $\textrm{m}^{-2}$
  - XY
* - lignin proportion of above ground structural litter
  - `lignin_above_structural`
  - unitless
  - XY
* - lignin proportion of woody litter
  - `lignin_woody`
  - unitless
  - XY
* - lignin proportion of below ground structural litter
  - `lignin_below_structural`
  - unitless
  - XY
```

The generation script creates a set of plausible values for the [litter
pools](../virtual_ecosystem/theory/soil/litter_theory.md) that absolutely have to be
defined for the {mod}`~virtual_ecosystem.models.litter.litter_model` to function
sensibly.

### Plant data

The `example_plant_data.nc` file provides the following variables. Note that the plant
data introduces a new axis dimension for the cohorts of plant functional groups (C). In
this example data, a single cohort of each of the two configured functional groups is
added for each of the 81 grid cells, giving 162 entries along the cohort axis.

```{list-table}
* - Variable
  - Name
  - Unit
  - Dims
* - Cohort plant functional type
  - `plant_cohorts_pft`
  - string
  - C
* - Cohort diameter at breast height
  - `plant_cohorts_dbh`
  - m
  - C
* - Downward shortwave radiation
  - `downward_shortwave_radiation`
  - W m$^{-2}$
  - XYT
```
-->

## Output directory

The `out` directory is empty when the example data is installed and is simply used as a
location to store model outputs when the model is run.

## Additional directories

The example model data directory also contains:

* The `generation_scripts` directory contains Python scripts that are used to generate
   the contents of the `data` directory.

   You don't really need to look at these, but they provide simple recipes for creating
   or editing the example data files, so might be useful for tinkering with the example
   inputs. For any real model you want to fit, you will need to prepare actual [data
   inputs](./model_inputs.md) using data for your ecosystem.

* The `static_config` directory is empty and
