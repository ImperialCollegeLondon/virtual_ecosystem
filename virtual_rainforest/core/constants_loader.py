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


def load_constants(config: Config, model_name: str, class_name: str) -> Any:
    """Load the specified constants class.

    Any constants that are supplied for this class in the config are used to populate
    the class, for all other constants default values are used.

    Args:
        config: A validated Virtual Rainforest model configuration object.
        model_name: Name of the model the constants belong to
        class_name: Name of the specific dataclass the constants belong to

    Returns:
        A constants class populated using the information provided in the config
    """

    # Extract dataclass of interest from registry
    try:
        constants_class = MODULE_REGISTRY[model_name].constants_classes[class_name]
    except KeyError as excep:
        LOGGER.critical(f"Unknown constants class: {model_name}.{class_name}")
        raise excep

    # Extract the constant class configuration if present
    constants_config = (
        config[model_name]["constants"][class_name]
        if "constants" in config[model_name]
        and class_name in config[model_name]["constants"]
        else {}
    )

    # Try and configure the constants class
    try:
        return constants_class.from_config(constants_config)
    except ConfigurationError:
        LOGGER.critical("Could not initialise {model_name}.{class_name} from config.")
        raise
