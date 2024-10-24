---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Developing `virtual_ecosystem`

This page gives an overview of the process of contributing code to the `virtual_ecosystem`
package, along with the development environment and tools you will need to setup to work
with the codebase.

## What is a package contributor?

Being a contributor is all about helping improve the `virtual_ecosystem` package. That
could be something very small, like fixing typos in the package website, or something
large, like adding a draft of an entirely new science module to the package.

We welcome _all_ contributions, but we need to manage contributions of code and
documentation to make sure everything works properly together and to keep the code and
documentation consistent. We do a lot of this by using some automated tools that help
keep the package well organised and ensure that it keeps giving the same results through
time.

These tools take a bit of getting used to and the rest of this document sets out how to
get your computer set up to run them. It is a good idea to start off with a small
contribution in order to get used to the workflow - please do reach out to other
developers for help in getting things to work if you run into problems. We will expect
you to have read this document and the linked details pages, but we do not expect them
to be a perfect or complete explanation!

## Contributing code

The workflow for contributing to `virtual_ecosystem` currently follows the Gitflow
strategy. The basic workflow is described below but [this AWS
link](https://docs.aws.amazon.com/prescriptive-guidance/latest/choosing-git-branch-approach/gitflow-branching-strategy.html)
provides an overview of the strategy.

1. Decide what you want to work on. This could be an existing bug or feature request or
   could be something new. If it is new, then create a new issue on Github describing
   what you want to change or add. The issue tracker provides templates for bugs and
   feature requests: please do provide as much detail as possible on the bug or the
   feature you would like to provide. If you want to work on an existing issue, then
   just add a comment and say you would like to work on it.

   [https://github.com/ImperialCollegeLondon/virtual_ecosystem/issues](https://github.com/ImperialCollegeLondon/virtual_ecosystem/issues)

   Whatever issue you do want to work on, do give other developers a chance to comment
   on suggestions before putting a lot of effort in!

1. On Github issue pages, there is a development link to "create a branch" for the
   issue. The branch name will then start with the issue number, which makes branches
   much easier to track, and is explicitly linked to the issue. Feel free to shorten the
   branch name - it uses the issue title by default.

1. Check that branch out locally and make commits to it, pushing them to GitHub
   regularly. Do try and make frequent small commits with clear, specific commit
   messages: a commit does not mean that an issue is completed, just that you want to
   record your progress. The commit history can always be compressed at the merge stage
   (see below).

1. Create a pull request (PR) from the issue branch onto the `develop` branch. The PR
   description should tag the issue being addressed and explain how the incoming code
   fixes the issue. You can start a PR as 'draft' PR: this can be a useful way to start
   describing a PR content and checking that testing is passing before opening a PR up
   for review.

   We prefer pull requests to be small, with the aim of reviewing and merging frequently
   the smallest functional unit of work that you can. This helps stop pull requests
   getting stalled on more and more complex tasks and makes code review fast.

1. Check that the continuous integration testing passes and fix any issues causing test
   failures.

1. Request reviews from other package developers using the Review section on the PR
   page. A PR cannot be merged into `develop` until at least one approving review has
   been added to the code. Reviews will often suggest changes to the code and you should
   discuss those suggestions and implement them.

   Hopefully, you will have talked to other developers during the process of writing the
   PR and should have some ideas of who to ask for a review. If not, please request
   [`davidorme`](https://github.com/davidorme) to review the PR and we can then work out
   which of the core team is best placed to give feedback.

1. Once a PR has been approved, the PR can be merged into `develop` and the branch can
   be deleted.

   The `Merge Pull Request` button provides alternative merge strategies. The default is
   to create a "merge commit" - all of the commits on the PR are merged individually to
   `develop` - but you can also "squash and commit" - which squashes all of the commits
   into a single commit and message before merging. Squashing commits can be really
   helpful to avoid a bunch of minor 'typo' commit messages, but can also make it harder
   to find commits that made bigger changes on a branch. In general, we use "merge
   commits", but if the commit history on a branch is mostly a sequence of minor edits,
   feel free to squash.

## The package development environment

The short descriptions below provide the key commands needed to set up your development
environment and provide links to more detailed descriptions of code development for
`virtual_ecosystem`. The [example setup script](#setup-script-example) below gathers
the commands together into a single script, currently only for Linux.

### Python environment

You will need to install Python to develop `virtual_ecosystem`. The package is currently
tested against the following Python versions: 3.10, 3.11 and 3.12. You should install
one of these versions before you start developing `virtual_ecosystem`.

We highly recommend using [`pyenv`](https://github.com/pyenv/pyenv) or
[`pyenv-win`](https://github.com/pyenv-win/pyenv-win) to manage your Python
installations. These tools allow you to manage multiple different python versions in
parallel and to switch between them. However, these extra steps are not necessary to get
started.

### Package management

We use [`poetry`](https://python-poetry.org/docs/#installation) for dependency
management and for managing development environments and you will need to install it.
The `virtual_ecosystem` package currently uses `poetry` version 1.8.2 and you should
specify this when installing to avoid conflicts with the package management process.

For the typical installation process, this would be as simple as:

```sh
curl -SSL https://install.python-poetry.org | python3 - --version 1.8.2
```

### Installing `virtual_ecosystem`

To develop `virtual_ecosystem`, you will also need to install [`git`](https://git-scm.com/)
and then clone the `virtual_ecosystem` GitHub repository.

```sh
git clone https://github.com/ImperialCollegeLondon/virtual_ecosystem.git
```

You can now use `poetry` to install the package dependencies. This is not just the
package requirements for end users of the package, but also a wider set of tools used in
package development. `poetry` uses the
[pyproject.toml](https://github.com/ImperialCollegeLondon/virtual_ecosystem/blob/develop/pyproject.toml)
file to configure the dependencies that will be installed.

```bash
poetry install
```

That command will install all of the packages required to use the Virtual Ecosystem and
all of the packages required to develop the code.

::::{dropdown} Output from `poetry install`

``` text
Installing dependencies from lock file

Package operations: 180 installs, 1 update, 0 removals

- Installing attrs (23.2.0)
- Installing rpds-py (0.18.1)
- Installing referencing (0.35.1)
- Installing six (1.16.0)
- Installing jsonschema-specifications (2023.12.1)
- Installing platformdirs (4.2.2)
- Installing python-dateutil (2.9.0.post0)
- Installing traitlets (5.14.3)
- Installing types-python-dateutil (2.9.0.20240316)
- Installing arrow (1.3.0)
- Installing fastjsonschema (2.20.0)
- Installing jsonschema (4.22.0)
- Installing jupyter-core (5.7.2)
- Installing pycparser (2.22)
- Installing pyzmq (26.0.3)
- Installing tornado (6.4.1)
- Installing cffi (1.16.0)
- Installing fqdn (1.5.1)
- Installing idna (3.7)
- Installing isoduration (20.11.0)
- Installing jsonpointer (3.0.0)
- Installing jupyter-client (8.6.2)
- Installing markupsafe (2.1.5)
- Installing nbformat (5.10.4)
- Installing ptyprocess (0.7.0)
- Installing rfc3339-validator (0.1.4)
- Installing rfc3986-validator (0.1.1)
- Installing soupsieve (2.5)
- Installing uri-template (1.3.0)
- Installing webcolors (24.6.0)
- Installing webencodings (0.5.1)
- Installing argon2-cffi-bindings (21.2.0)
- Installing asttokens (2.4.1)
- Installing beautifulsoup4 (4.12.3): Installing...
- Installing bleach (6.1.0): Installing...
- Installing certifi (2024.6.2)
- Installing charset-normalizer (3.3.2)
- Installing bleach (6.1.0): Installing...
- Installing certifi (2024.6.2)
- Installing charset-normalizer (3.3.2)
- Installing beautifulsoup4 (4.12.3)
- Installing bleach (6.1.0): Installing...
- Installing certifi (2024.6.2)
- Installing charset-normalizer (3.3.2)
- Installing certifi (2024.6.2)
- Installing charset-normalizer (3.3.2)
- Installing bleach (6.1.0)
- Installing certifi (2024.6.2)
- Installing charset-normalizer (3.3.2)
- Installing defusedxml (0.7.1)
- Installing exceptiongroup (1.2.1)
- Installing executing (2.0.1)
- Installing jinja2 (3.1.4)
- Installing jupyterlab-pygments (0.3.0)
- Installing mdurl (0.1.2)
- Installing mistune (3.0.2)
- Installing nbclient (0.10.0)
- Installing packaging (24.1)
- Installing pandocfilters (1.5.1)
- Installing parso (0.8.4)
- Installing pure-eval (0.2.2)
- Installing pygments (2.18.0)
- Installing python-json-logger (2.0.7)
- Installing pyyaml (6.0.1)
- Installing sniffio (1.3.1)
- Installing terminado (0.18.1)
- Installing typing-extensions (4.12.2)
- Installing tinycss2 (1.3.0)
- Installing urllib3 (2.2.2)
- Installing wcwidth (0.2.13)
- Installing alabaster (0.7.16)
- Installing anyio (4.4.0)
- Installing argon2-cffi (23.1.0)
- Installing babel (2.15.0): Pending...
- Installing decorator (5.1.1)
- Installing docutils (0.20.1): Installing...
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing decorator (5.1.1)
- Installing docutils (0.20.1): Installing...
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing babel (2.15.0): Installing...
- Installing decorator (5.1.1)
- Installing docutils (0.20.1): Installing...
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing docutils (0.20.1)
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing decorator (5.1.1)
- Installing docutils (0.20.1)
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing babel (2.15.0)
- Installing decorator (5.1.1)
- Installing docutils (0.20.1)
- Installing h11 (0.14.0)
- Installing imagesize (1.4.1)
- Installing jedi (0.19.1): Installing...
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing jedi (0.19.1)
- Installing jupyter-events (0.10.0)
- Installing jupyter-server-terminals (0.5.3)
- Installing latexcodec (3.0.0)
- Installing markdown-it-py (3.0.0)
- Installing matplotlib-inline (0.1.7)
- Installing nbconvert (7.16.4)
- Installing overrides (7.7.0)
- Installing pexpect (4.9.0)
- Installing prometheus-client (0.20.0)
- Installing prompt-toolkit (3.0.47)
- Installing requests (2.32.3)
- Installing send2trash (1.8.3)
- Installing snowballstemmer (2.2.0)
- Installing sphinxcontrib-applehelp (1.0.8)
- Installing sphinxcontrib-devhelp (1.0.6)
- Installing sphinxcontrib-htmlhelp (2.0.5)
- Installing sphinxcontrib-jsmath (1.0.1)
- Installing sphinxcontrib-qthelp (1.0.7)
- Installing sphinxcontrib-serializinghtml (1.1.10)
- Installing stack-data (0.6.3)
- Installing tomli (2.0.1)
- Installing websocket-client (1.8.0)
- Installing zipp (3.19.2)
- Installing appnope (0.1.4)
- Installing click (8.1.7)
- Installing comm (0.2.2)
- Installing debugpy (1.8.2): Downloading... 0%
- Installing distlib (0.3.8)
- Installing distlib (0.3.8)
- Installing debugpy (1.8.2): Downloading... 10%
- Installing distlib (0.3.8)
- Installing distlib (0.3.8)
- Installing debugpy (1.8.2): Downloading... 40%
- Installing distlib (0.3.8)
- Installing distlib (0.3.8)
- Installing debugpy (1.8.2): Downloading... 90%
- Installing distlib (0.3.8)
- Installing distlib (0.3.8)
- Installing debugpy (1.8.2): Downloading... 100%
- Installing distlib (0.3.8)
- Installing distlib (0.3.8)
- Installing debugpy (1.8.2): Installing...
- Installing distlib (0.3.8)
- Installing distlib (0.3.8)
- Installing debugpy (1.8.2)
- Installing distlib (0.3.8)
- Installing filelock (3.15.4)
- Installing httpcore (1.0.5)
- Installing importlib-metadata (8.0.0)
- Installing iniconfig (2.0.0)
- Installing ipython (8.26.0)
- Installing json5 (0.9.25)
- Installing jupyter-server (2.14.1)
- Installing locket (1.0.0)
- Installing mdit-py-plugins (0.4.1)
- Installing nest-asyncio (1.6.0)
- Installing numpy (1.26.4)
- Installing pluggy (1.5.0)
- Installing psutil (6.0.0)
- Installing pybtex (0.24.0)
- Installing pytz (2024.1)
- Installing ruamel-yaml-clib (0.2.8)
- Installing sphinx (7.3.7)
- Installing tabulate (0.9.0)
- Installing sqlalchemy (2.0.31)
- Installing toolz (0.12.1)
- Installing tzdata (2024.1)
- Installing async-lru (2.0.4)
- Installing cfgv (3.4.0)
- Installing cftime (1.6.4): Downloading... 0%
- Installing cloudpickle (3.0.0)
- Installing cloudpickle (3.0.0)
- Installing cftime (1.6.4): Downloading... 100%
- Installing cloudpickle (3.0.0)
- Installing cloudpickle (3.0.0)
- Installing cftime (1.6.4): Installing...
- Installing cloudpickle (3.0.0)
- Installing contourpy (1.2.1)
- Installing coverage (7.5.4)
- Installing cycler (0.12.1)
- Installing cloudpickle (3.0.0)
- Installing contourpy (1.2.1)
- Installing coverage (7.5.4)
- Installing cycler (0.12.1)
- Installing cftime (1.6.4)
- Installing cloudpickle (3.0.0)
- Installing contourpy (1.2.1)
- Installing coverage (7.5.4)
- Installing cycler (0.12.1)
- Installing fonttools (4.53.0): Installing...
- Installing fsspec (2024.6.1)
- Installing httpx (0.27.0)
- Installing identify (2.5.36)
- Installing fsspec (2024.6.1)
- Installing httpx (0.27.0)
- Installing identify (2.5.36)
- Installing fonttools (4.53.0)
- Installing fsspec (2024.6.1)
- Installing httpx (0.27.0)
- Installing identify (2.5.36)
- Installing ipykernel (6.29.4)
- Installing jupyter-cache (1.0.0)
- Installing jupyter-lsp (2.2.5)
- Installing jupyterlab-server (2.27.2)
- Installing kiwisolver (1.4.5)
- Installing mdformat (0.7.17)
- Installing mypy-extensions (1.0.0)
- Installing myst-parser (3.0.1)
- Installing nodeenv (1.9.1)
- Installing notebook-shim (0.2.4)
- Installing pandas (2.2.2)
- Installing partd (1.4.2)
- Installing pillow (10.3.0)
- Installing pybtex-docutils (1.0.3)
- Installing pyparsing (3.1.2)
- Installing pytest (7.4.4)
- Installing ruamel-yaml (0.18.6)
- Updating setuptools (70.0.0 -> 70.1.1)
- Installing sortedcontainers (2.4.0)
- Installing sphinxcontrib-jquery (4.1)
- Installing virtualenv (20.26.3)
- Installing autodocsumm (0.2.12)
- Installing dask (2023.12.1)
- Installing dpath (2.2.0)
- Installing hypothesis (6.104.1)
- Installing isort (5.13.2)
- Installing jupyterlab (4.2.3): Downloading... 20%
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0): Installing...
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-frontmatter (0.4.1)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1): Installing...
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1): Installing...
- Installing jupyterlab (4.2.3): Downloading... 40%
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1): Installing...
- Installing mypy (1.10.1)
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab (4.2.3): Downloading... 80%
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab (4.2.3): Downloading... 100%
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab (4.2.3): Installing...
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing jupyterlab (4.2.3)
- Installing jupyterlab-myst (2.4.2)
- Installing jupytext (1.16.2)
- Installing matplotlib (3.9.0)
- Installing mdformat-frontmatter (0.4.1)
- Installing mdformat-tables (0.4.1)
- Installing mypy (1.10.1)
- Installing myst-nb (1.1.1)
- Installing netcdf4 (1.7.1.post1)
- Installing pint (0.20.1)
- Installing pre-commit (2.21.0)
- Installing pydocstyle (6.3.0)
- Installing pytest-cov (3.0.0)
- Installing pytest-datadir (1.5.0)
- Installing pytest-mock (3.14.0)
- Installing scipy (1.14.0)
- Installing shapely (2.0.4)
- Installing sphinx-design (0.6.0)
- Installing sphinx-external-toc (1.0.1)
- Installing sphinx-rtd-theme (2.0.0)
- Installing sphinxcontrib-bibtex (2.6.2)
- Installing sphinxcontrib-mermaid (0.9.2)
- Installing tomli-w (1.0.0)
- Installing tqdm (4.66.4)
- Installing types-dataclasses (0.6.6)
- Installing types-jsonschema (4.22.0.20240610)
- Installing types-tqdm (4.66.0.20240417)
- Installing xarray (2024.6.0)

Installing the current project: virtual_ecosystem (0.1.1a4)
```

::::

Poetry uses a virtual environment for package development: all packages are installed to
a stand-alone python environment that is only used for `virtual_ecosystem` development.
This makes sure that the development environment is consistent across python versions
and different developers. However, when you are working on the command line, you need to
**explicitly use the `virtual_ecosystem` environment** to run any command that needs to
use the `virtual_ecosystem` environment - and that is pretty much everything described
in this document. There are two options to do this:

1. You can add `poetry run` before a command to make sure that single command is run
   using the `poetry` environment. This approach is used in the example commands below.
1. You can use `poetry shell` to start a new shell that uses this environment: you can
   then run commands without needing `poetry run` and they should use the correct
   enviroment. This is usually more convenient.

You should now be able to run the following command to see that `virtual_ecosystem` is
installed and is showing the current version.

```sh
poetry run python -c "import virtual_ecosystem; print(virtual_ecosystem.__version__)"
```

You can have parallel virtual environments for different Python versions: the command
`poetry env list` can be used to show available environments and `poetry env use` can be
used to add new environments and switch between existing environments.

### Key developer tools

This is not an exhaustive list, but the packages installed by `poetry` including the
following standalone tools that can be used in developing your code and documentation.

- `ipython`: an improved interactive Python shell. If you are running code in Python
  from the command line, this is the one to use. Visual Studio Code likes to use it.

- `jupyterlab`: an interactive computing server, providing elegant notebooks for
  documentation and how-to guides, as well as debugging and development discussion.

- `jupytext`: this allows `jupyter` to use Markdown formatted notebooks - in particular
  the extended [MyST Markdown](https://myst-parser.readthedocs.io/en/latest/) variety
  which will also be used for documentation.

### Updating `poetry` and package versions

You will not need to do this when setting up your development environment but one of the
things that `poetry` does is to maintain a fixed set of compatible required packages.
The `pyproject.toml` files sets constraints on package versions, but the particular
combination to be used for a given commit is resolved and stored in the `poetry.lock`
file.

- If you want to **add a package** - either using `poetry add` or by manually updating
  `pyproject.toml` - you will then need to run `poetry update` to check that a
  compatible set of package versions exists and to update the `poetry.lock` file.

- If you want to **update a package** then `poetry update` will update all the required
  packages and update `poetry.lock`. You can use `poetry update package_name` to only
  update a particular requirement.

- The `poetry install` command - as shown above - can be re-run to re-install the
  package. You will typically only need to do this if commands provided by the package
  have changed and need to be updated.

If you pull code from GitHub that changes `pyproject.toml` and `poetry.lock`, you should
also run `poetry update` to bring your environment in line with other developers.

### Installing and using `pre-commit`

Development of the `virtual_ecosystem` package uses [`pre-commit`](https://pre-commit.com/).
This is a python tool that runs a set of checks on `git` commits and stops the commit from
completing when any of those checks fail. We use `pre-commit` to help catch a wide range
of common issues and make sure that all code pushed to the GitHub repository meets some
simple quality assurance checks and uses some common formatting standards.

There is a detailed description of the `pre-commit` output and the  configured checks
and update process on the [code quality assurance page](./code_qa_and_typing.md).
Briefly, the main elements are to use `pre-commit` to run code quality and formatting
checks using the `ruff` tool and static typing using `mypy`.

The `pre-commit` tool is installed by the `poetry install` step above, so you now need
to install the `virtual_ecosystem` configuration for `pre-commit` and run the tool to
set up the environment and check it is all working.

```sh
poetry run pre-commit install
poetry run pre-commit run --all-files
```

That might take a little while to run on the first use. Once you have done this, every
`git commit` will generate similar output and your commit will fail if issues are found.

### Static typing with `mypy`

The `python` programming language does not _require_ code objects to be typed, but the
`virtual_ecosystem` package uses [type hints](https://peps.python.org/pep-0484/) to
annotate code. Those type hints are then checked using the `mypy` static type checker,
which is installed by `poetry` and is run as one of the `pre-commit` checks.

The `mypy` package and the plugins we use are all installed by `poetry`. See the [code
quality assurance page](./code_qa_and_typing.md) for more information on using `mypy`.

### Package testing

All code in the `virtual_ecosystem` package should have accompanying unit tests, using
`pytest`. Look at the existing test suite in the `tests/unit` directory to see the
structure and get a feel for what they should do, but essentially unit tests should
provide a set of known inputs to a function and check that the expected answer (which
could be an Exception) is generated.

Again, the `pytest` package and plugins are installed by `poetry`. See the [code testing
page](./code_testing.md) for more details but you should be able to check the tests run
using the following command. Be warned that the `mypy` steps can be very time consuming
on the first run, but `pytest` does some cacheing that makes them quicker when they next
run.

```sh
poetry run pytest
```

### The `example_data` module

The `virtual_ecosystem` package includes the [`example_data`
submodule](../../using_the_ve/example_data.md) that provides a simple configuration and
initial data inputs for running a simulation. This is widely used in the `pytest` suite
and may be useful in developing your own tests.

### Documentation

We use `sphinx` to maintain the documentation for `virtual_ecosystem` and Google style
docstrings using the `napoleon` formatting to provide API documentation for the code.
We use MyST Markdown to provide dynamically built usage examples. See the [documentation
pages](../documentation/documentation.md) for details but to get started, the following
code can be used to build the documentation.

```bash
# Build docs using sphinx
cd docs
poetry run sphinx-build -W --keep-going source build
```

Once that command completes, the file `docs/build/html/index.html` can be opened to view
the built documentation.

### GitHub Actions

We use GitHub Action workflows to update `pre-commit`, run code quality checks on pull
requests, and to automate the publication of package releases on PyPI. See the [GitHub
Actions page](./github_actions.md) for details.

### Package version releases

We use trusted publishing from GitHub releases to release new versions of the
`virtual_ecosystem` to
[PyPI](https://pypi.org/project/virtual_ecosystem/). Releases are also picked up and
archived on [Zenodo](https://doi.org/10.5281/zenodo.8366847). See the [release process
page](./release_process.md) for details.

## Setup script example

The scripts below bundle all the commands together to show the set up process, including
using `pyenv` to mangage `python` versions, ending by running the unit tests. This sets
up everything you need, ready to start developing on the `virtual_ecosystem`.

:::{admonition} Setup script

``` sh
!/bin/bash

# pyenv and poetry use sqlite3. You _may_ need to install these requirements first.
sudo apt install sqlite3 sqlite3-doc libsqlite3-dev

# install pyenv to manage parallel python environments
curl <https://pyenv.run> | bash

# Manually edit .bash_profile or .profile to setup pyenv:

# export PYENV_ROOT="$HOME/.pyenv":
# [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH":
# eval "$(pyenv init -)"

# Install a python version
pyenv install 3.11

# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Manually add poetry to path in profile file:

# export PATH="/home/validate/.local/bin:$PATH"

# Clone the repository
git clone https://github.com/ImperialCollegeLondon/virtual_ecosystem.git

# Configure the virtual_ecosystem repo to use python 3.11
cd virtual_ecosystem
pyenv local 3.11
poetry env use 3.11

# Install the package with poetry
poetry install

# Install pre-commit and check
poetry run pre-commit install
poetry run pre-commit run --all-files

# Run the test suite
poetry run pytest

```

:::
