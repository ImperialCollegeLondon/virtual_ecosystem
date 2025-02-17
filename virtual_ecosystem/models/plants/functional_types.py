"""The :mod:`~virtual_ecosystem.models.plants.functional_types` submodule provides
functionality to load plant functional type definitions from the model configuration and
generate a :class:`~pyrealm.demography.flora.Flora` object for use in simulation.
"""  # noqa: D205

from __future__ import annotations

from pyrealm.demography.flora import Flora

from virtual_ecosystem.core.config import Config, ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


def get_flora_from_config(config: Config) -> Flora:
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
        return Flora._from_file_data(pft_data)

    return Flora.from_csv(config["plants"]["pft_definitions_path"])
