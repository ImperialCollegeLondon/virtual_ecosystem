---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
language_info:
  codemirror_mode:
    name: ipython
    version: 3
  file_extension: .py
  mimetype: text/x-python
  name: python
  nbconvert_exporter: python
  pygments_lexer: ipython3
  version: 3.11.9
---

# Installing the Virtual Ecosystem

The Virtual Ecosystem model is written using the Python programming language and can be
installed from the [Python Package Index (PyPI)](https://pypi.org/), which is a
repository of published Python packages. The Python language is continually evolving and
so all Python packages declare a minimum version of Python needed to use the package.
For the Virtual Ecosystem, the minimum Python version is: ![Minimum Python
Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FImperialCollegeLondon%2Fvirtual_ecosystem%2Fdevelop%2Fpyproject.toml&logoSize=auto).

## Installing Python

Check if you already have Python on your computer and - if you do - is it recent enough
to meet the minimum version. If you need to install or update Python, installers for all
operating systems are available from the [official Python download
page](https://www.python.org/downloads/).

## Installing the Virtual Ecosystem package

You now need to install the Virtual Ecosystem package itself. Installing Python
automatically installs the package installer for Python (`pip`). You should be able to
open  a terminal window and use the following command to install the Virtual Ecosystem
using `pip`.

This will always install the most recent release of the Virtual Ecosystem model. Note
that the package is still being developed so we are currently releasing early
development (or 'alpha') releases that may may change rapidly.

`````{tab-set}
:sync-group: operating_system

````{tab-item} macOS/Linux
:sync: macoslinux

```{code-block} shell
pip install virtual-ecosystem
```
````

````{tab-item} Windows
:sync: windows

```{code-block} powershell
pip install virtual-ecosystem
```
````
`````

## The `ve_run` command

Installing the Virtual Ecosystem package will create the `ve_run` command line program
on your computer. The `ve_run` command can be used to:

* install the [example model data](./example_data.md) on your computer, and
* run a Virtual Ecosystem simulation, such as [running the example
  model](./virtual_ecosystem_in_use.md)

However, for now, you should be able to check that the package installation has been
successful by running the command below in a terminal to show the help for the `ve_run`
function:

`````{tab-set}
:sync-group: operating_system

````{tab-item} macOS/Linux
:sync: macoslinux

```{code-block} shell
ve_run --help
```
````

````{tab-item} Windows
:sync: windows

```{code-block} powershell
ve_run --help
```
````
`````

See the pages on [installing the example data](./example_data.md) and [running the
Virtual Ecosystem](./virtual_ecosystem_in_use.md) for details of the `ve_run` command
options.

## Using a Virtual Environment

The process above installs the Virtual Ecosystem package for use with the main Python
installation on your computer. This is typically fine if you are just using Python to
explore the use of the Virtual Ecosystem.

In general, however, we would recommend that you install and run the Virtual Ecosystem
package from within a dedicated virtual environment. This is a way to keep the Python
setup needed to run the Virtual Ecosystem separate from other uses of Python packages on
your system, and is generally recommended as good practice for computing with Python.

Creating a virtual environment is a moderately advanced topic and there is a good primer
on [the Real Python
website](https://realpython.com/python-virtual-environments-a-primer/).

## Altering the model code

If you are interested in actually making changes to the code underlying the `ve_run`
command and potentially developing extensions or alterations to the model, then we
strongly recommend installing the package source code from GitHub using the `poetry`
package manager. This will install the additional packages and tools used by the
development team that are required for code development and quality assurance, code
testing and building documentation.

This is a much more complex installation - see this [overview of the developer
setup](../development/contributing/overview.md) - but it will put you in a position to
work with most recent changes to the model or contribute your own suggestions to the
code.
