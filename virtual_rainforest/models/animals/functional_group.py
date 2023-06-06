"""The `models.animals.functional_group` module contains a class that organizes
constants and rate equations used by AnimalCohorts in the
:mod:`~virtual_rainforest.models.animals` module.
"""  # noqa: D205, D415

import pandas as pd

from virtual_rainforest.models.animals.animal_traits import (
    DietType,
    MetabolicType,
    TaxaType,
)
from virtual_rainforest.models.animals.constants import (
    CONVERSION_EFFICIENCY,
    DAMUTHS_LAW_TERMS,
    FAT_MASS_TERMS,
    INTAKE_RATE_TERMS,
    METABOLIC_RATE_TERMS,
    MUSCLE_MASS_TERMS,
)


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

    def __init__(self, name: str, taxa: str, diet: str, metabolic_type: str) -> None:
        """The constructor for the FunctionalGroup class."""

        self.name = name
        """The name of the functional group."""
        self.taxa = TaxaType.from_str(taxa)
        """The taxa of the functional group."""
        self.diet = DietType.from_str(diet)
        """The diet of the functional group."""
        self.metabolic_type = MetabolicType.from_str(metabolic_type)
        """The metabolic type of the functional group"""
        self.metabolic_rate_terms = METABOLIC_RATE_TERMS[self.metabolic_type][self.taxa]
        """The coefficient and exponent of metabolic rate."""
        self.damuths_law_terms = DAMUTHS_LAW_TERMS[self.taxa][self.diet]
        """The coefficient and exponent of damuth's law for population density."""
        self.muscle_mass_terms = MUSCLE_MASS_TERMS[self.taxa]
        """The coefficient and exponent of muscle mass allometry."""
        self.fat_mass_terms = FAT_MASS_TERMS[self.taxa]
        """The coefficient and exponent of fat mass allometry."""
        self.intake_rate_terms = INTAKE_RATE_TERMS[self.taxa]
        """The coefficient and exponent of intake allometry."""
        self.conversion_efficiency = CONVERSION_EFFICIENCY[self.diet]
        """The conversion efficiency of the functional group based on diet."""


def import_functional_groups(fg_csv_file: str) -> list[FunctionalGroup]:
    """The function to import pre-defined functional groups.

    This function is a first-pass of how we might import pre-defined functional groups.
    The current expected csv structure is:
    - ["name", "taxa", "diet", "metabolic_type"]
    the specific options of which can be found in functional_group.py.
    This allows a user to set out a basic outline of functional groups that accept our
    definitions of parameters and scaling relationships based on those traits.

    We will need a structure for users changing those underlying definitions but that
    can be constructed later.

    Args:
        csv_file: The location of the csv file holding the functional group definitions.

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
        FunctionalGroup(row.name, row.taxa, row.diet, row.metabolic_type)
        for row in fg.itertuples()
    ]

    return functional_group_list
