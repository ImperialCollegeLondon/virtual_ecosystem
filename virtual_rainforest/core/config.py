"""The `core.config` module.

The `core.config` module is used to read in the various configuration files, validate
their contents, and then configure a ready to run instance of the virtual rainforest
model.
"""
# TODO - find config folder based on command line argument

import os
import sys

import dpath.util
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
                            "additionalProperties": False,
                        },
                        "modules": {
                            "description": "List of modules to be configured",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["grid", "modules"],
                    "additionalProperties": False,
                }
            },
            "required": ["core"],
            "additionalProperties": False,
        }
    },
    "required": ["config"],
    "additionalProperties": False,
}


def check_dict_leaves(d1: dict, d2: dict, conflicts: list = [], path: list = []):
    """Recursively checks if leaves are repeated between two nested dictionaries.

    Args:
        d1: First nested dictionary to compare
        d2: Second nested dictionary to compare
        path: List describing recursive path through the nested dictionary
        conflicts: List of variables that are defined in multiple places

    Returns:
        conflicts: List of variables that are defined in multiple places
    """

    for key in d2:
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                check_dict_leaves(d1[key], d2[key], conflicts, path + [str(key)])
            else:
                conflicts.append("%s" % ".".join(path + [str(key)]))

    return conflicts


def validate_config(filepath: str):
    """Validates the contents of user provided config files.

    TODO - Add more details here
    Args:
        filepath: Path to folder containing configuration files.
    """

    # Count number of toml files
    c = len([f for f in os.listdir(filepath) if f.endswith(".toml")])

    # Critical check if no toml files are found
    if c == 0:
        LOGGER.critical("No toml files found in the config folder provided!")
        return None

    # Preallocate container for file names and corresponding dictionaries
    file_data: list[tuple[str, dict]] = []
    conflicts = []

    # Find and load all toml files supplied config directory
    for file in os.listdir(filepath):
        if file.endswith(".toml"):
            with open(os.path.join(filepath, file), "rb") as f:
                try:
                    toml_dict = tomllib.load(f)
                    # Check for repeated entries across previous nested dictionaries
                    for item in file_data:
                        repeats = check_dict_leaves(item[1], toml_dict, [])
                        for elem in repeats:
                            conflicts.append((elem, file, item[0]))

                    file_data.append((file, toml_dict))
                except tomllib.TOMLDecodeError as err:
                    LOGGER.critical(
                        f"Configuration file {file} is incorrectly formatted.\n"
                        f"Failed with the following message:\n{err}"
                    )
                    return None

    # Check if any tags are repeated across files
    if len(conflicts) != 0:
        # If so generate full list of errors
        msg = "The following tags are defined in multiple config files:\n"
        for conf in conflicts:
            msg += f"{conf[0]} defined in both {conf[1]} and {conf[2]}\n"
        msg = msg[:-1]
        LOGGER.critical(msg)
        return None

    # Merge everything into a single dictionary
    config_dict: dict = {}
    for item in file_data:
        dpath.util.merge(config_dict, item[1])

    # Validate against the core schema
    # TODO - extend to combine schema as required
    # NEED TO HANDLE ALL THE SCHEMA NOT FOUND, SCHEMA REPEAT KEYS ERRORS HERE AS WELL
    validate(instance=config_dict, schema=config_schema)

    # Merge them into a single object
    # 2 remaining critical errors, missing tags, failed validation against schema
    # Basically a matter of how best to report the errors validation spits out
    # Output combined toml (or json?) file, maybe into the same folder
    # Return the config object as a final module output


validate_config("virtual_rainforest/core")
