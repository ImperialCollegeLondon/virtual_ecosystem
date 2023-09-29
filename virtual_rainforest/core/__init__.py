"""The :mod:`~virtual_rainforest.core` module contains the key shared resources and
building blocks used to develop the different component models of the Virtual Rainforest
and then to configure them, populate them with data and provide logging.

Each of the core sub-modules has its own API reference page:

* The :mod:`~virtual_rainforest.core.config` submodule covers the definition of formal
  configuration schema for components and the parsing and validation of TOML
  configuration documents against those schema.
* The :mod:`~virtual_rainforest.core.logger` configures the :class:`~logging.Logger`
  instance used throughout the package.
* The :mod:`~virtual_rainforest.core.grid` submodule covers the definition of the
  spatial layout to be used in a simulation and provides an interface to the spatial
  relationships between cells.
* The :mod:`~virtual_rainforest.core.data` submodule provides the central data object
  used to store data required by the simulation and methods to populate that data object
  for use in simulations.
* The :mod:`~virtual_rainforest.core.readers` submodule provides functionality to read
  external data files into a standard internal format.
* The :mod:`~virtual_rainforest.core.axes` submodule provides validation for data to
  ensure that it is congruent with the model configuration.
* The :mod:`~virtual_rainforest.core.base_model` submodule provides an Abstract Base
  Class describing the shared API to be used by science models within the Virtual
  Rainforest.
* The :mod:`~virtual_rainforest.core.constants` contains the constants that are shared
  across multiple models.
* The :mod:`~virtual_rainforest.core.utils` contains the utility functions that are used
  across the Virtual Rainforest.
* The :mod:`~virtual_rainforest.core.exceptions` submodule defines custom exceptions
  that are used either in the core module, or across multiple modules.

The :mod:`~virtual_rainforest.core` module itself is only responsible for loading the
configuration schema for the core submodules.
"""  # noqa: D205, D415

from importlib import resources

from virtual_rainforest import AUTODISCOVER
from virtual_rainforest.core.config import register_schema

if AUTODISCOVER:
    with resources.path(
        "virtual_rainforest.core", "core_schema.json"
    ) as schema_file_path:
        register_schema(module_name="core", schema_file_path=schema_file_path)
