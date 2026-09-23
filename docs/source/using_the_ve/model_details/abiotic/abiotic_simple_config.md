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
  version: 3.11.9
mystnb:
  render_markdown_format: myst
---

# Simple abiotic model configuration

[See also the [configuration details](../../../api/models/abiotic_simple/model_config.md)]

Configuration for the `abiotic_simple` model includes two sections:

* A small set of constants values (`[abiotic_simple.constants]`), and
* A set of upper and lower bounds on the predicted microclimate variables
  (`[abiotic_simple.bounds]`).

In both cases, these default configuration will probably be enough to get an initial
configuration running for your simulation but may then need to be adjusted for your
study system.

## Abiotic simple constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleConstants

config_object = AbioticSimpleConstants()
dump_config_toml("abiotic_simple.constants", config_object)
model_config_to_deflist("abiotic_simple.constants", config_object)
```

## Abiotic simple bounds

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds

config_object = AbioticSimpleBounds()
dump_config_toml("abiotic_simple.constants", config_object)
model_config_to_deflist("abiotic_simple.constants", config_object)
```
