"""The `models.animals.animal_traits` module contains classes that organize
animal traits into enumerations for use by the Functional Group class in the
:mod:`~virtual_rainforest.models.animals.functional_group` module.
"""  # noqa: D205, D415

from enum import Enum, auto


class MetabolicType(Enum):
    """Enumeration for metabolic types."""

    ENDOTHERMIC = auto()
    ECTOTHERMIC = auto()

    @classmethod
    def from_str(cls, value: str) -> "MetabolicType":
        """Create a `MetabolicType` enumeration member from its string representation.

        Args:
            value: The string representation of the metabolic type.

        Returns:
            The corresponding `MetabolicType` enumeration member.

        Raises:
            ValueError: If the provided string does not match any valid metabolic type.
        """
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid metabolic type: {value}")


class DietType(Enum):
    """Enumeration for diet types."""

    HERBIVORE = auto()
    CARNIVORE = auto()

    @classmethod
    def from_str(cls, value: str) -> "DietType":
        """Create a `DietType` enumeration member from its string representation.

        Args:
            value: The string representation of the metabolic type.

        Returns:
            The corresponding `DietType` enumeration member.

        Raises:
            ValueError: If the provided string does not match any valid diet type.
        """
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid diet type: {value}")


class TaxaType(Enum):
    """Enumeration for taxa types."""

    MAMMAL = auto()
    BIRD = auto()
    INSECT = auto()

    @classmethod
    def from_str(cls, value: str) -> "TaxaType":
        """Create a `TaxaType` enumeration member from its string representation.

        Args:
            value: The string representation of the taxa type.

        Returns:
            The corresponding `TaxaType` enumeration member.

        Raises:
            ValueError: If the provided string does not match any valid taxa type.
        """
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid taxa type: {value}")
