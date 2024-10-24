---
jupytext:
  formats: md:myst
  main_language: python
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
  version: 3.11.9
---

# Implementation of the core components

The first stages in a simulation are the configuration and initialisation of the core
components.

## The configuration

The model core and each science model has a set of configuration options that set how
the simulation is set up and how the science models run. These configuration options are
defined by **model schema files** that:

* document the required elements for configuring the core system or model,
* provide any default values, and
* implement basic validation.

When a simulation starts, the Virtual Ecosystem:

* Loads the user-provided configuration files and checks the file formats are valid.
* Collates the configuration settings into a single unified configuration.
* Loads the model schemas for the core and requested science models and uses this to
  validate the congfiguration.
* The validation process populates any missing options from the default values.
* The configuration validation will fail if:
  * Any options are duplicated within the configuration.
  * Any configuration settings are not valid, given the rules in the model schema.
  * Any required fields without defaults are not completed.

Further details can be found in the [configuration
documentation](../../using_the_ve/configuration/config.md).

## The grid

Next, the spatial structure of the simulation is configured as a [`Grid`
object](../../using_the_ve/configuration/grid.md) that defines the area, coordinate system
and geometry of the individual cells that will be used in the simulation. The grid is
also used to establish grid cell neighbours and connectivity across the spatial domain.

## The vertical layer structure

The vertical layer structure of the Virtual Ecosystem can be configured to change a
number of elements, including: the maximum number of canopy layers, the number and
depths of soil layers, and the maximum soil depth for microbial activity. The
[LayerStructure core component](virtual_ecosystem.core.core_components.LayerStructure)
resolves these settings into a vertical layer structure and provides the  model code
with indexing to extract particular layers from within vertically structured  data (see
{numref}`fig_layer_structure`).

:::{figure} ../../_static/images/layer_structure.svg
:name: fig_layer_structure
:alt: Vertical Layer Structure
:width: 650px

The vertical layer structure of a Virtual Ecosystem simulation. The main layer structure
is shown on the left, including variable numbers of filled canopy layers across grid
cells. The right hand side shows the most commonly used sets of layers within the
vertical layer structure. (click to zoom).
:::

## Loading and validation of input data

All of the variables required to initialise and run the simulation are then loaded into
an internal [`Data` object](../../using_the_ve/data/data.md). The model configuration
provides the location of the file containing each required variables and the Data object
is then used to load the data, checking that:

* the input files are valid and can be read, and
* that the data in files is congruent with the rest of the configuration, such as
  checking the dimensionality and shape of [core
  axes](../../using_the_ve/configuration/axes.md) like the spatial grid.

## Simulation timescale

The simulation runs between two dates with an update interval at which each science
model is recalculated. These values are defined in the `core` configuration and are
now validated to ensure that the start date, end date and update interval are sensible.

:::{note}
The calculation of simulation run time is currently not calendar aware and so timing
uses 12 equal length months and equal length years, ignoring leap years.
:::

## Core constants

The [core constants](../../api/core/constants.md) contains values that are shared across
the whole simulation. This includes:

* Global scientific constants, such as the gravitational constant $G$.
* Simulation constants that are either:
  * required to configure the core components, such as the maximum depth of biologically
    active soil, or
  * used by multiple science models and so are defined in a single location.
