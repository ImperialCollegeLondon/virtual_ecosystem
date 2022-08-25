"""The `core.config` module.

The `core.config` module is used to read in the various configuration files, validate
their contents, and then configure a ready to run instance of the virtual rainforest
model.
"""
# TODO - find config folder based on command line argument

import os
import sys

from jsonschema import validate

from virtual_rainforest.core.logger import LOGGER

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

config_schema = {
    "type": "object",
    "properties": {
        "config": {
            "type": "object",
            "properties": {
                "core": {
                    "description": "Configuration settings for the core module",
                    "type": "object",
                    "properties": {
                        "grid": {
                            "description": "Details of the grid to configure",
                            "type": "object",
                            "properties": {
                                "nx": {
                                    "description": "Number of grid cells in x "
                                    "direction",
                                    "type": "integer",
                                    "exclusiveMinimum": 0,
                                },
                                "ny": {
                                    "description": "Number of grid cells in y "
                                    "direction",
                                    "type": "integer",
                                    "exclusiveMinimum": 0,
                                },
                            },
                            "required": ["nx", "ny"],
                        },
                        "modules": {
                            "description": "List of modules to be configured",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["grid", "modules"],
                }
            },
            "required": ["core"],
        }
    },
    "required": ["config"],
}


def validate_config(filepath: str):
    """Validates the contents of user provided config files.

    TODO - Add more details here
    Args:
        filepath: Path to folder containing configuration files.
    """

    # Find and load all toml files supplied config directory
    for file in os.listdir(filepath):
        if file.endswith(".toml"):
            with open(os.path.join(filepath, file), "rb") as f:
                try:
                    toml_dict = tomllib.load(f)
                except tomllib.TOMLDecodeError as err:
                    LOGGER.critical(
                        f"Configuration file {file} is incorrectly formatted.\n"
                        f"Failed with the following message:\n{err}"
                    )
                    return None

    # TODO - Critical check if no toml files are found
    print(toml_dict)

    # Validate against the core schema
    validate(instance=toml_dict, schema=config_schema)
    # AT THE MOMENT THIS PASSES WITH EXTRA CATAGORIES

    # Merge them into a single object
    # 3 potential critical errors, duplicated tags, missing tags, failed validation
    # against schema
    # Output combined toml (or json?) file, maybe into the same folder
    # Return the config object as a final module output


validate_config("virtual_rainforest/core")
