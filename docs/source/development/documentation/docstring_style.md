---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
---


# Docstring style for the Virtual Ecosystem package

The code below shows the docstring style that we have adopted for the Virtual
Ecosystem, including notes on why we have adopted particular docstring conventions.
We use the
[`autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
extension to `sphinx` to convert the docstrings in code modules into rendered HTML.

The results of using `autodoc` on the code below are shown [here](api_generation.md).

```{eval-rst}
.. include:: ./docstring_style.py
    :code: python
```
