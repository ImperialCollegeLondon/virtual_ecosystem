"""Check the configuration schema loading and validation routines."""

import json
from contextlib import nullcontext as does_not_raise
from logging import CRITICAL, ERROR

import jsonschema
import pytest
from jsonschema.exceptions import SchemaError

from tests.conftest import log_check


@pytest.mark.parametrize(
    "module_name, schema_file_path, expected_exception, expected_log_entries",
    [
        pytest.param(
            "failure_1",
            "missing_file.json",
            pytest.raises(FileNotFoundError),
            [(ERROR, "Schema file not found")],
            id="missing_schema_file",
        ),
        pytest.param(
            "failure_2",
            "bad_json_in_schema.json",
            pytest.raises(json.JSONDecodeError),
            [(ERROR, "JSON error in schema file")],
            id="bad_json_in_schema_file",
        ),
        pytest.param(
            "failure_3",
            "bad_schema_in_schema.json",
            pytest.raises(SchemaError),
            [(ERROR, "Module schema invalid in")],
            id="bad_schema_in_schema_file",
        ),
        pytest.param(
            "failure_4",
            "no_properties_in_schema.json",
            pytest.raises(ValueError),
            [(ERROR, "Missing key in module schema failure_4: 'failure_4'")],
            id="no_properties_in_schema_file",
        ),
        pytest.param(
            "failure_5",
            "no_required_in_schema.json",
            pytest.raises(ValueError),
            [(ERROR, "Missing key in module schema failure_5: 'required'")],
            id="no_required_in_schema_file",
        ),
        pytest.param(
            "test_module",
            "valid_schema.json",
            does_not_raise(),
            [],
            id="success",
        ),
    ],
)
def test_load_schema(
    shared_datadir,
    caplog,
    module_name,
    schema_file_path,
    expected_exception,
    expected_log_entries,
):
    """Tests schema loading and validation."""
    from virtual_rainforest.core.config import load_schema

    caplog.clear()

    with expected_exception:
        sfp = shared_datadir / schema_file_path
        _ = load_schema(module_name=module_name, schema_file_path=sfp)

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


def test_merge_schemas():
    """Test that module schemas are properly merged."""
    from virtual_rainforest.core.config import SCHEMA_REGISTRY, merge_schemas

    merged_schemas = merge_schemas(
        {
            "core": SCHEMA_REGISTRY["core"],
            "abiotic": SCHEMA_REGISTRY["abiotic"],
            "animals": SCHEMA_REGISTRY["animals"],
            "plants": SCHEMA_REGISTRY["plants"],
            "soil": SCHEMA_REGISTRY["soil"],
        }
    )

    assert set(merged_schemas["required"]) == set(
        ["abiotic", "animals", "plants", "soil", "core"]
    )


def test_extend_with_default():
    """Test that validator has been properly extended to allow addition of defaults."""
    from virtual_rainforest.core.config import ValidatorWithDefaults

    # Check that function adds a function with the right name in the right location
    TestValidator = ValidatorWithDefaults({"str": {}})
    assert TestValidator.VALIDATORS["properties"].__name__ == "set_defaults"
