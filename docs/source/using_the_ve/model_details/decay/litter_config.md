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
  version: 3.11.9
mystnb:
  render_markdown_format: myst
---

# Litter model configuration

[See also the [configuration details](../../../api/models/litter/model_config.md)]

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for litter constants
.. currentmodule:: virtual_ecosystem.models.litter.model_config
```

The litter model only requires one configuration section:

* The litter model constants (`[litter.constants]`)

## Litter constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.litter.model_config import LitterConstants

config_object = LitterConstants()
dump_config_toml("litter.constants", config_object)
model_config_to_deflist("litter.constants", config_object)
```
