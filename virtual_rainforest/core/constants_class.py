"""A base constants dataclass."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, fields
from typing import Any

from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER


@dataclass(frozen=True)
class ConstantsDataclass(ABC):
    """XYZ."""

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ConstantsDataclass:
        """MNO."""

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
