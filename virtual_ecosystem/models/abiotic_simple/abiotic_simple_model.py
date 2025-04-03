"""The :mod:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model` module
creates a
:class:`~virtual_ecosystem.models.abiotic_simple.abiotic_simple_model.AbioticSimpleModel`
class as a child of the :class:`~virtual_ecosystem.core.base_model.BaseModel` class.

Todo:
* update temperatures to Kelvin
* pressure and CO2 profiles should only be filled for filled/true above ground layers
"""  # noqa: D205

from __future__ import annotations

from typing import Any

from pyrealm.constants import CoreConst as PyrealmConst

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants_loader import load_constants
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.abiotic_simple.constants import (
    AbioticSimpleBounds,
    AbioticSimpleConsts,
)
from virtual_ecosystem.models.abiotic_simple.microclimate_simple import (
    calculate_vapour_pressure_deficit,
    run_simple_microclimate,
)


class AbioticSimpleModel(
    BaseModel,
    model_name="abiotic_simple",
    model_update_bounds=("1 day", "1 month"),
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
        "wind_speed",
    ),
    vars_required_for_update=(
        "air_temperature_ref",
        "relative_humidity_ref",
        "vapour_pressure_deficit_ref",
        "atmospheric_pressure_ref",
        "atmospheric_co2_ref",
        "wind_speed_ref",
        "leaf_area_index",
        "layer_heights",
    ),
    vars_populated_by_init=(  # TODO move functionality from setup() to __init__
        "soil_temperature",
        "vapour_pressure_ref",
        "vapour_pressure_deficit_ref",
    ),
    vars_populated_by_first_update=(
        "air_temperature",
        "relative_humidity",
        "vapour_pressure_deficit",
        "atmospheric_pressure",
        "atmospheric_co2",
        "wind_speed",
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
        static: bool = False,
        **kwargs: Any,
    ):
        """Abiotic simple init.

        The init function is used only to define class attributes. Any logic should be
        handeled in
        :fun:`~virtual_ecosystem.abiotic_simple.abiotic_simple_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

        self.model_constants: AbioticSimpleConsts
        """Set of constants for the abiotic simple model"""
        self.bounds: AbioticSimpleBounds
        """Upper and lower bounds for abiotic variables."""

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
        static = config["abiotic_simple"]["static"]

        LOGGER.info(
            "Information required to initialise the abiotic simple model successfully "
            "extracted."
        )
        return cls(
            data=data,
            core_components=core_components,
            static=static,
            model_constants=model_constants,
        )

    def _setup(self, model_constants: AbioticSimpleConsts, **kwargs) -> None:
        """Function to set up the abiotic simple model.

        This function initializes soil temperature for all soil layers and calculates
        the reference vapour pressure deficit for all time steps. Both variables are
        added directly to the self.data object.

        Args:
            model_constants: Set of constants for the abiotic simple model.
            **kwargs: Further arguments to the setup method.
        """
        self.model_constants = model_constants
        self.bounds = AbioticSimpleBounds()

        # create soil temperature array
        self.data["soil_temperature"] = self.layer_structure.from_template()

        # calculate vapour pressure deficit at reference height for all time steps
        vapour_pressure_and_deficit = calculate_vapour_pressure_deficit(
            temperature=self.data["air_temperature_ref"],
            relative_humidity=self.data["relative_humidity_ref"],
            pyrealm_const=PyrealmConst(),
        )
        self.data["vapour_pressure_deficit_ref"] = vapour_pressure_and_deficit[
            "vapour_pressure_deficit"
        ]
        self.data["vapour_pressure_ref"] = vapour_pressure_and_deficit[
            "vapour_pressure"
        ]

    def spinup(self) -> None:
        """Placeholder function to spin up the abiotic simple model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the abiotic simple model.

        Args:
            time_index: The index of the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

        # This section performs a series of calculations to update the variables in the
        # abiotic model. The updated variables are then added to the data object.
        output_variables = run_simple_microclimate(
            data=self.data,
            layer_structure=self.layer_structure,
            time_index=time_index,
            constants=self.model_constants,
            bounds=self.bounds,
        )
        self.data.add_from_dict(output_dict=output_variables)

    def cleanup(self) -> None:
        """Placeholder function for abiotic model cleanup."""
