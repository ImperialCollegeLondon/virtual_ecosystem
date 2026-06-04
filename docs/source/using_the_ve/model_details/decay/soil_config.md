---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.3
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

# Soil model configuration

[See also the [configuration details](../../../api/models/soil/model_config.md)]

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for soils config objects
.. currentmodule:: virtual_ecosystem.models.soil.model_config
```

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue
from typing import get_args
from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.soil.model_config import (
    REQUIRED_MICROBIAL_GROUPS,
    REQUIRED_ENZYMES,
)

glue("soil_required_enzymes", ", ".join([str(pair) for pair in REQUIRED_ENZYMES]))
glue("soil_required_groups", ", ".join([*get_args(REQUIRED_MICROBIAL_GROUPS)]))
```

The Soil model configuration is used to provide:

* Trait data on the microbial groups required for the soil model. The soil model
  requires a defined set of these groups, currently: {glue:text}`soil_required_groups`.

  These are currently configured directly in the TOML file using the
  `soil.microbial_group_definition` configuration option but this may move to loading
  from a CSV file using the `soil.microbial_group_definition_path` setting.

* Enzyme kinetics data for the enzymes produced by the taxonomic groups. Data is
  required for each pair of the higher taxonomic groups of microbes (fungi or bacteria)
  and the enzyme substrates targeted in the model (particulate organic matter or mineral
  associated organic matter): {glue:text}`soil_required_enzymes`

  These are currently configured directly in the TOML file using the
  `soil.enzyme_class_definition` configuration option but this may move to loading from
  a CSV file using the `soil.enzyme_class_definition_path` setting.

* A set of soil model constants using the `soil.constants` configuration.

## Soil microbial groups

The soil microbial groups are defined as a set of traits associated with each of the
required groups.

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilMicrobialGroup

config_object = SoilMicrobialGroup()
dump_config_toml("soil.microbial_group_definition", config_object)
model_config_to_deflist("soil.microbial_group_definition", config_object)
```

## Soil enzyme classes

The soil enzyme classes are defined as a set of traits associated with each pair of
higher taxon and substrate

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilEnzymeClass

config_object = SoilEnzymeClass()
dump_config_toml("soil.enzyme_class_definition", config_object)
model_config_to_deflist("soil.enzyme_class_definition", config_object)
```

## Soil constants

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.models.soil.model_config import SoilConstants

config_object = SoilConstants()
dump_config_toml("soil.constants", config_object)
model_config_to_deflist("soil.constants", config_object)
```
