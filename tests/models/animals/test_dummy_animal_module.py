"""Test module for dummy_animal_module.py."""

import pytest
from numpy import timedelta64


@pytest.fixture
def plant_instance():
    """Fixture for a plant community used in tests."""
    from virtual_rainforest.models.animals.dummy_animal_module import PlantCommunity

    return PlantCommunity(10000.0, 1)


class TestPlantCommunity:
    """Test Plant class."""

    @pytest.mark.parametrize(
        "initial, final",
        [(182000000000.0, 182000000000.0), (10000.0, 19999.99945054945), (0.0, 0.0)],
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
def soil_instance():
    """Fixture for a soil pool used in tests."""
    from virtual_rainforest.models.animals.dummy_animal_module import PalatableSoil

    return PalatableSoil(100000.0, 4)


@pytest.fixture
def animal_instance():
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.dummy_animal_module import AnimalCohort

    return AnimalCohort("Testasaurus", 10000.0, 1, 4)


class TestAnimalCohort:
    """Test Animal class."""

    def test_initialization(self, animal_instance):
        """Testing initialization of derived parameters for animal cohorts."""
        assert animal_instance.individuals == 1
        assert animal_instance.metabolic_rate == 8357.913227182937
        assert animal_instance.stored_energy == 28266000000.0

    @pytest.mark.parametrize(
        "dt, initial_energy, final_energy",
        [
            (timedelta64(1, "D"), 28266000000.0, 27543876297.171394),
            (timedelta64(1, "D"), 500.0, 0.0),
            (timedelta64(1, "D"), 0.0, 0.0),
            (timedelta64(3, "D"), 28266000000.0, 26099628891.514183),
        ],
    )
    def test_metabolize(self, animal_instance, dt, initial_energy, final_energy):
        """Testing metabolize at varying energy levels."""
        animal_instance.stored_energy = initial_energy
        animal_instance.metabolize(dt)
        assert animal_instance.stored_energy == final_energy

    @pytest.mark.parametrize(
        "animal_initial, animal_final, plant_initial, plant_final",
        [
            (28266000000.0, 28646761627.80271, 182000000000.0, 178192383721.97287),
            (0.0, 380761627.80271316, 182000000000.0, 178192383721.97287),
            (28266000000.0, 28266000010.0, 100.0, 0.0),
            (28266000000.0, 28266000000.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
        ],
    )
    def test_eat(
        self,
        animal_instance,
        animal_initial,
        animal_final,
        plant_instance,
        plant_initial,
        plant_final,
    ):
        """Testing eat for varying plant and animal energy levels."""
        animal_instance.stored_energy = animal_initial
        plant_instance.energy = plant_initial
        animal_instance.eat(plant_instance)
        assert animal_instance.stored_energy == animal_final
        assert plant_instance.energy == plant_final

    @pytest.mark.parametrize(
        "soil_initial, soil_final, consumed_energy",
        [
            (1000.0, 1100.0, 1000.0),
            (0.0, 100.0, 1000.0),
            (1000.0, 1000.0, 0.0),
            (0.0, 0.0, 0.0),
        ],
    )
    def test_excrete(
        self, animal_instance, soil_instance, soil_initial, soil_final, consumed_energy
    ):
        """Testing excrete() for varying soil energy levels."""
        soil_instance.energy = soil_initial
        animal_instance.excrete(soil_instance, consumed_energy)
        assert soil_instance.energy == soil_final

    @pytest.mark.parametrize(
        "dt, initial_age, final_age",
        [
            (timedelta64(0, "D"), 0.0, 0.0),
            (timedelta64(1, "D"), 0.0, 1.0),
            (timedelta64(0, "D"), 3.0, 3.0),
            (timedelta64(90, "D"), 10.0, 100.0),
        ],
    )
    def test_aging(self, animal_instance, dt, initial_age, final_age):
        """Testing aging at varying ages."""
        animal_instance.age = initial_age
        animal_instance.aging(dt)
        assert animal_instance.age == final_age
