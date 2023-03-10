"""The `models.animals.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class ScalingTerms:
    """Dataclass for handling the terms of scaling equations.

    In the future, this class will be significantly expanded to take a suite of animal
    cohort traits, environmental conditions, and/or food traits as input to determine
    the final required scaling relationship.

    """

    exponent: float
    """Handles the exponent on body-mass for scaling equations."""
    coefficient: float
    """Handles the coefficient of scaling equations"""


"""Mammalian herbivore population density, observed allometry (Damuth 1987). [kg]"""
DAMUTHS_LAW_TERMS = ScalingTerms(-0.75, 4.23)

"""Temporary basal metabolic rate values for mammals (citation from Rallings). [g]"""
METABOLIC_RATE_TERMS = ScalingTerms(0.75, 0.047)

"""Scaling of mammalian herbivore fat mass (citation from Rallings). [g]"""
FAT_MASS_TERMS = ScalingTerms(1.19, 0.02)

"""Scaling of mammalian herbivore muscle mass (citation from Rallings).[g]"""
MUSCLE_MASS_TERMS = ScalingTerms(1.0, 0.38)

"""Mammalian maximum intake rate (g/min) from (Shipley 1994)."""
INTAKE_RATE_TERMS = ScalingTerms(0.71, 0.63)


@dataclass
class Term:
    """Dataclass for handling fixed parameter values.

    In the future, this class will be significantly expanded to take a suite of animal
    cohort traits, environmental conditions, and/or food traits as input to determine
    the final required parameter value.

    """

    value: float
    """Contains the float value of the parameter"""


"""The energy of a unit mass of mammal meat (check citation from Rallings). [J/g]"""
MEAT_ENERGY = Term(7000.0)

"""Toy value expressing how much of a consumed food is absorbed as energy. [unitless]"""
CONVERSION_EFFICIENCY = Term(0.1)

"""Temporary realistic plant food value: Alfalfa ¬ 18,200,000 J/kg DM."""
PLANT_ENERGY_DENSITY = Term(18200000.0)
