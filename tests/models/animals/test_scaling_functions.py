"""Test module for scaling_functions.py."""

import pytest


@pytest.mark.parametrize(
    "mass, population_density, terms",
    [
        (100000.0, 1.0, (-0.75, 4.23)),
        (0.07, 32.0, (-0.75, 4.23)),
        (1.0, 5.0, (-0.75, 4.23)),
    ],
)
def test_damuths_law(mass, population_density, terms):
    """Testing damuth's law for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import damuths_law

    testing_pop = damuths_law(mass, terms)
    assert testing_pop == population_density


@pytest.mark.parametrize(
    "mass, temperature, terms, metabolic_type, met_rate",
    [
        # Test cases for an endothermic animal
        (0.0, 25, {"basal": (0.75, 0.047), "field": (0.75, 0.047)}, "endothermic", 0.0),
        (
            1.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            2.3264417757316824e-16,
        ),
        (
            1000.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "endothermic",
            3.218786623537764e-16,
        ),
        # Test cases for an ectothermic animal
        (0.0, 25, {"basal": (0.75, 0.047), "field": (0.75, 0.047)}, "ectothermic", 0.0),
        (
            1.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            9.116692117764761e-17,
        ),
        (
            1000.0,
            25,
            {"basal": (0.75, 0.047), "field": (0.75, 0.047)},
            "ectothermic",
            1.261354870157637e-16,
        ),
    ],
)
def test_metabolic_rate(mass, temperature, terms, metabolic_type, met_rate):
    """Testing metabolic rate for various body-masses."""

    from virtual_rainforest.models.animals.animal_traits import MetabolicType
    from virtual_rainforest.models.animals.scaling_functions import metabolic_rate

    testing_rate = metabolic_rate(
        mass, temperature, terms, MetabolicType(metabolic_type)
    )
    assert testing_rate == pytest.approx(met_rate, rel=1e-6)


@pytest.mark.parametrize(
    "mass, muscle, terms",
    [
        (0.0, 0.0, (1.0, 0.38)),
        (1.0, 380.0, (1.0, 0.38)),
        (1000.0, 380000.0, (1.0, 0.38)),
    ],
)
def test_muscle_mass_scaling(mass, muscle, terms):
    """Testing muscle mass scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import muscle_mass_scaling

    gains = muscle_mass_scaling(mass, terms)
    assert gains == pytest.approx(muscle, rel=1e-6)


@pytest.mark.parametrize(
    "mass, fat, terms",
    [
        (0.0, 0.0, (1.19, 0.02)),
        (1.0, 74.307045, (1.19, 0.02)),
        (1000.0, 276076.852920, (1.19, 0.02)),
    ],
)
def test_fat_mass_scaling(mass, fat, terms):
    """Testing fat mass scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import fat_mass_scaling

    gains = fat_mass_scaling(mass, terms)
    assert gains == pytest.approx(fat, rel=1e-6)


@pytest.mark.parametrize(
    "mass, energy, muscle_terms, fat_terms",
    [
        (0.0, 0.0, (1.0, 0.38), (1.19, 0.02)),
        (1.0, 3180149.320736, (1.0, 0.38), (1.19, 0.02)),
        (1000.0, 4592537970.444037, (1.0, 0.38), (1.19, 0.02)),
    ],
)
def test_energetic_reserve_scaling(mass, energy, muscle_terms, fat_terms):
    """Testing energetic reserve scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import (
        energetic_reserve_scaling,
    )

    gains = energetic_reserve_scaling(mass, muscle_terms, fat_terms)
    assert gains == pytest.approx(energy, rel=1e-6)


@pytest.mark.parametrize(
    "mass, intake_rate, terms",
    [
        (0.0, 0.0, (0.71, 0.63)),
        (1.0, 0.3024, (0.71, 0.63)),
        (1000.0, 40.792637, (0.71, 0.63)),
    ],
)
def test_intake_rate_scaling(mass, intake_rate, terms):
    """Testing intake rate scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import intake_rate_scaling

    test_rate = intake_rate_scaling(mass, terms)
    assert test_rate == pytest.approx(intake_rate, rel=1e-6)


def test_herbivore_prey_group_selection():
    """Test for herbivore diet type selection."""
    from virtual_rainforest.models.animals.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(DietType.HERBIVORE, 10.0, (0.1, 1000.0))
    assert result == {"plants": (0.0, 0.0)}


def test_carnivore_prey_group_selection():
    """Test for carnivore diet type selection."""
    from virtual_rainforest.models.animals.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result = prey_group_selection(DietType.CARNIVORE, 10.0, (0.1, 1000.0))
    expected_output = {
        "herbivorous_mammal": (0.1, 1000.0),
        "carnivorous_mammal": (0.1, 1000.0),
        "herbivorous_bird": (0.1, 1000.0),
        "carnivorous_bird": (0.1, 1000.0),
        "herbivorous_insect": (0.1, 1000.0),
        "carnivorous_insect": (0.1, 1000.0),
    }
    assert result == expected_output


def test_prey_group_selection_invalid_diet_type():
    """Test for an invalid diet type."""
    import pytest

    from virtual_rainforest.models.animals.scaling_functions import prey_group_selection

    with pytest.raises(ValueError, match="Invalid diet type:"):
        prey_group_selection("omnivore", 10.0, (0.1, 1000.0))


def test_prey_group_selection_mass_and_terms_impact():
    """Test to ensure `mass` and `terms` don't affect output."""
    from virtual_rainforest.models.animals.scaling_functions import (
        DietType,
        prey_group_selection,
    )

    result_default = prey_group_selection(DietType.CARNIVORE, 10.0, (0.1, 1000.0))
    result_diff_mass = prey_group_selection(DietType.CARNIVORE, 50.0, (0.1, 1000.0))
    result_diff_terms = prey_group_selection(DietType.CARNIVORE, 10.0, (0.5, 500.0))

    assert result_default == result_diff_mass == result_diff_terms


@pytest.mark.parametrize(
    "mass, terms, expected",
    [
        (1.0, (0.25, 0.05), 0.2055623),
        (1000.0, (0.01, 0.1), 0.1018162),
    ],
)
def test_natural_mortality_scaling(mass, terms, expected):
    """Testing natural mortality scaling for various body-masses."""
    from virtual_rainforest.models.animals.scaling_functions import (
        natural_mortality_scaling,
    )

    result = natural_mortality_scaling(mass, terms)
    assert result == pytest.approx(expected, rel=1e-6)


def test_natural_mortality_scaling_zero_mass():
    """Testing natural mortality scaling with a zero mass."""
    from virtual_rainforest.models.animals.scaling_functions import (
        natural_mortality_scaling,
    )

    with pytest.raises(ZeroDivisionError):
        natural_mortality_scaling(0.0, (0.71, 0.63))


def test_natural_mortality_scaling_negative_mass():
    """Testing natural mortality scaling with a negative mass."""
    from virtual_rainforest.models.animals.scaling_functions import (
        natural_mortality_scaling,
    )

    with pytest.raises(TypeError):
        natural_mortality_scaling(-1.0, (0.71, 0.63))


def test_natural_mortality_scaling_invalid_terms():
    """Testing natural mortality scaling with invalid terms."""
    from virtual_rainforest.models.animals.scaling_functions import (
        natural_mortality_scaling,
    )

    with pytest.raises(IndexError):
        natural_mortality_scaling(1.0, (0.71,))
