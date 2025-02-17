"""The :mod:`~virtual_ecosystem.core.base_model` module defines the high level API for
the different models within the Virtual Ecosystem. The module creates the
:class:`~virtual_ecosystem.core.base_model.BaseModel` abstract base class (ABC) which
defines a consistent API for subclasses defining an actual model. The API defines
abstract methods for each of the key stages in the workflow of running a model:
individual subclasses are **required** to provide model specific implementations for
each stage, although the specific methods may simply do nothing if no action is needed
at that stage. The stages are:

* Creating a model instance (:class:`~virtual_ecosystem.core.base_model.BaseModel`).
* Setup a model instance (:meth:`~virtual_ecosystem.core.base_model.BaseModel._setup`).
  This method should include any initialization logic including validating and
  populating class attributes.
* Perform any spinup required to get a model state to equilibrate
  (:meth:`~virtual_ecosystem.core.base_model.BaseModel.spinup`).
* Update the model from one time step to the next
  :meth:`~virtual_ecosystem.core.base_model.BaseModel.update`).
* Cleanup any unneeded resources at the end of a simulation
  (:meth:`~virtual_ecosystem.core.base_model.BaseModel.cleanup`).

The :class:`~virtual_ecosystem.core.base_model.BaseModel` class also provides default
implementations for the :meth:`~virtual_ecosystem.core.base_model.BaseModel.__repr__`
and :meth:`~virtual_ecosystem.core.base_model.BaseModel.__str__` special methods.

Declaring new subclasses
------------------------

The :class:`~virtual_ecosystem.core.base_model.BaseModel` has the following class
attributes that must be specified as arguments to the subclass declaration:

* :attr:`~virtual_ecosystem.core.base_model.BaseModel.model_name`,
* :attr:`~virtual_ecosystem.core.base_model.BaseModel.vars_required_for_init`,
* :attr:`~virtual_ecosystem.core.base_model.BaseModel.vars_populated_by_init`,
* :attr:`~virtual_ecosystem.core.base_model.BaseModel.vars_required_for_update`,
* :attr:`~virtual_ecosystem.core.base_model.BaseModel.vars_updated`,
* :attr:`~virtual_ecosystem.core.base_model.BaseModel.model_update_bounds` and
* :attr:`~virtual_ecosystem.core.base_model.BaseModel.vars_updated`.

This behaviour is defined in the :meth:`BaseModel.__init_subclass__()
<virtual_ecosystem.core.base_model.BaseModel.__init_subclass__>` method, which also
gives example code for declaring a new subclass.

The usage of these attributes is described in their docstrings and each is validated
when a new subclass is created using the following private methods of the class:

* :meth:`~virtual_ecosystem.core.base_model.BaseModel._check_model_name`,
* :meth:`~virtual_ecosystem.core.base_model.BaseModel._check_variables_attribute` and
* :meth:`~virtual_ecosystem.core.base_model.BaseModel._check_model_update_bounds`.

Model checking
--------------

The :class:`~virtual_ecosystem.core.base_model.BaseModel` abstract base class defines
the :func:`~virtual_ecosystem.core.base_model.BaseModel.__init_subclass__` class
method. This method is called automatically whenever a subclass of the ABC is imported
and validates the class attributes for the new model class.

The ``BaseModel.__init__`` method
----------------------------------

Each model subclass should include an ``__init__`` method that defines all
model specific attributes. The ``__init__`` should not contain any further
initialization logic, which should happen in the subclass ``_setup`` method instead.
The ``__init__`` method **must** call the
:meth:`BaseModel.__init__() <virtual_ecosystem.core.base_model.BaseModel.__init__>`
method, as this populates core shared model attrributes - see the linked method
description for details.

.. code-block:: python

    super().__init__(data, core_components)


The ``from_config`` factory method
----------------------------------

The ABC also defines the abstract class method
:func:`~virtual_ecosystem.core.base_model.BaseModel.from_config`. This method must be
defined by subclasses and must be a factory method that returns an instance of the model
subclass. The method must follow the signature of that method, providing:

* ``data`` as an instance of :class:`~virtual_ecosystem.core.data.Data`.
* ``core_components`` as an instance of
  :class:`~virtual_ecosystem.core.core_components.CoreComponents`.
* ``config`` as an instance of
  :class:`~virtual_ecosystem.core.config.Config`.

The method should provide any code to validate the configuration for that model and then
use the configuration to initialise and return a new instance of the class.

Model registration
------------------

Models have three core components: the
:class:`~virtual_ecosystem.core.base_model.BaseModel` subclass itself (``model``),
a JSON schema for validating the model configuration (``schema``) and an optional set of
user modifiable constants classes (``constants``, see
:class:`~virtual_ecosystem.core.constants_class.ConstantsDataclass`). All model
modules must register these components when they are imported: see the
:mod:`~virtual_ecosystem.core.registry` module.
"""  # noqa: D205, D415

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pint

