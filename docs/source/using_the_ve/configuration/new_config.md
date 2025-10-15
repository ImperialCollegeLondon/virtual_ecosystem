---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.0rc0
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

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
import json
from virtual_ecosystem.core.configuration import ModelConfigHTMLTable
from IPython.display import display, Markdown, HTML
```

This page is a test of the new configuration system and documentation. It is a work in
progress but is still useful as a reference for the configuration of the Virtual
Ecosystem.

Some of the default values are marked as placeholders: these are included to show the
structure of the configuration document but you will need to replace these placeholders
with actual values when you configure the model for your use.

## Core Model

### Core configuration TOML template

The TOML document below shows a template complete configuration definition for the
core model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.model_config import CoreConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"core": CoreConfig().model_dump(mode="json")})
        + "```"
    )
)
```

### Core model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("core", CoreConfig).get_table()))
```

## Soil Model

### Soil configuration TOML template

The TOML document below shows a template complete configuration definition for the
soil model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"soil": SoilConfig().model_dump(mode="json")})
        + "```"
    )
)
```

### Soil model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("soil", SoilConfig).get_table()))
```

## Plants Model

### Plant configuration TOML template

The TOML document below shows a template complete configuration definition for the
Plants model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.plants.model_config import PlantsConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"plants": PlantsConfig().model_dump(mode="json")})
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

display(HTML(ModelConfigHTMLTable("plants", PlantsConfig).get_table()))
```

## Abiotic Model

### Abiotic configuration TOML template

The TOML document below shows a template complete configuration definition for the
abiotic model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic.model_config import AbioticConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"abiotic": AbioticConfig().model_dump(mode="json")})
        + "```"
    )
)
```

### Abiotic model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("abiotic", AbioticConfig).get_table()))
```

## Hydrology Model

### Hydrology configuration TOML template

The TOML document below shows a template complete configuration definition for the
hydrology model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.hydrology.model_config import HydrologyConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"hydrology": HydrologyConfig().model_dump(mode="json")})
        + "```"
    )
)
```

### Hydrology model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("hydrology", HydrologyConfig).get_table()))
```

## Litter Model

### Litter configuration TOML template

The TOML document below shows a template complete configuration definition for the
litter model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.litter.model_config import LitterConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"litter": LitterConfig().model_dump(mode="json")})
        + "```"
    )
)
```

### Litter model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("litter", LitterConfig).get_table()))
```

## Abiotic Simple Model

### Abiotic Simple configuration TOML template

The TOML document below shows a template complete configuration definition for the
abiotic simplae model, complete with the default values for each of the configuration
options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps(
            {"abiotic_simple": AbioticSimpleConfig().model_dump(mode="json")}
        )
        + "```"
    )
)
```

### Abiotic Simple model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("abiotic_simple", AbioticSimpleConfig).get_table()))
```

## Animal Model

### Animal configuration TOML template

The TOML document below shows a template complete configuration definition for the
animal model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.animal.model_config import AnimalConfig

display(
    Markdown(
        "```toml\n"
        + tomli_w.dumps({"animal": AnimalConfig().model_dump(mode="json")})
        + "```"
    )
)
```

### Animal model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(ModelConfigHTMLTable("animal", AnimalConfig).get_table()))
```
