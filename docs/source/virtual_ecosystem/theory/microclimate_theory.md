---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.2
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

# Microclimate

## Definition

Microclimates are defined as the local climate conditions that organisms and ecosystems
are exposed to. In terrestrial ecosystems, microclimates often deviate strongly from the
climate representative of a large geographic region, the macroclimate
{cite}`kemppinen_microclimate_2024`. For example, the temperature directly above a
rainforest canopy might be modulated due to small scale variations in topography and
aspect. The temperature above the canopy is typically several degrees higher than near
the surface, the surface under a dense canopy tends to be cooler than unshaded surface
spots, and temperatures generally decrease with elevation.

Many ecosystems have a high spatial variability of microclimates providing suitable
habitats for a diverse range of species. Scales of microclimates typically range between
0.1-100 m horizontally, 10-100 m vertically, and seconds to minutes temporally
{cite}`bramer_chapter_2018`.

## Implementation details

Two alternative microclimate implementations exist in the Virtual Ecosystem the [simple
abiotic model](../implementation/abiotic_simple_implementation.md) and the
[process-based abiotic model](../implementation/abiotic_implementation.md). Details of
the actual equations used to simulate microclimate are to be found there.

We also provide [more detailed explanation](./microclimate_primer.md) of what
microclimate is and why it matters to ecological modelling, including description of the
[key factors](./microclimate_primer.md#factors-affecting-microclimate) influencing the
microclimate of an ecosystem and the [main
processes](./microclimate_primer.md#balancing-energy-water-and-carbon) that drive the
energy, carbon, and water cycle.
