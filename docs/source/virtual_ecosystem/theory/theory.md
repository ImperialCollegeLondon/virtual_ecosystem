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

# The theory of the Virtual Ecosystem

Ecosystems are complex systems that arise from the interplay between
[animals](./animal_theory.md),
[plants](./plant_theory.md),
and [soil microbes](./soil_theory.md) with their
[abiotic environment](./abiotic_theory.md). Many of these interactions are
non-linear and happen across a wide range of spatial and temporal scales which makes
ecosystem dynamics and emergent phenomena such as resilience to environmental stressors
challenging to understand and predict.

Despite rapid advancements in the development of detailed ecological models for
terrestrial ecosystems
{cite}`best_joint_2011,
clark_joint_2011,
harfoot_madingley_2014,
fatichi_mechanistic_2019,
geary_guide_2020`
, most models are limited in the breadth of processes being incorporated, and in the
diversity of users that might benefit from such models.

The general approach of the **Virtual Ecosystem** is to build on these model frameworks,
and to connect this prior work into a single modelling framework
that provides a fully mechanistic, fully integrated representation of key abiotic and
biotic processes that govern three key emergent properties of terrestrical ecosystems:
their stability, resilience, and sustainability.

We think we can replicate complex
ecosystem dynamics by focussing on the physiology of individual organisms and how
that’s influenced by the abiotic environment simulated based on first-principles physics
{numref}`ve_diagram`. The development serves the perspectives of a wide variety of users
and disciplines (see Box; Virtual Ecosystem Project Team 2024).

:::{figure} ../../_static/images/ve_diagram.svg
:name: ve_diagram
:alt: A diagram of the four domains in the Virtual Ecosystem
:scale: 70 %
:align: left

The key processes in the Virtual Ecosystem (from {cite:alp}`ewers_new_2024`).
The model aims to replicate ecosystem dynamics across four
ecological domains: plants, animals, soil, and the abiotic environment. These domains are
dynamically connected through the transfer of matter and energy.
:::

:::{card}User Stories
User stories serve as a project management tool that outlines the criteria for project
success. Below, we present example user stories as outlined in {cite}`ewers_new_2024`,
each equally vital in defining the success of a holistic ecosystem model. Fulfilling
the requirements of all user stories is necessary for the model to achieve complete
success.

Core user stories

* As a systems ecologist, I will be able to identify any core components and
sub-networks that exert strong control over the full system dynamics, so that I can
understand the mechanisms underlying ecosystem stability.
* As a disturbance ecologist, I will be able to track the attenuation of external
perturbations through the system, so that I can understand the mechanisms underlying
ecosystem resilience.
* As a sustainability scientist, I will be able to calculate the rate at which ecosystem
services are provided, so that I can make predictions about the long-term sustainability
of the ecosystem.
* As a biogeochemist, I will be able to track the flow of carbon, nitrogen and
phosphorus through the ecosystem, so that I can quantify elemental balances and
residence times.
* As a computational ecologist, I will have a modular tool that will allow me to
contrast different approaches to modelling ecosystems, so that I can better understand
the processes that drive ecosystem dynamics.
* As a community ecologist, I will be able to predict the spatial and temporal
distribution of biomass within and among functional groups, so that I can understand how
functional diversity is maintained.

Applied User stories

* As a hydrologist, I will be able to predict the frequency and magnitude of flood
events, so that I can design downstream flood defences.
* As a field ecologist, I will be able to identify knowledge gaps that significantly
impair our ability to predict ecosystem dynamics, so that I can prioritise future data
collection activities.
* As an applied ecologist, I will be able to examine the impact of climate change and
extreme climatic events on ecosystem dynamics, so that I can predict the likely future
state of the ecosystem.
* As a conservation biologist, I will be able to examine the impacts of invasion,
introduction and extinction on ecosystem dynamics, so that I can quantify the
importance of species-level conservation actions.
* As a climate scientist or carbon offsetting company, I will be able to examine the net
carbon sequestration potential of an ecosystem over decadal to centennial timescales.
* As a resource manager, I will be able to predict the outcomes of competing sets of
management strategies, so that I can make informed decisions about implementing
cost-effective management actions.

:::
