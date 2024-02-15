"""Module for all variables."""

from dataclasses import dataclass


@dataclass
class Variable:
    """Base class for all variables."""

    name: str
    description: str
    units: str

    def __post_init__(self) -> None:
        """Post init populates the registry."""
        if self.name in VARIABLES_REGISTRY:
            raise ValueError(f"Variable {self.name} already in registry")

        VARIABLES_REGISTRY[self.name] = self


VARIABLES_REGISTRY: dict[str, Variable] = {}
