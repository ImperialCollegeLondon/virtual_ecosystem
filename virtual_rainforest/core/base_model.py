"""The :mod:`~virtual_rainforest.core.base_model` module defines the high level API for
the different models within the Virtual Rainforest. The module creates the
:class:`~virtual_rainforest.core.base_model.BaseModel` abstract base class (ABC) which
defines a consistent API for subclasses defining an actual model. The API defines
abstract methods for each of the key stages in the workflow of running a model:
individual subclasses are **required** to provide model specific implementations for
each stage, although the specific methods may simply do nothing if no action is needed
at that stage. The stages are:

* Creating a model instance (:class:`~virtual_rainforest.core.base_model.BaseModel`).
* Setup a model instance (:meth:`~virtual_rainforest.core.base_model.BaseModel.setup`).
* Perform any spinup required to get a model state to equilibrate
  (:meth:`~virtual_rainforest.core.base_model.BaseModel.spinup`).
* Update the model from one time step to the next
  :meth:`~virtual_rainforest.core.base_model.BaseModel.update`).
* Cleanup any unneeded resources at the end of a simulation
  (:meth:`~virtual_rainforest.core.base_model.BaseModel.cleanup`).

The :class:`~virtual_rainforest.core.base_model.BaseModel` class also provides default
implementations for the :meth:`~virtual_rainforest.core.base_model.BaseModel.__repr__`
and :meth:`~virtual_rainforest.core.base_model.BaseModel.__str__` special methods.

The :class:`~virtual_rainforest.core.base_model.BaseModel` has two class attributes that
must be defined in subclasses:

* The :attr:`~virtual_rainforest.core.base_model.BaseModel.model_name` atttribute and
* The :attr:`~virtual_rainforest.core.base_model.BaseModel.required_init_vars`
  attribute.

The usage of these two attributes is described in their docstrings.

Model registration
------------------

The :class:`~virtual_rainforest.core.base_model.BaseModel` abstract base class defines
the :func:`~virtual_rainforest.core.base_model.BaseModel.__init_subclass__` class
method. This method is called automatically whenever a subclass of the ABC is imported:
it validates the class attributes for the new class and then registers the model name
and model class in the called :attr:`~virtual_rainforest.core.base_model.MODEL_REGISTRY`
register. This registry is used to identify requested model subclasses from the
configuration details from  Virtual Rainforest simulation.

The ``BaseModel.__init__`` method
----------------------------------

The ``__init__`` method for subclasses **must** call the ``BaseModel``
:meth:`~virtual_rainforest.core.base_model.BaseModel.__init__` method as shown below.
This method carries out some core initialisation steps: see the method description for
details.

.. code-block:: python

    super().__init__(data, update_interval, start_time, **kwargs)


The ``from_config`` factory method
----------------------------------

The ABC also defines the abstract class method
:func:`~virtual_rainforest.core.base_model.BaseModel.from_config`. This method must be
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

from virtual_rainforest.core.axes import AXIS_VALIDATORS
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

    @property
    @abstractmethod
    def model_name(cls) -> str:
        """The model name.

        This class property sets the name used to refer to identify the model class in
        the :data:`~virtual_rainforest.core.base_model.MODEL_REGISTRY`, within the
        configuration settings and in logging messages.
        """

    @property
    @abstractmethod
    def required_init_vars(cls) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Required variables for model initialisation.

        This class property defines a set of variable names that must be present in the
        :class:`~virtual_rainforest.core.data.Data` instance used to initialise an
        instance of this class. It is a tuple containing zero or more tuples, each
        providing a variable name and then a tuple of zero or more core axes that the
        variable must map onto.

        For example: ``(('temperature', ('spatial', 'temporal')),)``
        """

    def __init__(
        self,
        data: Data,
        update_interval: timedelta64,
        start_time: datetime64,
        **kwargs: Any,
    ):
        """Performs core initialisation for BaseModel subclasses.

        This method should be called by the ``__init__`` method of all subclasses and
        performs the following core steps:

        * It populates the shared instance attributes
          :attr:`~virtual_rainforest.core.base_model.BaseModel.data`,
          :attr:`~virtual_rainforest.core.base_model.BaseModel.next_update` and
          :attr:`~virtual_rainforest.core.base_model.BaseModel.update_interval`.
        * It uses the
          :meth:`~virtual_rainforest.core.base_model.BaseModel.check_required_init_vars`
          to confirm that the required variables for the model are present in the
          :attr:`~virtual_rainforest.core.base_model.BaseModel.data` attribute.
        """
        self.data = data
        """A Data instance providing access to the shared simulation data."""
        self.update_interval = update_interval
        """The time interval between model updates."""
        self.next_update = start_time + update_interval
        """The simulation time at which the model should next run the update method"""
        self._repr = ["update_interval", "next_update"]
        """A list of attributes to be included in the class __repr__ output"""

        # Check the required init variables
        self.check_init_data()

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
    def from_config(cls, data: Data, config: dict[str, Any]) -> BaseModel:
        """Factory function to unpack config and initialise a model instance."""

    @classmethod
    def __init_subclass__(cls) -> None:
        """Initialise subclasses deriving from BaseModel.

        This method runs when a new BaseModel subclass is imported. It adds the new
        subclasses to the model registry and validates the values of the class
        properties.

        Raises:
            ValueError: If the model_name or required_init_vars properties are not
                defined
            TypeError: If model_name is not a string
        """

        excep: Exception

        # Check that model_name exists and is a string - if it is not implemented in the
        # subclass then the object will be of type property
        if isinstance(cls.model_name, property):
            excep = NotImplementedError(
                f"Property model_name is not implemented in {cls.__name__}"
            )
            LOGGER.critical(excep)
            raise excep

        if not isinstance(cls.model_name, str):
            excep = TypeError(f"Property model_name in {cls.__name__} is not a string")
            LOGGER.critical(excep)
            raise excep

        # Check that required_init_vars is set
        if isinstance(cls.required_init_vars, property):
            excep = NotImplementedError(
                f"Property required_init_vars is not implemented in {cls.__name__}"
            )
            LOGGER.critical(excep)
            raise excep

        # Check the structure
        required_init_vars_ok = True

        if not isinstance(cls.required_init_vars, tuple):
            required_init_vars_ok = False
        else:
            for entry in cls.required_init_vars:
                # entry is a 2 tuple
                if not (isinstance(entry, tuple) and len(entry) == 2):
                    required_init_vars_ok = False
                    continue
                # and entry contains (str, tuple(str,...))
                vname, axes = entry
                if not (
                    isinstance(vname, str)
                    and isinstance(axes, tuple)
                    and all([isinstance(a, str) for a in axes])
                ):
                    required_init_vars_ok = False

        if not required_init_vars_ok:
            to_raise = TypeError(
                f"Property required_init_vars has the wrong structure in {cls.__name__}"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        # Check the axes are known
        all_axes = set([ax for nm, ax in cls.required_init_vars for ax in ax])
        unknown_axes = all_axes.difference(AXIS_VALIDATORS)
        if unknown_axes:
            to_raise = ValueError(
                f"Property required_init_vars uses unknown core "
                f"axes in {cls.__name__}: {','.join(unknown_axes)}"
            )
            LOGGER.critical(to_raise)
            raise to_raise

        # Add the new model to the registry
        if cls.model_name in MODEL_REGISTRY:
            old_class_name = MODEL_REGISTRY[cls.model_name].__name__
            LOGGER.warning(
                "%s already registered under name '%s', replaced with %s",
                old_class_name,
                cls.model_name,
                cls.__name__,
            )
        else:
            LOGGER.info("%s registered under name '%s'", cls.__name__, cls.model_name)

        MODEL_REGISTRY[cls.model_name] = cls

    def __repr__(self) -> str:
        """Represent a Model as a string."""

        # Add all args to the function signature
        func_sig = ", ".join([f"{k} = {getattr(self, k)}" for k in self._repr])

        return f"{self.__class__.__name__}({func_sig})"

    def __str__(self) -> str:
        """Inform user what the model type is."""
        return f"A {self.model_name} model instance"

    def check_init_data(self) -> None:
        """Check the init data contains the required variables.

        This method is used to check that the set of variables defined in the
        :attr:`~virtual_rainforest.core.base_model.BaseModel.required_init_vars` class
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
                    f"{self.model_name} model: init data missing required var '{var}'"
                )
                all_vars_found = False
                continue

            # Get a list of missing axes
            bad_axes = []
            # Could use try: here and let on_core_axis report errors but easier to
            # provide more clearly structured feedback this way
            for axis in axes:
                if not self.data.on_core_axis(var, axis):
                    bad_axes.append(axis)

            # Log the outcome
            if bad_axes:
                LOGGER.error(
                    f"{self.model_name} model: required var '{var}' "
                    f"not on required axes: {','.join(bad_axes)}"
                )
                all_axes_ok = False
            else:
                LOGGER.debug(f"{self.model_name} model: required var '{var}' checked")

        # Raise if any problems found
        if not (all_axes_ok and all_vars_found):
            error = ValueError(
                f"{self.model_name} model: error checking required_init_vars, see log."
            )
            LOGGER.error(error)
            raise error
