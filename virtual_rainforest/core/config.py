"""The :mod:`core.config` module is used to read in the various configuration files,
validate their contents, and then configure a ready to run instance of the virtual
rainforest model. The basic details of how this system is used can be found :doc:`here
</virtual_rainforest/core/config>`.

When a new module is defined a ``JSONSchema`` file should be written, which includes the
expected configuration tags, their expected types, and any constraints on their values
(e.g. the number of soil layers being strictly positive). Additionally, where sensible
default values exist (e.g. 1 week for the model time step) they should also be included
in the schema. This schema should be saved in the folder of the module that it relates
to. In order to make this schema generally accessible the module's ``__init__.py``
should call the :func:`~virtual_rainforest.core.config.register_schema` function, which
will load and validate the schema before adding it to the registry. You will need to
provides a module name to register the schema under, which should be unique to that
model. The function also requires the path to the schema file, which should be located
using the :meth:`importlib.resources.path()` context manager:

.. code-block:: python

    with resources.path(
        "virtual_rainforest.models.soil", "soil_schema.json"
    ) as schema_file_path:
        register_schema(module_name="soil", schema_file_path=schema_file_path)

The base :mod:`virtual_rainforest` module will automatically import modules when it is
imported, which ensures that all modules schemas are registered in
:attr:`~virtual_rainforest.core.config.SCHEMA_REGISTRY`.
"""  # noqa: D205, D415

import json
import sys
from collections import ChainMap
from copy import deepcopy
from pathlib import Path
from typing import Any, Generator, Iterator, Optional, Union

import dpath.util  # type: ignore
import tomli_w
from jsonschema import Draft202012Validator, FormatChecker, exceptions, validators

from virtual_rainforest.core.logger import LOGGER

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

SCHEMA_REGISTRY: dict = {}
"""A registry for different module schema.

:meta hide-value:
"""


class ConfigurationError(Exception):
    """Custom exception class for configuration failures."""

    pass


def log_all_validation_errors(
    errors: Generator[Any, None, None], complete: bool
) -> None:
    """Logs all validation errors and raises an exception.

    A tag is constructed to allow the location of each error to be better determined.
    For each error this is then printed along with the error message.

    Raises:
        ConfigurationError: As at least one validation error has occurred.
    """
    if complete:
        conf = "complete"
    else:
        conf = "core"

    for error in errors:
        # Construct details of the tag associated with the error
        tag = ""
        for k in error.path:
            tag += f"[{k}]"
        LOGGER.error("%s: %s" % (tag, error.message))

    to_raise = ConfigurationError(
        f"Validation of {conf} configuration files failed see above errors"
    )
    LOGGER.critical(to_raise)
    raise to_raise


#  Set up a JSON Schema validator that fills in default values


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


ValidatorWithDefaults = validators.extend(
    Draft202012Validator, {"properties": set_defaults}
)


def register_schema(module_name: str, schema_file_path: Path) -> None:
    """Simple function to add configuration schema to the registry.

    Args:
        module_name: The name to register the schema under
        schema_file_path: The file path to the JSON Schema file for the model

    Raises:
        ValueError: If the module name has already been used to register a schema
    """

    if module_name in SCHEMA_REGISTRY:
        excep = ValueError(f"The module schema for {module_name} is already registered")
        LOGGER.critical(excep)
        raise excep

    try:
        SCHEMA_REGISTRY[module_name] = get_schema(module_name, schema_file_path)
    except Exception as excep:
        LOGGER.critical(f"Schema registration for {module_name} failed: check log")
        raise excep

    LOGGER.info("Schema registered for module %s: %s ", module_name, schema_file_path)


def get_schema(module_name: str, schema_file_path: Path) -> dict:
    """Function to load the JSON schema for a module.

    This function tries to load a JSON schema file and then - if the JSON loaded
    correctly - checks that the JSON provides a valid JSON Schema.

    Args:
        module_name: The name to register the schema under
        schema_file_path: The file path to the JSON Schema file

    Raises:
        ValueError: the module name has no registered schema path
        FileNotFoundError: the schema path does not exist
        JSONDecodeError: the file at the schema path is not valid JSON
        SchemaError: the file contents are not valid JSON Schema
        ValueError: the JSON Schema is missing required keys
    """

    try:
        fobj = open(schema_file_path)
        json_schema = json.load(fobj)
    except FileNotFoundError as excep:
        LOGGER.error(excep)
        raise excep
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

    LOGGER.info("Module schema for %s loaded", module_name)

    return json_schema


def check_dict_leaves(
    d1: dict[str, Any],
    d2: dict[str, Any],
    conflicts: Optional[list] = None,
    path: Optional[list] = None,
) -> list[str]:
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


