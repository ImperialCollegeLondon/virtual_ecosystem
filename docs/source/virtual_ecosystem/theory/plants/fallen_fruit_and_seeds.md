---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.5
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

# Fallen fruit and seeds

Fallen seeds and fruit are tracked by the plant model as they are relevant to the
recruitment of new plant cohorts. Fallen seeds do not decay, they either get eaten by
animals or contribute to the recruitment of new cohorts.

:::{admonition} In progress 🛠️
Recruitment of new cohorts based on fallen seeds has not yet been implemented.
:::

## Fruit decay

The decay of fallen fruits occurs after animal consumption, this effectively
underestimates the amount of fruit decay. However, the alternative of fruit decaying
*before* animal consumption would overestimate the amount of fruit decay, potentially
leading to animal cohorts starving.

The fraction of the fallen fruit that decays (after animal consumption) is calculated as
follows:

$$f(t, T) = 1 - \exp(-k * \max(T,0) * t)$$

where $t$ is the simulation time step (in days), $T$ is the forest floor temperature (in
Celsius) and $k$ is the rate of fruit decay. This decay rate is expressed in units of
per "degree day" so that it captures the impact of *both* temperature and time on decay.
These degree days are calculated relative to zero degrees, so decay does not occur when
temperatures are below freezing.
