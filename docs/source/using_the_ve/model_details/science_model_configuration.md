---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
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
mystnb:
  render_markdown_format: myst
---

# Science model configuration in the Virtual Ecosystem

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
from virtual_ecosystem.core.configuration import Configuration
from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.core.registry import get_model_configuration_class
from IPython.display import display, Markdown, HTML
from importlib import import_module
```

Each of the science models in the Virtual Ecosystem has its own configuration section.
For some models, the configuration may only consist of a set of model-specific constant
values. In other cases, the science model may require additional configuration details,
such as paths to data files providing configuration data or initialisation values.

```{admonition} Data configuration
:class: important

This page specifically describes the model specific configuration settings. In addition,
you will need to configure the sources of the gridded array data providing the data
variables required by each model:

* The variables required for each model are described in the [model implementation
  pages](../../virtual_ecosystem/implementation/how_it_works.md#science-models).
* A complete list of variables can be found in the [variables description
  page](../variables/variables.md).

```

In all cases, your TOML configuration files only need to specify values that do not have
a default value (typically file paths) or where you want to change a default. To include
a model using only the default values, it is enough just to include the model name as a
header section. So for example:

```{code-block} toml
# This is sufficient to configure the abiotic model with default settings
[abiotic]
```

## Validation of science model configurations

As with the core configuration, each science model in the Virtual Ecosystem has a
defined set of configuration options that are built into the definition of the model.
Those options will also have specific validation settings that are used to check that
the setting values that you provide are appropriate for the model: these constraints are
automatically enforced when your configuration files are loaded. If configuration data
contains invalid values, then the simulation will exit and the log will contain a
detailed breakdown of any configuration validation issues.

The details of the validation constraints for a particular model configuration are
described in the documentation of the model configuration. These are linked in each
section below - these pages are part of the API (application programming interface) so
are a bit more technical but provide the a complete description of the model settings.

## Animal model

[See also the [configuration details](../../api/models/animal/model_config.md)]

### Animal functional groups

The `animals.functional_group_definitions_path` configuration setting must point to a
CSV defining the animal functional groups to be used in a simulation. Each row in the
CSV must provide a unique group name and then a set of functional trait values for
that group. The file in the example data is a good template to use for preparing this
file. The required trait fields are:

"name", "taxa", "diet", "metabolic_type", "reproductive_environment",
"reproductive_type", "development_type", "development_status",
"offspring_functional_group", "excretion_type", "migration_type",
"vertical_occupancy", "birth_mass", "adult_mass"

### Animal Constants

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for animal constants
.. currentmodule:: virtual_ecosystem.models.animal.model_config
```

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.animal.model_config import AnimalConstants

config_object = AnimalConstants()
dump_config_toml("animal.constants", config_object)
model_config_to_deflist("animal.constants", config_object)
```
