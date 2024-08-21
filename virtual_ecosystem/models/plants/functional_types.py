"""Initial definition of plant functional type classes.

These are likely to become part of pyrealm.
"""

from __future__ import annotations

from dataclasses import dataclass

from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


@dataclass(frozen=True)
class PlantFunctionalType:
    """Data class containing plant functional type definitions."""

    pft_name: str
    """The name of the plant functional type."""
    max_height: float
    """The maximum stem height of the plant functional type."""


class Flora(dict):
    """Defines the flora used in a ``virtual_ecosystem`` model.

    The flora is the set of plant functional types used within a particular simulation
    and this class provides dictionary-like access to a defined set of
    :class:`~virtual_ecosystem.models.plants.functional_types.PlantFunctionalType`
    instances.

    Instances of this class should not be altered during model fitting, at least until
    the point where plant evolution is included in the modelling process.

    Args:
        pfts: A list of ``PlantFunctionalType`` instances, which must not have
            duplicated
            :attr:`~virtual_ecosystem.models.plants.functional_types.PlantFunctionalType.pft_name`
            attributes.
    """

    def __init__(self, pfts: list[PlantFunctionalType]) -> None:
        # Get the names and check there are no duplicates
        pft_names = [p.pft_name for p in pfts]
        if len(pft_names) != len(set(pft_names)):
            msg = "Duplicated plant functional type names in creating Flora instance."
            LOGGER.critical(msg)
            raise ValueError(msg)

        for name, pft in zip(pft_names, pfts):
            self[name] = pft

    @classmethod
    def from_config(cls, config: Config) -> Flora:
        """Factory method to generate a Flora instance from a configuration.

        Args:
            config: A validated Virtual Ecosystem model configuration object.

        Returns:
            A populated Flora instance
        """

        # TODO alternative config option to load from CSV

        # Load the configuration, using a dict to keep track of duplicated PFT names
        # along the way.
        pft_dict: dict = {}

        if "plants" in config and "ftypes" in config["plants"]:
            for ftype in config["plants"]["ftypes"]:
                try:
                    pft = PlantFunctionalType(**ftype)
                    if pft.pft_name in pft_dict:
                        msg = f"Config duplicates plant functional type {pft.pft_name}."
                        LOGGER.critical(msg)
                        raise ConfigurationError(msg)
                    pft_dict[pft.pft_name] = pft
                except Exception as excep:
                    LOGGER.critical(
                        f"Error generating plant functional type: {excep!s}"
                    )
                    raise
        else:
            msg = "Missing plant functional type definitions in plant model config."
            LOGGER.critical(msg)
            raise ConfigurationError(msg)

        return cls(list(pft_dict.values()))
