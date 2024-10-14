"""The :mod:`~virtual_ecosystem.models.microclimate.microclimate_model` module
creates a
:class:`~virtual_ecosystem.models.microclimate.microclimate_model.MicroclimateModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.
"""  # noqa: D205

from __future__ import annotations

from typing import Any
import numpy as np

from xarray import DataArray

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents, LayerStructure
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.microclimate.constants import MicroclimateConsts
from virtual_ecosystem.models.microclimate import initialise_microclimate
from virtual_ecosystem.models.abiotic_simple import microclimate
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)


class MicroclimateModel(
    BaseModel,
    model_name="microclimate",
    model_update_bounds=("1 hour", "1 month"),
    vars_required_for_init=(
        "air_temperature_ref",
        "relative_humidity_ref",
    ),
    vars_updated=(
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "soil_temperature",
        "atmospheric_pressure",
        "atmospheric_co2",
    ),
    vars_required_for_update=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "vapour_pressure_deficit_ref",
        "atmospheric_pressure_ref",
        "atmospheric_co2_ref",
        "leaf_area_index",
        "layer_heights",
    ),
    vars_populated_by_init=(
        "soil_temperature",
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
    ),
    vars_populated_by_first_update=(),
):
    """A class describing the microclimate model.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        model_constants: Set of constants for the microclimate model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        model_constants: MicroclimateConsts = MicroclimateConsts(),
        **kwargs: Any,
    ):
        super().__init__(data=data, core_components=core_components, **kwargs)

        self.model_constants = model_constants
        """Set of constants for the microclimate model"""
        self.simple_constants = AbioticSimpleConsts()
        """Set of constants for simple abiotic model."""

        self._setup()

    @classmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> MicroclimateModel:
        """Factory function to initialise the abiotic model from configuration.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
        """

        # Load in the relevant constants
        model_constants = load_constants(config, "microclimate", "MicroclimateConsts")

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
        """No longer in use.

        TODO: Remove when the base model is updated.
        """

    def _setup(self) -> None:
        """Function to set up the microclimate model.

        This function initializes soil temperature and canopy temperature for all
        corresponding layers and calculates the reference vapour pressure deficit for
        all time steps of the simulation. All variables are added directly to the
        self.data object.
        """

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # Calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = microclimate.calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            saturation_vapour_pressure_factors=(
                self.simple_constants.saturation_vapour_pressure_factors
            ),
        )
        self.data["vapour_pressure_deficit_ref"] = (
            vapour_pressure_and_deficit["vapour_pressure_deficit"]
        ).rename("vapour_pressure_deficit_ref")

        self.data["vapour_pressure_ref"] = (
            vapour_pressure_and_deficit["vapour_pressure"]
        ).rename("vapour_pressure_ref")

        # Generate initial profiles of air temperature [C], relative humidity [-],
        # vapour pressure deficit [kPa], soil temperature [C], atmospheric pressure
        # [kPa], and atmospheric :math:`\ce{CO2}` [ppm]
        initial_microclimate = microclimate.run_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=0,
            constants=self.simple_constants,
            bounds=AbioticSimpleBounds(),
        )

        initial_canopy_and_soil = (
            initialise_microclimate.initialise_canopy_and_soil_fluxes(
                air_temperature=initial_microclimate["air_temperature"],
                topofcanopy_radiation=self.data["topofcanopy_radiation"].isel(
                    time_index=0
                ),
                leaf_area_index=self.data["leaf_area_index"],
                layer_heights=self.data["layer_heights"],
                layer_structure=self.layer_structure,
                light_extinction_coefficient=(
                    self.model_constants.light_extinction_coefficient
                ),
                canopy_temperature_ini_factor=(
                    self.model_constants.canopy_temperature_ini_factor
                ),
            )
        )

        # Update data object
        for output_dict in (
            initial_microclimate,
            initial_canopy_and_soil,
        ):
            self.data.add_from_dict(output_dict=output_dict)

    def spinup(self) -> None:
        """Placeholder function to spin up the microclimate model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the microclimate model.

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

    def cleanup(self) -> None:
        """Placeholder function for microclimate cleanup."""
