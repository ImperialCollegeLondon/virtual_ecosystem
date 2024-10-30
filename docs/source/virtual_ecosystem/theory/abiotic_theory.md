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

# The abiotic environment

The abiotic component of the Virtual Ecosystem focuses on non-living environmental
factors that influence ecosystem dynamics. These factors encompass
[microclimate](./microclimate_theory.md) and [hydrology](./hydrology_theory.md)
processes, which are critical for understanding and predicting ecological
responses of organisms to various environmental conditions, interactions between
organisms that shape communities, and the geographical distribution of species.

The microclimate and hydrology components rely on first principles by incorporating
fundamental physical laws to simulate
[local radiation, energy, and carbon balance](./microclimate_theory.md#balancing-energy-water-and-carbon)
as well as [local](./hydrology_theory.md#local-water-balance) and
[catchment scale water cycle dynamics](./hydrology_theory.md#catchment-scale-water-balance)
to predict how microclimatic conditions and hydrological processes interact and evolve
over time.

:::{figure} ../../_static/images/abiotic_sketch.jpg
:name: abiotic_sketch
:alt: Abiotic sketch
:class: bg-primary
:width: 650px

The key processes in a terrestrial abiotic environment at the example of a
tropical rainforest. The system simultaneously balances carbon cycle (green), radiation
(orange), energy (red), water (blue), and momentum through turbulent transfer (black).
Copyright: Vivienne Groner.
:::
