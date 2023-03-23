"""The `models.animals.import_functional_groups` module provides a function for the
import of pre-defined functional groups used by AnimalCohorts in the
:mod:`~virtual_rainforest.models.animals` module.
"""  # noqa: D205, D415

import csv

from virtual_rainforest.models.animals.functional_group import FunctionalGroup


def import_functional_groups(fg_file: str) -> list[FunctionalGroup]:
    """The function to import pre-defined functional groups.

    This function is a first-pass of how we might import pre-defined functional groups.
    The current expected csv structure is "name", "taxa", "diet" - the specific options
    of which can be found in functional_group.py. This allows a user to set out a basic
    outline of functional groups that accept our definitions of parameters and scaling
    relationships based on those traits.

    We will need a structure for users changing those underlying definitions but that
    can be constructed later.

    Args:
        csv_file: The location of the csv file holding the functional group definitions.

    Returns:
        A list of the FunctionalGroup instances created by the import.

    """
    functional_group_list: list[FunctionalGroup] = []

    with open(fg_file, newline="") as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)  # skip the header
        # unpack the row directly in the head of the for-loop
        for name, taxa, diet in reader:
            # create the FG instance and append it to the list
            functional_group_list.append(FunctionalGroup(name, taxa, diet))

    return functional_group_list
