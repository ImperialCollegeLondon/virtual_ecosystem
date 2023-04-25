"""Check that the configuration system is working as expected.

At the moment the tests are generally check that the correct critical errors are thrown
when configuration files or schema are missing or incorrectly formatted. There is also a
test that a complete configuration file passes the test, which will have to be kept up
to date.
"""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO, WARNING
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
            {},
            does_not_raise(),
            {},
            ((WARNING, "No config files set"),),
            id="no_file_warns",
        ),
        pytest.param(
            {"filename1.toml": {"core": {"grid": {"nx": 10, "ny": 10}}}},
            does_not_raise(),
            {"core": {"grid": {"nx": 10, "ny": 10}}},
            ((INFO, "Config set from single file"),),
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
                (
                    CRITICAL,
                    "Duplicated entries in config files: core.grid.nx, core.grid.ny",
                ),
            ),
            id="two_files_conflict",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"nx": 10, "ny": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
            },
            does_not_raise(),
            {"core": {"grid": {"nx": 10, "ny": 10}, "modules": ["plants", "abiotic"]}},
            ((INFO, "Config set from merged files"),),
            id="two_files_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"nx": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
                "filename3.toml": {"core": {"grid": {"ny": 10}}},
            },
            does_not_raise(),
            {"core": {"grid": {"nx": 10, "ny": 10}, "modules": ["plants", "abiotic"]}},
            ((INFO, "Config set from merged files"),),
            id="three_files_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"nx": 10, "ny": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
                "filename3.toml": {"core": {"grid": {"ny": 10}}},
            },
            pytest.raises(ConfigurationError),
            None,
            ((CRITICAL, "Duplicated entries in config files: core.grid.ny"),),
            id="three_files_conflict",
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
    "config_content,expected_exception,expected_log_entries",
    [
        pytest.param(
            {"core": {"modules": ["soil", "soil"]}},
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['core', 'modules']: "
                    "['soil', 'soil'] has non-unique elements",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="core_unique_module_violation",
        ),
        pytest.param(
            {"core": {"modules": ["soil", "pants"]}},
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['core', 'modules']: "
                    "Unknown model schema: pants",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="core_unknown_module",
        ),
        pytest.param(
            {"core": {"grid": {"nx": 10, "ny": 10}, "modules": ["plants"]}},
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['plants']: "
                    "'ftypes' is a required property",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="missing_required_property",
        ),
        pytest.param(
            {"core": {"grid": {"nx": 10, "ny": -10}, "modules": []}},
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['core', 'grid', 'ny']: "
                    "-10 is less than or equal to the minimum of 0",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="minimum_value_violation",
        ),
        # pytest.param(
        #     {
        #         "core": {"grid": {"nx": 10, "ny": 10}, "modules": ["soil"]},
        #         "soil": {"no_layers": 123},
        #     },
        #     pytest.raises(ConfigurationError),
        #     (
        #         (
        #             ERROR,
        #             "Configuration error in ['soil']: Additional properties "
        #             "are not allowed ('no_layers' was unexpected)",
        #         ),
        #         (CRITICAL, "Configuration contains schema violations: check log"),
        #     ),
        #     id="unexpected_property",
        # ),
    ],
)
def test_Config_validate_config(
    caplog, config_content, expected_exception, expected_log_entries
):
    """Test the validate_config method of Config."""
    from virtual_rainforest.core.config import Config

    # create an empty config and directly set the merged configuration values
    cfg = Config([], auto=False)
    cfg.update(config_content)
    caplog.clear()

    # Run the validation
    with expected_exception:
        cfg.validate_config()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "file_path,expected_log_entries",
    [
        (
            "default_config.toml",  # File entirely of defaults
            (
                (INFO, "Config paths resolve to 1 files"),
                (INFO, "Config TOML loaded from"),
                (INFO, "Config set from single file"),
                (INFO, "Configuration validated"),
            ),
        ),
        (
            "all_config.toml",  # File with no defaults
            (
                (INFO, "Config paths resolve to 1 files"),
                (INFO, "Config TOML loaded from"),
                (INFO, "Config set from single file"),
                (INFO, "Configuration validated"),
            ),
        ),
    ],
)
def test_Config_init_auto(caplog, shared_datadir, file_path, expected_log_entries):
    """Checks that auto validation passes as expected."""
    from virtual_rainforest.core.config import Config

    Config(shared_datadir / file_path, auto=True)
    log_check(caplog, expected_log_entries)
