---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
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
---

# The Virtual Ecosystem core configuration

The core configuration of the Virtual Ecosystem sets up the following parts of the
simulation, which are shared across all of the science models

* the [spatial grid](#the-spatial-grid),
* the [temporal extent and resolution](#the-temporal-extent-and-resolution),
* the [vertical layer structure](#the-vertical-layer-structure),
* the [core constants](#core-constants), and
* the [data output settings](#data-output-settings) for a simulation.

The core configuration section is also used to set the location of data input files for
required forcing variables for the simulation, but this section is discussed in the
[model inputs](./model_inputs.md) section.

## The spatial grid

## The temporal extent and resolution

## The vertical layer structure

## Core constants

## Data variable inputs

## Data output settings

```TOML
[core.constants]
standard_pressure = 101.325
standard_mole = 44.642
molar_heat_capacity_air = 29.19
gravity = 6.6743e-11
stefan_boltzmann_constant = 5.6703744191844314e-08
von_karmans_constant = 0.4
max_depth_of_microbial_activity = 0.25
meters_to_mm = 1000.0
molecular_weight_air = 28.96
gas_constant_water_vapour = 461.51
seconds_to_day = 86400.0
seconds_to_hour = 3600.0
characteristic_dimension_leaf = 0.01
specific_gas_constant_dry_air = 287.05
molecular_weight_ratio_water_to_dry_air = 0.622
conductance_to_resistance_conversion_factor = 40.9
density_water = 1000.0
fungal_fruiting_bodies_c_n_ratio = 10.0
fungal_fruiting_bodies_c_p_ratio = 75.0
fungal_fruiting_bodies_decay_rate = 0.013862943611198907

[core.grid]
grid_type = "square"
cell_area = 8100.0
cell_nx = 9
cell_ny = 9
xoff = -45.0
yoff = -45.0

[core.data_output_options]
save_initial_state = false
save_continuous_data = true
save_final_state = true
save_merged_config = true
out_path = "<DIRPATH_PLACEHOLDER>"
out_initial_file_name = "initial_state.nc"
out_folder_continuous = "."
out_continuous_file_name = "all_continuous_data.nc"
out_final_file_name = "final_state.nc"
out_merge_file_name = "ve_full_model_configuration.toml"

[core.layers]
soil_layers = [
    -0.25,
    -1.0,
]
canopy_layers = 10
above_canopy_height_offset = 2.0
subcanopy_layer_height = 1.5
surface_layer_height = 0.1

[core.timing]
start_date = "2013-01-01"
update_interval = "1 month"
run_length = "2 years"

[core.data]
variable = [
    { file_path = "<FILEPATH_PLACEHOLDER>", var_name = "variable_name_placeholder_one" },
    { file_path = "<FILEPATH_PLACEHOLDER>", var_name = "variable_name_placeholder_two" },
]

```
