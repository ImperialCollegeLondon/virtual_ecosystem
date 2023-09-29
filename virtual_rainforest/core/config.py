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
should call the :func:`register_schema` function, which will load and validate the
schema before adding it to the registry. You will need to provides a module name to
register the schema under, which should be unique to that model. The function also
requires the path to the schema file, which should be located using the
:func:`importlib.resources.path` context manager:

.. code-block:: python

    with resources.path(
        "virtual_rainforest.models.soil", "soil_schema.json"
    ) as schema_file_path:
        register_schema(module_name="soil", schema_file_path=schema_file_path)

The base Virtual Rainforest module will automatically import modules when it is
imported, which ensures that all modules schemas are registered in
:attr:`SCHEMA_REGISTRY`.
"""  # noqa: D205, D415
import sys
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any, Union

import tomli_w
from jsonschema import FormatChecker

from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.registry import MODULE_REGISTRY, register_module
from virtual_rainforest.core.schema import ValidatorWithDefaults, merge_schemas

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

SCHEMA_REGISTRY: dict[str, Any] = {}
"""A registry for different module schema.

:meta hide-value:
"""


def config_merge(
    dest: dict, source: dict, conflicts: tuple = (), path: str = ""
) -> tuple[dict, tuple]:
    """Recursively merge two dictionaries detecting duplicated key definitions.

    This function returns a copy of the input ``dest`` dictionary that has been extended
    recursively with the entries from the input ``source`` dictionary. The two input
    dictionaries must not share any key paths and when duplicated key paths are
    found, the value from the source dictionary is used and the function extends the
    returned ``conflicts`` tuple with the duplicated key path.

    Args:
        dest: A dictionary to extend
        source: A dictionary of key value pairs to extend ``dest``
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


def _fix_up_variable_entry_paths(config_dir: Path, params: dict[str, Any]) -> None:
    """Find paths in a dict and make them relative to config_dir.

    Check for file paths in variable entries (i.e. core.data.variable) and make them
    relative to config_dir.

    Args:
        config_dir: The new folder to use as the root for relative paths
        params: The dict to examine
    Todo:
        We may want to fix up other potential paths in config files in future.
    """
    try:
        var_entries = params["core"]["data"]["variable"]
    except KeyError:
        # No variable entries
        return

    if not isinstance(var_entries, list):
        # Must be an array
        return

    for entry in var_entries:
        # Though all variable entries should have a file attribute according to the
        # schema, the config has not been verified at this stage so we need to check
        if "file" in entry:
            file_path = Path(entry["file"])
            if not file_path.is_absolute():
                entry["file"] = str(config_dir / file_path)


