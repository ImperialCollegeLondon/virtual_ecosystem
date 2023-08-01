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

Some example data is included with Virtual Rainforest in the
`virtual_rainforest.example_data` package.

To try Virtual Rainforest using this example data, run:

```shell
vr_run --example
```
