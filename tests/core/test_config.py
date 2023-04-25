"""Check that the configuration system is working as expected.

At the moment the tests are generally check that the correct critical errors are thrown
when configuration files or schema are missing or incorrectly formatted. There is also a
test that a complete configuration file passes the test, which will have to be kept up
to date.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO
from pathlib import Path

import pytest

from tests.conftest import log_check
from virtual_rainforest.core.exceptions import ConfigurationError


@pytest.mark.parametrize(
    "dest,source,exp_result, exp_conflicts",
    [
        pytest.param(
            {"d1": {"d2": 3}},
            {"d3": {"d2": 3}},
            {"d1": {"d2": 3}, "d3": {"d2": 3}},
            (),
            id="no_conflict",
        ),
        pytest.param(
            {"d1": {"d2": 3}},
            {"d1": {"d3": 3}},
            {"d1": {"d2": 3, "d3": 3}},
            (),
            id="no_conflict2",
        ),
        pytest.param(
            {
                "a": {"aa": {"aaa": True, "aab": True}, "ab": {"abb": True}},
                "b": {
                    "ba": {"bab": {"baba": True}},
                    "bb": {
                        "bba": {"bbab": {"bbaba": True}},
                        "bbb": {"bbba": {"bbbaa": True}},
                    },
                },
            },
            {
                "a": {"ab": {"aba": False}},
                "b": {
                    "ba": {"baa": {"baaa": False}},
                    "bb": {
                        "bba": {"bbaa": {"bbaaa": False}},
                        "bbb": {"bbbb": {"bbbba": False}},
                    },
                },
            },
            {
                "a": {
                    "aa": {"aaa": True, "aab": True},
                    "ab": {"aba": False, "abb": True},
                },
                "b": {
                    "ba": {"baa": {"baaa": False}, "bab": {"baba": True}},
                    "bb": {
                        "bba": {"bbaa": {"bbaaa": False}, "bbab": {"bbaba": True}},
                        "bbb": {"bbba": {"bbbaa": True}, "bbbb": {"bbbba": False}},
                    },
                },
            },
            (),
            id="no_conflict_complex",
        ),
        pytest.param(
            {"d1": 1},
            {"d1": 2},
            {"d1": 2},  # source value takes precedence
            ("d1",),
            id="conflict_root",
        ),
        pytest.param(
            {"d1": 1},
            {"d1": {"d2": 1}},
            {"d1": {"d2": 1}},
            ("d1",),
            id="conflict_root2",
        ),
        pytest.param(
            {"d1": {"d2": 3, "d3": 12}},
            {"d1": {"d3": 7}},
            {"d1": {"d2": 3, "d3": 7}},
            ("d1.d3",),
            id="conflict_nested1",
        ),
        pytest.param(
            {"d1": {"d2": {"d3": 12, "d4": 5}}},
            {"d1": {"d2": {"d3": 5, "d4": 7}}},
            {"d1": {"d2": {"d3": 5, "d4": 7}}},
            ("d1.d2.d3", "d1.d2.d4"),
            id="conflict_nested_multiple",
        ),
        pytest.param(
            {
                "a": {"aa": {"aaa": True, "aab": True}, "ab": {"abb": True}},
                "b": {
                    "ba": {"bab": {"baba": True}},
                    "bb": {
                        "bba": {"bbab": {"bbaba": True}},
                        "bbb": {"bbba": {"bbbaa": True}},
                    },
                },
            },
            {
                "a": {"ab": {"aba": False}},
                "b": {
                    "ba": {"baa": {"baaa": False}},
                    "bb": {
                        "bba": {"bbaa": {"bbaaa": False}},
                        "bbb": {"bbba": {"bbbaa": False}, "bbbb": {"bbbba": False}},
                    },
                },
            },
            {
                "a": {
                    "aa": {"aaa": True, "aab": True},
                    "ab": {"aba": False, "abb": True},
                },
                "b": {
                    "ba": {"baa": {"baaa": False}, "bab": {"baba": True}},
                    "bb": {
                        "bba": {"bbaa": {"bbaaa": False}, "bbab": {"bbaba": True}},
                        "bbb": {"bbba": {"bbbaa": False}, "bbbb": {"bbbba": False}},
                    },
                },
            },
            ("b.bb.bbb.bbba.bbbaa",),
            id="conflict_complex",
        ),
    ],
)
def test_config_merge(dest, source, exp_result, exp_conflicts):
    """Checks configuration merge and validation function."""
    from virtual_rainforest.core.config import config_merge

    result, conflicts = config_merge(dest, source)

    assert result == exp_result
    assert conflicts == exp_conflicts


@pytest.mark.parametrize(
    "cfg_paths, expected_cfg_paths",
    [
        ("string1", [Path("string1")]),
        (Path("string1"), [Path("string1")]),
        (["string1", "string2"], [Path("string1"), Path("string2")]),
        (["string1", Path("string2")], [Path("string1"), Path("string2")]),
        ([Path("string1"), Path("string2")], [Path("string1"), Path("string2")]),
    ],
)
def test_Config_init(cfg_paths, expected_cfg_paths):
    """Tests the normalisation of Config instance init."""
    from virtual_rainforest.core.config import Config

    # Just check normalisation, no processing
    cfg = Config(cfg_paths, auto=False)

    assert cfg.cfg_paths == expected_cfg_paths


@pytest.mark.parametrize(
    "cfg_paths,expected_exception,expected_log_entries",
    [
        pytest.param(
            ["file_does_not_exist"],
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Config file path does not exist"),
                (CRITICAL, "Config paths not all valid: check log."),
            ),
            id="bad_path",
        ),
        pytest.param(
            ["cfg_no_toml"],
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Config directory path contains no TOML files"),
                (CRITICAL, "Config paths not all valid: check log."),
            ),
            id="no_toml_dir",
        ),
        pytest.param(
            ["bad_json_in_schema.json"],
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Config file path with non-TOML suffix"),
                (CRITICAL, "Config paths not all valid: check log."),
            ),
            id="not_toml",
        ),
        pytest.param(
            [".", "all_config.toml"],
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Repeated files in config paths:"),
                (CRITICAL, "Config paths not all valid: check log."),
            ),
            id="dupes",
        ),
        pytest.param(
            ["all_config.toml"],
            does_not_raise(),
            ((INFO, "Config paths resolve to 1 files"),),
            id="valid",
        ),
    ],
)
def test_Config_resolve_config_paths(
    caplog,
    shared_datadir,
    cfg_paths,
    expected_exception,
    expected_log_entries,
):
    """Checks errors for missing config files."""
    from virtual_rainforest.core.config import Config

    # Init the class
    cfg = Config([shared_datadir / p for p in cfg_paths], auto=False)

    # Check that file resolution runs as expected
    with expected_exception:
        cfg.resolve_config_paths()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_paths,expected_exception,expected_log_entries",
    [
        pytest.param(
            ["all_config_bad.toml"],
            pytest.raises(ConfigurationError),
            (
                (ERROR, "Config TOML parsing error in"),
                (CRITICAL, "Errors parsing config files:"),
            ),
            id="toml_errors",
        ),
        pytest.param(
            ["all_config.toml"],
            does_not_raise(),
            ((INFO, "Config TOML loaded from "),),
            id="toml_valid",
        ),
        # (
        #     [Path("fake_file1.toml"), Path("fake_file2.toml")],
        #     [b"[core.grid]\nnx = 10", b"[core.grid]\nnx = 12"],
        #     ConfigurationError,
        #     (
        #         (
        #             CRITICAL,
        #             "The following tags are defined in multiple config files:\n"
        #            "core.grid.nx defined in both fake_file2.toml and fake_file1.toml",
        #         ),
        #     ),
        # ),
    ],
)
def test_Config_load_config_toml(
    caplog, shared_datadir, cfg_paths, expected_exception, expected_log_entries
):
    """Check errors for incorrectly formatted config files."""
    from virtual_rainforest.core.config import Config

    # Initialise the Config instance and manually resolve the config paths to toml files
    cfg = Config([shared_datadir / p for p in cfg_paths], auto=False)
    cfg.resolve_config_paths()
    caplog.clear()

    # Check that load_config_toml behaves as expected
    with expected_exception:
        cfg.load_config_toml()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "content,expected_exception,expected_dict,expected_log_entries",
    [
        pytest.param(
            {"filename1.toml": {"core": {"grid": {"nx": 10, "ny": 10}}}},
            does_not_raise(),
            {"core": {"grid": {"nx": 10, "ny": 10}}},
            ((INFO, "Config files merged"),),
            id="single_file_ok",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"nx": 10, "ny": 10}}},
                "filename2.toml": {"core": {"grid": {"nx": 10, "ny": 10}}},
            },
            pytest.raises(ConfigurationError),
            None,
            (
                (ERROR, "Duplicate configuration across files for core.grid.nx"),
                (ERROR, "Duplicate configuration across files for core.grid.ny"),
                (CRITICAL, "Config file contain duplicate definitions: check log"),
            ),
            id="two_files_duplication",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"nx": 10, "ny": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
            },
            does_not_raise(),
            {"core": {"grid": {"nx": 10, "ny": 10}, "modules": ["plants", "abiotic"]}},
            ((INFO, "Config files merged"),),
            id="two_files_valid",
        ),
    ],
)
def test_Config_build_config(
    caplog, content, expected_dict, expected_exception, expected_log_entries
):
    """Check building merged config from loaded content."""
    from virtual_rainforest.core.config import Config

    # Initialise the Config instance and manually populate the loaded TOML
    cfg = Config([], auto=False)
    cfg.toml_contents = content
    caplog.clear()

    # Check that build_config behaves as expected
    with expected_exception:
        cfg.build_config()

    log_check(caplog, expected_log_entries)

    # Assert that the config dictionary is as expected
    if expected_dict is not None:
        assert cfg == expected_dict


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
