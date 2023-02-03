"""Test module for dummy_animal_module.py.

This module tests the functionality of dummy_animal_module.py
"""

import pytest


@pytest.fixture
def plant_instance():
    """Fixutre for a plant community used in tests."""
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
        if plant_instance.is_alive:
            plant_instance.die()
            assert not plant_instance.is_alive


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        from virtual_rainforest.models.animals.dummy_animal_module import CarcassPool

        c1 = CarcassPool(1000.7, 1)
        assert c1.energy == 1000.7


class TestSoilPool:
    """Test the Soil Pool class."""

    def test_initialization(self):
        """Testing initialization of soil pool."""
        from virtual_rainforest.models.animals.dummy_animal_module import SoilPool

        s1 = SoilPool(1000.7, 1)
        assert s1.energy == 1000.7
