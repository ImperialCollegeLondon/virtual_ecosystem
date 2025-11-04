"""A testing model to use in minimal ve_run testing."""

from __future__ import annotations

from typing import Any

from virtual_ecosystem.core.base_model import BaseModel
from virtual_ecosystem.core.configuration import CompiledConfiguration
from virtual_ecosystem.core.core_components import CoreComponents
from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.testing.model_config import TestingConfiguration


class TestingModel(
    BaseModel,
    model_name="testing",
    model_update_bounds=("1 day", "1 year"),
    vars_required_for_init=tuple(),
    vars_populated_by_init=tuple(),
    vars_required_for_update=tuple(),
    vars_updated=tuple(),
    vars_populated_by_first_update=tuple(),
):
    """A model that does literally nothing to run model testing.

    Args:
        data: The data object to be used in the model.
        core_components: The core components used across models.
        flora: A Flora instance of the plant functional types to be used in the model.
        model_constants: Set of constants for the plants model.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        static: bool = False,
        **kwargs: Any,
    ):
        """Plants init function.

        The init function is used only to define class attributes. Any logic should be
        handled in :fun:`~virtual_ecosystem.plants.plants_model._setup`.
        """

        super().__init__(data, core_components, static, **kwargs)

    @classmethod
    def from_config(
        cls,
        data: Data,
        configuration: CompiledConfiguration,
        core_components: CoreComponents,
    ) -> TestingModel:
        """Factory function to initialise a testing model from configuration.

        Args:
            data: A :class:`~virtual_ecosystem.core.data.Data` instance.
            configuration: A validated Virtual Ecosystem model configuration object.
            core_components: The core components used across models.
        """

        # Extract the validated model configuration from the complete compiled
        # configuration. This syntax is odd but required to support static typing
        model_configuration: TestingConfiguration = configuration.get_subconfiguration(
            "testing", TestingConfiguration
        )

        # Load in the relevant constants
        static = model_configuration.static

        # Create the instance
        inst = cls(
            data=data,
            core_components=core_components,
            static=static,
        )

        LOGGER.info("Testing model instance generated from configuration.")
        return inst

    def _setup(self, **kwargs: Any) -> None:
        """Placeholder function to setup the testing model."""

    def spinup(self) -> None:
        """Placeholder function to spin up the testing model."""

    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Placeholder function to update up the tesying model."""

    def cleanup(self) -> None:
        """Placeholder function for testing model cleanup."""
