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

# Dynamic content using `jupyter` notebooks

Jupyter notebooks are a literate-programming format that allows text and runnable code
to be combined in a single document. They provide the ability to write documentation
pages that show the actual use of the `virtual_ecosystem` project along with outputs
and figures. They are also an invaluable tool for sharing design and troubleshooting
investigations. The [Jupyter project](https://jupyter.org/) provides many different
tools for working with notebooks, including the main `jupyter` program and a
browser-based notebook editor called `jupyter-lab`.

## Running `jupyter-lab`

The `poetry` virtual environment for `virtual_ecosystem` is already setup to
include `jupyter` and `jupyter-lab`, which is a browser-based application for editing
and running notebooks. As that virtual environment also has the `virtual_ecosystem`
package installed in development mode, a `jupyter` notebook running using this
enviroment will be able to import and use `virtual_ecosystem` code from the active
branch.

You can open `jupyter-lab` in a couple of ways. The simplest way is to use `poetry run
jupyter-lab` from the terminal, but you can also open the notebook within VS Code use
the Jupyter extension within VS Code. For this option, you will need to make sure that
VS Code is using the right python environment. The information you will need is
produced from `poetry`:

```zsh
% poetry env list --full-path
/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-ecosystem-Laomc1u4-py3.10
/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-ecosystem-Laomc1u4-py3.9 (Activated)
```

In VS Code, you then have to set the Python interpreter to the full path to the
currently active `poetry` virtual environment:

- View > Command Palette
- Type `interpreter` and find 'Python: Select Interpreter'
- Enter the full path from the `poetry env list` output.

## Jupyter kernel setup

The `jupyter` system can be setup to run notebooks in a number of different languages
and even different environments of the same language. Each option is setup as a
**kernel**, which is basically a pointer to a particular programming environment or
virtual environment. Each notebook should specify which kernel is to be used when
executing any code, and we need to ensure two things.

- The selected kernel needs to point to a virtual environment including the
  `virtual_ecosystem` package and dependencies, and
- the kernel should be available consistently across supported Python versions,
  developer machines, GitHub runners used for testing and also within the ReadTheDocs
  build environment.

Fortunately, when `poetry run` or `poetry shell` are used, the `jupyter` kernels are
updated to set the `python3` kernel to point to the active `poetry` virtual environment.
This ensures that Jupyter is invoked in the correct environment on all platforms. We can
check this by running the following, which shows the `python3` kernel pointing to the
`python3` kernel Virtual Ecosystem virtual environment: that path will vary between
machines but `poetry` will ensure that the link is set correctly.

```zsh
% poetry run jupyter kernelspec list
Available kernels:
  ir                 ../Jupyter/kernels/ir
  python3            ../pypoetry/virtualenvs/virtual-ecosystem-In6MogPy-py3.11/share/jupyter/kernels/python3
```

## Notebook formats

The default `jupyter` notebook format is the IPython Notebook (`.ipynb` suffix). This
file uses the JSON format to store the text and code and a whole bunch of other
metadata. However, the `.ipynb` format is not great for use in version control.  The
basic problem is that - although JSON files are text-based and are **technically**
human-readable:

- they contain irrelevant metadata - such as the number of times the notebook has been
  run - that will generate unneccessary commits.
- they can contain output binary data - such as images - that may also have arbitrary
  changes.

There is a really neat summary of the problem
[here](https://nextjournal.com/schmudde/how-to-version-control-jupyter), along with a
discussion of tools (e.g. `nbdime` and `nbmerge`) that help manage those changes in a
more coherent way.

However, a simpler solution is to use plain text instead of JSON: we  use notebooks
written in the plain text MyST Markdown format. The `jupytext` extension then allows
`jupyter` to load and run those files as notebooks. More broadly, `jupytext` is a really
powerful tool for managing the content of Jupyter notebooks, including using markdown
formats for notebooks.

## Using `jupytext`

The `jupytext` package works as an extension running within Jupyter Lab, adding some
commands to the `jupyter-lab` command palette, but also provides a command line tool
with some really useful features.

To be used with `jupytext`, MyST Markdown files need to include a YAML preamble at the
very top of the file. This is used to set document metadata about the Markdown variety
and also code execution data like the `jupyter` kernel. This is where the `python3`
kernel name is set.

```yaml
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
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---
```

If you already have a simple Markdown file then the commands below will insert this YAML
header:

```zsh
% jupytext --set-format md:myst simple.md
% jupytext --set-kernel python3  simple.md
```

There **is a downside** to using Markdown notebooks. The `.ipynb` format includes the
results of executing the notebook code, including Python code outputs and any graphics
created in the code. GitHub knows how to render those outputs, so the page you see on
GitHub includes the most recently committed code and graphics outputs. These outputs are
_not_ stored in Myst Markdown notebooks, so you only see the text and input code on
GitHub.

In summary:

- We only commit notebooks in MyST Markdown format
- Notebooks should use the `python3` kernel.
- GitHub will render the markdown and code cells correctly but none of the executed
  outputs will be shown.
- However, the notebooks **will be executed** by the `sphinx` documentation system,
  so fully rendered versions will be in the documentation website.
- You can develop notebook content locally using `jupyter-lab` and run it to get
  outputs. You can also run `sphinx` to see how a notebook is rendered in the
  documentation.
- The code in notebooks should not take a long time to run - these pages have to be
  built every time the documentation is built.

## Notebook quality checking

All Myst Markdown content in a notebook will be checked using `markdownlint` when the
file is committed to GitHub (see
[here](documentation.md#quality-assurance-on-documentation)). In addition, the following
tools may be useful:

### Using `black` with `jupytext`

Although `jupytext` does not do Markdown validation, it does allow `black` to be run on
the code cells, so that the format of code in notebooks can be automatically formatted.

```zsh
jupytext --pipe black my_markdown.md
```

Note that this **does not format** Python code that is simply included in a Markdown
cell - essentially text that is formatted as if it were Python code. It **only** formats
code within a Jupyter notebook `{code-cell}` or `{code-block}` section.
