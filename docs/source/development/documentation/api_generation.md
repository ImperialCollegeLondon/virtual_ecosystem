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

This page shows how the docstring example in our [example docstring
sample](docstring_style.md) page can be rendered in the project web pages using the
`sphinx` [`autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
extension.

The docstring content of a module is converted to HTML by including a small Markdown
file in the `docs/source/api` folder. The source of this page provides an example and
can be seen following the 'Edit on GitHub' link at the top of the page to GitHub and
then clicking on the 'Raw' button to see the text.

The file has three components:

* The file will start with the `jupytext` YAML metadata, which just sets the Markdown
  format used in the file.
  
* A markdown header (`# A header`), which is shown as the page title. It is also used as
  the text for links to this page from the table of contents, unless a shorter name is
  provided in the `index.md` file. Typically, this header is the only markdown content
  in the file as the point of the docstrings is to keep all actual module documentation
  within the module code file.

* Lastly, an `automodule` instruction is included to instruct `autodoc` to render and
  insert content of the module docstrings.

The basic `automodule` declaration and options used are:

```{code-block} rst
.. automodule:: docstring_style
    :autosummary:
    :members:
    :special-members: __repr__
```

The `autosummary` option adds summary tables of the module objects below the module
docstring content and above the docstrings for those objects. The `members` option
includes all public module members in the documentation. These settings can be extended
from a [range of
options](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directive-automodule)
if required. Here, for example, the `special-members` option is used to make sure the
`__repr__` and its docstrings are included method. This option covers all 'dunder'
methods (`__special__`) of classes. Similarly, the `private-members` allows private
functions and methods (`_func` or `__func`) to be included in the API documentation if
needed.

Note that we **should not** include `:special-members: __init__` in the `automodule`
options: creating a class instance is documented by the class docstring.

Lastly, you need to check that the new Markdown file that creates the API documentation
is included in the API section of the sphinx `index.md` file.

````{admonition} Rendered content
All of the content below this box is rendered from the example docstring code. 
````

```{eval-rst}
.. automodule:: docstring_style
    :autosummary:
    :members:
    :special-members: __repr__
```
