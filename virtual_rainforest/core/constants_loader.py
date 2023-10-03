"""The :mod:`~virtual_rainforest.core.constants` module is used to store constants that
are used across the Virtual Rainforest. This includes universal constants, such as the
strength of gravity, but also model constants that are shared between multiple models,
such as the depth of the biogeochemically active soil layer.

At the moment, no constants are actually stored in this module. It currently only
contains the :attr:`CONSTANTS_REGISTRY`, which all model constants classes should be
registered in. This allows for all model constants to be documented neatly.
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
        constants_class = MODULE_REGISTRY[model_name]["constants"][class_name]
    except KeyError as excep:
        LOGGER.critical(f"Unknown constants class: {model_name}.{class_name}")
        raise excep

    # If the configuration supplies a section for this constant class, use the
    # ConstantsDataclass.from_config method to check that the arguments are valid for
    # the specific dataclass, otherwise return the default.
    try:
        constants_config = config[model_name]["constants"][class_name]
        return constants_class.from_config(constants_config)
    except (KeyError, IndexError):
        # No constants_config section, so return default instance.
        return constants_class()
    except ConfigurationError:
        # The from_config call failed, so log and exit.
        LOGGER.critical("Could not initialise {model_name}.{class_name} from config.")
        raise
