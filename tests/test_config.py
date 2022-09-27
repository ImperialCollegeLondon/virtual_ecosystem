"""Check that the configuration system is working as expected.

At the moment the tests are generally check that the correct critical errors are thrown
when configuration files or schema are missing or incorrectly formatted. There is also a
test that a complete configuration file passes the test, which will have to be kept up
to date.
"""

import os
from logging import CRITICAL, INFO

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


@pytest.mark.parametrize(
    "files,contents,expected_log_entries",
    [
        (
            ["core.toml"],
            [b"bshbsybdvshhd"],
            (
                (
                    CRITICAL,
                    "Configuration file core.toml is incorrectly formatted.",
                ),
            ),
        ),
        (
            ["core.toml"],
            [b"[core.grid]\nnx = 10\nny = 10"],
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
            [b"[core]\nmodules = ['soil','soil']"],
            (
                (
                    CRITICAL,
                    "The list of modules to configure given in the core configuration "
                    "file repeats 1 names!",
                ),
            ),
        ),
        (
            ["core1.toml", "core2.toml"],
            [b"[core.grid]\nnx = 10", b"[core.grid]\nnx = 12"],
            (
                (
                    CRITICAL,
                    "The following tags are defined in multiple config files:\n"
                    "core.grid.nx defined in both core2.toml and core1.toml",
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
    mocked_toml = []
    for item in contents:
        mocked_toml = mocker.mock_open(read_data=item)
    mocker.patch("builtins.open", side_effect=mocked_toml)

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config("tests")
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "files,content,expected_log_entries",
    [
        (
            ["core.toml"],
            b"[core]\nmodules = ['a_stupid_module_name']",
            (
                (
                    CRITICAL,
                    "Expected a schema for a_stupid_module_name module configuration, "
                    "it was not provided!",
                ),
            ),
        ),
        (
            ["core.toml"],
            b"[core]\nmodules = ['bad_module_1']",
            (
                (
                    CRITICAL,
                    "The schema for bad_module_1 does not set the module as a required "
                    "field, so validation cannot occur!",
                ),
            ),
        ),
    ],
)
def test_bad_schema(caplog, mocker, files, content, expected_log_entries):
    """Checks errors for bad or missing json schema."""

    # Use mock to override "no files found" error
    mock_get = mocker.patch("virtual_rainforest.core.config.os.listdir")
    mock_get.return_value = files

    # Mock toml content to look for specific modules
    mocked_toml = mocker.mock_open(read_data=content)
    mocker.patch("builtins.open", side_effect=mocked_toml)

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config("tests")
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "expected_log_entries",
    [
        (
            (
                (
                    INFO,
                    "Configuration files successfully validated!",
                ),
                (
                    INFO,
                    "Saving all configuration details to tests/fixtures/"
                    "complete_config.toml",
                ),
            )
        ),
    ],
)
def test_final_validation_log(caplog, expected_log_entries):
    """Checks that validation passes as expected and produces the correct output."""

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config(
        "tests/fixtures", out_file_name="complete_config", in_files=["all_config.toml"]
    )
    log_check(caplog, expected_log_entries)

    # Remove generated output file
    # As a bonus tests that output file was generated correctly + to the right location
    os.remove("tests/fixtures/complete_config.toml")

    # Check that final config has been within nested dictionary
    assert type(config.COMPLETE_CONFIG["config"]) == dict
