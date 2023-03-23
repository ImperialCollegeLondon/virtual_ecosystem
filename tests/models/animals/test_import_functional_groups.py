"""Test module for import_functional_groups.py."""

import pytest


@pytest.mark.parametrize(
    "index, name, taxa, diet",
    [
        (0, "carnivorous_bird", "bird", "carnivore"),
        (1, "herbivorous_bird", "bird", "herbivore"),
        (2, "carnivorous_mammal", "mammal", "carnivore"),
        (3, "herbivorous_mammal", "mammal", "herbivore"),
    ],
)
def test_import_functional_groups(shared_datadir, index, name, taxa, diet):
    """Testing import functional groups."""
    from virtual_rainforest.models.animals.functional_group import FunctionalGroup
    from virtual_rainforest.models.animals.import_functional_groups import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)
    assert len(fg_list) == 4
    assert type(fg_list[index]) == FunctionalGroup
    assert fg_list[index].name == name
    assert fg_list[index].taxa == taxa
    assert fg_list[index].diet == diet
