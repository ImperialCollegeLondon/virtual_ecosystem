"""The `models.animals.constants` module contains a set of dataclasses containing
constants" (fitting relationships taken from the literature) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from dataclasses import dataclass


@dataclass
class ScalingTerms:
    """Dataclass for handling the terms of scaling equations."""

    exponent: float
    """Handles the exponent on body-mass for scaling equations."""
    coefficient: float
    """Handles the coefficient of scaling equations"""


"""Mammalian herbivore population density, observed allometry (Damuth 1987). [kg]"""
DamuthsLaw = ScalingTerms(-0.75, 4.23)

"""Temporary basal metabolic rate values for mammals (citation from Rallings). [g]"""
MetabolicRate = ScalingTerms(0.75, 0.047)

"""Scaling of mammalian herbivore fat mass (citation from Rallings). [g]"""
FatMass = ScalingTerms(1.19, 0.02)

"""Scaling of mammalian herbivore muscle mass (citation from Rallings).[g]"""
MuscleMass = ScalingTerms(1.0, 0.38)

"""Mammalian maximum intake rate (kg/day) from (Shipley 1994)."""
IntakeRate = ScalingTerms(0.71, (0.63 * 480) * (1 / 1000))
""" Converts original g/min rate to kg/day where 'day' is an 8hr foraging window."""


@dataclass
class Term:
    """Dataclass for handling fixed parameter values."""

    value: float
    """Contains the float value of the parameter"""


"""The energy of a unit mass of mammal meat (check citation from Rallings). [J/g]"""
MeatEnergy = Term(7000.0)

"""Toy value expressing how much of a consumed food is absorbed as energy. [unitless]"""
ConversionEfficiency = Term(0.1)

"""Temporary realistic plant food value: Alfalfa ¬ 18,200,000 J/kg DM."""
PlantEnergyDensity = Term(18200000.0)
