"""The ``core.utils`` module contains functions that are used across the
Virtual Rainforest, but which don't have a natural home in a specific module. At the
moment, this module only contains a single function, but it will probably expand in
future. Adding functions here can be a good way to reduce the amount boiler plate code
generated for tasks that are repeated across modules.
"""  # noqa: D205, D415

from pathlib import Path
from typing import Any

import pint
from numpy import timedelta64

from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError
from virtual_rainforest.core.logger import LOGGER


def extract_update_interval(config: dict[str, Any]) -> timedelta64:
    """Function to extract the timing details required to setup a specific model.

    Args:
        config: The configuration for the Virtual Rainforest simulation.

    Returns:
        The update interval for the overall model

    Raises:
        InitialisationError: If the model timing cannot be properly extracted
    """

    try:
        raw_interval = pint.Quantity(config["core"]["timing"]["update_interval"]).to(
            "seconds"
        )
        # Round raw time interval to nearest second
        update_interval = timedelta64(round(raw_interval.magnitude), "s")
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError) as excep:
        LOGGER.error("Model timing error: %s" % str(excep))
        raise InitialisationError() from excep

    return update_interval


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
