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

# Hydrology

## Definition

In the context of the Virtual Ecosystem, hydrology is defined as the distribution and
movement of water both on and below the Earth's surface as well as through organisms.

Water is crucial in an ecosystem for several reasons. It is essential for the survival
of all living organisms, providing the medium for biochemical reactions and cellular
processes. Further, water plays a key role in many ecosystem processes such as
photosynthesis, nutrient cycling, and the decomposition of organic matter. Water
facilitates the movement of nutrients and minerals within the soil which enables plant
growth and maintains soil health. Aquatic environments, such as rivers, lakes, and
wetlands, provide habitats for a wide range of species which supports biodiversity.
Additionally, water bodies influence microclimates by regulating temperatures through
heat absorption and release.

## Implementation details

Hydrology only has a single implementation within the Virtual Ecosystem (the
`hydrology` model). Details of the actual equations used to simulate hydrology are
described in the [relevant section of the "How it works"
documentation](../implementation/hydrology_implementation.md)

We also provide [more detailed explanation](./hydrology_primer.md) of why hydrology
matters to ecological modelling, This page provides an overview of the [key
factors](./hydrology_primer.md#factors-affecting-hydrology) influencing the hydrology of
an ecosystem, the main processes that drive the hydrological cycle at [local
scale](./hydrology_primer.md#local-water-balance) and [catchment
scale](./hydrology_primer.md#catchment-scale-water-balance).
