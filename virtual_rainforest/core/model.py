"""The :mod:`~virtual_rainforest.core.model` module provides a consistent API across
models for the Virtual Rainforest model: that is, a common set of functions which work
the same across all modules. This cannot exist at a low level, as the basic classes and
functions will differ massively between modules (e.g. :mod:`~virtual_rainforest.abiotic`
will not have functions to handle consumption). So, this common api has to be high level
and define a basic set of functions to set up and run each model. These functions
effectively convert a general instruction (i.e. "setup the model") into the steps needed
to carry out that instruction for a specific model.

The :mod:`core.model` module defines the api that all individual models (e.g. the soil
model) should conform to. This consists of a class
(:class:`~virtual_rainforest.core.model.BaseModel`), which defines the expected
functions. Some functions of this class will be inherited and used by its child classes
(e.g. :func:`~virtual_rainforest.core.model.BaseModel.__repr__` and
:func:`~virtual_rainforest.core.model.BaseModel.__str__`), unless they are explicitly
overwritten in the child class (which is generally necessary for ``__init__``). This is
standard python class inheritance, which will be used in many places throughout the
``virtual_rainforest`` model.

However, a more complex form of inheritance is required for functions that define the
shared api. These should take the same input and perform an equivalent set of steps
across models, but because they interact with radically different modules their internal
workings will have little in common. Thus,
:class:`~virtual_rainforest.core.model.BaseModel` is defined as an abstract base class,
which is a class that is never intended to be instantiated itself but instead serves as
a blueprint for inheriting classes. This type of class can define abstract methods
(denoted by ``@abstractmethod``), which are merely placeholders. For these abstract
methods, child classes have to overwrite the methods with new functions, otherwise class
inheritance fails. This ensures that a consistent api (set of functions) is used across
models, while also ensuring that functions don't default to an inappropriate generic
behaviour due to a function not being defined for a particular model. At the moment, we
expect every model to have a setup, spinup, update and cleanup process, though this
might change in the future.

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
"""  # noqa: D205, D415

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
    includes functions to setup, spin up and update the specific model, as well as a
    function to cleanup redundant model data. At this level these functions are not
    define and are mere placeholders to be overwritten (where appropriate) by the
    inheriting classes.

    Args:
        start_time: Point in time that the model simulation should be started.
        end_time: Time that the model simulation should end
        update_interval: Time to wait between updates of the model state.
    """

    model_name: str

    def __init__(
        self, update_interval: timedelta64, start_time: datetime64, **kwargs: Any
    ):
        self.update_interval = update_interval
        self.next_update = start_time + update_interval
        # Save variables names to be used by the __repr__
        self._repr = ["update_interval", "next_update"]

    @abstractmethod
    def setup(self) -> None:
        """Function to use input data to set up the model."""

    @abstractmethod
    def spinup(self) -> None:
        """Function to spin up the model."""

    @abstractmethod
    def update(self) -> None:
        """Function to update the model."""

    @abstractmethod
    def cleanup(self) -> None:
        """Function to delete objects within the class that are no longer needed."""

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> Any:
        """Factory function to unpack config and initialise a model instance."""

    @classmethod
    def __init_subclass__(cls) -> None:
        """Method that adds new model classes to the model registry.

        Raises:
            ValueError: If model_name attribute isn't defined
            TypeError: If model_name is not a string
        """

        # Check that model_name exists and is a string
        if not hasattr(cls, "model_name"):
            excep = ValueError("Models must have a model_name attribute!")
            LOGGER.error(excep)
            raise excep
        elif not isinstance(cls.model_name, str):
            excep = TypeError("Models should only be named using strings!")
            LOGGER.error(excep)
            raise excep

        # Add the new model to the registry
        if cls.model_name in MODEL_REGISTRY:
            LOGGER.warning(
                "Model with name %s already exists and is being replaced",
                cls.model_name,
            )

        MODEL_REGISTRY[cls.model_name] = cls

    def __repr__(self) -> str:
        """Represent a Model as a string."""

        # Add all args to the function signature
        func_sig = ", ".join([f"{k} = {getattr(self, k)}" for k in self._repr])

        return f"{self.__class__.__name__}({func_sig})"

    def __str__(self) -> str:
        """Inform user what the model type is."""
        if hasattr(self, "model_name"):
            return f"A {self.model_name} model instance"
        else:
            return "A base model instance"
