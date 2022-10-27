"""The `soil.model` module.

The `soil.model` module creates a `SoilModel` class, which extended the base `Model`
class to be usable to simulate the soil. TODO - SOMETHING ABOUT ADDING TO THE REGISTRY
"""

from numpy import datetime64, timedelta64

from virtual_rainforest.core.logger import LOGGER, log_and_raise
from virtual_rainforest.core.model import BaseModel, register_model


# TODO - Change registry system to run in the init and created an instance rather than a
# class.
@register_model("soil")
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

    name = "soil model"

    # THIS IS BASICALLY JUST A PLACEHOLDER TO DEMONSTRATE HOW THE FUNCTION OVERWRITING
    # SHOULD WORK
    def setup(self) -> None:
        """Function to set up the soil model."""
        for layer in range(0, self.no_layers):
            LOGGER.info(f"Setting up soil layer {layer}")

    def __repr__(self) -> str:
        """Represent a Model as a string."""
        return (
            f"SoilModel(start_time={self.start_time}, end_time={self.end_time}, "
            f"update_interval={self.update_interval}, no_layers={self.no_layers})"
        )

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
        super(SoilModel, self).__init__(start_time, end_time, update_interval)
        self.no_layers = no_layers
