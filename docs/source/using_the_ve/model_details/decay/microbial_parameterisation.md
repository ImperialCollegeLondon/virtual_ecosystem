---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.6
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

# Defining microbial parametrisation

To parameterise the microbial community in the Soil model, you will need to define:

1. The parameters for the microbial functional groups used in the model.
1. The parameters for the different types of enzymes produced by the microbes.

The set of microbial functional groups and enzymes used in the model is **not** a choice
the user can make. Instead the user **must** provide parametrisation for each of the
required microbial groups and enzymes (these are described below).

## Microbial functional groups

Microbial groups in the soil model are defined by a set of parameter values that
describe the functional traits of each group. These functional group definitions need to
be stored in a CSV file, an example of this is shown below:

````{dropdown} example_microbial_groups.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/example_microbial_groups.csv
```
````

The [configuration of the soil model](./soil_config.md) must then provide the
`microbial_group_definition_path` setting with a path to the CSV file:

```toml
[soil]
microbial_group_definition_path = '/path/to/microbial_groups.csv'
```

The microbial group definitions file needs to include the following fields (the order
doesn't matter) defining the values for all microbial trait parameters:

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
# This cell generates a CSV table from the pydantic validation object for soil microbial
# functional group data, ensuring that the description stays up to date with the
# codebase.

import re

from IPython.display import display_markdown

from virtual_ecosystem.models.soil.microbial_groups import SoilMicrobe

rows = ["Field name,Description"]

for field_name, field in SoilMicrobe.model_fields.items():
    # Tidy descriptions: remove newlines, convert Sphinx maths, and quote
    # descriptions so commas are handled correctly by the CSV table.
    description = field.description or ""
    description = re.sub(r":math:`\\(.+)`", r"$\\\\\1$", description)
    description = re.sub(r":math:`(.+)`", r"$\1$", description)
    description = f'"{description.replace(chr(10), " ")}"'

    rows.append(f"`{field_name}`,{description}")

# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(rows)}\n```",
    raw=True,
)
```

## Enzyme classes

Enzyme classes in the soil model are defined by a set of parameter values that
describe the source of each class, the substrate they break down, and its various enzyme
kinetic parameters.

The enzyme class definitions for a simulation need to be stored in a CSV file: enzymes
are classified by source (fungal or bacteria) and by the substrate they break down
({term}`POM` or {term}`MAOM`). An enzyme needs to be defined for each combination of
source and substrate, an example of this is shown below:

````{dropdown} example_enzyme_parameters.csv
```{literalinclude} ../../../../../virtual_ecosystem/example_data/data/example_enzyme_parameters.csv
```
````

The [configuration of the soil model](./soil_config.md) must then provide the
`enzyme_class_definition_path` setting with a path to the CSV file:

```toml
[soil]
enzyme_class_definition_path = '/path/to/enzyme_parameters.csv'
```

The enzyme class definitions file needs to include the following fields (the order doesn't
matter) defining the values for all enzyme parameters:

```{code-cell} ipython3
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---
# This cell generates a CSV table from the pydantic validation object for
# soil enzyme data, ensuring that the description stays up to date with the
# codebase.

import re

from IPython.display import display_markdown

from virtual_ecosystem.models.soil.microbial_groups import SoilEnzyme

rows = ["Field name,Description"]

for field_name, field in SoilEnzyme.model_fields.items():
    # Tidy descriptions: remove newlines, convert Sphinx maths, and quote
    # descriptions so commas are handled correctly by the CSV table.
    description = field.description or ""
    description = re.sub(r":math:`\\(.+)`", r"$\\\\\1$", description)
    description = re.sub(r":math:`(.+)`", r"$\1$", description)
    description = f'"{description.replace(chr(10), " ")}"'

    rows.append(f"`{field_name}`,{description}")

# Display as markdown
display_markdown(
    f"```{{csv-table}}\n:header-rows: 1\n:quote: '\"'\n\n{"\n".join(rows)}\n```",
    raw=True,
)
```
