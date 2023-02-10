"""The :mod:`~virtual_rainforest.core.model` module defines the high level API for the
different models within the Virtual Rainforest. The module creates the
:class:`~virtual_rainforest.core.models.BaseModel` abstract base class (ABC) which
defines a consistent API for subclasses defining an actual model. The API defines
abstract methods for each of the key stages in the workflow of running a model:
individual subclasses are **required** to provide model specific implementations for
each stage, although the specific methods may simply do nothing if no action is needed
at that stage. The stages are:

* Creating a model instance (:class:`~virtual_rainforest.core.models.BaseModel`).
* Setup a model instance (:meth:`~virtual_rainforest.core.models.BaseModel.setup`).
* Perform any spinup required to get a model state to equilibrate
  (:meth:`~virtual_rainforest.core.models.BaseModel.spinup`).
* Update the model from one time step to the next
  :meth:`~virtual_rainforest.core.models.BaseModel.update`).
* Cleanup any unneeded resources at the end of a simulation
  (:meth:`~virtual_rainforest.core.models.BaseModel.cleanup`).

The :class:`~virtual_rainforest.core.models.BaseModel` class also provides default
implementations for the :func:`~virtual_rainforest.core.model.BaseModel.__repr__` and
:func:`~virtual_rainforest.core.model.BaseModel.__str__` special methods.

The :class:`~virtual_rainforest.core.models.BaseModel` has two class attributes that
must be defined in subclasses:

* The :attr:`~virtual_rainforest.core.models.BaseModel.model_name` atttribute and
* The :attr:`~virtual_rainforest.core.models.BaseModel.required_init_vars` attribute.

The usage of these two attributes is described in their docstrings.

Model registration
------------------

The :class:`~virtual_rainforest.core.models.BaseModel` abstract base class defines the
:func:`~virtual_rainforest.core.model.BaseModel.__init_subclass__` class method. This
method is called automatically whenever a subclass of the ABC is imported: it validates
the class attributes for the new class and then registers the model name and model class
in the called :attr:`~virtual_rainforest.core.model.MODEL_REGISTRY` register. This
registry is used to identify requested model subclasses from the configuration details
from  Virtual Rainforest simulation.

The ``BaseModel.__init__`` method
----------------------------------

All subclasses **must** call the
:meth:`~virtual_rainforest.core.models.BaseModel.__init__` method. This method does two
things:

* It populates the shared instance attributes
  :attr:`~virtual_rainforest.core.models.BaseModel.data`,
  :attr:`~virtual_rainforest.core.models.BaseModel.start_time` and
  :attr:`~virtual_rainforest.core.models.BaseModel.update_interval`.
* It uses the :meth:`~virtual_rainforest.core.models.BaseModel.check_required_init_vars`
  to confirm that the required variables for the model are present in the ``data``
  attribute.

The ``from_config`` factory method
----------------------------------

The ABC also defines the abstract class method
:func:`~virtual_rainforest.core.model.BaseModel.from_config`. This method must be
defined by subclasses and must be a factory method that takes a
:class:`~virtual_rainforest.core.data.Data` instance and  a model specific configuration
dictionary and returns an instance of the subclass. For any given model, the method
should provide any code to validate the configuration and then use the configuration to
initialise and return a new instance of the class.
"""  # noqa: D205, D415

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from numpy import datetime64, timedelta64

from virtual_rainforest.core.data import Data
from virtual_rainforest.core.logger import LOGGER

MODEL_REGISTRY: dict[str, Type[BaseModel]] = {}
"""A registry for different models."""


class InitialisationError(Exception):
    """Custom exception class for model initialisation failures."""


class BaseModel(ABC):
    """A superclass for all Virtual Rainforest models.

    This abstract base class defines the shared common methods and attributes used as an
    API across all Virtual Rainforest models. This includes functions to setup, spin up
    and update the specific model, as well as a function to cleanup redundant model
    data.

    The base class defines the core abstract methods that must be defined in subclasses
    as well as shared helper functions.

    Args:
        data: A :class:`~virtual_rainforest.core.data.Data` instance containing
            variables to be used in the model.
        start_time: Point in time that the model simulation should be started.
        update_interval: Time to wait between updates of the model state.
    """

    model_name: str
    """The model name.

    This class attribute sets the name used to refer to identify the model class in the
    :data:`~virtual_rainforest.core.model.MODEL_REGISTRY`, within the configuration
    settings and in logging messages."""

    required_init_vars: list[tuple[str, tuple[str]]]
    """Required variables for model initialisation.

    This class attribute defines a set of variable names that must be present in the
    :class:`~virtual_rainforest.core.data.Data` instance used to initialise an instance
    of this class. It is a list of variable names and then optionally the names of any
    core axes which the variable must map onto.

    For example: ``[('temperature', ('spatial', 'temporal'))]``
    """

    def __init__(
        self,
        data: Data,
        update_interval: timedelta64,
        start_time: datetime64,
        **kwargs: Any,
    ):
        self.data = data
        """A Data instance providing access to the shared simulation data."""
        self.update_interval = update_interval
        """The time interval between model updates."""
        self.next_update = start_time + update_interval
        """The simulation time at which the model should next run the update method"""
        self._repr = ["update_interval", "next_update"]
        """A list of attributes to be included in the class __repr__ output"""

        # Check the required init variables
        self.check_required_init_vars()

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
    def from_config(cls, data: Data, config: dict[str, Any]) -> Any:
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

        if not isinstance(cls.model_name, str):
            excep = TypeError("Models should only be named using strings!")
            LOGGER.error(excep)
            raise excep

        # Check that required_init_vars is set - not testing structure here
        if not hasattr(cls, "required_init_vars"):
            excep = ValueError("BaseModel subclasses must define required_init_vars")
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

    def check_required_init_vars(self) -> None:
        """Check the required set of variables is present.

        This method is used to check that the set of variables defined in the
        :attr:`~virtual_rainforest.core.model.BaseModel.required_init_vars` class
        attribute are present in the :attr:`~virtual_rainforest.core.data.Data` instance
        used to create a new instance of the class.

        Raises:
            ValueError: If the Data instance does not contain all the required variables
                or if those variables do not map onto the required axes.
        """

        # Sentinel variables
        all_axes_ok: bool = True
        all_vars_found: bool = True

        # Loop over the required  and axes
        for var, axes in self.required_init_vars:
            # Record when a variable is missing
            if var not in self.data:
                LOGGER.error(
                    f"Required init variable '{var}' missing from data in "
                    "{self.model_name} model."
                )
                all_vars_found = False
                continue

            # Check for required axes
            for axis in axes:
                axis_ok = self.data.on_core_axis(var, axis)

                if not axis_ok:
                    LOGGER.error(
                        f"Required init variable '{var}' not on core axis '{axis}' in "
                        "{self.model_name} model."
                    )

                    all_axes_ok = False

        # Raise if any problems found
        if not (all_axes_ok and all_vars_found):
            raise ValueError(
                "Required init variables missing or not on core axes in "
                f"{self.model_name} model: see log"
            )
