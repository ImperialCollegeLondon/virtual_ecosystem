"""Testing the utility functions."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL
from pathlib import Path

import numpy as np
import pytest

from tests.conftest import log_check
from virtual_ecosystem.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    "out_path,expected_log_entries",
    [
        (
            "./complete_config.toml",
            (
                (
                    CRITICAL,
                    "A file in the user specified output folder (.) already makes use "
                    "of the specified output file name (complete_config.toml), this "
                    "file should either be renamed or deleted!",
                ),
            ),
        ),
        (
            "bad_folder/complete_config.toml",
            (
                (
                    CRITICAL,
                    "The user specified output directory (bad_folder) doesn't exist!",
                ),
            ),
        ),
        (
            "pyproject.toml/complete_config.toml",
            (
                (
                    CRITICAL,
                    "The user specified output folder (pyproject.toml) isn't a "
                    "directory!",
                ),
            ),
        ),
    ],
)
def test_check_outfile(caplog, mocker, out_path, expected_log_entries):
    """Check that an error is logged if an output file is already saved."""
    from virtual_ecosystem.core.utils import check_outfile

    # Configure the mock to return a specific list of files
    if out_path == "./complete_config.toml":
        mock_content = mocker.patch("virtual_ecosystem.core.utils.Path.exists")
        mock_content.return_value = True

    # Check that check_outfile fails as expected
    with pytest.raises(ConfigurationError):
        check_outfile(Path(out_path))

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    argnames="vars, exp_result, exp_msg",
    argvalues=[
        pytest.param(
            {"a": np.ones(12), "b": np.ones(12)},
            does_not_raise(),
            "Variables form a data frame",
            id="correct",
        ),
        pytest.param(
            {"a": np.ones((12, 2)), "b": np.ones(12)},
            pytest.raises(ValueError),
            "Variables not one dimensional: a",
            id="not all one dimensional",
        ),
        pytest.param(
            {"a": np.ones(14), "b": np.ones(12)},
            pytest.raises(ValueError),
            "Variables of unequal length: 12, 14",
            id="not equal length",
        ),
    ],
)
def test_confirm_variables_form_data_frame(vars, exp_result, exp_msg):
    """Test the data frame validation mechanism."""

    from virtual_ecosystem.core.utils import confirm_variables_form_data_frame

    with exp_result as excep:
        confirm_variables_form_data_frame(vars)

    if not isinstance(exp_result, does_not_raise):
        assert str(excep.value) == exp_msg


@pytest.mark.parametrize(
    argnames="var_arrays, exp_result, context_handler, err_msg",
    argvalues=[
        pytest.param(
            {"a": np.arange(12), "b": np.arange(12, 24), "gp": np.repeat([2, 1], 6)},
            {
                1: {"a": np.arange(6, 12), "b": np.arange(18, 24)},
                2: {"a": np.arange(6), "b": np.arange(12, 18)},
            },
            does_not_raise(),
            None,
            id="good",
        ),
        pytest.param(
            {"a": np.arange(12), "b": np.arange(12, 24), "grp": np.repeat([2, 1], 6)},
            None,
            pytest.raises(ValueError),
            "Grouping variable gp not found in: a, b, grp",
            id="groupby not found",
        ),
        pytest.param(
            {"a": np.arange(11), "b": np.arange(12, 24), "grp": np.repeat([2, 1], 6)},
            None,
            pytest.raises(ValueError),
            "Variables of unequal length: 11, 12",
            id="not a dataframe",
        ),
    ],
)
def test_split_arrays_by_grouping_variable(
    var_arrays, exp_result, context_handler, err_msg
):
    """Test the  split_arrays_by_grouping_variable function."""

    from virtual_ecosystem.core.utils import split_arrays_by_grouping_variable

    with context_handler as excep:
        result = split_arrays_by_grouping_variable(var_arrays=var_arrays, group_by="gp")

        # Annoyingly awkward to test equality on dict of numpy arrays
        for cell, split_values in exp_result.items():
            for var, var_values in split_values.items():
                np.testing.assert_array_equal(result[cell][var], var_values)

    if not isinstance(context_handler, does_not_raise):
        assert str(excep.value) == err_msg
