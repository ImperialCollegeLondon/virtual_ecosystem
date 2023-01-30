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

# Generating API documentation from docstrings

````{admonition} Rendering docstrings in the project web pages
This page shows how the docstring example in our 
[example docstring sample](docstring_style.md) page can be rendered in the project web 
pages using the `sphinx` 
[`autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
extension. 

The docstring content of a module is converted to HTML by including a small Markdown
file in the `docs/source/api` folder. Typically, the file will start with the
`jupytext` YAML metadata, then a markdown title and then an `automodule` instruction to
insert all of the rest of the page content from the module docstrings. This text source
of this page provides an example and can be seen using the 'View page source' link at 
the top of the page.

The basic `automodule` declaration and options used are:

```{code-block} rst
.. automodule:: docstring_style
    :autosummary:
    :members:
    :special-members: __repr__
```

The `autosummary` option adds summary tables of the module objects below the module
docstring content and above the docstrings for those objects. The `members` option
includes all public module members in the documentation. These options can be extended 
to include other members if required. Here, the `special-members` option is used here
to document the `__repr__` method. 

Note that we **do not** include `__init__` in documentation: creating a class instance
is documented in the class docstring.

All of the content below this box is rendered from the example docstring code. 
Obviously, this explanatory box should be removed from real API pages.
````

```{eval-rst}
.. automodule:: docstring_style
    :autosummary:
    :members:
    :special-members: __repr__
```
