"""The ``core.utils`` module contains functions that are used across the
Virtual Ecosystem, but which don't have a natural home in a specific module. Adding
functions here can be a good way to reduce the amount boiler plate code generated for
tasks that are repeated across modules.
"""  # noqa: D205

from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from virtual_ecosystem.core.exceptions import ConfigurationError
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


def split_arrays_by_grouping_variable(
    arrays: list[NDArray], group_by: NDArray
) -> dict[Any, list[NDArray]]:
    """Split equal length arrays by a grouping variable.

    This function takes a set of one dimensional arrays of equal length - forming a data
    frame - and splits the values into lists of subarrays by a grouping variable. It
    sorts the arrays by the grouping variable before splitting the data.

    Args:
        arrays: A list of equal length, one dimensional arrays to be split.
        group_by: A grouping variable to be used to split the arrays.

    Returns:
        A dictionary of lists of subarrays for each group, keyed by unique values in the
        grouping variable.
    """

    # Get a sort order for the arrays based on the split_on variable
    sort_order = np.argsort(group_by)

    # Apply that sort order to all the arrays
    arrays = [arr[sort_order] for arr in arrays]

    # Get the indices where the group_by array changes and then split
    split_at = np.where(np.diff(group_by[sort_order]) > 0)[0] + 1

    # Split the arrays and then package them by the grouping values
    split_arrays = [np.split(arr, split_at) for arr in arrays]
    group_value = group_by[sort_order][np.insert(split_at, 0, 0)]
    arrays_by_split_var = zip(*split_arrays)

    return {
        gp.item(): arr_list for gp, arr_list in zip(group_value, arrays_by_split_var)
    }
