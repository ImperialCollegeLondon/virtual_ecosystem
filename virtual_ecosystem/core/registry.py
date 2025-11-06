"""The :mod:`~virtual_ecosystem.core.registry` module is used to populate the
:data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY`.

The registry is a dictionary, keyed using the short names of models, such as ``core`` or
``plants``. Each entry provides a :class:`~virtual_ecosystem.core.registry.ModuleInfo`
dataclass, which provides the BaseModel subclass for each model and its configuration
model. The ``core`` model has a configuration model but has no BaseModel subclass.

The module also provides the :func:`~virtual_ecosystem.core.registry.register_module`
function, which is used to populate the registry with the components of a given module.
"""  # noqa: D205

from dataclasses import dataclass
from importlib import import_module
from inspect import getmembers, isclass
from typing import Any

from virtual_ecosystem.core.configuration import Configuration
from virtual_ecosystem.core.logger import LOGGER


@dataclass
class ModuleInfo:
    """Dataclass for module information.

    This dataclass holds references to BaseModel subclass and configuration class for a
    model and is used to hold that information with  the
    data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY`. Note that the
    :mod:`virtual_ecosystem.core` module does not have an associated BaseModel subclass
    and the ``model`` attribute for the ``core`` module will be None.
    """

    # FIXME The typing below for model should be `None | type[BaseModel]`, but this is
    # circular. When core.base_model is imported, that imports core.config.Config, which
    # imports core.registry, which would then need to import core.base_model to use this
    # type. Not sure how to break out of this one, so for the moment, leaving as Any.

    model: Any
    """The BaseModel subclass associated with the module."""
    config: type[Configuration]
    """A Configuration subclass that provides a pydantic model to populate and validate
    the model configuration."""
    is_core: bool
    """Logical flag indicating if an instance contains registration information for the
    core module."""


MODULE_REGISTRY: dict[str, ModuleInfo] = {}
"""The global module registry.

As each module is registered using
:func:`~virtual_ecosystem.core.registry.register_module`, a
:class:`~virtual_ecosystem.core.registry.ModuleInfo` dataclass will be added to this
registry using the short name of the module being registered.
"""


def register_module(module_name: str) -> None:
    """Register module components.

    This function loads the main :func:`~virtual_ecosystem.core.base_model.BaseModel`
    subclass for a module and the root configuration object for a module. It then adds a
    :class:`~virtual_ecosystem.core.registry.ModuleInfo` dataclass instance to the
    :data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY` containing references to
    those classes. The :mod:`~virtual_ecosystem.core` module does not have an associated
    module.

    This function is primarily used within the
    :meth:`~virtual_ecosystem.core.config_builder.generate_configuration` method to
    register the components required to validate and setup the model configuration for a
    particular simulation.

    Args:
        module_name: The full name of the module to be registered (e.g.
            'virtual_ecosystem.model.animal').

    Raises:
        RuntimeError: if the requested module cannot be found or where a module does not
            provide a single subclass of the
            :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
        Exception: other exceptions can occur when loading the JSON schema fails.
    """

    # Extract the last component of the module name to act as unique short name
    module_name_short = module_name.rpartition(".")[-1]

    if module_name_short in MODULE_REGISTRY:
        LOGGER.warning(f"Module already registered: {module_name}")
        return

    LOGGER.info(f"Registering module: {module_name}")
    if module_name_short == "core":
        is_core = True
        model = None
    else:
        is_core = False
        model = get_model(module_name, module_name_short)

    # Find and register the model configuration
    model_config_class = get_model_configuration_class(
        module_name=module_name, module_name_short=module_name_short
    )

    LOGGER.info("Configuration class registered for %s", module_name)

    MODULE_REGISTRY[module_name_short] = ModuleInfo(
        model=model,
        config=model_config_class,
        is_core=is_core,
    )


def get_model(module_name: str, module_name_short: str):
    """Get the model class for a model.

    Discovery is by looking for a single BaseModel subclass within a submodule with a
    name matching the the model short name plus '_model'.

    * ``models.plants`` -> ``models.plants.plants_model.py``,

    Args:
        module_name: The full module name (e.g. ``virtual_ecosystem.models.plants``)
        module_name_short: The short module name (e.g ``plants``)
    """

    from virtual_ecosystem.core.base_model import BaseModel

    # Try and import the module from the name to get a reference to the module
    try:
        module = import_module(module_name + f".{module_name_short}_model")
    except ModuleNotFoundError as excep:
        LOGGER.critical(f"Unknown module - registration failed: {module_name}")
        raise excep

    # Locate _one_ BaseModel subclass in the module that is not the imported
    # BaseModelABC.
    models_found = [
        (obj_name, obj)
        for obj_name, obj in getmembers(module)
        if isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel
    ]

    # Trap missing and multiple models
    if len(models_found) == 0:
        msg = f"Model object not found in {module_name}"
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    if len(models_found) > 1:
        msg = f"More than one model defined in in {module_name}"
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    # Trap models that do not follow the requirement that the BaseModel.model_name
    # attribute matches the virtual_ecosystem.models.model_name
    # TODO - can we retire the model_name attribute if it just duplicates the module
    #        name or force it to match programmatically.
    _, model = models_found[0]
    if module_name_short != model.model_name:
        msg = f"Different model_name attribute and module name {module_name}"
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    # Register the resulting single model class
    LOGGER.info(f"Registering model class for {module_name}: {model.__name__}")

    return model


def get_model_configuration_class(module_name: str, module_name_short: str):
    """Get the root configuration class for a model.

    Discovery is name based, with the function attempting to retrieve a class based on
    the model short name:

    * ``plants`` -> ``PlantsConfiguration``,
    * ``abiotic_simple`` -> ``AbioticSimpleConfiguration``

    .. TODO:

        It would probably be cleaner and more flexible to use explicit setting of the
        configuration model name as a class attribute on the model definition, but that
        requires more changes in the BaseModel and definitions, so use this string
        pattern is being used to keep the rollout of the new config system simpler.

    Args:
        module_name: The full module name (e.g. ``virtual_ecosystem.models.plants``)
        module_name_short: The short module name (e.g ``plants``)
    """

    try:
        # Raise ModuleNotFound if the configuration module is missing
        config_submodule = import_module(f"{module_name}.model_config")
        # Raises Attribute error if the expected name is not found.
        expected_config_class_name = (
            "".join(word.capitalize() for word in module_name_short.split("_"))
            + "Configuration"
        )
        model_config_class = getattr(config_submodule, expected_config_class_name)
        # Raises a runtime error if the retrieved class is not a Configuration.
        if not issubclass(model_config_class, Configuration):
            raise RuntimeError
    except ModuleNotFoundError:
        raise RuntimeError(
            f"Model {module_name} does not provide a model_config submodule."
        )
    except AttributeError:
        raise RuntimeError(
            f"The {module_name}.model_config module does "
            f"not contain {expected_config_class_name}"
        )
    except RuntimeError:
        raise RuntimeError(
            f"Model {module_name} config class does does inherit from `ConfigRoot`."
        )

    return model_config_class
