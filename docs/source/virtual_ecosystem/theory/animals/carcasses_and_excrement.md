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

# Carcasses and excrement

Carcasses and excrement are critical components of litter, soil and animal models but
the fastest processes using these resources are carrion feeding and coprophagy by
animals. If carcasses and excrement are handled within the soil or litter model, new
inputs would only become available to animals at the end of each model update step. To
avoid the resulting lags in feeding responses to new carcass and excrement inputs, these
resources pools are handled within the animal model.

Each grid cell contains two pools recording carcass and excrement mass along with the
nitrogen and phosphorus stoichiometry of each resource. The total mass in each pool is
divided into two fractions:

* _scavengable_ mass that can be consumed by animals, and
* _decayed_ mass that will be added to the soil model at the next time step.

When biomass is added to either pool, the relative allocation to the scavengable
fraction is determined by the following equation

$$f_c = d / (s + d),$$

where $d$ is the rate at which the resource decays due to microbial activity and $s$ is
the rate at which animals discover and remove the resource.

:::{admonition} Future directions 🔭

* We currently only have one class of carcasses, but this may well be split into
  separate size classes at some point in the future.

* Both rates $d$ and $s$ are currently empirically derived constants. Scavenging rate
  ($s$) could be determined dynamically from the animal model but this would introduce
  parameterisation complexities that we don't want to tackle at present. Future
  extensions could allow the microbial decay rate ($d$) to vary environmentally (e.g.
  with temperature).

:::
