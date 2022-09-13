"""The `core.config` module.

The `core.config` module is used to read in the various configuration files, validate
their contents, and then configure a ready to run instance of the virtual rainforest
model.
"""
# TODO - find config folder based on command line argument

import os
import sys
from typing import Callable

import dpath.util
import jsonschema
import tomli_w

from virtual_rainforest.core.logger import LOGGER

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# Dictionary to store schema registry
SCHEMA_REGISTRY: dict = {}


def register_schema(module_name: str) -> Callable:
    """Decorator function to add configuration schema to the registry."""

    def wrap(func: Callable):
        SCHEMA_REGISTRY[module_name] = func()

    return wrap


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

    # Set output file name
    out_file_name = "complete_config"

    # Find and load all toml files supplied config directory
    for file in os.listdir(filepath):
        if file.endswith(".toml"):
            # Throw critical error if combined output file already exists
            if file == f"{out_file_name}.toml":
                LOGGER.critical(
                    f"A config file in the specified configuration folder makes use of "
                    f"the reserved name {out_file_name}.toml. This file should either "
                    f"be renamed or deleted!"
                )
                return None
            # If not then read in the file data
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

    # Find which other schema should be searched for
    try:
        modules = config_dict["config"]["core"]["modules"]
    except KeyError:
        LOGGER.critical(
            "Core configuration does not specify which other modules should be "
            "configured!"
        )
        return None

    # Add core to list of modules if its not already included
    if "core" not in modules:
        modules.append("core")

    if len(modules) != len(set(modules)):
        LOGGER.critical(
            f"The list of modules to configure given in the core configuration file "
            f"repeats {len(modules) - len(set(modules))} names!"
        )
        return None

    # Construct combined schema for all relevant modules
    comb_schema: dict = {}

    # Loop over expected modules and add them to the registry
    for module in modules:
        if module in SCHEMA_REGISTRY:
            try:
                m_schema = SCHEMA_REGISTRY[module]["properties"]["config"][
                    "properties"
                ][module]
            except KeyError as err:
                LOGGER.critical(
                    f"Schema for {module} module incorrectly structured, {err} key "
                    f"missing!"
                )
                return None
            # Store complete schema if no previous schema has been added
            if comb_schema == {}:
                comb_schema = SCHEMA_REGISTRY[module]
            # Otherwise only save truncated part of the schema
            else:
                comb_schema["properties"]["config"]["properties"][module] = m_schema
                # Add module name to list of required modules
                try:
                    comb_schema["properties"]["config"]["required"].append(module)
                except KeyError:
                    LOGGER.critical(
                        f"The schema for {modules[0]} does not set the module as a "
                        f"required field, so validation cannot occur!"
                    )
                    return None
        else:
            LOGGER.critical(
                f"Expected a schema for {module} module configuration, it was not "
                f"provided!"
            )
            return None

    # Validate the input configuration settings against the combined schema
    try:
        jsonschema.validate(instance=config_dict, schema=comb_schema)
    except jsonschema.exceptions.ValidationError as err:
        LOGGER.critical(f"Validation of configuration files failed: {err.message}")
        return None

    LOGGER.info("Configuration files successfully validated!")

    # Output combined toml file, into the initial config folder
    LOGGER.info(f"Saving all configuration details to {filepath}/{out_file_name}.toml")
    with open(f"{filepath}/{out_file_name}.toml", "wb") as toml_file:
        tomli_w.dump(config_dict, toml_file)

    # TODO - WORK OUT HOW THE CONFIG OBJECT SHOULD BE CONSTRUCTED
    # TODO - RECURSIVE CHECK THAT ADDITIONAL PROPERTIES ARE ALL SET + SET AS FALSE
    # TODO - ADD RELEVANT INFO TO THE DOCUMENTATION
