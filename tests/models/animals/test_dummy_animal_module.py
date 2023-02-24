"""Test module for dummy_animal_module.py.

This module tests the functionality of dummy_animal_module.py
"""

import pytest


@pytest.fixture
def plant_instance():
    """Fixture for a plant community used in tests."""
    from virtual_rainforest.models.animals.dummy_animal_module import PlantCommunity

    return PlantCommunity(10.0, 1)


class TestPlantCommunity:
    """Test Plant class."""

    @pytest.mark.parametrize(
        "initial, final", [(10000.0, 10000.0), (500.0, 975.0), (0.0, 0.0)]
    )
    def test_grow(self, plant_instance, initial, final):
        """Testing grow at 100%, 50%, and 0% maximum energy."""
        plant_instance.energy = initial
        plant_instance.grow()
        assert plant_instance.energy == final

    def test_die(self, plant_instance):
        """Testing die."""
        assert plant_instance.is_alive
        plant_instance.die()
        assert not plant_instance.is_alive


class TestPalatableSoil:
    """Test the Palatable Soil class."""

    def test_initialization(self):
        """Testing initialization of soil pool."""
        from virtual_rainforest.models.animals.dummy_animal_module import PalatableSoil

        s1 = PalatableSoil(1000.7, 1)
        assert s1.energy == 1000.7


@pytest.fixture
def animal_instance():
    """Fixutre for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.dummy_animal_module import AnimalCohort

    return AnimalCohort("Testasaurus", 10000.0, 1, 4)


class TestAnimalCohort:
    """Test Animal class."""

    def test_initialization(self, animal_instance):
        """Testing initialization of derived parameters for animal cohorts."""
        assert animal_instance.individuals == 1
        assert animal_instance.metabolic_rate == 0.01
        assert animal_instance.stored_energy == 10000.0

    @pytest.mark.parametrize(
        "initial, final", [(10000.0, 9712.0), (500.0, 212.0), (0.0, 0.0)]
    )
    def test_metabolize(self, animal_instance, initial, final):
        """Testing metabolize at varying energy levels."""
        animal_instance.stored_energy = initial
        animal_instance.metabolize()
        assert animal_instance.stored_energy == final
