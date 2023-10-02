"""The :mod:`~virtual_rainforest.core.constants` module is used to store constants that
are used across the Virtual Rainforest. This includes universal constants, such as the
strength of gravity, but also model constants that are shared between multiple models,
such as the depth of the biogeochemically active soil layer.

At the moment, no constants are actually stored in this module. It currently only
contains the :attr:`CONSTANTS_REGISTRY`, which all model constants classes should be
registered in. This allows for all model constants to be documented neatly.
"""  # noqa: D205, D415

import dataclasses
from typing import Any

from virtual_rainforest.core.config import Config
from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.registry import MODULE_REGISTRY


def check_valid_constant_names(constants_config: dict, constants_class: Any) -> None:
    """Check that the constant names given in the config are valid.

    This checks that the constants are expected for the specific dataclass that they are
    assigned to, if not an error is raised.

    Args:
        constants_config: A dictionary of configuration details for this constants class
        constants_class: The constants dataclass to validate the details against.

    Raises:
        ConfigurationError: If unexpected constant names are used
    """

    # Extract a set of provided constant names
    provided_names = set(constants_config.keys())

    # Get a set of valid names
    valid_names = {fld.name for fld in dataclasses.fields(constants_class)}

    # Check for unexpected names
    unexpected_names = provided_names.difference(valid_names)
    if unexpected_names:
        LOGGER.error(
            "Unknown names supplied for %s: %s"
            % (constants_class.__name__, ", ".join(unexpected_names))
        )
        LOGGER.info("Valid names are as follows: %s" % (", ".join(valid_names)))
        raise ConfigurationError()

    return


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

    # Check if the configuration supplies validly named values to use with the constants
    # class, otherwise return an instance with defalt values.
    if (
        model_name in config
        and "constants" in config[model_name]
        and class_name in config[model_name]["constants"]
    ):
        # Checks that constants in config are as expected
        constants_config = config[model_name]["constants"][class_name]
        check_valid_constant_names(
            constants_config=constants_config, constants_class=constants_class
        )
        # If an error isn't raised then generate the dataclass
        return constants_class(**constants_config)

    # If no constants are supplied then the defaults should be used
    return constants_class()
