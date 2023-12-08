# Basic Virtual Rainforest model usage

## Installing the virtual rainforest model

For most users the best way to make use of the Virtual Rainforest package is to install
it via `pip`. It should be noted, however, that this isn't currently possible.

Developer installation should be carried out using poetry. This is achieved by creating
a local copy of the Virtual Rainforest `git` repository. The package is then installed
by calling navigating to the repository and calling:

```shell
poetry install
```

This will install the model and all its dependencies. The model entry points (e.g.
`vr_run`) can then be made use of by calling `poetry run {name_of_entrypoint}`, or by
entering a poetry shell (by calling `poetry shell`). When actively developing it is
generally better to be within a poetry shell, as this ensures that you have command line
access to all relevant dependencies.

## Running an example Virtual Rainforest simulation

Some [example data](./example_data.md) is included with Virtual Rainforest to provide
an introduction to the file formats and configuration. To try Virtual Rainforest using
this example data, you first need to install the data to a location of your choice. The
command below will create the `vr_example` directory at the location you choose and
install all of the configuration and data files to run a model. The code to reproduce
the data is described [here](./example_data.md) and provided in the `vr_example`
directory.

```shell
vr_run --install-example /path/
```

You can then investigate the files needed to run the model and run the model itself:

```shell
vr_run /path/vr_example/config \
    --outpath /path/vr_example/config/out \
    --logfile /path/vr_example/out/vr_example.log
```
