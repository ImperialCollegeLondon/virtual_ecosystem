"""The `models.animal.functional_group` module contains a class that organizes
constants and rate equations used by AnimalCohorts in the
:mod:`~virtual_ecosystem.models.animal` module.
"""  # noqa: D205

import pandas as pd

from virtual_ecosystem.models.animal.animal_traits import (
    DevelopmentStatus,
    DevelopmentType,
    DietType,
    MetabolicType,
    ReproductiveType,
    TaxaType,
)
from virtual_ecosystem.models.animal.constants import AnimalConsts


class FunctionalGroup:
    """This is a class of animal functional groups.

    The goal of this class is to collect the correct constants and scaling relationships
    needed by an animal cohort such that they are accessed at initialization and stored
    in the AnimalCohort object as attributes. This should result in a system where an
    animal cohort can be auto-generated with a few keywords and numbers but that this
    procedure only need run once, at initialization, and that all further references to
    constants and scaling relationships are accessed through attributes of the
    AnimalCohort in question.

    """

    def __init__(
        self,
        name: str,
        taxa: str,
        diet: str,
        metabolic_type: str,
        reproductive_type: str,
        development_type: str,
        development_status: str,
        offspring_functional_group: str,
        birth_mass: float,
        adult_mass: float,
        constants: AnimalConsts = AnimalConsts(),
    ) -> None:
        """The constructor for the FunctionalGroup class."""

        self.name = name
        """The name of the functional group."""
        self.taxa = TaxaType(taxa)
        """The taxa of the functional group."""
        self.diet = DietType(diet)
        """The diet of the functional group."""
        self.metabolic_type = MetabolicType(metabolic_type)
        """The metabolic type of the functional group."""
        self.reproductive_type = ReproductiveType(reproductive_type)
        """The reproductive type of the functional group."""
        self.development_type = DevelopmentType(development_type)
        """The development type of the functional group."""
        self.development_status = DevelopmentStatus(development_status)
        """The development status of the functional group."""
        self.offspring_functional_group = offspring_functional_group
        """The offspring type produced by this functional group in reproduction or 
            metamorphosis."""
        self.birth_mass = birth_mass
        """The mass of the functional group at birth."""
        self.adult_mass = adult_mass
        """The mass of the functional group at adulthood."""
        self.constants = constants
        """Animal constants."""
        self.metabolic_rate_terms = self.constants.metabolic_rate_terms[
            self.metabolic_type
        ]
        """The coefficient and exponent of metabolic rate."""
        self.damuths_law_terms = self.constants.damuths_law_terms[self.taxa][self.diet]
        """The coefficient and exponent of damuth's law for population density."""
        self.muscle_mass_terms = self.constants.muscle_mass_terms[self.taxa]
        """The coefficient and exponent of muscle mass allometry."""
        self.fat_mass_terms = self.constants.fat_mass_terms[self.taxa]
        """The coefficient and exponent of fat mass allometry."""
        self.intake_rate_terms = self.constants.intake_rate_terms[self.taxa]
        """The coefficient and exponent of intake allometry."""
        self.conversion_efficiency = self.constants.conversion_efficiency[self.diet]
        """The conversion efficiency of the functional group based on diet."""
        self.mechanical_efficiency = self.constants.mechanical_efficiency[self.diet]
        """The mechanical transfer efficiency of a functional group based on diet."""
        self.prey_scaling = self.constants.prey_mass_scaling_terms[self.metabolic_type][
            self.taxa
        ]
        """The predator-prey mass ratio scaling relationship."""
        self.longevity_scaling = self.constants.longevity_scaling_terms[self.taxa]
        """The coefficient and exponent for lifespan allometry."""


def import_functional_groups(
    fg_csv_file: str, constants: AnimalConsts
) -> list[FunctionalGroup]:
    """The function to import pre-defined functional groups.

    This function is a first-pass of how we might import pre-defined functional groups.
    The current expected csv structure is:
    - ["name", "taxa", "diet", "metabolic_type", "birth_mass", "adult_mass"]
    the specific options of which can be found in functional_group.py.
    This allows a user to set out a basic outline of functional groups that accept our
    definitions of parameters and scaling relationships based on those traits.

    We will need a structure for users changing those underlying definitions but that
    can be constructed later.

    Args:
        fg_csv_file: The location of the csv file holding the functional group
            definitions.
        constants:  An object providing animal model constants.

    Returns:
        A list of the FunctionalGroup instances created by the import.

    """
    functional_group_list: list[FunctionalGroup] = []

    fg = pd.read_csv(fg_csv_file)

    expected_header = ["name", "taxa", "diet", "metabolic_type"]
    if not set(expected_header).issubset(fg.columns):
        raise ValueError(
            f"Invalid header. Expected at least {expected_header}, but got {fg.columns}"
        )

    functional_group_list = [
        FunctionalGroup(
            row.name,
            row.taxa,
            row.diet,
            row.metabolic_type,
            row.reproductive_type,
            row.development_type,
            row.development_status,
            row.offspring_functional_group,
            row.birth_mass,
            row.adult_mass,
            constants=constants,
        )
        for row in fg.itertuples()
    ]

    return functional_group_list


def get_functional_group_by_name(
    functional_groups: tuple[FunctionalGroup, ...], name: str
) -> FunctionalGroup:
    """Retrieve a FunctionalGroup by its name from a tuple of FunctionalGroup instances.

    Args:
        functional_groups: Tuple of FunctionalGroup instances.
        name: The name of the FunctionalGroup to retrieve.

    Returns:
        The FunctionalGroup instance with the matching name.

    Raises:
        ValueError: If no FunctionalGroup with the given name is found.
    """
    for fg in functional_groups:
        if fg.name == name:
            return fg
    raise ValueError(f"No FunctionalGroup with name '{name}' found.")
