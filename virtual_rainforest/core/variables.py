"""Module for all variables."""

from dataclasses import dataclass


@dataclass
class Variable:
    """Base class for all variables."""

    name: str
    description: str
    units: str
    var_type: str
    axis: tuple[str, ...]
    initialised_by: str
    updated_by: list[str]
    used_by: list[str]

    def __call__(self) -> None:
        """Calling the variable populates the registry."""
        if self.name in VARIABLES_REGISTRY:
            raise ValueError(f"Variable {self.name} already in registry")

        VARIABLES_REGISTRY[self.name] = self


VARIABLES_REGISTRY: dict[str, Variable] = {}
