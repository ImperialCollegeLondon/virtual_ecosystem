"""The :mod:`~virtual_rainforest.core.registry` module is used to populate the
:data:`~virtual_rainforest.core.registry.MODULE_REGISTRY`. This provides a dictionary
giving access to the core components of Virtual Rainforest modules used in model setup
and configuration. The dictionary is keyed by the model name and the special ``core``
case. The values in the dictionary are instances of the
:class:`~virtual_rainforest.core.registry.ModuleInfo` dataclass, which has ``schema``,
``model`` and ``constant_classes`` attributes.

The module also provides the :func:`~virtual_rainforest.core.registry.register_module`
function, which is used to populate the registry with the components of a given module.
This function should be called in the ``__init__.py`` file for all models, which ensures
that the model components are registered when the module is imported.

.. code-block:: python

    from virtual_rainforest.core.registry import register_module
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    register_module(module_name=__name__, model=AnimalModel)

"""  # noqa: D205, D415


import sys
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

    This dataclass is used to hold the core components of individual modules within the
    :data:`~virtual_rainforest.core.registry.MODULE_REGISTRY`. Each class attribute
    contains one of the core components of ``schema``, ``model`` and
    ``constant_classes``.

    Note that the  :mod:`virtual_rainforest.core` module does not have an associated
    BaseModel subclass and the ``model`` attribute for the ``core`` module will be None.
    """

    model: Any  # FIXME Optional[type[BaseModel]]
    """The BaseModel subclass associated with the module."""
    schema: dict[str, Any]
    """The module JSON schema as a dictionary, used to validate configuration data for
    running a simulation."""
    constants_classes: dict[str, ConstantsDataclass]
    """A dictionary of module constants classes. The individual ConstantsDataclass
    objects are keyed by their name."""


MODULE_REGISTRY: dict[str, ModuleInfo] = {}
"""The global module registry.

As each module is registered using
:func:`~virtual_rainforest.core.registry.register_module`, a
:class:`~virtual_rainforest.core.registry.ModuleInfo` dataclass will be added to this
registry using the stem name of the module being registered.
"""


def register_module(module_name: str, model: Any = None) -> None:
    """Register module components.

    This function loads the module schema, any constants classes and the main
    :func:`~virtual_rainforest.core.base_model.BaseModel` subclass for a module and then
    adds a :class:`~virtual_rainforest.core.registry.ModuleInfo` dataclass instance to
    the :data:`~virtual_rainforest.core.registry.MODULE_REGISTRY` containing those
    details. The :mod:`~virtual_rainforest.core` module does not have an associated
    module and it is an error to register that module with a model. Similarly,
    :mod:`~virtual_rainforest.models` modules must provide a model and it is an error to
    register a module without one.

    This function is intended to always be be called to register a module from within
    the ``__init__.py`` for that module. It expects to be able to use
    :data:`sys.modules` to access the module object which, when called from within the
    context of ``__init__.py``, will have been added to :data:`sys.modules`.

    To register a module outside of the context of the module `__init__.py`, for example
    for testing purposes, that module must first be explicitly imported to make it
    accessible from :data:`sys.modules`.

    Args:
        module_name: The name of the module containing the model to be registered
        model: The model to be associated with the module, if any.

    Raises:
        RuntimeError: the core module is registered with a model, a model module is
            registered without a module, or the module cannot be found in
            :data:`sys.modules`.
        Exception: loading the JSON schema fails.
    """

    # Extract the last component of the module name to act as unique short name
    _, _, module_name_short = module_name.rpartition(".")

    if module_name_short in MODULE_REGISTRY:
        LOGGER.warning(f"Module already registered: {module_name_short}")
        return

    try:
        module = sys.modules[module_name]
    except KeyError:
        msg = f"Module not found in sys.modules - registration failed: {module_name}"
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    is_core = module_name == "virtual_rainforest.core"

    LOGGER.info(f"Registering {module_name} module components")

    # Check on the model argument.
    if is_core and model:
        msg = "No model should be registered for the core module"
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    if not is_core and model is None:
        msg = "A model class is required to register model modules"
        LOGGER.critical(msg)
        raise RuntimeError(msg)

    if model:
        if module_name_short != model.model_name:
            msg = f"Different model_name attribute and module name {module_name}"
            LOGGER.critical(msg)
            raise RuntimeError(msg)

        # Register the resulting single model class
        LOGGER.info(
            f"Registering model class for {module_name_short} model: {model.__name__}"
        )

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
