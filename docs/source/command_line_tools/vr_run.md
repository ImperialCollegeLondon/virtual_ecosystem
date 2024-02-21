# Command line tools overview

The `virtual_ecosystem` package currently provides a single command line tool `ve_run`.
This is tool is likely to be superseded as the project develops, either by a set of
command line tools or a single more generic tool.

## The `ve_run` command line tool

The `ve_run` command line tool exists to run the virtual rainforest model. At the moment
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
