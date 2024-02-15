"""Module for all variables."""

from dataclasses import dataclass, field
from importlib import import_module
from inspect import getmembers

from virtual_rainforest.core.base_model import BaseModel
from virtual_rainforest.core.logger import LOGGER


@dataclass
class Variable:
    """Base class for all variables."""

    name: str
    description: str
    units: str
    var_type: str
    axes: tuple[str, ...] = field(default_factory=tuple)
    initialised_by: str = field(default_factory=str, init=False)
    updated_by: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)

    def initialise(self, model_name: str) -> None:
        """Calling the variable populates the runtime registry.

        Args:
            model_name: The name of the model that is initialising the variable.

        Raises:
            ValueError: If the variable is already in the registry.
        """
        if self.name in RUN_VARIABLES_REGISTRY:
            raise ValueError(
                f"Variable {self.name} already in registry, initialised by"
                f"{RUN_VARIABLES_REGISTRY[self.name].initialised_by}."
            )

        self.initialised_by = model_name
        RUN_VARIABLES_REGISTRY[self.name] = self


RUN_VARIABLES_REGISTRY: dict[str, Variable] = {}
"""The global registry of variables used in a run."""

KNOWN_VARIABLES: dict[str, Variable] = {}
"""The global known variable registry."""


def register_variables(module_name: str) -> None:
    """Register known variables.

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

    for _, var in getmembers(
        variables_submodule, lambda var: isinstance(var, Variable)
    ):
        if var.name in KNOWN_VARIABLES:
            raise ValueError(
                f"Variable {var.name} already in the known variables registry."
            )

        KNOWN_VARIABLES[var.name] = var
        LOGGER.info(
            "Variable registered for %s: %s ",
            module_name,
            var.name,
        )


def initialise_variables(models: list[type[BaseModel]]) -> None:
    """Initialise the runtime variable registry.

    Args:
        models: The list of models that are initialising the variables.

    Raises:
        ValueError: If a variable required by a model is not in the known variables
            registry.
    """
    for model in models:
        for v in model.required_init_vars:
            # TODO In the future, var will be a string, so this won't be necessary
            var = v[0]
            if var not in KNOWN_VARIABLES:
                raise ValueError(
                    f"Variable {var} required by {model.model_name} is not in the known"
                    " variables registry."
                )
            KNOWN_VARIABLES[var].initialise(model.model_name)


def verify_updated_by(models: list[type[BaseModel]]) -> None:
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


def verify_used_by(models: list[type[BaseModel]]) -> None:
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
