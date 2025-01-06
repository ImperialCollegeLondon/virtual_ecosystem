"""The :mod:`~virtual_ecosystem.core.registry` module is used to populate the
:data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY`. This provides a dictionary
giving access to the key components (schema, constants classes and model) of Virtual
Ecosystem modules used in model setup and configuration. Those components are stored in
the dictionary as instances of the :class:`~virtual_ecosystem.core.registry.ModuleInfo`
dataclass, which has ``schema``, ``model`` and ``constant_classes`` attributes. The
dictionary is keyed by either the model name or ``core``, which provides details on the
core schema and constants, but does not provide a model object.

The module also provides the :func:`~virtual_ecosystem.core.registry.register_module`
function, which is used to populate the registry with the components of a given module.
"""  # noqa: D205

from dataclasses import dataclass
from importlib import import_module, resources
from inspect import getmembers, isclass
from typing import Any

from virtual_ecosystem.core.constants_class import ConstantsDataclass
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.core.schema import load_schema


@dataclass
class ModuleInfo:
    """Dataclass for module information.

    This dataclass is used to hold the core components of individual modules within the
    :data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY`. Each class attribute
    contains one of the core components of ``schema``, ``model`` and
    ``constant_classes``.

    Note that the  :mod:`virtual_ecosystem.core` module does not have an associated
    BaseModel subclass and the ``model`` attribute for the ``core`` module will be None.
    """

    # FIXME The typing below for model should be `None | type[BaseModel]`, but this is
    # circular. When core.base_model is imported, that imports core.config.Config, which
    # imports core.registry, which would then need to import core.base_model to use this
    # type. Not sure how to break out of this one, so for the moment, leaving as Any.

    model: Any
    """The BaseModel subclass associated with the module."""
    schema: dict[str, Any]
    """The module JSON schema as a dictionary, used to validate configuration data for
    running a simulation."""
    constants_classes: dict[str, type[ConstantsDataclass]]
    """A dictionary of module constants classes. The individual ConstantsDataclass
    objects are keyed by their name."""
    is_core: bool
    """Logical flag indicating if an instance contains registration information for the
    core module."""


MODULE_REGISTRY: dict[str, ModuleInfo] = {}
"""The global module registry.

As each module is registered using
:func:`~virtual_ecosystem.core.registry.register_module`, a
:class:`~virtual_ecosystem.core.registry.ModuleInfo` dataclass will be added to this
registry using the stem name of the module being registered.
"""


def register_module(module_name: str) -> None:
    """Register module components.

    This function loads the module schema, any constants classes and the main
    :func:`~virtual_ecosystem.core.base_model.BaseModel` subclass for a module and then
    adds a :class:`~virtual_ecosystem.core.registry.ModuleInfo` dataclass instance to
    the :data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY` containing those
    details. The :mod:`~virtual_ecosystem.core` module does not have an associated
    module.

    This function is primarily used within the
    :meth:`~virtual_ecosystem.core.config.Config.build_schema` method to register the
    components required to validate and setup the model configuration for a particular
    simulation.

    Args:
        module_name: The full name of the module to be registered (e.g.
            'virtual_ecosystem.model.animal').

    Raises:
        RuntimeError: if the requested module cannot be found or where a module does not
            provide a single subclass of the
            :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
        Exception: other exceptions can occur when loading the JSON schema fails.
    """

    from virtual_ecosystem.core.base_model import BaseModel

    # Extract the last component of the module name to act as unique short name
    _, _, module_name_short = module_name.rpartition(".")

    if module_name_short in MODULE_REGISTRY:
        LOGGER.warning(f"Module already registered: {module_name}")
        return

    # Try and import the module from the name to get a reference to the module
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as excep:
        LOGGER.critical(f"Unknown module - registration failed: {module_name}")
        raise excep

    is_core = module_name == "virtual_ecosystem.core"

    LOGGER.info(f"Registering module: {module_name}")

    # Locate _one_ BaseModel class in the module root if this is not the core.
    if is_core:
        model = None
    else:
        models_found = [
            (obj_name, obj)
            for obj_name, obj in getmembers(module)
            if isclass(obj) and issubclass(obj, BaseModel)
        ]

        # Trap missing and multiple models
        if len(models_found) == 0:
            msg = f"Model object not found in {module_name}"
            LOGGER.critical(msg)
            raise RuntimeError(msg)

        if len(models_found) > 1:
            msg = "More than one model defined in in {module_name}"
            LOGGER.critical(msg)
            raise RuntimeError(msg)

        # Trap models that do not follow the requirement that the BaseModel.model_name
        # attribute matches the virtual_ecosystem.models.model_name
        # TODO - can we retire the model_name attribute if it just duplicates the module
        #        name or force it to match programatically.
        _, model = models_found[0]
        if module_name_short != model.model_name:
            msg = f"Different model_name attribute and module name {module_name}"
            LOGGER.critical(msg)
            raise RuntimeError(msg)

        # Register the resulting single model class
        LOGGER.info(f"Registering model class for {module_name}: {model.__name__}")

    # Register the schema
    with resources.as_file(
        resources.files(module) / "module_schema.json"
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

    LOGGER.info("Schema registered for %s: %s ", module_name, schema_file_path)

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
            if isclass(class_obj)
            and issubclass(class_obj, ConstantsDataclass)
            and class_obj is not ConstantsDataclass
        }

        for class_name in constants_classes.keys():
            LOGGER.info(
                "Constants class registered for %s: %s ",
                module_name,
                class_name,
            )

    MODULE_REGISTRY[module_name_short] = ModuleInfo(
        model=model, schema=schema, constants_classes=constants_classes, is_core=is_core
    )
