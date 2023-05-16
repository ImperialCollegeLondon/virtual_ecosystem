"""The :mod:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model` module
creates a
:class:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any, Dict, List

from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.models.abiotic_simple import simple_regression


# TODO THIS IS A DRAFT
# this is still very inconsistent as the new timing is not fully implemented
# the corresponding test are also incomplete and inconsistent
class AbioticSimpleModel(BaseModel):
    """A class describing the simple abiotic model.

    Args:
        data: The data object to be used in the model.
        start_time: A datetime64 value setting the start time of the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        initial_soil_moisture: The initial soil moisture for all layers.
    """

    model_name = "abiotic_simple"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that soil model can sensibly capture."""
    upper_bound_on_time_scale = "30 day"
    """Longest time scale that soil model can sensibly capture."""
    required_init_vars = (
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
        ("atmospheric_pressure_ref", ("spatial",)),
        ("precipitation", ("spatial",)),
        ("atmospheric_co2", ("spatial",)),
        ("mean_annual_temperature", ("spatial",)),
        ("leaf_area_index", ("spatial",)),
        ("layer_heights", ("spatial",)),
    )
    """The required variables and axes for the simple abiotic model"""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: int,
        canopy_layers: int,
        initial_soil_moisture: float,
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

        super().__init__(data, update_interval, **kwargs)

        # sanity checks for initial soil moisture
        if initial_soil_moisture < 0 or initial_soil_moisture > 100:
            to_raise = InitialisationError(
                "The initial soil moisture has to be between 0 and 100!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        if initial_soil_moisture != float(initial_soil_moisture):
            to_raise = InitialisationError("The initial soil moisture must be a float!")
            LOGGER.error(to_raise)
            raise to_raise

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        "A list of vertical layer roles."
        self.update_interval
        """The time interval between model updates."""
        self.initial_soil_moisture = initial_soil_moisture

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> AbioticSimpleModel:
        """Factory function to initialise the simple abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["abiotic"]["soil_layers"]
        canopy_layers = config["abiotic"]["canopy_layers"]
        initial_soil_moisture = config["abiotic"]["initial_soil_moisture"]

        LOGGER.info(
            "Information required to initialise the abiotic model successfully "
            "extracted."
        )
        return cls(
            data, update_interval, soil_layers, canopy_layers, initial_soil_moisture
        )

    def setup(self) -> None:
        """Function to set up the abiotic model."""

        setup_variables = simple_regression.setup_simple_regression(
            layer_roles=self.layer_roles,
            data=self.data,
            initial_soil_moisture=self.initial_soil_moisture,
        )
        update_data_object(data=self.data, output_dict=setup_variables)

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self) -> None:
        """Placeholder function to update the abiotic model."""
        # TODO do I need a counter to access the correct time index from the input data?
        output_variables = simple_regression.run_simple_regression(
            data=self.data,
            layer_roles=self.layer_roles,
            time_index=0,
        )
        update_data_object(data=self.data, output_dict=output_variables)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""


def set_layer_roles(canopy_layers: int, soil_layers: int) -> List[str]:
    """Create a list of layer roles.

    This function creates a list of layer roles for the vertical dimension of the
    Virtual Rainforest. The layer above the canopy is defined as 0 (canopy height + 2m)
    and the index increases towards the bottom of the soil column. The canopy includes
    a maximum number of canopy layers (defined in config) which are filled from the top
    with canopy node heights from the plant module (the rest is set to NaN). Below the
    canopy, we currently set one subcanopy layer (around 1.5m above ground) and one
    surface layer (0.1 m above ground). Below ground, we include a maximum number of
    soil layers (defined in config); the deepest layer is currently set to 1 m as the
    temperature there is fairly constant and equals the mean annual temperature.

    Args:
        canopy_layers: number of canopy layers
        soil_layers: number of soil layers

    Returns:
        List of canopy layer roles
    """
    return (
        ["above"]
        + ["canopy"] * canopy_layers
        + ["subcanopy"]
        + ["surface"]
        + ["soil"] * soil_layers
    )


def update_data_object(data: Data, output_dict: Dict[str, DataArray]) -> None:
    """Update data object from dict of variables.

    This function takes a dict of variables from a submodule to update
    the corresponding variables in the data object.

    Args:
        data: Data instance
        output_dict: dict of variables from submodule

    Returns:
        an updated data object for the current time step
    """

    for variable in output_dict:
        data[variable] = variable
