---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.4
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

# Getting started

## Installing the Virtual Ecosystem model

For most users the best way to get started with the Virtual Ecosystem package is to
[install Python](https://www.python.org/downloads/) and then install the Virtual
Ecosystem using the `pip` package installer.

```sh
pip install virtual-ecosystem
```

This will always install the most recent release of the Virtual Ecosystem model. Note
that the package is still being developed so these are currently early development (or
'alpha') releases, so the package details may change rapidly.

If you are more interested in playing around with the development of the model, then you
will need to follow the [overview of the code contribution
process]../development/contributing/overivew.md), which covers the installation of the
tools required for code development, testing and building documentation.

## Running an example Virtual Ecosystem simulation

Some example data is included with Virtual Ecosystem to provide an introduction to the
file formats and configuration. To try Virtual Ecosystem using this example data, you
first need to install the data to a location of your choice. The command below will
create the `ve_example` directory at the location you choose and install all of the
configuration and data files to run a model.

```shell
ve_run --install-example /path/
```

You can then run the model itself:

```shell
ve_run /path/ve_example/config \
    --outpath /path/ve_example/config/out \
    --logfile /path/ve_example/out/ve_example.log
```

The [Virtual Ecosystem in use](virtual_ecosystem_in_use.md) page provides a walkthrough
of this process, showing the typical outputs of the model run process, and also provides
some simple plots of model inputs and ouputs.

Once you want to start digging into the structure of the model and inputs, the [example
data](./example_data.md) pages provides a detailed description of the  contents of the
`ve_example` directory.
