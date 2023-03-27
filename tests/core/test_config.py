"""Check that the configuration system is working as expected.

At the moment the tests are generally check that the correct critical errors are thrown
when configuration files or schema are missing or incorrectly formatted. There is also a
test that a complete configuration file passes the test, which will have to be kept up
to date.
"""

import json
from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO
from pathlib import Path

import jsonschema
import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


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
def test_check_dict_leaves(d_a: dict, d_b: dict, overlap: list) -> None:
    """Checks overlapping dictionary search function."""
    from virtual_rainforest.core.config import check_dict_leaves

    assert overlap == check_dict_leaves(d_a, d_b, [])


@pytest.mark.parametrize(
    "cfg_paths,contents,expected_exception,expected_log_entries",
    [
        (
            ["Nonsense/file/location"],
            [],
            ConfigurationError,
            (
                (
                    CRITICAL,
                    "The following (user provided) config paths do not exist:",
                ),
            ),
        ),
        (
            ["."],
            [],
            ConfigurationError,
            (
                (
                    CRITICAL,
                    "The following (user provided) config folders do not contain any "
                    "toml files:",
                ),
            ),
        ),
        (
            ["", "all_config.toml"],
            ["all_config.toml"],
            ConfigurationError,
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
    caplog,
    mocker,
    shared_datadir,
    cfg_paths,
    contents,
    expected_exception,
    expected_log_entries,
):
    """Checks errors for missing config files."""
    from virtual_rainforest.core.config import collect_files

    # Configure the mock to return a specific list of files when globbing a directory
    mock_get = mocker.patch("virtual_rainforest.core.config.Path.glob")
    mock_get.return_value = [shared_datadir / fn for fn in contents]

    # Check that file collection fails as expected
    with pytest.raises(expected_exception):
        collect_files([shared_datadir / fn for fn in cfg_paths])

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "files,contents,expected_exception,expected_log_entries",
    [
        (
            [Path("fake_file1.toml")],
            [b"bshbsybdvshhd"],
            ConfigurationError,
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
            ConfigurationError,
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
    from virtual_rainforest.core.config import load_in_config_files

    # Mock the toml that is sent to the builtin open function
    mocked_toml = []
    for item in contents:
        mocked_toml = mocker.mock_open(read_data=item)
    mocker.patch("virtual_rainforest.core.config.Path.open", side_effect=mocked_toml)

    # Check that load_in_config_file fails as expected
    with pytest.raises(expected_exception):
        load_in_config_files(files)

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config_dict,expected_exception,expected_log_entries",
    [
        (
            {"core": {"grid": {"nx": 10, "ny": 10}}},
            ConfigurationError,
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
            ConfigurationError,
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
    from virtual_rainforest.core.config import find_schema

    # Check that find_schema fails as expected
    with pytest.raises(expected_exception):
        find_schema(config_dict)

    log_check(caplog, expected_log_entries)


def test_construct_combined_schema(caplog: pytest.LogCaptureFixture) -> None:
    """Checks errors for bad or missing json schema."""
    from virtual_rainforest.core.config import construct_combined_schema

    # Check that construct_combined_schema fails as expected
    with pytest.raises(ConfigurationError):
        construct_combined_schema(["a_stupid_module_name"])

    expected_log_entries = (
        (
            CRITICAL,
            "Expected a schema for a_stupid_module_name module configuration, "
            "it was not provided!",
        ),
    )

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "file_path,expected_log_entries",
    [
        (
            "default_config.toml",  # File entirely of defaults
            (
                (INFO, "Configuration files successfully validated!"),
                (INFO, "Saving all configuration details to"),
            ),
        ),
        (
            "all_config.toml",  # File with no defaults
            (
                (INFO, "Configuration files successfully validated!"),
                (INFO, "Saving all configuration details to"),
            ),
        ),
    ],
)
def test_final_validation_log(caplog, shared_datadir, file_path, expected_log_entries):
    """Checks that validation passes as expected and produces the correct output."""
    from virtual_rainforest.core.config import validate_config

    outfile = shared_datadir / "complete_config.toml"
    validate_config([shared_datadir / file_path], outfile)

    # Remove generated output file
    # As a bonus tests that output file was generated correctly + to the right location
    outfile.unlink()

    # Then check that the correct (critical error) log messages are emitted
    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "schema_name,schema,expected_exception,expected_log_entries",
    [
        (
            "core",
            "",
            ValueError,
            (
                (
                    CRITICAL,
                    "The module schema for core is already registered",
                ),
            ),
        ),
        (
            "test",
            "najsnjasnda",
            json.JSONDecodeError,
            (
                (ERROR, "JSON error in schema file"),
                (CRITICAL, "Schema registration for test failed: check log"),
            ),
        ),
        (
            "bad_module_1",
            '{"type": "hobbit", "properties": {"bad_module_1": {}}}',
            jsonschema.SchemaError,
            (
                (ERROR, "Module schema invalid in: "),
                (CRITICAL, "Schema registration for bad_module_1 failed: check log"),
            ),
        ),
        (
            "bad_module_2",
            '{"type": "object", "properties": {"bad_module_1": {}}}',
            ValueError,
            (
                (ERROR, "Missing key in module schema bad_module_2:"),
                (CRITICAL, "Schema registration for bad_module_2 failed: check log"),
            ),
        ),
        (
            "bad_module_3",
            '{"type": "object", "properties": {"bad_module_3": {}}}',
            ValueError,
            (
                (ERROR, "Missing key in module schema bad_module_3"),
                (CRITICAL, "Schema registration for bad_module_3 failed: check log"),
            ),
        ),
    ],
)
def test_register_schema_errors(
    caplog, mocker, schema_name, schema, expected_exception, expected_log_entries
):
    """Test that the schema registering decorator throws the correct errors."""

    from virtual_rainforest.core.config import register_schema

    data = mocker.mock_open(read_data=schema)
    mocker.patch("builtins.open", data)

    # Check that construct_combined_schema fails as expected
    with pytest.raises(expected_exception):
        register_schema(schema_name, "file_path")

    # Then check that the correct (critical error) log messages are emitted
    log_check(caplog, expected_log_entries)


def test_extend_with_default():
    """Test that validator has been properly extended to allow addition of defaults."""
    from virtual_rainforest.core.config import ValidatorWithDefaults

    # Check that function adds a function with the right name in the right location
    TestValidator = ValidatorWithDefaults({"str": {}})
    assert TestValidator.VALIDATORS["properties"].__name__ == "set_defaults"


@pytest.mark.parametrize(
    "config_dict,nx,raises,expected_log_entries",
    [
        (
            {},
            100,
            does_not_raise(),
            (),
        ),
        (
            {"core": {"grid": {"nx": 125}}},
            125,
            does_not_raise(),
            (),
        ),
        (
            {"core": {"grid": {"nx": -125, "ny": -10}}},
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "[core][grid][nx]: -125 is less than or equal to the minimum of 0",
                ),
                (
                    ERROR,
                    "[core][grid][ny]: -10 is less than or equal to the minimum of 0",
                ),
                (
                    CRITICAL,
                    "Validation of core configuration files failed see above errors",
                ),
            ),
        ),
    ],
)
def test_add_core_defaults(caplog, config_dict, nx, raises, expected_log_entries):
    """Test that default values are properly added to the core configuration."""
    from virtual_rainforest.core.config import add_core_defaults

    # Check that find_schema fails as expected
    with raises:
        add_core_defaults(config_dict)

    log_check(caplog, expected_log_entries)

    # If configuration occurs check that nx has the right value
    if nx is not None:
        assert config_dict["core"]["grid"]["nx"] == nx


def test_missing_core_schema(caplog, mocker):
    """Test that core schema not being in the registry is handled properly."""
    from virtual_rainforest.core.config import add_core_defaults

    mocker.patch("virtual_rainforest.core.config.SCHEMA_REGISTRY", {})

    # Check that find_schema fails as expected
    with pytest.raises(ConfigurationError):
        add_core_defaults({})

    expected_log_entries = (
        (
            CRITICAL,
            "Expected a schema for core module configuration, it was not provided!",
        ),
    )

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "config_dict,plant_int,raises,expected_log_entries",
    [
        (
            {"plants": {"ftypes": []}},
            1,
            does_not_raise(),
            (),
        ),
        (
            {"plants": {"ftypes": [], "a_plant_integer": 333}},
            333,
            does_not_raise(),
            (),
        ),
        (
            {"soil": {"no_layers": -1}},
            None,
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "[plants]: 'ftypes' is a required property",
                ),
                (
                    ERROR,
                    "[soil]: Additional properties are not allowed ('no_layers' was "
                    "unexpected)",
                ),
                (
                    CRITICAL,
                    "Validation of complete configuration files failed see above "
                    "errors",
                ),
            ),
        ),
    ],
)
def test_validate_with_defaults(
    caplog, config_dict, plant_int, raises, expected_log_entries
):
    """Test that addition of defaults values during configuration works as desired."""
    from virtual_rainforest.core.config import (
        construct_combined_schema,
        validate_with_defaults,
    )

    comb_schema = construct_combined_schema(["core", "plants", "soil"])

    # Check that find_schema fails as expected
    with raises:
        validate_with_defaults(config_dict, comb_schema)

    log_check(caplog, expected_log_entries)

    # If configuration occurs check that plant integer has the right value
    if plant_int is not None:
        assert config_dict["plants"]["a_plant_integer"] == plant_int
