"""Test module for functional_group.py."""

import pytest


class TestFunctionalGroup:
    """Test Animal class."""

    @pytest.mark.parametrize(
        "name, taxa, diet, dam_law_exp, dam_law_coef, conv_eff",
        [
            ("herbivorous_mammal", "mammal", "herbivore", -0.75, 4.23, 0.1),
            ("carnivorous_mammal", "mammal", "carnivore", -0.75, 1.00, 0.25),
            ("herbivorous_bird", "bird", "herbivore", -0.75, 5.00, 0.1),
            ("carnivorous_bird", "bird", "carnivore", -0.75, 2.00, 0.25),
        ],
    )
    def test_initialization(
        self, name, taxa, diet, dam_law_exp, dam_law_coef, conv_eff
    ):
        """Testing initialization of derived parameters for animal cohorts."""
        from virtual_rainforest.models.animals.functional_group import FunctionalGroup

        func_group = FunctionalGroup(name, taxa, diet)
        assert func_group.damuths_law_terms[0] == dam_law_exp
        assert func_group.damuths_law_terms[1] == dam_law_coef
        assert func_group.conversion_efficiency == conv_eff


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
    from virtual_rainforest.models.animals.functional_group import (
        FunctionalGroup,
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)
    assert len(fg_list) == 4
    assert type(fg_list[index]) == FunctionalGroup
    assert fg_list[index].name == name
    assert fg_list[index].taxa == taxa
    assert fg_list[index].diet == diet
