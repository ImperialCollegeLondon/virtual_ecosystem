# Developer setup

:::{note}

Outdated: to be merged into new developer docs

:::

This document is a help file for developers setting up a computer to work with the
Virtual Ecosystem codebase.

## Python version

We decided (June 2022) to support Python 3.9+:

- Recent new versions of `numpy` (^1.22.0) are 3.8+
- Python 3.9 enabled generics in type hints (list\[float\] not List\[float\])

## Python installation

We recommend using `pyenv` or `pyenv-win` to manage parallel Python environments:

- [Install notes](https://github.com/pyenv/pyenv#installation)

## Base python packages

The package manager `poetry` (see below) handles the installation of the required
packages for the project, but there are several packages that are more widely useful and
should be installed for the base `pyenv` installation of each Python version. These
should then be available for all virtual environments (see below!) using that Python
version.

- `ipython`: an improved interactive Python shell. If you are running code in Python
  from the command line, this is the one to use. Visual Studio Code likes to use it.

- `jupyterlab`: an interactive computing server, providing elegant notebooks for
  documentation and how-to guides, as well as debugging and development discussion.

- `jupytext`: this allows `jupyter` to use Markdown formatted notebooks - in particular
  the extended [MyST Markdown](https://myst-parser.readthedocs.io/en/latest/) variety
  which will also be used for documentation.

```sh
# Set the python version to install
pyenv local 3.9.12
# Install these into the package base
pip install ipython jupyterlab jupytext
```

## The `poetry` package manager

The next step is to install `poetry` and then use this to install the development
environment for the package.

- Install `poetry` following
  [the instructions](https://python-poetry.org/docs/#installation).
- Note that the installation also includes a step to configure your computer to find the
  installed `poetry` command!
- Use `poetry` to install the development environment. This step installs all the
  packages listed in the `pyproject.toml` file for the project, and specifically a set
  of versions that `poetry` has found to be mutually compatible and that are listed in
  the `poetry.lock` file.

```bash
cd path/to/vr_repo/root
poetry install
```

You should then see output describing the creation of a virtual environment and the
installation of the required packages into that environment. For example:

```bash
dorme@MacBook-Pro virtual_ecosystem % poetry install
Creating virtualenv virtual-ecosystem-Laomc1u4-py3.10 in /Users/dorme/Library/Caches/pypoetry/virtualenvs
Installing dependencies from lock file

Package operations: 39 installs, 0 updates, 0 removals

  • Installing pyparsing (3.0.9)
  • Installing attrs (21.4.0)
  • Installing distlib (0.3.4)
  • Installing filelock (3.7.1)
  • Installing iniconfig (1.1.1)
  • Installing mccabe (0.6.1)
  • Installing mdurl (0.1.1)
  • Installing mypy-extensions (0.4.3)
  • Installing packaging (21.3)
  • Installing platformdirs (2.5.2)
  • Installing pluggy (1.0.0)
  • Installing py (1.11.0)
  • Installing pycodestyle (2.8.0)
  • Installing pyflakes (2.4.0)
  • Installing six (1.16.0)
  • Installing tomli (2.0.1)
  • Installing typing-extensions (4.2.0)
  • Installing cfgv (3.3.1)
  • Installing click (8.1.3)
  • Installing coverage (6.4.1)
  • Installing flake8 (4.0.1)
  • Installing identify (2.5.1)
  • Installing markdown-it-py (2.1.0)
  • Installing mypy (0.961)
  • Installing nodeenv (1.7.0)
  • Installing pathspec (0.9.0)
  • Installing pytest (7.1.2)
  • Installing pyyaml (6.0)
  • Installing toml (0.10.2)
  • Installing virtualenv (20.15.1)
  • Installing black (22.6.0)
  • Installing isort (5.10.1)
  • Installing mdformat (0.7.14)
  • Installing numpy (1.23.0)
  • Installing pre-commit (2.19.0)
  • Installing pytest-cov (3.0.0)
  • Installing pytest-flake8 (1.1.1)
  • Installing pytest-mock (3.8.1)
  • Installing pytest-mypy (0.9.1)

Installing the current project: virtual_ecosystem (0.1.0)
```

## Using the virtual environments

In order to use the virtual environments (`venv`) created by `poetry`, you need to make
sure the one you want is activated and then launch a new shell using that `venv`. You
may have parallel `venv` for different Python versions and you can check this using
`poetry env list`:

```bash
dorme@MacBook-Pro virtual_ecosystem % poetry env list
virtual-ecosystem-Laomc1u4-py3.10 (Activated)
virtual-ecosystem-Laomc1u4-py3.9
dorme@MacBook-Pro virtual_ecosystem %
```

You can now launch a shell using that `venv`.

```bash
dorme@MacBook-Pro virtual_ecosystem % poetry shell
Spawning shell within /Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-ecosystem-Laomc1u4-py3.10
dorme@MacBook-Pro virtual_ecosystem % . /Users/dorme/Library/Caches/pypoetry/virtualenvs/virtual-ecosystem-Laomc1u4-py3.10/bin/activate
(virtual-ecosystem-Laomc1u4-py3.10) dorme@MacBook-Pro virtual_ecosystem %
```

The command line prompt has been updated to show the active `venv`.

## Installing `pre-commit` hooks

Now you have an active `venv` that includes the `pre-commit` package, which is one of
the developer dependencies specified in `pyproject.toml`. The `.pre-commit-config.yaml`
file defines the set of pre-commit checks that we want to use, and those can be
installed using:

```bash
pre-commit install
```

You should then see output describing the installation of the software required for the
pre-commit hooks. Once that has been done, the hooks are active:

- the contents of any `git commit` must pass those checks.
- If it does not, the commit will not happen and you will see which hooks have failed
  and why.
- You will need to `git add` further changes to those files to a point where they pass
  the checks.

## Setting up `git flow`

In this project we make use of
[`gitflow-avh`](https://github.com/petervanderdoes/gitflow-avh), as it offers a helpful
extended set of publishing commands. Installation instructions for different operating
systems can be found
[here](https://github.com/petervanderdoes/gitflow-avh/wiki/Installation). As example, on
MacOS it can be installed using the following command:

```bash
brew install git-flow-avh
```

Now that `git-flow-avh` is installed, `git flow` should be initialised for the repo by
calling:

```bash
git flow init
```

This generates a number of questions, these are shown below along with the answers that
should be given. N.B. that in most cases the default is fine, and so the question can be
skipped by pressing the enter key.

```bash
Which branch should be used for bringing forth production releases?
   - develop
   - main
   - testing_training
Branch name for production releases: [main] main

Which branch should be used for integration of the "next release"?
   - develop
   - testing_training
Branch name for "next release" development: [develop] develop

How to name your supporting branch prefixes?
Feature branches? [feature/]
Bugfix branches? [bugfix/]
Release branches? [release/]
Hotfix branches? [hotfix/]
Support branches? [support/]
Version tag prefix? [] v
Hooks and filters directory? [/usr/file/structure/virtual_ecosystem/.git/hooks]
```

Once this is done `git flow` has been setup and new branches can be created using
`git flow` commands
