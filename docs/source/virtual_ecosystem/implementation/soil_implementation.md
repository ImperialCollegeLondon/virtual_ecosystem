---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.1
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

# The Soil Model implementation

## Model overview

TODO - This section needs to be properly populated

## Model variables

## Initialisation and update

The tables below show the variables that are required to initialise the soil model and
then update it at each time step.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        "SoilModel", ["vars_required_for_init", "vars_required_for_update"]
    ),
    raw=True,
)
```

## Generated variables

The soil model does not currently generate any variables. If that changes this section
will need to be updated.

## Updated variables

At each model step, the following variables are then updated.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
display_markdown(generate_variable_table("SoilModel", ["vars_updated"]), raw=True)
```
