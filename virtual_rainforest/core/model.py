"""The `core.model` module.

The `core.model` module defines the api that all individual models (e.g. the soil
model) should conform to. This consists of a class (`Model`), which defines the expected
functions. The relevant modules will create classes to represent specific models, which
will inherit from the `Model` base class. These subclasses will generally overwrite the
functions defined in the base class, which are defined mainly to force a consistent api
between models. It also establishes a model registry that allows models to become
accessible across scripts without individual loading in.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from numpy import datetime64, timedelta64

from virtual_rainforest.core.logger import LOGGER, log_and_raise

MODEL_REGISTRY: dict[str, Type[BaseModel]] = {}
"""A registry for different models."""


class ImproperFunctionCall(Exception):
    """Custom exception class for cases where functions should not have been called."""


class InitialisationError(Exception):
    """Custom exception class for model initialisation failures."""


class BaseModel(ABC):
    """A superclass for all `vr` models.

    Describes the common functions and attributes that all `vr` models should have. This
    includes functions to setup, spin up and solve the specific model, as well as a
    function to cleanup redundant model data. At this level these functions are not
    define and are mere placeholders to be overwritten (where appropriate) by the
    inheriting classes.

    Args:
        start_time: Point in time that the model simulation should be started.
        end_time: Time that the model simulation should end
        update_interval: Time to wait between updates of the model state.

    Attributes:
        name: Names the model that is described
    """

    name = "base"

    def __init__(self, update_interval: timedelta64, **kwargs: Any):
        self.update_interval = update_interval
        # Save variables names to be used by the __repr__
        self._repr = ["update_interval"]

    @abstractmethod
    def spinup(self) -> None:
        """Function to spin up the model."""

    @abstractmethod
    def solve(self) -> None:
        """Function to solve the model."""

    @abstractmethod
    def cleanup(self) -> None:
        """Function to delete objects within the class that are no longer needed."""

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> Any:
        """Factory function to unpack config and initialise a model instance."""

    @classmethod
    def __init_subclass__(cls, model_name: str):
        """Method that adds new model classes to the model registry."""

        # Add the grid type to the registry
        if model_name in MODEL_REGISTRY:
            LOGGER.warning(
                "Model with name %s already exists and is being replaced", model_name
            )
        MODEL_REGISTRY[model_name] = cls

    def setup(self) -> None:
        """Function to use input data to set up the model."""

    def start_model_timing(self, start_time: datetime64) -> None:
        """Set of model timing by setting up initial last update time."""

        if hasattr(self, "last_update"):
            log_and_raise(
                "Model timing was already set up, it should not be setup again!",
                ImproperFunctionCall,
            )
        else:
            self.last_update = start_time

    def should_update(self, current_time: datetime64) -> bool:
        """Determines whether a model should be updated for a specific time step."""

        if current_time > self.last_update + self.update_interval:
            self.last_update = current_time
            return True
        return False

    def __repr__(self) -> str:
        """Represent a Model as a string."""

        # Add all args to the function signature
        func_sig = ", ".join([f"{k} = {getattr(self, k)}" for k in self._repr])

        return f"{self.__class__.__name__}({func_sig})"

    def __str__(self) -> str:
        """Inform user what the model type is."""
        return f"A {self.name} model instance"
