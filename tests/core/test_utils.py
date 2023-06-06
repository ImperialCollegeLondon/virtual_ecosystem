"""Testing the utility functions."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR
from pathlib import Path

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError, InitialisationError


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


@pytest.mark.parametrize(
    "soil_layers, canopy_layers, raises, exp_log",
    [
        (
            2,
            10,
            does_not_raise(),
            (),
        ),
        (
            -2,
            10,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "There has to be at least one soil layer in the abiotic model!",
                ),
            ),
        ),
        (
            2,
            -3,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "There has to be at least one canopy layer in the abiotic model!",
                ),
            ),
        ),
        (
            2.5,
            10,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The number of soil layers must be an integer!",
                ),
            ),
        ),
        (
            2,
            3.4,
            pytest.raises(InitialisationError),
            (
                (
                    ERROR,
                    "The number of canopy layers must be an integer!",
                ),
            ),
        ),
    ],
)
def test_set_layer_roles(soil_layers, canopy_layers, raises, caplog, exp_log):
    """Test correct order of layers."""
    from virtual_rainforest.core.utils import set_layer_roles

    with raises:
        result = set_layer_roles(canopy_layers, soil_layers)

        assert result == (
            ["above"] + ["canopy"] * 10 + ["subcanopy"] + ["surface"] + ["soil"] * 2
        )

    # Final check that expected logging entries are produced
    log_check(caplog, exp_log)
