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

# Using `jupyter` notebooks

We are going to be making extensive use of Jupyter notebooks as a format for providing
documentation and as a way of sharing design and troubleshooting notes.

## Running `jupyter-lab`

The `poetry` development environment is already setup to include `jupyter`, so you can
start a notebook browser either by using `jupyter-lab` in a terminal or simply by
opening the notebook within VS Code and letting the Jupyter extension within VS Code
handle it all.

You do **have to make sure that `jupyter` is using the `poetry` python virtual
environment**: this venv has all the development packages installed and also has the
`virtual_rainforest` package installed in development mode, so that it can be used in
code cells. The information you will need is produced from `poetry`:

```zsh
% poetry env list --full-path
/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-rainforest-Laomc1u4-py3.10
/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-rainforest-Laomc1u4-py3.9 (Activated)
```

### VS Code

In VS Code, you have to set the Python interpreter to the full path to the currently
active `poetry` virtual environment:

- View > Command Palette
- Type `interpreter` and find 'Python: Select Interpreter'
- Enter the full path from the `poetry env list` output.

### Jupyter Lab

There is a good discussion of this
[here](https://janakiev.com/blog/jupyter-virtual-envs/) but the take home is that you
need to add a kernel specification to your local Jupyter installation that points to the
venv created by `poetry`.

```zsh
poetry run python -m ipykernel install --user --name=vr_python3
```

When you run `jupyter-lab` now, you should be able to select the `vr_python3` kernel to
run the code cells. That command is doing some subtle and important things:

- Python is being run in the active `poetry` virtual environment (`poetry run`).
- The active `python` environment is then being installed as a kernel specification.
- It is being installed into a location that is available for the user from anywhere
  they run `jupyter` (`--user`).
- It is being installed with the name `vr_python3` (`--name vr_python3`).

The choice of kernel name is **important** because it is included in IPython notebooks
and we want it to be stable. The kernel name:

- needs to point to a virtual environment including the `virtual_rainforest` package
  and dependencies, and
- should be consistent across supported Python versions and developer machines.

The options are:

- By default, it would be installed as `python3`, which is way too generic.
- The `poetry` venv name contains a hash (e.g. `Laomc1u4`) which uniquely identifies the
  project directory and helps `poetry` track the project-specific venvs. This is a
  **spectacularly bad** kernel name because files would change as they are run on
  different developer machines.
- Using the `vr_python3` name is hopefully unique and should be a stable pointer to a
  venv that includes  the `virtual_rainforest` package and dependencies.

Just to point to the gory details, there is now a `kernelspec` called `vr_python3`. That
is just a pointer to a JSON file that points to the machine-specific venv location.

```zsh
% jupyter kernelspec list
Available kernels:
  ir            /Users/dorme/Library/Jupyter/kernels/ir
  julia-1.0     /Users/dorme/Library/Jupyter/kernels/julia-1.0
  vr_python3    /Users/dorme/Library/Jupyter/kernels/vr_python3
```

```zsh
% cat /Users/dorme/Library/Jupyter/kernels/vr_python3/kernel.json
{
 "argv": [
  "/Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-rainforest-Laomc1u4-py3.10/bin/python",
  "-m",
  "ipykernel_launcher",
  "-f",
  "{connection_file}"
 ],
 "display_name": "vr_python3",
 "language": "python",
 "metadata": {
  "debugger": true
 }
}%
```

## Notebook formats

The default `jupyter` notebook format is the IPython Notebook `.ipynb`. This file uses
the JSON format to store the text and code and a whole bunch of other metadata. The
`.ipynb` format is not great for use in version control. There is a really neat summary
of the problem and some solutions
[here](https://nextjournal.com/schmudde/how-to-version-control-jupyter)

The basic problem is that - although JSON files are text-based and are **technically**
human-readable:

- they contain irrelevant metadata - such as the number of times the notebook has been
  run - that will generate unneccessary commits.
- they can contain output binary data - such as images - that may also have arbitrary
  changes.

While there are tools (e.g. `nbdime` and `nbmerge`) that help manage those changes in a
more coherent way, a simpler solution is simply _not to include `.ipynb` files within
the repository at all_. The `jupytext` tool is a really powerful way to manage the
content of Jupyter notebooks, including using markdown formats for notebooks and having
paired (`ipynb` and `md`) files.

There **is a downside**: `.ipynb` files contain code cell outputs, including any
graphics created in the code. GitHub knows how to render those binary and output
contents of `ipynb` files, so the rendered page you see on GitHub includes the most
recent output runs.

- We only commit notebooks in markdown format.
- Notebooks should use the `vr_python3` kernel, so that they will hopefully run on any
  machine that has set up the `kernelspec` correctly.
- GitHub will render the markdown and code cells correctly but none of the executed
  outputs will be shown.
- However, the markdown files **will be executed** by the `sphinx` documentation system,
  so fully rendered versions will be in the documentation website.
- You can also simply launch your local copy in `jupyter-lab` and run it to get outputs.
  This is a problem if the computation is particularly slow, though!

## The `jupytext` package

The `jupytext` package works as an extension running within Jupyter Lab, adding some
commands to the `jupyter` command palette, but also provides a command line tool with
some really useful features.

To be used with `jupytext`, Markdown files need to include a YAML preamble at the very
top of the file. This is used to set document metadata about the Markdown variety and
also code execution data like the Python kernel.

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
  display_name: vr_python3
  language: python
  name: vr_python3
---
```

If you already have a simple Markdown file then the commands below will insert this YAML
header:

```zsh
% jupytext --set-format md:myst simple.md
% jupytext --set-kernel vr_python3  simple.md
```

## Notebook pre-commit checking

### The `mdformat` command

This is an autoformatter for Markdown, with specific extensions to handle the Myst
Markdown variety and the YAML frontmatter (`mdformat-myst` and `mdformat-frontmatter`).
It is configured using `.mdformat.toml`, to set up line wrapping length and default list
formatting.

```zsh
mdformat my_markdown.md
```

### Using `black` with `jupytext`

Although `jupytext` does not do Markdown validation, it does allow `black` to be run on
the code cells, so that the format of code in notebooks can be automatically formatted.

```zsh
jupytext --pipe black my_markdown.md
```

Note that this **does not format** Python code that is simply included in a Markdown
cell - essentially text that is formatted as if it were Python code. It **only** formats
code within a Jupyter notebook code cell - actual code to be executed.
