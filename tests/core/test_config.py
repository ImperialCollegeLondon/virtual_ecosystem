"""Check that the configuration system is working as expected.

At the moment the tests are generally check that the correct critical errors are thrown
when configuration files or schema are missing or incorrectly formatted. There is also a
test that a complete configuration file passes the test, which will have to be kept up
to date.
"""

import sys
from contextlib import nullcontext as does_not_raise
from itertools import repeat
from logging import CRITICAL, ERROR, INFO, WARNING
from pathlib import Path
from unittest.mock import patch

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
            {"filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}}},
            does_not_raise(),
            {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
            ((INFO, "Config set from single file"),),
            id="single_file_ok",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
                "filename2.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
            },
            pytest.raises(ConfigurationError),
            None,
            (
                (
                    CRITICAL,
                    "Duplicated entries in config files: "
                    "core.grid.cell_nx, core.grid.cell_ny",
                ),
            ),
            id="two_files_conflict",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
            },
            does_not_raise(),
            {
                "core": {
                    "grid": {"cell_nx": 10, "cell_ny": 10},
                    "modules": ["plants", "abiotic"],
                }
            },
            ((INFO, "Config set from merged files"),),
            id="two_files_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
                "filename3.toml": {"core": {"grid": {"cell_ny": 10}}},
            },
            does_not_raise(),
            {
                "core": {
                    "grid": {"cell_nx": 10, "cell_ny": 10},
                    "modules": ["plants", "abiotic"],
                }
            },
            ((INFO, "Config set from merged files"),),
            id="three_files_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
                "filename2.toml": {"core": {"modules": ["plants", "abiotic"]}},
                "filename3.toml": {"core": {"grid": {"cell_ny": 10}}},
            },
            pytest.raises(ConfigurationError),
            None,
            ((CRITICAL, "Duplicated entries in config files: core.grid.cell_ny"),),
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
            {"core": {"modules": ["soil", "plants"]}},
            does_not_raise(),
            ((INFO, "Validation schema for configuration built."),),
            id="core_modules_all_known",
        ),
        pytest.param(
            {"core": {"modules": ["soil", "pants"]}},
            pytest.raises(ConfigurationError),
            ((ERROR, "Configuration contains module with no schema: pants"),),
            id="core_modules_include_unknown",
        ),
    ],
)
def test_Config_build_schema(
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
        cfg.build_schema()

    log_check(caplog, expected_log_entries)


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
            {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}, "modules": ["plants"]}},
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
            {"core": {"grid": {"cell_nx": 10, "cell_ny": -10}, "modules": []}},
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['core', 'grid', 'cell_ny']: "
                    "-10 is less than or equal to the minimum of 0",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="minimum_value_violation",
        ),
        pytest.param(
            {
                "core": {"grid": {"cell_nx": 10, "cell_ny": 10}, "modules": ["soil"]},
                "soil": {"no_layers": 123},
            },
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['soil']: Additional properties "
                    "are not allowed ('no_layers' was unexpected)",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="unexpected_property",
        ),
        pytest.param(
            {
                "core": {"modules": ["abiotic_simple"]},
            },
            does_not_raise(),
            ((INFO, "Configuration validated"),),
            id="no constants",
        ),
        pytest.param(
            {
                "core": {"modules": ["abiotic_simple"]},
                "abiotic_simple": {
                    "constants": {"AbioticSimpleConsts": {"constant1": 1.0}}
                },
            },
            does_not_raise(),
            ((INFO, "Configuration validated"),),
            id="correct constant",
        ),
        pytest.param(
            {
                "core": {"modules": ["abiotic_simple"]},
                "abiotic_simple": {"constants": {"constant1": 1.0}},
            },
            pytest.raises(ConfigurationError),
            (
                (
                    ERROR,
                    "Configuration error in ['abiotic_simple', 'constants']: "
                    "'AbioticSimpleConsts' is a required property",
                ),
                (
                    ERROR,
                    "Configuration error in ['abiotic_simple', 'constants']: Additional"
                    " properties are not allowed ('constant1' was unexpected)",
                ),
                (CRITICAL, "Configuration contains schema violations: check log"),
            ),
            id="missing AbioticSimpleConsts",
        ),
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
    cfg.build_schema()
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
                (INFO, "Validation schema for configuration built."),
                (INFO, "Configuration validated"),
            ),
        ),
        (
            "all_config.toml",  # File with no defaults
            (
                (INFO, "Config paths resolve to 1 files"),
                (INFO, "Config TOML loaded from"),
                (INFO, "Config set from single file"),
                (INFO, "Validation schema for configuration built."),
                (INFO, "Configuration validated"),
            ),
        ),
    ],
)
def test_Config_init_auto(caplog, shared_datadir, file_path, expected_log_entries):
    """Checks that auto validation passes as expected."""
    from virtual_rainforest.core.config import Config

    with patch.object(Config, "export_config") as export_mock:
        Config(shared_datadir / file_path, auto=True)
        log_check(caplog, expected_log_entries)
        export_mock.assert_called_once()


