"""The ``core.utils`` module contains functions that are used across the
Virtual Ecosystem, but which don't have a natural home in a specific module. Adding
functions here can be a good way to reduce the amount boiler plate code generated for
tasks that are repeated across modules.
"""  # noqa: D205

from pathlib import Path

import numpy as np

from virtual_ecosystem.core.exceptions import ConfigurationError, InitialisationError
from virtual_ecosystem.core.logger import LOGGER


def check_outfile(merge_file_path: Path) -> None:
    """Check that final output file is not already in the output folder.

    Args:
        merge_file_path: Path to save merged config file to (i.e. folder location + file
            name)

    Raises:
        ConfigurationError: If the path is invalid or the final output file already
            exists.
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


def set_layer_roles(
    canopy_layers: int = 10, soil_layers: list[float] = [-0.5, -1.0]
) -> list[str]:
    """Create a list of layer roles.

    This function creates a list of strings describing the layer roles for the vertical
    dimension of the Virtual Ecosystem. These roles are used with data arrays that have
    that vertical dimension: the roles then show what information is being captured at
    different heights through that vertical dimension. Within the model, ground level is
    at height 0 metres: above ground heights are positive and below ground heights are
    negative. At present, models are expecting two soil layers: the top layer being
    where microbial activity happens (usually around 0.5 metres below ground) and the
    second layer where soil temperature equals annual mean air temperature (usually
    around 1 metre below ground).

    There are five layer roles capture data:

    * ``above``:  at ~2 metres above the top of the canopy.
    * ``canopy``: within each canopy layer. The maximum number of canopy layers is set
      by the ``canopy_layers`` argument and is a configurable part of the model. The
      heights of these layers are modelled from the plant community data.
    * ``subcanopy``: at ~1.5 metres above ground level.
    * ``surface``: at ~0.1 metres above ground level.
    * ``soil``: at fixed depths within the soil. These depths are set in the
      ``soil_layers`` argument and are a configurable part of the model.

    With the default values, this function gives the following layer roles.

    .. csv-table::
        :header: "Index", "Role", "Description"
        :widths: 5, 10, 30

        0, "above", "Canopy top height + 2 metres"
        1, "canopy", "Height of top of the canopy (1)"
        "...", "canopy", "Height of canopy layer ``i``"
        10, "canopy", "Height of the bottom canopy layer (10)"
        11, "subcanopy", "1.5 metres above ground level"
        12, "surface", "0.1 metres above ground level"
        13, "soil", "First soil layer at -0.5 metres"
        14, "soil", "First soil layer at -1.0 metres"

    Args:
        canopy_layers: the number of canopy layers
        soil_layers: a list giving the depth of each soil layer as a sequence of
            negative and strictly decreasing values.

    Raises:
        InitialisationError: If the number of canopy layers is not a positive
            integer or the soil depths are not a list of strictly decreasing, negative
            float values.

    Returns:
        A list of vertical layer role names
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

    if not all([isinstance(v, float | int) for v in soil_layers]):
        to_raise = InitialisationError("The soil layer depths are not all numeric.")
        LOGGER.error(to_raise)
        raise to_raise

    np_soil_layer = np.array(soil_layers)
    if not (np.all(np_soil_layer < 0) and np.all(np.diff(np_soil_layer) < 0)):
        to_raise = InitialisationError(
            "Soil layer depths must be strictly decreasing and negative."
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
