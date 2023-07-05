"""The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` module creates a
:class:`~virtual_rainforest.models.abiotic.abiotic_model.AbioticModel` class as a child
of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

from pint import Quantity

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER


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
    lower_bound_on_time_scale = "30 minutes"
    """Shortest time scale that soil model can sensibly capture."""
    upper_bound_on_time_scale = "1 day"
    """Longest time scale that soil model can sensibly capture."""
    required_init_vars = ()
    """Required initialisation variables for the abiotic model.

    This is a set of variables that must be present in the data object used to create an
    AbioticModel instance, along with any core axes that those variables must map on
    to."""
    vars_updated = []
    """Once this model is functional variables should be included here."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
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

        super().__init__(data, update_interval, **kwargs)
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

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> AbioticModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) virtual rainforest configuration.
            update_interval: Frequency with which all models are updated
        """

        soil_layers = config["abiotic"]["soil_layers"]
        canopy_layers = config["abiotic"]["canopy_layers"]

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(data, update_interval, soil_layers, canopy_layers)

    def setup(self) -> None:
        """Function to set up the abiotic model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self, time_index: int) -> None:
        """Placeholder function to update the abiotic model.

        Args:
            time_index: The index representing the current time step in the data object.
        """

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
