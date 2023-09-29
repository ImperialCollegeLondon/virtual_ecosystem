"""The :mod:`~virtual_rainforest.core.registry` module is used to populate the
:data:`~virtual_rainforest.core.registry.MODULE_REGISTRY`. This provides a dictionary
for the core components of Virtual Rainforest modules that is used in model
configuration. The core components included in the registry are:

* The module schema, used to validate configuration data for running a simulation.
* Any module constants classes, which are then available for automatic validation
    and instance creation.
* The model class associated with the module.

Note that the  :mod:`virtual_rainforest.core` module does not have an associated model
but does have a schema and constants.

The module provides the :func:`~virtual_rainforest.core.registry.register_module`
umbrella function and then separate functions to handle the components:
:func:`~virtual_rainforest.core.registry.register_schema`,
:func:`~virtual_rainforest.core.registry.register_model` and
:func:`~virtual_rainforest.core.registry.register_constants_classes`.
"""  # noqa: D205, D415


import sys
from dataclasses import is_dataclass
from importlib import resources
from inspect import getmembers, isclass
from pathlib import Path
from types import ModuleType
from typing import Any

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.schema import load_schema

MODULE_REGISTRY: dict[str, Any] = {}
"""Information about module schemas, constants and model, keyed by module name.

The registry is a dictionary keyed by the final part of the module name. The entry for
each module is itself a dictionary with 'model', 'constants' and 'schema' entries. For
example:

MODULE_REGISTRY['plants']['model'] = <virtual_rainforest.models.plants.PlantsModel>
MODULE_REGISTRY['plants']['constants'] = [
    'PlantsConsts': <virtual_rainforest.models.plants.constants.PlantsConsts>
]
MODULE_REGISTRY['plants']['schema'] = {schema_dict}
"""


def register_module(module_name: str) -> None:
    """Register module components.

    This functions registers the module schemas, any constants classes and the main
    Model for Virtual Rainforest modules with the global MODULE_REGISTRY object.

    Args:
        module_name: The name of the module containing the model to be registered

    Raises:
        ConfigurationError: If the module does not define a single Model class which is
            a child of BaseModel.
    """

    # Get a reference to the module and get the short name
    try:
        module = sys.modules[module_name]
    except KeyError as excep:
        LOGGER.critical(f"Unknown module - registration failed: {module_name}")
        raise excep

    module_name_short = module_name.split(".")[-1]
    is_not_core = module_name != "virtual_rainforest.core"

    LOGGER.info(f"Registering {module_name} module components")

    # Create an entry for the module
    if module_name_short not in MODULE_REGISTRY:
        MODULE_REGISTRY[module_name_short] = {}

    # Register the model unless this is core
    if is_not_core:
        register_model(
            module=module, module_name=module_name, module_name_short=module_name_short
        )

    # Register the schema
    schema_file_name = "model_schema.json" if is_not_core else "core_schema.json"
    with resources.as_file(
        resources.files(module) / schema_file_name
    ) as schema_file_path:
        register_schema(
            module_name_short=module_name_short, schema_file_path=schema_file_path
        )

    # Find and register the constant dataclasses
    register_constants_classes(module=module, module_name_short=module_name_short)


def register_model(
    module: ModuleType, module_name: str, module_name_short: str
) -> None:
    """Register the model component of a module.

    This function automatically looks for a single subclass of a
    :class:`~virtual_rainforest.core.base_model.BaseModel` within the members of the
    provided module and adds it to the module registry.

    Args:
        module: A module object that might contain constants classes.
        module_name: The full name of a module
        module_name_short: The short name of the module.
    """
    from virtual_rainforest.core.base_model import BaseModel

    # Extract BaseModel objects from the module root
    model = [
        (obj_name, obj)
        for obj_name, obj in getmembers(module)
        if isclass(obj) and issubclass(obj, BaseModel)
    ]

    # Trap missing and multiple models
    if len(model) == 0:
        excep = RuntimeError(f"Model object not found in {module_name}")
        LOGGER.critical(excep)
        raise excep

    if len(model) > 1:
        excep = RuntimeError(f"More than one model defined in in {module_name}")
        LOGGER.critical(excep)
        raise excep

    # Trap models that do not follow the requirement that the BaseModel.model_name
    # attribute matches the virtual_rainforest.models.model_name
    # TODO - can we retire the model_name attribute if it just duplicates the module
    #        name
    model_name, model_obj = model[0]
    if module_name_short != model_obj.model_name:
        excep = RuntimeError(
            f"The model_name attribute does not match the module name in {module_name}"
        )
        LOGGER.critical(excep)
        raise excep

    # Register the resulting single model
    MODULE_REGISTRY[module_name_short]["model"] = model_obj
    LOGGER.info(f"Registered class for {module_name_short} model: {model_name}")


def register_schema(module_name_short: str, schema_file_path: Path) -> None:
    """Simple function to add configuration schema to the registry.

    Args:
        module_name: The name to register the schema under
        schema_file_path: The file path to the JSON Schema file for the model

    Raises:
        ValueError: If the module name has already been used to register a schema
    """

    if (
        module_name_short in MODULE_REGISTRY
        and "schema" in MODULE_REGISTRY[module_name_short]
    ):
        excep = ValueError(
            f"The module schema for {module_name_short} is already registered"
        )
        LOGGER.critical(excep)
        raise excep

    try:
        MODULE_REGISTRY[module_name_short]["schema"] = load_schema(
            module_name_short, schema_file_path
        )
    except Exception as excep:
        LOGGER.critical(
            f"Schema registration for {module_name_short} failed: check log"
        )
        raise excep

    LOGGER.info(
        "Schema registered for module %s: %s ", module_name_short, schema_file_path
    )


def register_constants_classes(module: ModuleType, module_name_short: str) -> None:
    """Simple function to add a constants class to the registry.

    Args:
        module: A module object that might contain constants classes.
        module_name_short: The short name of the module

    Raises:
        ValueError: If the model and class name have already been used to register a
            constants class
    """

    constants_classes = (
        class_ for class_ in getmembers(module.constants) if is_dataclass(class_[1])
    )

    if "constants" not in MODULE_REGISTRY[module_name_short]:
        MODULE_REGISTRY[module_name_short]["constants"] = {}

    for class_name, class_obj in constants_classes:
        if class_name in MODULE_REGISTRY[module_name_short]["constants"]:
            excep = ValueError(
                f"Constants class {module_name_short}.{class_name} already registered"
            )
            LOGGER.critical(excep)
            raise excep

        # Add data class to the constants registry
        MODULE_REGISTRY[module_name_short]["constants"][class_name] = class_obj

        LOGGER.info("Constants class %s.%s registered", module_name_short, class_name)
