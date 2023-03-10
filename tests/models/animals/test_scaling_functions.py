"""Test module for scaling_functions.py."""

import pytest

from virtual_rainforest.models.animals.scaling_functions import (
    damuths_law,
    energetic_reserve_scaling,
    fat_mass_scaling,
    intake_rate_scaling,
    metabolic_rate,
    muscle_mass_scaling,
)


@pytest.mark.parametrize(
    "mass, population_density",
    [(100000.0, 1.0), (0.07, 32.0), (1.0, 5.0)],
)
def test_damuths_law(mass, population_density):
    """Testing damuth's law for various body-masses."""
    testing_pop = damuths_law(mass)
    assert testing_pop == population_density


@pytest.mark.parametrize(
    "mass, met_rate",
    [(0.0, 0.0), (1.0, 8.357913227182937), (1000.0, 1486.2705002791383)],
)
def test_metabolic_rate(mass, met_rate):
    """Testing metabolic rate for various body-masses."""
    testing_rate = metabolic_rate(mass)
    assert testing_rate == met_rate


@pytest.mark.parametrize(
    "mass, muscle",
    [(0.0, 0.0), (1.0, 380.0), (1000.0, 380000.0)],
)
def test_muscle_mass_scaling(mass, muscle):
    """Testing muscle mass scaling for various body-masses."""
    gains = muscle_mass_scaling(mass)
    assert gains == muscle


@pytest.mark.parametrize(
    "mass, fat",
    [(0.0, 0.0), (1.0, 74.30704581943448), (1000.0, 276076.8529205768)],
)
def test_fat_mass_scaling(mass, fat):
    """Testing fat mass scaling for various body-masses."""
    gains = fat_mass_scaling(mass)
    assert gains == fat


@pytest.mark.parametrize(
    "mass, energy",
    [(0.0, 0.0), (1.0, 3180149.3207360418), (1000.0, 4592537970.444037)],
)
def test_energetic_reserve_scaling(mass, energy):
    """Testing energetic reserve scaling for various body-masses."""
    gains = energetic_reserve_scaling(mass)
    assert gains == energy


@pytest.mark.parametrize(
    "mass, intake_rate",
    [(0.0, 0.0), (1.0, 0.3024), (1000.0, 40.79263756957159)],
)
def test_intake_rate_scaling(mass, intake_rate):
    """Testing intake rate scaling for various body-masses."""
    test_rate = intake_rate_scaling(mass)
    assert test_rate == intake_rate
