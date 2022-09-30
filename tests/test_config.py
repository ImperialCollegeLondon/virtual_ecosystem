"""Check that the configuration system is working as expected.

At the moment the tests are generally check that the correct critical errors are thrown
when configuration files or schema are missing or incorrectly formatted. There is also a
test that a complete configuration file passes the test, which will have to be kept up
to date.
"""

from logging import CRITICAL, INFO
from pathlib import Path

import pytest

import virtual_rainforest.core.config as config
from virtual_rainforest.core.config import register_schema

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
    "file_name,expected_exception,expected_log_entries",
    [
        (
            "complete_config",
            OSError,
            (
                (
                    CRITICAL,
                    "A config file in the specified configuration folder already makes "
                    "use of the specified output file name (complete_config.toml), this"
                    " file should either be renamed or deleted!",
                ),
            ),
        ),
    ],
)
def test_check_outfile(
    caplog, mocker, file_name, expected_exception, expected_log_entries
):
    """Check that an error is logged if an output file is already saved."""

    # Configure the mock to return a specific list of files
    mock_content = mocker.patch("virtual_rainforest.core.config.Path.iterdir")
    mock_content.return_value = [Path(f"{file_name}.toml")]

    # Check that check_outfile fails as expected
    with pytest.raises(expected_exception):
        config.check_outfile(".", file_name)

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_paths,contents,expected_exception,expected_log_entries",
    [
        (
            ["Nonsense/file/location"],
            [],
            OSError,
            (
                (
                    CRITICAL,
                    "The following (user provided) config paths do not exist:\n"
                    "['Nonsense/file/location']",
                ),
            ),
        ),
        (
            ["."],
            [],
            OSError,
            (
                (
                    CRITICAL,
                    "The following (user provided) config folders do not contain any "
                    "toml files:\n['.']",
                ),
            ),
        ),
        (
            ["tests/fixtures/", "tests/fixtures/all_config.toml"],
            [Path("tests/fixtures/all_config.toml")],
            RuntimeError,
            (
                (
                    CRITICAL,
                    "A total of 1 config files are specified more than once (possibly "
                    "indirectly)",
                ),
            ),
        ),
    ],
)
def test_collect_files(
    caplog, mocker, cfg_paths, contents, expected_exception, expected_log_entries
):
    """Checks errors for missing config files."""

    # Configure the mock to return a specific list of files
    mock_get = mocker.patch("virtual_rainforest.core.config.Path.glob")
    mock_get.return_value = contents

    # Check that file collection fails as expected
    with pytest.raises(expected_exception):
        config.collect_files(cfg_paths)

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "files,contents,expected_exception,expected_log_entries",
    [
        (
            [Path("fake_file1.toml")],
            [b"bshbsybdvshhd"],
            RuntimeError,
            (
                (
                    CRITICAL,
                    "Configuration file fake_file1.toml is incorrectly formatted. "
                    "Failed with the following message:\nExpected '=' after a key in "
                    "a key/value pair (at end of document)",
                ),
            ),
        ),
        (
            [Path("fake_file1.toml"), Path("fake_file2.toml")],
            [b"[core.grid]\nnx = 10", b"[core.grid]\nnx = 12"],
            RuntimeError,
            (
                (
                    CRITICAL,
                    "The following tags are defined in multiple config files:\n"
                    "core.grid.nx defined in both fake_file2.toml and fake_file1.toml",
                ),
            ),
        ),
    ],
)
def test_load_in_config_files(
    caplog, mocker, files, contents, expected_exception, expected_log_entries
):
    """Check errors for incorrectly formatted config files."""

    # Mock the toml that is sent to the builtin open function
    mocked_toml = []
    for item in contents:
        mocked_toml = mocker.mock_open(read_data=item)
    mocker.patch("virtual_rainforest.core.config.Path.open", side_effect=mocked_toml)

    # Check that load_in_config_file fails as expected
    with pytest.raises(expected_exception):
        config.load_in_config_files(files)

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config_dict,expected_exception,expected_log_entries",
    [
        (
            {"core": {"grid": {"nx": 10, "ny": 10}}},
            KeyError,
            (
                (
                    CRITICAL,
                    "Core configuration does not specify which other modules should be "
                    "configured!",
                ),
            ),
        ),
        (
            {"core": {"modules": ["soil", "soil"]}},
            RuntimeError,
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
def test_find_schema(caplog, config_dict, expected_exception, expected_log_entries):
    """Check errors in finding module schema."""

    # Check that find_schema fails as expected
    with pytest.raises(expected_exception):
        config.find_schema(config_dict)

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "modules,expected_exception,expected_log_entries",
    [
        (
            ["a_stupid_module_name"],
            RuntimeError,
            (
                (
                    CRITICAL,
                    "Expected a schema for a_stupid_module_name module configuration, "
                    "it was not provided!",
                ),
            ),
        ),
        (
            ["bad_module_1", "core"],
            KeyError,
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
def test_construct_combined_schema(
    caplog, modules, expected_exception, expected_log_entries
):
    """Checks errors for bad or missing json schema."""

    # Check that construct_combined_schema fails as expected
    with pytest.raises(expected_exception):
        config.construct_combined_schema(modules)

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
                    "Saving all configuration details to ./complete_config.toml",
                ),
            )
        ),
    ],
)
def test_final_validation_log(caplog, expected_log_entries):
    """Checks that validation passes as expected and produces the correct output."""

    # Then check that the correct (critical error) log messages are emitted
    config.validate_config(["tests/fixtures"], out_file_name="complete_config")
    log_check(caplog, expected_log_entries)

    # Remove generated output file
    # As a bonus tests that output file was generated correctly + to the right location
    Path("./complete_config.toml").unlink()

    # Check that final config has been within nested dictionary
    assert type(config.COMPLETE_CONFIG["config"]) == dict


# NOT SURE HOW TO CATCH LOGGED OUTPUT IN THIS CASE
# TODO - EXTEND THIS TO ALSO CHECK LOGGER OUTPUT
@pytest.mark.parametrize(
    "schema_name,schema, expected_exception",
    [
        ("core", {}, ValueError),
        (
            "test",
            "najsnjasnda",
            OSError,
        ),
        (
            "bad_module_2",
            {"type": "object", "propertie": {"bad_module_2": {}}},
            KeyError,
        ),
    ],
)
def test_register_schema_errors(schema_name, schema, expected_exception):
    """Test that the schema registering decorator throws the correct errors."""
    # Check that construct_combined_schema fails as expected
    with pytest.raises(expected_exception):

        @register_schema(schema_name)
        def to_be_decorated():
            return schema

        to_be_decorated()
