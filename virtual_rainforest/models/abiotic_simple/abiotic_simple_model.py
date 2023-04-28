"""The :mod:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model` module
creates a
:class:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any, List

from numpy import datetime64, timedelta64

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import extract_model_time_details


class AbioticSimpleModel(BaseModel):
    """A class describing the simple abiotic model.

    Args:
        data: The data object to be used in the model.
        start_time: A datetime64 value setting the start time of the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
    """

    model_name = "abiotic_simple"
    """The model name for use in registering the model and logging."""
    required_init_vars = (
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
        ("atmospheric_pressure_ref", ("spatial",)),
        ("precipitation", ("spatial",)),
        ("atmospheric_co2", ("spatial",)),
        (
            "mean_annual_temperature",
            ("spatial",),
        ),
        (
            "leaf_area_index",
            ("spatial",),
        ),
        (
            "layer_heights",
            ("spatial",),
        ),
    )
    """The required variables and axes for the simple abiotic model"""

    def __init__(
        self,
        data: Data,
        update_interval: timedelta64,
        start_time: datetime64,
        soil_layers: int,
        canopy_layers: int,
        **kwargs: Any,
    ):
        # sanity checks for soil and canopy layers
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

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        "A list of vertical layer roles."
        self.update_interval
        """The time interval between model updates."""
        self.next_update
        """The simulation time at which the model should next run the update method"""

    @classmethod
    def from_config(cls, data: Data, config: dict[str, Any]) -> AbioticSimpleModel:
        """Factory function to initialise the simple abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
        """

        # Find timing details
        start_time, update_interval = extract_model_time_details(config, cls.model_name)

        # Find number of soil and canopy layers
        soil_layers = config["abiotic"]["soil_layers"]
        canopy_layers = config["abiotic"]["canopy_layers"]

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(data, update_interval, start_time, soil_layers, canopy_layers)

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


def set_layer_roles(canopy_layers: int, soil_layers: int) -> List[str]:
    """Define a list of layer roles.

    Args:
        canopy_layers: number of canopy layers
        soil_layers: number of soil layers

    Returns:
        List of canopy layer roles
    """
    return (
        ["soil"] * soil_layers
        + ["surface"]
        + ["subcanopy"]
        + ["canopy"] * canopy_layers
        + ["above"]
    )