"""The :mod:`~virtual_ecosystem.core.config` module is used to read in the various
configuration files, validate their contents, and then configure a ready to run instance
of the virtual ecosystem model. The basic details of how this system is used can be
found :doc:`here </using_the_ve/configuration/config>`.

The validation of configuration documents is done using JSONSchema documents associated
with the different model components. See the :mod:`~virtual_ecosystem.core.schema`
module for details.
"""  # noqa: D205

import sys
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

import tomli_w
from jsonschema import FormatChecker

from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.registry import MODULE_REGISTRY, register_module
from virtual_ecosystem.core.schema import ValidatorWithDefaults, merge_schemas

if sys.version_info[:2] >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def config_merge(
    dest: dict, source: dict, conflicts: tuple = (), path: str = ""
) -> tuple[dict, tuple]:
    """Recursively merge two dictionaries detecting duplicated key definitions.

    This function returns a copy of the input ``dest`` dictionary that has been extended
    recursively with the entries from the input ``source`` dictionary.

    In general, if two input dictionaries share complete key paths (that is a set of
    nested dictionary keys leading to a value) then that indicates a duplicated setting.
    The values might be identical, but the configuration files should not duplicate
    settings. When  duplicated key paths are found, the value from the source dictionary
    is used and the function extends the returned ``conflicts`` tuple with the
    duplicated key path.

    However an exception is where both entries are lists - resulting from a TOML array
    of tables (https://toml.io/en/v1.0.0#array-of-tables). In this case, it is
    reasonable to append the source values to the destination values. The motivating
    example here are `[[core.data.variable]]` entries, which can quite reasonably be
    split across configuration sources. Note that no attempt is made to check that the
    combined values are congruent - this is deferred to error handling when the
    configuration is used.

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
        elif isinstance(dest_val, list) and isinstance(src_val, list):
            # Both values for this key are lists, so merge the lists
            dest[src_key] = [*dest_val, *src_val]
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


def _resolve_config_paths(config_dir: Path, config_dict: dict[str, Any]) -> None:
    """Resolve paths in a configuration file.

    Configuration files may contain keys providing file paths for data and other
    settings: these paths may be absolute but also could be relative to the specific
    configuration file. This becomes a problem when configurations are compiled across
    multiple configuration files, possibly in different locations, so this function
    searches the configuration dictionary loaded from a single file and updates
    configure paths to be congruent from the directory in which Virtual Ecosystem is
    being run.

    At present, the configuration schema does not have an explicit mechanism to type a
    configuration option as being a path, so we currently use the `_path` suffix to
    indicate configuration options setting a path. So, this function recursively search
    a configuration file payload for values stored under keys ending in `_path` and
    resolves the paths.

    Args:
        config_dir: A folder containing a configuration file.
        config_dict: A dictionary of contents of the configuration file, which may
            contain file paths to resolve.

    Raises:
        ValueError: if a key ending in ``_path`` has a non-string value.
    """

    for key, item in config_dict.items():
        if isinstance(item, dict):
            _resolve_config_paths(config_dir=config_dir, config_dict=item)
        elif isinstance(item, list):
            for list_entry in item:
                _resolve_config_paths(config_dir=config_dir, config_dict=list_entry)
        elif key.endswith("_path"):
            if not isinstance(item, str):
                raise ValueError(
                    f"The value for config key '{key}' is not a string: {item}"
                )
            file_path = Path(item)
            if not file_path.is_absolute():
                # The resolve method is used here because it is the only method to
                # resolve ../ entries from relative file paths. However, it also makes
                # all paths absolute, which lengthens paths if the config directory
                # itself is relative. The approach here converts `path/to/config` and
                # `../data/file1.nc` to `path/to/data/file1.nc` when both paths are
                # relative
                file_resolved = (config_dir / file_path).resolve()
                if not config_dir.is_absolute():
                    config_absolute = Path(config_dir.root).absolute()
                    file_resolved = file_resolved.relative_to(config_absolute)

                config_dict[key] = str(file_resolved)


class Config(dict):
    """Configuration loading and validation.

    The ``Config`` class is used to generate a validated configuration for a Virtual
    Ecosystem simulation. The ``cfg_paths`` attribute is used to provide paths to TOML
    configuration files or directories containing sets of files to be used. The provided
    paths are then run through the follow steps to resolve and load the configuration
    data.

    * The :meth:`~virtual_ecosystem.core.config.Config.collect_config_paths` method is
      used to collect the actual TOML files to be used to build the configuration from
      the provided paths.

    * The :meth:`~virtual_ecosystem.core.config.Config.load_config_toml` method is then
      used to load the parsed contents of each resolved file into the
      :attr:`~virtual_ecosystem.core.config.Config.toml_contents` attribute.

    Alternatively, configuration data may be passed as a string or list of strings using
    the ``cfg_strings`` argument. These strings must contain TOML formatted data, which
    is parsed and added to the
    :attr:`~virtual_ecosystem.core.config.Config.toml_contents` attribute.

    Whichever approach is used, the next two steps are then applied to the provided TOML
    data:

    * The :meth:`~virtual_ecosystem.core.config.Config.build_config` method is used to
      merge the loaded configuration across files and check that configuration settings
      are uniquely defined.

    * The :meth:`~virtual_ecosystem.core.config.Config.validate_config` method
      validates the compiled configuration against the appropriate configuration schema
      for the :mod:`~virtual_ecosystem.core` module and any models included in the
      configuration. This validation will also fill in any missing configuration
      settings with defined defaults.

    By default, creating a ``Config`` instance automatically runs these steps across the
    provided ``cfg_paths``, but the ``auto`` argument can be used to turn off automatic
    validation.

    The :meth:`~virtual_ecosystem.core.config.Config.export_config` method can be used
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
        cfg_paths: str | Path | Sequence[str | Path] = [],
        cfg_strings: str | list[str] = [],
        override_params: dict[str, Any] = {},
        auto: bool = True,
    ) -> None:
        # Define custom attributes
        self.cfg_paths: list[Path] = []
        """The configuration file paths, normalised from the cfg_paths argument."""
        self.toml_files: list[str | Path] = []
        """A list of TOML file paths resolved from the initial config paths."""
        self.cfg_strings: list[str] = []
        """A list of strings containing TOML content, provided by the ``cfg_strings``
        argument."""
        self.toml_contents: dict[str | Path, dict] = {}
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
        self.model_classes: dict[str, Any] = {}  # FIXME: -> dict[str, Type[BaseModel]]
        """A dictionary of the model classes specified in the configuration, keyed by
        model name."""

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
            if isinstance(cfg_paths, str | Path):
                self.cfg_paths = [Path(cfg_paths)]
            else:
                self.cfg_paths = [Path(p) for p in cfg_paths]

        if auto:
            if cfg_strings:
                # Load the TOML content
                self.load_config_toml_string()
            if cfg_paths:
                # Load the TOML content from resolved paths and resolve file paths
                # within configuration files.
                self.collect_config_paths()
                self.load_config_toml()
                self.resolve_config_file_paths()

        if auto:
            # Now build the merged configuration and validate it.
            self.build_config()
            self.override_config(override_params)
            self.build_schema()
            self.validate_config()

    def collect_config_paths(self) -> None:
        """Collect TOML config files from provided paths.

        The :class:`~virtual_ecosystem.core.config.Config` class is initialised with a
        list of paths to either individual TOML config files or directories containing
        possibly multiple config files. This method examines that list to collect all
        the individual TOML config files in the provided locations and then populates
        the :attr:`~virtual_ecosystem.core.config.Config.toml_files` attribute.

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
        dupl_files = {
            str(md) for md in self.toml_files if self.toml_files.count(md) > 1
        }
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
        :attr:`~virtual_ecosystem.core.config.Config.toml_contents` dictionary with the
        contents of the configuration files set in
        :attr:`~virtual_ecosystem.core.config.Config.toml_files`. That attribute is
        normally populated by providing a set of paths to
        :class:`~virtual_ecosystem.core.config.Config` and running the
        :meth:`~virtual_ecosystem.core.config.Config.collect_config_paths` method, but
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
                LOGGER.error(f"Config TOML parsing error in {this_file}: {err!s}")
            else:
                LOGGER.info(f"Config TOML loaded from {this_file}")

        if failed_inputs:
            to_raise = ConfigurationError("Errors parsing config files: check log")
            LOGGER.critical(to_raise)
            raise to_raise

    def load_config_toml_string(self) -> None:
        """Load the contents of a config provided as a string.

        This method populates the
        :attr:`~virtual_ecosystem.core.config.Config.toml_contents` dictionary with the
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
                    f"TOML parsing error in cfg_strings: {err!s}"
                )
                LOGGER.critical(to_raise)
                raise to_raise

        LOGGER.info("Config TOML loaded from config strings")

    def resolve_config_file_paths(self) -> None:
        """Resolve the locations of configured file paths.

        Configuration files can contain paths to other resources, such as the paths to
        files containing input data variables. These paths can be absolute, but may also
        be relative to the location of the configuration file itself. This method is
        used to resolve the location of files to the common root of the provided set of
        configuration files, typically the path where a simulation is started.
        """

        # Safeguard against running this when the toml_contents is from a cfg_string
        if self.from_cfg_strings:
            # TODO - how to resolve relative paths in cfg_string - niche use case
            LOGGER.warning("Config file paths not resolved with cfg_string")
            return

        for config_file, contents in self.toml_contents.items():
            if isinstance(config_file, Path):
                try:
                    _resolve_config_paths(
                        config_dir=config_file.parent, config_dict=contents
                    )
                except ValueError as excep:
                    LOGGER.critical(excep)
                    raise excep

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

        This method identifies the modules to be configured from the top-level
        configuration keys, setting the requested modules to be used in the configured
        simulation. The schemas for the requested modules are then loaded and combined
        using the :meth:`~virtual_ecosystem.core.schema.merge_schemas` function to
        generate a single validation schema for model configuration.
        """

        # Extract the requested modules, which are the top-level config keys.
        requested_modules: list[str] = list(self.keys())

        # Warn if implicitly using core defaults, otherwise remove core to generate a
        # list of optional modules to be registered.
        if "core" not in requested_modules:
            LOGGER.warning("No core configuration section, using defaults.")
        else:
            requested_modules.remove("core")

        # Register the core module components and access the core schema.
        register_module("virtual_ecosystem.core")
        core_schema = MODULE_REGISTRY["core"].schema

        # Attempt to register the requested modules - this function will handle unknown
        # module names and exit.
        for module in requested_modules:
            register_module(f"virtual_ecosystem.models.{module}")

        # Generate a dictionary of schemas for requested modules and populate the
        # model_classes attribute
        all_schemas: dict[str, Any] = {"core": core_schema}
        for module in requested_modules:
            all_schemas[module] = MODULE_REGISTRY[module].schema
            self.model_classes[module] = MODULE_REGISTRY[module].model

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
        :attr:`~virtual_ecosystem.core.config.Config.config_errors` attribute.

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
        :class:`~virtual_ecosystem.core.config.Config` instance has been successfully
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
