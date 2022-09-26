"""A PLACEHOLDER DOCSTRING FOR THE TIME BEING.

MORE DETAILS BELOW HERE IF NECESSARY
TODO - EITHER FILL OUT DOC STRINGS OR CHANGE OPTIONS TO DELETE THEM
"""

from logging import CRITICAL

import pytest

import virtual_rainforest.core.config as config

from .conftest import log_check


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
    """Checks overlapping dictionary search function."""
    assert overlap == config.check_dict_leaves(d_a, d_b, [])


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
    """Checks errors for missing config files."""

    # Configure the mock to return a specific list of files
    mock_get = mocker.patch("virtual_rainforest.core.config.os.listdir")
    mock_get.return_value = contents

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config("tests", in_files=file_list)
    log_check(caplog, expected_log_entries)


# TAGS REPEATED ACROSS MULTIPLE TOML FILES
# mock_toml.side_effect == contents
@pytest.mark.parametrize(
    "files,contents,expected_log_entries",
    [
        (
            ["core.toml"],
            b"bshbsybdvshhd",
            (
                (
                    CRITICAL,
                    "Configuration file core.toml is incorrectly formatted.",
                ),
            ),
        ),
        (
            ["core.toml"],
            b"[config.core.grid]\nnx = 10\nny = 10",
            (
                (
                    CRITICAL,
                    "Core configuration does not specify which other modules should be "
                    "configured!",
                ),
            ),
        ),
        (
            ["core.toml"],
            b"[config.core]\nmodules = ['soil','soil']",
            (
                (
                    CRITICAL,
                    "The list of modules to configure given in the core configuration "
                    "file repeats 1 names!",
                ),
            ),
        ),
    ],
)
def test_bad_config_files(caplog, mocker, files, contents, expected_log_entries):
    """Checks errors for incorrectly formatted config files."""

    # Use mock to override "no files found" error
    mock_get = mocker.patch("virtual_rainforest.core.config.os.listdir")
    mock_get.return_value = files

    # Mock the toml that is sent to the builtin open function
    mocked_toml = mocker.mock_open(read_data=contents)
    mocker.patch("builtins.open", mocked_toml)

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config("tests")
    log_check(caplog, expected_log_entries)


# THESE ERRORS NEED MORE THOUGHT
# DEFINE A BUNCH OF BAD SCHEMA IN FIXTURES AND ADD THEM TO THE REGISTRY
# THESE CAN GENERATE MOST OF THE SCHEMA
# MODULE SCHEMA IN REGISTRY MISSING
# MISSING REQUIRED MODULE KEY IN SCHEMA
# MODULE NOT IN SCHEMA REGISTRY

# SUCCESSFUL VALIDATION => CHECK THAT LOGGING IS CORRECT, AND THAT THINGS GET OUTPUT
# AS EXPECTED
# => Could just go with good, bad, and incorrectly formatted