class Config(dict):
    """Configuration loading and validation.

    The ``Config`` class is used to generate a validated configuration for a Virtual
    Rainforest simulation. The ``cfg_paths`` attribute is used to provide paths to TOML
    configuration files or directories containing sets of files to be used. The provided
    paths are then run through the follow steps to resolve and load the configuration
    data.

    * The :meth:`~virtual_rainforest.core.config.Config.resolve_config_paths` method is
      used to resolve the provided paths into the set of actual TOML files to be used to
      build the configuration.

    * The :meth:`~virtual_rainforest.core.config.Config.load_config_toml` method is then
      used to load the parsed contents of each resolved file into the
      :attr:`~virtual_rainforest.core.config.Config.toml_contents` attribute.

    Alternatively, configuration data may be passed as a string or list of strings using
    the ``cfg_strings`` argument. These strings must contain TOML formatted data, which
    is parsed and added to the
    :attr:`~virtual_rainforest.core.config.Config.toml_contents` attribute.

    Whichever approach is used, the next two steps are then applied to the provided TOML
    data:

    * The :meth:`~virtual_rainforest.core.config.Config.build_config` method is used to
      merge the loaded configuration across files and check that configuration settings
      are uniquely defined.

    * The :meth:`~virtual_rainforest.core.config.Config.validate_config` method
      validates the compiled configuration against the appropriate configuration schema
      for the :mod:`~virtual_rainforest.core` module and any models included in the
      configuration. This validation will also fill in any missing configuration
      settings with defined defaults.

    By default, creating a ``Config`` instance automatically runs these steps across the
    provided ``cfg_paths``, but the ``auto`` argument can be used to turn off automatic
    validation.

    The :meth:`~virtual_rainforest.core.config.Config.export_config` method can be used
    to export the compiled and validated configuration as a single TOML file.

    If the core.data_output_options.save_merged_config option is set to true a merged
    config file will be automatically generated, unless ``auto`` is set to false.

    Args:
        cfg_paths: A string, Path or list of strings or Paths giving configuration
            file or directory paths.
        cfg_strings: A string or list of strings containing TOML formatted configuration
            data.
        override_params: Extra parameters provided by the user.
        auto: A boolean flag setting whether the configuration data is automatically
            loaded and validated
    """

    def __init__(
        self,
        cfg_paths: Union[str, Path, Sequence[Union[str, Path]]] = [],
        cfg_strings: Union[str, list[str]] = [],
        override_params: dict[str, Any] = {},
        auto: bool = True,
    ) -> None:
        # Define custom attributes
        self.cfg_paths: list[Path] = []
        """The configuration file paths, normalised from the cfg_paths argument."""
        self.toml_files: list[Union[str, Path]] = []
        """A list of TOML file paths resolved from the initial config paths."""
        self.cfg_strings: list[str] = []
        """A list of strings containing TOML content, provided by the ``cfg_strings``
        argument."""
        self.toml_contents: dict[Union[str, Path], dict] = {}
        """A dictionary of the parsed TOML contents of config files or strings, keyed by
        file path or string index."""
        self.merge_conflicts: list = []
        """A list of configuration keys duplicated across configuration files."""
        self.config_errors: list[tuple[str, Any]] = []
        """Configuration errors, as a list of tuples of key path and error details."""
        self.merged_schema: dict = {}
        """The merged schema for the core and modules present in the configuration."""
        self.validated: bool = False
        """A boolean flag indicating successful validation."""
        self.from_cfg_strings: bool = False
        """A boolean flag indicating whether paths or strings were used to create the
        instance."""

        # Prohibit using both paths and string
        if not (cfg_paths or cfg_strings):
            to_raise = ValueError("Provide cfg_paths or cfg_strings.")
            LOGGER.critical(to_raise)
            raise to_raise

        if cfg_paths and cfg_strings:
            to_raise = ValueError("Do not use both cfg_paths and cfg_strings.")
            LOGGER.critical(to_raise)
            raise to_raise

        # Standardise inputs and set from_cfg_strings
        if cfg_strings:
            # Standardise to a list of strings
            if isinstance(cfg_strings, str):
                cfg_strings = [cfg_strings]

            self.cfg_strings = cfg_strings

            self.from_cfg_strings = True
        if cfg_paths:
            # Standardise cfg_paths to list of Paths
            if isinstance(cfg_paths, (str, Path)):
                self.cfg_paths = [Path(cfg_paths)]
            else:
                self.cfg_paths = [Path(p) for p in cfg_paths]

        if auto:
            if cfg_strings:
                # Load the TOML content
                self.load_config_toml_string()
            if cfg_paths:
                # Load the TOML content from resolved paths and fix relative file paths
                self.resolve_config_paths()
                self.load_config_toml()
                self.fix_up_file_paths()

        if auto:
            # Now build the merged configuration and validate it.
            self.build_config()
            self.override_config(override_params)
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

        failed_inputs = False

        # Load the contents into the instance
        for this_file in self.toml_files:
            try:
                with open(this_file, "rb") as file_io:
                    self.toml_contents[this_file] = tomllib.load(file_io)
            except tomllib.TOMLDecodeError as err:
                failed_inputs = True
                LOGGER.error(f"Config TOML parsing error in {this_file}: {str(err)}")
            else:
                LOGGER.info(f"Config TOML loaded from {this_file}")

        if failed_inputs:
            to_raise = ConfigurationError("Errors parsing config files: check log")
            LOGGER.critical(to_raise)
            raise to_raise

    def load_config_toml_string(self) -> None:
        """Load the contents of a config provided as a string.

        This method populates the
        :attr:`~virtual_rainforest.core.config.Config.toml_contents` dictionary with the
        contents of a provided TOML formatted string.

        Raises:
            ConfigurationError: Invalid TOML string.
        """

        for index, cfg_string in enumerate(self.cfg_strings):
            # Load the contents into the instance
            try:
                self.toml_contents[f"cfg_string_{index}"] = tomllib.loads(cfg_string)
            except tomllib.TOMLDecodeError as err:
                to_raise = ConfigurationError(
                    f"TOML parsing error in cfg_strings: {str(err)}"
                )
                LOGGER.critical(to_raise)
                raise to_raise

        LOGGER.info("Config TOML loaded from config strings")

    def fix_up_file_paths(self) -> None:
        """Make any file paths in the configs relative to location of config files."""

        # Safeguard against running this when the toml_contents is from a cfg_string
        if self.from_cfg_strings:
            # TODO - how to resolve relative paths in cfg_string - niche use case
            LOGGER.warning("Config file paths not resolved with cfg_string")
            return

        for config_file, contents in self.toml_contents.items():
            if isinstance(config_file, Path):
                _fix_up_variable_entry_paths(config_file.parent, contents)

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
            LOGGER.warn("No config files set")
            return

        if len(input_dicts) == 1:
            # One input dict, which becomes the content of the Config dict
            self.update(**input_dicts[0])

        else:
            # Otherwise, merge other dicts into first
            master = input_dicts[0]
            others = input_dicts[1:]
            conflicts: tuple = ()

            for each_dict in others:
                master, conflicts = config_merge(master, each_dict, conflicts=conflicts)

            # Check if any tags are repeated across files
            if conflicts:
                self.merge_conflicts = sorted(set(conflicts))
                to_raise = ConfigurationError(
                    "Duplicated entries in config "
                    f"files: {', '.join(self.merge_conflicts)}",
                )
                LOGGER.critical(to_raise)
                raise to_raise

            # Update the object
            self.update(master)

        if self.from_cfg_strings:
            LOGGER.info("Config built from config string")
        else:
            LOGGER.info(f"Config built from {len(input_dicts)} file(s)")

    def build_schema(self) -> None:
        """Build a schema to validate the model configuration.

        This method identifies the modules to be configured from the config
        `core.modules` entry, using the core schema default if this entry is missing.
        This sets the requested modules to be used in the configured model. The schemas
        for the requested modules are then loaded and combined using the
        :meth:`~virtual_rainforest.core.config.merge_schemas` function to generate a
        single validation schema for model configuration.

        Raises:
            ConfigurationError: if the requested modules includes a model name that does
                not have an entry in the
                :data:`~virtual_rainforest.core.config.SCHEMA_REGISTRY`.
        """

        # Extract the modules requested in the configuration, falling back to the schema
        # defaults

        register_module("virtual_rainforest.core")
        core_schema = MODULE_REGISTRY["core"]["schema"]
        defmods = core_schema["properties"]["core"]["properties"]["modules"]["default"]

        try:
            # Provided in config
            requested_modules = self["core"]["modules"]
        except KeyError:
            # Revert to defaults
            requested_modules = defmods

        # Register the requested modules
        for module in requested_modules:
            register_module(f"virtual_rainforest.models.{module}")

        # Generate a dictionary of schemas for requested modules
        all_schemas: dict[str, Any] = {"core": core_schema}
        for module in requested_modules:
            # Trap unknown model schemas
            if module not in MODULE_REGISTRY:
                to_raise = ConfigurationError(
                    f"Configuration contains module with no schema: {module}"
                )
                LOGGER.error(to_raise)
                raise to_raise

            all_schemas[module] = MODULE_REGISTRY[module]["schema"]

        # Merge the schemas into a single combined schema
        self.merged_schema = merge_schemas(all_schemas)
        LOGGER.info("Validation schema for configuration built.")

    def validate_config(self) -> None:
        """Validate the model configuration.

        This method first validates the 'core' configuration and applies defaults, which
        ensures that the modules to be used in the configured model are set. The schemas
        for the requested modules are then applied to each configuration section to
        validate the contents and apply any default values.

        Raises:
            ConfigurationError: if the loaded configuration is not compatible with the
                configuration schemas.
        """

        # Check to see if the instance is in a validatable state
        if not self.merged_schema:
            raise RuntimeError("Merged schema not built.")

        # Run the validation, which either populates self.config_errors or updates the
        # config data in place
        self._validate_and_set_defaults(self, self.merged_schema)

        if self.config_errors:
            for cfg_err_path, cfg_err in self.config_errors:
                LOGGER.error(f"Configuration error in {cfg_err_path}: {cfg_err}")

            to_raise = ConfigurationError(
                "Configuration contains schema violations: check log"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        self.validated = True
        LOGGER.info("Configuration validated")

    def _validate_and_set_defaults(
        self, config_data: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        """Validates config data against a schema and sets default values.

        This private method takes a dictionary containing configuration data and
        validates it against the provided schema. Missing values are filled using
        defaults from the schema where available.

        Note that the configuration data is updated in place and different schema can be
        applied sequentially to incrementally validate subsections of the merged config
        inputs. This is used to validate the core config to confirm the module list
        before then validating individual module configurations. When validation errors
        are found, the details of each validation issue is appended to the
        :attr:`~virtual_rainforest.core.config.Config.config_errors` attribute.

        Args:
            config_data: A dictionary containing model configuration data.
            schema: The schema that the configuration data should conform to.
        """

        val = ValidatorWithDefaults(schema, format_checker=FormatChecker())
        errors = [
            (str(list(error.path)), error.message)
            for error in val.iter_errors(config_data)
        ]

        if errors:
            self.config_errors.extend(errors)
        else:
            val.validate(config_data)

    def export_config(self, outfile: Path) -> None:
        """Exports a validated and merged configuration as a single file.

        This method will only export a configuration file if the
        :class:`~virtual_rainforest.core.config.Config` instance has been successfully
        validated.

        Args:
            outfile: An output path for the TOML configuration file.
        """

        if not self.validated:
            LOGGER.error("Cannot export unvalidated or invalid configuration")
            return

        # Output combined toml file
        with open(outfile, "wb") as toml_file:
            tomli_w.dump(self, toml_file)
        LOGGER.info("Saving config to: %s", outfile)

    def override_config(self, override_params: dict[str, Any]) -> None:
        """Override any parameters desired.

        Args:
            override_params: Extra parameter settings
        """
        updated, conflicts = config_merge(self, override_params, conflicts=tuple())

        # Conflicts are not errors as we want users to be able to override parameters
        if conflicts:
            LOGGER.info(
                "The following parameter values were overridden: "
                + ", ".join(conflicts)
            )

        self.update(updated)
