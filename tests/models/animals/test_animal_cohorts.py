"""Test module for animal_cohorts.py."""

import pytest
from numpy import timedelta64


@pytest.fixture
def plant_instance():
    """Fixture for a plant community used in tests."""
    from virtual_rainforest.models.animals.dummy_plants_and_soil import PlantCommunity

    return PlantCommunity(10000.0, 1)


@pytest.fixture
def soil_instance():
    """Fixture for a soil pool used in tests."""
    from virtual_rainforest.models.animals.dummy_plants_and_soil import PalatableSoil

    return PalatableSoil(100000.0, 4)


@pytest.fixture
def animal_model_instance():
    """Fixture for an animal model used in tests."""
    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    test_grid = Grid(cell_nx=3, cell_ny=3)
    test_data = Data(test_grid)
    test_config = {
        "core": {"timing": {"start_date": "2020-01-01"}},
        "animals": {"model_time_step": "12 hours"},
    }
    return AnimalModel.from_config(test_data, test_config)


@pytest.fixture
def functional_group_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list[3]


@pytest.fixture
def animal_cohort_instance(functional_group_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(functional_group_instance, 10000.0, 1)


@pytest.fixture
def carcass_instance():
    """Fixture for an carcass pool used in tests."""
    from virtual_rainforest.models.animals.carcasses import CarcassPool

    return CarcassPool(0.0, 4)


class TestAnimalCohort:
    """Test AnimalCohort class."""

    def test_initialization(self, animal_cohort_instance):
        """Testing initialization of derived parameters for animal cohorts."""
        assert animal_cohort_instance.individuals == 1
        assert animal_cohort_instance.metabolic_rate == pytest.approx(
            3200.9029380, rel=1e-6
        )
        assert animal_cohort_instance.stored_energy == pytest.approx(
            56531469253.03123, rel=1e-6
        )

    @pytest.mark.parametrize(
        "functional_group, mass, age, error_type",
        [
            (lambda fg: fg, -1000.0, 1.0, ValueError),
            (lambda fg: fg, 1000.0, -1.0, ValueError),
        ],
    )
    def test_invalid_animal_cohort_initialization(
        self, functional_group_instance, functional_group, mass, age, error_type
    ):
        """Test for invalid inputs during AnimalCohort initialization."""
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

        with pytest.raises(error_type):
            AnimalCohort(functional_group(functional_group_instance), mass, age)

    @pytest.mark.parametrize(
        "dt, initial_energy, final_energy",
        [
            (timedelta64(1, "D"), 28266000000.0, 27989441986.150745),
            (timedelta64(1, "D"), 500.0, 0.0),
            (timedelta64(1, "D"), 0.0, 0.0),
            (timedelta64(3, "D"), 28266000000.0, 27436325958.45224),
        ],
    )
    def test_metabolize(self, animal_cohort_instance, dt, initial_energy, final_energy):
        """Testing metabolize at varying energy levels."""
        animal_cohort_instance.stored_energy = initial_energy
        animal_cohort_instance.metabolize(dt)
        assert animal_cohort_instance.stored_energy == final_energy

    @pytest.mark.parametrize(
        "dt, initial_energy, error_type",
        [
            (-1, 28266000000.0, ValueError),
            (timedelta64(1, "D"), -100.0, ValueError),
        ],
    )
    def test_metabolize_invalid_input(
        self, animal_cohort_instance, dt, initial_energy, error_type
    ):
        """Testing metabolize with invalid inputs."""
        animal_cohort_instance.stored_energy = initial_energy
        with pytest.raises(error_type):
            animal_cohort_instance.metabolize(dt)

    @pytest.mark.parametrize(
        "animal_initial, animal_final, plant_initial, plant_final",
        [
            (28266000000.0, 28608685465.02244, 182000000000.0, 178192383721.97287),
            (0.0, 342685465.02244186, 182000000000.0, 178192383721.97287),
            (28266000000.0, 28266000009.0, 100.0, 0.0),
            (28266000000.0, 28266000000.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
        ],
    )
    def test_herbivory(
        self,
        animal_cohort_instance,
        animal_initial,
        animal_final,
        plant_instance,
        plant_initial,
        plant_final,
        soil_instance,
    ):
        """Testing eat for varying plant and animal energy levels."""
        animal_cohort_instance.stored_energy = animal_initial
        plant_instance.energy = plant_initial
        animal_cohort_instance.herbivory(plant_instance, soil_instance)
        assert animal_cohort_instance.stored_energy == animal_final
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
        self,
        animal_cohort_instance,
        soil_instance,
        soil_initial,
        soil_final,
        consumed_energy,
    ):
        """Testing excrete() for varying soil energy levels."""
        soil_instance.energy = soil_initial
        animal_cohort_instance.excrete(soil_instance, consumed_energy)
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
    def test_aging(self, animal_cohort_instance, dt, initial_age, final_age):
        """Testing aging at varying ages."""
        animal_cohort_instance.age = initial_age
        animal_cohort_instance.aging(dt)
        assert animal_cohort_instance.age == final_age

    @pytest.mark.parametrize(
        "number_dead, initial_pop, final_pop, initial_carcass, final_carcass",
        [
            (0, 0, 0, 0.0, 0.0),
            (0, 1000, 1000, 0.0, 0.0),
            (1, 1, 0, 1.0, 70000001.0),
            (100, 200, 100, 0.0, 7000000000.0),
        ],
    )
    def test_die_individual(
        self,
        animal_cohort_instance,
        number_dead,
        initial_pop,
        final_pop,
        carcass_instance,
        initial_carcass,
        final_carcass,
    ):
        """Testing aging at varying ages."""
        animal_cohort_instance.individuals = initial_pop
        carcass_instance.energy = initial_carcass
        animal_cohort_instance.die_individual(number_dead, carcass_instance)
        assert animal_cohort_instance.individuals == final_pop
        assert carcass_instance.energy == final_carcass

    @pytest.mark.parametrize(
        """animal_initial, animal_final, plant_initial, plant_final, soil_initial,
        soil_final""",
        [
            (
                28266000000.0,
                28608685465.02244,
                182000000000.0,
                178192383721.97287,
                1000.0,
                761524255.60542,
            ),
            (
                0.0,
                342685465.02244,
                182000000000.0,
                178192383721.97287,
                1000.0,
                761524255.60542,
            ),
            (28266000000.0, 28266000010.0, 100.0, 0.0, 1000.0, 1020.0),
            (28266000000.0, 28266000000.0, 0.0, 0.0, 1000.0, 1000.0),
            (0.0, 0.0, 0.0, 0.0, 1000.0, 1000.0),
        ],
    )
    def test_forage_cohort(
        self,
        animal_cohort_instance,
        animal_initial,
        animal_final,
        plant_instance,
        plant_initial,
        plant_final,
        soil_instance,
        soil_initial,
        soil_final,
    ):
        """Testing forage."""
        animal_cohort_instance.stored_energy = animal_initial
        plant_instance.energy = plant_initial
        soil_instance.energy = soil_initial
        animal_cohort_instance.forage_cohort(plant_instance, soil_instance)
        assert animal_cohort_instance.stored_energy == pytest.approx(
            animal_final, rel=1e-6
        )
        assert plant_instance.energy == pytest.approx(plant_final, rel=1e-6)
        assert soil_instance.energy == pytest.approx(soil_final, rel=1e-6)
