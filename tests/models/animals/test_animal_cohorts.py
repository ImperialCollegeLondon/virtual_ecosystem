"""Test module for animal_cohorts.py."""

import pytest
from numpy import isclose, timedelta64


@pytest.fixture
def predator_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[2]


@pytest.fixture
def predator_cohort_instance(predator_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        predator_functional_group_instance, 10000.0, 1, 10, constants_instance
    )


@pytest.fixture
def ectotherm_functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[5]


@pytest.fixture
def ectotherm_cohort_instance(ectotherm_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        ectotherm_functional_group_instance, 100.0, 1, 10, constants_instance
    )


@pytest.fixture
def prey_cohort_instance(herbivore_functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        herbivore_functional_group_instance, 100.0, 1, 10, constants_instance
    )


@pytest.fixture
def carcass_pool_instance():
    """Fixture for an carcass pool used in tests."""
    from virtual_ecosystem.models.animal.decay import CarcassPool

    return CarcassPool(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


@pytest.mark.usefixtures("mocker")
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
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

        with pytest.raises(error_type):
            AnimalCohort(
                functional_group(herbivore_functional_group_instance),
                mass,
                age,
                individuals,
                constants_instance,
            )

    @pytest.mark.parametrize(
        "cohort_type, dt, initial_mass, temperature, expected_final_mass, error_type,"
        "metabolic_rate_return_value",
        [
            # Endotherm cases
            (
                "herbivore",
                timedelta64(1, "D"),
                1000.0,
                298.0,
                998.5205247106326,
                None,
                1.4794752893674,
            ),  # normal case
            (
                "herbivore",
                timedelta64(1, "D"),
                0.0,
                298.0,
                0.0,
                None,
                0.0,
            ),  # edge case: zero mass
            (
                "herbivore",
                timedelta64(3, "D"),
                1000.0,
                298.0,
                995.5615741318977,
                None,
                1.4794752893674,
            ),  # 3 days
            # Ectotherm cases
            (
                "ectotherm",
                timedelta64(1, "D"),
                100.0,
                20.0,
                99.95896219913648,
                None,
                0.04103780086352,
            ),  # normal case
            (
                "ectotherm",
                timedelta64(1, "D"),
                0.0,
                20.0,
                0.0,
                None,
                0.0,
            ),  # edge case: zero mass
            (
                "ectotherm",
                timedelta64(1, "D"),
                100.0,
                0.0,
                99.99436706014961,
                None,
                0.00563293985039,
            ),  # edge case: zero temperature
            # Invalid input cases
            (
                "herbivore",
                timedelta64(-1, "D"),
                100.0,
                298.0,
                None,
                ValueError,
                1.0,
            ),  # negative dt
            (
                "herbivore",
                timedelta64(1, "D"),
                -100.0,
                298.0,
                None,
                ValueError,
                1.0,
            ),  # negative mass
        ],
        ids=[
            "endotherm_normal",
            "endotherm_zero_mass",
            "endotherm_three_days",
            "ectotherm_normal",
            "ectotherm_zero_mass",
            "ectotherm_zero_temp",
            "invalid_negative_dt",
            "invalid_negative_mass",
        ],
    )
    def test_metabolize(
        self,
        mocker,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        cohort_type,
        dt,
        initial_mass,
        temperature,
        expected_final_mass,
        error_type,
        metabolic_rate_return_value,
    ):
        """Testing metabolize method for various scenarios."""

        # Select the appropriate cohort instance
        if cohort_type == "herbivore":
            cohort_instance = herbivore_cohort_instance
        elif cohort_type == "ectotherm":
            cohort_instance = ectotherm_cohort_instance
        else:
            raise ValueError("Invalid cohort type provided.")

        # Set initial mass
        cohort_instance.mass_current = initial_mass

        # Mocking the sf.metabolic_rate function to return a specific value
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.metabolic_rate",
            return_value=metabolic_rate_return_value,
        )

        if error_type:
            with pytest.raises(error_type):
                cohort_instance.metabolize(temperature, dt)
        else:
            cohort_instance.metabolize(temperature, dt)
            assert isclose(cohort_instance.mass_current, expected_final_mass, rtol=1e-9)

    @pytest.mark.parametrize(
        "cohort_type, excreta_mass, initial_pool_energy, expected_pool_energy",
        [
            ("herbivore", 100.0, 500.0, 500.0),  # normal case for herbivore
            ("herbivore", 0.0, 500.0, 500.0),  # zero excreta mass for herbivore
            ("ectotherm", 50.0, 300.0, 300.0),  # normal case for ectotherm
            ("ectotherm", 0.0, 300.0, 300.0),  # zero excreta mass for ectotherm
        ],
        ids=[
            "herbivore_normal",
            "herbivore_zero_excreta",
            "ectotherm_normal",
            "ectotherm_zero_excreta",
        ],
    )
    def test_excrete(
        self,
        mocker,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        cohort_type,
        excreta_mass,
        initial_pool_energy,
        expected_pool_energy,
    ):
        """Testing excrete method for various scenarios.

        This method is doing nothing of substance until the stoichiometry rework.

        """

        # Select the appropriate cohort instance
        if cohort_type == "herbivore":
            cohort_instance = herbivore_cohort_instance
        elif cohort_type == "ectotherm":
            cohort_instance = ectotherm_cohort_instance
        else:
            raise ValueError("Invalid cohort type provided.")

        # Mock the excrement pool
        excrement_pool = mocker.Mock()
        excrement_pool.decomposed_energy = initial_pool_energy

        # Call the excrete method
        cohort_instance.excrete(excreta_mass, excrement_pool)

        # Check the expected results
        assert excrement_pool.decomposed_energy == expected_pool_energy

    @pytest.mark.parametrize(
        "cohort_type, excreta_mass, expected_carbon_waste",
        [
            ("herbivore", 100.0, 100.0),  # normal case for herbivore
            ("herbivore", 0.0, 0.0),  # zero excreta mass for herbivore
            ("ectotherm", 50.0, 50.0),  # normal case for ectotherm
            ("ectotherm", 0.0, 0.0),  # zero excreta mass for ectotherm
        ],
        ids=[
            "herbivore_normal",
            "herbivore_zero_excreta",
            "ectotherm_normal",
            "ectotherm_zero_excreta",
        ],
    )
    def test_respire(
        self,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        cohort_type,
        excreta_mass,
        expected_carbon_waste,
    ):
        """Testing respire method for various scenarios.

        This test is deliberately simple because it will be reworked with stoichiometry.

        """

        # Select the appropriate cohort instance
        if cohort_type == "herbivore":
            cohort_instance = herbivore_cohort_instance
        elif cohort_type == "ectotherm":
            cohort_instance = ectotherm_cohort_instance
        else:
            raise ValueError("Invalid cohort type provided.")

        # Call the respire method
        carbon_waste = cohort_instance.respire(excreta_mass)

        # Check the expected results
        assert carbon_waste == expected_carbon_waste

    @pytest.mark.parametrize(
        "scav_initial, scav_final, decomp_initial, decomp_final, consumed_energy",
        [
            (1000.0, 1500.0, 0.0, 500.0, 1000.0),
            (0.0, 500.0, 1000.0, 1500.0, 1000.0),
            (1000.0, 1000.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 1000.0, 1000.0, 0.0),
        ],
    )
    def test_defecate(
        self,
        herbivore_cohort_instance,
        excrement_pool_instance,
        scav_initial,
        scav_final,
        decomp_initial,
        decomp_final,
        consumed_energy,
    ):
        """Testing defecate() for varying soil energy levels."""
        excrement_pool_instance.scavengeable_energy = scav_initial
        excrement_pool_instance.decomposed_energy = decomp_initial
        herbivore_cohort_instance.defecate(excrement_pool_instance, consumed_energy)
        assert excrement_pool_instance.scavengeable_energy == scav_final
        assert excrement_pool_instance.decomposed_energy == decomp_final

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
        carcass_pool_instance,
        initial_carcass,
        final_carcass,
        decomp_carcass,
    ):
        """Testing death."""
        herbivore_cohort_instance.individuals = initial_pop
        carcass_pool_instance.scavengeable_energy = initial_carcass
        herbivore_cohort_instance.die_individual(number_dead, carcass_pool_instance)
        assert herbivore_cohort_instance.individuals == final_pop
        assert carcass_pool_instance.scavengeable_energy == final_carcass
        assert carcass_pool_instance.decomposed_energy == decomp_carcass

    def test_get_eaten(
        self, prey_cohort_instance, predator_cohort_instance, carcass_pool_instance
    ):
        """Test the get_eaten method for accuracy in updating prey and carcass pool."""
        potential_consumed_mass = 100  # Set a potential consumed mass for testing
        initial_individuals = prey_cohort_instance.individuals
        initial_mass_current = prey_cohort_instance.mass_current
        initial_carcass_scavengeable_energy = carcass_pool_instance.scavengeable_energy
        initial_carcass_decomposed_energy = carcass_pool_instance.decomposed_energy

        # Execute the get_eaten method with test parameters
        actual_consumed_mass = prey_cohort_instance.get_eaten(
            potential_consumed_mass, predator_cohort_instance, carcass_pool_instance
        )

        # Assertions to check if individuals were correctly removed and carcass pool
        # updated
        assert (
            prey_cohort_instance.individuals < initial_individuals
        ), "Prey cohort should have fewer individuals."
        assert (
            prey_cohort_instance.mass_current == initial_mass_current
        ), "Prey cohort should have the same total mass."
        assert (
            actual_consumed_mass <= potential_consumed_mass
        ), "Actual consumed mass should be less than/equal to potential consumed mass."
        assert (
            carcass_pool_instance.scavengeable_energy
            > initial_carcass_scavengeable_energy
        ), "Carcass pool's scavengeable energy should increase."
        assert (
            carcass_pool_instance.decomposed_energy > initial_carcass_decomposed_energy
        ), "Carcass pool's decomposed energy should increase."

    @pytest.mark.parametrize(
        "below_threshold,expected_mass_current_increase,"
        "expected_reproductive_mass_increase",
        [
            (
                0.5,
                100,
                0,
            ),  # Scenario where the current total mass is below the threshold
            (
                1.5,
                0,
                100,
            ),  # Scenario where the current total mass is above the threshold
        ],
    )
    def test_eat(
        self,
        herbivore_cohort_instance,
        below_threshold,
        expected_mass_current_increase,
        expected_reproductive_mass_increase,
    ):
        """Testing eat method adjusting for the mass threshold."""
        mass_consumed = 100  # Define a test mass consumed

        # Set up the instance to reflect the test scenario
        adult_mass = 200  # Assume an adult mass for calculation
        herbivore_cohort_instance.functional_group.adult_mass = adult_mass
        total_mass = adult_mass * below_threshold
        herbivore_cohort_instance.mass_current = (
            total_mass * 0.8
        )  # 80% towards current mass
        herbivore_cohort_instance.reproductive_mass = (
            total_mass * 0.2
        )  # 20% towards reproductive mass

        initial_mass_current = herbivore_cohort_instance.mass_current
        initial_reproductive_mass = herbivore_cohort_instance.reproductive_mass

        # Execute the eat method
        herbivore_cohort_instance.eat(mass_consumed)

        # Assertions
        assert (
            herbivore_cohort_instance.mass_current
            == initial_mass_current + expected_mass_current_increase
        ), "Current mass did not increase as expected."
        assert (
            herbivore_cohort_instance.reproductive_mass
            == initial_reproductive_mass + expected_reproductive_mass_increase
        ), "Reproductive mass did not increase as expected."

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
        "alpha_0_herb, mass_current, expected_alpha",
        [
            pytest.param(1.0e-11, 50, 5e-10, id="base rate and mass"),
            pytest.param(2.0e-11, 100, 2e-9, id="increased rate and mass"),
            pytest.param(5.0e-12, 25, 1.25e-10, id="decreased rate and mass"),
            pytest.param(2.0e-11, 25, 5e-10, id="high rate, low mass"),
            pytest.param(5.0e-12, 100, 5e-10, id="low rate, high mass"),
        ],
    )
    def test_calculate_alpha(
        self,
        mocker,
        alpha_0_herb,
        mass_current,
        expected_alpha,
        herbivore_functional_group_instance,
    ):
        """Testing for calculate alpha."""
        # Assuming necessary imports and setup based on previous examples
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.constants import AnimalConsts

        # Mock the scaling function to control its return value
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.alpha_i_k",
            return_value=expected_alpha,
        )

        # Setup constants and functional group mock
        constants = AnimalConsts()
        functional_group_mock = herbivore_functional_group_instance

        # Initialize the AnimalCohort instance with test parameters
        cohort_instance = AnimalCohort(
            functional_group=functional_group_mock,
            mass=mass_current,
            age=1.0,  # Example age
            individuals=1,  # Example number of individuals
            constants=constants,
        )

        # Execute the method under test
        result = cohort_instance.calculate_alpha()

        # Assert that the result matches the expected outcome for the given scenario
        assert (
            result == expected_alpha
        ), f"Failed scenario: alpha_0_herb={alpha_0_herb}, mass_current={mass_current}"

    @pytest.mark.parametrize(
        "alpha, mass_current, phi_herb_t, expected_biomass",
        [
            pytest.param(1.0e-11, 100, 0.1, 1, id="low_alpha_high_mass"),
            pytest.param(2.0e-11, 100, 0.2, 2, id="high_alpha_high_mass"),
            pytest.param(1.0e-11, 0.1, 0.1, 3, id="low_alpha_low_mass"),
            pytest.param(2.0e-11, 0.1, 0.2, 4, id="high_alpha_low_mass"),
        ],
    )
    def test_calculate_potential_consumed_biomass(
        self, mocker, alpha, mass_current, phi_herb_t, expected_biomass
    ):
        """Testing for calculate_potential_consumed_biomass."""
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import DietType
        from virtual_ecosystem.models.animal.protocols import Resource

        # Mock the target plant
        target_plant = mocker.MagicMock(spec=Resource, mass_current=mass_current)

        # Mock k_i_k to return the expected_biomass
        k_i_k_mock = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.k_i_k",
            return_value=expected_biomass,
        )

        # Setup functional group mock to provide phi_herb_t
        functional_group_mock = mocker.MagicMock()
        functional_group_mock.diet = DietType("herbivore")
        functional_group_mock.constants.phi_herb_t = phi_herb_t

        # Initialize the AnimalCohort instance with mocked functional group
        cohort_instance = AnimalCohort(
            functional_group=functional_group_mock,
            mass=100.0,  # Arbitrary value since mass is not directly used in this test
            age=1.0,  # Arbitrary value
            individuals=1,  # Arbitrary value
            constants=mocker.MagicMock(),
        )

        # Execute the method under test
        result = cohort_instance.calculate_potential_consumed_biomass(
            target_plant, alpha
        )

        # Verify that the result matches the expected outcome for the given scenario
        assert result == expected_biomass, (
            f"Failed scenario: alpha={alpha}, mass_current={mass_current}, "
            f"phi_herb_t={phi_herb_t}"
        )

        # verify that k_i_k was called with the correct parameters
        A_cell = 1.0
        k_i_k_mock.assert_called_once_with(alpha, phi_herb_t, mass_current, A_cell)

    def calculate_total_handling_time_for_herbivory(
        self, mocker, herbivore_cohort_instance, plant_list_instance
    ):
        """Test aggregation of handling times across all available plant resources."""

        alpha = 0.1  # Assume this is the calculated search efficiency
        with (
            mocker.patch(
                "virtual_ecosystem.models.animal.scaling_functions.k_i_k",
                return_value=20.0,
            ),
            mocker.patch(
                "virtual_ecosystem.models.animal.scaling_functions.H_i_k",
                return_value=0.2,
            ),
        ):
            total_handling_time = (
                herbivore_cohort_instance.calculate_total_handling_time_for_herbivory(
                    plant_list_instance, alpha
                )
            )
            # Assert based on expected behavior; this will need to be adjusted based on
            # number of plants and their handling times
            expected_handling_time = sum(
                [20.2 for _ in plant_list_instance]
            )  # Simplified; adjust calculation as needed
            assert total_handling_time == pytest.approx(
                expected_handling_time, rel=1e-6
            )

    @pytest.mark.parametrize(
        "alpha, potential_biomass, total_handling_time, plant_biomass, "
        "cohort_size, expected_rate, scenario_id",
        [
            pytest.param(
                0.1,
                20.0,
                40.4,
                100,
                10,
                "expected_rate_calculation_1",
                "low_alpha_high_mass",
            ),
            pytest.param(
                0.2,
                30.0,
                20.2,
                200,
                5,
                "expected_rate_calculation_2",
                "high_alpha_high_mass",
            ),
        ],
    )
    def test_F_i_k(
        self,
        mocker,
        alpha,
        potential_biomass,
        total_handling_time,
        plant_biomass,
        cohort_size,
        expected_rate,
        scenario_id,
        herbivore_cohort_instance,
    ):
        """Test for F_i_k."""
        from virtual_ecosystem.models.animal.protocols import Resource

        # Mock the target plant with specified biomass
        target_plant = mocker.MagicMock(spec=Resource, mass_current=plant_biomass)
        plant_list = [target_plant]  # Simplified plant list for testing

        # Mock internal method calls
        mocker.patch.object(
            herbivore_cohort_instance, "calculate_alpha", return_value=alpha
        )
        mocker.patch.object(
            herbivore_cohort_instance,
            "calculate_potential_consumed_biomass",
            return_value=potential_biomass,
        )
        mocker.patch.object(
            herbivore_cohort_instance,
            "calculate_total_handling_time_for_herbivory",
            return_value=total_handling_time,
        )

        # Execute the method under test
        rate = herbivore_cohort_instance.F_i_k(plant_list, target_plant)

        N = herbivore_cohort_instance.individuals
        k = potential_biomass
        B_k = plant_biomass
        total_handling_t = total_handling_time

        calculated_expected_rate = N * (k / (1 + total_handling_t)) * (1 / B_k)

        # Assert that the rate matches the expected output
        assert rate == pytest.approx(calculated_expected_rate, rel=1e-6), (
            f"The calculated rate does not match"
            f"the expected rate for scenario {scenario_id}"
        )

    def test_calculate_theta_opt_i(self, mocker, herbivore_cohort_instance):
        """Test calculate_theta_opt_i."""
        theta_opt_i_mock = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.theta_opt_i",
            return_value=0.5,  # Mocked return value to simulate `theta_opt_i` behavior
        )
        result = herbivore_cohort_instance.calculate_theta_opt_i()

        # Assert the result matches the mocked return value
        assert (
            result == 0.5
        ), "The result does not match the expected return value from sf.theta_opt_i"

        # Assert sf.theta_opt_i was called with the correct parameters
        theta_opt_i_mock.assert_called_once_with(
            herbivore_cohort_instance.constants.theta_opt_min_f,
            herbivore_cohort_instance.constants.theta_opt_f,
            herbivore_cohort_instance.constants.sigma_opt_f,
        )

    def test_calculate_predation_success_probability(
        self, mocker, herbivore_cohort_instance
    ):
        """Test successful predation probability calculation."""

        target_mass = 50.0  # Example target mass

        mock_theta_opt_i = mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.AnimalCohort"
            ".calculate_theta_opt_i",
            return_value=0.7,
        )

        mock_w_bar = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.w_bar_i_j",
            return_value=0.6,
        )

        result = herbivore_cohort_instance.calculate_predation_success_probability(
            target_mass
        )

        # Ensure calculate_theta_opt_i is called within the method
        mock_theta_opt_i.assert_called_once()

        # Verify that w_bar_i_j was called with the correct parameters
        mock_w_bar.assert_called_once_with(
            herbivore_cohort_instance.mass_current,
            target_mass,
            0.7,  # Expected theta_opt_i from mocked
            herbivore_cohort_instance.constants.sigma_opt_pred_prey,
        )

        # Asserting the result matches the mocked return value
        assert result == 0.6, "Expected predation success probability not returned."

    def test_calculate_predation_search_rate(self, mocker, herbivore_cohort_instance):
        """Test predation search rate calculation."""

        success_probability = 0.5  # Example success probability

        mock_alpha_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.alpha_i_j",
            return_value=0.8,
        )

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

    def test_calculate_potential_prey_consumed(self, mocker, herbivore_cohort_instance):
        """Test calculation of potential number of prey consumed."""

        alpha = 0.8  # Example search rate
        theta_i_j = 0.7  # Example predation parameter

        mock_k_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.k_i_j",
            return_value=15.0,
        )

        result = herbivore_cohort_instance.calculate_potential_prey_consumed(
            alpha, theta_i_j
        )

        # Verify that k_i_j was called with the correct parameters
        mock_k_i_j.assert_called_once_with(
            alpha,
            herbivore_cohort_instance.individuals,
            1.0,
            theta_i_j,
        )

        # Asserting the result matches the mocked return value
        assert result == 15.0, "Expected potential prey consumed not returned."

    def test_calculate_total_handling_time_for_predation(
        self, mocker, herbivore_cohort_instance
    ):
        """Test total handling time calculation for predation."""

        mock_H_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.H_i_j", return_value=2.5
        )

        result = herbivore_cohort_instance.calculate_total_handling_time_for_predation()

        # Verify that H_i_j was called with the correct parameters
        mock_H_i_j.assert_called_once_with(
            herbivore_cohort_instance.constants.h_pred_0,
            herbivore_cohort_instance.constants.M_pred_ref,
            herbivore_cohort_instance.mass_current,
            herbivore_cohort_instance.constants.b_pred,
        )

        # Asserting the result matches the mocked return value
        assert result == 2.5, "Expected total handling time for predation not returned."

    def test_F_i_j_individual(
        self, mocker, predator_cohort_instance, animal_list_instance
    ):
        """Test instantaneous predation rate calculation on a selected target cohort."""

        target_animal = animal_list_instance[0]

        # Mock methods using the mocker fixture
        mock_success_prob = mocker.patch(
            (
                "virtual_ecosystem.models.animal.animal_cohorts."
                "AnimalCohort.calculate_predation_success_probability"
            ),
            return_value=0.5,
        )
        mock_search_rate = mocker.patch(
            (
                "virtual_ecosystem.models.animal.animal_cohorts."
                "AnimalCohort.calculate_predation_search_rate"
            ),
            return_value=0.8,
        )
        mock_theta_i_j = mocker.patch(
            (
                "virtual_ecosystem.models.animal.animal_cohorts."
                "AnimalCohort.theta_i_j"
            ),
            return_value=0.7,
        )
        mock_potential_prey = mocker.patch(
            (
                "virtual_ecosystem.models.animal.animal_cohorts."
                "AnimalCohort.calculate_potential_prey_consumed"
            ),
            return_value=10,
        )
        mock_total_handling = mocker.patch(
            (
                "virtual_ecosystem.models.animal.animal_cohorts."
                "AnimalCohort.calculate_total_handling_time_for_predation"
            ),
            return_value=2,
        )

        # Execute the method under test
        rate = predator_cohort_instance.F_i_j_individual(
            animal_list_instance, target_animal
        )

        # Verify each mocked method was called with expected arguments
        mock_success_prob.assert_called_once_with(target_animal.mass_current)
        mock_search_rate.assert_called_once_with(0.5)
        mock_theta_i_j.assert_called_once_with(animal_list_instance)
        mock_potential_prey.assert_called_once_with(0.8, 0.7)
        mock_total_handling.assert_called_once()

        # Calculate the expected rate based on the mocked return values and assert
        N_i = predator_cohort_instance.individuals
        N_target = target_animal.individuals
        expected_rate = N_i * (10 / (1 + 2)) * (1 / N_target)
        assert rate == pytest.approx(
            expected_rate
        ), "F_i_j_individual did not return the expected predation rate."

    def test_theta_i_j(self, predator_cohort_instance, animal_list_instance):
        """Test theta_i_j."""
        # TODO change this A_cell to call it from its real plant in the data
        A_cell = 1.0  # Define A_cell value used in method implementation

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

    @pytest.mark.parametrize(
        "consumed_mass, expected_total_consumed_mass",
        [
            (100.0, 300.0),  # Assuming three cohorts each consuming 100.0 units
        ],
    )
    def test_delta_mass_predation(
        self,
        mocker,
        predator_cohort_instance,
        animal_list_instance,
        excrement_pool_instance,
        carcass_pool_instance,
        consumed_mass,
        expected_total_consumed_mass,
    ):
        """Test the delta_mass_predation.

        The expected total consumed mass is 300 because there are three cohorts in the
        animal cohort instance.
        """

        # Mock calculate_consumed_mass_predation to return a specific consumed mass
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_consumed_mass_predation",
            return_value=consumed_mass,
        )

        # Mock AnimalCohort.get_eaten to simulate consumption behavior
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.AnimalCohort.get_eaten",
            return_value=consumed_mass,
        )

        # Mock predator_cohort_instance.defecate to verify its call
        mock_defecate = mocker.patch.object(predator_cohort_instance, "defecate")

        total_consumed_mass = predator_cohort_instance.delta_mass_predation(
            animal_list_instance, excrement_pool_instance, carcass_pool_instance
        )

        # Check if the total consumed mass matches the expected value
        assert (
            total_consumed_mass == expected_total_consumed_mass
        ), "Total consumed mass should match expected value."

        # Ensure defecate was called with the correct total consumed mass
        mock_defecate.assert_called_once_with(
            excrement_pool_instance, total_consumed_mass
        )

    def test_delta_mass_herbivory(
        self,
        mocker,
        herbivore_cohort_instance,
        plant_list_instance,
        excrement_pool_instance,
    ):
        """Test mass assimilation calculation from herbivory."""

        # Mock the calculate_consumed_mass_herbivory method
        mock_calculate_consumed_mass_herbivory = mocker.patch.object(
            herbivore_cohort_instance,
            "calculate_consumed_mass_herbivory",
            side_effect=lambda plant_list, plant: 10.0,
            # Assume 10.0 kg mass consumed from each plant for simplicity
        )

        # Mock the PlantResources.get_eaten method
        mock_get_eaten = mocker.patch(
            "virtual_ecosystem.models.animal.plant_resources.PlantResources.get_eaten",
            side_effect=lambda consumed_mass, herbivore, excrement_pool: consumed_mass,
        )

        delta_mass = herbivore_cohort_instance.delta_mass_herbivory(
            plant_list_instance, excrement_pool_instance
        )

        # Ensure calculate_consumed_mass_herbivory and get_eaten were called correctly
        assert mock_calculate_consumed_mass_herbivory.call_count == len(
            plant_list_instance
        )
        assert mock_get_eaten.call_count == len(plant_list_instance)

        # Calculate the expected total consumed mass based on the number of plants
        expected_delta_mass = 10.0 * len(plant_list_instance)

        # Assert the calculated delta_mass_herb matches the expected value
        assert delta_mass == pytest.approx(
            expected_delta_mass
        ), "Calculated change in mass due to herbivory did not match expected value."

    def test_forage_cohort(
        self,
        mocker,
        herbivore_cohort_instance,
        predator_cohort_instance,
        plant_list_instance,
        animal_list_instance,
        excrement_pool_instance,
        carcass_pool_instance,
    ):
        """Test foraging behavior for different diet types."""

        # Mocking the delta_mass_herbivory and delta_mass_predation methods
        mock_delta_mass_herbivory = mocker.patch.object(
            herbivore_cohort_instance, "delta_mass_herbivory", return_value=100
        )
        mock_delta_mass_predation = mocker.patch.object(
            predator_cohort_instance, "delta_mass_predation", return_value=200
        )
        mock_eat_herbivore = mocker.patch.object(herbivore_cohort_instance, "eat")
        mock_eat_predator = mocker.patch.object(predator_cohort_instance, "eat")

        # Test herbivore diet
        herbivore_cohort_instance.forage_cohort(
            plant_list_instance, [], excrement_pool_instance, carcass_pool_instance
        )
        mock_delta_mass_herbivory.assert_called_once_with(
            plant_list_instance, excrement_pool_instance
        )
        mock_eat_herbivore.assert_called_once_with(100)

        # Test carnivore diet
        predator_cohort_instance.forage_cohort(
            [], animal_list_instance, excrement_pool_instance, carcass_pool_instance
        )
        mock_delta_mass_predation.assert_called_once_with(
            animal_list_instance, excrement_pool_instance, carcass_pool_instance
        )
        mock_eat_predator.assert_called_once_with(200)

    @pytest.mark.parametrize(
        "mass_current, V_disp, M_disp_ref, o_disp, expected_probability",
        [
            pytest.param(10, 0.5, 10, 0.5, 0.5, id="normal_case"),
            pytest.param(10, 1.5, 10, 0.5, 1.0, id="cap_at_1"),
            pytest.param(10, 0, 10, 0.5, 0, id="zero_velocity"),
            pytest.param(0, 0.5, 10, 0.5, 0, id="zero_mass"),
        ],
    )
    def test_migrate_juvenile_probability(
        self,
        mocker,
        mass_current,
        V_disp,
        M_disp_ref,
        o_disp,
        expected_probability,
        herbivore_cohort_instance,
    ):
        """Test the calculation of juvenile migration probability."""
        from math import sqrt

        # Assign test-specific values to the cohort instance
        cohort = herbivore_cohort_instance
        cohort.mass_current = mass_current
        cohort.constants = mocker.MagicMock(
            V_disp=V_disp, M_disp_ref=M_disp_ref, o_disp=o_disp
        )

        # Mock juvenile_dispersal_speed
        mocked_velocity = V_disp * (mass_current / M_disp_ref) ** o_disp
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions."
            "juvenile_dispersal_speed",
            return_value=mocked_velocity,
        )

        # Calculate expected probability
        A_cell = 1.0
        grid_side = sqrt(A_cell)
        calculated_probability = mocked_velocity / grid_side
        expected_probability = min(calculated_probability, 1.0)  # Cap at 1.0

        # Call the method under test
        probability_of_dispersal = cohort.migrate_juvenile_probability()

        # Assertion to check if the method returns the correct probability
        assert (
            probability_of_dispersal == expected_probability
        ), "The probability calculated did not match the expected probability."

    @pytest.mark.parametrize(
        "is_mature, u_bg, lambda_se, t_to_maturity, t_since_maturity, lambda_max, J_st,"
        "zeta_st, mass_current, mass_max, dt, expected_dead",
        [
            pytest.param(
                True,
                0.001,
                0.003,
                365,
                30,
                1.0,
                0.6,
                0.05,
                600,
                600,
                30,
                13,
                id="mature_with_all_mortalities",
            ),
            pytest.param(
                False,
                0.001,
                0.003,
                365,
                30,
                1.0,
                0.6,
                0.05,
                600,
                600,
                30,
                4,
                id="immature_without_senescence",
            ),
        ],
    )
    def test_inflict_non_predation_mortality(
        self,
        mocker,
        is_mature,
        u_bg,
        lambda_se,
        t_to_maturity,
        t_since_maturity,
        lambda_max,
        J_st,
        zeta_st,
        mass_current,
        mass_max,
        dt,
        expected_dead,
        predator_cohort_instance,
        carcass_pool_instance,
    ):
        """Test the calculation of total non-predation mortality in a cohort."""
        from math import ceil, exp

        import virtual_ecosystem.models.animal.scaling_functions as sf

        # Use the predator cohort instance and set initial individuals to 100
        cohort = predator_cohort_instance
        cohort.individuals = 100  # Set initial individuals count
        cohort.is_mature = is_mature
        cohort.mass_current = mass_current
        cohort.time_to_maturity = t_to_maturity
        cohort.time_since_maturity = t_since_maturity
        cohort.functional_group.adult_mass = mass_max

        # Mocking the mortality functions to return predefined values
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.background_mortality",
            return_value=u_bg,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.senescence_mortality",
            return_value=(
                lambda_se * exp(t_since_maturity / t_to_maturity) if is_mature else 0.0
            ),
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.starvation_mortality",
            return_value=(
                lambda_max
                / (1 + exp((mass_current - J_st * mass_max) / (zeta_st * mass_max)))
            ),
        )

        # Diagnostics
        print(f"Initial individuals: {cohort.individuals}")

        # Run the method
        cohort.inflict_non_predation_mortality(dt, carcass_pool_instance)

        # Calculate expected number of deaths inside the test
        u_bg_value = sf.background_mortality(u_bg)
        u_se_value = (
            sf.senescence_mortality(lambda_se, t_to_maturity, t_since_maturity)
            if is_mature
            else 0.0
        )
        u_st_value = sf.starvation_mortality(
            lambda_max, J_st, zeta_st, mass_current, mass_max
        )
        u_t = u_bg_value + u_se_value + u_st_value

        number_dead = ceil(100 * (1 - exp(-u_t * dt)))

        # Diagnostics
        print(
            f"background: {u_bg_value},"
            f"senescence: {u_se_value},"
            f"starvation: {u_st_value}"
        )
        print(f"Calculated total mortality rate: {u_t}")
        print(
            f"Calculated number dead: {number_dead},"
            f"Expected number dead: {expected_dead}"
        )
        print(
            f"Remaining individuals: {cohort.individuals},"
            f"Expected remaining: {100 - expected_dead}"
        )

        # Verify
        assert (
            cohort.individuals == 100 - expected_dead
        ), "The calculated number of dead individuals doesn't match the expected value."
