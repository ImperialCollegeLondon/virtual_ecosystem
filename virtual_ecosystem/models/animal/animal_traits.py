"""The `models.animal.animal_traits` module contains classes that organizes
animal traits into enumerations for use by the Functional Group class in the
:mod:`~virtual_ecosystem.models.animal.functional_group` module.
"""  # noqa: D205

from enum import Enum


class MetabolicType(Enum):
    """Enumeration for metabolic types."""

    ENDOTHERMIC = "endothermic"
    ECTOTHERMIC = "ectothermic"


class DietType(Enum):
    """Enumeration for diet types."""

    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"


class TaxaType(Enum):
    """Enumeration for taxa types."""

    MAMMAL = "mammal"
    BIRD = "bird"
    INSECT = "insect"


class ReproductiveType(Enum):
    """Enumeration for reproductive types."""

    SEMELPAROUS = "semelparous"
    ITEROPAROUS = "iteroparous"
    NONREPRODUCTIVE = "nonreproductive"


class DevelopmentType(Enum):
    """Enumeration for development types."""

    DIRECT = "direct"
    INDIRECT = "indirect"


class DevelopmentStatus(Enum):
    """Enumeration for development status."""

    LARVAL = "larval"
    ADULT = "adult"


class ExcretionType(Enum):
    """Enumeration for excretion type."""

    UREOTELIC = "ureotelic"
    URICOTELIC = "uricotelic"
