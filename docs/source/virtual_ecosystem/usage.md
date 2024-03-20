# Basic Virtual Ecosystem model usage

## Installing the Virtual Ecosystem model

For most users the best way to make use of the Virtual Ecosystem package is to install
it via `pip`. It should be noted, however, that this isn't currently possible.

Developer installation should be carried out using poetry. This is achieved by creating
a local copy of the Virtual Ecosystem `git` repository. The package is then installed
by calling navigating to the repository and calling:

```shell
poetry install
```

This will install the model and all its dependencies. The model entry points (e.g.
`ve_run`) can then be made use of by calling `poetry run {name_of_entrypoint}`, or by
entering a poetry shell (by calling `poetry shell`). When actively developing it is
generally better to be within a poetry shell, as this ensures that you have command line
access to all relevant dependencies.

## Running an example Virtual Ecosystem simulation

Some example data is included with Virtual Ecosystem to provide
an introduction to the file formats and configuration. To try Virtual Ecosystem using
this example data, you first need to install the data to a location of your choice. The
command below will create the `ve_example` directory at the location you choose and
install all of the configuration and data files to run a model.

```shell
ve_run --install-example /path/
```

You can then run the model itself:

```shell
ve_run /path/ve_example/config \ 
    --outpath /path/ve_example/config/out \ 
    --logfile /path/ve_example/out/ve_example.log
```

Once you want to start digging into the structure of the model and inputs, the [example
data](./example_data.md) pages provides a detailed description of the  contents of the
`ve_example` directory.
