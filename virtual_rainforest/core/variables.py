"""Module for all variables."""

from dataclasses import dataclass, field
from importlib import import_module
from inspect import getmembers

from virtual_rainforest.core.axes import AXIS_VALIDATORS
from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.logger import LOGGER


@dataclass
class Variable:
    """Simulation variable, containing static and runtime metadata."""

    name: str
    """Name of the variable. Must be unique."""
    description: str
    """Description of what the variable represents."""
    units: str
    """Unites the variable should be represented in."""
    var_type: str
    """Type of the variable."""
    axis: tuple[str, ...]
    """Axes the variable is defined on."""
    initialised_by: str = field(default_factory=str, init=False)
    """Model that initialised the variable."""
    updated_by: list[str] = field(default_factory=list, init=False)
    """Models that update the variable."""
    used_by: list[str] = field(default_factory=list, init=False)
    """Models that use the variable."""

    def __post_init__(self) -> None:
        """Register the variable in the known variables.

        Raises:
            ValueError: If a variable is already in the known variables registry.
        """
        if self.name in KNOWN_VARIABLES:
            raise ValueError(
                f"Variable {self.name} already in the known variables registry."
            )

        LOGGER.info(
            "Variable registered for %s: %s ",
            self.__module__,
            self.name,
        )

        KNOWN_VARIABLES[self.name] = self


RUN_VARIABLES_REGISTRY: dict[str, Variable] = {}
"""The global registry of variables used in a run."""

KNOWN_VARIABLES: dict[str, Variable] = {}
"""The global known variable registry."""


def register_variables(module_name: str) -> None:
    """Register known variables in the module.

    As variables are global, they are registered in the global KNOWN_VARIABLES registry
    rather than on a per-module basis.

    Args:
        module_name: The name of the module to register variables for.

    Raises:
        ValueError: If a variable is already in the known variables registry.
    """
    try:
        variables_submodule = import_module(f"{module_name}.variables")
    except ModuleNotFoundError:
        LOGGER.info("No variables registered for %s.", module_name)
        return

    list(getmembers(variables_submodule))


def _initialise_variables(models: list[type[BaseModel]]) -> None:
    """Initialise the runtime variable registry.

    Args:
        models: The list of models that are initialising the variables.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or if it is already initialised by another model.
    """
    for model in models:
        for v in model.required_init_vars:
            # TODO In the future, var will be a string, so this won't be necessary
            var_name = v[0]
            if var_name not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var_name} required by {model.model_name} is not in the"
                    " known variables registry."
                )
            if var_name in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var_name} already in registry, initialised by"
                    f"{RUN_VARIABLES_REGISTRY[var_name].initialised_by}."
                )

            KNOWN_VARIABLES[var_name].initialised_by = model.model_name
            RUN_VARIABLES_REGISTRY[var_name] = KNOWN_VARIABLES[var_name]


def _verify_updated_by(models: list[type[BaseModel]]) -> None:
    """Verify that all variables updated by models are in the runtime registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_updated:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the known"
                    " variables registry."
                )
            if var not in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model."
                )
            if len(RUN_VARIABLES_REGISTRY[var].updated_by):
                LOGGER.warning(
                    f"Variable {var} updated by {model.model_name} is already updated"
                    f" by {RUN_VARIABLES_REGISTRY[var].updated_by}."
                )
            RUN_VARIABLES_REGISTRY[var].updated_by.append(model.model_name)


def _verify_used_by(models: list[type[BaseModel]]) -> None:
    """Verify that all variables used by models are in the runtime registry.

    Args:
        models: The list of models to check.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    for model in models:
        for var in model.vars_used:
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the known"
                    " variables registry."
                )
            if var not in RUN_VARIABLES_REGISTRY:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not initialised"
                    " by any model."
                )
            RUN_VARIABLES_REGISTRY[var].used_by.append(model.model_name)


def setup_variables(models: list[type[BaseModel]]) -> None:
    """Setup the runtime variable registry, running some validation.

    Args:
        models: The list of models to setup the registry for.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry or the runtime registry.
    """
    _initialise_variables(models)
    _verify_updated_by(models)
    _verify_used_by(models)


def verify_variables_axis() -> None:
    """Verify that all required variables have valid, available axis."""
    for var in RUN_VARIABLES_REGISTRY.values():
        unknown_axes = set(var.axis).difference(AXIS_VALIDATORS)

        if unknown_axes:
            to_raise = ValueError(
                f"Variable {var.name} uses unknown core: {','.join(unknown_axes)}"
            )
            LOGGER.error(to_raise)
            raise to_raise
