"""Test module for functional_group.py."""

import pytest


class TestFunctionalGroup:
    """Test FunctionalGroup class."""

    @pytest.mark.parametrize(
        (
            "name, taxa, diet, metabolic_type, reproductive_environment,"
            "reproductive_type, development_type, development_status,"
            "offspring_functional_group, excretion_type,migration_type,"
            "vertical_occupancy, birth_mass,"
            "adult_mass, dam_law_exp, dam_law_coef,conv_eff, expected_cnp"
        ),
        [
            (
                "herbivorous_mammal",
                "mammal",
                "herbivore",
                "endothermic",
                "terrestrial",
                "iteroparous",
                "direct",
                "adult",
                "herbivorous_mammal",
                "ureotelic",
                "none",
                "ground",
                1.0,
                10.0,
                -0.75,
                4.23,
                0.1,
                {"carbon": 0.5, "nitrogen": 0.3, "phosphorus": 0.2},
            ),
            (
                "carnivorous_bird",
                "bird",
                "carnivore",
                "endothermic",
                "terrestrial",
                "iteroparous",
                "direct",
                "adult",
                "carnivorous_bird",
                "uricotelic",
                "seasonal",
                "ground_canopy",
                0.1,
                1.0,
                -0.75,
                2.00,
                0.25,
                {"carbon": 0.4, "nitrogen": 0.3, "phosphorus": 0.3},
            ),
            (
                "herbivorous_insect_iteroparous",
                "invertebrate",
                "herbivore",
                "ectothermic",
                "terrestrial",
                "iteroparous",
                "direct",
                "adult",
                "herbivorous_insect_iteroparous",
                "uricotelic",
                "none",
                "soil_ground_canopy",
                0.0005,
                0.005,
                -0.75,
                5.00,
                0.1,
                {"carbon": 0.4, "nitrogen": 0.2, "phosphorus": 0.4},
            ),
        ],
    )
    def test_initialization(
        self,
        name,
        taxa,
        diet,
        metabolic_type,
        reproductive_environment,
        reproductive_type,
        development_type,
        development_status,
        offspring_functional_group,
        excretion_type,
        migration_type,
        vertical_occupancy,
        birth_mass,
        adult_mass,
        dam_law_exp,
        dam_law_coef,
        conv_eff,
        expected_cnp,
    ):
        """Testing initialization of derived parameters for animal cohorts."""
        from virtual_ecosystem.models.animal.animal_traits import (
            DietType,
            ExcretionType,
            MetabolicType,
            MigrationType,
            ReproductiveEnvironment,
            ReproductiveType,
            TaxaType,
            VerticalOccupancy,
        )
        from virtual_ecosystem.models.animal.constants import AnimalConsts
        from virtual_ecosystem.models.animal.functional_group import FunctionalGroup

        func_group = FunctionalGroup(
            name,
            taxa,
            diet,
            metabolic_type,
            reproductive_environment,
            reproductive_type,
            development_type,
            development_status,
            offspring_functional_group,
            excretion_type,
            migration_type,
            vertical_occupancy,
            birth_mass,
            adult_mass,
            constants=AnimalConsts(density_scaling_method="damuth"),
        )
        assert func_group.name == name
        assert func_group.taxa == TaxaType(taxa)
        assert func_group.diet == DietType.parse(diet)
        assert func_group.metabolic_type == MetabolicType(metabolic_type)
        assert func_group.reproductive_environment == ReproductiveEnvironment(
            reproductive_environment
        )
        assert func_group.reproductive_type == ReproductiveType(reproductive_type)
        assert func_group.offspring_functional_group == offspring_functional_group
        assert func_group.excretion_type == ExcretionType(excretion_type)
        assert func_group.migration_type == MigrationType(migration_type)
        assert func_group.vertical_occupancy == VerticalOccupancy.parse(
            vertical_occupancy
        )
        assert func_group.population_density_terms[0] == dam_law_exp
        assert func_group.population_density_terms[1] == dam_law_coef
        assert func_group.conversion_efficiency == conv_eff

        assert hasattr(func_group, "cnp_proportions"), (
            "cnp_proportions attribute missing!"
        )

        # Check CNP proportions
        assert func_group.cnp_proportions == expected_cnp, (
            f"Expected {expected_cnp} but got {func_group.cnp_proportions} for "
            f"taxa {taxa}."
        )


