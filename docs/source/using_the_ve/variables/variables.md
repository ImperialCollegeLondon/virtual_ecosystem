---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.2
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

* Note that the additional JS and sphinx targets the full path of the page, so if this
  page is moved then conf.py will need to be updated.
-->

# Virtual Ecosystem array variables

The table below list all of the variables that are stored centrally within Virtual
Ecosystem simulations. These variables are arrays of data that are structured using the
[core axes of the simulation](../../using_the_ve/axes.md).

Each science model declares which of these variables are used when the model runs. There
are five different usage cases, identifying sets of variables that are:

* required to setup a model,
* populated when the model is set up,
* required when the model updates,
* populated when the model first updates, and
* updated by the model at every time step.

The variables required to set up a model can be further split into two classes:

* **Input variables**: these are the variables that you will need to provide through the
  [model data
  configuration](../running_ve_with_your_own_data.md#configuring-array-data-inputs) for
  a simulation. These variables are shown in bold in the table below.
* **Calculated variables**: these variables are calculated  from the input variables by
  the setup process of another model.

```{code-cell} ipython3
:tags: [remove-input]

from IPython.display import display_html

from virtual_ecosystem.core.docutils import variable_table

display_html(variable_table(), raw=True)
```
