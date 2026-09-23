"""A disturbance that captures the addition of fertiliser to the soil model.

At present, this disturbance only affects the inorganic nitrogen pools (nitrate and
ammonium). You can select the time steps for which fertiliser is applied, however, you
cannot select specific grid cells to apply it for, i.e. it is always applied across the
entire grid.

For simplicity, the units used for fertiliser application are currently densities per
(simulation) timestep, these almost certainly need to be altered to better match the
units used in real world management.

This disturbance is intended to be expanded over time so the limitations already
mentioned can be removed (if it becomes necessary).
"""

from __future__ import annotations

from typing import Any

from virtual_ecosystem.core.base_model import BaseDisturbance, BaseModel
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents, DisturbanceTiming
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.disturbances.add_fertiliser.model_config import (
    AddFertiliserConfiguration,
    AddFertiliserConstants,
)


class AddFertiliserModel(
    BaseDisturbance,
    model_name="add_fertiliser",
    disturbed_models=(),
    data_variables_disturbed=tuple(("soil_n_pool_ammonium", "soil_n_pool_nitrate")),
):
    """A disturbance that simulates fertilisation by adding nutrients to the soil.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        static: Boolean flag indicating if the model should run in static mode.
    """

    def __init__(
        self,
        data: Data,
        models: dict[str, BaseModel],
        disturbance_timing: DisturbanceTiming,
        constants: AddFertiliserConstants = AddFertiliserConstants(),
    ):
        """Add_fertiliser init function.

        The init function is used only to define class attributes.
        """

        super().__init__(
            data=data, models=models, disturbance_timing=disturbance_timing
        )

        self.constants = constants
        """Set of constants for the add_fertiliser disturbance."""

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
        models: dict[str, BaseModel],
    ) -> AddFertiliserModel:
        """Factory function to initialise fertiliser addition disturbance from config.

        This function unpacks the relevant information from the configuration file, and
        then uses it to initialise the model. If any information from the config is
        invalid rather than returning an initialised model instance an error is raised.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
            config: A validated Virtual Ecosystem model configuration object.
            models: dictionary of :class:`~virtual_ecosystem.core.base_model.BaseModel`
                instances of the models available in the simulation.
        """

        # Extract the validated model configuration from the complete compiled
        # configuration. This syntax is odd but required to support static typing
        model_configuration: AddFertiliserConfiguration = (
            configuration.get_subconfiguration(
                cls.model_name, AddFertiliserConfiguration
            )
        )

        # Get the disturbance timing
        model_timing = core_components.model_timing
        disturbance_timing = DisturbanceTiming(
            model_timing,
            run_at=model_configuration.run_at,
            run_every=model_configuration.run_every,
        )

        LOGGER.info(
            "Information required to initialise the fertiliser addition disturbance "
            "successfully extracted."
        )

        # Create the instance
        inst = cls(
            data=data,
            models=models,
            disturbance_timing=disturbance_timing,
            constants=model_configuration.constants,
        )

        LOGGER.info(
            "Fertiliser addition disturbance instance generated from configuration."
        )
        return inst

    def _disturb(self, time_index: int, **kwargs: Any) -> None:
        """Disturb the soil model with fertiliser addition.

        This adds inorganic nitrogen to the nitrate and ammonium soil pools
        """

        # Calculate total addition to each pool
        nitrate_addition = (
            self.constants.inorganic_nitrogen_addition * self.constants.nitrate_fraction
        )
        ammonium_addition = self.constants.inorganic_nitrogen_addition * (
            1 - self.constants.nitrate_fraction
        )

        # Add the fertiliser to the pools
        self.data["soil_n_pool_nitrate"] += nitrate_addition
        self.data["soil_n_pool_ammonium"] += ammonium_addition
