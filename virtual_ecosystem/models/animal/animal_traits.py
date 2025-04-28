"""The `models.animal.animal_traits` module contains classes that organizes
animal traits into enumerations for use by the Functional Group class in the
:mod:`~virtual_ecosystem.models.animal.functional_group` module.
"""  # noqa: D205

from enum import Enum, Flag, auto


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
    AMPHIBIAN = "amphibian"


class ReproductiveType(Enum):
    """Enumeration for reproductive types."""

    SEMELPAROUS = "semelparous"
    ITEROPAROUS = "iteroparous"
    NONREPRODUCTIVE = "nonreproductive"


class ReproductiveEnvironment(Enum):
    """Where and how reproduction happens: aquatic vs terrestrial."""

    TERRESTRIAL = "terrestrial"
    AQUATIC = "aquatic"


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


class MigrationType(Enum):
    """Enumeration for external migration trait."""

    NONE = "none"
    SEASONAL = "seasonal"


class VerticalOccupancy(Flag):
    """Enumeration for vertical occupancy trait."""

    SOIL = auto()
    GROUND = auto()
    CANOPY = auto()

    @classmethod
    def parse(cls, occupancy: str) -> "VerticalOccupancy":
        """Convert a string like 'soil_ground' into a VerticalOccupancy flag.

        This method parses a lowercase underscore-separated string into a combined
        VerticalOccupancy flag using bitwise OR logic. It enables easy construction
        of multi-layer occupancy traits from a single string field, such as those
        found in CSV imports or config files.

        Args:
            occupancy: A string representing one or more vertical layers, such as
                'soil', 'ground_canopy', or 'soil_ground_canopy'.

        Returns:
            A VerticalOccupancy flag representing the combined vertical occupancy.
        """

        occupancy_list = occupancy.split("_")
        occupancy_flags = getattr(cls, occupancy_list.pop(0).upper())
        for oc in occupancy_list:
            occupancy_flags = occupancy_flags | getattr(cls, oc.upper())

        return occupancy_flags
