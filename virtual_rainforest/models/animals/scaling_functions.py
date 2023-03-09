"""The `models.animals.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a train) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from math import ceil

from virtual_rainforest.models.animals.constants import (
    DamuthsLawTerms,
    FatMassTerms,
    IntakeRateTerms,
    MeatEnergy,
    MetabolicRateTerms,
    MuscleMassTerms,
)


def DamuthsLaw(mass: float) -> int:
    """The function set initial population densities .

        Currently, this function just employs Damuth's Law (Damuth 1987) for
        terrestrial herbivorous mammals. Later, it will be expanded to other types. The
        current form takes the ceiling of the population density to ensure there is a
        minimum of 1 individual and integer values. This will be corrected once the
        multi-grid occupation system for large animals is implemented.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The population density of that AnimalCohort [individuals/km2].

    """
    return ceil(DamuthsLawTerms.coefficient * mass ** (DamuthsLawTerms.exponent))


def MetabolicRate(mass: float) -> float:
    """The function to set the metabolic rate of animal cohorts.

        Currently, this function provides the allometric scaling of the basal metabolic
        rate of terrestrial mammals. This will be later expanded to be a more complex
        function of metabolic type, functional type, activity levels, and temperature.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The metabolic rate of an individual of the given cohort in [J/s].

    """
    return MetabolicRateTerms.coefficient * (mass * 1000) ** MetabolicRateTerms.exponent


def MuscleMassScaling(mass: float) -> float:
    """The function to set the amount of muscle mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The mass [g] of muscle on an individual of the animal cohort.

    """
    return MuscleMassTerms.coefficient * (mass * 1000) ** MuscleMassTerms.exponent


def FatMassScaling(mass: float) -> float:
    """The function to set the amount of fat mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The mass [g] of fat on an individual of the animal cohort.

    """
    return FatMassTerms.coefficient * (mass * 1000) ** FatMassTerms.exponent


def EnergeticReserveScaling(mass: float) -> float:
    """The function to set the energetic reserve of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The energetic reserve [J] of  an individual of the animal cohort.

    """
    return (MuscleMassScaling(mass) + FatMassScaling(mass)) * MeatEnergy.value


def IntakeRateScaling(mass: float) -> float:
    """The function to set the intake rate of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial
        herbivorous mammals interacting with plant foods. This will later be updated
        for additional functional types and interactions.

        The function form converts the original g/min rate into a kg/day rate, where a
        day is an 8hr foraging window.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The intake rate [kg/day] of an individual of the animal cohort.

    """
    return (
        IntakeRateTerms.coefficient
        * mass**IntakeRateTerms.exponent
        * 480
        * (1 / 1000)
    )
