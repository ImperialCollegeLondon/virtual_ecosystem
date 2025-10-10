---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
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

# Configuration documentation example

## Plants Model

### Plant configuration TOML template

The TOML document below shows a template complete configuration definition for the
Plants model. Some of the values are marked as placeholders - these will need to be
replaced with actual values when you configure the model for your use.

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
import json
from virtual_ecosystem.models.plants.model_config import PlantsConfig
from IPython.display import display, Markdown

plants_config = PlantsConfig()

display(
    Markdown(
        "```toml\n" + tomli_w.dumps({"plants": plants_config.model_dump()}) + "```"
    )
)
```

### Plants model configuration details

The TOML document above maps onto the structure of the model configuration classes.
The root configuration is shown below, along with the definitions of the root level
settings.

```{eval-rst}
.. autoclass:: virtual_ecosystem.models.plants.model_config.PlantsConfig
    :autosummary:
    :members:
    :exclude-members: model_config
```

The `community_data_export` and `constants` sections of the configuration then map onto
the following two configuration classes.

```{eval-rst}
.. autoclass:: virtual_ecosystem.models.plants.model_config.PlantsExportConfig
    :autosummary:
    :members:
    :exclude-members: model_config
```

```{eval-rst}
.. autoclass:: virtual_ecosystem.models.plants.model_config.PlantsConstants
    :autosummary:
    :members:
    :exclude-members: model_config
```
