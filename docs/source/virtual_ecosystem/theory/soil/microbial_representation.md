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

# Microbial representation

This page provides a brief outline of our approach to representing soil microbes.

:::{admonition} In progress 🛠️

Our approach to representing microbial communities is not yet final. As such, this
page is currently very short and will be expanded significantly in future.

:::

Microbes are represented as carbon pools, each of which produces a set of enzymes. Each
microbial group will be represented by a separate pool, and will either produce a
different set of enzymes, or the same set in differing proportions.

Major decisions still need to be made in terms of which functional groups will be
included, and how exactly they will differ. So, the above is likely to be
revised/extended in the near future.
