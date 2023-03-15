"""The `models.animals.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a train) required by the broader
:mod:`~virtual_rainforest.models.animals` module

To Do:
- streamline units of scaling functions [kg]->[kg] etc

"""  # noqa: D205, D415

from math import ceil

from virtual_rainforest.models.animals.constants import (
    DAMUTHS_LAW_TERMS,
    ENDOTHERM_METABOLIC_RATE_TERMS,
    ENERGY_DENSITY,
    FAT_MASS_TERMS,
    INTAKE_RATE_TERMS,
    MUSCLE_MASS_TERMS,
)


def damuths_law(
    mass: float,
    taxa: str,
    diet: str,
    terms: dict = DAMUTHS_LAW_TERMS,
) -> int:
    """The function set initial population densities .

        Currently, this function just employs Damuth's Law (Damuth 1987) for
        terrestrial herbivorous mammals. Later, it will be expanded to other types. The
        current form takes the ceiling of the population density to ensure there is a
        minimum of 1 individual and integer values. This will be corrected once the
        multi-grid occupation system for large animals is implemented.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        taxa: The taxa category of the animal cohort [toy: mammal or bird].
        diet: The diet category of the animal cohort [toy: herbivore or carnivore].
        terms: The dictionary of population density terms used, default to Damuth.

    Returns:
        The population density of that AnimalCohort [individuals/km2].

    """
    exp = terms[taxa][diet][0]
    coef = terms[taxa][diet][1]
    return ceil(coef * mass**exp)


def metabolic_rate(
    mass: float, taxa: str, terms: dict = ENDOTHERM_METABOLIC_RATE_TERMS
) -> float:
    """The function to set the metabolic rate of animal cohorts.

        Currently, this function provides the allometric scaling of the basal metabolic
        rate of terrestrial mammals. This will be later expanded to be a more complex
        function of metabolic type, functional type, activity levels, and temperature.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        taxa: The taxa category of the animal cohort [toy: mammal or bird].
        terms: The dictionary of metabolic rate terms used.

    Returns:
        The metabolic rate of an individual of the given cohort in [J/s].

    """
    exp = terms[taxa][0]
    coef = terms[taxa][1]
    return coef * (mass * 1000) ** exp


def muscle_mass_scaling(
    mass: float, taxa: str, terms: dict = MUSCLE_MASS_TERMS
) -> float:
    """The function to set the amount of muscle mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        taxa: The taxa category of the animal cohort [toy: mammal or bird].
        terms: The dictionary of muscle scaling terms used.

    Returns:
        The mass [g] of muscle on an individual of the animal cohort.

    """
    exp = terms[taxa][0]
    coef = terms[taxa][1]
    return coef * (mass * 1000) ** exp


def fat_mass_scaling(mass: float, taxa: str, terms: dict = FAT_MASS_TERMS) -> float:
    """The function to set the amount of fat mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        taxa: The taxa category of the animal cohort [toy: mammal or bird].
        terms: The dictionary of fat scaling terms used.

    Returns:
        The mass [g] of fat on an individual of the animal cohort.

    """
    exp = terms[taxa][0]
    coef = terms[taxa][1]
    return coef * (mass * 1000) ** exp


def energetic_reserve_scaling(
    mass: float, taxa: str, terms: dict = ENERGY_DENSITY
) -> float:
    """The function to set the energetic reserve of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        taxa: The taxa category of the animal cohort [toy: mammal or bird].
        terms: The dictionary of energy density terms used.

    Returns:
        The energetic reserve [J] of  an individual of the animal cohort.

    """
    return (muscle_mass_scaling(mass, taxa) + fat_mass_scaling(mass, taxa)) * terms[
        "meat"
    ]


def intake_rate_scaling(
    mass: float, taxa: str, terms: dict = INTAKE_RATE_TERMS
) -> float:
    """The function to set the intake rate of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial
        herbivorous mammals interacting with plant foods. This will later be updated
        for additional functional types and interactions.

        The function form converts the original g/min rate into a kg/day rate, where a
        day is an 8hr foraging window.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        taxa: The taxa category of the animal cohort [toy: mammal or bird].
        terms: The dictionary of intake rate terms used.

    Returns:
        The intake rate [kg/day] of an individual of the animal cohort.

    """
    exp = terms[taxa][0]
    coef = terms[taxa][1]
    return coef * mass**exp * 480 * (1 / 1000)