@pytest.mark.parametrize(
    "auto,expected_log_entries",
    [
        pytest.param(
            True,
            ((INFO, "Saving config to: "),),
            id="can_export",
        ),
        pytest.param(
            False,
            ((ERROR, "Cannot export unvalidated or invalid configuration"),),
            id="cannot_export",
        ),
    ],
)
def test_Config_export_config(caplog, shared_datadir, auto, expected_log_entries):
    """Checks that auto validation passes as expected."""
    from virtual_rainforest.core.config import Config

    cfg = Config(shared_datadir / "all_config.toml", auto=auto)
    caplog.clear()

    outpath = shared_datadir / "test_output.toml"
    cfg.export_config(outfile=outpath)

    log_check(caplog, expected_log_entries)

    # Check file is created - maybe add a file hash check?
    if auto:
        assert outpath.exists()
        assert outpath.is_file()


_NEW_VAR_ENTRY_PATH = Path("new/path")
_ABS_PATH = Path("C:" if sys.platform == "win32" else "/root")


@pytest.mark.parametrize(
    "params,expected",
    (
        pytest.param(
            # params
            {
                "core": {
                    "data": {
                        "variable": [
                            {"file": "file.txt", "var_name": "my_path"},
                            {"file": "file2.txt", "var_name": "my_other_path"},
                        ]
                    }
                },
                "some": {"other": {"value": 5}},
            },
            # expected
            {
                "core": {
                    "data": {
                        "variable": [
                            {
                                "file": str(_NEW_VAR_ENTRY_PATH / "file.txt"),
                                "var_name": "my_path",
                            },
                            {
                                "file": str(_NEW_VAR_ENTRY_PATH / "file2.txt"),
                                "var_name": "my_other_path",
                            },
                        ]
                    }
                },
                "some": {"other": {"value": 5}},
            },
            id="normal",
        ),
        pytest.param(
            *repeat(
                {
                    "core": {
                        "data": {
                            "variable": [
                                {
                                    "file": str(_ABS_PATH / "file.txt"),
                                    "var_name": "my_path",
                                },
                            ]
                        }
                    },
                },
                times=2,
            ),
            id="leave_abs_paths_unchanged",
        ),
        pytest.param(
            *repeat(
                {
                    "core": {
                        "data": {
                            # NB: Missing "file" key
                            "variable": [
                                {
                                    "var_name": "my_path",
                                },
                            ]
                        }
                    },
                },
                times=2,
            ),
            id="ignore_missing_file_key",
        ),
        pytest.param(
            *repeat(
                {
                    "core": {
                        "data": {
                            # NB: Not a list, as it should be
                            "variable": {
                                "file": "file.txt",
                                "var_name": "my_path",
                            },
                        }
                    },
                },
                times=2,
            ),
            id="variable_not_list",
        ),
    ),
)
def test_fix_up_variable_entry_paths(params, expected):
    """Test the _fix_up_variable_entry_paths() function."""
    from virtual_rainforest.core.config import _fix_up_variable_entry_paths

    _fix_up_variable_entry_paths(Path(_NEW_VAR_ENTRY_PATH), params)
    assert params == expected
