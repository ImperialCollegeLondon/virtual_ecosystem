"""Module for all variables."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Variable:
    """Base class for all variables."""

    name: str = field(init=False)
    descritpion: str = field(init=False)
    units: str = field(init=False)

    def __init_subclass__(cls, name: str, descritpion: str, units: str) -> None:
        """Checks if the variable class is unique and registers it.

        Args:
            name (str): Name of the variable.
            descritpion (str): Description of the variable.
            units (str): Units to use for the variable across the project.

        Raises:
            ValueError: If a variable class with the same name is already registered.
            ValueError: If a variable with the same name field is already registered.
        """
        cls.name = name
        cls.descritpion = descritpion
        cls.units = units

        if cls.__name__ in _UNIQUE_VARIABLES_CLASSES:
            raise ValueError(f"Variable class {cls.__name__} already registered.")

        if cls.name in _UNIQUE_VARIABLES_NAMES:
            raise ValueError(f"Variable name {cls.name} already registered.")

        _UNIQUE_VARIABLES_CLASSES.append(cls.__name__)
        _UNIQUE_VARIABLES_NAMES.append(cls.name)

    def __new__(cls) -> "Variable":
        """Creates a new variable of this type or returns an existing one.

        Returns:
            Variable: The new or existing variable of this type.
        """
        if cls.name not in VARIABLES_REGISTRY:
            VARIABLES_REGISTRY[cls.name] = super().__new__(cls)

        return VARIABLES_REGISTRY[cls.name]

    def __setattr__(self, __name: str, __value: Any) -> None:
        """Raises an error if a variable is changed.

        While we could use `frozen=True` in the dataclass, that will only prevent
        modifying the existing attributes, but will not prevent adding new ones.
        Overwritting __setattr__ is the way to prevent that both. Using `slots=True`
        does not play well with `__init_subclass__`.
        """
        raise TypeError("Variables are immutable.")


_UNIQUE_VARIABLES_CLASSES: list[str] = []
_UNIQUE_VARIABLES_NAMES: list[str] = []
VARIABLES_REGISTRY: dict[str, Variable] = {}


class Temperature(Variable, name="temperature", descritpion="Temperature", units="K"):
    """Temperature variable."""


class Pressure(Variable, name="pressure", descritpion="Pressure", units="Pa"):
    """Pressure variable."""


if __name__ == "__main__":
    print(_UNIQUE_VARIABLES_CLASSES)
    print(_UNIQUE_VARIABLES_NAMES)

    T = Temperature()
    P = Pressure()

    T2 = Temperature()
    P2 = Pressure()

    print(VARIABLES_REGISTRY)

    assert T is T2
    assert P is P2
    assert T == T2
    assert P == P2

    # These should raise an error
    # T.name = "T2"
    # T.somehting = 42
