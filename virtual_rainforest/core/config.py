"""The `core.config` module.

The `core.config` module is used to read in the various configuration files, validate
their contents, and then configure a ready to run instance of the virtual rainforest
model.
"""
# TODO - find config folder based on command line argument

import os
import sys

# from jsonschema import validate

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

config_schema = {
    "description": "Schema for configuration of the core module.",
    "type": "object",
    "properties": {
        "grid": {
            "description": "Details of the grid to configure",
            "type": "object",
            "properties": {
                "nx": {
                    "description": "Number of grid cells in x direction",
                    "type": "integer",
                    "exclusiveMinimum": 0,
                },
                "ny": {
                    "description": "Number of grid cells in y direction",
                    "type": "integer",
                    "exclusiveMinimum": 0,
                },
            },
        },
        "modules": {
            "description": "List of modules to be configured",
            "type": "array",
            "items": {"type": "string"},
        },
    },
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
                    # TODO - log this as a critical error
                    print(f"Configuration file {file} is incorrectly formatted.")
                    print(f"Failed with the following message: {err}")
                    return None

                print(toml_dict)

    # CHECK IF DICTIONARY IS EMPTY, IF SO THIS IS A NOTHING FOUND EXCEPTION

    # Read in collection of toml (or maybe also json files)
    # Merge them into a single object
    # 3 potential critical errors, duplicated tags, missing tags, failed validation
    # against schema
    # Output combined toml (or json?) file, maybe into the same folder
    # Return the config object as a final module output


validate_config("virtual_rainforest/core")
