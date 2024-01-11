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

TODO temperatures in Kelvin
"""  # noqa: D205, D415

from __future__ import annotations

from typing import Any

import numpy as np
from pint import Quantity
from xarray import DataArray

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.config import Config
from virtual_rainforest.core.constants import CoreConsts
from virtual_rainforest.core.constants_loader import load_constants
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER
from virtual_rainforest.core.utils import set_layer_roles
from virtual_rainforest.models.abiotic import wind
from virtual_rainforest.models.abiotic.constants import AbioticConsts
from virtual_rainforest.models.abiotic_simple import microclimate
from virtual_rainforest.models.abiotic_simple.constants import AbioticSimpleConsts


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
    required_init_vars = (
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
    )
    """The required variables and axes for the abiotic model."""
    vars_updated = ()
    """Variables updated by the abiotic model."""

    def __init__(
        self,
        data: Data,
        update_interval: Quantity,
        soil_layers: list[float],
        canopy_layers: int,
        constants: AbioticConsts,
        core_constants: CoreConsts,
        **kwargs: Any,
    ):
        super().__init__(data, update_interval, **kwargs)

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.constants = constants
        """Set of constants for the abiotic model."""
        self.core_constants = core_constants
        """Set of universal constants that are used across all models."""

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
        core_constants = load_constants(config, "core", "CoreConsts")

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
            core_constants,
        )

    def setup(self) -> None:
        """Function to set up the abiotic model.

        This function initializes soil temperature and canopy temperature for all
        corresponding layers and calculates the reference vapour pressure deficit for
        all time steps of the simulation. All variables are added directly to the
        self.data object.
        """

        # Calculate vapour pressure deficit at reference height for all time steps
        # TODO sort out constants argument in simple abiotic model
        self.data[
            "vapour_pressure_deficit_ref"
        ] = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            constants=AbioticSimpleConsts(),
        ).rename(
            "vapour_pressure_deficit_ref"
        )

        # Generate initial profiles of air temperature [C], relative humidity [-],
        # vapour pressure deficit [kPa], soil temperature [C], atmospheric pressure
        # [kPa], and atmospheric :math:`\ce{CO2}` [ppm]
        output_variables = microclimate.run_microclimate(
            data=self.data,
            layer_roles=self.layer_roles,
            time_index=0,
            constants=AbioticSimpleConsts(),
            Bounds=microclimate.Bounds,
        )
        self.data.add_from_dict(output_dict=output_variables)

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic model.

        Args:
            time_index: The index of the current time step in the data object.
        """

        wind_update_inputs: dict[str, DataArray] = {}

        for var in ["layer_heights", "leaf_area_index", "air_temperature"]:
            selection = (
                self.data[var]
                .where(self.data[var].layer_roles != "soil")
                .dropna(dim="layers")
            )
            wind_update_inputs[var] = selection

        wind_update = wind.calculate_wind_profile(
            canopy_height=self.data["canopy_height"].to_numpy(),
            wind_height_above=(self.data["canopy_height"] + 15).to_numpy(),  # TODO
            wind_layer_heights=wind_update_inputs["layer_heights"].to_numpy(),
            leaf_area_index=wind_update_inputs["leaf_area_index"].to_numpy(),
            air_temperature=wind_update_inputs["air_temperature"].to_numpy(),
            atmospheric_pressure=self.data["atmospheric_pressure"].to_numpy()[0],
            sensible_heat_flux_topofcanopy=(
                self.data["sensible_heat_flux_topofcanopy"].to_numpy()
            ),
            wind_speed_ref=(
                self.data["wind_speed_ref"].isel(time_index=time_index).to_numpy()
            ),
            wind_reference_height=(self.data["canopy_height"] + 10).to_numpy(),
            abiotic_constants=self.constants,
            core_constants=self.core_constants,
        )

        wind_output = {}
        wind_speed_above_canopy = DataArray(
            wind_update["wind_speed_above_canopy"],
            dims="cell_id",
            coords={"cell_id": self.data.grid.cell_id},
        )
        wind_output["wind_speed_above_canopy"] = wind_speed_above_canopy

        for var in ["wind_speed_canopy", "friction_velocity"]:
            var_out = DataArray(
                np.concatenate(
                    (
                        wind_update[var],
                        np.full(
                            (
                                len(self.layer_roles) - len(wind_update[var]),
                                self.data.grid.n_cells,
                            ),
                            np.nan,
                        ),
                    ),
                ),
                dims=self.data["layer_heights"].dims,
                coords=self.data["layer_heights"].coords,
            )
            wind_output[var] = var_out

        self.data.add_from_dict(output_dict=wind_output)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
