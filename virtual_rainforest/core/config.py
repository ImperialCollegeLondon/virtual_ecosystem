"""The :mod:`~virtual_rainforest.core.config` module is used to read in the various
configuration files, validate their contents, and then configure a ready to run instance
of the virtual rainforest model. The basic details of how this system is used can be
found :doc:`here </virtual_rainforest/core/config>`.

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
using the :func:`importlib.resources.path` context manager:

.. code-block:: python

    with resources.path(
        "virtual_rainforest.models.soil", "soil_schema.json"
    ) as schema_file_path:
        register_schema(module_name="soil", schema_file_path=schema_file_path)

The base Virtual Rainforest module will automatically import modules when it is
imported, which ensures that all modules schemas are registered in
:attr:`~virtual_rainforest.core.config.SCHEMA_REGISTRY`.
"""  # noqa: D205, D415

import json
import sys
from collections import ChainMap
from pathlib import Path
from typing import Any, Generator, Iterator, Optional, Union

import dpath.util  # type: ignore
import tomli_w
from jsonschema import Draft202012Validator, FormatChecker, exceptions, validators

from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

SCHEMA_REGISTRY: dict[str, Any] = {}
"""A registry for different module schema.

:meta hide-value:
"""


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
        SCHEMA_REGISTRY[module_name] = load_schema(module_name, schema_file_path)
    except Exception as excep:
        LOGGER.critical(f"Schema registration for {module_name} failed: check log")
        raise excep

    LOGGER.info("Schema registered for module %s: %s ", module_name, schema_file_path)


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
    integrated schema that can then be used to validate a mergedconfiguration for those
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
        List of variables that are defined in multiple places
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