@pytest.mark.parametrize(
    "index, name, taxa, diet, metabolic_type, reproductive_environment,"
    "reproductive_type, development_type, development_status,"
    "offspring_functional_group, excretion_type, migration_type,"
    "vertical_occupancy, birth_mass, adult_mass",
    [
        (
            0,
            "carnivorous_bird",
            "bird",
            "vertebrates_invertebrates_carcasses",
            "endothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "carnivorous_bird",
            "uricotelic",
            "none",
            "ground_canopy",
            0.1,
            1.0,
        ),
        (
            1,
            "herbivorous_bird",
            "bird",
            "fruit_foliage",
            "endothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "herbivorous_bird",
            "uricotelic",
            "none",
            "ground_canopy",
            0.05,
            0.5,
        ),
        (
            2,
            "carnivorous_mammal",
            "mammal",
            "vertebrates_invertebrates_carcasses",
            "endothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "carnivorous_mammal",
            "ureotelic",
            "none",
            "ground",
            4.0,
            40.0,
        ),
        (
            3,
            "herbivorous_mammal",
            "mammal",
            "fruit_foliage",
            "endothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "herbivorous_mammal",
            "ureotelic",
            "none",
            "ground",
            1.0,
            10.0,
        ),
        (
            4,
            "carnivorous_insect_iteroparous",
            "invertebrate",
            "invertebrates",
            "ectothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "carnivorous_insect_iteroparous",
            "uricotelic",
            "none",
            "soil_ground_canopy",
            0.001,
            0.01,
        ),
        (
            5,
            "herbivorous_insect_iteroparous",
            "invertebrate",
            "fruit_foliage",
            "ectothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "herbivorous_insect_iteroparous",
            "uricotelic",
            "none",
            "soil_ground_canopy",
            0.0005,
            0.005,
        ),
        (
            6,
            "carnivorous_insect_semelparous",
            "invertebrate",
            "invertebrates",
            "ectothermic",
            "terrestrial",
            "semelparous",
            "direct",
            "adult",
            "carnivorous_insect_semelparous",
            "uricotelic",
            "none",
            "soil_ground_canopy",
            0.001,
            0.01,
        ),
        (
            7,
            "herbivorous_insect_semelparous",
            "invertebrate",
            "fruit_foliage",
            "ectothermic",
            "terrestrial",
            "semelparous",
            "direct",
            "adult",
            "herbivorous_insect_semelparous",
            "uricotelic",
            "none",
            "soil_ground_canopy",
            0.0005,
            0.005,
        ),
        (
            8,
            "butterfly",
            "invertebrate",
            "fruit_foliage",
            "ectothermic",
            "terrestrial",
            "semelparous",
            "indirect",
            "adult",
            "caterpillar",
            "uricotelic",
            "none",
            "ground_canopy",
            0.0005,
            0.005,
        ),
        (
            9,
            "caterpillar",
            "invertebrate",
            "fruit_foliage",
            "ectothermic",
            "terrestrial",
            "nonreproductive",
            "indirect",
            "larval",
            "butterfly",
            "uricotelic",
            "none",
            "canopy",
            0.0005,
            0.005,
        ),
        (
            10,
            "frog",
            "amphibian",
            "vertebrates_invertebrates_carcasses",
            "ectothermic",
            "aquatic",
            "iteroparous",
            "direct",
            "adult",
            "frog",
            "ureotelic",
            "none",
            "ground",
            0.005,
            0.5,
        ),
        (
            11,
            "swallow",
            "bird",
            "invertebrates",
            "endothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "swallow",
            "uricotelic",
            "seasonal",
            "canopy",
            0.005,
            0.2,
        ),
        (
            12,
            "earthworm",
            "invertebrate",
            "detritus_fungi_pom_bacteria",
            "ectothermic",
            "terrestrial",
            "iteroparous",
            "direct",
            "adult",
            "earthworm",
            "uricotelic",
            "none",
            "soil",
            0.0005,
            0.005,
        ),
    ],
)
def test_import_functional_groups(
    shared_datadir,
    index,
    name,
    taxa,
    diet,
    metabolic_type,
    reproductive_environment,
    reproductive_type,
    development_type,
    development_status,
    offspring_functional_group,
    excretion_type,
    migration_type,
    vertical_occupancy,
    birth_mass,
    adult_mass,
):
    """Testing import functional groups."""
    from virtual_ecosystem.models.animal.animal_traits import (
        DevelopmentStatus,
        DevelopmentType,
        DietType,
        ExcretionType,
        MetabolicType,
        MigrationType,
        ReproductiveEnvironment,
        ReproductiveType,
        TaxaType,
        VerticalOccupancy,
    )
    from virtual_ecosystem.models.animal.constants import AnimalConsts
    from virtual_ecosystem.models.animal.functional_group import (
        FunctionalGroup,
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants=AnimalConsts())

    fg = fg_list[index]
    assert isinstance(fg, FunctionalGroup)
    assert fg.name == name
    assert fg.taxa == TaxaType(taxa)
    assert fg.diet == DietType.parse(diet)
    assert fg.metabolic_type == MetabolicType(metabolic_type)
    assert fg.reproductive_environment == ReproductiveEnvironment(
        reproductive_environment
    )
    assert fg.reproductive_type == ReproductiveType(reproductive_type)
    assert fg.development_type == DevelopmentType(development_type)
    assert fg.development_status == DevelopmentStatus(development_status)
    assert fg.offspring_functional_group == offspring_functional_group
    assert fg.excretion_type == ExcretionType(excretion_type)
    assert fg.migration_type == MigrationType(migration_type)
    assert fg.vertical_occupancy == VerticalOccupancy.parse(vertical_occupancy)
    assert fg.birth_mass == birth_mass
    assert fg.adult_mass == adult_mass


@pytest.mark.parametrize(
    "name, raises_exception",
    [
        pytest.param("herbivorous_mammal", False, id="Valid functional group name"),
        pytest.param("non_existent_group", True, id="Invalid functional group name"),
    ],
)
def test_get_functional_group_by_name(
    functional_group_list_instance, name, raises_exception
):
    """Test get_functional_group_by_name for both valid and invalid names."""
    from virtual_ecosystem.models.animal.functional_group import (
        FunctionalGroup,
        get_functional_group_by_name,
    )

    functional_groups = tuple(functional_group_list_instance)

    if raises_exception:
        with pytest.raises(
            ValueError, match=f"No FunctionalGroup with name '{name}' found."
        ):
            get_functional_group_by_name(functional_groups, name)
    else:
        result = get_functional_group_by_name(functional_groups, name)
        assert isinstance(result, FunctionalGroup)
        assert result.name == name
