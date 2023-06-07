"""The `models.animals.scaling_functions` module contains a set of functions containing
scaling equations" (relationships between body-mass and a trait) required by the broader
:mod:`~virtual_rainforest.models.animals` module

To Do:
- streamline units of scaling functions [kg]->[kg] etc

"""  # noqa: D205, D415

from math import ceil, exp

from virtual_rainforest.models.animals.animal_traits import MetabolicType
from virtual_rainforest.models.animals.constants import BOLTZMANN_CONSTANT


def damuths_law(mass: float, terms: tuple) -> int:
    """The function set initial population densities .

        Currently, this function just employs Damuth's Law (Damuth 1987) for
        terrestrial herbivorous mammals. Later, it will be expanded to other types. The
        current form takes the ceiling of the population density to ensure there is a
        minimum of 1 individual and integer values. This will be corrected once the
        multi-grid occupation system for large animals is implemented.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        terms: The tuple of population density terms used, default to Damuth.

    Returns:
        The population density of that AnimalCohort [individuals/km2].

    """

    return ceil(terms[1] * mass ** terms[0])


def metabolic_rate(
    mass: float, temperature: float, terms: tuple, metabolic_type: MetabolicType
) -> float:
    """Calculates the metabolic rate of animal cohorts.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        temperature: The temperature [Celsius] of the environment.
        terms: The tuple of metabolic rate terms used.
        metabolic_type: The metabolic type of the animal [ENDOTHERMIC or ECTOTHERMIC].

    Returns:
        The metabolic rate of an individual of the given cohort in [J/s].

    """
    mass_g = mass * 1000  # Convert mass to grams
    temperature_k = temperature + 273.15  # Convert temperature to Kelvin

    match metabolic_type:
        case MetabolicType.ENDOTHERMIC:
            return terms[1] * mass_g ** terms[0]
        case MetabolicType.ECTOTHERMIC:
            b0, exponent = terms
            return (
                b0
                * mass_g**exponent
                * exp(-0.65 / (BOLTZMANN_CONSTANT * temperature_k))
            )


def muscle_mass_scaling(mass: float, terms: tuple) -> float:
    """The function to set the amount of muscle mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        terms: The tuple of muscle scaling terms used.

    Returns:
        The mass [g] of muscle on an individual of the animal cohort.

    """

    return terms[1] * (mass * 1000) ** terms[0]


def fat_mass_scaling(mass: float, terms: tuple) -> float:
    """The function to set the amount of fat mass on individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        terms: The tuple of fat scaling terms used.

    Returns:
        The mass [g] of fat on an individual of the animal cohort.

    """

    return terms[1] * (mass * 1000) ** terms[0]


def energetic_reserve_scaling(
    mass: float, muscle_terms: tuple, fat_terms: tuple
) -> float:
    """The function to set the energetic reserve of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial mammals.
        This will later be updated for additional functional types.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        muscle_terms: The tuple of muscle scaling terms used.
        fat_terms: The tuple of fat scaling terms used.

    Returns:
        The energetic reserve [J] of  an individual of the animal cohort.

    """
    return (
        muscle_mass_scaling(mass, muscle_terms) + fat_mass_scaling(mass, fat_terms)
    ) * 7000.0  # j/g


def intake_rate_scaling(mass: float, terms: tuple) -> float:
    """The function to set the intake rate of an individual in an AnimalCohort.

        Currently, this scaling relationship is only accurate for terrestrial
        herbivorous mammals interacting with plant foods. This will later be updated
        for additional functional types and interactions.

        The function form converts the original g/min rate into a kg/day rate, where a
        day is an 8hr foraging window.

    Args:
        mass: The body-mass [kg] of an AnimalCohort.
        terms: The tuple of intake rate terms used.

    Returns:
        The intake rate [kg/day] of an individual of the animal cohort.

    """

    return terms[1] * mass ** terms[0] * 480 * (1 / 1000)
