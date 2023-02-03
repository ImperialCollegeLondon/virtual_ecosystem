"""Test module for dummy_animal_module.py.

This module tests the functionality of dummy_animal_module.py
"""

# Problems:
# handling string returns for details
# handling initialization of animals with zero energy
# test that eat can't drive energy negative

import virtual_rainforest.animals.dummy_animal_module as am


class TestPlantCommunity:
    """Test Plant class."""

    def test_grow1(self):
        """Testing grow at 100% energy."""
        p = am.PlantCommunity(10.0, 1)
        p.grow()
        assert p.energy == 10000.0

    def test_grow2(self):
        """Testing grow at 50% energy."""
        p = am.PlantCommunity(10.0, 1)
        p.energy = 500.0
        p.grow()
        assert p.energy == 975.0

    def test_grow3(self):
        """Testing grow at 0% energy."""
        p = am.PlantCommunity(10.0, 1)
        p.energy = 0.0
        p.grow()
        assert p.energy == 0.0

    def test_die(self):
        """Testing die."""
        p = am.PlantCommunity(10.0, 1)
        p.die()
        assert not p.is_alive


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        c1 = am.CarcassPool(1000.7, 1)
        assert c1.energy == 1000.7
