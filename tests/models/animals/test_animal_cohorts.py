"""Test module for animal_cohorts.py."""

import pytest
from numpy import isclose, timedelta64


@pytest.fixture
def predator_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[2]


@pytest.fixture
def predator_cohort_instance(predator_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(
        predator_functional_group_instance, 10000.0, 1, 10, constants_instance
    )


@pytest.fixture
def ectotherm_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[5]


@pytest.fixture
def ectotherm_cohort_instance(ectotherm_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(
        ectotherm_functional_group_instance, 100.0, 1, 10, constants_instance
    )


@pytest.fixture
def prey_cohort_instance(herbivore_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(
        herbivore_functional_group_instance, 100.0, 1, 10, constants_instance
    )


@pytest.fixture
def carcass_instance():
    """Fixture for an carcass pool used in tests."""
    from virtual_rainforest.models.animals.decay import CarcassPool

    return CarcassPool(0.0, 0.0)


class TestAnimalCohort:
    """Test AnimalCohort class."""

    def test_initialization(self, herbivore_cohort_instance):
        """Testing initialization of derived parameters for animal cohorts."""
        assert herbivore_cohort_instance.individuals == 10
        assert herbivore_cohort_instance.mass_current == 10000.0

    @pytest.mark.parametrize(
        "functional_group, mass, age, individuals, error_type",
        [
            (lambda fg: fg, -1000.0, 1.0, 10, ValueError),
            (lambda fg: fg, 1000.0, -1.0, 10, ValueError),
        ],
    )
    def test_invalid_animal_cohort_initialization(
        self,
        herbivore_functional_group_instance,
        functional_group,
        mass,
        age,
        individuals,
        error_type,
        constants_instance,
    ):
        """Test for invalid inputs during AnimalCohort initialization."""
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

        with pytest.raises(error_type):
            AnimalCohort(
                functional_group(herbivore_functional_group_instance),
                mass,
                age,
                individuals,
                constants_instance,
            )

    @pytest.mark.parametrize(
        "dt, initial_mass, temperature, final_mass",
        [
            (timedelta64(1, "D"), 1000.0, 298.0, 998.5205247106326),  # normal case
            (timedelta64(1, "D"), 0.0, 298.0, 0.0),  # edge case: zero mass
            (timedelta64(3, "D"), 1000.0, 298.0, 995.5615741318977),  # 3 days
        ],
    )
    def test_metabolize_endotherm(
        self, herbivore_cohort_instance, dt, initial_mass, temperature, final_mass
    ):
        """Testing metabolize with an endothermic metabolism."""
        herbivore_cohort_instance.mass_current = initial_mass
        herbivore_cohort_instance.metabolize(temperature, dt)
        assert herbivore_cohort_instance.mass_current == final_mass
        assert isclose(herbivore_cohort_instance.mass_current, final_mass, rtol=1e-9)

    @pytest.mark.parametrize(
        "dt, initial_mass, temperature, final_mass",
        [
            (timedelta64(1, "D"), 100.0, 20.0, 99.95896219913648),  # normal case
            (timedelta64(1, "D"), 0.0, 20.0, 0.0),  # edge case: zero mass
            (
                timedelta64(1, "D"),
                100.0,
                0.0,
                99.99436706014961,
            ),  # edge case: zero temperature
        ],
    )
    def test_metabolize_ectotherm(
        self, ectotherm_cohort_instance, dt, initial_mass, temperature, final_mass
    ):
        """Testing metabolize with ectotherms."""
        # from math import isclose

        ectotherm_cohort_instance.mass_current = initial_mass
        ectotherm_cohort_instance.metabolize(temperature, dt)
        assert ectotherm_cohort_instance.mass_current == final_mass

    @pytest.mark.parametrize(
        "dt, initial_mass, temperature, error_type",
        [
            (timedelta64(-1, "D"), 28266000000.0, 298.0, ValueError),
            (timedelta64(1, "D"), -100.0, 298.0, ValueError),
            # Add more invalid cases as needed
        ],
    )
    def test_metabolize_invalid_input(
        self, herbivore_cohort_instance, dt, initial_mass, temperature, error_type
    ):
        """Testing metabolize for invalid input."""
        herbivore_cohort_instance.mass_current = initial_mass
        with pytest.raises(error_type):
            herbivore_cohort_instance.metabolize(temperature, dt)

    @pytest.mark.parametrize(
        "scav_initial, scav_final, decomp_initial, decomp_final, consumed_energy",
        [
            (1000.0, 1500.0, 0.0, 500.0, 1000.0),
            (0.0, 500.0, 1000.0, 1500.0, 1000.0),
            (1000.0, 1000.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 1000.0, 1000.0, 0.0),
        ],
    )
    def test_excrete(
        self,
        herbivore_cohort_instance,
        excrement_instance,
        scav_initial,
        scav_final,
        decomp_initial,
        decomp_final,
        consumed_energy,
    ):
        """Testing excrete() for varying soil energy levels."""
        excrement_instance.scavengeable_energy = scav_initial
        excrement_instance.decomposed_energy = decomp_initial
        herbivore_cohort_instance.excrete(excrement_instance, consumed_energy)
        assert excrement_instance.scavengeable_energy == scav_final
        assert excrement_instance.decomposed_energy == decomp_final

    @pytest.mark.parametrize(
        "dt, initial_age, final_age",
        [
            (timedelta64(0, "D"), 0.0, 0.0),
            (timedelta64(1, "D"), 0.0, 1.0),
            (timedelta64(0, "D"), 3.0, 3.0),
            (timedelta64(90, "D"), 10.0, 100.0),
        ],
    )
    def test_increase_age(self, herbivore_cohort_instance, dt, initial_age, final_age):
        """Testing aging at varying ages."""
        herbivore_cohort_instance.age = initial_age
        herbivore_cohort_instance.increase_age(dt)
        assert herbivore_cohort_instance.age == final_age

    @pytest.mark.parametrize(
        argnames=[
            "number_dead",
            "initial_pop",
            "final_pop",
            "initial_carcass",
            "final_carcass",
            "decomp_carcass",
        ],
        argvalues=[
            (0, 0, 0, 0.0, 0.0, 0.0),
            (0, 1000, 1000, 0.0, 0.0, 0.0),
            (1, 1, 0, 1.0, 8001.0, 2000.0),
            (100, 200, 100, 0.0, 800000.0, 200000.0),
        ],
    )
    def test_die_individual(
        self,
        herbivore_cohort_instance,
        number_dead,
        initial_pop,
        final_pop,
        carcass_instance,
        initial_carcass,
        final_carcass,
        decomp_carcass,
    ):
        """Testing death."""
        herbivore_cohort_instance.individuals = initial_pop
        carcass_instance.scavengeable_energy = initial_carcass
        herbivore_cohort_instance.die_individual(number_dead, carcass_instance)
        assert herbivore_cohort_instance.individuals == final_pop
        assert carcass_instance.scavengeable_energy == final_carcass
        assert carcass_instance.decomposed_energy == decomp_carcass

    def test_get_eaten(
        self, prey_cohort_instance, predator_cohort_instance, carcass_instance
    ):
        """Testing get_eaten.

        Currently, this just tests rough execution. As the model gets paramterized,
        these tests will be expanded to specific values.
        """

        initial_individuals = prey_cohort_instance.individuals
        initial_scavengeable_energy = carcass_instance.scavengeable_energy

        # Execution
        prey_cohort_instance.get_eaten(predator_cohort_instance, carcass_instance)

        # Assertions
        assert prey_cohort_instance.individuals < initial_individuals
        assert carcass_instance.scavengeable_energy > initial_scavengeable_energy
        assert carcass_instance.decomposed_energy > 0.0

    def test_forage_cohort(
        self, predator_cohort_instance, prey_cohort_instance, mocker
    ):
        """Testing forage_cohort."""
        # Setup
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort
        from virtual_rainforest.models.animals.animal_traits import DietType
        from virtual_rainforest.models.animals.decay import CarcassPool, ExcrementPool
        from virtual_rainforest.models.animals.plant_resources import PlantResources

        # Mocking the eat method of AnimalCohort
        mock_eat = mocker.patch.object(AnimalCohort, "eat")

        # Instances
        plant_list_instance = [mocker.MagicMock(spec=PlantResources)]
        animal_list_instance = [
            mocker.MagicMock(spec=AnimalCohort) for _ in range(3)
        ]  # Assuming 3 animal cohorts
        carcass_pool_instance = mocker.MagicMock(spec=CarcassPool)
        excrement_pool_instance = mocker.MagicMock(spec=ExcrementPool)
        excrement_pool_instance.scavengeable_energy = 0
        excrement_pool_instance.decomposed_energy = 0

        animal_cohort_instances = [predator_cohort_instance, prey_cohort_instance]

        for animal_cohort_instance in animal_cohort_instances:
            # Execution
            animal_cohort_instance.forage_cohort(
                plant_list=plant_list_instance,
                animal_list=animal_list_instance,
                carcass_pool=carcass_pool_instance,
                excrement_pool=excrement_pool_instance,
            )

            # Assertions
            if animal_cohort_instance.functional_group.diet == DietType.HERBIVORE:
                mock_eat.assert_called_with(
                    plant_list_instance[0], excrement_pool_instance
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

    def test_eat(self, herbivore_cohort_instance, mocker):
        """Testing eat."""
        from virtual_rainforest.models.animals.protocols import Pool, Resource

        mock_food = mocker.MagicMock(spec=Resource)
        mock_pool = mocker.MagicMock(spec=Pool)

        # Common Setup
        herbivore_cohort_instance.individuals = 10
        mock_mass_return = 100
        mock_food.get_eaten.return_value = mock_mass_return

        # Scenario 1: Test mass_current is updated when below threshold
        herbivore_cohort_instance.mass_current = 0  # Resetting for test
        herbivore_cohort_instance.reproductive_mass = 0  # Resetting for test
        herbivore_cohort_instance.is_below_mass_threshold = mocker.MagicMock(
            return_value=True
        )

        # Execution
        herbivore_cohort_instance.eat(mock_food, mock_pool)

        # Assertions for Scenario 1
        assert (
            herbivore_cohort_instance.mass_current
            == mock_mass_return / herbivore_cohort_instance.individuals
        )
        assert herbivore_cohort_instance.reproductive_mass == 0

        # Scenario 2: Test reproductive_mass is updated when above threshold
        herbivore_cohort_instance.mass_current = 0  # Resetting for test
        herbivore_cohort_instance.reproductive_mass = 0  # Resetting for test
        herbivore_cohort_instance.is_below_mass_threshold = mocker.MagicMock(
            return_value=False
        )

        # Execution
        herbivore_cohort_instance.eat(mock_food, mock_pool)

        # Assertions for Scenario 2
        assert (
            herbivore_cohort_instance.reproductive_mass
            == mock_mass_return / herbivore_cohort_instance.individuals
        )
        assert herbivore_cohort_instance.mass_current == 0

    def test_is_below_mass_threshold(
        self, herbivore_cohort_instance, constants_instance
    ):
        """Test the can_reproduce method of AnimalCohort."""

        # TODO: test other mass thresholds
        # 1. Test when stored_energy is exactly equal to the threshold
        herbivore_cohort_instance.mass_current = (
            herbivore_cohort_instance.functional_group.adult_mass
            * constants_instance.birth_mass_threshold
        )
        assert not herbivore_cohort_instance.is_below_mass_threshold(
            constants_instance.birth_mass_threshold
        )

        # 2. Test when stored_energy is just below the threshold
        herbivore_cohort_instance.mass_current = (
            herbivore_cohort_instance.functional_group.adult_mass
            * constants_instance.birth_mass_threshold
            - 0.01
        )
        assert herbivore_cohort_instance.is_below_mass_threshold(
            constants_instance.birth_mass_threshold
        )

        # 3. Test when stored_energy is above the threshold
        herbivore_cohort_instance.mass_current = (
            herbivore_cohort_instance.functional_group.adult_mass
            * constants_instance.birth_mass_threshold
            + 0.01
        )
        assert not herbivore_cohort_instance.is_below_mass_threshold(
            constants_instance.birth_mass_threshold
        )

        # 4. Test with stored_energy set to 0
        herbivore_cohort_instance.mass_current = 0.0
        assert herbivore_cohort_instance.is_below_mass_threshold(
            constants_instance.birth_mass_threshold
        )

    @pytest.mark.parametrize(
        "initial_individuals, number_days, mortality_prob",
        [(100, 10.0, 0.01), (1000, 20.0, 0.05), (0, 10.0, 0.01), (100, 10.0, 0.0)],
    )
    def test_inflict_natural_mortality(
        self,
        herbivore_cohort_instance,
        carcass_instance,
        mocker,
        initial_individuals,
        number_days,
        mortality_prob,
    ):
        """Testing inflict natural mortality method."""
        from random import seed

        from numpy import floor

        seed(42)

        expected_deaths = initial_individuals * (
            1 - (1 - mortality_prob) ** number_days
        )
        expected_deaths = int(floor(expected_deaths))

        # Set individuals and adult natural mortality probability
        herbivore_cohort_instance.individuals = initial_individuals
        herbivore_cohort_instance.adult_natural_mortality_prob = mortality_prob

        # Mock the random.binomial call
        mocker.patch(
            "virtual_rainforest.models.animals.animal_cohorts.random.binomial",
            return_value=expected_deaths,
        )
        # Keep a copy of initial individuals to validate number_of_deaths
        initial_individuals_copy = herbivore_cohort_instance.individuals

        # Call the inflict_natural_mortality method
        herbivore_cohort_instance.inflict_natural_mortality(
            carcass_instance, number_days
        )

        # Verify the number_of_deaths and remaining individuals
        assert (
            herbivore_cohort_instance.individuals
            == initial_individuals_copy - expected_deaths
        )
