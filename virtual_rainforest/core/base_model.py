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

The :class:`~virtual_rainforest.core.base_model.BaseModel` has four class attributes
that must be defined in subclasses:

* The :attr:`~virtual_rainforest.core.base_model.BaseModel.model_name` attribute and
* The :attr:`~virtual_rainforest.core.base_model.BaseModel.required_init_vars`
  attribute.
* The :attr:`~virtual_rainforest.core.base_model.BaseModel.lower_bound_on_time_scale`
  attribute
* The :attr:`~virtual_rainforest.core.base_model.BaseModel.upper_bound_on_time_scale`
  attribute

The usage of these four attributes is described in their docstrings and three private
methods are provided to validate that the properties are set and valid in subclasses
(:meth:`~virtual_rainforest.core.base_model.BaseModel._check_model_name`,
:meth:`~virtual_rainforest.core.base_model.BaseModel._check_required_init_vars`,
:meth:`~virtual_rainforest.core.base_model.BaseModel._check_time_bounds_units`).

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
from typing import Any

import pint

from virtual_rainforest.core.axes import AXIS_VALIDATORS
from virtual_rainforest.core.config import Config
from virtual_rainforest.core.data import Data
from virtual_rainforest.core.exceptions import ConfigurationError
from virtual_rainforest.core.logger import LOGGER


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
    def lower_bound_on_time_scale(cls) -> str:
        """The shortest time scale for which the model is reasonable to use.

        Whether or not a model is an acceptable representation of reality depends on the
        time scale of interest. At large time scales some processes can be treated as
        transient (and therefore ignored), but at shorter time scales these processes
        can be vital to capture. We thus require each model to define a lower bound on
        the time scale for which it is thought to be a reasonable approximation.
        """

    @property
    @abstractmethod
    def upper_bound_on_time_scale(cls) -> str:
        """The longest time scale for which the model is reasonable to use.

        Whether or not a model is an acceptable representation of reality depends on the
        time scale of interest. Processes that can be sensibly simulated in detail at
        shorter time scales often need to approximated as time scales get longer (e.g.
        impacts of diurnal or seasonal cycles). We thus require each model to define an
        upper bound on the time scale for which it is thought to be a reasonable
        approximation.
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

    @property
    @abstractmethod
    def vars_updated(cls) -> tuple[str, ...]:
        """Variables that are updated by the model.

        At the moment, this tuple is used to decide which variables to output from the
        :class:`~virtual_rainforest.core.data.Data` object, i.e. every variable updated
        by a model used in the specific simulation. In future, this could also be used
        to prevent multiple models from updating the same variable and similar problems.
        """

    def __init__(
        self,
        data: Data,
        update_interval: pint.Quantity,
        **kwargs: Any,
    ):
        """Performs core initialisation for BaseModel subclasses.

        This method should be called by the ``__init__`` method of all subclasses and
        performs the following core steps:

        * It populates the shared instance attributes
          :attr:`~virtual_rainforest.core.base_model.BaseModel.data` and
          :attr:`~virtual_rainforest.core.base_model.BaseModel.update_interval`.
        * It uses the
          :meth:`~virtual_rainforest.core.base_model.BaseModel.check_init_data`
          to confirm that the required variables for the model are present in the
          :attr:`~virtual_rainforest.core.base_model.BaseModel.data` attribute.
        """
        self.data = data
        """A Data instance providing access to the shared simulation data."""
        self.update_interval = self._check_update_speed(update_interval)
        """The time interval between model updates."""
        self._repr = ["update_interval"]
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
    def update(self, time_index: int) -> None:
        """Function to update the model.

        Args:
            time_index: The index representing the current time step in the data object.
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Function to delete objects within the class that are no longer needed."""

    @classmethod
    @abstractmethod
    def from_config(
        cls, data: Data, config: Config, update_interval: pint.Quantity
    ) -> BaseModel:
        """Factory function to unpack config and initialise a model instance."""

    @classmethod
    def _check_model_name(cls) -> None:
        """Check the model_name property is set and valid.

        Raises:
            NotImplementedError: model_name has not been set in a subclass
            ValueError: the model_name is not a string.
        """

        # Check that model_name exists and is a string - if it is not implemented in the
        # subclass then the object will be of type property
        if isinstance(cls.model_name, property):
            excep = NotImplementedError(
                f"Property model_name is not implemented in {cls.__name__}"
            )
            LOGGER.error(excep)
            raise excep

        if not isinstance(cls.model_name, str):
            excep = TypeError(f"Property model_name in {cls.__name__} is not a string")
            LOGGER.error(excep)
            raise excep

    @classmethod
    def _check_required_init_vars(cls) -> None:
        """Check the required_init_vars property is set and valid.

        Raises:
            NotImplementedError: required_init_vars has not been set in a subclass.
            TypeError: the value of required_init_vars has the wrong type structure.
            ValueError: required_init_vars uses unknown core axis names.
        """

        to_raise: Exception

        # Check that required_init_vars is set
        if isinstance(cls.required_init_vars, property):
            to_raise = NotImplementedError(
                f"Property required_init_vars is not implemented in {cls.__name__}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check the structure
        required_init_vars_ok = True
        unknown_axes: list[str] = []

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
                else:
                    # Add any unknown axes
                    unknown_axes.extend(set(axes).difference(AXIS_VALIDATORS))

        if not required_init_vars_ok:
            to_raise = TypeError(
                f"Property required_init_vars has the wrong structure in {cls.__name__}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        if unknown_axes:
            to_raise = ValueError(
                f"Property required_init_vars uses unknown core "
                f"axes in {cls.__name__}: {','.join(unknown_axes)}"
            )
            LOGGER.error(to_raise)
            raise to_raise

    @classmethod
    def _check_time_bounds_units(
        cls, which: str = "lower_bound_on_time_scale"
    ) -> pint.Quantity:
        """Check that the time bounds defined by each model have time units.

        Args:
            which: Which bound should be checked (i.e. lower or upper)

        Raises:
            NotImplementedError: If either of the bounds is not defined
            ValueError: If model time bounds either don't have units or have non-time
                units

        Returns:
            The requested time scale bound
        """

        # First check that upper and lower bounds are set
        if isinstance(getattr(cls, which), property):
            to_raise: Exception = NotImplementedError(
                f"Property {which} is not implemented in {cls.__name__}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Assume time bound has valid units until we learn otherwise
        valid_bound = True

        # Making bound naming nicer so that it can be printed
        if which == "lower_bound_on_time_scale":
            bound_name = "Lower bound"
        elif which == "upper_bound_on_time_scale":
            bound_name = "Upper bound"

        # Check unit for lower bound first
        try:
            bound = pint.Quantity(getattr(cls, which))
            if not bound.check("[time]"):
                LOGGER.error(f"{bound_name} for {cls.__name__} given a non-time unit.")
                valid_bound = False
        except pint.errors.UndefinedUnitError:
            LOGGER.error(f"{bound_name} for {cls.__name__} not given a valid unit.")
            valid_bound = False

        if not valid_bound:
            to_raise = ValueError(
                "Invalid units for model time bound, see above errors."
            )
            LOGGER.error(to_raise)
            raise to_raise
        else:
            return bound

    def _check_update_speed(self, update_interval: pint.Quantity) -> pint.Quantity:
        """Function to check that the update speed of a specific model is within bounds.

        Args:
            update_interval: Simulation update interval

        Returns:
            The update interval for the overall model

        Raises:
            ConfigurationError: If the update interval does not fit with the model's
                time bounds
        """

        # Check if either bound is violated
        if update_interval < pint.Quantity(self.lower_bound_on_time_scale):
            to_raise = ConfigurationError(
                "The update interval is shorter than the model's lower bound"
            )
            LOGGER.error(to_raise)
            raise to_raise
        elif update_interval > pint.Quantity(self.upper_bound_on_time_scale):
            to_raise = ConfigurationError(
                "The update interval is longer than the model's upper bound"
            )
            LOGGER.error(to_raise)
            raise to_raise

        return update_interval

    @classmethod
    def _check_vars_updated(cls) -> None:
        """Check that vars_updated has been set properly.

        Raises:
            NotImplementedError: vars_updated has not been set in a subclass
        """

        # Check that vars_updated is set
        if isinstance(cls.vars_updated, property):
            to_raise = NotImplementedError(
                f"Property vars_updated is not implemented in {cls.__name__}"
            )
            LOGGER.error(to_raise)
            raise to_raise

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

        try:
            cls._check_model_name()
            cls._check_required_init_vars()
            cls._check_vars_updated()
            lower_bound = cls._check_time_bounds_units("lower_bound_on_time_scale")
            upper_bound = cls._check_time_bounds_units("upper_bound_on_time_scale")
            # Once bounds units are checked their relative values can be validated
            if upper_bound <= lower_bound:
                to_raise = ValueError(
                    f"Lower time bound for {cls.__name__} is not less than the upper "
                    f"bound."
                )
                LOGGER.error(to_raise)
                raise to_raise
        except (NotImplementedError, TypeError, ValueError) as excep:
            LOGGER.critical(f"Errors in {cls.__name__} class properties: see log")
            raise excep

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
