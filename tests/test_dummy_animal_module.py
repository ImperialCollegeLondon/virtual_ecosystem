"""Test module for dummy_animal_module.py.

This module tests the functionality of dummy_animal_module.py
"""

# Problems:
# handling string returns for details
# handling initialization of animals with zero energy
# test that eat can't drive energy negative

import virtual_rainforest.animals.dummy_animal_module as am


class TestPlant:
    """Test Plant class."""

    def test_plant_growth1(self):
        """Testing plant_growth at 100% energy."""
        p = am.Plant("tree", 10.0, 1)
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth2(self):
        """Testing plant_growth at 50% energy."""
        p = am.Plant("tree", 10.0, 1)
        p.energy = 500
        p.plant_growth()
        assert p.energy == 750

    def test_plant_growth3(self):
        """Testing plant_growth at 0% energy."""
        p = am.Plant("tree", 10.0, 1)
        p.energy = 0
        p.plant_growth()
        assert p.energy == 0

    def test_plant_death(self):
        """Testing plant_death."""
        p = am.Plant("tree", 10.0, 1)
        p.plant_death()
        assert not p.is_alive


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        c1 = am.CarcassPool(1000.7, 1)
        assert c1.energy == 1000.7
