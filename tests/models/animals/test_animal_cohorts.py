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


def test_calculate_alpha(herbivore_cohort_instance):
    """Test the calculation of search efficiency based on the cohort's current mass."""

    from unittest.mock import patch

    with patch(
        "virtual_rainforest.models.animals.scaling_functions.alpha_i_k",
        return_value=0.1,
    ) as mock_alpha:
        alpha = herbivore_cohort_instance.calculate_alpha()
        mock_alpha.assert_called_once_with(
            herbivore_cohort_instance.constants.alpha_0_herb,
            herbivore_cohort_instance.mass_current,
        )
        assert alpha == 0.1


def test_calculate_potential_consumed_biomass(
    herbivore_cohort_instance, plant_instance
):
    """Test the calculation of potential consumed biomass for a target plant."""

    from unittest.mock import patch

    alpha = 0.1  # Assume this is the calculated search efficiency
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.k_i_k", return_value=20.0
    ) as mock_k:
        biomass = herbivore_cohort_instance.calculate_potential_consumed_biomass(
            plant_instance, alpha
        )
        mock_k.assert_called_once_with(
            alpha,
            herbivore_cohort_instance.functional_group.constants.phi_herb_t,
            plant_instance.mass_current,
            1.0,
        )  # Assuming A_cell is temporarily 1.0
        assert biomass == 20.0


def calculate_total_handling_time_for_herbivory(
    herbivore_cohort_instance, plant_list_instance
):
    """Test the aggregation of handling times across all available plant resources."""

    from unittest.mock import patch

    alpha = 0.1  # Assume this is the calculated search efficiency
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.k_i_k", return_value=20.0
    ), patch(
        "virtual_rainforest.models.animals.scaling_functions.H_i_k", return_value=0.2
    ):
        total_handling_time = (
            herbivore_cohort_instance.calculate_total_handling_time_for_herbivory(
                plant_list_instance, alpha
            )
        )
        # Assert based on expected behavior; this will need to be adjusted based on the
        # number of plants and their handling times
        expected_handling_time = sum(
            [20.2 for _ in plant_list_instance]
        )  # Simplified; adjust calculation as needed
        assert total_handling_time == pytest.approx(expected_handling_time, rel=1e-6)


def test_F_i_k(herbivore_cohort_instance, plant_list_instance):
    """Test F_i_k."""

    from unittest.mock import patch

    target_plant = plant_list_instance[0]

    with patch(
        (
            "virtual_rainforest.models.animals.animal_cohorts."
            "AnimalCohort.calculate_alpha"
        ),
        return_value=0.1,
    ) as mock_alpha, patch(
        (
            "virtual_rainforest.models.animals.animal_cohorts."
            "AnimalCohort.calculate_potential_consumed_biomass"
        ),
        return_value=20.0,
    ) as mock_potential_biomass, patch(
        (
            "virtual_rainforest.models.animals.animal_cohorts."
            "AnimalCohort.calculate_total_handling_time_for_herbivory"
        ),
        return_value=40.4,
    ) as mock_total_handling:
        rate = herbivore_cohort_instance.F_i_k(plant_list_instance, target_plant)

        mock_alpha.assert_called_once()
        mock_potential_biomass.assert_called_once_with(target_plant, 0.1)
        mock_total_handling.assert_called_once_with(plant_list_instance, 0.1)

        N = herbivore_cohort_instance.individuals
        B_k = target_plant.mass_current
        expected_rate = N * (20.0 / (1 + 40.4)) * (1 / B_k)

        assert rate == pytest.approx(expected_rate, rel=1e-6)


def test_calculate_theta_opt_i(herbivore_cohort_instance):
    """Test calculate_theta_opt_i for correct optimal predation parameter."""
    from unittest.mock import patch

    # Mocking the theta_opt_i function from the scaling_functions module
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.theta_opt_i",
        return_value=0.5,
    ) as mock_theta_opt:
        result = herbivore_cohort_instance.calculate_theta_opt_i()

        # Verifying that theta_opt_i was called with the correct parameters
        mock_theta_opt.assert_called_once_with(
            herbivore_cohort_instance.constants.theta_opt_min_f,
            herbivore_cohort_instance.constants.theta_opt_f,
            herbivore_cohort_instance.constants.sigma_opt_f,
        )

        # Asserting the result matches the mocked return value
        assert result == 0.5, "Expected optimal predation parameter not returned."


