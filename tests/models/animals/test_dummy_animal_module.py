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
        assert animal_instance.metabolic_rate == 722123702.8286058
        assert animal_instance.stored_energy == 28266000000.0

    @pytest.mark.parametrize(
        "dt, initial, final",
        [
            (timedelta64(1, "D"), 10000.0, 9136.0),
            (timedelta64(1, "D"), 500.0, 0.0),
            (timedelta64(1, "D"), 0.0, 0.0),
            (timedelta64(5, "D"), 10000.0, 5680.0),
        ],
    )
    def test_metabolize(self, animal_instance, dt, initial, final):
        """Testing metabolize at varying energy levels."""
        animal_instance.stored_energy = initial
        animal_instance.metabolize(dt)
        assert animal_instance.stored_energy == final

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
