"""The :mod:`~virtual_rainforest.models.hydrology.hydrology_model` module
creates a
:class:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class.
At present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.hydrology.hydrology_model.HydrologyModel.from_config`
exists in a
more complete state, and unpacks a small number of parameters from our currently pretty
minimal configuration dictionary. These parameters are then used to generate a class
instance. If errors crop here when converting the information from the config dictionary
to the required types they are caught and then logged, and at the end of the unpacking
an error is thrown. This error should be caught and handled by downstream functions so
that all model configuration failures can be reported as one.
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union

import numpy as np
import xarray as xr
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import InitialisationError
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.hydrology.hydrology_constants import HydrologyParameters


class HydrologyModel(BaseModel):
    """A class describing the hydrology model.

    Args:
        data: The data object to be used in the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: The number of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        initial_soil_moisture: The initial soil moisture for all layers.

    Raises:
        InitialisationError: when initial soil moisture is out of bounds.
    """

    model_name = "hydrology"
    """The model name for use in registering the model and logging."""
    lower_bound_on_time_scale = "1 day"
    """Shortest time scale that hydrology model can sensibly capture."""
    upper_bound_on_time_scale = "1 month"
    """Longest time scale that hydrology model can sensibly capture."""
    required_init_vars = (
        ("precipitation", ("spatial",)),
        ("leaf_area_index", ("spatial",)),
    )  # TODO add time
    """The required variables and axes for the hydrology model"""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: int,
        canopy_layers: int,
        initial_soil_moisture: float,
        **kwargs: Any,
    ):
        # sanity checks for initial soil moisture
        if type(initial_soil_moisture) is not float:
            to_raise = InitialisationError("The initial soil moisture must be a float!")
            LOGGER.error(to_raise)
            raise to_raise

        if initial_soil_moisture < 0 or initial_soil_moisture > 1:
            to_raise = InitialisationError(
                "The initial soil moisture has to be between 0 and 1!"
            )
            LOGGER.error(to_raise)
            raise to_raise

        super().__init__(data, update_interval, **kwargs)

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.update_interval
        """The time interval between model updates."""
        self.initial_soil_moisture = initial_soil_moisture
        """Initial soil moisture for all layers and grill cells identical."""
        self.time_index = 0
        """Start counter for extracting correct input data."""

    @classmethod
    def from_config(
        cls, data: Data, config: dict[str, Any], update_interval: Quantity
    ) -> HydrologyModel:
        """Factory function to initialise the hydrology model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            config: The complete (and validated) Virtual Rainforest configuration.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]
        initial_soil_moisture = config["hydrology"]["initial_soil_moisture"]

        LOGGER.info(
            "Information required to initialise the hydrology model successfully "
            "extracted."
        )
        return cls(
            data, update_interval, soil_layers, canopy_layers, initial_soil_moisture
        )

    def setup(self) -> None:
        """Function to set up the hydrology model.

        At the moment, this function only initializes soil moisture homogenously for all
        soil layers.
        """

        # Create 1-dimenaional numpy array filled with initial soil moisture values for
        # all soil layers and np.nan for atmosphere layers
        soil_moisture_values = np.repeat(
            a=[np.nan, self.initial_soil_moisture],
            repeats=[
                len(self.layer_roles) - self.layer_roles.count("soil"),
                self.layer_roles.count("soil"),
            ],
        )
        # Broadcast 1-dimensional array to grid and assign dimensions and coordinates
        self.data["soil_moisture"] = DataArray(
            np.broadcast_to(
                soil_moisture_values,
                (len(self.data.grid.cell_id), len(self.layer_roles)),
            ).T,
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(15),
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": self.data.grid.cell_id,
            },
            name="soil_moisture",
        )

    def spinup(self) -> None:
        """Placeholder function to spin up the hydrology model."""

    def update(
        self,
        HydrologyParameters: Dict = HydrologyParameters,
    ) -> None:
        """Function to update the hydrology model.

        At the moment, this step updates the soil moisture and surface runoff .
        """

        # Precipitation at the surface is reduced as a function of leaf area index
        precipitation_surface = self.data["precipitation"].isel(
            time_index=self.time_index
        ) * (
            1
            - HydrologyParameters["water_interception_factor"]
            * self.data["leaf_area_index"].sum(dim="layers")
        )

        # Mean soil moisture profile, [] and Runoff, [mm]
        soil_moisture_only, surface_run_off = calculate_soil_moisture(
            layer_roles=self.layer_roles,
            precipitation_surface=precipitation_surface,
            current_soil_moisture=self.data["soil_moisture"],
            soil_moisture_capacity=HydrologyParameters["soil_moisture_capacity"],
        )

        self.data["soil_moisture"] = xr.concat(
            [
                self.data["soil_moisture"].isel(
                    layers=np.arange(
                        0, len(self.layer_roles) - self.layer_roles.count("soil")
                    )
                ),
                soil_moisture_only,
            ],
            dim="layers",
        )
        self.data["surface_run_off"] = surface_run_off

        self.time_index += 1

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""


