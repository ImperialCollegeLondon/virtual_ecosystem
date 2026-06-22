---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.4
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

# Abiotic model configuration

Configuration for the `abiotic` model includes three sections:

* An expanded set of constants values (`[abiotic.constants]`).
* A set of upper and lower bounds on the predicted microclimate variables
  (`[abiotic.bounds]`). This uses the same defaults as the [simple abiotic
  model](./abiotic_simple_config.md).
* The abiotic model uses the simple abiotic model to initialise the system state and
  also requires the simple constants used by that model (`[abiotic.simple_constants]`).

The last two sections are defined identically to the abiotic simple above and so follow
the structure for the [bounds](./abiotic_simple_config.md#abiotic-simple-bounds) and
[simple constants](./abiotic_simple_config.md#abiotic-simple-constants). The
only difference is that the should use the section names for the abiotic model.

## Abiotic constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.abiotic.model_config import AbioticConstants

config_object = AbioticConstants()
dump_config_toml("abiotic.constants", config_object)
model_config_to_deflist("abiotic.constants", config_object)
```