def test_calculate_predation_success_probability(herbivore_cohort_instance):
    """Test successful predation probability calculation."""
    from unittest.mock import patch

    target_mass = 50.0  # Example target mass

    # Patch both calculate_theta_opt_i and w_bar_i_j for isolation
    with patch(
        "virtual_rainforest.models.animals.animal_cohorts."
        "AnimalCohort.calculate_theta_opt_i",
        return_value=0.7,
    ) as mock_theta_opt, patch(
        "virtual_rainforest.models.animals.scaling_functions.w_bar_i_j",
        return_value=0.6,
    ) as mock_w_bar:
        result = herbivore_cohort_instance.calculate_predation_success_probability(
            target_mass
        )

        # Ensure calculate_theta_opt_i is called within the method
        mock_theta_opt.assert_called_once()

        # Verify that w_bar_i_j was called with the correct parameters
        mock_w_bar.assert_called_once_with(
            herbivore_cohort_instance.mass_current,
            target_mass,
            0.7,  # Expect theta_opt_i from mocked calculate_theta_opt_i return value
            herbivore_cohort_instance.constants.sigma_opt_pred_prey,
        )

        # Asserting the result matches the mocked return value
        assert result == 0.6, "Expected predation success probability not returned."


def test_calculate_predation_search_rate(herbivore_cohort_instance):
    """Test predation search rate calculation."""
    from unittest.mock import patch

    success_probability = 0.5  # Example success probability

    # Mock the alpha_i_j function to isolate and control its output
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.alpha_i_j",
        return_value=0.8,
    ) as mock_alpha_i_j:
        result = herbivore_cohort_instance.calculate_predation_search_rate(
            success_probability
        )

        # Verify that alpha_i_j was called with the correct parameters
        mock_alpha_i_j.assert_called_once_with(
            herbivore_cohort_instance.constants.alpha_0_pred,
            herbivore_cohort_instance.mass_current,
            success_probability,
        )

        # Asserting the result matches the mocked return value
        assert result == 0.8, "Expected predation search rate not returned."


def test_calculate_potential_prey_consumed(herbivore_cohort_instance):
    """Test calculation of potential number of prey consumed."""
    from unittest.mock import patch

    alpha = 0.8  # Example search rate
    theta_i_j = 0.7  # Example predation parameter

    # Mock the k_i_j function to control its output
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.k_i_j", return_value=15.0
    ) as mock_k_i_j:
        result = herbivore_cohort_instance.calculate_potential_prey_consumed(
            alpha, theta_i_j
        )

        # Verify that k_i_j was called with the correct parameters
        mock_k_i_j.assert_called_once_with(
            alpha,
            herbivore_cohort_instance.individuals,
            1.0,  # Assuming A_cell is temporarily set to 1.0
            theta_i_j,
        )

        # Asserting the result matches the mocked return value
        assert result == 15.0, "Expected potential prey consumed not returned."


def test_calculate_total_handling_time_for_predation(herbivore_cohort_instance):
    """Test total handling time calculation for predation."""
    from unittest.mock import patch

    # Example predation search rate
    alpha = 0.8

    # Mock the H_i_j function to control its output
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.H_i_j", return_value=2.5
    ) as mock_H_i_j:
        result = herbivore_cohort_instance.calculate_total_handling_time_for_predation(
            alpha
        )

        # Verify that H_i_j was called with the correct parameters
        mock_H_i_j.assert_called_once_with(
            herbivore_cohort_instance.constants.h_pred_0,
            herbivore_cohort_instance.constants.M_pred_ref,
            herbivore_cohort_instance.mass_current,
            herbivore_cohort_instance.constants.b_pred,
        )

        # Asserting the result matches the mocked return value
        assert result == 2.5, "Expected total handling time for predation not returned."


