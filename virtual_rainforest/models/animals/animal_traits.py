"""The `models.animals.animal_traits` module contains classes that organizes
animal traits into enumerations for use by the Functional Group class in the
:mod:`~virtual_rainforest.models.animals.functional_group` module.
"""  # noqa: D205, D415

from enum import Enum


class MetabolicType(Enum):
    """Enumeration for metabolic types.

    The current allowable metabolic types are:
        - endothermic
        - ectothermic

    """

    ENDOTHERMIC = "endothermic"
    ECTOTHERMIC = "ectothermic"


class DietType(Enum):
    """Enumeration for diet types.

    The current allowable metabolic types are:
        - herbivore
        - carnivore

    """

    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"


class TaxaType(Enum):
    """Enumeration for taxa types.

    The current allowable taxa types are:
        - mammal
        - bird
        - insect


    """

    MAMMAL = "mammal"
    BIRD = "bird"
    INSECT = "insect"