def calculate_soil_moisture(
    layer_roles: List,
    precipitation_surface: DataArray,
    current_soil_moisture: DataArray,
    soil_moisture_capacity: Union[DataArray, float] = HydrologyParameters[
        "soil_moisture_capacity"
    ],
) -> Tuple[DataArray, DataArray]:
    """Calculate surface runoff and update soil moisture for one time step.

    Soil moisture and surface runoff are calculated with a simple bucket model based on
    :cite:p`davis_simple_2017`: if precipitation exceeds soil moisture capacity, the
    excess water is added to runoff and soil moisture is set to soil moisture capacity
    value; if the soil is not saturated, precipitation is added to the current soil
    moisture level and runoff is set to zero.

    Args:
        layer_roles: list of layer roles (from top to bottom: above, canopy, subcanopy,
            surface, soil)
        precipitation_surface: precipitation that reaches surface, [mm],
        current_soil_moisture: current soil moisture at upper layer, [mm],
        soil_moisture_capacity: soil moisture capacity (optional), [relative water
            content]

    Returns:
        current soil moisture for one layer, [relative water content], surface runoff,
            [mm]
    """
    # calculate how much water can be added to soil before capacity is reached.
    # The relative water content is converted to mm at 1 m depth with the equation:
    # water content in mm = relative water content / 100 * depth in mm
    # for 20% water at 40 cm this would be: 20/100 * 400mm = 80 mm
    available_capacity = (
        soil_moisture_capacity - current_soil_moisture.mean(dim="layers")
    ) * 1000

    # calculate where precipitation exceeds available capacity
    surface_runoff_cells = precipitation_surface.where(
        precipitation_surface > available_capacity
    )
    # calculate runoff
    surface_runoff = (
        DataArray(surface_runoff_cells.data - available_capacity.data / 1000)
        .fillna(0)
        .rename("surface_runoff")
        .rename({"dim_0": "cell_id"})
        .assign_coords({"cell_id": current_soil_moisture.cell_id})
    )

    # calculate total water in each grid cell
    total_water = (
        current_soil_moisture.mean(dim="layers") + precipitation_surface / 1000
    )

    # calculate soil moisture for one layer (1 m depth) and copy to all layers
    # TODO variable soil moisture with depth
    soil_moisture = (
        DataArray(np.clip(total_water, 0, soil_moisture_capacity))
        .expand_dims(dim={"layers": np.arange(layer_roles.count("soil"))}, axis=0)
        .assign_coords(
            {
                "cell_id": current_soil_moisture.cell_id,
                "layers": [
                    len(layer_roles) - layer_roles.count("soil"),
                    len(layer_roles) - 1,
                ],
                "layer_roles": ("layers", layer_roles.count("soil") * ["soil"]),
            }
        )
    )

    return soil_moisture, surface_runoff
