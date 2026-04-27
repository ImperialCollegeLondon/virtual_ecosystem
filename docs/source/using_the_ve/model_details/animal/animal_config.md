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
  version: 3.11.9
mystnb:
  render_markdown_format: myst
---

# Animal model configuration

[See also the [configuration details](../../../api/models/animal/model_config.md)]

## Animal functional groups

The `animals.functional_group_definitions_path` configuration setting must point to a
CSV defining the animal functional groups to be used in a simulation. Each row in the
CSV must provide a unique group name and then a set of functional trait values for
that group. The file in the example data is a good template to use for preparing this
file. The required trait fields are:

"name", "taxa", "diet", "metabolic_type", "reproductive_environment",
"reproductive_type", "development_type", "development_status",
"offspring_functional_group", "excretion_type", "migration_type",
"vertical_occupancy", "birth_mass", "adult_mass"

## Animal Constants

```{eval-rst}
..
    This is needed to allow sphinx to resolve the :attr: links for animal constants
.. currentmodule:: virtual_ecosystem.models.animal.model_config
```

```{code-cell} ipython3
:tags: [remove-input]

from virtual_ecosystem.core.docutils import dump_config_toml, model_config_to_deflist
from virtual_ecosystem.models.animal.model_config import AnimalConstants

config_object = AnimalConstants()
dump_config_toml("animal.constants", config_object)
model_config_to_deflist("animal.constants", config_object)
```
