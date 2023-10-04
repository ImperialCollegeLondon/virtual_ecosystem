"""The :mod:`~virtual_rainforest.core.constants_class` module provides the abstract base
class :mod:`~virtual_rainforest.core.constants_class.ConstantsDataclass` and the
:mod:`~virtual_rainforest.core.constants_class.ConstantsDataclass.from_config` method to
generate instances using a dictionary to override default constant values.

The main use of the base class is to unambiguously identify dataclasses within the core
and models as providing constants for use within models. To create a constants class for
use in a model:

1. Create a `constants.py` submodule within the model.
2. Import the :mod:`~virtual_rainforest.core.constants_class.ConstantsDataclass` base
   class.
3. Declare a new frozen dataclass as a subclass of the base class and populate the
   dataclass with the required constant values.

.. code-block:: python
    from dataclasses import dataclass
    from virtual_rainforest.core.constants import ConstantsDataclass

    @dataclass(frozen=True)
    class NewConstantsClass(ConstantsDataclass):

        constant_one: float = 2.0
        constant_two: int = 6

"""  # noqa: D205, D415

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, fields
from typing import Any

from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER


@dataclass(frozen=True)
class ConstantsDataclass(ABC):
    """The constants dataclass abstract base class.

    This abstract base class provides a template for all constants dataclasses in
    models. This allows constants classes to be identified from a common class.
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
                match the subclass fields.
        """

        # Extract a set of provided constant names
        provided_names = set(config.keys())

        # Get a set of valid names
        valid_names = {fld.name for fld in fields(cls)}

        # Check for unexpected names
        unexpected_names = provided_names.difference(valid_names)
        if unexpected_names:
            msg = (
                "Unknown names supplied "
                f'for {cls.__name__}: {", ".join(unexpected_names)}'
            )
            LOGGER.error(msg)
            LOGGER.info("Valid names are as follows: %s" % (", ".join(valid_names)))
            raise ConfigurationError(msg)

        return cls(**config)
