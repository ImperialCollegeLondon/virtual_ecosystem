"""The :mod:`~virtual_rainforest.core.constants_loader` module  provides the function
:mod:`~virtual_rainforest.core.constants_loader.load_constants`. This is a utility
function that retrieves a constants dataclass from the
:data:`~virtual_rainforest.core.registry.MODULE_REGISTRY` and then extracts any
configuration details for that constants dataclass from a
:mod:`~virtual_rainforest.core.config.Config` instance.
"""  # noqa: D205, D415

from typing import Any

from virtual_rainforest.core.config import Config
from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.registry import MODULE_REGISTRY


def load_constants(config: Config, module_name: str, class_name: str) -> Any:
    """Load the specified constants class.

    Any constants that are supplied for this class in the config are used to populate
    the class, for all other constants default values are used.

    Args:
        config: A validated Virtual Rainforest model configuration object.
        module_name: Name of the module that the constants belong to
        class_name: Name of the specific dataclass the constants belong to

    Returns:
        A constants class populated using the information provided in the config
    """

    # Extract dataclass of interest from registry
    if module_name not in MODULE_REGISTRY:
        msg = f"Unknown or unregistered module in: {module_name}.{class_name}"
        LOGGER.critical(msg)
        raise KeyError(msg)

    if class_name not in MODULE_REGISTRY[module_name].constants_classes:
        msg = f"Unknown constants class: {module_name}.{class_name}"
        LOGGER.critical(msg)
        raise KeyError(msg)

    # Get the class and extract the constant class configuration if present
    constants_class = MODULE_REGISTRY[module_name].constants_classes[class_name]
    constants_config = (
        config[module_name]["constants"][class_name]
        if "constants" in config[module_name]
        and class_name in config[module_name]["constants"]
        else {}
    )

    # Try and configure the constants class
    try:
        class_instance = constants_class.from_config(constants_config)
    except ConfigurationError:
        LOGGER.critical(f"Could not initialise {module_name}.{class_name} from config")
        raise

    LOGGER.info(f"Initialised {module_name}.{class_name} from config")
    return class_instance
