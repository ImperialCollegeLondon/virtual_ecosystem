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

# Soil theory

The storage of carbon and cycling of nutrients within the soil are key processes we aim
to capture in the Virtual Ecosystem. This requires modelling soil specific processes, as
well as litter decay processes that occur both within the topsoil (e.g. for dead roots)
and within the above ground litter layer.

This broad domain gets split into two separate models. The [litter
model](./litter_theory.md) handles the breakdown of biomass that's still in an
identifiable form, both in the above ground litter layer as well as below ground. The
[soil model](./soil_theory.md) handles the processes that are specific to the soil,
i.e. it includes a much broader set of nutrient transformations.

The litter model is significantly simpler than the soil model. The biggest uncertainty
in this model are the rates at which different types of litter decay, and this can be
parameterised relatively well from commonly collected empirical data. The model
provides reasonably good estimates of the standing stocks of litter and the rates at
which carbon, nitrogen and phosphorus enter the soil.

In contrast, the soil model is more detailed in order to address deeper uncertainties
about nutrient transformations within the soil. The two biggest uncertainties for the
soil model are the long term fate of soil carbon and the impact of plant-microbe
interactions on uptake rates of nutrients by plants. We believe that the soil related
uncertainties are of greater consequence so have made the conscious choice to focus more
detailed modelling effort soil processes than the litter model. The biggest obstacle our
this model faces is data limitation, as soils are generally poorly characterised
compared to the other constituent parts of terrestrial ecosystems.

Most processes in the soil are effected by both the environmental temperature and the
soil moisture. The specific of how we have implemented these known effects are provided
[here](./environmental_links.md).

:::{admonition} Future directions 🔭

There are ecologically explicit extensions to the litter model - such as
modelling of litter microbial communities - that could increase the realism of
litter model, but the current model is expected to be sufficient in the short term.

:::