from virtual_ecosystem.core.config import Config
from virtual_ecosystem.core.constants import CoreConsts
from virtual_ecosystem.core.core_components import (
    CoreComponents,
    LayerStructure,
    ModelTiming,
)
from virtual_ecosystem.core.data import Data, Grid
from virtual_ecosystem.core.exceptions import ConfigurationError
from virtual_ecosystem.core.logger import LOGGER


class BaseModel(ABC):
    """A superclass for all Virtual Ecosystem models.

    This abstract base class defines the shared common methods and attributes used as an
    API across all Virtual Ecosystem models. This includes functions to setup, spin up
    and update the specific model, as well as a function to cleanup redundant model
    data.

    The base class defines the core abstract methods that must be defined in subclasses
    as well as shared helper functions.

    Args:
        data: A :class:`~virtual_ecosystem.core.data.Data` instance containing
            variables to be used in the model.
        core_components: A
            :class:`~virtual_ecosystem.core.core_components.CoreComponents`
            instance containing shared core elements used throughout models.
    """

    model_name: str
    """The model name.

    This class attribute sets the name used to refer to identify the model class in
    the :data:`~virtual_ecosystem.core.registry.MODULE_REGISTRY`, within the
    configuration settings and in logging messages.
    """

    model_update_bounds: tuple[pint.Quantity, pint.Quantity]
    """Bounds on model update frequencies.

    This class attribute defines two time intervals that define a lower and upper bound
    on the update frequency that can reasonably be used with a model. Models updated
    more often than the lower bound may fail to capture transient dynamics and models
    updated more slowly than the upper bound may fail to capture important temporal
    patterns.
    """

    vars_required_for_init: tuple[str, ...]
    """Required variables for model initialisation.

    This class property defines a set of variable names that must be present in the
    :class:`~virtual_ecosystem.core.data.Data` instance used to initialise an
    instance of this class. It is a tuple containing zero or more tuples, each
    providing a variable name and then a tuple of zero or more core axes that the
    variable must map onto.

    For example: ``(('temperature', ('spatial', 'temporal')),)``
    """

    vars_updated: tuple[str, ...]
    """Variables that are updated by the model.

    At the moment, this tuple is used to decide which variables to output from the
    :class:`~virtual_ecosystem.core.data.Data` object, i.e. every variable updated
    by a model used in the specific simulation. It is also be used warn if multiple
    models will be updating the same variable and to verify that these variables are
    indeed initialised by another model, and therefore will be available.
    """

    vars_required_for_update: tuple[str, ...]
    """Variables that are required by the update method of the model.

    These variables should have been initialised by another model or loaded from
    external sources, but in either case they will be available in the data object.
    """

    vars_populated_by_init: tuple[str, ...]
    """Variables that are initialised by the model during the setup.

    These are the variables that are initialised by the model and stored in the data
    object when running the setup method and that will be available for other models to
    use in their own setup or update methods.
    """

    vars_populated_by_first_update: tuple[str, ...]
    """Variables that are initialised by the model during the first update.

    These are the variables that are initialised by the model and stored in the data
    object when running the update method for the first time. They will be available for
    other models to use in their update methods but not in the setup methos.
    """

    def __init__(
        self,
        data: Data,
        core_components: CoreComponents,
        static: bool = False,
        **kwargs: Any,
    ):
        """Performs core initialisation for BaseModel subclasses.

        This method **must** be called in the ``__init__`` method of all subclasses.

        It populates a set of shared instance attributes from the provided
        :class:`~virtual_ecosystem.core.core_components.CoreComponents` and
        :class:`~virtual_ecosystem.core.data.Data` value:

        * ``data``: the provided :class:`~virtual_ecosystem.core.data.Data` instance.
        * ``model_timing``: the
          :class:`~virtual_ecosystem.core.core_components.ModelTiming` instance from the
          ``core_components`` argument.
        * ``grid``: the :class:`~virtual_ecosystem.core.grid.Grid` instance from the
          ``core_components`` argument.
        * ``layer_structure``: the
          :class:`~virtual_ecosystem.core.core_components.LayerStructure` instance from
          the ``core_components`` argument.
        * ``core_constants``: the :class:`~virtual_ecosystem.core.constants.CoreConsts`
          instance from the ``core_components`` argument.

        It then uses the
        :meth:`~virtual_ecosystem.core.base_model.BaseModel.check_init_data` method to
        confirm that the required variables for the model are present in the provided
        :attr:`~virtual_ecosystem.core.base_model.BaseModel.data` attribute.
        """
        self.data: Data = data
        """A Data instance providing access to the shared simulation data."""
        self.model_timing: ModelTiming = core_components.model_timing
        """The ModelTiming details used in the model."""
        self.grid: Grid = core_components.grid
        """The Grid details used in the model."""
        self.layer_structure: LayerStructure = core_components.layer_structure
        """The LayerStructure details used in the model."""
        self.core_constants: CoreConsts = core_components.core_constants
        """The core constants used in the model."""
        self._repr: list[tuple[str, ...]] = [("model_timing", "update_interval")]
        """A list of attributes to be included in the class __repr__ output"""
        self._static = static
        """Flag indicating if the model is static, i.e. does not change with time."""

        # Check the required init variables
        self.check_init_data()
        # Check the configured update interval is within model bounds
        self._check_update_speed()
        # Check static configuration
        bypass_setup, run_initial = self._check_static_config()

        self._run_initial_static_update = run_initial
        """Flag indicating if the update method should be run once when model static."""

        if not bypass_setup:
            self._setup(**kwargs)

    def _check_static_config(self) -> tuple[bool, bool]:
        """Check if the static configuration is valid.

        Raises:
            ConfigurationError: If there is any error in the static configuration of the
            model.

        Returns:
            A tuple of two boolean flags indicating if the _setup method should be
            bypassed and the update method should be run, respectively.
        """
        bypass = self._bypass_setup_due_to_static_configuration()
        run = self._run_update_due_to_static_configuration()

        # Bypassing the setup and running the update is not valid
        if bypass and run:
            raise ConfigurationError(
                f"Static model {self.model_name} will not run the setup method, but "
                "requires the update method to run once. This is an invalid "
                "configuration. Please, make sure that either both methods are run once"
                " by not providing any variables in vars_populated_by_first_update and "
                "vars_updated or that both are bypassed by providing all variables in "
                "vars_populated_by_init."
            )

        # Flag indicating if the setup method will setup any variable
        any_var_to_setup = len(self.vars_populated_by_init) > 0
        # Flag indicating if the update method will update any variable
        any_var_to_update = (
            len(self.vars_populated_by_first_update) > 0 or len(self.vars_updated) > 0
        )

        # Running the setup but not the update is only valid if
        # - There are no variables to setup (setup is always run in this case), or
        # - There are no variables to update (unusual case)
        if not bypass and not run and any_var_to_setup and any_var_to_update:
            raise ConfigurationError(
                f"Static model {self.model_name} will run the setup method, but "
                "not the update method. This is an invalid configuration. "
                "Please, make sure that either both methods are run once"
                " by not providing any variables in vars_populated_by_init or that both"
                " are bypassed by providing all variables in "
                "vars_populated_by_first_update and vars_updated."
            )
        return bypass, run

    def _bypass_setup_due_to_static_configuration(self) -> bool:
        """Decide if the setup should be bypassed based on the static flag.

        In particular, it checks that the appropriate variables populated by init are
        present or not in the data object. Based on this, an exception is raised is
        there is a problem or a decision is made on whether or not bypass the setup.

        Raises:
            ConfigurationError: If the model is static and some but not all the
                variables or None in vars_populated_by_init are present in the data
                object or if the model is not static and some of the variables in
                vars_populated_by_init are not present in the data object.

        Returns:
            True if the model is static and all variables are present, such that the
            setup method can be bypassed. False otherwise.
        """
        present = [var for var in self.vars_populated_by_init if var in self.data]
        found = len(present)
        expected = len(self.vars_populated_by_init)

        if not self._static and present:
            raise ConfigurationError(
                f"Non-static model {self.model_name} requires none of the variables in "
                "vars_populated_by_init to be present in the data object. "
                f"Present variables: {', '.join(present)}"
            )

        elif self._static:
            if 0 < found < expected:
                raise ConfigurationError(
                    f"Static model {self.model_name} requires to either all variables "
                    "in vars_populated_by_init to be present in the data object or "
                    f"all to be absent. {found} out of {expected} found: "
                    f"{', '.join(present)}."
                )
            elif found == 0:
                # The case when static is true and no init vars provided
                return False
            else:
                # The case when static is true and all init vars provided
                return True

        return False

    def _run_update_due_to_static_configuration(self) -> bool:
        """Decides if the update should be bypassed based on the static flag.

        In particular, it checks that the appropriate variables created or updated in
        the update method are present or not in the data object. Based on this, an
        exception is raised is there is a problem or a decission is made on whether or
        not running the update method once.

        Raises:
            ConfigurationError: If the model is static and some but not all the
                variables or None in vars_populated_by_first_update or vars_updated are
                present in the data object or if the model is not static and some of the
                variables in vars_populated_by_init are not present in the data object.

        Returns:
            True if the model is static and the update method needs to run once. False
            otherwise.
        """
        required = set(self.vars_populated_by_first_update + self.vars_updated) - set(
            self.vars_required_for_init
        )
        present = [var for var in required if var in self.data]
        found = len(present)
        expected = len(required)

        if not self._static and present:
            raise ConfigurationError(
                f"Non-static model {self.model_name} requires none of the variables in "
                "vars_populated_by_first_update or vars_updated to be present in the "
                f"data object. Present variables: {', '.join(present)}"
            )

        elif self._static:
            if found == 0 and expected > 0:
                return True
            elif found == expected:
                return False
            else:
                raise ConfigurationError(
                    f"Static model {self.model_name} requires to either all variables "
                    "in vars_populated_by_first_update and vars_updated to be present "
                    f"in the data object or all to be absent. {found} out of {expected}"
                    f" found: {', '.join(present)}."
                )

        return True

    @abstractmethod
    def _setup(self, *args: Any, **kwargs: Any) -> None:
        """Function to setup the model during initialisation."""

    @abstractmethod
    def spinup(self) -> None:
        """Function to spin up the model."""

    def update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the model.

        If the model is static, the inner update method, self._update will only run
        once, at most.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """
        if self._static:
            if not self._run_initial_static_update:
                return
            else:
                self._run_initial_static_update = False

        self._update(time_index, **kwargs)

    @abstractmethod
    def _update(self, time_index: int, **kwargs: Any) -> None:
        """Function to update the model.

        Args:
            time_index: The index representing the current time step in the data object.
            **kwargs: Further arguments to the update method.
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Function to delete objects within the class that are no longer needed."""

    @classmethod
    @abstractmethod
    def from_config(
        cls, data: Data, core_components: CoreComponents, config: Config
    ) -> BaseModel:
        """Factory function to unpack config and initialise a model instance."""

    @classmethod
    def _check_model_name(cls, model_name: str) -> str:
        """Check the model_name attribute is valid.

        Args:
            model_name: The
                :attr:`~virtual_ecosystem.core.base_model.BaseModel.model_name`
                attribute to be used for a subclass.

        Raises:
            ValueError: the model_name is not a string.

        Returns:
            The provided ``model_name`` if valid
        """

        if not isinstance(model_name, str):
            excep = TypeError(
                f"Class attribute model_name in {cls.__name__} is not a string"
            )
            LOGGER.error(excep)
            raise excep

        return model_name

    @classmethod
    def _check_variables_attribute(
        cls,
        variables_attribute_name: str,
        variables_attribute_value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Check a model variables attribute property is valid.

        Creating an instance of the BaseModel class requires that several variables
        attributes are set. Each of these provides a list of variable names that are
        required or updated by the model at various points. This method is used to
        validate the structure of the new instance and ensure the resulting model
        structure is consistent.

        Args:
            variables_attribute_name: The name of the variables attribute
            variables_attribute_value: The provided value for the variables attribute

        Raises:
            TypeError: the value of the model variables attribute has the wrong type
                structure.

        Returns:
            The validated variables attribute value
        """

        # Check the structure
        if isinstance(variables_attribute_value, tuple) and all(
            isinstance(vname, str) for vname in variables_attribute_value
        ):
            return variables_attribute_value

        to_raise = TypeError(
            f"Class attribute {variables_attribute_name} has the wrong "
            f"structure in {cls.__name__}"
        )
        LOGGER.error(to_raise)
        raise to_raise

    @classmethod
    def _check_model_update_bounds(
        cls, model_update_bounds: tuple[str, str]
    ) -> tuple[pint.Quantity, pint.Quantity]:
        """Check that the model_update_bounds attribute is valid.

        This is used to validate the class attribute
        :attr:`~virtual_ecosystem.core.base_model.BaseModel.model_update_bounds`, which
        describes the lower and upper bounds on model update frequency. The lower bound
        must be less than the upper bound.

        Args:
            model_update_bounds: A tuple of two strings representing time periods that
                can be parsed using :class:`pint.Quantity`.


        Raises:
            ValueError: If the provided model_update_bounds cannot be parsed as
                :class:`pint.Quantity` with time units or if the lower bound is not less
                than the upper bound.

        Returns:
            The validated model_update_bounds, converted to a tuple of
            :class:`pint.Quantity` values.
        """

        # Check the conversion
        try:
            model_update_bounds_pint: tuple[pint.Quantity, pint.Quantity] = (
                pint.Quantity(model_update_bounds[0]),
                pint.Quantity(model_update_bounds[1]),
            )
        except pint.errors.UndefinedUnitError:
            to_raise = ValueError(
                f"Class attribute model_update_bounds for {cls.__name__} "
                "contains undefined units."
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check time units
        if not all(val.check("[time]") for val in model_update_bounds_pint):
            to_raise = ValueError(
                f"Class attribute model_update_bounds for {cls.__name__} "
                "contains non-time units."
            )
            LOGGER.error(to_raise)
            raise to_raise

        # Check lower less than upper bound
        if model_update_bounds_pint[0] >= model_update_bounds_pint[1]:
            to_raise = ValueError(
                f"Lower time bound for {cls.__name__} is not less than the upper bound."
            )
            LOGGER.error(to_raise)
            raise to_raise

        return model_update_bounds_pint

    def _check_update_speed(self) -> None:
        """Method to check that the configure update speed is within the model bounds.

        Raises:
            ConfigurationError: If the update interval does not fit with the model's
                time bounds
        """

        # Check if either bound is violated
        if self.model_timing.update_interval_quantity < self.model_update_bounds[0]:
            to_raise = ConfigurationError(
                f"The update interval is faster than the {self.model_name} "
                f"lower bound of {self.model_update_bounds[0]}."
            )
            LOGGER.error(to_raise)
            raise to_raise

        if self.model_timing.update_interval_quantity > self.model_update_bounds[1]:
            to_raise = ConfigurationError(
                f"The update interval is slower than the {self.model_name} "
                f"upper bound of {self.model_update_bounds[1]}."
            )
            LOGGER.error(to_raise)
            raise to_raise

    @classmethod
    def __init_subclass__(
        cls,
        model_name: str,
        model_update_bounds: tuple[str, str],
        vars_required_for_init: tuple[str, ...],
        vars_updated: tuple[str, ...],
        vars_required_for_update: tuple[str, ...],
        vars_populated_by_init: tuple[str, ...],
        vars_populated_by_first_update: tuple[str, ...],
    ) -> None:
        """Initialise subclasses deriving from BaseModel.

        This method runs when a new BaseModel subclass is imported. It adds the new
        subclasses to the model registry and populates the values of the class
        attributes.

        Subclasses of the BaseModel need to provide the values for class attributes in
        their signatures. Those values are defined by the arguments to this method,
        which validates and sets the class attributes for the subclass. See
        :class:`~virtual_ecosystem.core.base_model.BaseModel` for details on the class
        attributes. For example:

        .. code-block:: python

            class ExampleModel(
                BaseModel,
                model_name='example',
                model_update_bounds= ("30 minutes", "3 months"),
                vars_required_for_init=(("required_variable", ("spatial",)),),
                vars_updated=("updated_variable"),
            ):
                ...

        Args:
            model_name: The model name to be used
            model_update_bounds: Bounds on update intervals handled by the model
            vars_required_for_init: A tuple of the variables required to create a model
                instance.
            vars_populated_by_init: A tuple of the variables initialised when a model
                instance is created.
            vars_populated_by_first_update: A tuple of the variables initialised when a
                model update method first run.
            vars_required_for_update: A tuple of the variables required to update a
                model instance.
            vars_updated: A tuple of the variable names updated by the model.

        Raises:
            ValueError: If the model_name or vars_required_for_init properties are not
                defined
            TypeError: If model_name is not a string
        """

        if cls.update != BaseModel.update:
            raise NotImplementedError(
                "Model subclasses cannot override the update method."
            )

        try:
            cls.model_name = cls._check_model_name(model_name=model_name)

            # Validate the structure of the variables attributes
            for name, attr in (
                ("vars_required_for_init", vars_required_for_init),
                ("vars_populated_by_init", vars_populated_by_init),
                ("vars_required_for_update", vars_required_for_update),
                ("vars_updated", vars_updated),
                ("vars_populated_by_first_update", vars_populated_by_first_update),
            ):
                setattr(cls, name, cls._check_variables_attribute(name, attr))

            cls.model_update_bounds = cls._check_model_update_bounds(
                model_update_bounds=model_update_bounds
            )

        except (NotImplementedError, TypeError, ValueError) as excep:
            LOGGER.critical(
                f"Errors in defining {cls.__name__} class attributes: see log"
            )
            raise excep

    def __repr__(self) -> str:
        """Represent a Model as a string from the attributes listed in _repr.

        Each entry in self._repr is a tuple of strings providing a path through the
        model hierarchy. The method assembles the tips of each path into a repr string.
        """

        repr_elements: list[str] = []

        for repr_entry in self._repr:
            obj = self
            for attr in repr_entry:
                obj = getattr(obj, attr)
            repr_elements.append(f"{attr}={obj}")

        # Add all args to the function signature
        repr_string = ", ".join(repr_elements)

        return f"{self.__class__.__name__}({repr_string})"

    def __str__(self) -> str:
        """Inform user what the model type is."""
        return f"A {self.model_name} model instance"

    def check_init_data(self) -> None:
        """Check the init data contains the required variables.

        This method is used to check that the set of variables defined in the
        :attr:`~virtual_ecosystem.core.base_model.BaseModel.vars_required_for_init`
        class attribute are present in the :attr:`~virtual_ecosystem.core.data.Data`
        instance used to create a new instance of the class.

        Raises:
            ValueError: If the Data instance does not contain all the required variables
                or if those variables do not map onto the required axes.
        """

        # Sentinel variables
        # all_axes_ok: bool = True
        all_vars_found: bool = True

        # Loop over the required  and axes
        for var in self.vars_required_for_init:
            # Record when a variable is missing
            if var not in self.data:
                LOGGER.error(
                    f"{self.model_name} model: init data missing required var '{var}'"
                )
                all_vars_found = False
                continue

            # # Get a list of missing axes
            # bad_axes = []
            # # Could use try: here and let on_core_axis report errors but easier to
            # # provide more clearly structured feedback this way
            # for axis in axes:
            #     if not self.data.on_core_axis(var, axis):
            #         bad_axes.append(axis)

            # Log the outcome
            # if bad_axes:
            #     LOGGER.error(
            #         f"{self.model_name} model: required var '{var}' "
            #         f"not on required axes: {','.join(bad_axes)}"
            #     )
            #     all_axes_ok = False
            # else:

            LOGGER.debug(f"{self.model_name} model: required var '{var}' checked")

        # Raise if any problems found
        if not (all_vars_found):
            error = ValueError(
                f"{self.model_name} model: error checking vars_required_for_init, "
                "see log."
            )
            LOGGER.error(error)
            raise error
