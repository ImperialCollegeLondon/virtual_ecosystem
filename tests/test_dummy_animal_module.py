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

    def test_plant_growth0(self):
        """Testing plant_growth at 100% energy."""
        p = am.Plant("tree", 10.0, 1)
        print("testing plant growth : plant")
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth1(self):
        """Testing plant_growth at 100% energy."""
        p = am.Plant("tree", 10.0, 1)
        print("testing plant growth : plant")
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth2(self):
        """Testing plant_growth at 50% energy."""
        p = am.Plant("tree", 10.0, 1)
        print("testing plant growth : plant")
        p.energy = 500
        p.plant_growth()
        assert p.energy == 750

    def test_plant_growth3(self):
        """Testing plant_growth at 0% energy."""
        p = am.Plant("tree", 10.0, 1)
        print("testing plant growth : plant")
        p.energy = 0
        p.plant_growth()
        assert p.energy == 0

    def test_plant_death(self):
        """Testing plant_death."""
        p = am.Plant("tree", 10.0, 1)
        print("testing plant growth : plant")
        p.plant_death()
        assert p.alive == "dead"


class TestAnimal:
    """Test the Animal class."""

    def test_metabolism(self):
        """Testing metabolism."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        a1.metabolism(0.0)
        assert a1.stored_energy == 1000.0
        a2 = am.Animal("Testasaurus", 100, 1, 1)
        a2.metabolism(1.0)
        assert a2.stored_energy == 999.999683772234

    def test_eat(self):
        """Testing eat."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        p1 = am.Plant("tree", 10.0, 1)
        a1.eat(p1)
        assert a1.stored_energy == 1000.0021081851067
        assert p1.energy == 999.9968377223398

    def test_excrete(self):
        """Testing excrete."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        animal_energy_1 = a1.stored_energy
        s1 = am.SoilPool(100.0, 1)
        soil_energy_1 = s1.energy
        a1.excrete(s1)
        animal_energy_2 = a1.stored_energy
        soil_energy_2 = s1.energy
        assert a1.stored_energy == 990.0
        assert s1.energy == 110.0
        assert (animal_energy_1 - animal_energy_2) == (soil_energy_2 - soil_energy_1)

    def test_aging(self):
        """Testing aging."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        animal_age_1 = a1.age
        time = 1
        a1.aging(time)
        animal_age_2 = a1.age
        assert a1.age == 2
        assert animal_age_1 + time == animal_age_2

    def test_animal_individual_death(self):
        """Testing animal_individual_death."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        animal_individuals_1 = a1.individuals
        deaths = 0
        a1.animal_individual_death(deaths)
        animal_individuals_2 = a1.individuals
        assert a1.individuals == 133765
        assert animal_individuals_1 - deaths == animal_individuals_2

    def test_animal_cohort_death(self):
        """Testing animal_cohort_death."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        a1.animal_cohort_death()
        assert a1.alive == "dead"

    def test_birth(self):
        """Testing birth."""
        a1 = am.Animal("Testasaurus", 100.0, 1, 1)
        a2 = a1.birth()
        assert a2.name == "Testasaurus"
        assert a2.mass == 100.0
        assert a2.age == 0


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        c1 = am.CarcassPool(1000.7, 1)
        assert c1.energy == 1000.7
