"""The :mod:`~virtual_rainforest.core.constants` module is used to store constants that
are used across the Virtual Rainforest. This includes universal constants, such as the
strength of gravity, but also constants that are shared between multiple models, such as
the depth of the biogeochemically active soil layer.

At the moment, no constants are actually stored in this module. It currently only
contains the :attr:`CONSTANTS_REGISTRY`, which all constants classes should be
registered in across models. This allows for all constants to be documented neatly.
"""  # noqa: D205, D415

from importlib import import_module
from typing import Callable

from virtual_rainforest.core.logger import LOGGER

CONSTANTS_REGISTRY: dict[str, dict[str, Callable]] = {}
"""A registry for all the constants data classes.

:meta hide-value:
"""


def register_constants_class(model_name: str, class_name: str) -> None:
    """Simple function to add a constants class to the registry.

    Args:
        model_name: The name of the model that the constant class belongs to
        class_name: The name of the constants class

    Raises:
        ValueError: If the model and class name have already been used to register a
            constants class
    """

    if model_name in CONSTANTS_REGISTRY:
        if class_name in CONSTANTS_REGISTRY[model_name]:
            excep = ValueError(
                f"The constants class {model_name}.{class_name} is already registered"
            )
            LOGGER.critical(excep)
            raise excep
    else:
        # If model name is yet registered add it in as an empty dictionary
        CONSTANTS_REGISTRY[model_name] = {}

    try:
        # Import dataclass of interest
        import_path = f"virtual_rainforest.models.{model_name}.constants"
        consts_module = import_module(import_path)
        # Add data class to the constants registry
        CONSTANTS_REGISTRY[model_name][class_name] = getattr(consts_module, class_name)
    except Exception as excep:
        LOGGER.critical(
            "Registration for %s.%s constants class failed: check log",
            model_name,
            class_name,
        )
        raise excep

    LOGGER.info("Constants class %s.%s registered", model_name, class_name)
