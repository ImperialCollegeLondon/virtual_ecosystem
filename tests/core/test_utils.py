"""Testing the utility functions."""

from logging import CRITICAL
from pathlib import Path

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


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
    from virtual_rainforest.core.utils import check_outfile

    # Configure the mock to return a specific list of files
    if out_path == "./complete_config.toml":
        mock_content = mocker.patch("virtual_rainforest.core.config.Path.exists")
        mock_content.return_value = True

    # Check that check_outfile fails as expected
    with pytest.raises(ConfigurationError):
        check_outfile(Path(out_path))

    log_check(caplog, expected_log_entries)
