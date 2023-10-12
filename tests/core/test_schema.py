"""Check the configuration schema loading and validation routines."""

import json
from contextlib import nullcontext as does_not_raise
from logging import ERROR

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
    from virtual_rainforest.core.schema import load_schema

    caplog.clear()

    with expected_exception:
        sfp = shared_datadir / schema_file_path
        _ = load_schema(module_name=module_name, schema_file_path=sfp)

    log_check(caplog, expected_log_entries)


def test_merge_schemas():
    """Test that module schemas are properly merged."""

    from virtual_rainforest.core.registry import MODULE_REGISTRY, register_module
    from virtual_rainforest.core.schema import merge_schemas

    # Import the models to populate the registry
    register_module("virtual_rainforest.core")
    register_module("virtual_rainforest.models.abiotic_simple")
    register_module("virtual_rainforest.models.animals")
    register_module("virtual_rainforest.models.plants")
    register_module("virtual_rainforest.models.soil")

    merged_schemas = merge_schemas(
        {
            "core": MODULE_REGISTRY["core"].schema,
            "abiotic_simple": MODULE_REGISTRY["abiotic_simple"].schema,
            "animals": MODULE_REGISTRY["animals"].schema,
            "plants": MODULE_REGISTRY["plants"].schema,
            "soil": MODULE_REGISTRY["soil"].schema,
        }
    )

    assert set(merged_schemas["required"]) == set(
        ["abiotic_simple", "animals", "plants", "soil", "core"]
    )


def test_extend_with_default():
    """Test that validator has been properly extended to allow addition of defaults."""
    from virtual_rainforest.core.config import ValidatorWithDefaults

    # Check that function adds a function with the right name in the right location
    TestValidator = ValidatorWithDefaults({"str": {}})
    assert TestValidator.VALIDATORS["properties"].__name__ == "set_defaults"
