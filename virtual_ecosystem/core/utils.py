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


def confirm_variables_form_data_frame(var_arrays: dict[str, NDArray]) -> None:
    """Check a list of arrays form a data frame.

    This is a utility method to check if a set of arrays form a data frame: a set of
    equal length, one dimensional arrays, providing consistent tuples of values across
    the variables.

    .. note::

        This function and
        :meth:`~virtual_ecosystem.core.utils.split_arrays_by_grouping_variable` could
        be methods of the
        :class:`~virtual_ecosystem.core.data.Data` class, but then would only be
        usable for arrays stored within a ``Data`` instance. At present, they are
        provided within the :mod:`~virtual_ecosystem.core.utils` module so that they can
        be used independently.

    Args:
        var_arrays: A dictionary of arrays keyed by variable name.

    Raises:
        ValueError: The input values do not form a data frame.
    """

    # All vars one dimensional
    data_not_one_d = [ky for ky, val in var_arrays.items() if val.ndim > 1]
    if data_not_one_d:
        raise ValueError(
            f"Variables not one dimensional: {', '.join(sorted(data_not_one_d))}"
        )

    # All vars equal sized
    shapes = sorted(set(str(val.shape[0]) for val in var_arrays.values()))
    if len(shapes) != 1:
        raise ValueError(f"Variables of unequal length: {', '.join(shapes)}")


def split_arrays_by_grouping_variable(
    var_arrays: dict[str, NDArray], group_by: str
) -> dict[Any, dict[str, NDArray]]:
    """Split a data frame by a grouping variable.

    This function takes a set of one dimensional arrays of equal length - forming a data
    frame - and splits the values into lists of subarrays by a grouping variable. It
    sorts the arrays by the grouping variable before splitting the data.

    .. note::

        This function and
        :meth:`~virtual_ecosystem.core.utils.confirm_variables_form_data_frame` could
        be methods of the
        :class:`~virtual_ecosystem.core.data.Data` class, but then would only be
        usable for arrays stored within a ``Data`` instance. At present, they are
        provided within the :mod:`~virtual_ecosystem.core.utils` module so that they can
        be used independently.

    Args:
        var_arrays: A dictionary of arrays keyed by variable name.
        group_by: The variable name to be used to split the arrays.

    Returns:
        A dictionary of lists of subarrays for each group, keyed by unique values in the
        grouping variable.
    """

    # Validate the inputs form a data frame and that the grouping variable is provided
    try:
        confirm_variables_form_data_frame(var_arrays=var_arrays)
    except ValueError:
        raise

    if group_by not in var_arrays:
        raise ValueError(
            f"Grouping variable {group_by} not found in: {', '.join(var_arrays)}"
        )
    group_var = var_arrays.pop(group_by)

    # Get a sort order for the arrays based on the split_on variable
    # `stable` is being used here primarily to avoid sorting order differences in
    # testing across platforms
    sort_order = np.argsort(group_var, kind="stable")

    # Apply that sort order to all the arrays
    var_arrays = {ky: arr[sort_order] for ky, arr in var_arrays.items()}

    # Get the indices where the grouping array changes and the grouping variable value
    split_at = np.where(np.diff(group_var[sort_order]) > 0)[0] + 1
    group_values = group_var[sort_order][np.insert(split_at, 0, 0)]

    split_data: dict[Any, dict[str, NDArray]] = {ky: dict() for ky in group_values}

    for var_name, values in var_arrays.items():
        split_values = np.split(values, split_at)
        for group_id, group_vals in zip(group_values, split_values):
            split_data[group_id][var_name] = group_vals

    return split_data
