"""The :mod:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model` module
creates a
:class:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the :class:`~virtual_rainforest.core.base_model.BaseModel` class. At
present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_rainforest.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Rainforest
model develops. The factory method
:func:`~virtual_rainforest.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel.from_config`
exists in a more complete state, and unpacks a small number of parameters from our
currently pretty minimal configuration dictionary. These parameters are then used to
generate a class instance. If errors crop here when converting the information from the
config dictionary to the required types they are caught and then logged, and at the end
of the unpacking an error is thrown. This error should be caught and handled by
downstream functions so that all model configuration failures can be reported as one.
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
from virtual_rainforest.models.abiotic_simple import microclimate
from virtual_rainforest.models.abiotic_simple.constants import AbioticSimpleConsts


class AbioticSimpleModel(
    BaseModel,
    model_name="abiotic_simple",
    model_update_bounds=("1 day", "1 month"),
    required_init_vars=(  # TODO add temporal axis
        ("air_temperature_ref", ("spatial",)),
        ("relative_humidity_ref", ("spatial",)),
        ("atmospheric_pressure_ref", ("spatial",)),
        ("atmospheric_co2_ref", ("spatial",)),
        ("mean_annual_temperature", ("spatial",)),
        ("leaf_area_index", ("spatial",)),
        ("layer_heights", ("spatial",)),
    ),
    vars_updated=(
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
    ),
):
    """A class describing the abiotic simple model.

    Args:
        data: The data object to be used in the model.
        core_constants: The core constants instance to be used for the model.
        update_interval: Time to wait between updates of the model state.
        soil_layers: A list setting the number and depths of soil layers to be modelled.
        canopy_layers: The initial number of canopy layers to be modelled.
        constants: Set of constants for the abiotic simple model.
    """

    def __init__(
        self,
        data: Data,
        core_constants: CoreConsts,
        update_interval: Quantity,
        soil_layers: list[float],
        canopy_layers: int,
        constants: AbioticSimpleConsts,
        **kwargs: Any,
    ):
        super().__init__(
            data=data,
            core_constants=core_constants,
            update_interval=update_interval,
            **kwargs,
        )

        # create a list of layer roles
        layer_roles = set_layer_roles(canopy_layers, soil_layers)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.layer_roles = layer_roles
        """A list of vertical layer roles."""
        self.update_interval
        """The time interval between model updates."""
        self.constants = constants
        """Set of constants for the abiotic simple model"""

    @classmethod
    def from_config(
        cls,
        data: Data,
        config: Config,
        core_constants: CoreConsts,
        update_interval: Quantity,
    ) -> AbioticSimpleModel:
        """Factory function to initialise the abiotic simple model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_rainforest.core.data.Data` instance.
            core_constants: The core constants instance to be used for the model.
            config: A validated Virtual Rainforest model configuration object.
            update_interval: Frequency with which all models are updated.
        """

        # Find number of soil and canopy layers
        soil_layers = config["core"]["layers"]["soil_layers"]
        canopy_layers = config["core"]["layers"]["canopy_layers"]

        # Load in the relevant constants
        constants = load_constants(config, "abiotic_simple", "AbioticSimpleConsts")

        LOGGER.info(
            "Information required to initialise the abiotic simple model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_constants=core_constants,
            update_interval=update_interval,
            soil_layers=soil_layers,
            canopy_layers=canopy_layers,
            constants=constants,
        )

    def setup(self) -> None:
        """Function to set up the abiotic simple model.

        At the moment, this function only initializes soil temperature for all
        soil layers and calculates the reference vapour pressure deficit for all time
        steps. Both variables are added directly to the self.data object.
        """

        # create soil temperature array
        self.data["soil_temperature"] = DataArray(
            np.full((len(self.layer_roles), len(self.data.grid.cell_id)), np.nan),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, len(self.layer_roles)),
                "layer_roles": ("layers", self.layer_roles),
                "cell_id": self.data.grid.cell_id,
            },
            name="soil_temperature",
        )

        # calculate vapour pressure deficit at reference height for all time steps
        self.data[
            "vapour_pressure_deficit_ref"
        ] = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            constants=self.constants,
        ).rename(
            "vapour_pressure_deficit_ref"
        )

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic simple model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic simple model.

        Args:
            time_index: The index of the current time step in the data object.
        """

        # This section performs a series of calculations to update the variables in the
        # abiotic model. This could be moved to here and written directly to the data
        # object. For now, we leave it as a separate routine.
        output_variables = microclimate.run_microclimate(
            data=self.data,
            layer_roles=self.layer_roles,
            time_index=time_index,
            constants=self.constants,
        )
        self.data.add_from_dict(output_dict=output_variables)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
