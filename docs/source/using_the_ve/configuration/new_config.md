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
mystnb:
  render_markdown_format: myst
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
from virtual_ecosystem.core.configuration import model_markdown_description
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

This section provides a description of each option set in the TOML document above. The
technical details of the validation classes used to check configuration documents can be
seen in the API documentation for the
{mod}`~virtual_ecosystem.models.plants.model_config` module.

The TOML document contains some root options, directly under the `[plants]` section, and
then two nested sections, setting the plant community data export options
(`[plants.community_data_export]`) and the constants values used in the model
(`[plants.constants]`).

```{code-cell} ipython3
:tags: [remove-input]

display(Markdown(model_markdown_description("plants", PlantsConfig)))
```
