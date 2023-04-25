"""Testing the utility functions."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR
from pathlib import Path

import pytest
from numpy import timedelta64

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError


@pytest.mark.parametrize(
    argnames=["config", "raises", "timestep", "expected_log"],
    argvalues=[
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 hours",
                    }
                },
            },
            does_not_raise(),
            timedelta64(720, "m"),
            (),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 interminable hours",
                    }
                },
            },
            pytest.raises(InitialisationError),
            None,
            (
                (
                    ERROR,
                    "Model timing error: 'interminable' is not defined in the unit "
                    "registry",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "12 kilograms",
                    }
                },
            },
            pytest.raises(InitialisationError),
            None,
            (
                (
                    ERROR,
                    "Model timing error: Cannot convert from 'kilogram' ([mass]) to "
                    "'second' ([time])",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "30 minutes",
                    }
                },
            },
            pytest.raises(ConfigurationError),
            None,
            (
                (
                    ERROR,
                    "The update interval is shorter than the model's lower bound",
                ),
            ),
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "3 months",
                    }
                },
            },
            pytest.raises(ConfigurationError),
            None,
            (
                (
                    ERROR,
                    "The update interval is longer than the model's upper bound",
                ),
            ),
        ),
    ],
)
def test_extract_update_interval(caplog, config, raises, timestep, expected_log):
    """Tests timing details extraction utility."""

    from virtual_rainforest.core.utils import extract_update_interval

    with raises:
        update_interval = extract_update_interval(config, "1 hour", "1 month")
        assert update_interval == timestep

    log_check(caplog, expected_log)


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
