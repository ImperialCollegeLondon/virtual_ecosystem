"""The :mod:`~virtual_ecosystem.core.config_builder` provides tools to load a set of
TOML formatted configuration dictionaries, either from files or from strings. String
inputs are primarily intended for use in configuring models for testing, where it is
more convenient to simply provide a string.

The main class :class:`ConfigurationLoader` handles the loading of configuration data
and compiling multiple sources into a single dictionary of configuration data.

The :func:`generate_configuration` function then:

* takes a compiled dictionary of configuration settings,
* assembles a pydantic validation model class using the configuration validators for
  each of the requested science modules, and
* passes the data through the validator to return a validated configuration model for
  the simulation.

Canonical usage patterns for the module would be:

.. code-block:: python

    config_data = ConfigurationLoader(...)
    config_object = generate_configuration(config_data.data)

"""  # noqa: D205

import tomllib
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import ValidationError, create_model

from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.registry import MODULE_REGISTRY, register_module


def merge_configuration_dicts(
    dest: dict, source: dict, **kwargs
) -> tuple[dict, set[str]]:
    """Recursively merge two configuration dictionaries.

    This function returns a copy of the input ``dest`` dictionary that has been extended
    recursively with the entries from the input ``source`` dictionary.

    The merging process looks for duplicated settings. In general, if two input
    dictionaries share complete key paths (that is a set of nested dictionary keys
    leading to a value) then that indicates a duplicated setting. The values might be
    identical, but the configuration files should not duplicate settings. When
    duplicated key paths are found, the value from the source dictionary is used and the
    function extends the returned ``conflicts`` set with the duplicated key path.

    However an exception is where both entries are lists - for example, resulting from a
    TOML array of tables (https://toml.io/en/v1.0.0#array-of-tables). In this case, it
    is reasonable to append the source values to the destination values. The motivating
    example here are `[[core.data.variable]]` entries, which can quite reasonably be
    split across configuration sources. Note that no attempt is made to check that the
    combined values are congruent - this is deferred to error handling when the
    configuration data is loaded.

    Args:
        dest: A dictionary to extend
        source: A dictionary of key value pairs to extend ``dest``
        **kwargs: Additional arguments used in recursion

    Returns:
        A copy of dest, extended recursively with values from source, and a tuple of
        duplicate key paths.
    """

    # Copy inputs to avoid mangling inputs
    dest = deepcopy(dest)
    source = deepcopy(source)

    # Populate conflicts and path from defaults or kwargs. These are not provided as
    # explicit arguments, because they would never really be used outside of recursion
    # and so are not really part of the API.
    conflicts: set = kwargs.get("conflicts", set())
    path: str | None = kwargs.get("path", None)

    # Loop over the elements in the source dictionary
    for src_key, src_val in source.items():
        # Get the source key from the dest dictionary and then check for three possible
        # outcomes of comparing dest_val and src_val
        dest_val = dest.get(src_key)

        if isinstance(dest_val, dict) and isinstance(src_val, dict):
            # Both values for this key are dictionaries, so recurse, extending the path
            next_path = src_key if path is None else f"{path}.{src_key}"
            dest[src_key], conflicts = merge_configuration_dicts(
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
            # but extend the conflicts set with the path to the conflicting key.
            dest[src_key] = src_val
            conflict_path = src_key if path is None else f"{path}.{src_key}"
            conflicts.add(conflict_path)

            # NOTE: Could extend here to check for dest_val == src_val and then ignore
            #       duplicate matching definitions, but cleaner to just forbid overlap.

    return dest, conflicts


def compile_configuration_data(data: list[dict]) -> tuple[dict, set[str]]:
    """Compile a combined configuration multiple configuration dictionaries.

    This method sequentially merges configuration dictionaries, such as those loaded
    from multiple individual configuration files, into a single configuration
    dictionary. It returns the merged dictionary and a set of keys that have duplicated
    definitions in the input files.
    """

    # Handle empty lists
    if len(data) == 0:
        LOGGER.warning("No config files set")
        return {}, set()

    # Just return the contents for a singleton list
    if len(data) == 1:
        return data[0], set()

    # Otherwise, merge other dicts into first
    compiled = data[0]

    for src in data[1:]:
        compiled, conflicts = merge_configuration_dicts(compiled, src)

    return compiled, conflicts


def _resolve_config_paths(config_dir: Path, config_dict: dict[str, Any]) -> None:
    """Resolve paths in a configuration file.

    Configuration files may contain keys providing file paths for data and other
    settings: these paths may be absolute but also could be relative to the specific
    configuration file. This becomes a problem when configurations are compiled across
    multiple configuration files, possibly in different locations, so this function
    searches the configuration dictionary loaded from a single file and updates
    configured relative paths to their absolute paths.

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

    if not config_dir.is_absolute():
        config_dir = config_dir.absolute()

    for key, item in config_dict.items():
        if isinstance(item, dict):
            _resolve_config_paths(config_dir=config_dir, config_dict=item)
        elif isinstance(item, list):
            for list_entry in item:
                if isinstance(list_entry, dict):
                    _resolve_config_paths(config_dir=config_dir, config_dict=list_entry)
        elif key.endswith("_path"):
            if not isinstance(item, str):
                raise ValueError(
                    f"The value for config key '{key}' is not a string: {item}"
                )
            file_path = Path(item)
            if not file_path.is_absolute():
                # The resolve method is used here because it is the only method to
                # resolve ../ entries from relative file paths and then the path is made
                # explicitly absolute
                file_resolved = (config_dir / file_path).resolve().absolute()

                config_dict[key] = str(file_resolved)


class ConfigurationLoader:
    """Configuration loading.

    The ``ConfigurationLoader`` class is used to load and compile configuration data for
    a Virtual Ecosystem simulation. Configuration data can be passed in as one of:

    * a list of paths to individual TOML configuration files or directories of TOML
      files  (the ``cfg_paths`` argument) or
    * a list of TOML strings providing configuration data (the ``cfg_strings``
      argument).

    In both cases, there is initial input validation of the argument values and then two
    data handling steps are run.

    Data loading
    ~~~~~~~~~~~~

    The :meth:`_load_data` method handles the parsing of the TOML inputs. For
    configuration data passed as strings, this is largely checking that the data is
    valid TOML.

    For configuration data passed as paths, the following steps occur:

    * The :meth:`_collect_config_paths` method is used to compile a complete list of the
      individual TOML files to be used to build the configuration from the provided
      paths.

    * The :meth:`_load_config_toml` method is then
      used to parse the TOML content of each file, verifying that is valid TOML, and
      then store the parsed contents.

    * The :meth:`_resolve_config_file_paths` method is then used to to update file paths
      in configuration inputs to resolve them to absolute file paths. This is so that
      the file paths in the final compiled configuration data are all mutually
      resolvable, as the input files may use relative paths and do not necessarily all
      live in the same directory.

    At the end of this step, the :attr:`toml_contents` attribute will have been
    populated with individual parsed dictionaries of configuration data from each file
    or input string.

    Data compilation
    ~~~~~~~~~~~~~~~~

    The :meth:`_compile_data` method is then run to compile the different individual
    dictionaries into a single configuration document. This method checks that
    configuration settings are uniquely set across the various configuration data
    sources. The :attr:`data` attribute then contains the complete compiled set of
    configuration data from the provided sources.


    Args:
        cfg_paths: A string, Path or list of strings or Paths giving configuration
            file or directory paths.
        cfg_strings: A string or list of strings containing TOML formatted configuration
            data.
        override_params: Extra parameters provided by the user.
        autoload: A boolean flag that can be used to turn off automatic data loading and
            compilation.
    """

    def __init__(
        self,
        cfg_paths: str | Path | Sequence[str | Path] = [],
        cfg_strings: str | list[str] = [],
        override_params: dict[str, Any] | None = None,
        autoload: bool = True,
    ) -> None:
        # Define attributes
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
        self.from_cfg_strings: bool = False
        """A boolean flag indicating whether paths or strings were used to create the
        instance."""
        self.model_classes: dict[str, Any] = {}  # FIXME: -> dict[str, Type[BaseModel]]
        """A dictionary of the model classes specified in the configuration, keyed by
        model name."""
        self.override_params: dict[str, Any] | None = override_params
        """An optional set of parameters that can be used to override configuration data
        loaded from file."""
        self.data: dict[str, Any]
        """A dictionary of the compiled configuration data from the provided data
        sources."""

        # Prohibit using neither paths and string or both paths and strings. Note that
        # these trap empty lists, so you have to provide _something_.
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
            self.cfg_strings = (
                [cfg_strings] if isinstance(cfg_strings, str) else cfg_strings
            )
            self.from_cfg_strings = True

        if cfg_paths:
            # Standardise cfg_paths to list of Paths
            self.cfg_paths = (
                [Path(cfg_paths)]
                if isinstance(cfg_paths, str | Path)
                else [Path(p) for p in cfg_paths]
            )

        if autoload:
            self._load_data()
            self._compile_data()

    def _load_data(self):
        """Load configuration data.

        This method loads configuration data from the sources set when the class
        instance was created.
        """
        if self.from_cfg_strings:
            # Load the TOML content
            self._load_config_toml_string()
        else:
            # Load the TOML content from resolved paths and resolve file paths
            # within configuration files.
            self._collect_config_paths()
            self._load_config_toml()
            self._resolve_config_file_paths()

    def _compile_data(self):
        """Compile configuration data.

        This method compiles loaded configuration data into a single data dictionary,
        warning of conflicting or repeated settings across the sources.
        """

        data, conflicts = compile_configuration_data(list(self.toml_contents.values()))

        # Report on duplicated settings, sorting the conflicts to give stable ordering
        # in log reports and errors.
        if conflicts:
            to_raise = ConfigurationError(
                f"Duplicated entries in config files: {', '.join(sorted(conflicts))}",
            )
            LOGGER.critical(to_raise)
            raise to_raise

        # Override any existing parameters. Conflicts are allowed here - although this
        # mechanism can also be used to set configuration options _not_ in the other
        # sources - so do nothing about conflicting settings
        if self.override_params is not None:
            data, _ = merge_configuration_dicts(data, self.override_params)

        self.data = data

        LOGGER.info("Configuration data compiled.")

    def _collect_config_paths(self) -> None:
        """Collect TOML config files from provided paths.

        The :class:`ConfigurationLoader` class is initialised with a list of paths to
        either individual TOML config files or directories containing possibly multiple
        config files. This method examines that list to collect all the individual TOML
        config files in the provided locations and then populates the :attr:`toml_files`
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

    def _load_config_toml(self) -> None:
        """Load the contents of resolved configuration files.

        This method populates the :attr:`toml_contents` dictionary with the contents of
        the configuration files set in :attr:`toml_files`.

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

    def _load_config_toml_string(self) -> None:
        """Load the contents of a config provided as a string.

        This method populates the :attr:`toml_contents` dictionary with the parsed
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

    def _resolve_config_file_paths(self) -> None:
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


def build_configuration_model(
    requested_modules: list[str],
) -> type[CompiledConfiguration]:
    """Build a configuration model for a simulation.

    This function identifies the modules to be configured from the top-level
    configuration keys in a compiled configuration dictionary. It then registers the
    required modules to populate the module registry and to access the BaseModel and
    root configuration models for each requested model.

    The configuration models are then combined dynamically to give a single combined
    pydantic base model for the model elements requested for a given simulation. This is
    returned and can then be used to validate the data provided in the configuration
    files.

    The returned model class also provides the class variables ``_model_classes`` that
    provides a dictionary of the requested modules and their BaseModel instances.
    """

    # The core module is mandatory
    if "core" not in requested_modules:
        requested_modules = ["core", *requested_modules]

    # Register the requested modules, which handles unknown module names. This step is
    # required to populate the module registry with the details of the requested modules
    for module in requested_modules:
        module = (
            "virtual_ecosystem.core"
            if module == "core"
            else f"virtual_ecosystem.models.{module}"
        )
        register_module(module)

    # Create a list of submodels in the configuration.
    submodels = (
        (module, MODULE_REGISTRY[module].config) for module in requested_modules
    )

    # Use pydantic create_model to dynamically generate a model with a field for each
    # requested module
    #  Mypy does not like this, but it seems to be used as intended:
    # https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation
    combined_model = create_model(
        "CompiledConfiguration",
        __base__=CompiledConfiguration,
        **{fname: (cname, cname()) for fname, cname in submodels},
    )  # type: ignore[call-overload]

    # Populate the _model_classes class variable with the required dictionary of VE
    # BaseModel science models by requested model name.
    combined_model._model_classes = {
        m: MODULE_REGISTRY[m].model for m in requested_modules if m != "core"
    }

    return combined_model


def generate_configuration(data: dict[str, Any] = {}) -> CompiledConfiguration:
    """Generate a configuration model from configuration data.

    This method takes a dictionary of configuration data and tries to build a validated
    configuration model. The input data is typically loaded and compiled using the
    :class:`ConfigurationLoader` class.

    The first step is to take the root sections in the configuration data - indicating
    the various science models requested for a simulation - and uses those to build a
    composite configuration validator class.

    The provided data is then passed into the validator. If validation is successful
    then a validated configuration object is returned, otherwise the specific validation
    errors are written to the log and the function raises a :class`ConfigurationError`

    Args:
        data: A dictionary of unvalidated configuration data.
    """

    # Build the configuration model from the compiled configuration
    try:
        ConfigurationModel = build_configuration_model(
            requested_modules=list(data.keys())
        )
    except (ModuleNotFoundError, RuntimeError) as err:
        LOGGER.critical(str(err))
        raise

    LOGGER.info("Configuration model built.")

    try:
        configuration = ConfigurationModel().model_validate(data)
    except ValidationError as validation_errors:
        for error in validation_errors.errors():
            LOGGER.error(
                f"{'.'.join(str(x) for x in error['loc'])} = {error['input']}: "
                f"{error['msg']}"
            )
        LOGGER.critical("Configuration validation failed. See errors above.")
        raise ConfigurationError("Validation errors in configuration data - check log.")

    # self.override_config(override_params)
    LOGGER.info("Configuration validated.")

    return configuration
