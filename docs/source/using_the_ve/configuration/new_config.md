---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Configuration documentation example

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
import json
from virtual_ecosystem.core.configuration import model_config_to_html, Configuration
from virtual_ecosystem.core.registry import get_model_configuration_class
from IPython.display import display, Markdown, HTML
from importlib import import_module


def get_config_class(module_name: str) -> Configuration:
    """Helper function to get the configuration model for a module.

    Returns a tuple of the module short name and configuration class.
    """

    # Get the config class for the module
    short_name = module_name.split(".")[-1]
    config_class = get_model_configuration_class(module_name, short_name)

    return module_name.split(".")[-1], config_class


def dump_config_toml(name: str, config_class: Configuration) -> None:

    # Render the config defaults as TOML
    display(
        Markdown(
            "```toml\n"
            + tomli_w.dumps({name: config_class().model_dump(mode="json")})
            + "```"
        )
    )
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

config_setup = get_config_class("virtual_ecosystem.core")
dump_config_toml(*config_setup)
```

### Core model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```

## Soil Model

### Soil configuration TOML template

The TOML document below shows a template complete configuration definition for the
soil model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.soil")
dump_config_toml(*config_setup)
```

### Soil model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```

## Plants Model

### Plant configuration TOML template

The TOML document below shows a template complete configuration definition for the
Plants model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.plants")
dump_config_toml(*config_setup)
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

display(HTML(model_config_to_html(*config_setup)))
```

## Abiotic Model

### Abiotic configuration TOML template

The TOML document below shows a template complete configuration definition for the
abiotic model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.abiotic")
dump_config_toml(*config_setup)
```

### Abiotic model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```

## Hydrology Model

### Hydrology configuration TOML template

The TOML document below shows a template complete configuration definition for the
hydrology model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.hydrology")
dump_config_toml(*config_setup)
```

### Hydrology model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```

## Litter Model

### Litter configuration TOML template

The TOML document below shows a template complete configuration definition for the
litter model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.litter")
dump_config_toml(*config_setup)
```

### Litter model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```

## Abiotic Simple Model

### Abiotic Simple configuration TOML template

The TOML document below shows a template complete configuration definition for the
abiotic simplae model, complete with the default values for each of the configuration
options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.abiotic_simple")
dump_config_toml(*config_setup)
```

### Abiotic Simple model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```

## Animal Model

### Animal configuration TOML template

The TOML document below shows a template complete configuration definition for the
animal model, complete with the default values for each of the configuration options.

```{code-cell} ipython3
:tags: [remove-input]

config_setup = get_config_class("virtual_ecosystem.models.animal")
dump_config_toml(*config_setup)
```

### Animal model configuration details

This section provides a description of each option set in the TOML document above.

```{code-cell} ipython3
:tags: [remove-input]

display(HTML(model_config_to_html(*config_setup)))
```
