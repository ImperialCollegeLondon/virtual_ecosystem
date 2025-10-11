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
Plants model, complete with the default values for each of the configuration options.
Some of these default values are marked as placeholders: these are included to show the
structure of the configuration document but you will need to replace these placeholders
with actual values when you configure the model for your use.

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
import json
from virtual_ecosystem.models.plants.model_config import PlantsConfig
from IPython.display import display, Markdown

plants_config = PlantsConfig()

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"plants": json.loads(plants_config.model_dump_json())})
        + "```"
    )
)
```

### Plants model configuration details

The model configuration is defined in a set of Python data structures ("classes") that
set out the option names and their defaults.

* The TOML options directly under `[plants]` are set in the root
{class}`~virtual_ecosystem.models.plants.model_config.PlantsConfig` class.
* There are then two nested sections, each of which has its own configuration class:
  * The `[plants.community_data_export]` section sets whether plant cohort data is
    exported when the model runs and is defined by the
    {class}`~virtual_ecosystem.models.plants.model_config.PlantsExportConfig` class.
  * The `[plants.constants]` section defines constant values for the model and is set
    in the {class}`~virtual_ecosystem.models.plants.model_config.PlantsConstants`
    class.

The technical details of each class are shown below, which provides descriptions of each
option.

```{eval-rst}
.. autoclass:: virtual_ecosystem.models.plants.model_config.PlantsConfig
    :members:
    :exclude-members: model_config
```

```{eval-rst}
.. autoclass:: virtual_ecosystem.models.plants.model_config.PlantsExportConfig
    :members:
    :exclude-members: model_config
```

```{eval-rst}
.. autoclass:: virtual_ecosystem.models.plants.model_config.PlantsConstants
    :members:
    :exclude-members: model_config
```
