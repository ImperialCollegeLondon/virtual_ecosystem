"""API documentation for the :mod:`core.model` module.
************************************************** # noqa: D205

The :mod:`core.model` module defines the api that all individual models (e.g. the soil
model) should conform to. This consists of a class
(:class:`~virtual_rainforest.core.model.BaseModel`), which defines the expected
functions. This class is an abstract base class, which is a class that is never intended
to be instantiated itself but instead serves as a blueprint for inheriting classes. Some
of its functions will be inherited and used by its child classes (e.g.
:func:`~virtual_rainforest.core.model.BaseModel.__repr__` and
:func:`~virtual_rainforest.core.model.BaseModel.__str__`), unless they are explicitly
overwritten in the child class (which is generally necessary for ``__init__``). However,
it also possesses abstract methods (denoted by ``@abstractmethod``), which are merely
placeholders. For these abstract methods, child classes have to overwrite the methods
with new functions, otherwise class inheritance fails. This ensures that a consistent
api (set of functions) is used across models, while also ensuring that functions don't
default to an inappropriate generic behaviour due to a function not being defined for a
particular model. Therefore, abstract methods should be used for functions that are
always required, and are near certain to follow a different process for each model. At
the moment, we expect every model to have a setup, spinup, solve and cleanup process,
though this might change in the future.

We also define an abstract class method to perform model initialisation. This method
(:func:`~virtual_rainforest.core.model.BaseModel.from_config`) is a factory method which
unpacks the configuration dictionary, extracts the relevant tags and attempts to convert
them into the form needed to initialise a class instance. This method must be defined
for every child class of :class:`~virtual_rainforest.core.model.BaseModel`, as unpacking
our complex configuration dictionary is a necessary before a class instance can be
initialised.

As in the case of configuration schema, we make ``Model`` classes generally accessible
by adding them to a registry. However, in this case the function to add to the registry
isn't a decorator but rather a member function of
:class:`~virtual_rainforest.core.model.BaseModel`. The existence of this
:func:`~virtual_rainforest.core.model.BaseModel.__init_subclass__` function means that
every child class is automatically added to the model registry (called
:attr:`~virtual_rainforest.core.model.MODEL_REGISTRY`), but that in every case a
``model_name`` has to be provided to register it under. This model name should be
unique. Although registration is automatic, it only happens when class definition
happens, which requires the module which defines the child class to be imported
somewhere. At the moment, we import all child models in the top level ``__init__.py`` to
ensure that they are added to the registry.

An example of ``Model`` inheritance from
:class:`~virtual_rainforest.core.model.BaseModel` can been seen in the :mod:`soil.model`
module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from numpy import datetime64, timedelta64

from virtual_rainforest.core.logger import LOGGER

MODEL_REGISTRY: dict[str, Type[BaseModel]] = {}
"""A registry for different models."""


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
    # TODO - Once higher level timing function is written use it to set this
    last_update = datetime64("2000-01-01")

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
