"""Test module for functional_group.py."""

import pytest


class TestFunctionalGroup:
    """Test Animal class."""

    @pytest.mark.parametrize(
        (
            "name, taxa, diet, metabolic_type, "
            "birth_mass, adult_mass, dam_law_exp, dam_law_coef, conv_eff"
        ),
        [
            (
                "herbivorous_mammal",
                "mammal",
                "herbivore",
                "endothermic",
                1.0,
                10.0,
                -0.75,
                4.23,
                0.1,
            ),
            (
                "carnivorous_mammal",
                "mammal",
                "carnivore",
                "endothermic",
                4.0,
                40.0,
                -0.75,
                1.00,
                0.25,
            ),
            (
                "herbivorous_bird",
                "bird",
                "herbivore",
                "endothermic",
                0.05,
                0.5,
                -0.75,
                5.00,
                0.1,
            ),
            (
                "carnivorous_bird",
                "bird",
                "carnivore",
                "endothermic",
                0.1,
                1.0,
                -0.75,
                2.00,
                0.25,
            ),
            (
                "herbivorous_insect",
                "insect",
                "herbivore",
                "ectothermic",
                0.0005,
                0.005,
                -0.75,
                5.00,
                0.1,
            ),
            (
                "carnivorous_insect",
                "insect",
                "carnivore",
                "ectothermic",
                0.001,
                0.01,
                -0.75,
                2.00,
                0.25,
            ),
        ],
    )
    def test_initialization(
        self,
        name,
        taxa,
        diet,
        metabolic_type,
        birth_mass,
        adult_mass,
        dam_law_exp,
        dam_law_coef,
        conv_eff,
    ):
        """Testing initialization of derived parameters for animal cohorts."""

        from virtual_rainforest.models.animals.animal_traits import (
            DietType,
            MetabolicType,
            TaxaType,
        )
        from virtual_rainforest.models.animals.functional_group import FunctionalGroup

        func_group = FunctionalGroup(
            name, taxa, diet, metabolic_type, birth_mass, adult_mass
        )
        assert func_group.name == name
        assert func_group.taxa == TaxaType(taxa)
        assert func_group.diet == DietType(diet)
        assert func_group.metabolic_type == MetabolicType(metabolic_type)
        assert func_group.damuths_law_terms[0] == dam_law_exp
        assert func_group.damuths_law_terms[1] == dam_law_coef
        assert func_group.conversion_efficiency == conv_eff


@pytest.mark.parametrize(
    "index, name, taxa, diet, metabolic_type",
    [
        (0, "carnivorous_bird", "bird", "carnivore", "endothermic"),
        (1, "herbivorous_bird", "bird", "herbivore", "endothermic"),
        (2, "carnivorous_mammal", "mammal", "carnivore", "endothermic"),
        (3, "herbivorous_mammal", "mammal", "herbivore", "endothermic"),
        (4, "carnivorous_insect", "insect", "carnivore", "ectothermic"),
        (5, "herbivorous_insect", "insect", "herbivore", "ectothermic"),
    ],
)
def test_import_functional_groups(
    shared_datadir, index, name, taxa, diet, metabolic_type
):
    """Testing import functional groups."""
    from virtual_rainforest.models.animals.animal_traits import (
        DietType,
        MetabolicType,
        TaxaType,
    )
    from virtual_rainforest.models.animals.functional_group import (
        FunctionalGroup,
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)
    assert len(fg_list) == 6
    assert isinstance(fg_list[index], FunctionalGroup)
    assert fg_list[index].name == name
    assert fg_list[index].taxa == TaxaType(taxa)
    assert fg_list[index].diet == DietType(diet)
    assert fg_list[index].metabolic_type == MetabolicType(metabolic_type)
