# Using `jupyter` notebooks

We are going to be making extensive use of Jupyter notebooks as a format for providing
documentation and as a way of sharing design and troubleshooting notes.

## Running `jupyter-lab`

The `poetry` development environment is already setup to include `jupyter`, so you can
start a notebook browser either by using `jupyter-lab` in a terminal or simply by
opening the notebook within VS Code.

You will have to make sure that `jupyter` is using the `poetry` python virtual
environment: this has the development packages installed but also has the
`virtual_rainforest` package installed in development mode. For the terminal, this is
using `poetry run jupyter-lab`. In VS Code, you will have to set the Python interpreter
to the full path to the currently active `poetry` virtual environment:

- View > Command Palette
- Type `interpreter` and find 'Python: Select Interpreter'
- Enter the full path to the virtual environment:

```zsh
% poetry env list --full-path
/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-rainforest-Laomc1u4-py3.10
/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-rainforest-Laomc1u4-py3.9 (Activated)
```

## Notebook formats

The default `jupyter` notebook format is the IPython Notebook `.ipynb`. This file uses
the JSON format to store the text and code and a whole bunch of other metadata. The
`.ipynb` format is not great for use in version control. There is a really neat summary
of the problem and some solutions here:

[](https://nextjournal.com/schmudde/how-to-version-control-jupyter)

The basic problem is that - although JSON files are text-based and are **technically**
human-readable:

- they contain irrelevant metadata - such as the number of times the notebook has been
  run - that will generate unneccessary commits.
- they can contain output binary data - such as images - that may also have arbitrary
  changes.

While there are tools (e.g. `nbdime` and `nbmerge`) that help manage those changes in a
more coherent way, a simpler solution is simply \_not to include `.ipynb` files within
the repository at all. The `jupytext` tool is a really powerful way to manage the
content of Jupyter notebooks, including using markdown formats for notebooks and having
paired (`ipynb` and `md`) files.

There **is a cost to not storing `'ipynb`**: GitHub knows how to render the binary and
output contents of `ipynb` files, so that they display in GitHub. So:

- We only commit notebooks in markdown format.
- GitHub will render the markdown but the markdown format does not include executed
  outputs.
- The markdown files **will** be executed by the `sphinx` documentation system, so fully
  rendered versions will be in the documentation website.
- You can also simply launch your local copy in `jupyter-lab` and run it to get outputs.
  This is a problem if the computation is particularly slow, though.

## The `jupytext` package

The `jupytext` package is a separate package to `jupyter` but also works as an extension
to `jupyter-lab`, adding some commands to the `jupyter` command palette. Specifically,
you can use it from within `jupyter-lab` to pair `ipynb` notebooks with other formats. I
think you do **always have to have an `ipynb` version**.
