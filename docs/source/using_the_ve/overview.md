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
  version: 3.12
---

# Using the Virtual Ecosystem

The Virtual Ecosystem model is a complex simulation with many moving parts. It can be
intimidating to get started with using the model, so these pages are intended to provide
a step-by-step guide to getting up and running. The main sections are:

1. Before you can run a Virtual Ecosystem simulation, you need to install the Python
   programming language and the Virtual Ecosystem Python package: see the section on
   [installing the Virtual Ecosystem](./installing_ve.md).

1. The Virtual Ecosystem package includes a simple example simulation. Before trying to
   setup your own model, [install the data to run the example model](./example_data.md)
   to learn about the structure of the files required to run a simulation in the Virtual
   Ecosystem.

1. Once you have installed the Virtual Ecosystem package and the example model data,
   you should be able to [run the example model](./virtual_ecosystem_in_use) to learn
   about how the model runs and learn about the model outputs.

1. When it comes to running your own models, you will need to understand how to provide
   the required inputs to the Virtual Ecosystem model for your own system. There are
   three main parts to setting up your own model.

   1. Defining the [configuration of the model core system](./core_configuration.md),
      which establishes the spatial and temporal context of your simulation

   1. [Configuring the science models](./science_model_configuration.md) that you want
      to include in your simulation.

   1. [Creating any data inputs](./model_data_inputs.md) required by your science models
      and then adding those to your configuration files.

## Advanced usage

Once you have your own model running, you can run experiments on the system.

* Develop new model configurations to run different scenarios within your virtual
  ecosystem. What happens if you remove a top predator? What happens with a 2°C increase
  in temperature?

* Run models with different permutations of particular parameters to explore the
  sensitivity of your simulation to changes in the parameterisation.

* Isolate a single component of the model to see how it responds to constant inputs
  through time using the [static model
  system](./virtual_ecosystem_in_static_mode.ipynb). Although this is primarily intended
  as a model development tool, it can be useful to understand the details of how
  different components of your model are behaving.
