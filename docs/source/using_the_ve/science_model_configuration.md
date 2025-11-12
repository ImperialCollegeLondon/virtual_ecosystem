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

# Configuring science models in the Virtual Ecosystem

```{code-cell} ipython3
:tags: [remove-input]

import tomli_w
import json
from config_display import (
    dump_config_toml,
    model_config_to_deflist,
)
from virtual_ecosystem.core.configuration import Configuration
from virtual_ecosystem.core.registry import get_model_configuration_class
from IPython.display import display, Markdown, HTML
from importlib import import_module
```

Each of the science models in the Virtual Ecosystem has its own configuration section.
For some models, the configuration may only consist of a set of model-specific constant
values. In other cases, the science model may require additional configuration details,
such as paths to data files providing configuration data or initialisation values.

In all cases, your TOML configuration files only need to specify values that do not have
a default value (typically file paths) or where you want to change a default. To include
a model using only the default values, it is enough just to include the model name as a
header section. So for example:

```{code-block} toml
# This is sufficient to configure the abiotic model with default settings
[abiotic]
```

## Simple abiotic model

Configuration for the `abiotic_simple` model includes two sections:

* A small set of constants values (`[abiotic_simple.constants]`), and
* A set of upper and lower bounds on the predicted microclimate variables
  (`[abiotic_simple.bounds]`).

In both cases, these default configuration will probably be enough to get an initial
configuration running for your simulation but may then need to be adjusted for your
study system.

### Abiotic simple constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleConstants

dump_config_toml("abiotic_simple.constants", AbioticSimpleConstants)
model_config_to_deflist("abiotic_simple.constants", AbioticSimpleConstants)
```

### Abiotic simple bounds

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleBounds

dump_config_toml("abiotic_simple.constants", AbioticSimpleBounds)
model_config_to_deflist("abiotic_simple.constants", AbioticSimpleBounds)
```

## Abiotic model

Configuration for the `abiotic` model includes three sections:

* An expanded set of constants values (`[abiotic.constants]`).
* A set of upper and lower bounds on the predicted microclimate variables
  (`[abiotic.bounds]`). This uses the same defaults as the simple abiotic model.
* The abiotic model uses the simple abiotic model to initialise the system state and
  also requires the simple constants used by that model (`[abiotic.simple_constants`).

The last two sections are defined identically to the abiotic simple above and so follow
the structure for the [bounds](#abiotic-simple-bounds) and [simple
constants](#abiotic-simple-constants) shown above. The only difference is that the
should use the section names for the abiotic model.

### Abiotic constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.abiotic.model_config import AbioticConstants

dump_config_toml("abiotic.constants", AbioticConstants)
model_config_to_deflist("abiotic.constants", AbioticConstants)
```

## Litter model

The litter model only requires one configuration section:

* The litter model constants (`[litter.constants]`)

### Litter constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.litter.model_config import LitterConstants

dump_config_toml("litter.constants", LitterConstants)
model_config_to_deflist("litter.constants", LitterConstants)
```

## Hydrology model

The hydrology model requires two simple initialisation values and then a set of
hydrology constants one configuration section:

* the initial soil moisture,
* the initial groundwater saturation, and
* the hydrology model constants (`[hydrology.constants]`)

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.hydrology.model_config import HydrologyConfiguration

dump_config_toml("hydrology", HydrologyConfiguration)
model_config_to_deflist("hydrology", HydrologyConfiguration)
```

## Soil model

## Plants model

## Animal model
