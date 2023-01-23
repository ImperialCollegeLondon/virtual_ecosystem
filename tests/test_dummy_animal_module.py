"""Test module for dummy_animal_module.py.

This module tests the functionality of dummy_animal_module.py
"""

# Problems:
# handling string returns for details
# handling initialization of animals with zero energy
# test that eat can't drive energy negative

import virtual_rainforest.animals.dummy_animal_module as am

# from random import choice


class TestPlant:
    """Test Plant class."""

    def test_plant_growth0(self):
        """Testing plant_growth at 100% energy."""
        p = am.Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth1(self):
        """Testing plant_growth at 100% energy."""
        p = am.Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.plant_growth()
        assert p.energy == 1000

    def test_plant_growth2(self):
        """Testing plant_growth at 50% energy."""
        p = am.Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.energy = 500
        p.plant_growth()
        assert p.energy == 750

    def test_plant_growth3(self):
        """Testing plant_growth at 0% energy."""
        p = am.Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.energy = 0
        p.plant_growth()
        assert p.energy == 0

    def test_plant_death(self):
        """Testing plant_death."""
        p = am.Plant("tree", 10.0, "g4")
        print("testing plant growth : plant")
        p.plant_death()
        assert p.alive == "dead"


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
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        a1.metabolism(0.0)
        assert a1.stored_energy == 1000.0
        a2 = am.Animal("Testasaurus", 100, 1, "g4")
        a2.metabolism(1.0)
        assert a2.stored_energy == 999.999683772234
        # a3 = Animal("Testasaurus", 0, 1, "g4")
        # a3.metabolism(1.0)
        # assert a2.stored_energy == 0

    def test_eat(self):
        """Testing eat."""
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        p1 = am.Plant("tree", 10.0, "g4")
        a1.eat(p1)
        assert a1.stored_energy == 1000.0021081851067
        assert p1.energy == 999.9968377223398

    def test_excrete(self):
        """Testing excrete."""
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        animal_energy_1 = a1.stored_energy
        s1 = am.SoilPool(100.0, "g4")
        soil_energy_1 = s1.energy
        a1.excrete(s1)
        animal_energy_2 = a1.stored_energy
        soil_energy_2 = s1.energy
        assert a1.stored_energy == 990.0
        assert s1.energy == 110.0
        assert (animal_energy_1 - animal_energy_2) == (soil_energy_2 - soil_energy_1)

    def test_aging(self):
        """Testing aging."""
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        animal_age_1 = a1.age
        time = 1
        a1.aging(time)
        animal_age_2 = a1.age
        assert a1.age == 2
        assert animal_age_1 + time == animal_age_2

    def test_animal_individual_death(self):
        """Testing animal_individual_death."""
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        animal_individuals_1 = a1.individuals
        deaths = 0
        a1.animal_individual_death(deaths)
        animal_individuals_2 = a1.individuals
        assert a1.individuals == 133765
        assert animal_individuals_1 - deaths == animal_individuals_2

    def test_animal_cohort_death(self):
        """Testing animal_cohort_death."""
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        a1.animal_cohort_death()
        assert a1.alive == "dead"

    def test_birth(self):
        """Testing birth."""
        a1 = am.Animal("Testasaurus", 100.0, 1, "g4")
        a2 = a1.birth()
        assert a2.name == "Testasaurus"
        assert a2.mass == 100.0
        assert a2.age == 0
        # assert a2.position == "g4"

    # def test_disperse(self):
    #     """Testing disperse."""
    #     adjacency = {
    #         "g0": ["g1", "g3"],
    #         "g1": ["g0", "g2", "g4"],
    #         "g2": ["g1", "g5"],
    #         "g3": ["g0", "g4", "g6"],
    #         "g4": ["g1", "g3", "g5", "g7"],
    #         "g5": ["g2", "g4", "g8"],
    #         "g6": ["g3", "g7"],
    #         "g7": ["g4", "g6", "g8"],
    #         "g8": ["g5", "g7"],
    #     }
    #     for initial_position in adjacency.keys():
    #         grid = am.Grid()
    #         grid.populate_grid_squares()
    #         a1 = grid.grid_squares[initial_position].elephants[0]
    #         a1.disperse(grid)
    #         final_position = a1.position
    #         assert final_position in (adjacency[initial_position])


class TestCarcassPool:
    """Test the CarcassPool class."""

    def test_initialization(self):
        """Testing initialization of CarcassPool."""
        c1 = am.CarcassPool(1000.7, "g4")
        assert c1.energy == 1000.7
        # assert c1.position == "g4"


# class TestGridSquare:
#     """Test the GridSquare class."""

#     def test_initialization(self):
#         """Testing initialization of GridSquare."""
#         gs1 = am.GridSquare("gtest")
#         assert gs1.name == "gtest"
#         assert gs1.soil == []
#         assert gs1.trees == []
#         assert gs1.carcasses == []
#         assert gs1.beetles == []
#         assert gs1.elephants == []

#     def test_populate_grid_square(self):
#         """Testing populate_grid_square."""
#         gs1 = am.GridSquare("gtest")
#         gs1.populate_grid_square()
#         assert isinstance(gs1.soil[0], am.SoilPool)
#         assert isinstance(gs1.trees[0], am.Plant)
#         assert isinstance(gs1.carcasses[0], am.CarcassPool)
#         assert isinstance(gs1.beetles[0], am.Animal)
#         assert isinstance(gs1.elephants[0], am.Animal)


# class TestGrid:
#     """Test the Grid class."""

#     def test_initialization(self):
#         """Testing initialization of Grid."""
#         g1 = am.Grid()
#         assert len(g1.grid_squares) == 9
#         assert isinstance(g1.grid_squares["g0"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g1"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g2"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g3"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g4"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g5"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g6"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g7"], am.GridSquare)
#         assert isinstance(g1.grid_squares["g8"], am.GridSquare)

#     def test_populate_grid_squares(self):
#         """Testing populate_grid_squares."""
#         g1 = am.Grid()
#         g1.populate_grid_squares()
#         for square in g1.grid_squares:
#             assert isinstance(g1.grid_squares[square].soil[0], am.SoilPool)
#             assert isinstance(g1.grid_squares[square].trees[0], am.Plant)
#             assert isinstance(g1.grid_squares[square].carcasses[0], am.CarcassPool)
#             assert isinstance(g1.grid_squares[square].beetles[0], am.Animal)
#             assert isinstance(g1.grid_squares[square].elephants[0], am.Animal)
