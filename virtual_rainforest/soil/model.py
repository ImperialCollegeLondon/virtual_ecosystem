"""The `soil.model` module.

The `soil.model` module creates a `SoilModel` class, which extended the base `Model`
class to be usable to simulate the soil.
"""

from __future__ import annotations

from typing import Any, Optional

from numpy import timedelta64
from pint import Quantity

from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.model import BaseModel


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
            LOGGER.error("There has to be at least one soil layer in the soil model!")
        elif no_layers != int(no_layers):
            LOGGER.error("The number of soil layers must be an integer!")

        super(SoilModel, self).__init__(update_interval, **kwargs)
        self.no_layers = int(no_layers)
        # Save variables names to be used by the __repr__
        self._repr.append("no_layers")

    @classmethod
    def factory(cls, config: dict[str, Any]) -> Optional[SoilModel]:
        """Factory function to initialise the soil model.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance None is returned.

        Args:
            config: The complete (and validated) virtual rainforest configuration.

        """

        # Assume input is valid until we learn otherwise
        valid_input = True
        try:
            raw_interval = Quantity(config["core"]["timing"]["min_time_step"]).to(
                "minutes"
            )
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(raw_interval.magnitude), "m")
            no_layers = config["soil"]["no_layers"]
        except KeyError as e:
            valid_input = False
            LOGGER.error(
                f"Configuration is missing information required to initialise the soil "
                f"model. The first missing key is {str(e)}."
            )
        except ValueError as e:
            valid_input = False
            LOGGER.error(
                f"Configuration types appear not to have been properly validated. This "
                f"problem prevents initialisation of the soil model. The first instance"
                f" of this problem is as follows: {str(e)}"
            )

        # TODO - Add further relevant checks on input here as they become necessary

        if valid_input:
            LOGGER.info(
                "Information required to initialise the soil model successfully "
                "extracted."
            )
            return cls(update_interval, no_layers)
        else:
            return None

    # THIS IS BASICALLY JUST A PLACEHOLDER TO DEMONSTRATE HOW THE FUNCTION OVERWRITING
    # SHOULD WORK
    # AT THIS STEP COMMUNICATION BETWEEN MODELS CAN OCCUR IN ORDER TO DEFINE INITIAL
    # STATE
    def setup(self) -> None:
        """Function to set up the soil model."""
        for layer in range(0, self.no_layers):
            LOGGER.info(f"Setting up soil layer {layer}")

    def spinup(self) -> None:
        """Placeholder function to spin up the soil model."""

    def solve(self) -> None:
        """Placeholder function to solve the soil model."""

    def cleanup(self) -> None:
        """Placeholder function for soil model cleanup."""
