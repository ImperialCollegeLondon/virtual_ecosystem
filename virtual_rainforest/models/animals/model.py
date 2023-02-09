"""The :mod:`~virtual_rainforest.animal.model` module creates a
:class:`~virtual_rainforest.animal.model.AnimalModel` class as a child of the
:class:`~virtual_rainforest.core.model.BaseModel` class. At present a lot of the
abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.model.BaseModel.setup` and
:func:`~virtual_rainforest.core.model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the
:mod:`virtual_rainforest` model develops. The factory method
:func:`~virtual_rainforest.soil.model.AnimalModel.from_config` exists in a more complete
state, and unpacks a small number of parameters from our currently pretty minimal
configuration dictionary. These parameters are then used to generate a class instance.
If errors crop here when converting the information from the config dictionary to the
required types (e.g. :class:`~numpy.timedelta64`) they are caught and then logged, and
at the end of the unpacking an error is thrown. This error should be caught and handled
by downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205, D415


from __future__ import annotations

from typing import Any

import pint
from numpy import datetime64, timedelta64

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.model import BaseModel, InitialisationError


class AnimalModel(BaseModel):
    """A class describing the animal model.

    Describes the specific functions and attributes that the animal module should
    possess. Currently it is incomplete and mostly just a copy of the template set out
    in SoilModel.

    Args:
        update_interval: Time to wait between updates of the model state.


    """

    model_name = "animal"
    """The model name for use in registering the model and logging."""

    def __init__(
        self,
        update_interval: timedelta64,
        start_time: datetime64,
        **kwargs: Any,
    ):

        super().__init__(update_interval, start_time, **kwargs)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> AnimalModel:
        """Factory function to initialise the animal model from configuration.

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
            raw_interval = pint.Quantity(config["animal"]["model_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")
            start_time = datetime64(config["core"]["timing"]["start_time"])
        except (
            ValueError,
            pint.errors.DimensionalityError,
            pint.errors.UndefinedUnitError,
        ) as e:
            valid_input = False
            LOGGER.error(
                "Configuration types appear not to have been properly validated. This "
                "problem prevents initialisation of the animal model. The first"
                "instance of this problem is as follows: %s" % str(e)
            )

        if valid_input:
            LOGGER.info(
                "Information required to initialise the animal model successfully "
                "extracted."
            )
            return cls(update_interval, start_time)
        else:
            raise InitialisationError()

    # THIS IS BASICALLY JUST A PLACEHOLDER TO DEMONSTRATE HOW THE FUNCTION OVERWRITING
    # SHOULD WORK
    # AT THIS STEP COMMUNICATION BETWEEN MODELS CAN OCCUR IN ORDER TO DEFINE INITIAL
    # STATE
    def setup(self) -> None:
        """Function to set up the soil model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def update(self) -> None:
        """Placeholder function to solve the soil model."""

        # Finally increment timing
        self.next_update += self.update_interval

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""