def test_F_i_j_individual(predator_cohort_instance, animal_list_instance):
    """Test instantaneous predation rate calculation on a selected target cohort."""
    from unittest.mock import patch

    # Selecting a target animal from the provided animal list instance
    target_animal = animal_list_instance[0]

    # Mock all component methods used in F_i_j_individual to isolate integration logic.
    with patch.object(
        predator_cohort_instance,
        "calculate_predation_success_probability",
        return_value=0.5,
    ) as mock_success_prob, patch.object(
        predator_cohort_instance, "calculate_predation_search_rate", return_value=0.8
    ) as mock_search_rate, patch.object(
        predator_cohort_instance, "theta_i_j", return_value=0.7
    ) as mock_theta_i_j, patch.object(
        predator_cohort_instance, "calculate_potential_prey_consumed", return_value=10
    ) as mock_potential_prey, patch.object(
        predator_cohort_instance,
        "calculate_total_handling_time_for_predation",
        return_value=2,
    ) as mock_total_handling:
        # Execute the method under test
        rate = predator_cohort_instance.F_i_j_individual(
            animal_list_instance, target_animal
        )

        # Verify each mocked method was called with expected arguments
        mock_success_prob.assert_called_once_with(target_animal.mass_current)
        mock_search_rate.assert_called_once_with(0.5)  # w_bar from mock_success_prob
        mock_theta_i_j.assert_called_once_with(animal_list_instance)
        mock_potential_prey.assert_called_once_with(
            0.8, 0.7
        )  # alpha from mock_search_rate, theta_i_j from mock_theta_i_j
        mock_total_handling.assert_called_once_with(0.8)  # alpha from mock_search_rate

        # Calculate the expected rate based on the mocked return values and assert
        N_i = predator_cohort_instance.individuals
        N_target = target_animal.individuals
        expected_rate = (
            N_i * (10 / (1 + 2)) * (1 / N_target)
        )  # Using mocked return values
        assert rate == pytest.approx(
            expected_rate
        ), "F_i_j_individual did not return the expected predation rate."


def test_theta_i_j(predator_cohort_instance, animal_list_instance):
    """Test theta_i_j."""
    # TODO change this A_cell to call it from its real plant in the data
    A_cell = (
        1.0  # Define A_cell value used in method implementation, adjust as necessary
    )

    # Execute the method under test
    theta = predator_cohort_instance.theta_i_j(animal_list_instance)

    # Calculate expected theta value considering A_cell
    expected_theta = (
        sum(
            cohort.individuals
            for cohort in animal_list_instance
            if cohort.mass_current == predator_cohort_instance.mass_current
        )
        / A_cell
    )

    assert theta == expected_theta


def test_delta_mass_predation(predator_cohort_instance, animal_list_instance):
    """Test mass assimilation calculation from predation."""

    import math
    from unittest.mock import patch

    # Mocking external calls used in delta_mass_predation
    with patch(
        "virtual_rainforest.models.animals.scaling_functions.theta_opt_i",
        return_value=0.7,
    ), patch(
        "virtual_rainforest.models.animals.scaling_functions.w_bar_i_j",
        return_value=0.5,
    ), patch(
        "virtual_rainforest.models.animals.scaling_functions.alpha_i_j",
        return_value=0.8,
    ), patch(
        "virtual_rainforest.models.animals.scaling_functions.k_i_j", return_value=10
    ), patch(
        "virtual_rainforest.models.animals.scaling_functions.H_i_j", return_value=2
    ), patch(
        "virtual_rainforest.models.animals.scaling_functions.F_i_j_individual",
        return_value=0.3,
    ):
        delta_t = 30.0  # Assuming delta_t is 30 days for the calculation
        tau_f = (
            predator_cohort_instance.constants.tau_f
        )  # Assumed to be available from constants
        sigma_f_t = (
            predator_cohort_instance.constants.sigma_f_t
        )  # Assumed to be available from constants

        # Execute the method under test
        delta_mass = predator_cohort_instance.delta_mass_predation(animal_list_instance)

        # Manually compute the expected delta_mass_pred using mocked return values
        # and provided constants
        expected_delta_mass = sum(
            cohort.mass_current
            * cohort.individuals
            * (
                1
                - math.exp(
                    -0.3 * delta_t * tau_f * sigma_f_t
                )  # Using F, delta_t, tau_f, sigma_f_t
            )
            for cohort in animal_list_instance
        )

        # Assert the calculated delta_mass_pred matches the expected value
        assert delta_mass == pytest.approx(
            expected_delta_mass
        ), "The calculated change in mass from predation did not match expected value."


