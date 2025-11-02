"""The `models.animal.animal_traits` module contains classes that organizes
animal traits into enumerations for use by the Functional Group class in the
:mod:`~virtual_ecosystem.models.animal.functional_group` module.
"""  # noqa: D205

from __future__ import annotations

from enum import Enum, Flag, auto


class MetabolicType(Enum):
    """Enumeration for metabolic types."""

    ENDOTHERMIC = "endothermic"
    ECTOTHERMIC = "ectothermic"


class DietType(Flag):
    """Enumeration for diet resource types.

    TODO: refine categorizations

    """

    ALGAE = auto()
    DETRITUS = auto()
    FLOWERS = auto()
    FOLIAGE = auto()
    FRUIT = auto()
    MUSHROOMS = auto()
    FUNGI = auto()
    SEEDS = auto()
    BLOOD = auto()
    INVERTEBRATES = auto()
    NECTAR = auto()
    FISH = auto()
    CARCASSES = auto()
    VERTEBRATES = auto()
    WASTE = auto()
    WOOD = auto()
    NONFEEDING = auto()
    POM = auto()
    BACTERIA = auto()

    HERBIVORE = (
        ALGAE
        | DETRITUS
        | FLOWERS
        | FOLIAGE
        | FRUIT
        | SEEDS
        | NECTAR
        | WOOD
        | NONFEEDING  # not strictly correct
    )
    CARNIVORE = BLOOD | INVERTEBRATES | FISH | VERTEBRATES | CARCASSES | WASTE
    OMNIVORE = HERBIVORE | CARNIVORE

    @classmethod
    def parse(cls, diet_string: str) -> DietType:
        """Parse a string of underscore-separated diet terms into a DietType flag.

        This method takes a lowercase string such as 'fruit_foliage_fish' and converts
        it into a combined DietType flag using bitwise OR logic. This allows diet
        traits to be specified flexibly in configuration files or CSV inputs.

        Args:
            diet_string: A lowercase underscore-separated string representing one or
              more diet components (e.g., 'foliage', 'fruit_fish', 'nectar_fungus').

        Returns:
            A DietType flag representing the combined diet traits.
        """

        diet_string = diet_string.lower()

        # Handle known composite categories directly
        if diet_string == "herbivore":
            return cls.HERBIVORE
        elif diet_string == "carnivore":
            return cls.CARNIVORE
        elif diet_string == "omnivore":
            return cls.OMNIVORE

        # Otherwise parse individual components
        parts = diet_string.split("_")
        try:
            flags = getattr(cls, parts[0].upper())
            for part in parts[1:]:
                flags |= getattr(cls, part.upper())
        except AttributeError as e:
            raise ValueError(f"Invalid diet term in string: {diet_string}") from e

        return flags

    def coarse_category(self) -> DietType:
        """Classify the detailed diet into a broad trophic category.

        This method examines the components of the current DietType flag and returns one
        of the three broad trophic categories: HERBIVORE, CARNIVORE, or OMNIVORE. These
        categories are defined as composite flags within the DietType enumeration.

        - Returns OMNIVORE if the diet includes both plant/fungal and animal-derived
            resources.
        - Returns CARNIVORE if the diet includes only animal-derived resources.
        - Returns HERBIVORE for all other combinations, including plant-only or empty
            diets.

        Returns:
            DietType: A diet type flag representing the coarse category.
        """
        is_herb = bool(self & DietType.HERBIVORE)
        is_carn = bool(self & DietType.CARNIVORE)

        if is_herb and is_carn:
            return DietType.OMNIVORE
        elif is_carn:
            return DietType.CARNIVORE
        else:
            return DietType.HERBIVORE

    def count_dietary_categories(self) -> int:
        """Count the number of distinct dietary categories in this flag set.

        Returns:
            An integer of the number of different type types possessed by the functional
            group.

        """
        excluded = {"HERBIVORE", "CARNIVORE", "OMNIVORE", "NONFEEDING"}
        return len(
            [flag for flag in DietType if flag in self and flag.name not in excluded]
        )


class TaxaType(Enum):
    """Enumeration for taxa types."""

    MAMMAL = "mammal"
    BIRD = "bird"
    INVERTEBRATE = "invertebrate"
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
    def parse(cls, occupancy: str) -> VerticalOccupancy:
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
