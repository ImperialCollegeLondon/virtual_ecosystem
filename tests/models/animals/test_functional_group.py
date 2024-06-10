"""Test module for functional_group.py."""

import pytest


class TestFunctionalGroup:
    """Test FunctionalGroup class."""

    @pytest.mark.parametrize(
        (
            "name, taxa, diet, metabolic_type, reproductive_type, "
            "birth_mass, adult_mass, dam_law_exp, dam_law_coef, conv_eff"
        ),
        [
            (
                "herbivorous_mammal",
                "mammal",
                "herbivore",
                "endothermic",
                "iteroparous",
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
                "iteroparous",
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
                "iteroparous",
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
                "iteroparous",
                0.1,
                1.0,
                -0.75,
                2.00,
                0.25,
            ),
            (
                "herbivorous_insect_iteroparous",
                "insect",
                "herbivore",
                "ectothermic",
                "iteroparous",
                0.0005,
                0.005,
                -0.75,
                5.00,
                0.1,
            ),
            (
                "carnivorous_insect_iteroparous",
                "insect",
                "carnivore",
                "ectothermic",
                "iteroparous",
                0.001,
                0.01,
                -0.75,
                2.00,
                0.25,
            ),
            (
                "herbivorous_insect_semelparous",
                "insect",
                "herbivore",
                "ectothermic",
                "semelparous",
                0.0005,
                0.005,
                -0.75,
                5.00,
                0.1,
            ),
            (
                "carnivorous_insect_semelparous",
                "insect",
                "carnivore",
                "ectothermic",
                "semelparous",
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
        reproductive_type,
        birth_mass,
        adult_mass,
        dam_law_exp,
        dam_law_coef,
        conv_eff,
    ):
        """Testing initialization of derived parameters for animal cohorts."""

        from virtual_ecosystem.models.animal.animal_traits import (
            DietType,
            MetabolicType,
            ReproductiveType,
            TaxaType,
        )
        from virtual_ecosystem.models.animal.constants import AnimalConsts
        from virtual_ecosystem.models.animal.functional_group import FunctionalGroup

        func_group = FunctionalGroup(
            name,
            taxa,
            diet,
            metabolic_type,
            reproductive_type,
            birth_mass,
            adult_mass,
            constants=AnimalConsts(),
        )
        assert func_group.name == name
        assert func_group.taxa == TaxaType(taxa)
        assert func_group.diet == DietType(diet)
        assert func_group.metabolic_type == MetabolicType(metabolic_type)
        assert func_group.reproductive_type == ReproductiveType(reproductive_type)
        assert func_group.damuths_law_terms[0] == dam_law_exp
        assert func_group.damuths_law_terms[1] == dam_law_coef
        assert func_group.conversion_efficiency == conv_eff


@pytest.mark.parametrize(
    "index, name, taxa, diet, metabolic_type, reproductive_type",
    [
        (0, "carnivorous_bird", "bird", "carnivore", "endothermic", "iteroparous"),
        (1, "herbivorous_bird", "bird", "herbivore", "endothermic", "iteroparous"),
        (2, "carnivorous_mammal", "mammal", "carnivore", "endothermic", "iteroparous"),
        (3, "herbivorous_mammal", "mammal", "herbivore", "endothermic", "iteroparous"),
        (
            4,
            "carnivorous_insect_iteroparous",
            "insect",
            "carnivore",
            "ectothermic",
            "iteroparous",
        ),
        (
            5,
            "herbivorous_insect_iteroparous",
            "insect",
            "herbivore",
            "ectothermic",
            "iteroparous",
        ),
        (
            6,
            "carnivorous_insect_semelparous",
            "insect",
            "carnivore",
            "ectothermic",
            "semelparous",
        ),
        (
            7,
            "herbivorous_insect_semelparous",
            "insect",
            "herbivore",
            "ectothermic",
            "semelparous",
        ),
    ],
)
def test_import_functional_groups(
    shared_datadir, index, name, taxa, diet, metabolic_type, reproductive_type
):
    """Testing import functional groups."""
    from virtual_ecosystem.models.animal.animal_traits import (
        DietType,
        MetabolicType,
        ReproductiveType,
        TaxaType,
    )
    from virtual_ecosystem.models.animal.constants import AnimalConsts
    from virtual_ecosystem.models.animal.functional_group import (
        FunctionalGroup,
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants=AnimalConsts())
    assert len(fg_list) == 8
    assert isinstance(fg_list[index], FunctionalGroup)
    assert fg_list[index].name == name
    assert fg_list[index].taxa == TaxaType(taxa)
    assert fg_list[index].diet == DietType(diet)
    assert fg_list[index].metabolic_type == MetabolicType(metabolic_type)
    assert fg_list[index].reproductive_type == ReproductiveType(reproductive_type)
