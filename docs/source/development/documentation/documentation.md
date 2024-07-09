---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.2
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Documentation

This page describes the documentation of the `virtual_ecosystem` package, which is
hosted at:

[https://virtual-ecosystem.readthedocs.io](https://virtual-ecosystem.readthedocs.io)

The Virtual Ecosystem project is documented using the
[`sphinx`](https://www.sphinx-doc.org/en/master/) document generation system. This
includes documentation to:

* present the scientific background underpinning the `virtual_ecosystem` package,
* provide tutorials in using the package,
* demonstrate how to use the package components in more detail, and
* technical details of the application program interface (API) of the underlying code.

This broadly follows the [Diátaxis framework](https://diataxis.fr/), which
provides a useful breakdown of four distinct documentation modes (tutorial, how-to,
explanation and reference) and how to approach these with users in mind.

## Documentation guide

The `docs/source` directory contains the content and `sphinx` configuration to build the
package website. In addition to the top level index pages, we have three main content
directories:

* The `api` directory contains some simple stub files that are used to link to API
content generated from docstrings.
* The `development` directory contains details on code development, model design, and
documentation for the `virtual_ecosystem`.
* The `using_the_ve` directory contains user guides and code examples. It also contains
information on climate data download and pre-processing.

### MyST Markdown and notebooks

All of the documentation in `docs/source` uses [MyST
Markdown](https://myst-parser.readthedocs.io/en/latest/) rather than the
reStructuredText (`.rst`) format. Markdown is easier to write and read and the MyST
Markdown extension is a literate programming format that allows Markdown pages to be run
using Jupyter to generate dynamic content to show package use.

In addition to displaying static text, MyST Markdown can also be used to write notebook
files that contain code. We use the `myst-nb` extension to `sphinx` to allow those
notebooks to be run when the documentation is built, allowing code examples and
demonstrations to be included in the documentation.

For more information, see the [Jupyter notebooks](./jupyter_notebooks.md) page.

### Table of contents

We use the `sphinx_external_toc` package to maintain a table of contents for the
package. This table of contents is used to populate the site menu that appears on the
left of the webpage. The file `docs/source/_toc.yml` sets the structure of the table and
you will need to add new documentation files to this file for them to appear in the table.
The documentation build process will fail if it finds files in `docs/source` that are
not included in the table of contents!

### Docstrings

The `virtual_ecosystem` package uses docstrings written in the [Google
style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
This allows the function documentation to be stored alongside the code and it is included
in the documentation using the `sphinx` `autodoc` extension. See the code itself for
examples of the documentation formatting and typical content.

At the moment, we use the `autodoc` plugins for `sphinx` to convert docstrings to HTML
and build the online API documentation. Unfortunately, the `autodoc` package is
hard-coded to expect docstrings to use reStructuredText, which means that at the moment
**all docstrings have to be written in `rst` format**. At some point, we'd like to
switch away to using Markdown throughout, but for the moment look at the existing
docstrings to get examples of how the formatting differs.

```{admonition} More information

* The [docstring style](docstring_style.md) page includes some simple dummy code
  demonstrating the docstring style adopted  by the project. It is based on the [Google
  Python code
  style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).

* The [API generation](api_generation.md) page explains how to include the API
  for a new module in the project documentation. It also shows how the dummy code
  above is rendered as HTML by that process.
```

Also see the [section on using `doctests`](../contributing/code_testing.md) to include
and validate simple usage examples in docstrings.

### Referencing

Both the `docs/source` and docstrings uses the `sphinxcontrib-bibtex` package to support
citations. This uses Latex like citation keys in the documentation to insert references
and build a bibliography. The `sphinx` configuration in `docs/source/conf.py` provides a
custom Author/Year citation style. The reference library in `source/refs.bib` needs to
be kept up to date with the literature for the project.

The three common use cases are shown below using a couple of reference tags
(`campbell_introduction_2012` and `porporato_hydrologic_2003`) that are included
in the current [reference library](../../bibliography.md).

* Cite with date in parentheses (``{cite:t}`campbell_introduction_2012` ``): the model
  implemented in {cite:p}`campbell_introduction_2012`.
* Cite with reference(s) in parentheses
  (``{cite:p}`campbell_introduction_2012,porporato_hydrologic_2003` ``): using the P
  Model {cite:t}`campbell_introduction_2012,porporato_hydrologic_2003`.
* Cite as above but suppressing the parentheses to allow text before or after the
  citation (``(see {cite:alp}`campbell_introduction_2012` for details)``): the class
  implements the P Model (see {cite:alp}`campbell_introduction_2012` for details).

## Building the documentation

The `sphinx` package is used to build an HTML version of the package documentation
provided in `docs/source` and to include the API documentation provided in the code
docstrings. The `sphinx` building process requires some extra packages, but these are
included in the `docs` group in `pyproject.toml` and should be installed.

In order to build the package documentation, Jupyter needs to be able to associate the
documentation files with the Python environment managed by `poetry`. Fortunately, the
`poetry shell` and `poetry run` commands update the Jupyter kernel specifications so
that the `python3` kernel name points to the `poetry` environment. For example:

```bash
$ poetry run jupyter kernelspec list
Available kernels:
  ...
  python3        .../pyrealm-QywIOHcp-py3.10/share/jupyter/kernels/python3
```

In order to build the package documentation, the following command can then be used:

```bash
# Build docs using sphinx
cd docs
poetry run sphinx-build -M html source build -W --keep-going
```

Once that has completed, you can open the file `docs/build/html/index.html` to view the
locally built documentation in a browser.

The `sphinx` build process typically only runs on updated or changed files, to save time
when generating the documentation. If you want to completely rebuild the documentation
from scratch - if you are changing the table of contents or the links for example - then
the command `sphinx-build -M clean source build` can be used to remove the existing
built documentation before rebuilding as above.

## Quality assurance on documentation

The `pre-commit` configuration for the project includes two components that run quality
checking on documentation before it can be committed to GitHub. Neither of these attempt
to automatically fix documentation content: there is quite a lot of variation in
particular markup flavours and it is for too easy for autoformatters to break content
rather than fix it.

1. We have configured `ruff` to use the [`pydocstyle`
   ruleset](https://docs.astral.sh/ruff/rules/#pydocstyle-d), which checks for
   consistent documentation style and matches docstring contents to the function and
   method signatures.

1. We use the [`markdownlint-cli`](https://github.com/igorshubovych/markdownlint-cli)
   package to maintain quality on Markdown documents, including Jupyter notebooks. This
   applies a set of [quality checking
   rules](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md) to ensure
   common standards for Markdown content. Again, [comments in a Markdown
   document](https://github.com/DavidAnson/markdownlint#configuration)  can be used to
   suppress particular rules where appropriate.
