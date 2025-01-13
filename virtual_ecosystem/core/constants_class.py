"""The :mod:`~virtual_ecosystem.core.constants_class` module provides the abstract base
class :mod:`~virtual_ecosystem.core.constants_class.ConstantsDataclass` and the
:mod:`~virtual_ecosystem.core.constants_class.ConstantsDataclass.from_config` method to
generate instances using a dictionary to override default constant values.

The main use of the base class is to unambiguously identify dataclasses within the core
and models as providing constants for use within models. To create a constants class for
use in a model:

1. Create a `constants.py` submodule within the model.
2. Import the :mod:`~virtual_ecosystem.core.constants_class.ConstantsDataclass` base
   class.
3. Define a new frozen dataclass as a subclass of the base class and populate the
   dataclass with the required constant values. See
   :mod:`~virtual_ecosystem.core.constants_class.ConstantsDataclass` for syntax
   details.
"""  # noqa: D205

from __future__ import annotations

from abc import ABC
from dataclasses import (  # type: ignore [attr-defined]
    _FIELD_CLASSVAR,
    dataclass,
    fields,
)
from typing import Any

from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


@dataclass(frozen=True)
class ConstantsDataclass(ABC):
    """The constants dataclass abstract base class.

    This abstract base class provides a template for all constants dataclasses in
    models. This allows constants classes to be identified from a common class. Within
    the definition of subclasses, variables can either be defined as instance variables,
    which can be configured by the user, or class variables, which cannot. This is
    useful to prevent accidental modification of truly universal constants.

    .. code-block:: python

        @dataclass(frozen=True)
        class ExampleConsts(ConstantsDataclass):

            cannot_be_changed: ClassVar[float] = 1.0
            can_be_configured: float = 2.0
    """

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ConstantsDataclass:
        """Create a constants dataclass instance from a configuration dictionary.

        This method accepts a configuration dictionary and validates the provided keys
        against the dataclass fields of the subclass. If all the keys are valid, it
        returns a new constants instance, overriding default values with any
        provided values in the dictionary.

        Raises:
            ConfigurationError: where the keys in the configuration dictionary do not
                match the subclass fields or the configuration attempts to set
                non-configurable universal constants.
        """

        # Extract a set of provided constant names
        provided_names = set(config.keys())

        # Get a set of valid names and also any class vars
        valid_names = {fld.name for fld in fields(cls)}
        classvar_names = {
            ky
            for ky, val in cls.__dataclass_fields__.items()
            if val._field_type == _FIELD_CLASSVAR  # type: ignore [attr-defined]
        }

        # Check for unexpected names
        unexpected_names = provided_names.difference(valid_names)
        unconfigurable_names = unexpected_names.intersection(classvar_names)

        if unconfigurable_names:
            msg = (
                f"Constant in {cls.__name__} "
                f"not configurable: {', '.join(unconfigurable_names)}"
            )
            LOGGER.error(msg)
            LOGGER.info("Valid names are: {}".format(", ".join(valid_names)))
            raise ConfigurationError(msg)

        if unexpected_names:
            msg = (
                "Unknown names supplied "
                f"for {cls.__name__}: {', '.join(unexpected_names)}"
            )
            LOGGER.error(msg)
            LOGGER.info("Valid names are: {}".format(", ".join(valid_names)))
            raise ConfigurationError(msg)

        return cls(**config)
