"""The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` module creates a
:class:`~virtual_rainforest.models.abiotic.abiotic_model.AbioticModel` class as a child
of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import BaseModel, InitialisationError
from virtual_rainforest.core.config import ConfigurationError
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import extract_model_time_details


class AbioticModel(BaseModel):
    """A class describing the abiotic model.

    Describes the specific functions and attributes that the abiotic module should
    possess. It's very much incomplete at the moment, and only overwrites one function
    in a pretty basic manner. This is intended as a demonstration of how the class
    inheritance should be handled for the model classes.

    Args:
        data: The data object to be used in the model.
        start_time: A datetime64 value setting the start time of the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
    """

    model_name = "abiotic"
    """An internal name used to register the model and schema"""
    required_init_vars = ()
    """Required initialisation variables for the abiotic model.

    This is a set of variables that must be present in the data object used to create an
    AbioticModel instance, along with any core axes that those variables must map on
    to."""

    def __init__(
        self,
        data: Data,
        update_interval: timedelta64,
        start_time: datetime64,
        soil_layers: int,
        canopy_layers: int,
        **kwargs: Any,
    ):
        if soil_layers < 1:
            to_raise = InitialisationError(
                "There has to be at least one soil layer in the abiotic model!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        if soil_layers != int(soil_layers):
            to_raise = InitialisationError(
                "The number of soil layers must be an integer!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        if canopy_layers < 1:
            to_raise = InitialisationError(
                "There has to be at least one canopy layer in the abiotic model!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        if canopy_layers != int(canopy_layers):
            to_raise = InitialisationError(
                "The number of canopy layers must be an integer!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        super().__init__(data, update_interval, start_time, **kwargs)
        self.soil_layers = int(soil_layers)
        """The number of soil layers to be modelled."""
        self.canopy_layers = int(canopy_layers)
        """The initial number of canopy layers to be modelled."""

        # Save variables names to be used by the __repr__
        self._repr.append("soil_layers")
        self._repr.append("canopy_layers")

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.update_interval
        """The time interval between model updates."""
        self.next_update
        """The simulation time at which the model should next run the update method"""

    @classmethod
    def from_config(cls, data: Data, config: dict[str, Any]) -> AbioticModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) virtual rainforest configuration.

        Raises:
            InitialisationError: If configuration data can't be properly converted
        """

        # Assume input is valid until we learn otherwise
        valid_input = True
        try:
            start_time, update_interval = extract_model_time_details(
                config, cls.model_name
            )
        except ConfigurationError:
            valid_input = False

        soil_layers = config["abiotic"]["soil_layers"]
        canopy_layers = config["abiotic"]["canopy_layers"]

        if valid_input:
            LOGGER.info(
                "Information required to initialise the abiotic model successfully "
                "extracted."
            )
            return cls(data, update_interval, start_time, soil_layers, canopy_layers)
        else:
            raise InitialisationError()

    def setup(self) -> None:
        """Function to set up the abiotic model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self) -> None:
        """Placeholder function to update the abiotic model."""

        # Finally increment timing
        self.next_update += self.update_interval

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
