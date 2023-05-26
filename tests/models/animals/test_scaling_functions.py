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
        (0.0, 25, (0.75, 0.047), "endothermic", 0.0),
        (1.0, 25, (0.75, 0.047), "endothermic", 8.357913),
        (1000.0, 25, (0.75, 0.047), "endothermic", 1486.270500),
        # Test cases for an ectothermic animal
        (0.0, 25, (0.75, 0.047), "ectothermic", 0.0),
        (
            1.0,
            25,
            (0.75, 0.047),
            "ectothermic",
            1.068530698734203e-11,
        ),
        (
            1000.0,
            25,
            (0.75, 0.047),
            "ectothermic",
            1.478383149667868e-11,
        ),
    ],
)
def test_metabolic_rate(mass, temperature, terms, metabolic_type, met_rate):
    """Testing metabolic rate for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import metabolic_rate

    testing_rate = metabolic_rate(mass, temperature, terms, metabolic_type)
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
