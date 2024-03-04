"""The :mod:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model` module
creates a
:class:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class. At
present a lot of the abstract methods of the parent class (e.g.
:func:`~virtual_ecosystem.core.base_model.BaseModel.spinup`) are overwritten using
placeholder functions that don't do anything. This will change as the Virtual Ecosystem
model develops. The factory method
:func:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel.from_config`
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
from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic_simple import microclimate
from virtual_ecosystem.models.abiotic_simple.constants import AbioticSimpleConsts


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
        core_components: The core components used across models.
        model_constants: Set of constants for the abiotic_simple model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: AbioticSimpleConsts = AbioticSimpleConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        self.data
        """A Data instance providing access to the shared simulation data."""
        self.model_constants = model_constants
        """Set of constants for the abiotic simple model"""

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> AbioticSimpleModel:
        """Factory function to initialise the abiotic simple model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(
            config, "abiotic_simple", "AbioticSimpleConsts"
        )

        LOGGER.info(
            "Information required to initialise the abiotic simple model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            model_constants=model_constants,
        )

    def setup(self) -> None:
        """Function to set up the abiotic simple model.

        At the moment, this function only initializes soil temperature for all
        soil layers and calculates the reference vapour pressure deficit for all time
        steps. Both variables are added directly to the self.data object.
        """

        # create soil temperature array
        self.data["soil_temperature"] = DataArray(
            np.full(
                (self.layer_structure.n_layers, self.data.grid.n_cells),
                np.nan,
            ),
            dims=["layers", "cell_id"],
            coords={
                "layers": np.arange(0, self.layer_structure.n_layers),
                "layer_roles": ("layers", self.layer_structure.layer_roles),
                "cell_id": self.data.grid.cell_id,
            },
            name="soil_temperature",
        )

        # calculate vapour pressure deficit at reference height for all time steps
        self.data["vapour_pressure_deficit_ref"] = (
            microclimate.calculate_vapour_pressure_deficit(
                temperature=self.data["air_temperature_ref"],
                relative_humidity=self.data["relative_humidity_ref"],
                constants=self.model_constants,
            ).rename("vapour_pressure_deficit_ref")
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
            layer_roles=self.layer_structure.layer_roles,
            time_index=time_index,
            constants=self.model_constants,
        )
        self.data.add_from_dict(output_dict=output_variables)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
