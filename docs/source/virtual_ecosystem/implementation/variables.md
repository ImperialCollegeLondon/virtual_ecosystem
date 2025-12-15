---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0.dev0
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

<!-- Page build notes:

The variables page build is a bit complex:

* The code cell below calls a function that loads the data_variables.TOML file to get
  a complete list of variables and then _also_ checks each of the models to extend that
  data to include which variables are used at which stage for each model. That data is
  wrapped into a table for display using the DataTables framework. The
  Responsive extension to that framework allows column classes to set whether a column
  is always shown, always wrapped into a dropdown row child or never shown (but still
  searchable). The function also adds some checkboxes that are used to filter the
  variables by model and usage and returns a chunk of HTML that is then included in the
  notebook _as_ HTML.

* When the page is built, the `sphinx` app is used to add the required JS and CSS files
  for DataTables, and also some custom JS (`_static/js/variables_table.js`) to hook the
  table up to the DataTables framework and to power the checkboxes.
-->

```{code-cell} ipython3
:tags: [remove-input]

from IPython.display import display_html
from variable_table import variable_table

display_html(variable_table(), raw=True)
```
