"""The `core.config` module.

The `core.config` module is used to read in the various configuration files, validate
their contents, and then configure a ready to run instance of the virtual rainforest
model.
"""
# TODO - find config folder based on command line argument

import sys
from collections import ChainMap
from pathlib import Path
from typing import Callable, Optional, Union

import dpath.util  # type: ignore
import jsonschema
import tomli_w

from virtual_rainforest.core.logger import LOGGER, log_and_raise

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# Dictionary to store schema registry
SCHEMA_REGISTRY: dict = {}


def register_schema(module_name: str) -> Callable:
    """Decorator function to add configuration schema to the registry.

    Args:
        module_name: The name to register the schema under
    Raises:
        ValueError: If the schema name has already been used
        OSError: If the module schema is not valid JSON
        KeyError: If a module schema is missing one of the required keys
    """

    def wrap(func: Callable) -> Callable:
        if module_name in SCHEMA_REGISTRY:
            log_and_raise(
                f"The module schema {module_name} is used multiple times, this "
                f"shouldn't be the case!",
                ValueError,
            )
        else:
            # Check that this is a valid schema
            try:
                jsonschema.Draft202012Validator.check_schema(func())
            except jsonschema.exceptions.SchemaError:
                log_and_raise(
                    f"Module schema {module_name} not valid JSON!",
                    OSError,
                )
            # Check that relevant keys are included
            try:
                func()["properties"][module_name]
                func()["required"]
            except KeyError as err:
                log_and_raise(
                    f"Schema for {module_name} module incorrectly structured, {err} key"
                    f" missing!",
                    KeyError,
                )
            # If it is valid then add it to the registry
            SCHEMA_REGISTRY[module_name] = func()

        return func

    return wrap


# Dictionary to store validated config
COMPLETE_CONFIG: dict = {}


def check_dict_leaves(
    d1: dict, d2: dict, conflicts: Optional[list] = None, path: Optional[list] = None
) -> list:
    """Recursively checks if leaves are repeated between two nested dictionaries.

    Args:
        d1: First nested dictionary to compare
        d2: Second nested dictionary to compare
        path: List describing recursive path through the nested dictionary
            conflicts: List of variables that are defined in multiple places

    Returns:
        conflicts: List of variables that are defined in multiple places
    """

    if conflicts is None:
        conflicts = []

    if path is None:
        path = []

    for key in d2:
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                check_dict_leaves(d1[key], d2[key], conflicts, path + [str(key)])
            else:
                conflicts.append("%s" % ".".join(path + [str(key)]))

    return conflicts


def check_outfile(output_folder: str, out_file_name: str) -> None:
    """Check that final output file is not already in the output folder.

    Args:
        output_folder: Path to a folder to output the outputted complete configuration
            file to
        out_file_name: The name to save the outputted complete configuration file under
    Raises:
        OSError: If the final output file already exist.
    """

    # Throw critical error if combined output file already exists
    for file in Path(output_folder).iterdir():
        if file.name == f"{out_file_name}.toml":
            log_and_raise(
                f"A config file in the specified configuration folder already makes use"
                f" of the specified output file name ({out_file_name}.toml), this file "
                f"should either be renamed or deleted!",
                OSError,
            )

    return None


def collect_files(cfg_paths: list[str]) -> list[Path]:
    """Collect all toml files from a user specified list of files and directories.

    Args:
        cfg_paths: A path or a set of paths that point to either configuration files, or
            folders containing configuration files
    Raises:
        OSError: If toml configuration files cannot be found at the specified locations
        RuntimeError: If configuration files are specified more than once (this is
            likely to be through both direct and indirect specification)
    """

    # Preallocate file list
    files: list[Path] = []
    not_found: list[str] = []  # Stores all invalid paths
    empty_fold: list[str] = []  # Stores all empty toml folders

    for path in cfg_paths:
        p = Path(path)
        # Check if each path is to a file or a directory
        if p.is_dir():
            toml_files = list([f for f in p.glob("*.toml")])
            if len(toml_files) != 0:
                files.extend(toml_files)
            else:
                empty_fold.append(path)
        elif p.is_file():
            files.append(p)
        else:
            # Add missing path to list of missing paths
            not_found.append(path)

    # Check for items that are not found
    if len(not_found) != 0:
        log_and_raise(
            f"The following (user provided) config paths do not exist:\n{not_found}",
            OSError,
        )
    # And for empty folders
    elif len(empty_fold) != 0:
        log_and_raise(
            f"The following (user provided) config folders do not contain any toml "
            f"files:\n{empty_fold}",
            OSError,
        )
    # Finally check that no files are pointed to twice
    elif len(files) != len(set(files)):
        log_and_raise(
            f"A total of {len(files) - len(set(files))} config files are specified more"
            f" than once (possibly indirectly)",
            RuntimeError,
        )

    return files


