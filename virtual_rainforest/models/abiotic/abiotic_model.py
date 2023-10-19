"""The :mod:`~virtual_rainforest.models.abiotic.abiotic_model` module creates a
:class:`~virtual_rainforest.models.abiotic.abiotic_model.AbioticModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class. At
present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.abiotic.abiotic_model.AbioticModel.from_config`
exists in a more complete state, and unpacks a small number of parameters from our
currently pretty minimal configuration dictionary. These parameters are then used to
generate a class instance. If errors crop here when converting the information from the
config dictionary to the required types they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled by
downstream functions so that all model configuration failures can be reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

from pint import Quantity

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.config import Config
from virtual_rainforest.core.constants_loader import load_constants
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.abiotic.constants import AbioticConsts


class AbioticModel(BaseModel):
    """A class describing the abiotic model.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: A list setting the number and depths of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        constants: Set of constants for the abiotic model.
    """

    model_name = "abiotic"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 minute"
    """Shortest time scale that abiotic model can sensibly capture."""
    upper_bound_on_time_scale = "1 day"
    """Longest time scale that abiotic model can sensibly capture."""
    required_init_vars = (("air_temperature_ref", ("spatial",)),)
    """The required variables and axes for the abiotic model"""
    vars_updated = ()
    """Variables updated by the abiotic model"""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: list[float],
        canopy_layers: int,
        constants: AbioticConsts,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.update_interval
        """The time interval between model updates."""
        self.constants = constants
        """Set of constants for the abiotic model"""

    @classmethod
    def from_config(
        cls, data: Data, config: Config, update_interval: Quantity
    ) -> AbioticModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: A validated Virtual Rainforest model configuration object.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]

        # Load in the relevant constants
        constants = load_constants(config, "abiotic", "AbioticConsts")

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(
            data,
            update_interval,
            soil_layers,
            canopy_layers,
            constants,
        )

    def setup(self) -> None:
        """Function to set up the abiotic model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic model.

        Args:
            time_index: The index of the current time step in the data object.
        """

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
