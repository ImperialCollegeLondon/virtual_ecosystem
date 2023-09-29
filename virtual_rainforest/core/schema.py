"""The :mod:`~virtual_rainforest.core.schema` module  provides the
:func:`~virtual_rainforest.core.schema.load_schema` and
:func:`~virtual_rainforest.core.schema.merge_schema` functions to build a single
JSONSchema configuration validator from individual module schames. The JSONSchema
validation is extended using the :func:`~virtual_rainforest.core.schema.set_defaults`
iterator to provide a  global JSONSchema validator instance that handles
the provision of default values within schema
(:data:`~virtual_rainforest.core.registry.ValidatorWithDefaults`).
"""  # noqa: D205, D415


import json
from pathlib import Path
from typing import Any, Iterator

import dpath.util  # type: ignore
from jsonschema import Draft202012Validator, exceptions, validators

from virtual_rainforest.core.logger import LOGGER


def set_defaults(
    validator: type[Draft202012Validator],
    properties: dict[str, Any],
    instance: dict[str, Any],
    schema: dict[str, Any],
) -> Iterator:
    """Generate an iterator to populate schema defaults.

    This function is used to extend the Draft202012Validator to include automatic
    insertion of default values from a schema where values are not specified. The
    function signature follows the required JSON schema pattern:

    https://python-jsonschema.readthedocs.io/en/latest/creating/

    Args:
        validator: a validator instance,
        properties: the value of the property being validated within the instance
        instance: the instance
        schema: the schema

    Returns:
        An iterator to be applied to JSON schema entries.
    """
    for property, subschema in properties.items():
        if "default" in subschema:
            instance.setdefault(property, subschema["default"])

    for error in Draft202012Validator.VALIDATORS["properties"](
        validator,
        properties,
        instance,
        schema,
    ):
        yield error


ValidatorWithDefaults: Draft202012Validator = validators.extend(
    Draft202012Validator, {"properties": set_defaults}
)
"""A JSONSchema validator that sets defaults where required."""


def load_schema(module_name: str, schema_file_path: Path) -> dict:
    """Function to load the JSON schema for a module.

    This function tries to load a JSON schema file and then - if the JSON loaded
    correctly - checks that the JSON provides a valid JSON Schema.

    Args:
        module_name: The name to register the schema under
        schema_file_path: The file path to the JSON Schema file

    Raises:
        FileNotFoundError: the schema path does not exist
        json.JSONDecodeError: the file at the schema path is not valid JSON
        jsonschema.SchemaError: the file contents are not valid JSON Schema
        ValueError: the JSON Schema is missing required keys
    """

    # Try and get the contents of the JSON schema file
    try:
        json_schema = json.load(open(schema_file_path))
    except FileNotFoundError:
        fnf_error = FileNotFoundError(f"Schema file not found {schema_file_path}.")
        LOGGER.error(fnf_error)
        raise fnf_error
    except json.JSONDecodeError as excep:
        LOGGER.error(f"JSON error in schema file {schema_file_path}")
        raise excep

    # Check that this is a valid schema - deliberately log a separate message and let
    # the schema traceback output rather than replacing it.
    try:
        ValidatorWithDefaults.check_schema(json_schema)
    except exceptions.SchemaError as excep:
        LOGGER.error(f"Module schema invalid in: {schema_file_path}")
        raise excep

    # Check that relevant keys are included - deliberately re-raising as ValueError here
    # as the KeyError has built in quoting and is expecting to provide simple missing
    # key messages.
    try:
        json_schema["properties"][module_name]
        json_schema["required"]
    except KeyError as excep:
        to_raise = ValueError(f"Missing key in module schema {module_name}: {excep}")
        LOGGER.error(to_raise)
        raise to_raise

    return json_schema


def merge_schemas(schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Merge the validation schemas for desired modules.

    The method merges a set of schemas for a set of desired modules into a single
    integrated schema that can then be used to validate a merged configuration for those
    modules.

    Args:
        schema: A dictionary of schemas keyed by module name

    Returns:
        An integrated schema combining the modules.
    """

    # Construct combined schema for all relevant modules
    comb_schema: dict = {"type": "object", "properties": {}, "required": []}

    # Loop over expected modules amd add them to the combined schema
    for this_module, this_schema in schemas.items():
        comb_schema["properties"][this_module] = this_schema["properties"][this_module]
        # Add module name to list of required modules
        comb_schema["required"].append(this_module)

    p_paths = []
    # Recursively search for all instances of properties in the schema
    for path, value in dpath.util.search(comb_schema, "**/properties", yielded=True):
        # Remove final properties instance from path so that additionalProperties ends
        # up in the right place
        p_paths.append("" if path == "properties" else path[:-11])

    # Set additional properties to false everywhere that properties are defined
    for path in p_paths:
        dpath.util.new(comb_schema, f"{path}/additionalProperties", False)

    return comb_schema
