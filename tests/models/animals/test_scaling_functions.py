"""Test module for scaling_functions.py."""

import pytest


@pytest.mark.parametrize(
    "mass, population_density",
    [(100000.0, 1.0), (0.07, 32.0), (1.0, 5.0)],
)
def test_damuths_law(mass, population_density):
    """Testing damuth's law for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import damuths_law

    testing_pop = damuths_law(mass)
    assert testing_pop == population_density


@pytest.mark.parametrize(
    "mass, met_rate",
    [(0.0, 0.0), (1.0, 8.357913), (1000.0, 1486.270500)],
)
def test_metabolic_rate(mass, met_rate):
    """Testing metabolic rate for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import metabolic_rate

    testing_rate = metabolic_rate(mass)
    assert testing_rate == pytest.approx(met_rate, rel=1e-6)


@pytest.mark.parametrize(
    "mass, muscle",
    [(0.0, 0.0), (1.0, 380.0), (1000.0, 380000.0)],
)
def test_muscle_mass_scaling(mass, muscle):
    """Testing muscle mass scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import muscle_mass_scaling

    gains = muscle_mass_scaling(mass)
    assert gains == pytest.approx(muscle, rel=1e-6)


@pytest.mark.parametrize(
    "mass, fat",
    [(0.0, 0.0), (1.0, 74.307045), (1000.0, 276076.852920)],
)
def test_fat_mass_scaling(mass, fat):
    """Testing fat mass scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import fat_mass_scaling

    gains = fat_mass_scaling(mass)
    assert gains == pytest.approx(fat, rel=1e-6)


@pytest.mark.parametrize(
    "mass, energy",
    [(0.0, 0.0), (1.0, 3180149.320736), (1000.0, 4592537970.444037)],
)
def test_energetic_reserve_scaling(mass, energy):
    """Testing energetic reserve scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import (
        energetic_reserve_scaling,
    )

    gains = energetic_reserve_scaling(mass)
    assert gains == pytest.approx(energy, rel=1e-6)


@pytest.mark.parametrize(
    "mass, intake_rate",
    [(0.0, 0.0), (1.0, 0.3024), (1000.0, 40.792637)],
)
def test_intake_rate_scaling(mass, intake_rate):
    """Testing intake rate scaling for various body-masses."""

    from virtual_rainforest.models.animals.scaling_functions import intake_rate_scaling

    test_rate = intake_rate_scaling(mass)
    assert test_rate == pytest.approx(intake_rate, rel=1e-6)
