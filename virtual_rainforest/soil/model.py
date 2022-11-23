"""API documentation for the :mod:`soil.model` module.
************************************************** # noqa: D205

The :mod:`soil.model` module creates a :class:`~virtual_rainforest.soil.model.SoilModel`
class as a child of the :class:`~virtual_rainforest.core.model.BaseModel` class. At
present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.model.BaseModel.setup` and
:func:`~virtual_rainforest.core.model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the
:mod:`virtual_rainforest` model develops. The factory method
:func:`~virtual_rainforest.soil.model.SoilModel.from_config` exists in a more complete
state, and unpacks a small number of parameters from our currently pretty minimal
configuration dictionary. These parameters are then used to generate a class instance.
If errors crop here when converting the information from the config dictionary to the
required types (e.g. :class:`~numpy.timedelta64`) they are caught and then logged, and
at the end of the unpacking an error is thrown. This error should be caught and handled
by downstream functions so that all model configuration failures can be reported as one.
"""

from __future__ import annotations

from typing import Any

import pint
from numpy import timedelta64

from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.model import BaseModel, InitialisationError


class SoilModel(BaseModel, model_name="soil"):
    """A class describing the soil model.

    Describes the specific functions and attributes that the soil module should possess.
    It's very much incomplete at the moment, and only overwrites one function in a
    pretty basic manner. This is intended as a demonstration of how the class
    inheritance should be handled for the model classes.

    Args:
        update_interval: Time to wait between updates of the model state.
        no_layers: The number of soil layers to be modelled.

    Attributes:
        name: Names the model that is described
    """

    name = "soil"

    def __init__(self, update_interval: timedelta64, no_layers: int, **kwargs: Any):

        if no_layers < 1:
            log_and_raise(
                "There has to be at least one soil layer in the soil model!",
                InitialisationError,
            )
        elif no_layers != int(no_layers):
            log_and_raise(
                "The number of soil layers must be an integer!", InitialisationError
            )

        super(SoilModel, self).__init__(update_interval, **kwargs)
        self.no_layers = int(no_layers)
        # Save variables names to be used by the __repr__
        self._repr.append("no_layers")

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> SoilModel:
        """Factory function to initialise the soil model from configuration.

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
            raw_interval = pint.Quantity(config["core"]["timing"]["min_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(raw_interval.magnitude), "m")
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
            return cls(update_interval, no_layers)
        else:
            raise InitialisationError()

    # THIS IS BASICALLY JUST A PLACEHOLDER TO DEMONSTRATE HOW THE FUNCTION OVERWRITING
    # SHOULD WORK
    # AT THIS STEP COMMUNICATION BETWEEN MODELS CAN OCCUR IN ORDER TO DEFINE INITIAL
    # STATE
    def setup(self) -> None:
        """Function to set up the soil model."""
        for layer in range(0, self.no_layers):
            LOGGER.info("Setting up soil layer %s" % layer)

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def solve(self) -> None:
        """Placeholder function to solve the soil model."""

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""