def test_delta_mass_herbivory(herbivore_cohort_instance, plant_list_instance):
    """Test mass assimilation calculation from herbivory."""
    import math
    from unittest.mock import patch

    # Assuming delta_t, tau_f, and sigma_f_t are known or can be obtained from
    # the herbivore's constants
    delta_t = 30.0  # days, assumed for the calculation
    tau_f = herbivore_cohort_instance.constants.tau_f
    sigma_f_t = herbivore_cohort_instance.constants.sigma_f_t

    # Mock the F_i_k method to control its output
    with patch.object(
        herbivore_cohort_instance, "F_i_k", side_effect=lambda plant_list, plant: 0.1
    ) as mock_F_i_k:
        # Execute the method under test
        delta_mass = herbivore_cohort_instance.delta_mass_herbivory(plant_list_instance)

        # Ensure F_i_k is called for each plant in the list with the correct arguments
        assert mock_F_i_k.call_count == len(plant_list_instance)
        for plant in plant_list_instance:
            mock_F_i_k.assert_any_call(plant_list_instance, plant)

        # Manually compute the expected delta_mass_herb using mocked return values and
        # provided constants
        expected_delta_mass = sum(
            plant.mass_current
            * (
                1
                - math.exp(
                    -0.1 * delta_t * tau_f * sigma_f_t
                )  # Using mocked F value, delta_t, tau_f, sigma_f_t
            )
            for plant in plant_list_instance
        )

        # Assert the calculated delta_mass_herb matches the expected value
        assert delta_mass == pytest.approx(
            expected_delta_mass
        ), "The calculated change in mass due herbivory did not match expected value."


@pytest.fixture
def excrement_instance():
    """Fixture for a soil pool used in tests."""
    from virtual_rainforest.models.animals.decay import ExcrementPool

    return ExcrementPool(100000.0, 0.0)


def test_forage_cohort_herbivore(
    herbivore_cohort_instance, plant_list_instance, excrement_instance
):
    """Test resource selection and mass change for a herbivore cohort."""
    from unittest.mock import patch

    # Mocking the delta_mass_herbivory method
    with patch.object(
        herbivore_cohort_instance, "delta_mass_herbivory", return_value=5.0
    ) as mock_herbivory, patch.object(
        herbivore_cohort_instance, "excrete"
    ) as mock_excrete:
        delta_mass = herbivore_cohort_instance.forage_cohort(
            plant_list_instance, [], excrement_instance
        )

        mock_herbivory.assert_called_once_with(plant_list_instance)
        mock_excrete.assert_called_once_with(excrement_instance, 5.0)
        assert delta_mass == 5.0, "Expected delta mass not returned for herbivory."


def test_forage_cohort_carnivore(
    predator_cohort_instance, animal_list_instance, excrement_instance
):
    """Test resource selection and mass change for a carnivore cohort."""
    from unittest.mock import patch

    # Mocking the delta_mass_predation method
    with patch.object(
        predator_cohort_instance, "delta_mass_predation", return_value=10.0
    ) as mock_predation, patch.object(
        predator_cohort_instance, "excrete"
    ) as mock_excrete:
        delta_mass = predator_cohort_instance.forage_cohort(
            [], animal_list_instance, excrement_instance
        )

        mock_predation.assert_called_once_with(animal_list_instance)
        mock_excrete.assert_called_once_with(excrement_instance, 10.0)
        assert delta_mass == 10.0, "Expected delta mass not returned for predation."


def test_forage_cohort_no_food_available(herbivore_cohort_instance, excrement_instance):
    """Test behavior when no food is available."""

    delta_mass = herbivore_cohort_instance.forage_cohort([], [], excrement_instance)
    # Assuming delta_mass should be 0 or another specific value when no food available
    assert (
        delta_mass == 0
    ), "Expected delta mass not handled correctly when no food is available."