class Config(dict):
    """Draft config class."""

    def __init__(self, cfg_paths: Union[str, list[str]]):
        # Define custom attributes
        self.cfg_paths = (
            [cfg_paths] if isinstance(cfg_paths, (str, Path)) else cfg_paths
        )
        self.toml_inputs: dict[Path, dict] = {}
        self.failed_inputs: dict[Path, str] = {}
        self.merged_config: dict = {}
        self.merge_conflicts: list = []
        self.merged_schema: dict[str, Any]
        self.config_errors: list[tuple[str, Any]] = []
        self.validated: bool = False

        # Run the validation steps
        self.resolve_config_files()
        self.build_config()
        self.build_schema()
        self.validate_config()

    def resolve_config_files(self) -> None:
        """Resolve config file paths into a set of TOML config paths.

        The :class:`~virtual_rainforest.core.config.Config` class is initialised with a
        set of paths to TOML config files or directories containing sets of files. This
        method resolves those paths to the set of paths to individual TOML config files.
        """

        toml_files: list[Path] = []
        not_found: list[str] = []  # Stores all invalid paths
        empty_folder: list[str] = []  # Stores all empty toml folders

        for path in self.cfg_paths:
            p = Path(path)
            # Check if each path is to a file or a directory
            if p.is_dir():
                toml_in_dir = list([f for f in p.glob("*.toml")])
                if toml_files:
                    toml_files.extend(toml_in_dir)
                else:
                    empty_folder.append(path)
            elif p.is_file():
                toml_files.append(p)
            else:
                # Add missing path to list of missing paths
                not_found.append(path)

        # Check for items that are not found
        if not_found:
            to_raise = ConfigurationError(
                f"Some config paths do not exist: {','.join(not_found)}"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        # And for empty folders
        if empty_folder:
            to_raise = ConfigurationError(
                f"Config directories contain no toml files: {','.join(empty_folder)}"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        # Check that no files are resolved twice
        dupl_files = set([str(md) for md in toml_files if toml_files.count(md) > 1])
        if dupl_files:
            to_raise = ConfigurationError(
                f"Repeated files in config paths: {','.join(dupl_files)}"
            )
            LOGGER.critical(to_raise)

        # Load the contents into the instance
        for this_file in toml_files:
            try:
                with open(this_file, "rb") as file_io:
                    self.toml_inputs[this_file] = tomllib.load(file_io)
            except tomllib.TOMLDecodeError as err:
                self.failed_inputs[this_file] = str(err)
                LOGGER.error(f"Config TOML parsing error in {this_file}: {str(err)}")

        if self.failed_inputs:
            to_raise = ConfigurationError("Errors parsing config files: check log")
            LOGGER.critical(to_raise)
            raise to_raise

    def build_config(self) -> None:
        """Build a combined configuration from the loaded files.

        This method does pairwise comparisons of the loaded config data from individual
        files and merges them to build a single configuration dictionary. If there are
        duplicate definitions, an error is logged.
        """

        # Loop over loaded TOML checking each file against the previous entries in the
        # dictionary
        input_keys = list(self.toml_inputs.keys())

        for idx, this_key in enumerate(input_keys):
            # Get a list of the keys before this one
            previous_keys = input_keys[:idx]
            # Check this key doesn't overlap with all previous ones
            for this_previous in previous_keys:
                repeats = check_dict_leaves(
                    self.toml_inputs[this_previous], self.toml_inputs[this_key], []
                )

                for elem in repeats:
                    self.merge_conflicts.append((elem, this_key, previous_keys))
                    LOGGER.error(f"Duplicate configuration across files for {elem}")

        # Check if any tags are repeated across files
        if self.merge_conflicts:
            to_raise = ConfigurationError(
                "Config file contain duplicate definitions: check log"
            )
            LOGGER.critical(to_raise)
            raise to_raise
        else:
            # Merge everything into a single dictionary and update the object
            self.update(dict(ChainMap(*self.toml_inputs.values())))

    def build_schema(self) -> None:
        """Build a schema to validate the model configuration.

        This method first validates the 'core' configuration, which sets the requested
        modules to be used in the configured model. The schemas for the requested
        modules are then loaded and combined to generate a single validation schema for
        model configuration.
        """

        # Get the core schema and then use it to validate the 'core' element of the
        # configuration dictionary
        core_schema = SCHEMA_REGISTRY["core"]
        self._validate_and_set_defaults(self["core"], core_schema)

        # Cannot proceed if there are configuration errors in the core - this validation
        # also should ensure that the config["core"]["modules"] element is populated
        if self.config_errors:
            return

        # Generate a dictionary of schemas for requested modules
        all_schemas: dict[str, Any] = {"core": core_schema}
        requested_modules = self["core"]["modules"]
        for module in requested_modules:
            # Trap unknown model schemas
            if module not in SCHEMA_REGISTRY:
                to_raise = ConfigurationError(
                    f"Configuration contains model with no schema: {module}"
                )
                LOGGER.error(to_raise)
                raise to_raise

            all_schemas[module] = SCHEMA_REGISTRY[module]

        # Merge the schemas into a single combined schema
        self.merged_schema = merge_schemas(all_schemas)

    def validate_config(self) -> None:
        """Validates the loaded config."""

        # Check to see if the instance is in a validatable state
        if not self.merged_schema:
            raise RuntimeError("Merged schema not built.")

        # Run the validation, which either populates self.config_errors or updates the
        # config data in place
        self._validate_and_set_defaults(self, self.merged_schema)

        if self.config_errors:
            LOGGER.error("Invalid configuration - see config_errors.")
        else:
            self.validated = True
            LOGGER.info("Configuration validated")

    def export_config(self, outfile: Path) -> None:
        """Exports a validated and merged configuration as a single file."""

        # Output combined toml file
        with open(outfile, "wb") as toml_file:
            tomli_w.dump(self, toml_file)
        LOGGER.info("Saving config to: %s", outfile)

    def _validate_and_set_defaults(
        self, config: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        """Validate a config dictionary against a schema and set default values.

        This method takes a config dictionary (or subset of one) and validates it
        against the provided schema. Where default values are provided in the schema,
        missing required values are filled using those defaults.

        The behaviour of this method is tricky - the config dictionary is updated in
        place and it can be used on a subsection of a dictionary, which makes it useful
        for bootstrapping the core config in order to build a full model schema.

        Args:
            config: A dictionary containing config information
            schema: The schema that the config dictionary should conform to.
        """

        val = ValidatorWithDefaults(schema, format_checker=FormatChecker())
        errors = [
            (str(list(error.path)), error.message) for error in val.iter_errors(config)
        ]

        if errors:
            self.config_errors.extend(errors)
            LOGGER.error("Configuration schema violations - check config_errors")
        else:
            val.validate(config)
