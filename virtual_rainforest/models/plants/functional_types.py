"""Initial definition of plant functional type classes.

These are likely to become part of pyrealm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from virtual_rainforest.core.config import ConfigurationError
from virtual_rainforest.core.logger import LOGGER


@dataclass(frozen=True)
class PlantFunctionalType:
    """Data class containing plant functional type definitions."""

    pft_name: str
    max_height: float


class PlantFunctionalTypes(dict):
    """Dictionary of plant functional types."""

    def __init__(self, pfts: dict[str, PlantFunctionalType]) -> None:
        for name, pft in pfts.items():
            self[name] = pft

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PlantFunctionalTypes:
        """Factory method to generate PlantFunctionalTypes from a configuration."""

        pft_dict: dict = {}

        # TODO alternative config option to load from CSV

        if "plants" in config and "ftypes" in config["plants"]:
            for ftype in config["plants"]["ftypes"]:
                try:
                    pft_dict[ftype["pft_name"]] = PlantFunctionalType(**ftype)
                except Exception as excep:
                    LOGGER.critical(
                        f"Error generating plant functional type: {str(excep)}"
                    )
                    raise
        else:
            msg = "Missing plant functional type definitions in plant model config."
            LOGGER.critical(msg)
            raise ConfigurationError(msg)

        return cls(pft_dict)
