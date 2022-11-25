"""Test module for dummy_animal_module.py.

This module tests the functionality of dummy_animal_module.py
"""

from virtual_rainforest.animals.dummy_animal_module import Animal, Plant


class TestPlant:
    """Test Plant class."""

    def test_plant_growth0(self):
        """Testing plant_growth at 100% energy."""
        p = Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth1(self):
        """Testing plant_growth at 100% energy."""
        p = Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth2(self):
        """Testing plant_growth at 50% energy."""
        p = Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.energy = 500
        p.plant_growth()
        assert p.energy == 750

    def test_plant_growth3(self):
        """Testing plant_growth at 0% energy."""
        p = Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.energy = 0
        p.plant_growth()
        assert p.energy == 0

    def test_plant_death(self):
        """Testing plant_death."""
        p = Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.plant_death()
        assert p.alive == "dead"  # I need to figure out how to deal with flake8 here


class TestAnimal:
    """Test the Animal class."""

    # def test_details(self):
    #    """Test animal details."""
    #    a = Animal("Testasaurus", 100, 1, "g4")
    #    assert (
    #        a.details()
    #        == """This Testasaurus cohort is alive, is 1 years old,
    #        has 1000.0 stored energy, and has: 0.0 waste energy."""
    #    )

    def test_metabolism(self):
        """Testing metabolism."""
        a1 = Animal("Testasaurus", 100, 1, "g4")
        a1.metabolism(0.0)
        assert a1.stored_energy == 1000.0
        a2 = Animal("Testasaurus", 100, 1, "g4")
        a2.metabolism(1.0)
        assert a2.stored_energy == 999.999683772234
