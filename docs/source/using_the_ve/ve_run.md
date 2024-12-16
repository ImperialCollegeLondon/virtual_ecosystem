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

# Command line tools overview

The `virtual_ecosystem` package currently provides a single command line tool `ve_run`.
This is tool is likely to be superseded as the project develops, either by a set of
command line tools or a single more generic tool.

## The `ve_run` command line tool

The `ve_run` command line tool exists to run the Virtual Ecosystem model. At the moment
this consists of validated a set of schema files, using their contents to initialise a
set of models and then setting up the main simulation loop. It goes no further than
that, and no actual simulation steps are performed. This will change in the future.

### Using `ve_run`

The usage instructions for `ve_run` can be found by calling:

```bash
ve_run --help
```

Essentially, you can run the Virtual Ecosystem model by calling:

```bash
ve_run path/to/config/file.toml path/to/second/config/file.toml
```
