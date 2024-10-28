---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

# Virtual Ecosystem variables

All variables used by Virtual Ecosystem that represent a physical quantity and that are
either provided as input or produced as part of the simulation need to be registered
and documented.

## Known variables

The table below summarises the variables currently available in Virtual Ecosystem and
used by one or another of the existing models. It is followed by a more complete listing
showing which models use each variable and at what stage during the model initialisation
or update process. For instructions on how to add new variables visit the [API
documentation](../../api/core/variables.md) section.

```{code-cell} ipython3
---
mystnb:
  markdown_format: myst
tags: [remove-input]
---
from IPython.display import display_markdown
from var_generator import generate_all_variable_markdown

display_markdown(
    generate_all_variable_markdown(
        fields_to_display=["name", "description", "unit", "axis"],
        widths=[30, 40, 15, 15],
    ),
    raw=True,
)
```

## Detailed variable listing

```{eval-rst}
.. include:: ../../variables.rst
```
