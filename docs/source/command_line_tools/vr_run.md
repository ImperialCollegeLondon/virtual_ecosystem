# Command line tools overview

The `virtual_rainforest` package currently provides a single command line tool `vr_run`.
This is tool is likely to be superseded as the project develops, either by a set of
command line tools or a single more generic tool.

## The `vr_run` command line tool

The `vr_run` command line tool exists to run the virtual rainforest model. At the moment
this consists of validated a set of schema files, using their contents to initialise a
set of models and then setting up the main simulation loop. It goes no further than
that, and no actual simulation steps are performed. This will change in the future.

### Using `vr_run`

The usage instructions for `vr_run` are given below:

```{include} command_line_usage/vr_run.txt
```

Essentially, you can run the Virtual Rainforest model by calling:

```bash
vr_run path/to/config/file.toml path/to/second/config/file.toml
```
