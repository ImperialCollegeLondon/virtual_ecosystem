---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.2
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# The Litter Model implementation

## Required variables

The tables below show the variables that are required to initialise the litter model and
then update it at each time step.

```{code-cell}
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

from IPython.display import display_markdown
from var_generator import generate_variable_table

display_markdown(
    generate_variable_table(
        'LitterModel', 
        ['vars_required_for_init', 'vars_required_for_update']
    ), 
    raw=True
)
```

## Model overview

TODO - Add a high level overview of how this model works here, this can only be done
after the new flow is fixed

## Generated variables

The calculations described above result in the following variables being calculated and
saved within the model data store, and then updated

```{code-cell}
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'LitterModel', 
        ['vars_populated_by_first_update']
    ), 
    raw=True
)
```

## Updated variables

The table below shows the complete set of model variables that are updated at each model
step.

```{code-cell}
---
tags: [remove-input]
mystnb:
  markdown_format: myst
---

display_markdown(
    generate_variable_table(
        'LitterModel', 
        ['vars_updated']
    ), 
    raw=True
)
```
