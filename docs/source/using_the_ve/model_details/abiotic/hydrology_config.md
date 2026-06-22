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

# Hydrology model configuration

[See also the [configuration details](../../../api/models/hydrology/model_config.md)]

The hydrology model requires two simple initialisation values and then a set of
hydrology constants one configuration section:

* the initial soil moisture,
* the initial groundwater saturation, and
* the hydrology model constants (`[hydrology.constants]`)

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.hydrology.model_config import HydrologyConfiguration

config_object = HydrologyConfiguration()
dump_config_toml("hydrology", config_object)
model_config_to_deflist("hydrology", config_object)
```