def check_outfile(merge_file_path: Path) -> None:
    """Check that final output file is not already in the output folder.

    Args:
        merge_file_path: Path that merged config file is meant to be saved to
    Raises:
        ConfigurationError: If the final output directory doesn't exist, isn't a
            directory, or the final output file already exists.
    """

    # Extract parent folder name and output file name. If this is a relative path, it is
    # expected to be relative to where the command is being run.
    if not merge_file_path.is_absolute():
        parent_fold = merge_file_path.parent.relative_to(".")
    else:
        parent_fold = merge_file_path.parent
    out_file_name = merge_file_path.name

    # Throw critical error if the output folder doesn't exist
    if not Path(parent_fold).exists():
        to_raise = ConfigurationError(
            f"The user specified output directory ({parent_fold}) doesn't exist!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    elif not Path(parent_fold).is_dir():
        to_raise = ConfigurationError(
            f"The user specified output folder ({parent_fold}) isn't a directory!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # Throw critical error if combined output file already exists
    for file in Path(parent_fold).iterdir():
        if file.name == f"{out_file_name}":
            to_raise = ConfigurationError(
                f"A config file in the user specified output folder ({parent_fold}) "
                f"already makes use of the specified output file name ({out_file_name})"
                f", this file should either be renamed or deleted!"
            )
            LOGGER.critical(to_raise)
            raise to_raise

    return None


def collect_files(cfg_paths: list[str]) -> list[Path]:
    """Collect all toml files from a user specified list of files and directories.

    Args:
        cfg_paths: A path or a set of paths that point to either configuration files, or
            folders containing configuration files
    Raises:
        ConfigurationError: If toml configuration files cannot be found at the specified
            locations, or if configuration files are specified more than once (this is
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
        to_raise = ConfigurationError(
            f"The following (user provided) config paths do not exist:\n{not_found}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # And for empty folders
    if len(empty_fold) != 0:
        to_raise = ConfigurationError(
            f"The following (user provided) config folders do not contain any toml "
            f"files:\n{empty_fold}"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # Finally check that no files are pointed to twice
    if len(files) != len(set(files)):
        to_raise = ConfigurationError(
            f"A total of {len(files) - len(set(files))} config files are specified more"
            f" than once (possibly indirectly)"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return files


def load_in_config_files(files: list[Path]) -> dict[str, Any]:
    """Load in a set of toml files checking that no tags are repeated.

    This function also ensure that no tags are repeated across different toml files.

    Args:
        files: List of files to be read in and checked for overlapping tags
    Raises:
        ConfigurationError: If files are poorly formatted or tags are repeated between
            files
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
                to_raise = ConfigurationError(
                    f"Configuration file {file} is incorrectly formatted. Failed with "
                    f"the following message:\n{err}"
                )
                LOGGER.critical(to_raise)
                raise to_raise

    # Check if any tags are repeated across files
    if len(conflicts) != 0:
        # If so generate full list of errors
        msg = "The following tags are defined in multiple config files:\n"
        for conf in conflicts:
            msg += f"{conf[0]} defined in both {conf[1]} and {conf[2]}\n"
        msg = msg[:-1]
        to_raise = ConfigurationError(msg)
        LOGGER.critical(to_raise)
        raise to_raise

    # Merge everything into a single dictionary
    config_dict = dict(ChainMap(*file_data.values()))

    return config_dict


def add_core_defaults(config_dict: dict[str, Any]) -> None:
    """Add default config options for the core module to the config dictionary.

    This is a separate function because the default modules to load are specified in the
    core schema. So, these defaults must be populated before the complete schema can be
    constructed.

    Args:
        config_dict: The complete configuration settings for the particular model
            instance
    Raises:
        ConfigurationError: If the core module schema can't be found, or if it cannot be
            validated
    """

    # Look for core config in schema registry
    if "core" in SCHEMA_REGISTRY:
        core_schema = SCHEMA_REGISTRY["core"]
    else:
        to_raise = ConfigurationError(
            "Expected a schema for core module configuration, it was not provided!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    try:
        ValidatorWithDefaults(core_schema, format_checker=FormatChecker()).validate(
            config_dict
        )
    except exceptions.ValidationError:
        # Find full set of errors
        errors = ValidatorWithDefaults(
            core_schema, format_checker=FormatChecker()
        ).iter_errors(config_dict)
        # Then log all errors in validating core config
        log_all_validation_errors(errors, False)


def find_schema(config_dict: dict[str, Any]) -> list[str]:
    """Find which schema the configuration requires to be loaded.

    Args:
        config_dict: The complete configuration settings for the particular model
            instance
    Raises:
        ConfigurationError: If core configuration does not list the other modules to
            configure, or any module is specified to be configured twice
    """

    # Find which other schema should be searched for
    try:
        modules = config_dict["core"]["modules"]
    except KeyError:
        to_raise = ConfigurationError(
            "Core configuration does not specify which other modules should be "
            "configured!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    # Add core to list of modules if its not already included
    if "core" not in modules:
        modules.append("core")

    if len(modules) != len(set(modules)):
        to_raise = ConfigurationError(
            f"The list of modules to configure given in the core configuration file "
            f"repeats {len(modules) - len(set(modules))} names!"
        )
        LOGGER.critical(to_raise)
        raise to_raise

    return modules


def construct_combined_schema(modules: list[str]) -> dict[str, Any]:
    """Load validation schema for desired modules, and combine into a single schema.

    Args:
        modules: List of modules to load schema for
    Raises:
        ConfigurationError: If a particular module schema can't be found
    """

    # Construct combined schema for all relevant modules
    comb_schema: dict = {}

    # Loop over expected modules and add them to the registry
    for module in modules:
        if module in SCHEMA_REGISTRY:
            # Store complete schema if no previous schema has been added
            if comb_schema == {}:
                comb_schema = deepcopy(SCHEMA_REGISTRY[module])
            # Otherwise only save truncated part of the schema
            else:
                comb_schema["properties"][module] = deepcopy(
                    SCHEMA_REGISTRY[module]["properties"][module]
                )
                # Add module name to list of required modules
                comb_schema["required"].append(module)
        else:
            to_raise = ConfigurationError(
                f"Expected a schema for {module} module configuration, it was not "
                f"provided!"
            )
            LOGGER.critical(to_raise)
            raise to_raise

    p_paths = []
    # Recursively search for all instances of properties in the schema
    for path, value in dpath.util.search(comb_schema, "**/properties", yielded=True):
        # Remove final properties instance from path so that additionalProperties ends
        # up in the right place
        p_paths.append(
            ""
            if path == "properties"
            else path[::-1].replace("seitreporp/", "", 1)[::-1]
        )

    # Set additional properties to false everywhere that properties are defined
    for path in p_paths:
        dpath.util.new(comb_schema, f"{path}/additionalProperties", False)

    return comb_schema


def validate_with_defaults(
    config_dict: dict[str, Any], comb_schema: dict[str, Any]
) -> None:
    """Validate the configuration settings against the combined schema.

    This function also adds default values into the configuration dictionary where it is
    appropriate.

    Args:
        config_dict: The complete configuration settings for the particular model
            instance
        comb_schema: Combined schema for all modules that are being configured

    Raises:
        ConfigurationError: If the configuration files fail to validate against the JSON
            schema
    """

    # Validate the input configuration settings against the combined schema
    # This step also adds in all default module configuration details
    try:
        ValidatorWithDefaults(comb_schema, format_checker=FormatChecker()).validate(
            config_dict
        )
    except exceptions.ValidationError:
        # Find full set of errors
        errors = ValidatorWithDefaults(
            comb_schema, format_checker=FormatChecker()
        ).iter_errors(config_dict)
        # Then log all errors in validating complete config
        log_all_validation_errors(errors, True)


def validate_config(
    cfg_paths: Union[str, list[str]],
    merge_file_path: Path = Path("./vr_full_model_configuration.toml"),
) -> dict[str, Any]:
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
    is then returned for use in downstream simulation setup.

    Args:
        cfg_paths: A path or a set of paths that point to either configuration files, or
            folders containing configuration files
        merge_file_path: Path to save merged config file to
    """

    # Check that there isn't a final output file saved in the final output folder
    check_outfile(merge_file_path)
    # If this passes collect the files
    if isinstance(cfg_paths, str):
        files = collect_files([cfg_paths])
    else:
        files = collect_files(cfg_paths)

    # Then load all config files to a combined config dict
    config_dict = load_in_config_files(files)

    # Add in core configuration defaults
    add_core_defaults(config_dict)

    # Find schema to load in
    modules = find_schema(config_dict)

    # Construct combined schema for all relevant modules
    comb_schema = construct_combined_schema(modules)

    # Validate all the complete configuration, adding in module defaults where required
    validate_with_defaults(config_dict, comb_schema)

    LOGGER.info("Configuration files successfully validated!")

    # Output combined toml file, into the initial config folder
    LOGGER.info("Saving all configuration details to %s" % merge_file_path)
    with open(merge_file_path, "wb") as toml_file:
        tomli_w.dump(config_dict, toml_file)

    # Return the complete validated config
    return config_dict
