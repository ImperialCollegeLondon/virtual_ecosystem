---
jupytext:
  formats: md:myst
  main_language: python
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
---

# Using the Virtual Ecosystem

The Virtual Ecosystem model is a complex simulation with many moving parts. It can be
intimidating to get started with using the model, so these pages are intended to provide
a step-by-step guide to getting up and running. The main sections are:

1. You need to install Python and the Virtual Ecosystem package to run a simulation so
   you first need to [install the Virtual Ecosystem](./installing_ve.md).

1. The Virtual Ecosystem package includes a simple example simulation. Before trying to
   setup your own model, [install the data to run the example model](./example_data.md)
   to learn about the structure of the files required to run a simulation in the Virtual
   Ecosystem.

1. Once you have installed the Virtual Ecosystem package and the example model data,
   you should be able to [run the example model](./virtual_ecosystem_in_use.md) to learn
   about how the model runs and learn about the model outputs.

1. When it comes to running your own models, you will need to understand how to generate
   the required inputs to the Virtual Ecosystem model for your own system. The [model
   inputs](./model_inputs) page provides a guide to the different ways in which you will
   need to configure the model and provide initial data.

1. Once you have your own model running, you can run experiments on the system. One
   example is isolating a component of the model to see how it responds to constant
   inputs through time. This is the the [static model
   system](./virtual_ecosystem_in_static_mode.md).
