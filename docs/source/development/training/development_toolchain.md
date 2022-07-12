---
jupytext:
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

<!-- markdownlint-disable MD024 MD041 - repeated headings and not header first-->

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

# Development toolchain

David Orme

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## Toolchain components

- `pyenv`: python installation manager
- `poetry`: package manager
- `virtualenv`: virtual environments
- `pre-commit`: Git pre-commit hooks
  - `black`: code auto-formatter
  - `isort`: import sorter
  - `flake8`: code linter
  - `mypy`: type checker
  - `markdownlint`: markdown linter

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `pyenv` package

![python env hell](https://imgs.xkcd.com/comics/python_environment.png)

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `pyenv` package

- Creates a set of parallel `python` installations
  - Linux/MacOS: [](https://github.com/pyenv/pyenv)
  - Windows: [](https://github.com/pyenv-win/pyenv-win)
- Can set **which** version is being used and **where**
- `~/.pyenv/version` `.python_version` and `$PYENV_VERSION`

```{code-cell}
%%bash
pyenv versions
```

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## Poetry

The `poetry` system supports all of the aspects of package development:

- Dependency management
- Virtual environments
- Package building
- Package publication (`pypi`)

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Installing `poetry`

- Poetry is written in python but not installed via `pip`!
- Not (currently) tied to a particular python installation

### Installation

- [](https://python-poetry.org/docs/)

- Pipe a script from the web straight into Python 3.7+

- Linux/MacOS/WSL

<!-- markdownlint-disable MD013 -->
```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
<!-- markdownlint-enable MD013 -->

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Accessing poetry

- The location of the `poetry` command now needs to be set
- Edit the `$PATH` environment variable in your shell profile
  - `.bash_profile`, `.zshrc`

```bash
# On Mac/Linux
export PATH=$HOME/.poetry/bin:$PATH
# On WSL
export PATH=$USERPROFILE/.poetry/bin:$PATH
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Using poetry

```{code-cell}
%%bash
~/.poetry/bin/poetry --help
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Using poetry with a package

- Start using poetry: `poetry init` or `poetry new`
- Creates `pyproject.toml` file
  - Description, authors, URLS
  - Dependencies (aka requirements)
  - Command line scripts
  - Package build setup
  - Also used to configure other tools

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Managing dependencies

The `poetry` subcommands: `add`, `update`, `remove`

- Manage dependencies and minimum versions described in `pyproject.toml`
- Resolves dependencies and versions **if possible**
- Exports a resolved set to the `poetry.lock` file
- `poetry install`: Installs set using the current active python

````bash
~ % poetry env use 3.8
Creating virtualenv demo-py3.8 in /.../virtualenvs
Using virtualenv: /.../demo-py3.8
~ % poetry install
Installing dependencies from lock file
Package operations: 56 installs, 0 updates, 0 removals
...
Installing the current project: safedata_validator (2.0.1-post9000)

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Virtual environments

The `poetry env` command manages **virtual environments** ('venv')

* A specific version of python with specific packages
* Python installation **specific** to a particular project
* Can have multiple venvs in parallel: `poetry env add`
* A single venv can be **active**

```bash
dorme@MacBook-Pro safedata_validator % poetry env list
demo-py3.6
demo-py3.7
demo-py3.8 (Activated)
dorme@MacBook-Pro safedata_validator %
````

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Activating virtual environments

- A `venv` must be active to be used:

```bash
~ % poetry shell
Spawning shell within /.../demo-py3.8
~ % . /.../demo-py3.8/bin/activate
(demo-py3.8) dorme@MacBook-Pro safedata_validator_package %
```

- Or a single command can use the `venv`:

```bash
poetry run command
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Package build and publish

For a release candidate (`release/x.y.z`) or release (`master`):

- Build the package into a release format (`bdist`, `wheel`)
  - `poetry build`
- Publish the package to PyPi (or Test PyPi)!
  - `poetry publish`

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## Pre-commit

- A python package to manage `git` pre-commit hooks
- Prevents commits that do not pass checks
- Configured in `.pre-commit-config.yaml`
- Install using: `pre-commit install`
- Can double check before committing: `pre-commit run`...
- ...but not much point!

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## `pre-commit` configuration

```text
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.1.0
    hooks:
      - id: check-merge-conflict
      - id: debug-statements
  - repo: https://github.com/timothycrosley/isort
    rev: "5.10.1"
    hooks:
      - id: isort
        additional_dependencies: [toml]
  - repo: https://github.com/psf/black
    rev: "22.3.0"
    hooks:
      - id: black
  - repo: https://gitlab.com/pycqa/flake8
    rev: 3.9.2
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: "v0.931"
    hooks:
      - id: mypy
  - repo: https://github.com/markdownlint/markdownlint
    rev: "v0.11.0"
    hooks:
      - id: markdownlint
        args: ["-r", "~MD013"]
```

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `isort` import formatter

- Expected order and layout of package imports
- Automatically enforced by [the `isort` package](https://pycqa.github.io/isort/)
- Configured from `pyproject.toml`

```python
import standard_library

import third_party_library

import my_library
```

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `black` code formatter

- An ['uncomprising code formatter'](https://black.readthedocs.io/en/stable/)
- **Imposes** a particular format on code files
  - Use of double quotes, not single
  - Maximum line length (Usually 88 characters)
  - Wrapping patterns for long lines
- Only slightly configurable - this is what you get
- Maintains a consistent code layout

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `flake8` linter

- A [python **linter**](https://flake8.pycqa.org/en/latest/)
- Provides commentary on files but does not change them
- Wraps `PyFlakes` and `pycodestyle` but many other options
- Highly configurable and extendable
- Not just formatting: coding styles, complexity etc.
- Run `black` **first**

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `mypy` type checker

- Python is **dynamically** typed:
  - using an object checks the object type
  - 'duck' typing
- [PEP 484](https://peps.python.org/pep-0484/) (2015, Python 3.5+) introduced optional
  **type hints**
- Implemented using `typing` standard library and others
- `mypy` is a **static typing tool for code development**
- Checks that a code base is internally consistent
- Python does not enforce type hints **at runtime**

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `mypy` type checker

- Type hints in a function **signature**

```{code-cell}
# %load -s my_picky_float_multiplier mfm.py
def my_picky_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier3(2.1, 3.6)  # doctest: +ELLIPSIS
        7.56...
        >>> my_picky_float_multiplier(2, 3)
        ... # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        ValueError: Both x and y must be of type float
    """

    if not (isinstance(x, float) and isinstance(y, float)):
        raise ValueError("Both x and y must be of type float")

    return x * y
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `mypy` package

- Provides the command `mypy`
- Highly configurable
- Installable **stubs** to add type checking of imports
- The [`typeshed` repository](https://github.com/python/typeshed) maintains stubs
- Checks that codebase uses type hints **compatibly**

```python
# Mypy does _not_ complain: int is compatible with float
important_result = my_picky_float_multiplier(2, 3)

# Mypy _does_ complain: str is not compatible with float
important_result = my_picky_float_multiplier('a', 3)
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `pydantic` package

- Can decorate functions to enable **runtime** type checking

```{code-cell}
def my_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier(2.1, 3.6)
        7.56
    """

    return x * y


my_float_multiplier(5, "a")
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `pydantic` package

- Can decorate functions to enable runtime type checking

```{code-cell}
:tags: [raises-exception]

from pydantic import validate_arguments


@validate_arguments
def my_validated_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier(2.1, 3.6)
        7.56
    """

    return x * y


my_validated_float_multiplier(1, "a")
```

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## Markdownlint

- A [markdown linter](https://github.com/markdownlint/markdownlint)
  - Compliance with CommonMark markdown
  - VS Code extension
  - Linter _not_ a formatter
  - Written in `ruby` (or `node.js`)
- `mdformat`: an opinionated **formatter**:
  - (some) extensions for MyST Markdown
  - Also available as a pre-commit hook
  - Written in Python

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## Playgrounds

Online sandboxes for exploring tools:

- [isort playground](https://pycqa.github.io/isort/docs/quick_start/0.-try.html)
- [black playground](https://black.vercel.app/)
- flake8 playground - Can't find one!
- [mypy playground](https://mypy-play.net/)
- [markdownlint playground](https://dlaa.me/markdownlint/)
