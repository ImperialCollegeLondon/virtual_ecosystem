"""The :mod:`~virtual_rainforest.models.soil.soil_model` module creates a
:class:`~virtual_rainforest.models.soil.soil_model.SoilModel` class as a child of the
:class:`~virtual_rainforest.core.base_model.BaseModel` class. At present a lot of the
abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.setup` and
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.soil.soil_model.SoilModel.from_config` exists in a
more complete state, and unpacks a small number of parameters from our currently pretty
minimal configuration dictionary. These parameters are then used to generate a class
instance. If errors crop here when converting the information from the config dictionary
to the required types (e.g. :class:`~numpy.timedelta64`) they are caught and then
logged, and at the end of the unpacking an error is thrown. This error should be caught
and handled by downstream functions so that all model configuration failures can be
reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import BaseModel, InitialisationError
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER


class SoilModel(BaseModel):
    """A class describing the soil model.

    Describes the specific functions and attributes that the soil module should possess.
    It's very much incomplete at the moment, and only overwrites one function in a
    pretty basic manner. This is intended as a demonstration of how the class
    inheritance should be handled for the model classes.

    Args:
        data: The data object to be used in the model.
        start_time: A datetime64 value setting the start time of the model.
        update_interval: Time to wait between updates of the model state.
        no_layers: The number of soil layers to be modelled.
    """

    model_name = "soil"
    """An internal name used to register the model and schema"""
    required_init_vars = ()
    """Required initialisation variables for the soil model.

    This is a set of variables that must be present in the data object used to create a
    SoilModel , along with any core axes that those variables must map on
    to."""

    def __init__(
        self,
        data: Data,
        update_interval: timedelta64,
        start_time: datetime64,
        no_layers: int,
        **kwargs: Any,
    ):
        if no_layers < 1:
            to_raise = InitialisationError(
                "There has to be at least one soil layer in the soil model!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        if no_layers != int(no_layers):
            to_raise = InitialisationError(
                "The number of soil layers must be an integer!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        super().__init__(data, update_interval, start_time, **kwargs)
        self.no_layers = int(no_layers)
        """The number of soil layers to be modelled."""
        # Save variables names to be used by the __repr__
        self._repr.append("no_layers")

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.update_interval
        """The time interval between model updates."""
        self.next_update
        """The simulation time at which the model should next run the update method"""

    @classmethod
    def from_config(cls, data: Data, config: dict[str, Any]) -> SoilModel:
        """Factory function to initialise the soil model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.

        Raises:
            InitialisationError: If configuration data can't be properly converted
        """

        # Assume input is valid until we learn otherwise
        valid_input = True
        try:
            raw_interval = pint.Quantity(config["soil"]["model_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")
            start_time = datetime64(config["core"]["timing"]["start_time"])
            no_layers = config["soil"]["no_layers"]
        except (
            ValueError,
            pint.errors.DimensionalityError,
            pint.errors.UndefinedUnitError,
        ) as e:
            valid_input = False
            LOGGER.error(
                "Configuration types appear not to have been properly validated. This "
                "problem prevents initialisation of the soil model. The first instance"
                " of this problem is as follows: %s" % str(e)
            )

        if valid_input:
            LOGGER.info(
                "Information required to initialise the soil model successfully "
                "extracted."
            )
            return cls(data, update_interval, start_time, no_layers)
        else:
            raise InitialisationError()

    def setup(self) -> None:
        """Placeholder function to setup up the soil model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def update(self) -> None:
        """Placeholder function to update the soil model."""

        # Finally increment timing
        self.next_update += self.update_interval

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""
