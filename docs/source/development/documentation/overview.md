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

# Documentation system overview

The Virtual Ecosystem project is documented using the
[`sphinx`](https://www.sphinx-doc.org/en/master/) document generation system. This
includes documentation to:

* present the scientific background underpinning the `virtual_ecosystem` package,
* provide tutorials in using the package,
* demonstrate how to use the package components in more detail, and
* technical details of the application program interface (API) of the underlying code.

The project makes use of the following technologies within `sphinx` to structure the
documentation content and then render that content as the [project
website](https://virtual-ecosystem.readthedocs.io/).

## Sphinx build process

The documentation sources for `virtual_ecosystem` are stored in the `docs/source`
directory along with the `sphinx` configuration file `conf.py`. As noted below, the
`sphinx` build process will need to run and build Jupyter notebooks. This requires the
extra setup step shown below and [explained
here](jupyter_notebooks.md#jupyter-kernel-setup).

```zsh
poetry run python -m ipykernel install --user --name=vr_python3
```

The HTML documentation can be built from `docs` folder from the command line using the
commands below and will be built in  the `docs/build/html` directory. You can open
`docs/build/html/index.html` in a browser to see the documentation.

```sh
cd docs/
# Optionally, to rebuild from scratch
make clean
# To build the HTML pages
make html
```

The `make html` command will only build pages for files that have changed recently, and
it can sometimes be necessary to use `make clean` to remove all of the existing built
pages in order to rebuild  the documentation from scratch.

## MyST Markdown

All of the documentation apart from code docstrings is written using [MyST
Markdown](https://myst-parser.readthedocs.io/), which provides an extended set of
Markdown features. MyST also provides a parser for MyST Markdown content (`myst-parser`)
that allows pages written in MyST to be rendered in `sphinx`. It is a simple replacement
for the [RST format](https://docutils.sourceforge.io/rst.html).

## Jupyter Notebooks

In addition to static content, both 'tutorial' and 'how to' pages can contain actual
Python code demonstrating how to use the components of the `virtual_ecosystem` package.
These pages are written using [Jupyter](https://jupyter.org/) notebooks. These notebooks
can be worked on interactively by developers using [`jupyter`](https://jupyter.org/) and
can also be run by `sphinx`, using the [`myst-nb`
extension](https://myst-nb.readthedocs.io/), to automatically run the code in the
notebooks and then convert the content into web pages. We use the MyST Markdown format
for writing Jupyter notebooks, making use of the [`jupytext`
extension](https://jupytext.readthedocs.io/) to Jupyter.
  
```{admonition} More information
See the [Jupyter Notebooks](jupyter_notebooks.md) page for more information on using 
Jupyter notebooks in the documentation.
```

## Docstrings

All of the code provided in the `virtual_ecosystem` package should be extensively
documented in place using docstrings. We use the
[`napoleon` extension](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/) to
`sphinx` to provide a more legible docstring style. We also use the [`autodoc`
extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
to automatically generate API webpages directly from the docstrings. At present, it is
not easy to use MyST Markdown with the `autodoc` extension, so unfortunately
**docstrings must be written using RST format**.

```{admonition} More information

* The [docstring style](docstring_style.md) page includes a simple dummy code model
  demonstrating the docstring style adopted  by the project. It is based on the [Google
  Python code
  style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).

* The [API generation](api_generation.md) page explains how to include the API
  for a new module in the project documentation. It also shows how the dummy code model
  mentioned above is rendered as HTML by that process.
```

## Quality assurance on documentation

The `pre-commit` configuration for the project includes two components that run quality
checking on documentation before it can be committed to GitHub. Neither of these attempt
to automatically fix documentation content: there is quite a lot of variation in
particular markup flavours and it is for too easy for autoformatters to break content
rather than fix it.

1. We use the [`flake8-docstrings`
   extension](https://github.com/pycqa/flake8-docstrings) to `flake8` to validate the
   formatting of all docstrings in the code base. The `# noqa: error_code` comment can
   be used to suppress [docstring
   errors](https://www.pydocstyle.org/en/latest/error_codes.html#default-conventions)
   when appropriate.

1. We use the [`markdownlint-cli`](https://github.com/igorshubovych/markdownlint-cli)
   package to maintain quality on Markdown documents, including Jupyter notebooks. This
   applies a set of [quality checking
   rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md) to ensure
   common standards for Markdown content. Again, [comments in a Markdown
   document](https://github.com/DavidAnson/markdownlint#configuration)  can be used to
   suppress particular rules where appropriate.
