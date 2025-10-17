"""Testing the config_builder module."""

from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR, INFO
from operator import attrgetter
from pathlib import Path

import pytest
import tomli_w
from pydantic import BaseModel

from tests.conftest import log_check, record_found_in_log
from virtual_ecosystem.core.exceptions import ConfigurationError

# ------------------------------------------------
# Testing configuration dictionary compilation and merging
# ------------------------------------------------


@pytest.mark.parametrize(
    "dest,source,exp_result, exp_conflicts",
    [
        pytest.param(
            {"d1": {"d2": 3}},
            {"d3": {"d2": 3}},
            {"d1": {"d2": 3}, "d3": {"d2": 3}},
            set(),
            id="no_conflict",
        ),
        pytest.param(
            {"d1": {"d2": 3}},
            {"d1": {"d3": 3}},
            {"d1": {"d2": 3, "d3": 3}},
            set(),
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
            set(),
            id="no_conflict_complex",
        ),
        pytest.param(
            {"d1": 1},
            {"d1": 2},
            {"d1": 2},  # source value takes precedence
            set(["d1"]),
            id="conflict_root",
        ),
        pytest.param(
            {"d1": 1},
            {"d1": {"d2": 1}},
            {"d1": {"d2": 1}},
            set(["d1"]),
            id="conflict_root2",
        ),
        pytest.param(
            {"d1": {"d2": 3, "d3": 12}},
            {"d1": {"d3": 7}},
            {"d1": {"d2": 3, "d3": 7}},
            set(["d1.d3"]),
            id="conflict_nested1",
        ),
        pytest.param(
            {"d1": {"d2": {"d3": 12, "d4": 5}}},
            {"d1": {"d2": {"d3": 5, "d4": 7}}},
            {"d1": {"d2": {"d3": 5, "d4": 7}}},
            set(["d1.d2.d3", "d1.d2.d4"]),
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
            set(["b.bb.bbb.bbba.bbbaa"]),
            id="conflict_complex",
        ),
        pytest.param(
            {"d1": {"d2": [1, 2, 3]}},
            {"d1": {"d2": [4, 5]}},
            {"d1": {"d2": [1, 2, 3, 4, 5]}},
            set(),
            id="no_conflict_list_merge",
        ),
        # The next example passes just fine, which is intentional, but the test is here
        # to highlight the behaviour
        pytest.param(
            {"d1": {"d2": [1, 2, 3]}},
            {"d1": {"d2": [{"file": "a_path"}]}},
            {"d1": {"d2": [1, 2, 3, {"file": "a_path"}]}},
            set(),
            id="no_conflict_list_merge_dubious_content",
        ),
        pytest.param(
            {"d1": {"d2": [1, 2, 3]}},
            {"d1": {"d2": "a"}},
            {"d1": {"d2": "a"}},
            set(["d1.d2"]),
            id="conflict_list_and_not_list",
        ),
    ],
)
def test_config_merge(dest, source, exp_result, exp_conflicts):
    """Checks configuration merge and validation function."""
    from virtual_ecosystem.core.config_builder import merge_configuration_dicts

    result, conflicts = merge_configuration_dicts(dest, source)

    assert result == exp_result
    assert conflicts == exp_conflicts


@pytest.mark.parametrize(
    argnames="data, expected_data, expected_conflicts",
    argvalues=(
        pytest.param(
            [{"a": 1}, {"b": 2}, {"c": 3}],
            {"a": 1, "b": 2, "c": 3},
            set(),
            id="simple",
        ),
        pytest.param(
            [{"a": 1, "d": {"e": 4}}, {"b": 2}, {"c": 3, "f": {"g": 4}}],
            {"a": 1, "b": 2, "c": 3, "d": {"e": 4}, "f": {"g": 4}},
            set(),
            id="nested",
        ),
        pytest.param(
            [{"a": 1, "d": {"e": 4}}, {"b": 2}, {"c": 3, "d": {"e": 5}}],
            {"a": 1, "b": 2, "c": 3, "d": {"e": 5}},
            set(["d.e"]),
            id="conflicts",
        ),
    ),
)
def test_compile_configuration_data(data, expected_data, expected_conflicts):
    """Tests compile_configuration_data."""

    from virtual_ecosystem.core.config_builder import compile_configuration_data

    result, conflicts = compile_configuration_data(data)

    assert result == expected_data
    assert conflicts == expected_conflicts


