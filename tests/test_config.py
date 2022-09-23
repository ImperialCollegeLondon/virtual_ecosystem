"""A PLACEHOLDER DOCSTRING FOR THE TIME BEING.

MORE DETAILS BELOW HERE IF NECESSARY
TODO - EITHER FILL OUT DOC STRINGS OR CHANGE OPTIONS TO DELETE THEM
"""

from logging import CRITICAL

import pytest

import virtual_rainforest.core.config as config

from .conftest import log_check


# test that function checking overlap of nested dictionaries works correctly
@pytest.mark.parametrize(
    "d_a,d_b,overlap",
    [
        ({"d1": {"d2": 3}}, {"d3": {"d2": 3}}, []),
        ({"d1": {"d2": 3}}, {"d1": {"d3": 3}}, []),
        ({"d1": 1}, {"d1": 2}, ["d1"]),
        ({"d1": 1}, {"d1": {"d2": 1}}, ["d1"]),
        ({"d1": {"d2": 3, "d3": 12}}, {"d1": {"d3": 7}}, ["d1.d3"]),
        (
            {"d1": {"d2": {"d3": 12, "d4": 5}}},
            {"d1": {"d2": {"d3": 5, "d4": 7}}},
            ["d1.d2.d3", "d1.d2.d4"],
        ),
    ],
)
def test_check_dict_leaves(d_a, d_b, overlap):
    """EXAMPLE DOC STRING."""
    assert overlap == config.check_dict_leaves(d_a, d_b, [])


# DOES CRITICAL ERROR ORDER MATTER PARTICUALRLY
# test that errors relating to correct files not being found fire correctly
@pytest.mark.parametrize(
    "contents,file_list,expected_log_entries",
    [
        ([], [], ((CRITICAL, "No toml files found in the config folder provided!"),)),
        (
            ["complete_config.toml"],
            [],
            (
                (
                    CRITICAL,
                    "A config file in the specified configuration folder already makes "
                    "use of the specified output file name (complete_config.toml), this"
                    " file should either be renamed or deleted!",
                ),
            ),
        ),
        (
            ["plants.toml", "core.toml"],
            ["plant_with_hydro.toml"],
            (
                (
                    CRITICAL,
                    "The files the user specified to be read from are not all found in "
                    "tests. The following files are missing:\n"
                    "['plant_with_hydro.toml']",
                ),
            ),
        ),
        (
            [],
            ["core.toml"],
            (
                (
                    CRITICAL,
                    "The files the user specified to be read from are not all found in "
                    "tests. The following files are missing:\n['core.toml']",
                ),
            ),
        ),
    ],
)
def test_missing_config_files(
    caplog, mocker, contents, file_list, expected_log_entries
):
    """EXAMPLE DOC STRING."""

    # Configure the mock to return a specific list of files
    mock_get = mocker.patch("virtual_rainforest.core.config.os.listdir")
    mock_get.return_value = contents

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config("tests", in_files=file_list)
    log_check(caplog, expected_log_entries)


# PROBABLY CAN SUPPLY SIMPLE STRINGS HERE AS TOML FILES

# INCORRECTLY FORMATTED TOML
# TAGS REPEATED ACROSS MULTIPLE TOML FILES
# MODULE TOML MISSING FROM CORE
# CORE.MODULE REPEATS NAMES
# def test_bad_config_files():

# THESE ERRORS NEED MORE THOUGHT
# MODULE SCHEMA IN REGISTRY MISSING
# MISSING REQUIRED MODULE KEY IN SCHEMA
# MODULE NOT IN SCHEMA REGISTRY
# FAILED VALIDATION
