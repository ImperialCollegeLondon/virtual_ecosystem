"""Module for all variables."""

from dataclasses import dataclass, field, is_dataclass
from importlib import import_module
from inspect import getmembers

from virtual_rainforest.core.logger import LOGGER


@dataclass
class Variable:
    """Base class for all variables."""

    name: str
    description: str
    units: str
    var_type: str
    axis: tuple[str, ...] = field(default_factory=tuple)
    initialised_by: str = field(default_factory=str, init=False)
    updated_by: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)

    def __call__(self, model_name: str) -> None:
        """Calling the variable populates the registry.

        TODO: Validation of the axis should be added here, currently implemented in
        BaseModel._check_required_init_vars.

        Args:
            model_name: The name of the model that is initialising the variable.
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
            raise ValueError(f"Variable {var.name} already in registry")

        KNOWN_VARIABLES[var.name] = var
        LOGGER.info(
            "Variable registered for %s: %s ",
            module_name,
            var.name,
        )