# ------------------------------------------------
# Testing ConfigurationLoader methods
# ------------------------------------------------


@pytest.mark.parametrize(
    "cfg_paths, cfg_strings, expected_cfg_paths, raises, err_msg",
    [
        pytest.param(
            "string1",
            None,
            [Path("string1")],
            does_not_raise(),
            None,
            id="paths_as_str",
        ),
        pytest.param(
            Path("string1"),
            None,
            [Path("string1")],
            does_not_raise(),
            None,
            id="paths_as_path",
        ),
        pytest.param(
            ["string1", "string2"],
            None,
            [Path("string1"), Path("string2")],
            does_not_raise(),
            None,
            id="paths_as_str_list",
        ),
        pytest.param(
            ["string1", Path("string2")],
            None,
            [Path("string1"), Path("string2")],
            does_not_raise(),
            None,
            id="paths_as_mixed_list",
        ),
        pytest.param(
            [Path("string1"), Path("string2")],
            None,
            [Path("string1"), Path("string2")],
            does_not_raise(),
            None,
            id="paths_as_path_list",
        ),
        pytest.param(
            None,
            """[[core.data.variable]]
            file_path = "cellid_coords.nc
            var_name = "temp"
            """,
            [],
            does_not_raise(),
            None,
            id="cfg_strings_as_str",
        ),
        pytest.param(
            None,
            [
                """[[core.data.variable]]
                file_path = "cellid_coords.nc
                var_name = "temp"
                """,
                """[[core.data.variable]]
                file_path = "cellid_coords.nc
                var_name = "patm"
                """,
            ],
            [],
            does_not_raise(),
            None,
            id="cfg_strings_as_list",
        ),
        pytest.param(
            None,
            None,
            [],
            pytest.raises(ValueError),
            "Provide cfg_paths or cfg_strings.",
            id="neither",
        ),
        pytest.param(
            "string1",
            """[[core.data.variable]]
            file_path = "cellid_coords.nc
            var_name = "temp"
            """,
            [],
            pytest.raises(ValueError),
            "Do not use both cfg_paths and cfg_strings.",
            id="both",
        ),
    ],
)
def test_ConfigurationLoader_init(
    cfg_paths, cfg_strings, expected_cfg_paths, raises, err_msg
):
    """Tests the normalisation and startup of ConfigurationLoader instance init."""
    from virtual_ecosystem.core.config_builder import ConfigurationLoader

    # Just check normalisation and error conditions, no processing
    with raises as err:
        cfg = ConfigurationLoader(cfg_paths=cfg_paths, cfg_strings=cfg_strings)

        if not isinstance(raises, does_not_raise):
            assert str(err) == err_msg

        assert cfg.cfg_paths == expected_cfg_paths
        if cfg_strings is not None:
            assert cfg.from_cfg_strings is True


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
def test_ConfigurationLoader_collect_config_paths(
    caplog,
    shared_datadir,
    cfg_paths,
    expected_exception,
    expected_log_entries,
):
    """Checks errors for missing config files."""
    from virtual_ecosystem.core.config_builder import ConfigurationLoader

    caplog.clear()

    # Init the class
    cfg = ConfigurationLoader([shared_datadir / p for p in cfg_paths])

    # Check that file resolution runs as expected
    with expected_exception:
        cfg.collect_config_paths()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_paths,expected_exception,expected_log_entries",
    [
        pytest.param(
            ["toml_errors.toml"],
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
def test_ConfigurationLoader_load_config_toml(
    caplog, shared_datadir, cfg_paths, expected_exception, expected_log_entries
):
    """Check errors for incorrectly formatted config files."""
    from virtual_ecosystem.core.config_builder import ConfigurationLoader

    # Initialise the ConfigurationLoader instance and manually resolve the config paths
    # to toml files
    cfg = ConfigurationLoader([shared_datadir / p for p in cfg_paths])
    cfg.collect_config_paths()
    caplog.clear()

    # Check that load_config_toml behaves as expected
    with expected_exception:
        cfg.load_config_toml()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "cfg_paths,expected_exception,expected_log_entries",
    [
        pytest.param(
            "toml_errors.toml",
            pytest.raises(ConfigurationError),
            ((CRITICAL, "TOML parsing error in cfg_strings:"),),
            id="toml_errors",
        ),
        pytest.param(
            "all_config.toml",
            does_not_raise(),
            ((INFO, "Config TOML loaded from config strings"),),
            id="toml_valid",
        ),
    ],
)
def test_ConfigurationLoader_load_config_toml_string(
    caplog, shared_datadir, cfg_paths, expected_exception, expected_log_entries
):
    """Check errors for incorrectly formatted cfg_strings."""
    from virtual_ecosystem.core.config_builder import ConfigurationLoader

    # Initialise the Config instance and manually run the load process
    with open(Path(shared_datadir) / cfg_paths) as cfg_file:
        cfg_strings = cfg_file.read()

    cfg = ConfigurationLoader(cfg_strings=cfg_strings)
    caplog.clear()

    # Check that load_config_toml behaves as expected
    with expected_exception:
        cfg.load_config_toml_string()

    log_check(caplog, expected_log_entries)


@pytest.mark.parametrize(
    "content,expected_exception,expected_path_log,expected_string_log",
    [
        pytest.param(
            {"filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}}},
            does_not_raise(),
            (
                (INFO, "Config paths resolve to 1 files"),
                (INFO, "Config TOML loaded from "),
                (INFO, "Configuration data compiled."),
            ),
            (
                (INFO, "Config TOML loaded from config strings"),
                (INFO, "Configuration data compiled."),
            ),
            id="single_file_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
                "filename2.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
            },
            pytest.raises(ConfigurationError),
            (
                (INFO, "Config paths resolve to 2 files"),
                (INFO, "Config TOML loaded from "),
                (INFO, "Config TOML loaded from "),
                (
                    CRITICAL,
                    "Duplicated entries in config files: "
                    "core.grid.cell_nx, core.grid.cell_ny",
                ),
            ),
            (
                (INFO, "Config TOML loaded from config strings"),
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
                "filename1.toml": {"core": {"grid": {"cell_nx": 10}}},
                "filename2.toml": {"core": {"grid": {"cell_ny": 10}}},
            },
            does_not_raise(),
            (
                (INFO, "Config paths resolve to 2 files"),
                (INFO, "Config TOML loaded from "),
                (INFO, "Config TOML loaded from "),
                (INFO, "Configuration data compiled."),
            ),
            (
                (INFO, "Config TOML loaded from config strings"),
                (INFO, "Configuration data compiled."),
            ),
            id="two_files_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10}}},
                "filename2.toml": {"core": {}},
                "filename3.toml": {"core": {"grid": {"cell_ny": 10}}},
            },
            does_not_raise(),
            (
                (INFO, "Config paths resolve to 3 files"),
                (INFO, "Config TOML loaded from "),
                (INFO, "Config TOML loaded from "),
                (INFO, "Config TOML loaded from "),
                (INFO, "Configuration data compiled."),
            ),
            (
                (INFO, "Config TOML loaded from config strings"),
                (INFO, "Configuration data compiled."),
            ),
            id="three_files_valid",
        ),
        pytest.param(
            {
                "filename1.toml": {"core": {"grid": {"cell_nx": 10, "cell_ny": 10}}},
                "filename2.toml": {"core": {}},
                "filename3.toml": {"core": {"grid": {"cell_ny": 10}}},
            },
            pytest.raises(ConfigurationError),
            (
                (INFO, "Config paths resolve to 3 files"),
                (INFO, "Config TOML loaded from "),
                (INFO, "Config TOML loaded from "),
                (INFO, "Config TOML loaded from "),
                (
                    CRITICAL,
                    "Duplicated entries in config files: core.grid.cell_ny",
                ),
            ),
            (
                (INFO, "Config TOML loaded from config strings"),
                (
                    CRITICAL,
                    "Duplicated entries in config files: core.grid.cell_ny",
                ),
            ),
            id="three_files_conflict",
        ),
    ],
)
@pytest.mark.parametrize("override", [True, False])
def test_ConfigurationLoader_load_configuration_data(
    tmpdir,
    caplog,
    content,
    expected_exception,
    expected_path_log,
    expected_string_log,
    override,
):
    """This test checks the load_configuration_data method.

    This method wraps up the stages of collating the configuration files, loading their
    data and resolving relative paths and the final compilation of the resulting data
    into a single configuration data dictionary. It also checks that override_params is
    handled correctly.
    """
    from virtual_ecosystem.core.config_builder import ConfigurationLoader

    # Set an override value or leave empty
    if override:
        override_params = {"core": {"grid": {"cell_ny": 20}}}
    else:
        override_params = None

    # ----------------------------
    # Test the cfg_paths option
    # ----------------------------

    cfg_paths = []
    for filename, filedata in content.items():
        filepath = tmpdir / filename
        cfg_paths.append(filepath)
        with open(filepath, "wb") as outfile:
            tomli_w.dump(filedata, outfile)

    # Initialise the Config instance
    config_builder = ConfigurationLoader(
        cfg_paths=cfg_paths, override_params=override_params
    )
    caplog.clear()

    # Check that load_configuration_data behaves as expected
    with expected_exception:
        config_builder.load_configuration_data()

        # Test the values that were passed into valid configs.

        assert config_builder.data["core"]["grid"]["cell_nx"] == 10
        if override:
            assert config_builder.data["core"]["grid"]["cell_ny"] == 20
        else:
            assert config_builder.data["core"]["grid"]["cell_ny"] == 10

    log_check(caplog, expected_path_log)

    # Tidy up
    [Path(p).unlink() for p in cfg_paths]

    # ----------------------------
    # Test the cfg_strings option
    # ----------------------------

    cfg_strings = [tomli_w.dumps(v) for k, v in content.items()]

    # Initialise the Config instance
    config_builder = ConfigurationLoader(
        cfg_strings=cfg_strings, override_params=override_params
    )
    caplog.clear()

    # Check that load_configuration_data behaves as expected
    with expected_exception:
        config_builder.load_configuration_data()

        # Test the values that were passed into valid configs.

        assert config_builder.data["core"]["grid"]["cell_nx"] == 10
        if override:
            assert config_builder.data["core"]["grid"]["cell_ny"] == 20
        else:
            assert config_builder.data["core"]["grid"]["cell_ny"] == 10

    log_check(caplog, expected_string_log)


