"""The ``core.utils`` module contains functions that are used across the
Virtual Rainforest, but which don't have a natural home in a specific module. At the
moment, this module only contains a single function, but it will probably expand in
future. Adding functions here can be a good way to reduce the amount boiler plate code
generated for tasks that are repeated across modules.
"""  # noqa: D205, D415

import dataclasses
from importlib import import_module
from pathlib import Path
from typing import Any

from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.core.logger import LOGGER


def check_outfile(merge_file_path: Path) -> None:
    """Check that final output file is not already in the output folder.

    Args:
        merge_file_path: Path to save merged config file to (i.e. folder location + file
            name)

    Raises:
        ConfigurationError: If the final output directory doesn't exist, isn't a
            directory, or the final output file already exists.
    """

    # Extract parent folder name and output file name. If this is a relative path, it is
    # expected to be relative to where the command is being run.
    if not merge_file_path.is_absolute():
        parent_fold = merge_file_path.parent.relative_to(".")
    else:
        parent_fold = merge_file_path.parent
    out_file_name = merge_file_path.name

    # Throw critical error if the output folder doesn't exist
    if not Path(parent_fold).exists():
        to_raise = ConfigurationError(
            f"The user specified output directory ({parent_fold}) doesn't exist!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    elif not Path(parent_fold).is_dir():
        to_raise = ConfigurationError(
            f"The user specified output folder ({parent_fold}) isn't a directory!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # Throw critical error if combined output file already exists
    if merge_file_path.exists():
        to_raise = ConfigurationError(
            f"A file in the user specified output folder ({parent_fold}) already "
            f"makes use of the specified output file name ({out_file_name}), this "
            f"file should either be renamed or deleted!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return None


def set_layer_roles(canopy_layers: int, soil_layers: int) -> list[str]:
    """Create a list of layer roles.

    This function creates a list of layer roles for the vertical dimension of the
    Virtual Rainforest. The layer above the canopy is defined as 0 (canopy height + 2m)
    and the index increases towards the bottom of the soil column. The canopy includes a
    maximum number of canopy layers (defined in config) which are filled from the top
    with canopy node heights from the plant module (the rest is set to NaN). Below the
    canopy, we currently set one subcanopy layer (around 1.5m above ground) and one
    surface layer (0.1 m above ground). Below ground, we include a maximum number of
    soil layers (defined in config); the deepest layer is currently set to 1 m as the
    temperature there is fairly constant and equals the mean annual temperature.

    Args:
        canopy_layers: number of canopy layers soil_layers: number of soil layers

    Raises:
        InitialisationError: If the number soil or canopy layers are not both positive
            integers

    Returns:
        List of canopy layer roles
    """

    # sanity checks for soil and canopy layers
    if soil_layers < 1:
        to_raise = InitialisationError(
            "There has to be at least one soil layer in the Virtual Rainforest!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    if not isinstance(soil_layers, int):
        to_raise = InitialisationError("The number of soil layers must be an integer!")
        LOGGER.error(to_raise)
        raise to_raise

    if canopy_layers < 1:
        to_raise = InitialisationError(
            "There has to be at least one canopy layer in the Virtual Rainforest!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    if canopy_layers != int(canopy_layers):
        to_raise = InitialisationError(
            "The number of canopy layers must be an integer!"
        )
        LOGGER.error(to_raise)
        raise to_raise

    layer_roles = (
        ["above"]
        + ["canopy"] * canopy_layers
        + ["subcanopy"]
        + ["surface"]
        + ["soil"] * soil_layers
    )
    return layer_roles


# TODO - Write tests for this function
def check_constants(config: dict[str, Any], model_name: str, class_name: str) -> None:
    """Check that the constants defined in the config are expected.

    This checks that the constants are expected for the specific dataclass that they are
    assigned to, if not an error is raised.

    Args:
        config: The full virtual rainforest config
        model_name: Name of the model the constants belong to
        class_name: Name of the specific dataclass the constants belong to

    Raises:
        ConfigurationError: If unexpected constant names are used
    """

    # Import dataclass of interest
    import_path = f"virtual_rainforest.models.{model_name}.constants"
    consts_module = import_module(import_path)
    ConstantsClass = getattr(consts_module, class_name)

    # Extract the relevant set of constants
    constants = config[model_name]["constants"][class_name]

    # Create list of unexpected names
    unexpected_names = []

    # Iterate over every item in the constants dictionary
    for const_name, const_value in constants.items():
        try:
            ConstantsClass(**{const_name: const_value})
        except TypeError:
            unexpected_names.append(const_name)

    if unexpected_names:
        LOGGER.error(
            "Incorrect constant names supplied for %s dataclass: %s"
            % (class_name, unexpected_names)
        )
        # Find all valid names and inform the user about them
        valid_names = [fld.name for fld in dataclasses.fields(ConstantsClass)]
        LOGGER.info("Valid names are as follows: %s" % (valid_names))
        raise ConfigurationError()

    return
