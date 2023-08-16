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
def herb_functional_group_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list[3]


@pytest.fixture
def pred_functional_group_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list[2]


@pytest.fixture
def predator_cohort_instance(pred_functional_group_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(pred_functional_group_instance, 10000.0, 1)


@pytest.fixture
def prey_cohort_instance(herb_functional_group_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(herb_functional_group_instance, 100.0, 1)


@pytest.fixture
def herb_cohort_instance(herb_functional_group_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(herb_functional_group_instance, 10000.0, 1)


@pytest.fixture
def carcass_instance():
    """Fixture for an carcass pool used in tests."""
    from virtual_rainforest.models.animals.carcasses_and_poo import CarcassPool

    return CarcassPool(0.0, 4)


class TestAnimalCohort:
    """Test AnimalCohort class."""

    def test_initialization(self, herb_cohort_instance):
        """Testing initialization of derived parameters for animal cohorts."""
        assert herb_cohort_instance.individuals == 1
        assert herb_cohort_instance.metabolic_rate == pytest.approx(
            3200.9029380, rel=1e-6
        )
        assert herb_cohort_instance.stored_energy == pytest.approx(
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
        self, herb_functional_group_instance, functional_group, mass, age, error_type
    ):
        """Test for invalid inputs during AnimalCohort initialization."""
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

        with pytest.raises(error_type):
            AnimalCohort(functional_group(herb_functional_group_instance), mass, age)

    @pytest.mark.parametrize(
        "dt, initial_energy, final_energy",
        [
            (timedelta64(1, "D"), 28266000000.0, 27989441986.150745),
            (timedelta64(1, "D"), 500.0, 0.0),
            (timedelta64(1, "D"), 0.0, 0.0),
            (timedelta64(3, "D"), 28266000000.0, 27436325958.45224),
        ],
    )
    def test_metabolize(self, herb_cohort_instance, dt, initial_energy, final_energy):
        """Testing metabolize at varying energy levels."""
        herb_cohort_instance.stored_energy = initial_energy
        herb_cohort_instance.metabolize(dt)
        assert herb_cohort_instance.stored_energy == final_energy

    @pytest.mark.parametrize(
        "dt, initial_energy, error_type",
        [
            (-1, 28266000000.0, ValueError),
            (timedelta64(1, "D"), -100.0, ValueError),
        ],
    )
    def test_metabolize_invalid_input(
        self, herb_cohort_instance, dt, initial_energy, error_type
    ):
        """Testing metabolize with invalid inputs."""
        herb_cohort_instance.stored_energy = initial_energy
        with pytest.raises(error_type):
            herb_cohort_instance.metabolize(dt)

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
        herb_cohort_instance,
        soil_instance,
        soil_initial,
        soil_final,
        consumed_energy,
    ):
        """Testing excrete() for varying soil energy levels."""
        soil_instance.stored_energy = soil_initial
        herb_cohort_instance.excrete(soil_instance, consumed_energy)
        assert soil_instance.stored_energy == soil_final

    @pytest.mark.parametrize(
        "dt, initial_age, final_age",
        [
            (timedelta64(0, "D"), 0.0, 0.0),
            (timedelta64(1, "D"), 0.0, 1.0),
            (timedelta64(0, "D"), 3.0, 3.0),
            (timedelta64(90, "D"), 10.0, 100.0),
        ],
    )
    def test_increase_age(self, herb_cohort_instance, dt, initial_age, final_age):
        """Testing aging at varying ages."""
        herb_cohort_instance.age = initial_age
        herb_cohort_instance.increase_age(dt)
        assert herb_cohort_instance.age == final_age

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
        herb_cohort_instance,
        number_dead,
        initial_pop,
        final_pop,
        carcass_instance,
        initial_carcass,
        final_carcass,
    ):
        """Testing death."""
        herb_cohort_instance.individuals = initial_pop
        carcass_instance.stored_energy = initial_carcass
        herb_cohort_instance.die_individual(number_dead, carcass_instance)
        assert herb_cohort_instance.individuals == final_pop
        assert carcass_instance.stored_energy == final_carcass

    def test_get_eaten(
        self, prey_cohort_instance, predator_cohort_instance, carcass_instance
    ):
        """Testing get_eaten.

        Currently, this just tests rough execution. As the model gets paramterized,
        these tests will be expanded to specific values.
        """

        initial_individuals = prey_cohort_instance.individuals
        initial_stored_energy = carcass_instance.stored_energy

        # Execution
        prey_cohort_instance.get_eaten(predator_cohort_instance, carcass_instance)

        # Assertions
        assert prey_cohort_instance.individuals < initial_individuals
        assert carcass_instance.stored_energy > initial_stored_energy

    def test_forage_cohort(
        self, predator_cohort_instance, prey_cohort_instance, mocker
    ):
        """Testing forage_cohort."""
        # Setup
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort
        from virtual_rainforest.models.animals.animal_traits import DietType
        from virtual_rainforest.models.animals.carcasses_and_poo import (
            CarcassPool,
            ExcrementPool,
        )
        from virtual_rainforest.models.animals.dummy_plants_and_soil import (
            PalatableSoil,
            PlantCommunity,
        )

        # Mocking the eat method of AnimalCohort
        mock_eat = mocker.patch.object(AnimalCohort, "eat")

        # Instances
        plant_list_instance = [mocker.MagicMock(spec=PlantCommunity)]
        animal_list_instance = [
            mocker.MagicMock(spec=AnimalCohort) for _ in range(3)
        ]  # Assuming 3 animal cohorts
        carcass_pool_instance = mocker.MagicMock(spec=CarcassPool)
        soil_pool_instance = mocker.MagicMock(spec=PalatableSoil)
        soil_pool_instance.stored_energy = 0  # setting the attribute on the mock
        excrement_pool_instance = mocker.MagicMock(spec=ExcrementPool)
        excrement_pool_instance.stored_energy = 0  # setting the attribute on the mock

        animal_cohort_instances = [predator_cohort_instance, prey_cohort_instance]

        for animal_cohort_instance in animal_cohort_instances:
            # Execution
            animal_cohort_instance.forage_cohort(
                plant_list=plant_list_instance,
                animal_list=animal_list_instance,
                carcass_pool=carcass_pool_instance,
                soil_pool=soil_pool_instance,
                excrement_pool=excrement_pool_instance,
            )

            # Assertions
            if animal_cohort_instance.functional_group.diet == DietType.HERBIVORE:
                mock_eat.assert_called_with(
                    plant_list_instance[0], soil_pool_instance
                )  # Assuming just one plant instance for simplicity
            elif animal_cohort_instance.functional_group.diet == DietType.CARNIVORE:
                # Ensure eat was called for each animal in the list
                assert len(mock_eat.call_args_list) == 1
                for call in mock_eat.call_args_list:
                    # Ensure each call had a single AnimalCohort and the CarcassPool
                    args, _ = call
                    assert args[0] in animal_list_instance
                    assert args[1] == carcass_pool_instance

            # Reset mock_eat for next iteration
            mock_eat.reset_mock()

    def test_eat(self, herb_cohort_instance, mocker):
        """Testing eat."""
        from virtual_rainforest.models.animals.protocols import Pool, Resource

        mock_food = mocker.MagicMock(spec=Resource)
        mock_pool = mocker.MagicMock(spec=Pool)

        herb_cohort_instance.individuals = (
            10  # Setting a non-zero value for individuals
        )
        herb_cohort_instance.stored_energy = (
            0  # Setting initial energy to 0 for simplicity
        )

        # Mocking get_eaten to return a fixed energy value
        mock_energy_return = 100  # Example energy return value
        mock_food.get_eaten.return_value = mock_energy_return

        # Execution
        herb_cohort_instance.eat(mock_food, mock_pool)

        # Assertions
        mock_food.get_eaten.assert_called_once_with(herb_cohort_instance, mock_pool)
        assert (
            herb_cohort_instance.stored_energy
            == mock_energy_return / herb_cohort_instance.individuals
        )

        # Test ValueError for zero individuals
        herb_cohort_instance.individuals = 0
        with pytest.raises(ValueError, match="Individuals cannot be 0."):
            herb_cohort_instance.eat(mock_food, mock_pool)

    def test_can_reproduce_method(self, herb_cohort_instance):
        """Test the can_reproduce method of AnimalCohort."""

        # 1. Test when stored_energy is exactly equal to the threshold
        herb_cohort_instance.stored_energy = (
            herb_cohort_instance.reproduction_energy_threshold
        )
        assert herb_cohort_instance.can_reproduce()

        # 2. Test when stored_energy is just below the threshold
        herb_cohort_instance.stored_energy = (
            herb_cohort_instance.reproduction_energy_threshold - 0.01
        )
        assert not herb_cohort_instance.can_reproduce()

        # 3. Test when stored_energy is above the threshold
        herb_cohort_instance.stored_energy = (
            herb_cohort_instance.reproduction_energy_threshold + 0.01
        )
        assert herb_cohort_instance.can_reproduce()

        # 4. Test with stored_energy set to 0
        herb_cohort_instance.stored_energy = 0.0
        assert not herb_cohort_instance.can_reproduce()
