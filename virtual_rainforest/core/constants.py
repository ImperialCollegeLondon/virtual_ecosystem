"""The :mod:`~virtual_rainforest.core.constants` module is used to store constants that
are used across the Virtual Rainforest. This includes universal constants, such as the
strength of gravity, but also model constants that are shared between multiple models,
such as the depth of the biogeochemically active soil layer.

At the moment, no constants are actually stored in this module. It currently only
contains the :attr:`CONSTANTS_REGISTRY`, which all model constants classes should be
registered in. This allows for all model constants to be documented neatly.
"""  # noqa: D205, D415

import dataclasses
from importlib import import_module
from typing import Any, Callable

from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER

CONSTANTS_REGISTRY: dict[str, dict[str, Callable]] = {}
"""A registry for all the model constants data classes.

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


def check_valid_constant_names(
    config: dict[str, Any], model_name: str, class_name: str
) -> None:
    """Check that the constant names given in the config are valid.

    This checks that the constants are expected for the specific dataclass that they are
    assigned to, if not an error is raised.

    Args:
        config: The full virtual rainforest config
        model_name: Name of the model the constants belong to
        class_name: Name of the specific dataclass the constants belong to

    Raises:
        ConfigurationError: If unexpected constant names are used
    """

    # Extract dataclass of interest from registry
    constants_class = CONSTANTS_REGISTRY[model_name][class_name]

    # Extract a set of provided constant names
    provided_names = set(config[model_name]["constants"][class_name].keys())

    # Get a set of valid names
    valid_names = {fld.name for fld in dataclasses.fields(constants_class)}

    # Check for unexpected names
    unexpected_names = provided_names.difference(valid_names)
    if unexpected_names:
        LOGGER.error(
            "Unknown names supplied for %s: %s"
            % (class_name, ", ".join(unexpected_names))
        )
        LOGGER.info("Valid names are as follows: %s" % (", ".join(valid_names)))
        raise ConfigurationError()

    return


def load_constants(config: dict[str, Any], model_name: str, class_name: str) -> Any:
    """Load the specified constants class.

    Any constants that are supplied for this class in the config are used to populate
    the class, for all other constants default values are used.

    Args:
        config: The full virtual rainforest config
        model_name: Name of the model the constants belong to
        class_name: Name of the specific dataclass the constants belong to

    Returns:
        A constants class populated using the information provided in the config
    """

    # Extract dataclass of interest from registry
    constants_class = CONSTANTS_REGISTRY[model_name][class_name]

    # Check if any constants have been supplied
    if model_name in config and "constants" in config[model_name]:
        # Checks that constants in config are as expected
        check_valid_constant_names(config, model_name, class_name)
        # If an error isn't raised then generate the dataclass
        constants = constants_class(**config[model_name]["constants"][class_name])
    else:
        # If no constants are supplied then the defaults should be used
        constants = constants_class()

    return constants
