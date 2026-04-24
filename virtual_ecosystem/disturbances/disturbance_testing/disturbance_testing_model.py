"""A testing model to use in minimal ve_run testing."""

from __future__ import annotations

from typing import Any

from virtual_ecosystem.core.base_model import BaseDisturbance, BaseModel
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents, DisturbanceTiming
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.disturbances.disturbance_testing.model_config import (
    DisturbanceTestingConfiguration,
)


class DisturbanceTestingModel(
    BaseDisturbance,
    model_name="disturbance_testing",
    disturbed_models=("testing",),
    data_variables_disturbed=tuple(),
):
    """A disturbance model that does literally nothing.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        static: Boolean flag indicating if the model should run in static mode.
    """

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
        models: dict[str, BaseModel],
    ) -> DisturbanceTestingModel:
        """Factory function to initialise a testing model from configuration."""

        # Extract the validated model configuration from the complete compiled
        # configuration. This syntax is odd but required to support static typing
        model_configuration: DisturbanceTestingConfiguration = (
            configuration.get_subconfiguration(
                cls.model_name, DisturbanceTestingConfiguration
            )
        )

        # Get the disturbance timing
        model_timing = core_components.model_timing
        disturbance_timing = DisturbanceTiming(
            model_timing,
            run_at=model_configuration.run_at,
            run_every=model_configuration.run_every,
        )

        # Create the instance
        inst = cls(data=data, models=models, disturbance_timing=disturbance_timing)

        LOGGER.info("Disturbance testing model instance generated from configuration.")
        return inst

    def _disturb(self, time_index: int, **kwargs: Any) -> None:
        """Placeholder function to disturb the models."""