# ---------------------------------------------------------------
# Testing functions to create and validate configuration models
# ---------------------------------------------------------------


@pytest.mark.parametrize(
    argnames="requested, outcome, expected",
    argvalues=(
        pytest.param(
            ["core", "plants"],
            does_not_raise(),
            ["core", "plants"],
            id="core present",
        ),
        pytest.param(
            ["plants"],
            does_not_raise(),
            ["core", "plants"],
            id="core added",
        ),
        pytest.param(
            ["planets"],
            pytest.raises(ModuleNotFoundError),
            None,
            id="unknown model",
        ),
    ),
)
def test_build_configuration_model(requested, outcome, expected):
    """Tests build_configuration_model."""
    from virtual_ecosystem.core.config_builder import build_configuration_model

    with outcome:
        model = build_configuration_model(requested)

        assert issubclass(model, BaseModel)
        assert set(expected) == set(model.model_fields.keys())


@pytest.mark.parametrize(
    argnames="data, outcome, expected_attr_values, expected_log",
    argvalues=(
        pytest.param(
            {"core": {"grid": {"cell_nx": 10}}},
            does_not_raise(),
            (("core.grid.cell_nx", 10),),
            ((INFO, "Configuration validated."),),
            id="core_only",
        ),
        pytest.param(
            {
                "core": {"grid": {"cell_nx": 10}},
                "plants": {"constants": {"dsr_to_ppfd": 0.2}},
            },
            does_not_raise(),
            (("core.grid.cell_nx", 10), ("plants.constants.dsr_to_ppfd", 0.2)),
            ((INFO, "Configuration validated."),),
            id="core_plants",
        ),
        pytest.param(
            {
                "core": {"grid": {"cell_nx": 10}},
                "plants": {"constants": {"dsr_to_ppfd": "a"}},
            },
            pytest.raises(ConfigurationError),
            None,
            (
                (ERROR, "plants.constants.dsr_to_ppfd = a"),
                (CRITICAL, "Configuration validation failed. See errors above."),
            ),
            id="core_plants_bad_type",
        ),
    ),
)
def test_get_configuration(caplog, data, outcome, expected_attr_values, expected_log):
    """Tests the get_configuration function."""
    from virtual_ecosystem.core.config_builder import get_configuration

    with outcome:
        # Run the function
        config = get_configuration(data=data)

        # Do we get a model
        assert isinstance(config, BaseModel)

        # Are the attributes as expected
        for attr_path, expected_value in expected_attr_values:
            assert expected_value == attrgetter(attr_path)(config)

        # Does the log contain the expected outputs
        for message in expected_log:
            assert record_found_in_log(caplog=caplog, find=message)
