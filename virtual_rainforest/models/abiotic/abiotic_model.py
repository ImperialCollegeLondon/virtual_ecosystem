"""The :mod:`abiotic.model` module creates a
:class:`~virtual_rainforest.abiotic.abiotic_model.AbioticModel` class as a child of the
:class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import BaseModel, InitialisationError
from virtual_rainforest.core.logger import LOGGER


class AbioticModel(BaseModel):
    """A class describing the abiotic model.

    Describes the specific functions and attributes that the abiotic module should
    possess. It's very much incomplete at the moment, and only overwrites one function
    in a pretty basic manner. This is intended as a demonstration of how the class
    inheritance should be handled for the model classes.

    Args:
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
    """

    model_name = "abiotic"

    def __init__(
        self,
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

        super().__init__(update_interval, start_time, **kwargs)
        self.soil_layers = int(soil_layers)
        self.canopy_layers = int(canopy_layers)
        # Save variables names to be used by the __repr__
        self._repr.append("soil_layers")
        self._repr.append("canopy_layers")

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> AbioticModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            config: The complete (and validated) virtual rainforest configuration.

        Raises:
            InitialisationError: If configuration data can't be properly converted
        """

        # Assume input is valid until we learn otherwise
        valid_input = True
        try:
            raw_interval = pint.Quantity(config["abiotic"]["model_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")
            start_time = datetime64(config["core"]["timing"]["start_time"])
            soil_layers = config["abiotic"]["soil_layers"]
            canopy_layers = config["abiotic"]["canopy_layers"]
        except (
            ValueError,
            pint.errors.DimensionalityError,
            pint.errors.UndefinedUnitError,
        ) as e:
            valid_input = False
            LOGGER.error(
                "Configuration types appear not to have been properly validated. This "
                "problem prevents initialisation of the abiotic model. The first "
                "instance of this problem is as follows: %s" % str(e)
            )

        if valid_input:
            LOGGER.info(
                "Information required to initialise the abiotic model successfully "
                "extracted."
            )
            return cls(update_interval, start_time, soil_layers, canopy_layers)
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
