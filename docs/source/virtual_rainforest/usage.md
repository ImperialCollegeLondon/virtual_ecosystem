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

An example configuration file and the dummy data required to run the `abiotic_simple`
and `soil` models are stored in the Imperial College Research Data Store (RDS). To
access this data you must have been added to the the Virtual Rainforest RDS project.
Details of how to access RDS can be found
[here](https://wiki.imperial.ac.uk/pages/viewpage.action?spaceKey=HPC&title=Research+Data+Store)
(Imperial College login required).

Once you are connected to RDS a simulation using this configuration and data set can be
run through the command line by calling:

```shell
vr_run /Volumes/virtual_rainforest/live/dummy_data/ 
```

**Note:** The directory path above is specific to macOS and will be different for
Windows and Linux machines.
