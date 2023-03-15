"""Test module for scaling_functions.py."""

import pytest


@pytest.mark.parametrize(
    "mass, population_density, taxa, diet",
    [
        (100000.0, 1.0, "mammal", "herbivore"),
        (0.07, 32.0, "mammal", "herbivore"),
        (1.0, 5.0, "mammal", "herbivore"),
    ],
)
def test_damuths_law(mass, population_density, taxa, diet):
    """Testing damuth's law for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import damuths_law

    testing_pop = damuths_law(mass, taxa, diet)
    assert testing_pop == population_density


@pytest.mark.parametrize(
    "mass, met_rate, taxa",
    [(0.0, 0.0, "mammal"), (1.0, 8.357913, "mammal"), (1000.0, 1486.270500, "mammal")],
)
def test_metabolic_rate(mass, met_rate, taxa):
    """Testing metabolic rate for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import metabolic_rate

    testing_rate = metabolic_rate(mass, taxa)
    assert testing_rate == pytest.approx(met_rate, rel=1e-6)


@pytest.mark.parametrize(
    "mass, muscle, taxa",
    [(0.0, 0.0, "mammal"), (1.0, 380.0, "mammal"), (1000.0, 380000.0, "mammal")],
)
def test_muscle_mass_scaling(mass, muscle, taxa):
    """Testing muscle mass scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import muscle_mass_scaling

    gains = muscle_mass_scaling(mass, taxa)
    assert gains == pytest.approx(muscle, rel=1e-6)


@pytest.mark.parametrize(
    "mass, fat, taxa",
    [
        (0.0, 0.0, "mammal"),
        (1.0, 74.307045, "mammal"),
        (1000.0, 276076.852920, "mammal"),
    ],
)
def test_fat_mass_scaling(mass, fat, taxa):
    """Testing fat mass scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import fat_mass_scaling

    gains = fat_mass_scaling(mass, taxa)
    assert gains == pytest.approx(fat, rel=1e-6)


@pytest.mark.parametrize(
    "mass, energy, taxa",
    [
        (0.0, 0.0, "mammal"),
        (1.0, 3180149.320736, "mammal"),
        (1000.0, 4592537970.444037, "mammal"),
    ],
)
def test_energetic_reserve_scaling(mass, energy, taxa):
    """Testing energetic reserve scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import (
        energetic_reserve_scaling,
    )

    gains = energetic_reserve_scaling(mass, taxa)
    assert gains == pytest.approx(energy, rel=1e-6)


@pytest.mark.parametrize(
    "mass, intake_rate, taxa",
    [(0.0, 0.0, "mammal"), (1.0, 0.3024, "mammal"), (1000.0, 40.792637, "mammal")],
)
def test_intake_rate_scaling(mass, intake_rate, taxa):
    """Testing intake rate scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import intake_rate_scaling

    test_rate = intake_rate_scaling(mass, taxa)
    assert test_rate == pytest.approx(intake_rate, rel=1e-6)
