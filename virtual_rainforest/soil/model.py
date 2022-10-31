"""The `soil.model` module.

The `soil.model` module creates a `SoilModel` class, which extended the base `Model`
class to be usable to simulate the soil.
"""

from __future__ import annotations

from typing import Any

from numpy import datetime64, timedelta64

from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.model import BaseModel


class InitialisationError(Exception):
    """Custom exception class for model initialisation failures."""


class SoilModel(BaseModel):
    """A class describing the soil model.

    Describes the specific functions and attributes that the soil module should possess.
    It's very much incomplete at the moment, and only overwrites one function in a
    pretty basic manner. This is intended as a demonstration of how the class
    inheritance should be handled for the model classes.

    Args:
        start_time: Point in time that the model simulation should be started.
        end_time: Time that the model simulation should end
        update_interval: Time to wait between updates of the model state.

    Attributes:
        name: Names the model that is described
    """

    name = "soil"

    def __init__(
        self,
        start_time: datetime64,
        end_time: datetime64,
        update_interval: timedelta64,
        no_layers: int,
    ):
        if no_layers < 1:
            log_and_raise(
                "There has to be at least one soil layer in the soil model!", ValueError
            )
        elif not isinstance(no_layers, int):
            log_and_raise("The number of soil layers must be an integer!", TypeError)

        super(SoilModel, self).__init__(start_time, end_time, update_interval)
        self.no_layers = no_layers

    @classmethod
    def factory(cls, config: dict[str, Any]) -> SoilModel:
        """Factory function to initialise the soil model.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model.

        Args:
            config: The complete (and validated) virtual rainforest configuration.

        Raises:
            InitialisationError: If the information required to initialise the model
                either isn't found, or isn't of the correct type.
        """
        try:
            start_time = datetime64(config["core"]["timing"]["start_time"])
            end_time = datetime64(config["core"]["timing"]["end_time"])
            raw_interval = config["core"]["timing"]["update_interval"]
            # Round raw time interval to nearest minute
            update_interval = timedelta64(int(raw_interval * 24 * 60), "m")
            no_layers = config["soil"]["no_layers"]
        except KeyError as e:
            log_and_raise(
                f"Configuration is missing information required to initialise the soil "
                f"model. The first missing key is {str(e)}.",
                InitialisationError,
            )
        except ValueError as e:
            log_and_raise(
                f"Configuration types appear not to have been properly validated. This "
                f"problem prevents initialisation of the soil model. The first instance"
                f" of this problem is as follows: {str(e)}",
                InitialisationError,
            )

        # TODO - Add further relevant checks on input here as they become relevant

        LOGGER.info(
            "Information required to initialise the soil model successfully extracted."
        )

        return cls(start_time, end_time, update_interval, no_layers)

    # THIS IS BASICALLY JUST A PLACEHOLDER TO DEMONSTRATE HOW THE FUNCTION OVERWRITING
    # SHOULD WORK
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
