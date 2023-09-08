"""The ``core.utils`` module contains functions that are used across the
Virtual Rainforest, but which don't have a natural home in a specific module. At the
moment, this module only contains a single function, but it will probably expand in
future. Adding functions here can be a good way to reduce the amount boiler plate code
generated for tasks that are repeated across modules.
"""  # noqa: D205, D415

from pathlib import Path

import numpy as np

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


def set_layer_roles(canopy_layers: int, soil_layers: list[float]) -> list[str]:
    """Create a list of layer roles.

    This function creates a list of strings describing the layer roles for the vertical
    dimension of the Virtual Rainforest. The vertical dimension consists of the
    following layers and roles.

    .. csv-table::
        :header: "Index", "Role", "Description"
        :widths: 5, 10, 30

        0, "above", "Canopy top height + 2 metres"
        1, "canopy", "Height of first canopy layer"
        "...", "canopy", "Height of canopy layer ``i`` "
        10, "canopy", "Height of last canopy layer"
        11, "subcanopy", "1.5 metres above ground level"
        12, "surface", "0.1 metres above ground level"
        13, "soil", "Depth of first soil layer"
        "...", "soil", "Depth of soil layer ``j``"
        15, "soil", "Depth of last soil layer"

    The number of canopy layers is taken from the canopy layer argument and the number
    of soil layers is taken from the length of the soil_layers argument, which also
    provides soil layer depths. Both are typically set in the model configuration.

    Args:
        canopy_layers: the number of canopy layers
        soil_layers: a list giving the depth of each soil layer

    Raises:
        InitialisationError: If the number of canopy layers is not a positive
            integer or the soil depths are not a list of strictly increasing, positive
            float values.

    Returns:
        List of canopy layer roles
    """

    # sanity checks for soil and canopy layers
    if not isinstance(soil_layers, list):
        to_raise = InitialisationError(
            "The soil layers must be a list of layer depths."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if len(soil_layers) < 1:
        to_raise = InitialisationError(
            "The number of soil layers must be greater than zero."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if not all([isinstance(v, (float, int)) for v in soil_layers]):
        to_raise = InitialisationError("The soil layer depths are not all numeric.")
        LOGGER.error(to_raise)
        raise to_raise

    np_soil_layer = np.array(soil_layers)
    if not (np.all(np_soil_layer > 0) and np.all(np.diff(np_soil_layer) > 0)):
        to_raise = InitialisationError(
            "Soil layer depths must be strictly increasing and positive."
        )
        LOGGER.error(to_raise)
        raise to_raise

    if not isinstance(canopy_layers, int) and not (
        isinstance(canopy_layers, float) and canopy_layers.is_integer()
    ):
        to_raise = InitialisationError("The number of canopy layers is not an integer.")
        LOGGER.error(to_raise)
        raise to_raise

    if canopy_layers < 1:
        to_raise = InitialisationError(
            "The number of canopy layer must be greater than zero."
        )
        LOGGER.error(to_raise)
        raise to_raise

    layer_roles = (
        ["above"]
        + ["canopy"] * int(canopy_layers)
        + ["subcanopy"]
        + ["surface"]
        + ["soil"] * len(soil_layers)
    )
    return layer_roles
