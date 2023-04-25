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
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator, Union

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

# Schema handling functions


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


def config_merge(
    dest: dict, source: dict, conflicts: tuple = (), path: str = ""
) -> tuple[dict, tuple]:
    """Recursively merge two dictionaries detecting duplicated key definitions.

    This function returns a copy of the dest dictionary that has been extended
    recursively with the entries from the source dictionary. No key path should be
    repeated between the two dictionaries. When duplicated key paths are found, the
    value from the source dictionary is used and the function extends the returned
    ``conflicts`` tuple with the conflicting key path.

    Args:
        dest: A dictionary to extend
        source: A dictionary of key value pairs to extend dest
        conflicts: A tuple of duplicated key paths between the two dictionaries
        path: A string giving the current key path.

    Returns:
        A copy of dest, extended recursively with values from source, and a tuple of
        duplicate key paths.
    """

    # Copy inputs to avoid mangling inputs
    dest = deepcopy(dest)
    source = deepcopy(source)

    # Loop over the elements in the source dictionary
    for src_key, src_val in source.items():
        # Get the source key from the dest dictionary and then check for three possible
        # outcomes of comparing dest_val and src_val
        dest_val = dest.get(src_key)

        if isinstance(dest_val, dict) and isinstance(src_val, dict):
            # Both values for this key are dictionaries, so recurse, extending the path
            next_path = src_key if path == "" else f"{path}.{src_key}"
            dest[src_key], conflicts = config_merge(
                dest_val, src_val, conflicts=conflicts, path=next_path
            )
        elif dest_val is None:
            # The key is not currently in dest, so add the key value pair
            dest[src_key] = src_val
        else:
            # The key is in _both_, so override destval with srcval to keep processing,
            # but extend the conflicts tuple with the path to the conflicting key.
            dest[src_key] = src_val
            conflict_path = src_key if path == "" else f"{path}.{src_key}"
            conflicts += (conflict_path,)

            # NOTE: Could extend here to check for dest_val == src_val and then ignore
            #       duplicate matching definitions, but cleaner to just forbid overlap.

    return dest, conflicts


class Config(dict):
    """Draft config class."""

    def __init__(
        self, cfg_paths: Union[str, Path, list[str], list[Path]], auto: bool = True
    ) -> None:
        # Standardise cfg_paths
        if isinstance(cfg_paths, (str, Path)):
            self.cfg_paths = [Path(cfg_paths)]
        else:
            self.cfg_paths = [Path(p) for p in cfg_paths]

        # Define custom attributes
        self.toml_files: list[Path] = []
        self.toml_contents: dict[Path, dict] = {}
        self.failed_inputs: dict[Path, str] = {}
        self.merged_config: dict = {}
        self.merge_conflicts: set = set()
        self.merged_schema: dict[str, Any]
        self.config_errors: list[tuple[str, Any]] = []
        self.validated: bool = False

        # Run the validation steps
        if auto:
            self.resolve_config_paths()
            self.load_config_toml()
            self.build_config()
            self.build_schema()
            self.validate_config()

    def resolve_config_paths(self) -> None:
        """Resolve config file paths into a set of TOML config files.

        The :class:`~virtual_rainforest.core.config.Config` class is initialised with a
        set of paths to TOML config files or directories containing sets of files. This
        method resolves those paths to a set of individual TOML config files and then
        populates the  :attr:`~virtual_rainforest.core.config.Config.toml_files`
        attribute.

        Raises:
            ConfigurationError: this is raised if any of the paths: do not exist, are
            directories that do not contain TOML files, are not TOML files or if the
            resolved files contain duplicate entries.
        """

        all_valid = True

        # Validate the paths
        for path in self.cfg_paths:
            if not path.exists():
                all_valid = False
                LOGGER.error(f"Config file path does not exist: {path}")
            elif path.is_dir():
                toml_in_dir = list(path.glob("*.toml"))
                if toml_in_dir:
                    self.toml_files.extend(toml_in_dir)
                else:
                    all_valid = False
                    LOGGER.error(
                        f"Config directory path contains no TOML files: {path}"
                    )
            elif path.is_file() and path.suffix != ".toml":
                all_valid = False
                LOGGER.error(f"Config file path with non-TOML suffix: {path}")
            else:
                self.toml_files.append(path)

        # Check that no files are resolved twice
        dupl_files = set(
            [str(md) for md in self.toml_files if self.toml_files.count(md) > 1]
        )
        if dupl_files:
            all_valid = False
            LOGGER.error(f"Repeated files in config paths: {','.join(dupl_files)}")

        # Raise if there are any path errors
        if not all_valid:
            to_raise = ConfigurationError("Config paths not all valid: check log.")
            LOGGER.critical(to_raise)
            raise to_raise

        LOGGER.info(f"Config paths resolve to {len(self.toml_files)} files")

    def load_config_toml(self) -> None:
        """Load the contents of resolved configuration files.

        This method populates the
        :attr:`~virtual_rainforest.core.config.Config.toml_contents` dictionary with the
        contents of the configuration files set in
        :attr:`~virtual_rainforest.core.config.Config.toml_files`. That attribute is
        normally populated by providing a set of paths to
        :class:`~virtual_rainforest.core.config.Config` and running the
        :meth:`~virtual_rainforest.core.config.Config.resolve_config_paths` method, but
        it can also be set directly.

        Raises:
            ConfigurationError: Invalid TOML content in config files.
        """
        # Load the contents into the instance
        for this_file in self.toml_files:
            try:
                with open(this_file, "rb") as file_io:
                    self.toml_contents[this_file] = tomllib.load(file_io)
            except tomllib.TOMLDecodeError as err:
                self.failed_inputs[this_file] = str(err)
                LOGGER.error(f"Config TOML parsing error in {this_file}: {str(err)}")
            else:
                LOGGER.info(f"Config TOML loaded from {this_file}")

        if self.failed_inputs:
            to_raise = ConfigurationError("Errors parsing config files: check log")
            LOGGER.critical(to_raise)
            raise to_raise

    def build_config(self) -> None:
        """Build a combined configuration from the loaded files.

        This method does pairwise merging of the loaded config data from individual
        files to build a single configuration dictionary, looking for duplicate
        definitions in the config tree.

        Raises:
            ConfigurationError: if duplicate config definitions occur across files.
        """

        # Get the config dictionaries
        input_dicts = list(self.toml_contents.values())

        if len(input_dicts) == 0:
            # No input dicts, Config dict is empty
            return

        if len(input_dicts) == 1:
            # One input dict, which becomes the content of the Config dict
            self.update(**input_dicts[0])
            return

        # Otherwise, merge other dicts into first
        master = input_dicts[0]
        others = input_dicts[1:]
        conflicts: tuple = ()

        for each_dict in others:
            master, conflicts = config_merge(master, each_dict, conflicts=conflicts)

        # Check if any tags are repeated across files
        if conflicts:
            self.merge_conflicts = set(conflicts)
            to_raise = ConfigurationError(
                f"Duplicated entries in config files: {','.join(self.merge_conflicts)}"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        # Merge everything into a single dictionary and update the object
        self.update(master)
        LOGGER.info("Config files merged")

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
