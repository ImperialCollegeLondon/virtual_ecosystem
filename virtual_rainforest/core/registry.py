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


from dataclasses import dataclass, is_dataclass
from importlib import import_module, resources
from inspect import getmembers
from typing import Any

from virtual_rainforest.core.constants_class import ConstantsDataclass
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.schema import load_schema


@dataclass
class ModuleInfo:
    """Dataclass for module information.

    This dataclass is used to hold individual module registration details within the
    module registry.
    """

    model: Any  # Optional[type[BaseModel]]
    """The BaseModel subclass associated with the module."""
    schema: dict[str, Any]
    """The schema used to validate module configuration."""
    constants_classes: dict[str, ConstantsDataclass]
    """A dictionary of module constants classes."""


MODULE_REGISTRY: dict[str, ModuleInfo] = {}
"""The module registry."""


def register_module(module_name: str, model: Any = None) -> None:
    """Register module components.

    This functions registers the module schemas, any constants classes and the main
    Model for Virtual Rainforest modules with the global MODULE_REGISTRY object.

    Args:
        module_name: The name of the module containing the model to be registered

    Raises:
        ConfigurationError: If the module does not define a single Model class which is
            a child of BaseModel.
    """

    # Try and import the module from the name to get a reference to the module
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as excep:
        LOGGER.critical(f"Unknown module - registration failed: {module_name}")
        raise excep

    # Extract the last component of the module name to act as unique short name
    module_name_short = module_name.split(".")[-1]
    if module_name_short in MODULE_REGISTRY:
        LOGGER.warning(f"Module already registered: {module_name_short}")
        return

    is_core = module_name == "virtual_rainforest.core"

    LOGGER.info(f"Registering {module_name} module components")

    # Check on the model argument.
    if is_core and model:
        msg = "No model should be registered for the core module."
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    if not is_core and model is None:
        msg = "A model class is required to register model modules."
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    if model:
        if module_name_short != model.model_name:
            msg = f"The model_name attribute and module name differ in {module_name}"
            LOGGER.critical(msg)
            raise RuntimeError(msg)

        # Register the resulting single model class
        LOGGER.info(
            f"Registering model class for {module_name_short} model: {model.__name__}"
        )

    # Register the schema
    schema_file_name = "core_schema.json" if is_core else "model_schema.json"
    with resources.as_file(
        resources.files(module) / schema_file_name
    ) as schema_file_path:
        try:
            schema = load_schema(
                module_name=module_name_short, schema_file_path=schema_file_path
            )
        except Exception as excep:
            LOGGER.critical(
                f"Schema registration for {module_name_short} failed: check log"
            )
            raise excep

    LOGGER.info(
        "Schema registered for module %s: %s ", module_name_short, schema_file_path
    )

    # Find and register the constant dataclasses
    try:
        constants_submodule = import_module(f"{module_name}.constants")
    except ModuleNotFoundError:
        constants_submodule = None

    if constants_submodule is None:
        constants_classes = {}
    else:
        # Get all subclasses of ConstantsDataclass, excluding the ABC where imported
        # into the module members.
        constants_classes = {
            class_name: class_obj
            for class_name, class_obj in getmembers(constants_submodule)
            if is_dataclass(class_obj)
            and issubclass(class_obj, ConstantsDataclass)
            and class_obj is not ConstantsDataclass
        }

        for class_name in constants_classes.keys():
            LOGGER.info(
                "Constants class registered for module %s: %s ",
                module_name_short,
                class_name,
            )

    MODULE_REGISTRY[module_name_short] = ModuleInfo(
        model=model, schema=schema, constants_classes=constants_classes
    )