def load_in_config_files(files: list[Path]) -> dict:
    """Load in a set of toml files checking that no tags are repeated.

    This function also ensure that no tags are repeated across different toml files.

    Args:
        files: List of files to be read in and checked for overlapping tags
    Raises:
        RuntimeError: If files are poorly formatted or tags are repeated between files
    """

    # Preallocate container for file names and corresponding dictionaries
    file_data: dict[Path, dict] = {}
    conflicts = []

    # Load all toml files that we want to read from
    for file in files:
        # If not then read in the file data
        with file.open("rb") as f:
            try:
                toml_dict = tomllib.load(f)
                # Check for repeated entries across previous nested dictionaries
                for existing_file, existing_dict in file_data.items():
                    repeats = check_dict_leaves(existing_dict, toml_dict, [])
                    for elem in repeats:
                        conflicts.append((elem, file, existing_file))

                file_data[file] = toml_dict
            except tomllib.TOMLDecodeError as err:
                log_and_raise(
                    f"Configuration file {file} is incorrectly formatted. Failed with "
                    f"the following message:\n{err}",
                    RuntimeError,
                )

    # Check if any tags are repeated across files
    if len(conflicts) != 0:
        # If so generate full list of errors
        msg = "The following tags are defined in multiple config files:\n"
        for conf in conflicts:
            msg += f"{conf[0]} defined in both {conf[1]} and {conf[2]}\n"
        msg = msg[:-1]
        log_and_raise(msg, RuntimeError)

    # Merge everything into a single dictionary
    config_dict = dict(ChainMap(*file_data.values()))

    return config_dict


def find_schema(config_dict: dict) -> list[str]:
    """Find which schema the configuration requires to be loaded.

    Args:
        config_dict: The complete configuration settings for the particular model
            instance
    Raises:
        KeyError: If core configuration does not list the other modules to configure
        RuntimeError: If any module is specified to be configured twice
    """

    # Find which other schema should be searched for
    try:
        modules = config_dict["core"]["modules"]
    except KeyError:
        log_and_raise(
            "Core configuration does not specify which other modules should be "
            "configured!",
            KeyError,
        )

    # Add core to list of modules if its not already included
    if "core" not in modules:
        modules.append("core")

    if len(modules) != len(set(modules)):
        log_and_raise(
            f"The list of modules to configure given in the core configuration file "
            f"repeats {len(modules) - len(set(modules))} names!",
            RuntimeError,
        )

    return modules


def construct_combined_schema(modules: list[str]) -> dict:
    """Load validation schema for desired modules, and combine into a single schema.

    Args:
        modules: List of modules to load schema for
    Raises:
        RuntimeError: If a particular module schema can't be found
    """

    # Construct combined schema for all relevant modules
    comb_schema: dict = {}

    # Loop over expected modules and add them to the registry
    for module in modules:
        if module in SCHEMA_REGISTRY:
            # Store complete schema if no previous schema has been added
            if comb_schema == {}:
                comb_schema = SCHEMA_REGISTRY[module]
            # Otherwise only save truncated part of the schema
            else:
                comb_schema["properties"][module] = SCHEMA_REGISTRY[module][
                    "properties"
                ][module]
                # Add module name to list of required modules
                comb_schema["required"].append(module)
        else:
            log_and_raise(
                f"Expected a schema for {module} module configuration, it was not "
                f"provided!",
                RuntimeError,
            )

    p_paths = []
    # Recursively search for all instances of properties in the schema
    for (path, value) in dpath.util.search(comb_schema, "**/properties", yielded=True):
        p_paths.append("" if path == "properties" else path.replace("/properties", ""))

    # Set additional properties to false everywhere that properties are defined
    for path in p_paths:
        dpath.util.new(comb_schema, f"{path}/additionalProperties", False)

    return comb_schema


def validate_config(
    cfg_paths: Union[str, list[str]],
    output_folder: str = ".",
    out_file_name: str = "complete_config",
) -> None:
    """Validates the contents of user provided config files.

    This function first reads in a set of configuration files in `.toml` format. This
    either consists of all `.toml` files in a specified folder, or a set of user
    specified files within this folder. Checks are carried out to ensure that these
    files are correctly formatted. The module validation schemas are extracted from
    `SCHEMA_REGISTRY` for the modules the user has specified to configure (in
    `config.core.modules`). These schemas are then consolidated into a single combined
    JSON schema. This combined schema is then used to validate the combined contents of
    the configuration files. If this validation passes the combined configuration is
    saved in toml format in the specified configuration file folder. This configuration
    is finally used to populate the global `COMPLETE_CONFIG` dictionary.

    Args:
        cfg_paths: A path or a set of paths that point to either configuration files, or
            folders containing configuration files
        output_folder: Path to a folder to output the outputted complete configuration
            file to
        out_file_name: The name to save the outputted complete configuration file under.

    Raises:
        RuntimeError: If the configuration files fail to validate against the JSON
            schema
    """

    # Check that there isn't a final output file saved in the final output folder
    check_outfile(output_folder, out_file_name)
    # If this passes collect the files
    if isinstance(cfg_paths, str):
        files = collect_files([cfg_paths])
    else:
        files = collect_files(cfg_paths)

    # Then load all config files to a combined config dict
    config_dict = load_in_config_files(files)

    # Find schema to load in
    modules = find_schema(config_dict)

    # Construct combined schema for all relevant modules
    comb_schema = construct_combined_schema(modules)

    # Validate the input configuration settings against the combined schema
    try:
        jsonschema.validate(instance=config_dict, schema=comb_schema)
    except jsonschema.exceptions.ValidationError as err:
        log_and_raise(
            f"Validation of configuration files failed: {err.message}", RuntimeError
        )

    LOGGER.info("Configuration files successfully validated!")

    # Output combined toml file, into the initial config folder
    LOGGER.info(
        f"Saving all configuration details to {output_folder}/{out_file_name}.toml"
    )
    with open(f"{output_folder}/{out_file_name}.toml", "wb") as toml_file:
        tomli_w.dump(config_dict, toml_file)

    # Populate the global config dictionary with the complete validated config
    COMPLETE_CONFIG["config"] = config_dict
