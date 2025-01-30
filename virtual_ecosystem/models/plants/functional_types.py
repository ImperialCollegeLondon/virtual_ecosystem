"""Initial definition of plant functional type classes.

These are likely to become part of pyrealm.
"""

from __future__ import annotations

from pyrealm.demography.flora import Flora as pyrealmFlora

from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


def get_flora_from_config(config: Config) -> pyrealmFlora:
    """Generate a Flora object from a Virtual Ecosystem configuration.

    Args:
        config: A validated Virtual Ecosystem model configuration object.

    Returns:
        A populated :class:`pyrealm.demography.flora.Flora` instance
    """

    if "plants" not in config:
        msg = "Model configuration for plants model not found."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # Check for duplicate definition options - this should be prevented by the schema
    # definition setting oneOf the following two is required
    if (
        "pft_definition" in config["plants"]
        and "pft_definitions_path" in config["plants"]
    ):
        msg = "Do not use both `pft_definitions_path` and `pft_definition` in config."
        LOGGER.critical(msg)
        raise ConfigurationError(msg)

    # If the data is provided in the configuration, load that
    if "pft_definition" in config["plants"]:
        # TODO: currently need to rename this property to match internal expectation in
        # pyrealm, change here if this is fixed/aligned.
        pft_data = {"pft": config["plants"]["pft_definition"]}
        return pyrealmFlora._from_file_data(pft_data)

    return pyrealmFlora.from_csv(config["plants"]["pft_definitions_path"])
