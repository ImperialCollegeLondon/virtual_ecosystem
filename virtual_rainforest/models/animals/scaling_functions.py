"""The `models.animals.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a train) required by the broader
:mod:`~virtual_rainforest.models.animals` module
"""  # noqa: D205, D415

from math import ceil

from virtual_rainforest.models.animals.constants import (
    DAMUTHS_LAW_TERMS,
    FAT_MASS_TERMS,
    INTAKE_RATE_TERMS,
    MEAT_ENERGY,
    METABOLIC_RATE_TERMS,
    MUSCLE_MASS_TERMS,
)


def damuths_law(mass: float) -> int:
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
    return ceil(DAMUTHS_LAW_TERMS.coefficient * mass ** (DAMUTHS_LAW_TERMS.exponent))


def metabolic_rate(mass: float) -> float:
    """The function to set the metabolic rate of animal cohorts.

        Currently, this function provides the allometric scaling of the basal metabolic
        rate of terrestrial mammals. This will be later expanded to be a more complex
        function of metabolic type, functional type, activity levels, and temperature.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The metabolic rate of an individual of the given cohort in [J/s].

    """
    return (
        METABOLIC_RATE_TERMS.coefficient
        * (mass * 1000) ** METABOLIC_RATE_TERMS.exponent
    )


def muscle_mass_scaling(mass: float) -> float:
    """The function to set the amount of muscle mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The mass [g] of muscle on an individual of the animal cohort.

    """
    return MUSCLE_MASS_TERMS.coefficient * (mass * 1000) ** MUSCLE_MASS_TERMS.exponent


def fat_mass_scaling(mass: float) -> float:
    """The function to set the amount of fat mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The mass [g] of fat on an individual of the animal cohort.

    """
    return FAT_MASS_TERMS.coefficient * (mass * 1000) ** FAT_MASS_TERMS.exponent


def energetic_reserve_scaling(mass: float) -> float:
    """The function to set the energetic reserve of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.

    Returns:
        The energetic reserve [J] of  an individual of the animal cohort.

    """
    return (muscle_mass_scaling(mass) + fat_mass_scaling(mass)) * MEAT_ENERGY.value


def intake_rate_scaling(mass: float) -> float:
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
        INTAKE_RATE_TERMS.coefficient
        * mass**INTAKE_RATE_TERMS.exponent
        * 480
        * (1 / 1000)
    )
