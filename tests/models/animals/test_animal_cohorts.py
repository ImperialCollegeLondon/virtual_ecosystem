"""Test module for animal_cohorts.py."""

import uuid

import pytest
from numpy import isclose, timedelta64


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
def ectotherm_cohort_instance(
    ectotherm_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        ectotherm_functional_group_instance,
        100.0,
        1,
        10,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


@pytest.fixture
def prey_cohort_instance(
    herbivore_functional_group_instance,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        herbivore_functional_group_instance,
        100.0,
        1,
        10,
        1,  # centroid
        animal_data_for_cohorts_instance.grid,  # grid
        constants_instance,
    )


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
        animal_data_for_cohorts_instance,
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
                1,  # centroid
                animal_data_for_cohorts_instance.grid,  # grid
                constants_instance,
            )

    def test_mass_current(self, herbivore_cohort_instance):
        """Test the mass_current property."""

        expected_mass = sum(
            herbivore_cohort_instance.mass_current * proportion
            for proportion in (
                herbivore_cohort_instance.functional_group.cnp_proportions.values()
            )
        )

        assert herbivore_cohort_instance.mass_current == pytest.approx(
            expected_mass, rel=1e-6
        )

    @pytest.mark.parametrize(
        "cohort_type, dt, initial_mass, temperature, expected_final_mass, error_type,"
        "metabolic_rate_return_value",
        [
            (
                "herbivore",
                timedelta64(1, "D"),
                1000.0,
                298.0,
                998.5205247106326,
                None,
                1.4794752893674,
            ),
            ("herbivore", timedelta64(1, "D"), 0.0, 298.0, 0.0, None, 0.0),
            (
                "herbivore",
                timedelta64(3, "D"),
                1000.0,
                298.0,
                995.5615741318977,
                None,
                1.4794752893674,
            ),
            (
                "ectotherm",
                timedelta64(1, "D"),
                100.0,
                20.0,
                99.95896219913648,
                None,
                0.04103780086352,
            ),
            ("ectotherm", timedelta64(1, "D"), 0.0, 20.0, 0.0, None, 0.0),
            (
                "ectotherm",
                timedelta64(1, "D"),
                100.0,
                0.0,
                99.99436706014961,
                None,
                0.00563293985039,
            ),
            ("herbivore", timedelta64(-1, "D"), 100.0, 298.0, None, ValueError, 1.0),
            ("herbivore", timedelta64(1, "D"), -100.0, 298.0, None, ValueError, 1.0),
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
        from virtual_ecosystem.models.animal.cnp import CNP

        # Select the appropriate cohort instance
        cohort_instance = (
            herbivore_cohort_instance
            if cohort_type == "herbivore"
            else ectotherm_cohort_instance
        )

        # Set initial mass using CNP object
        cohort_instance.mass_cnp = CNP(initial_mass, 0.0, 0.0)

        # Mock metabolic_rate to return a specific value
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.metabolic_rate",
            return_value=metabolic_rate_return_value,
        )

        if error_type:
            with pytest.raises(error_type):
                cohort_instance.metabolize(temperature, dt)
        else:
            cohort_instance.metabolize(temperature, dt)
            assert isclose(cohort_instance.mass_cnp.C, expected_final_mass, rtol=1e-9)

    @pytest.mark.parametrize(
        "cohort_type, excreta_mass, num_pools",
        [
            ("herbivore", {"C": 100.0, "N": 10.0, "P": 1.0}, 1),
            ("herbivore", {"C": 0.0, "N": 0.0, "P": 0.0}, 1),
            ("ectotherm", {"C": 50.0, "N": 5.0, "P": 0.5}, 1),
            ("ectotherm", {"C": 0.0, "N": 0.0, "P": 0.0}, 1),
            ("herbivore", {"C": 100.0, "N": 10.0, "P": 1.0}, 3),
            ("herbivore", {"C": 0.0, "N": 0.0, "P": 0.0}, 3),
            ("ectotherm", {"C": 50.0, "N": 5.0, "P": 0.5}, 3),
            ("ectotherm", {"C": 0.0, "N": 0.0, "P": 0.0}, 3),
        ],
    )
    def test_excrete(
        self,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        cohort_type,
        excreta_mass,
        num_pools,
        excrement_pools_by_cell_instance,
    ):
        """Testing excrete method for various scenarios using the fixture."""
        # Select the appropriate cohort instance
        cohort_instance = (
            herbivore_cohort_instance
            if cohort_type == "herbivore"
            else ectotherm_cohort_instance
        )

        # Retrieve the excrement pools from the fixture
        excrement_pools = excrement_pools_by_cell_instance[1][:num_pools]

        # Store initial values before excretion
        initial_scavengeable_cnp = {
            nutrient: sum(
                getattr(pool.scavengeable_cnp, nutrient) for pool in excrement_pools
            )
            for nutrient in excreta_mass
        }
        initial_decomposed_cnp = {
            nutrient: sum(
                getattr(pool.decomposed_cnp, nutrient) for pool in excrement_pools
            )
            for nutrient in excreta_mass
        }

        # Call the excrete method
        cohort_instance.excrete(excreta_mass, excrement_pools)

        # Expected results calculation
        excreta_mass_per_community = {
            nutrient: excreta_mass[nutrient] / num_pools for nutrient in excreta_mass
        }
        decay_fraction = cohort_instance.decay_fraction_excrement

        expected_decomposed_cnp = {
            nutrient: initial_decomposed_cnp[nutrient]
            + decay_fraction * excreta_mass_per_community[nutrient] * num_pools
            for nutrient in excreta_mass
        }
        expected_scavengeable_cnp = {
            nutrient: initial_scavengeable_cnp[nutrient]
            + (1 - decay_fraction) * excreta_mass_per_community[nutrient] * num_pools
            for nutrient in excreta_mass
        }

        for excrement_pool in excrement_pools:
            for nutrient in excreta_mass:
                assert getattr(
                    excrement_pool.decomposed_cnp, nutrient
                ) == pytest.approx(expected_decomposed_cnp[nutrient], rel=1e-3)
                assert getattr(
                    excrement_pool.scavengeable_cnp, nutrient
                ) == pytest.approx(expected_scavengeable_cnp[nutrient], rel=1e-3)

    @pytest.mark.parametrize(
        "cohort_type, excreta_mass",
        [
            ("herbivore", {"C": 100.0, "N": 0.0, "P": 0.0}),
            (
                "herbivore",
                {"C": 0.0, "N": 0.0, "P": 0.0},
            ),  # Zero excreta
            ("ectotherm", {"C": 50.0, "N": 0.0, "P": 0.0}),
            (
                "ectotherm",
                {"C": 0.0, "N": 0.0, "P": 0.0},
            ),  # Zero excreta
        ],
    )
    def test_respire(
        self,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        cohort_type,
        excreta_mass,
    ):
        """Testing respire method for various scenarios."""

        # Select the appropriate cohort instance
        cohort_instance = (
            herbivore_cohort_instance
            if cohort_type == "herbivore"
            else ectotherm_cohort_instance
        )

        # Calculate the expected carbon waste based on the cohort's constants
        expected_carbon_waste = (
            excreta_mass["C"] * cohort_instance.constants.carbon_excreta_proportion
        )

        # Call the respire method
        carbon_waste = cohort_instance.respire(excreta_mass)

        # Check the expected results
        assert carbon_waste == expected_carbon_waste

    @pytest.mark.parametrize(
        "cohort_type, mass_consumed, num_pools",
        [
            ("herbivore", {"C": 100.0, "N": 10.0, "P": 1.0}, 1),
            ("herbivore", {"C": 0.0, "N": 0.0, "P": 0.0}, 1),
            ("ectotherm", {"C": 50.0, "N": 5.0, "P": 0.5}, 1),
            ("ectotherm", {"C": 0.0, "N": 0.0, "P": 0.0}, 1),
            ("herbivore", {"C": 100.0, "N": 10.0, "P": 1.0}, 3),
            ("herbivore", {"C": 0.0, "N": 0.0, "P": 0.0}, 3),
            ("ectotherm", {"C": 50.0, "N": 5.0, "P": 0.5}, 3),
            ("ectotherm", {"C": 0.0, "N": 0.0, "P": 0.0}, 3),
        ],
    )
    def test_defecate(
        self,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        cohort_type,
        mass_consumed,
        num_pools,
        excrement_pools_by_cell_instance,
    ):
        """Testing defecate method for various scenarios using the fixture."""

        # Select the appropriate cohort instance
        cohort_instance = (
            herbivore_cohort_instance
            if cohort_type == "herbivore"
            else ectotherm_cohort_instance
        )

        # Retrieve the excrement pools from the fixture
        excrement_pools = excrement_pools_by_cell_instance[1][:num_pools]

        # Store initial values before defecation
        initial_scavengeable_cnp = {
            nutrient: sum(pool.scavengeable_cnp[nutrient] for pool in excrement_pools)
            for nutrient in mass_consumed
        }
        initial_decomposed_cnp = {
            nutrient: sum(pool.decomposed_cnp[nutrient] for pool in excrement_pools)
            for nutrient in mass_consumed
        }

        # Call the defecate method
        cohort_instance.defecate(excrement_pools, mass_consumed)

        # Expected results calculation
        total_waste_mass = {
            nutrient: mass
            * cohort_instance.functional_group.conversion_efficiency
            * cohort_instance.individuals
            for nutrient, mass in mass_consumed.items()
        }

        waste_mass_per_community = {
            nutrient: total_waste_mass[nutrient] / num_pools
            for nutrient in total_waste_mass
        }
        decay_fraction = cohort_instance.decay_fraction_excrement

        # Calculate expected decomposed and scavengeable fractions
        expected_decomposed_cnp = {
            nutrient: initial_decomposed_cnp[nutrient]
            + decay_fraction * waste_mass_per_community[nutrient] * num_pools
            for nutrient in mass_consumed
        }
        expected_scavengeable_cnp = {
            nutrient: initial_scavengeable_cnp[nutrient]
            + (1 - decay_fraction) * waste_mass_per_community[nutrient] * num_pools
            for nutrient in mass_consumed
        }

        for excrement_pool in excrement_pools:
            for nutrient in mass_consumed:
                assert excrement_pool.decomposed_cnp[nutrient] == pytest.approx(
                    expected_decomposed_cnp[nutrient], rel=1e-3
                )
                assert excrement_pool.scavengeable_cnp[nutrient] == pytest.approx(
                    expected_scavengeable_cnp[nutrient], rel=1e-3
                )

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
        "initial_individuals, number_of_deaths, expected_final_individuals",
        [
            (0, 0, 0),  # zero_death_empty_pop
            (1000, 0, 1000),  # zero_death_non_empty_pop
            (1, 1, 0),  # single_death_single_pool
            (200, 100, 100),  # multiple_deaths_single_pool
            (1, 1, 0),  # single_death_multiple_pools
            (200, 100, 100),  # multiple_deaths_multiple_pools
        ],
        ids=[
            "zero_death_empty_pop",
            "zero_death_non_empty_pop",
            "single_death_single_pool",
            "multiple_deaths_single_pool",
            "single_death_multiple_pools",
            "multiple_deaths_multiple_pools",
        ],
    )
    def test_die_individual(
        self,
        herbivore_cohort_instance,
        initial_individuals,
        number_of_deaths,
        expected_final_individuals,
        mocker,
    ):
        """Test `die_individual` for zero and positive deaths.

        Ensures that:
        * Zero deaths leave the cohort unchanged and do not touch carcass pools.
        * Positive deaths reduce individuals and transfer the correct mass to carcasses.
        """

        # Set the initial number of individuals
        herbivore_cohort_instance.individuals = initial_individuals

        # Mock update_carcass_pool to prevent it from running real logic
        mock_update_carcass_pool = mocker.patch.object(
            herbivore_cohort_instance, "update_carcass_pool"
        )

        # Call the method under test
        herbivore_cohort_instance.die_individual(number_of_deaths, [])

        # Check the number of individuals after death
        assert herbivore_cohort_instance.individuals == expected_final_individuals

        if number_of_deaths == 0:
            # No deaths -> no carcass mass transfer
            mock_update_carcass_pool.assert_not_called()
        else:
            # Positive deaths -> carcass pool should receive total mass lost
            expected_mass_lost = {
                "C": herbivore_cohort_instance.mass_cnp.C * number_of_deaths,
                "N": herbivore_cohort_instance.mass_cnp.N * number_of_deaths,
                "P": herbivore_cohort_instance.mass_cnp.P * number_of_deaths,
            }

            mock_update_carcass_pool.assert_called_once_with(
                expected_mass_lost["C"],
                expected_mass_lost["N"],
                expected_mass_lost["P"],
                [],
            )

    @pytest.mark.parametrize(
        "carcass_mass, num_pools, decay_fraction, should_raise",
        [
            (
                {"C": 0.0, "N": 0.0, "P": 0.0},
                1,
                0.5,
                False,
            ),  # zero_mass
            (
                {"C": 1000.0, "N": 500.0, "P": 250.0},
                1,
                0.5,
                False,
            ),  # single_pool_distribution
            (
                {"C": 1000.0, "N": 500.0, "P": 250.0},
                2,
                0.5,
                False,
            ),  # multiple_pools_distribution
            (
                {"C": 1000.0, "N": 500.0, "P": 250.0},
                1,
                1.0,
                False,
            ),  # high_decay_fraction
            (
                {"C": 1000.0, "N": 500.0, "P": 250.0},
                1,
                0.0,
                False,
            ),  # low_decay_fraction
            (
                {"C": 1000.0, "N": 500.0, "P": 250.0},
                0,
                0.5,
                True,
            ),  # no_pools_provided
            (
                {"C": -100.0, "N": 500.0, "P": 250.0},
                1,
                0.5,
                True,
            ),  # negative_mass_values
        ],
        ids=[
            "zero_mass",
            "single_pool_distribution",
            "multiple_pools_distribution",
            "high_decay_fraction",
            "low_decay_fraction",
            "no_pools_provided",
            "negative_mass_values",
        ],
    )
    def test_update_carcass_pool(
        self,
        herbivore_cohort_instance,
        carcass_mass,
        num_pools,
        decay_fraction,
        should_raise,
    ):
        """Test carcass mass distribution in update_carcass_pool()."""
        from virtual_ecosystem.models.animal.cnp import CNP
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcass_pools = [
            CarcassPool(
                scavengeable_cnp=CNP(C=500.0, N=100.0, P=50.0),
                decomposed_cnp=CNP(C=0.0, N=0.0, P=0.0),
            )
            for _ in range(num_pools)
        ]

        # Store initial values from the pools
        initial_scavengeable_cnp = {
            nutrient: sum(pool.scavengeable_cnp[nutrient] for pool in carcass_pools)
            for nutrient in carcass_mass
        }
        initial_decomposed_cnp = {
            nutrient: sum(pool.decomposed_cnp[nutrient] for pool in carcass_pools)
            for nutrient in carcass_mass
        }

        # Set the decay fraction
        herbivore_cohort_instance.decay_fraction_carcasses = decay_fraction

        # If expected to raise an error, assert exception is raised
        if should_raise:
            with pytest.raises(ValueError):
                herbivore_cohort_instance.update_carcass_pool(
                    carcass_mass["C"],
                    carcass_mass["N"],
                    carcass_mass["P"],
                    carcass_pools,
                )
            return

        herbivore_cohort_instance.update_carcass_pool(
            carcass_mass["C"],
            carcass_mass["N"],
            carcass_mass["P"],
            carcass_pools,
        )

        # Adjust expected values to correctly distribute across pools
        expected_scavengeable_cnp = {
            nutrient: (initial_scavengeable_cnp[nutrient] / num_pools)
            + ((1 - decay_fraction) * (carcass_mass[nutrient] / num_pools))
            for nutrient in carcass_mass
        }
        expected_decomposed_cnp = {
            nutrient: (initial_decomposed_cnp[nutrient] / num_pools)
            + (decay_fraction * (carcass_mass[nutrient] / num_pools))
            for nutrient in carcass_mass
        }

        # Check updated values
        for carcass_pool in carcass_pools:
            for nutrient in carcass_mass:
                assert carcass_pool.scavengeable_cnp[nutrient] == pytest.approx(
                    expected_scavengeable_cnp[nutrient], rel=1e-3
                )
                assert carcass_pool.decomposed_cnp[nutrient] == pytest.approx(
                    expected_decomposed_cnp[nutrient], rel=1e-3
                )

    @pytest.mark.parametrize(
        "initial_individuals, individual_mass, potential_consumed_mass,"
        "expected_remaining_individuals",
        [
            (10, 10.0, 10.0, 9),  # One individual consumed
            (10, 10.0, 50.0, 5),  # Five individuals consumed
            (10, 10.0, 100.0, 0),  # All individuals consumed
            (
                10,
                10.0,
                200.0,
                0,
            ),  # Predator requests more than available, should consume all
        ],
    )
    def test_get_eaten(
        self,
        mocker,  # Inject pytest's mocker
        herbivore_cohort_instance,
        predator_cohort_instance,
        carcass_pools_by_cell_instance,
        initial_individuals,
        individual_mass,
        potential_consumed_mass,
        expected_remaining_individuals,
    ):
        """Test that get_eaten updates individuals and properly distributes mass."""

        from virtual_ecosystem.models.animal.cnp import CNP

        # Given a herbivore cohort with the specified number of individuals
        herbivore_cohort_instance.individuals = initial_individuals

        # Ensure mass_current correctly reflects individual mass
        herbivore_cohort_instance.mass_cnp = CNP(
            C=individual_mass * herbivore_cohort_instance.cnp_proportions["C"],
            N=individual_mass * herbivore_cohort_instance.cnp_proportions["N"],
            P=individual_mass * herbivore_cohort_instance.cnp_proportions["P"],
        )

        # Track initial total carcass pool mass for each nutrient
        initial_carcass_mass_c = sum(
            pool.scavengeable_cnp["C"]
            for pools in carcass_pools_by_cell_instance.values()
            for pool in pools
        )
        initial_carcass_mass_n = sum(
            pool.scavengeable_cnp["N"]
            for pools in carcass_pools_by_cell_instance.values()
            for pool in pools
        )
        initial_carcass_mass_p = sum(
            pool.scavengeable_cnp["P"]
            for pools in carcass_pools_by_cell_instance.values()
            for pool in pools
        )

        # Get predators mechanical efficiency
        mechanical_efficiency = (
            predator_cohort_instance.functional_group.mechanical_efficiency
        )

        # Get decay fraction for carcasses
        decay_fraction_carcasses = herbivore_cohort_instance.decay_fraction_carcasses

        # **Get C, N, P proportions for the prey species (mammal)**
        c_proportion = herbivore_cohort_instance.cnp_proportions["C"]
        n_proportion = herbivore_cohort_instance.cnp_proportions["N"]
        p_proportion = herbivore_cohort_instance.cnp_proportions["P"]

        # **Mock `find_intersecting_carcass_pools` return only relevant carcass pools**
        predator_cells = predator_cohort_instance.territory
        intersecting_cells = [
            cell for cell in predator_cells if cell in carcass_pools_by_cell_instance
        ]

        mock_carcass_pools = [
            pool
            for cell in intersecting_cells
            for pool in carcass_pools_by_cell_instance[cell]
        ]

        mocker.patch.object(
            herbivore_cohort_instance,
            "find_intersecting_carcass_pools",
            return_value=mock_carcass_pools,
        )

        # Get the number of actual intersecting carcass pools
        number_carcass_pools = len(mock_carcass_pools)

        # When get_eaten is called
        actual_mass_consumed = herbivore_cohort_instance.get_eaten(
            potential_consumed_mass,
            predator_cohort_instance,
            carcass_pools_by_cell_instance,
        )

        # Compute expected consumed and carcass mass
        total_mass_killed = (
            initial_individuals - expected_remaining_individuals
        ) * individual_mass
        expected_mass_consumed = (
            min(total_mass_killed, potential_consumed_mass) * mechanical_efficiency
        )

        # **Fix: Adjust for correct stoichiometry (C, N, P)**
        expected_carcass_mass_c = (
            (total_mass_killed - expected_mass_consumed)
            * (1 - decay_fraction_carcasses)
            * c_proportion
        )
        expected_carcass_mass_n = (
            (total_mass_killed - expected_mass_consumed)
            * (1 - decay_fraction_carcasses)
            * n_proportion
        )
        expected_carcass_mass_p = (
            (total_mass_killed - expected_mass_consumed)
            * (1 - decay_fraction_carcasses)
            * p_proportion
        )

        # **Divide across the number of intersecting pools**
        expected_carcass_mass_c_per_pool = (
            expected_carcass_mass_c / number_carcass_pools
        )
        expected_carcass_mass_n_per_pool = (
            expected_carcass_mass_n / number_carcass_pools
        )
        expected_carcass_mass_p_per_pool = (
            expected_carcass_mass_p / number_carcass_pools
        )

        # Compute total expected carcass mass for each nutrient
        expected_total_carcass_mass_c = (
            expected_carcass_mass_c_per_pool * number_carcass_pools
        )
        expected_total_carcass_mass_n = (
            expected_carcass_mass_n_per_pool * number_carcass_pools
        )
        expected_total_carcass_mass_p = (
            expected_carcass_mass_p_per_pool * number_carcass_pools
        )

        # Track final total carcass pool mass for each nutrient
        final_carcass_mass_c = sum(
            pool.scavengeable_cnp["C"]
            for pools in carcass_pools_by_cell_instance.values()
            for pool in pools
        )
        final_carcass_mass_n = sum(
            pool.scavengeable_cnp["N"]
            for pools in carcass_pools_by_cell_instance.values()
            for pool in pools
        )
        final_carcass_mass_p = sum(
            pool.scavengeable_cnp["P"]
            for pools in carcass_pools_by_cell_instance.values()
            for pool in pools
        )

        # Ensure the predator consumes the correct amount of mass
        assert sum(actual_mass_consumed.values()) == pytest.approx(
            expected_mass_consumed, rel=1e-6
        ), (
            f"Expected {expected_mass_consumed} mass consumed, but got"
            f"{sum(actual_mass_consumed.values())}"
        )

        # Ensure carcass pools receive the correct mass for each nutrient
        assert final_carcass_mass_c - initial_carcass_mass_c == pytest.approx(
            expected_total_carcass_mass_c, rel=1e-6
        )
        assert final_carcass_mass_n - initial_carcass_mass_n == pytest.approx(
            expected_total_carcass_mass_n, rel=1e-6
        )
        assert final_carcass_mass_p - initial_carcass_mass_p == pytest.approx(
            expected_total_carcass_mass_p, rel=1e-6
        )

    @pytest.mark.parametrize(
        "mass_consumed, expected_waste",
        [
            # Normal cases
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 20.0, "N": 2.0, "P": 0.2},
            ),
            (
                {"C": 50.0, "N": 5.0, "P": 0.5},
                {"C": 10.0, "N": 1.0, "P": 0.1},
            ),
            # Edge cases
            (
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
            ),  # Zero consumption
            (
                {"C": 1e9, "N": 1e9, "P": 1e9},
                {"C": 2e8, "N": 2e8, "P": 2e8},
            ),  # Extremely high consumption
            (
                {"C": 0.0000001, "N": 0.0000001, "P": 0.0000001},
                {
                    "C": 0.00000002,
                    "N": 0.00000002,
                    "P": 0.00000002,
                },
            ),  # Floating point precision
            (
                {"C": 1e-6, "N": 1e-6, "P": 1e-6},
                {"C": 2e-7, "N": 2e-7, "P": 2e-7},
            ),  # Minimum nonzero consumption
        ],
    )
    def test_eat(
        self,
        mocker,
        herbivore_cohort_instance,
        mass_consumed,
        expected_waste,
        excrement_pools_by_cell_instance,
    ):
        """Test that `eat` calls `grow` and `defecate` with correct arguments."""

        # Mock the grow method to return expected waste mass
        mock_grow = mocker.patch.object(
            herbivore_cohort_instance, "grow", return_value=expected_waste
        )

        # Mock the defecate method
        mock_defecate = mocker.patch.object(herbivore_cohort_instance, "defecate")

        # Call eat method
        herbivore_cohort_instance.eat(mass_consumed, excrement_pools_by_cell_instance)

        # Assert that grow was called once with the expected arguments
        mock_grow.assert_called_once_with(mass_consumed)

        # Assert that defecate was called once with the expected waste mass
        mock_defecate.assert_called_once_with(
            excrement_pools_by_cell_instance, expected_waste
        )

    @pytest.mark.parametrize(
        "mass_consumed, excrement_pools, expected_error_message",
        [
            # Missing required keys
            (
                {"C": 100.0, "N": 10.0},
                ["mock_pool"],
                "mass_consumed must contain all required keys",
            ),
            (
                {"C": 100.0, "P": 1.0},
                ["mock_pool"],
                "mass_consumed must contain all required keys",
            ),
            (
                {"N": 10.0, "P": 1.0},
                ["mock_pool"],
                "mass_consumed must contain all required keys",
            ),
            # Negative values
            (
                {"C": -100.0, "N": 10.0, "P": 1.0},
                ["mock_pool"],
                "Values in mass_consumed must be non-negative",
            ),
            (
                {"C": 100.0, "N": -10.0, "P": 1.0},
                ["mock_pool"],
                "Values in mass_consumed must be non-negative",
            ),
            (
                {"C": 100.0, "N": 10.0, "P": -1.0},
                ["mock_pool"],
                "Values in mass_consumed must be non-negative",
            ),
            # No excrement pools
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                [],
                "At least one excrement pool must be provided.",
            ),
        ],
    )
    def test_eat_errors(
        self,
        herbivore_cohort_instance,
        mass_consumed,
        excrement_pools,
        expected_error_message,
    ):
        """Test that `eat` raises appropriate ValueErrors for invalid inputs."""
        with pytest.raises(ValueError, match=expected_error_message):
            herbivore_cohort_instance.eat(mass_consumed, excrement_pools)

    @pytest.mark.parametrize(
        "mass_current, reproductive_mass, adult_mass, threshold, expected_result",
        [
            (50.0, 5.0, 100.0, 0.6, True),  # Below threshold (55 / 100 < 0.6)
            (60.0, 10.0, 100.0, 0.7, False),  # Below threshold (70 / 100 < 0.7)
            (70.0, 10.0, 100.0, 0.8, False),  # Equal to threshold (80 / 100 == 0.8)
            (80.0, 10.0, 100.0, 0.7, False),  # Above threshold (90 / 100 > 0.7)
            (
                0.0,
                0.0,
                100.0,
                0.1,
                True,
            ),  # Zero mass, should return True for any threshold
            (120.0, 20.0, 100.0, 1.0, False),  # Above adult mass, always False
        ],
    )
    def test_is_below_mass_threshold(
        self,
        herbivore_cohort_instance,
        mass_current,
        reproductive_mass,
        adult_mass,
        threshold,
        expected_result,
    ):
        """Test `is_below_mass_threshold` for different mass and threshold values."""

        from virtual_ecosystem.models.animal.cnp import CNP

        # Mock `mass_current` and `reproductive_mass` properties
        herbivore_cohort_instance.mass_cnp = CNP(C=mass_current, N=0.0, P=0.0)
        herbivore_cohort_instance.reproductive_mass_cnp = CNP(
            C=reproductive_mass, N=0.0, P=0.0
        )

        # Mock `adult_mass`
        herbivore_cohort_instance.functional_group.adult_mass = adult_mass

        # Call method and check result
        assert (
            herbivore_cohort_instance.is_below_mass_threshold(threshold)
            == expected_result
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
        animal_data_for_cohorts_instance,
    ):
        """Testing for calculate alpha."""
        # Assuming necessary imports and setup based on previous examples
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.model_config import AnimalConstants

        # Mock the scaling function to control its return value
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.alpha_i_k",
            return_value=expected_alpha,
        )

        # Setup constants and functional group mock
        constants = AnimalConstants()
        functional_group_mock = herbivore_functional_group_instance

        # Initialize the AnimalCohort instance with test parameters
        cohort_instance = AnimalCohort(
            functional_group=functional_group_mock,
            mass=mass_current,
            age=1.0,  # Example age
            individuals=1,  # Example number of individuals
            centroid_key=1,  # centroid
            grid=animal_data_for_cohorts_instance.grid,  # grid
            constants=constants,
        )

        # Execute the method under test
        result = cohort_instance.calculate_alpha()

        # Assert that the result matches the expected outcome for the given scenario
        assert result == expected_alpha, (
            f"Failed scenario: alpha_0_herb={alpha_0_herb}, mass_current={mass_current}"
        )

    @pytest.mark.parametrize(
        "target_plant_attrs, alpha, should_raise_error, expected_error_message",
        [
            # Normal cases: ensure k_i_k is called correctly
            ({"mass_current": 100.0}, 0.1, False, None),
            ({"mass_current": 50.0}, 0.5, False, None),
            ({"mass_current": 10.0}, 0.01, False, None),
            # Error cases: ensure input validation works
            (
                {"mass_current": -10.0},
                0.1,
                True,
                r"target_plant.mass_current must be non-negative",
            ),
            (
                {},
                0.1,
                True,
                r"target_plant.mass_current must be defined and non-negative",
            ),
            (
                {"mass_current": 100.0},
                -0.5,
                True,
                r"alpha must be positive",
            ),
            (
                {"mass_current": 100.0},
                0.0,
                True,
                r"alpha must be positive",
            ),
        ],
    )
    def test_calculate_potential_consumed_biomass(
        self,
        mocker,
        herbivore_cohort_instance,
        target_plant_attrs,
        alpha,
        should_raise_error,
        expected_error_message,
    ):
        """Test `calculate_potential_consumed_biomass`."""

        from virtual_ecosystem.models.animal.protocols import Resource

        # Mock the target plant with given attributes
        target_plant = mocker.MagicMock(spec=Resource)
        target_plant.mass_current = target_plant_attrs.get("mass_current", None)

        # Mock `k_i_k` to check call parameters (not its return value)
        mock_kik = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.k_i_k"
        )

        # Extract functional group parameter
        phi_herb_t = herbivore_cohort_instance.functional_group.constants.phi_herb_t
        A_cell = herbivore_cohort_instance.grid.cell_area

        if should_raise_error:
            # Ensure the correct error is raised
            with pytest.raises(ValueError, match=expected_error_message):
                herbivore_cohort_instance.calculate_potential_consumed_biomass(
                    target_plant, alpha
                )
        else:
            # Call the method
            herbivore_cohort_instance.calculate_potential_consumed_biomass(
                target_plant, alpha
            )

            # Ensure `k_i_k` was called with correct parameters
            mock_kik.assert_called_once_with(
                alpha, phi_herb_t, target_plant.mass_current, A_cell
            )

    def test_calculate_total_handling_time_for_herbivory(
        self, mocker, herbivore_cohort_instance
    ):
        """Test aggregation of handling times across array resources."""

        import numpy as np

        from virtual_ecosystem.models.animal.array_resources import CellResource

        # Create minimal CellResource objects (protocol-compatible)
        plant_list = []
        for i in range(3):
            plant_list.append(
                CellResource(
                    resource=object(),
                    available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
                    consumed_total_mass=np.zeros(1, dtype=float),
                    vertical_occupancy=herbivore_cohort_instance.functional_group.vertical_occupancy,
                    cell_id=i,
                )
            )

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
                    plant_list, alpha
                )
            )

            # Expected: each resource contributes (k_i_k + H_i_k)
            expected_handling_time = 3 * (20.0 + 0.2)

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
        assert result == 0.5, (
            "The result does not match the expected return value from sf.theta_opt_i"
        )

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
        alpha = 0.8
        theta_i_j = 0.7
        intersection_area = 5000.0

        mock_k_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.k_i_j",
            return_value=15.0,
        )

        result = herbivore_cohort_instance.calculate_potential_prey_consumed(
            alpha, theta_i_j, intersection_area
        )

        mock_k_i_j.assert_called_once_with(
            alpha,
            herbivore_cohort_instance.individuals,
            intersection_area,
            theta_i_j,
        )
        assert result == 15.0, "Expected potential prey consumed not returned."

    @pytest.mark.parametrize(
        "prey_masses, expected_call_count, expected_result",
        [
            pytest.param([], 0, 0.0, id="empty_prey_list"),
            pytest.param([1.0], 1, 6.0, id="single_prey"),
            pytest.param([1.0, 5.0], 2, 12.0, id="two_prey_different_masses"),
        ],
    )
    def test_calculate_total_handling_time_for_predation(
        self,
        mocker,
        herbivore_cohort_instance,
        prey_masses,
        expected_call_count,
        expected_result,
    ):
        """Test total handling time sums H_i_j * k_i_j correctly across prey cohorts."""
        animal_list = [mocker.MagicMock(mass_current=m) for m in prey_masses]
        theta_opt = 0.5

        mock_H_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.H_i_j",
            return_value=2.0,
        )
        mock_k_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.k_i_j",
            return_value=3.0,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.w_bar_i_j",
            return_value=0.8,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.alpha_i_j",
            return_value=1.5,
        )
        mocker.patch.object(herbivore_cohort_instance, "theta_i_j", return_value=0.4)

        result = herbivore_cohort_instance.calculate_total_handling_time_for_predation(
            animal_list, theta_opt
        )

        assert mock_H_i_j.call_count == expected_call_count
        assert mock_k_i_j.call_count == expected_call_count
        assert result == expected_result

        if animal_list:
            # theta_i_j always computed exactly once regardless of prey count
            herbivore_cohort_instance.theta_i_j.assert_called_once_with(animal_list)

            # verify the last call used the correct prey mass for that cohort
            last_prey_mass = prey_masses[-1]
            mock_H_i_j.assert_called_with(
                herbivore_cohort_instance.constants.h_pred_0,
                herbivore_cohort_instance.constants.M_pred_ref,
                herbivore_cohort_instance.mass_current,
                herbivore_cohort_instance.constants.b_pred,
                last_prey_mass,
            )

    @pytest.mark.parametrize(
        "n_target, expected_early_return",
        [
            pytest.param(0, True, id="zero_individuals_returns_zero"),
            pytest.param(10, False, id="normal_predation_rate"),
        ],
    )
    def test_F_i_j_individual(
        self,
        mocker,
        predator_cohort_instance,
        animal_list_instance,
        n_target,
        expected_early_return,
    ):
        """Test instantaneous predation rate calculation on a selected target cohort."""
        target_animal = animal_list_instance[0]
        target_animal.individuals = n_target

        theta_opt = 0.5

        mock_theta_opt = mocker.patch.object(
            predator_cohort_instance,
            "calculate_theta_opt_i",
            return_value=theta_opt,
        )
        mock_w_bar = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.w_bar_i_j",
            return_value=0.8,
        )
        mock_search_rate = mocker.patch.object(
            predator_cohort_instance,
            "calculate_predation_search_rate",
            return_value=0.8,
        )
        mock_theta_i_j = mocker.patch.object(
            predator_cohort_instance,
            "theta_i_j",
            return_value=0.7,
        )
        mock_potential_prey = mocker.patch.object(
            predator_cohort_instance,
            "calculate_potential_prey_consumed",
            return_value=10,
        )
        mock_total_handling = mocker.patch.object(
            predator_cohort_instance,
            "calculate_total_handling_time_for_predation",
            return_value=2,
        )

        rate = predator_cohort_instance.F_i_j_individual(
            animal_list_instance, target_animal
        )

        if expected_early_return:
            assert rate == 0.0
            mock_theta_opt.assert_not_called()
            mock_total_handling.assert_not_called()
            return

        # theta_opt drawn exactly once and passed into both w_bar and handling time
        mock_theta_opt.assert_called_once()
        mock_w_bar.assert_called_once_with(
            predator_cohort_instance.mass_current,
            target_animal.mass_current,
            theta_opt,
            predator_cohort_instance.constants.sigma_opt_pred_prey,
        )
        mock_search_rate.assert_called_once_with(0.8)
        mock_theta_i_j.assert_called_once_with(animal_list_instance)
        mock_potential_prey.assert_called_once_with(0.8, 0.7)

        # theta_opt threaded through to handling time denominator
        mock_total_handling.assert_called_once_with(animal_list_instance, theta_opt)

        N_i = predator_cohort_instance.individuals
        expected_rate = N_i * (10 / (1 + 2)) * (1 / n_target)
        assert rate == pytest.approx(expected_rate)

    def test_theta_i_j(self, predator_cohort_instance, animal_list_instance):
        """Test theta_i_j."""
        # TODO change this A_cell to call it from its real plant in the data
        A_cell = predator_cohort_instance.grid.cell_area

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

    def test_calculate_consumed_mass_predation_not_in_list(
        self,
        predator_cohort_instance,
        mocker,
    ):
        """Test behavior when target cohort is not present in the prey list."""
        from numpy import timedelta64

        predator = predator_cohort_instance

        prey = mocker.Mock()
        prey.mass_current = 10.0
        prey.individuals = 5

        # Use a day-based timedelta64, matching model usage
        adjusted_dt = timedelta64(10, "D")

        prey_list = []  # Empty list, so target is not present

        mocker.patch.object(predator, "F_i_j_individual", return_value=0.05)

        result = predator.calculate_consumed_mass_predation(
            prey_list,
            prey,
            adjusted_dt,
        )

        # No error expected — default formula still works, prey list isn't validated
        assert isinstance(result, float)
        assert result >= 0.0

    @pytest.mark.parametrize(
        "F_value, mass_current, individuals, expected_behavior",
        [
            (0.05, 10.0, 5, "formula"),  # normal case
            (0.0, 10.0, 5, 0.0),  # F = 0
            (1e6, 10.0, 5, "max"),  # very high F
            (0.05, 10.0, 0, 0.0),  # zero individuals
            (0.05, 0.0, 5, 0.0),  # zero mass
        ],
    )
    def test_calculate_consumed_mass_predation_cases(
        self,
        predator_cohort_instance,
        mocker,
        F_value,
        mass_current,
        individuals,
        expected_behavior,
    ):
        """Parametrized test for consumed mass predation with mocked prey."""
        from math import exp, isclose

        from numpy import timedelta64

        predator = predator_cohort_instance

        # Mock prey cohort
        prey = mocker.Mock()
        prey.mass_current = mass_current
        prey.individuals = individuals
        prey_list = [prey]

        # Use an integer-day timedelta64 and derive dt_days the same way the
        # model does internally.
        adjusted_dt = timedelta64(8, "D")
        dt_days = float(adjusted_dt / timedelta64(1, "D"))

        # Patch predation rate method to return fixed value
        mocker.patch.object(predator, "F_i_j_individual", return_value=F_value)

        # Run method under test
        result = predator.calculate_consumed_mass_predation(
            prey_list,
            prey,
            adjusted_dt,
        )

        if expected_behavior == "formula":
            expected = mass_current * individuals * (1.0 - exp(-F_value * dt_days))
            assert isclose(result, expected, rel_tol=1e-9)

        elif expected_behavior == "max":
            expected = mass_current * individuals
            assert isclose(result, expected, rel_tol=1e-3)

        else:
            # Zero F, zero individuals, or zero mass → zero consumption
            assert result == expected_behavior

    @pytest.mark.parametrize(
        "animal_list, carcass_pools, should_raise_error, expected_error_message,"
        "mock_consumed_mass, mock_actual_cnp, expected_total",
        [
            # Normal case: Predation occurs with valid inputs, single prey
            (
                [{"mock": True}],
                {1: [{"mock": True}]},
                False,
                None,
                {"C": 10.0, "N": 2.0, "P": 1.0},
                {"C": 8.0, "N": 1.5, "P": 0.8},
                {"C": 8.0, "N": 1.5, "P": 0.8},
            ),
            # Normal case: Two prey cohorts, sum their values
            (
                [{"mock": True}, {"mock": True}],
                {1: [{"mock": True}]},
                False,
                None,
                {"C": 5.0, "N": 1.0, "P": 0.5},
                {"C": 4.0, "N": 0.8, "P": 0.4},
                {"C": 8.0, "N": 1.6, "P": 0.8},
            ),
            # No prey (should return zero mass)
            (
                [],
                {1: [{"mock": True}]},
                False,
                None,
                None,
                None,
                {"C": 0.0, "N": 0.0, "P": 0.0},
            ),
            # animal_list is None
            (
                None,
                {1: [{"mock": True}]},
                True,
                "animal_list cannot be None.",
                None,
                None,
                None,
            ),
            # carcass_pools is None
            (
                [{"mock": True}],
                None,
                True,
                "carcass_pools cannot be None.",
                None,
                None,
                None,
            ),
            # calculate_consumed_mass_predation returns None
            (
                [{"mock": True}],
                {1: [{"mock": True}]},
                True,
                "calculate_consumed_mass_predation.*returned None",
                None,
                {"C": 8.0, "N": 1.5, "P": 0.8},
                None,
            ),
            # get_eaten returns None
            (
                [{"mock": True}],
                {1: [{"mock": True}]},
                True,
                "get_eaten.*returned None",
                {"C": 10.0, "N": 2.0, "P": 1.0},
                None,
                None,
            ),
        ],
    )
    def test_delta_mass_predation(
        self,
        mocker,
        herbivore_cohort_instance,
        animal_list,
        carcass_pools,
        should_raise_error,
        expected_error_message,
        mock_consumed_mass,
        mock_actual_cnp,
        expected_total,
    ):
        """Test `delta_mass_predation` for normal and error cases.."""

        # Import inside the method
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import CarcassPool

        # Mock the animal cohorts and carcass pools
        if animal_list:
            animal_list = [mocker.MagicMock(spec=AnimalCohort) for _ in animal_list]
            for prey in animal_list:
                prey.id = uuid.uuid4()
                mocker.patch.object(prey, "get_eaten", return_value=mock_actual_cnp)
        if carcass_pools:
            carcass_pools = {
                k: [mocker.MagicMock(spec=CarcassPool) for _ in v]
                for k, v in carcass_pools.items()
            }

        adjusted_dt = 10

        # Mock `calculate_consumed_mass_predation`
        mock_calculate = mocker.patch.object(
            herbivore_cohort_instance,
            "calculate_consumed_mass_predation",
            return_value=mock_consumed_mass,
        )

        # Mock `get_eaten` on all prey cohorts
        for prey in animal_list or []:
            mocker.patch.object(prey, "get_eaten", return_value=mock_actual_cnp)

        if should_raise_error:
            with pytest.raises(ValueError, match=expected_error_message):
                herbivore_cohort_instance.delta_mass_predation(
                    animal_list, carcass_pools, adjusted_dt=10
                )
        else:
            # Call method
            result = herbivore_cohort_instance.delta_mass_predation(
                animal_list, carcass_pools, adjusted_dt
            )

            # Ensure correct mass summation
            assert result == expected_total, (
                f"Expected {expected_total}, but got {result}"
            )

            # Ensure `calculate_consumed_mass_predation` was called for each prey
            assert mock_calculate.call_count == len(animal_list)

            # Ensure `get_eaten` was called for each prey
            for prey in animal_list:
                prey.get_eaten.assert_called_once_with(
                    mock_consumed_mass, herbivore_cohort_instance, carcass_pools
                )

    @pytest.mark.parametrize(
        "F_value, mass_current, expected",
        [
            (0.05, 10.0, "formula"),  # Normal case
            (0.0, 10.0, 0.0),  # Zero handling rate
            (1e6, 10.0, "max"),  # Extreme rate → consume all
            (0.05, 0.0, 0.0),  # No mass available
        ],
        ids=[
            "typical_formula_case",
            "zero_F_consumes_nothing",
            "high_F_consumes_all",
            "zero_mass_returns_zero",
        ],
    )
    def test_consumed_resource_mass_behavior(
        self, herbivore_cohort_instance, mocker, F_value, mass_current, expected
    ):
        """Test mass calculation with different F_i_k and mass_current cases."""
        from math import exp, isclose

        from numpy import timedelta64

        herbivore = herbivore_cohort_instance

        # Use a day-based timedelta64, matching model usage
        adjusted_dt = timedelta64(8, "D")
        dt_days = float(adjusted_dt / timedelta64(1, "D"))

        plant = mocker.Mock()
        plant.mass_current = mass_current
        mocker.patch.object(herbivore, "F_i_k", return_value=F_value)

        result = herbivore._consumed_resource_mass(
            [plant],
            plant,
            adjusted_dt,
        )

        if expected == "formula":
            # Normal case: compare against the same formula used in the method
            expected_val = mass_current * (1.0 - exp(-F_value * dt_days))
            assert isclose(result, expected_val, rel_tol=1e-9)
        elif expected == "max":
            # Extremely high F: should effectively consume all available mass
            assert isclose(result, mass_current, rel_tol=1e-3)
        else:
            # Zero F or zero mass: expect zero consumption
            assert result == expected

    @pytest.mark.parametrize(
        "gain, litter, expect_waste_call, expect_error, test_id",
        [
            (
                {"C": 10.0, "N": 5.0, "P": 2.0},
                {"C": 3.0, "N": 1.0, "P": 0.5},
                2,
                None,
                "standard",
            ),
            (
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                2,
                None,
                "no_gain",
            ),
            (
                {"C": 4.0, "N": 2.0, "P": 1.0},
                {"C": 1.0, "N": 0.5, "P": 0.25},
                0,
                KeyError,
                "no_waste_pool",
            ),
            (
                {"C": 5.0, "N": 2.5, "P": 1.0},
                {},
                0,
                None,
                "no_litter",
            ),
        ],
        ids=lambda param: param if isinstance(param, str) else None,
    )
    def test_forage_resource_list_gain_and_waste(
        self,
        herbivore_cohort_instance,
        mocker,
        gain,
        litter,
        expect_waste_call,
        expect_error,
        test_id,
    ):
        """Test `forage_resource_list` with different gain/litter scenarios."""
        herbivore = herbivore_cohort_instance
        herbivore.functional_group.conversion_efficiency = 0.5

        # Create two mock resources
        resource1 = mocker.Mock()
        resource1.mass_current = 10.0
        resource1.cell_id = 1
        resource1.get_eaten.return_value = (gain, litter)

        resource2 = mocker.Mock()
        resource2.mass_current = 5.0
        resource2.cell_id = 2
        resource2.get_eaten.return_value = (gain, litter)

        # Waste pool, with conditional presence based on test
        if test_id == "no_waste_pool":
            waste_pools = {1: mocker.Mock()}  # Only one key, missing key 2
        else:
            waste = mocker.Mock()
            waste_pools = {1: waste, 2: waste}

        # Mock calculate_consumed_mass
        mock_calc = mocker.Mock(return_value=5.0)

        if expect_error:
            with pytest.raises(expect_error):
                herbivore.forage_resource_list(
                    resources=[resource1, resource2],
                    adjusted_dt=10,
                    calculate_consumed_mass=mock_calc,
                    herbivory_waste_pools=waste_pools,
                    resource_kind="plant_resource",
                )
        else:
            result = herbivore.forage_resource_list(
                resources=[resource1, resource2],
                adjusted_dt=10,
                calculate_consumed_mass=mock_calc,
                herbivory_waste_pools=waste_pools,
                resource_kind="plant_resource",
            )

            expected = {
                "C": gain["C"] * 0.5 * 2,
                "N": gain["N"] * 0.5 * 2,
                "P": gain["P"] * 0.5 * 2,
            }

            assert result == expected

            if expect_waste_call:
                for waste in waste_pools.values():
                    assert waste.add_waste.call_count == expect_waste_call

    def test_delta_mass_herbivory_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test herbivory wrapper delegates to forage_resource_list correctly."""
        cohort = herbivore_cohort_instance
        plant_list = [mocker.Mock()]
        waste_pools = {4: mocker.Mock()}

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 1, "N": 2, "P": 3},
        )

        result = cohort.delta_mass_herbivory(
            plant_list=plant_list,
            adjusted_dt=7.5,
            herbivory_waste_pools=waste_pools,
        )

        mock_forage.assert_called_once_with(
            resources=plant_list,
            adjusted_dt=7.5,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            herbivory_waste_pools=waste_pools,
            resource_kind="plant_resource",
        )
        assert result == {"C": 1, "N": 2, "P": 3}

    def test_delta_mass_detritivory_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test detritivory wrapper delegates to forage_resource_list correctly."""
        cohort = herbivore_cohort_instance
        pools = [mocker.Mock()]

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 1, "N": 2, "P": 3},
        )

        result = cohort.delta_mass_detritivory(pools, adjusted_dt=7.5)

        mock_forage.assert_called_once_with(
            resources=pools,
            adjusted_dt=7.5,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            resource_kind="litter_pool",
        )
        assert result == {"C": 1, "N": 2, "P": 3}

    def test_delta_mass_carcass_scavenging_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test carcass scavenging wrapper delegates to forage_resource_list."""
        cohort = herbivore_cohort_instance
        carcass_pools = [mocker.Mock()]

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 1.0, "N": 2.0, "P": 3.0},
        )

        result = cohort.delta_mass_carcass_scavenging(
            carcass_pools=carcass_pools,
            adjusted_dt=7.5,
        )

        mock_forage.assert_called_once_with(
            resources=carcass_pools,
            adjusted_dt=7.5,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            resource_kind="carcass_pool",
        )

        assert result == {"C": 1.0, "N": 2.0, "P": 3.0}

    def test_delta_mass_excrement_scavenging_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test excrement scavenging wrapper delegates to forage_resource_list."""
        cohort = herbivore_cohort_instance
        excrement_pools = [mocker.Mock()]

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 4.0, "N": 1.0, "P": 0.5},
        )

        result = cohort.delta_mass_excrement_scavenging(
            excrement_pools=excrement_pools,
            adjusted_dt=7.5,
        )

        mock_forage.assert_called_once_with(
            resources=excrement_pools,
            adjusted_dt=7.5,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            resource_kind="excrement_pool",
        )

        assert result == {"C": 4.0, "N": 1.0, "P": 0.5}

    def test_delta_mass_fruiting_fungivory_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test fruiting fungivory wrapper delegates to forage_resource_list."""
        cohort = herbivore_cohort_instance
        fruits = [mocker.Mock()]
        waste_pools = {0: mocker.Mock()}

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 1, "N": 2, "P": 3},
        )

        result = cohort.delta_mass_fruiting_fungivory(
            fungal_fruit_list=fruits,
            adjusted_dt=5.0,
            herbivory_waste_pools=waste_pools,
        )

        mock_forage.assert_called_once_with(
            resources=fruits,
            adjusted_dt=5.0,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            herbivory_waste_pools=waste_pools,
            resource_kind="fungal_fruit_pool",
        )
        assert result == {"C": 1, "N": 2, "P": 3}

    def test_delta_mass_soil_fungivory_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test soil fungivory wrapper delegates to forage_resource_list."""
        cohort = herbivore_cohort_instance
        fungi = [mocker.Mock()]

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 4, "N": 5, "P": 6},
        )

        result = cohort.delta_mass_soil_fungivory(
            soil_fungi_list=fungi,
            adjusted_dt=3.25,
        )

        mock_forage.assert_called_once_with(
            resources=fungi,
            adjusted_dt=3.25,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            herbivory_waste_pools=None,
            resource_kind="soil_fungi_pool",
        )
        assert result == {"C": 4, "N": 5, "P": 6}

    def test_delta_mass_pomivory_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test pomivory wrapper delegates to forage_resource_list."""
        cohort = herbivore_cohort_instance
        poms = [mocker.Mock()]

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 7, "N": 8, "P": 9},
        )

        result = cohort.delta_mass_pomivory(
            pom_list=poms,
            adjusted_dt=2.0,
        )

        mock_forage.assert_called_once_with(
            resources=poms,
            adjusted_dt=2.0,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            herbivory_waste_pools=None,  #
            resource_kind="pom_pool",
        )
        assert result == {"C": 7, "N": 8, "P": 9}

    def test_delta_mass_bacteriophagy_calls_forage_resource_list(
        self, herbivore_cohort_instance, mocker
    ):
        """Test bacteriophagy wrapper delegates to forage_resource_list."""
        cohort = herbivore_cohort_instance
        bacteria = [mocker.Mock()]

        mock_forage = mocker.patch.object(
            cohort,
            "forage_resource_list",
            return_value={"C": 10, "N": 11, "P": 12},
        )

        result = cohort.delta_mass_bacteriophagy(
            bacteria_list=bacteria,
            adjusted_dt=1.5,
        )

        mock_forage.assert_called_once_with(
            resources=bacteria,
            adjusted_dt=1.5,
            calculate_consumed_mass=cohort._consumed_resource_mass,
            herbivory_waste_pools=None,
            resource_kind="bacteria_pool",
        )
        assert result == {"C": 10, "N": 11, "P": 12}

    @pytest.mark.parametrize(
        "cohort_instance, diet_string, plant_list, animal_list, fungal_fruit_list,"
        "soil_fungi_list, pom_list, bacteria_list, expected_nutrient_gain,"
        "delta_mass_mock",
        [
            (
                "herbivore_cohort_instance",
                "foliage_fruit",
                "array_plant_list_instance",
                [],
                [],
                [],
                [],
                [],
                {"C": 60.0, "N": 30.0, "P": 10.0},
                "delta_mass_herbivory",
            ),
            (
                "predator_cohort_instance",
                "vertebrates_invertebrates_carcasses",
                [],
                "animal_list_instance",
                [],
                [],
                [],
                [],
                {"C": 120.0, "N": 60.0, "P": 20.0},
                "delta_mass_predation",
            ),
            (
                "fungivore_cohort_instance",
                "mushrooms",
                [],
                [],
                "fungal_fruit_list_instance",
                [],
                [],
                [],
                {"C": 25.0, "N": 5.0, "P": 2.5},
                "delta_mass_fruiting_fungivory",
            ),
        ],
        ids=["herbivore", "carnivore", "fungivore"],
    )
    def test_forage_cohort(
        self,
        mocker,
        request,
        cohort_instance,
        diet_string,
        plant_list,
        animal_list,
        fungal_fruit_list,
        soil_fungi_list,
        pom_list,
        bacteria_list,
        expected_nutrient_gain,
        delta_mass_mock,
        array_plant_list_instance,
        animal_list_instance,
        fungal_fruit_list_instance,
        excrement_pool_instance,
        carcass_pools_by_cell_instance,
        herbivory_waste_pool_instance,
    ):
        """Test forage_cohort routes resources and calls correct delta_mass_* helper."""
        from numpy import timedelta64

        from virtual_ecosystem.models.animal.animal_traits import DietType

        cohort = request.getfixturevalue(cohort_instance)
        cohort.functional_group.diet = DietType.parse(diet_string)

        # Resolve lists from fixture names if provided as strings.
        if isinstance(plant_list, str):
            plant_list = request.getfixturevalue(plant_list)
        if isinstance(animal_list, str):
            animal_list = request.getfixturevalue(animal_list)
        if isinstance(fungal_fruit_list, str):
            fungal_fruit_list = request.getfixturevalue(fungal_fruit_list)

        # Herbivory waste pools: keyed by cell_id for plant-like resources.
        herbivory_waste_pools = {
            plant.cell_id: herbivory_waste_pool_instance
            for plant in array_plant_list_instance
        }

        mock_delta_mass = mocker.patch.object(
            cohort, delta_mass_mock, return_value=expected_nutrient_gain
        )

        empty_list = []
        dt = timedelta64(30, "D")

        cohort.forage_cohort(
            plant_list=plant_list,
            animal_list=animal_list,
            fungal_fruit_list=fungal_fruit_list,
            soil_fungi_list=soil_fungi_list,
            pom_list=pom_list,
            bacteria_list=bacteria_list,
            litter_pools=empty_list,
            excrement_pools=[excrement_pool_instance],
            carcass_pool_map=carcass_pools_by_cell_instance,
            scavenge_carcass_pools=empty_list,
            scavenge_excrement_pools=empty_list,
            herbivory_waste_pools=herbivory_waste_pools
            if diet_string == "foliage_fruit"
            else {},
            dt=dt,
        )

        mock_delta_mass.assert_called_once()
        kwargs = mock_delta_mass.call_args.kwargs

        if diet_string == "foliage_fruit":
            assert kwargs["plant_list"] == array_plant_list_instance
            assert kwargs["herbivory_waste_pools"] == herbivory_waste_pools
            assert kwargs["adjusted_dt"] == pytest.approx(
                dt * 0 + kwargs["adjusted_dt"]
            )
            assert kwargs["adjusted_dt"] > 0

        elif diet_string == "vertebrates_invertebrates_carcasses":
            assert kwargs["animal_list"] == animal_list_instance
            assert kwargs["carcass_pools"] == carcass_pools_by_cell_instance
            assert kwargs["adjusted_dt"] > 0

        elif diet_string == "mushrooms":
            assert kwargs["fungal_fruit_list"] == fungal_fruit_list_instance
            assert kwargs["adjusted_dt"] > 0

        else:
            assert False, f"Unhandled diet_string: {diet_string}"

    def test_forage_cohort_earthworm_multisoil(
        self,
        mocker,
        earthworm_cohort_instance,
        soil_fungi_list_instance,
        pom_list_instance,
        bacteria_list_instance,
        excrement_pool_instance,
        carcass_pools_by_cell_instance,
    ):
        """Ensure composite diet routes to all four paths."""
        # Imports inside test per project rules.
        from virtual_ecosystem.models.animal.animal_traits import DietType

        cohort = earthworm_cohort_instance
        cohort.functional_group.diet = DietType.parse("detritus_fungi_pom_bacteria")

        # Patch delta-mass methods to observe calls and avoid side effects.
        expected = {"C": 1.0, "N": 0.5, "P": 0.1}
        m_det = mocker.patch.object(
            cohort, "delta_mass_detritivory", return_value=expected
        )
        m_fungi = mocker.patch.object(
            cohort, "delta_mass_soil_fungivory", return_value=expected
        )
        m_pom = mocker.patch.object(
            cohort, "delta_mass_pomivory", return_value=expected
        )
        m_bact = mocker.patch.object(
            cohort, "delta_mass_bacteriophagy", return_value=expected
        )

        # Litter must be non-empty so detritivory path is exercised.
        litter_pools = ["litter_resources"]

        cohort.forage_cohort(
            plant_list=[],
            animal_list=[],
            fungal_fruit_list=[],
            soil_fungi_list=soil_fungi_list_instance,
            pom_list=pom_list_instance,
            bacteria_list=bacteria_list_instance,
            litter_pools=litter_pools,
            excrement_pools=[excrement_pool_instance],
            carcass_pool_map=carcass_pools_by_cell_instance,
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools={},
            dt=30,
        )

        # Each relevant path should be called exactly once with correct args.
        m_det.assert_called_once()
        m_fungi.assert_called_once()
        m_pom.assert_called_once()
        m_bact.assert_called_once()

        assert m_det.call_args.kwargs["litter_pools"] == litter_pools
        assert m_fungi.call_args.kwargs["soil_fungi_list"] == soil_fungi_list_instance
        assert m_pom.call_args.kwargs["pom_list"] == pom_list_instance
        assert m_bact.call_args.kwargs["bacteria_list"] == bacteria_list_instance

        # Basic sanity: adjusted_dt is numeric for each call.
        for m in (m_det, m_fungi, m_pom, m_bact):
            assert isinstance(m.call_args.kwargs["adjusted_dt"], int | float)

    def test_forage_cohort_skips_when_no_individuals(
        self, mocker, herbivore_cohort_instance
    ):
        """Ensure cohort with 0 individuals does not forage."""
        cohort = herbivore_cohort_instance
        cohort.individuals = 0
        mocker.patch.object(
            type(cohort),
            "mass_current",
            new_callable=mocker.PropertyMock,
            return_value=0.0,
        )
        mocker.patch.object(cohort, "delta_mass_herbivory")
        mock_eat = mocker.patch.object(cohort, "eat")

        cohort.forage_cohort(
            plant_list=[],
            animal_list=[],
            fungal_fruit_list=[],
            soil_fungi_list=[],
            pom_list=[],
            bacteria_list=[],
            litter_pools=[],
            excrement_pools=[],
            carcass_pool_map={},
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools={},
            dt=30,
        )

        mock_eat.assert_not_called()

    def test_forage_cohort_skips_when_no_mass(self, mocker, herbivore_cohort_instance):
        """Ensure cohort with 0 mass does not forage."""
        cohort = herbivore_cohort_instance
        cohort.individuals = 5

        # Patch the mass_current property to return 0.0
        mocker.patch.object(
            type(cohort),
            "mass_current",
            new_callable=mocker.PropertyMock,
            return_value=0.0,
        )

        mock_delta = mocker.patch.object(cohort, "delta_mass_herbivory")
        mock_eat = mocker.patch.object(cohort, "eat")

        cohort.forage_cohort(
            plant_list=[],
            animal_list=[],
            fungal_fruit_list=[],
            soil_fungi_list=[],
            pom_list=[],
            bacteria_list=[],
            litter_pools=[],
            excrement_pools=[],
            carcass_pool_map={},
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools={},
            dt=30,
        )

        mock_delta.assert_not_called()
        mock_eat.assert_not_called()

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

        # Mock `mass_current` properly as a property on the class
        mocker.patch.object(
            type(cohort),
            "mass_current",
            new_callable=mocker.PropertyMock,
            return_value=mass_current,
        )

        # Mock `constants`
        cohort.constants = mocker.MagicMock(
            V_disp=V_disp, M_disp_ref=M_disp_ref, o_disp=o_disp
        )

        # Mock `juvenile_dispersal_speed`
        mocked_velocity = V_disp * (mass_current / M_disp_ref) ** o_disp
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.juvenile_dispersal_speed",
            return_value=mocked_velocity,
        )

        # Calculate expected probability
        A_cell = herbivore_cohort_instance.grid.cell_area
        grid_side = sqrt(A_cell)
        calculated_probability = mocked_velocity / grid_side
        expected_probability = min(calculated_probability, 1.0)  # Cap at 1.0

        # Call the method under test
        probability_of_dispersal = cohort.migrate_juvenile_probability()

        # Assertion to check if the method returns the correct probability
        assert probability_of_dispersal == expected_probability, (
            f"Expected {expected_probability}, but got {probability_of_dispersal}."
        )

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
        cohort.time_to_maturity = t_to_maturity
        cohort.time_since_maturity = t_since_maturity
        cohort.functional_group.adult_mass = mass_max

        # Mock `mass_current` properly as a property on the class
        mocker.patch.object(
            type(cohort),
            "mass_current",
            new_callable=mocker.PropertyMock,
            return_value=mass_current,
        )

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
        cohort.inflict_non_predation_mortality(dt, [carcass_pool_instance])

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
        assert cohort.individuals == 100 - expected_dead, (
            "The calculated number of dead individuals doesn't match the expected "
            "value."
        )

    @pytest.mark.parametrize(
        "mock_random, expected_result",
        [
            (0.0, True),  # Always migrate (random value < probability)
            (0.05, True),  # Should migrate (0.05 < 0.083)
            (0.083, True),  # Edge case (should migrate)
            (0.084, False),  # Just above threshold
            (0.5, False),  # Should not migrate
            (0.99, False),  # Almost certain not to migrate
        ],
    )
    def test_is_migration_season(
        self, mocker, herbivore_cohort_instance, mock_random, expected_result
    ):
        """Test whether is_migration_season correctly triggers based on probability."""

        # Mock the correct module where random() is called
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.random.random",
            return_value=mock_random,
        )

        # Run function
        result = herbivore_cohort_instance.is_migration_season()

        # Ensure print happens even if the test fails
        assert result == expected_result, (
            f"\n[ASSERT FAILED] Expected {expected_result} but got {result}\n"
        )

    @pytest.mark.parametrize(
        "prey_mass, prey_individuals, vertical_match, is_same_object, expected",
        [
            (10.0, 5, True, False, True),  # Valid prey
            (0.00001, 5, True, False, False),  # Too small
            (2000.0, 5, True, False, False),  # Too large
            (10.0, 0, True, False, False),  # No individuals
            (10.0, 5, False, False, False),  # No vertical match
            (10.0, 5, True, True, False),  # Same object
        ],
    )
    def test_can_prey_on(
        self,
        prey_mass,
        prey_individuals,
        vertical_match,
        is_same_object,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Parametrized test for can_prey_on across valid and invalid scenarios."""
        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import DietType
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )
        from virtual_ecosystem.models.animal.scaling_functions import (
            prey_group_selection,
        )

        # Setup grid and functional groups
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        predator_group = get_functional_group_by_name(
            functional_group_list_instance, "carnivorous_mammal"
        )
        prey_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Setup predator
        predator = AnimalCohort(
            functional_group=predator_group,
            mass=40.0,
            age=100.0,
            individuals=10,
            centroid_key=4,
            grid=grid,
            constants=constants_instance,
        )

        predator.prey_groups = prey_group_selection(
            predator.functional_group.diet,
            predator.functional_group.adult_mass,
            predator.functional_group.prey_scaling,
            functional_group_list_instance,
        )

        print(DietType.parse("vertebrates_invertebrates_carcasses"))

        assert "herbivorous_mammal" in predator.prey_groups, (
            f"herbivorous_mammal not in"
            f"self.predator.prey_groups: {predator.prey_groups.keys()}"
        )

        # If testing same-object condition, reuse predator as prey
        if is_same_object:
            prey = predator
        else:
            prey = AnimalCohort(
                functional_group=prey_group,
                mass=prey_mass,
                age=50.0,
                individuals=prey_individuals,
                centroid_key=4,
                grid=grid,
                constants=constants_instance,
            )

        # Patch vertical matching result
        setattr(predator, "match_vertical", lambda _: vertical_match)

        assert predator.can_prey_on(prey) is expected

    @pytest.mark.parametrize(
        "territory, cell_prey_map, prey_diet, expected",
        [
            # Single valid prey in one cell (vertebrate prey allowed)
            ([1], {1: ["valid_vert"]}, "vertebrates", 1),
            # Valid and invalid prey in different cells (only vertebrates allowed)
            ([1, 2], {1: ["valid_vert"], 2: ["invalid_vert"]}, "vertebrates", 1),
            # All prey invalid (only vertebrates allowed)
            ([1, 2], {1: ["invalid_vert"], 2: ["invalid_vert"]}, "vertebrates", 0),
            # Multiple valid prey (only vertebrates allowed)
            ([1, 2], {1: ["valid_vert"], 2: ["valid_vert"]}, "vertebrates", 2),
            # Mixed prey in one cell (only vertebrates allowed)
            ([1], {1: ["valid_vert", "invalid_vert"]}, "vertebrates", 1),
            # Invertebrates excluded when only vertebrates allowed
            ([1], {1: ["valid_invert"]}, "vertebrates", 0),
            # Vertebrates excluded when only invertebrates allowed
            ([1], {1: ["valid_vert"]}, "invertebrates", 0),
            # Both prey categories allowed
            ([1], {1: ["valid_vert", "valid_invert"]}, "vertebrates_invertebrates", 2),
        ],
    )
    def test_get_prey(
        self,
        territory,
        cell_prey_map,
        prey_diet,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Parametrized test for get_prey."""
        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import DietType
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional groups
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        predator_group = get_functional_group_by_name(
            functional_group_list_instance, "carnivorous_mammal"
        )
        vertebrate_prey_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )
        invertebrate_prey_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_insect_iteroparous"
        )

        # Create predator and assign mock territory
        predator = AnimalCohort(
            functional_group=predator_group,
            mass=40.0,
            age=100.0,
            individuals=10,
            centroid_key=4,
            grid=grid,
            constants=constants_instance,
        )
        predator.territory = territory

        # Create mock prey cohorts
        communities: dict[int, list[AnimalCohort]] = {}
        for cell_id, prey_types in cell_prey_map.items():
            cell_prey: list[AnimalCohort] = []
            for prey_type in prey_types:
                if "invert" in prey_type:
                    functional_group = invertebrate_prey_group
                else:
                    functional_group = vertebrate_prey_group

                is_valid = prey_type.startswith("valid")
                cohort = AnimalCohort(
                    functional_group=functional_group,
                    mass=10.0 if is_valid else 2000.0,
                    age=50.0,
                    individuals=5,
                    centroid_key=cell_id,
                    grid=grid,
                    constants=constants_instance,
                )
                cell_prey.append(cohort)
            communities[cell_id] = cell_prey

        # Patch can_prey_on to return True for mass < 1000 only
        predator.can_prey_on = lambda prey: prey.mass_current < 1000.0

        # Run and assert
        prey_flags = DietType.parse(prey_diet)
        result = predator.get_prey(communities=communities, prey_diet=prey_flags)
        assert len(result) == expected

    @pytest.mark.parametrize(
        "resource_vertical, expected",
        [
            ("GROUND", True),
            ("CANOPY", False),
        ],
    )
    def test_can_forage_on(
        self,
        resource_vertical,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test can_forage_on using a CellResource from array_resources."""
        import numpy as np

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
        from virtual_ecosystem.models.animal.array_resources import CellResource
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )

        cell_resource = CellResource(
            resource=object(),
            available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
            consumed_total_mass=np.zeros(1, dtype=float),
            vertical_occupancy=getattr(VerticalOccupancy, resource_vertical),
            cell_id=0,
        )

        assert cohort.can_forage_on(cell_resource) is expected

    @pytest.mark.parametrize(
        "territory, cell_pool_map, expected",
        [
            # Single pool in one cell
            ([1], {1: [1]}, 1),
            # Pools in multiple cells
            ([1, 2], {1: [1], 2: [2]}, 2),
            # Territory includes a cell with no pools
            ([1, 2], {1: [1]}, 1),
            # Territory with no matching cells
            ([3], {1: [1], 2: [2]}, 0),
            # Multiple pools in a single cell
            ([1], {1: [1, 2, 3]}, 3),
        ],
    )
    def test_get_excrement_pools(
        self,
        territory,
        cell_pool_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_excrement_pools returns all pools in the territory."""

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import ExcrementPool
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create cohort with a known territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Create dummy excrement pools from simple integers
        excrement_pools = {
            cell_id: [ExcrementPool() for _ in pool_ids]
            for cell_id, pool_ids in cell_pool_map.items()
        }

        result = cohort.get_excrement_pools(excrement_pools)

        assert len(result) == expected

    @pytest.mark.parametrize(
        "territory, pool_map, expected",
        [
            # Single pool in one cell
            ([1], {1: 1}, 1),
            # Pools in multiple cells
            ([1, 2], {1: 1, 2: 1}, 2),
            # Territory includes a cell with no pool
            ([1, 2], {1: 1}, 1),
            # Territory with no matching cells
            ([3], {1: 1, 2: 1}, 0),
        ],
    )
    def test_get_herbivory_waste_pools(
        self,
        territory,
        pool_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_herbivory_waste_pools returns all pools in the territory."""

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import HerbivoryWaste
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create cohort with a known territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Create dummy herbivory waste pool map
        herbivory_waste = {
            cell_id: HerbivoryWaste("leaf") for cell_id in pool_map.keys()
        }

        result = cohort.get_herbivory_waste_pools(herbivory_waste)

        assert len(result) == expected

    @pytest.mark.parametrize(
        "territory, cell_pool_map, expected",
        [
            # Single pool in one cell
            ([1], {1: [1]}, 1),
            # Pools in multiple cells
            ([1, 2], {1: [1], 2: [2]}, 2),
            # Territory includes a cell with no pool
            ([1, 2], {1: [1]}, 1),
            # Territory with no matching cells
            ([3], {1: [1], 2: [2]}, 0),
            # Multiple pools in a single cell
            ([1], {1: [1, 2, 3]}, 3),
        ],
    )
    def test_get_carcass_pools(
        self,
        territory,
        cell_pool_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_carcass_pools returns all pools in the territory."""

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import CarcassPool
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create cohort with a known territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Create dummy carcass pools from simple identifiers
        carcass_pools = {
            cell_id: [CarcassPool() for _ in pool_ids]
            for cell_id, pool_ids in cell_pool_map.items()
        }

        result = cohort.get_carcass_pools(carcass_pools)

        assert len(result) == expected

    @pytest.mark.parametrize(
        "territory, cell_fruit_map, expected",
        [
            # Single valid fruiting pool
            ([1], {1: "valid"}, 1),
            # Valid and invalid in separate cells
            ([1, 2], {1: "valid", 2: "invalid"}, 1),
            # All invalid
            ([1, 2], {1: "invalid", 2: "invalid"}, 0),
            # Multiple valid across cells
            ([1, 2], {1: "valid", 2: "valid"}, 2),
            # Territory includes a cell with no pool
            ([1, 2], {1: "valid"}, 1),
        ],
    )
    def test_get_fungal_fruit_pools(
        self,
        territory,
        cell_fruit_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_fungal_fruit_pools with singleton-per-cell mapping."""

        from types import SimpleNamespace

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create dummy cohort with defined territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Build singleton-per-cell dict of "fungal fruiting pools".
        # We use simple objects to avoid needing real Data; only identity matters.
        fungal_fruiting_bodies = {}  # dict[int, object]
        all_fruits = []  # list[tuple[object, bool]]

        for cell_id, label in cell_fruit_map.items():
            fruit = SimpleNamespace(cell_id=cell_id)
            fungal_fruiting_bodies[cell_id] = fruit
            all_fruits.append((fruit, label == "valid"))

        # Filter: keep only objects flagged "valid" above.
        cohort.can_forage_on = lambda resource: any(
            resource is res and is_valid for res, is_valid in all_fruits
        )

        result = cohort.get_fungal_fruit_pools(fungal_fruiting_bodies)
        assert len(result) == expected

    @pytest.mark.parametrize(
        "territory, cell_soil_map, expected",
        [
            # Single valid fungi pool
            ([1], {1: "valid"}, 1),
            # Valid and invalid in separate cells
            ([1, 2], {1: "valid", 2: "invalid"}, 1),
            # All invalid
            ([1, 2], {1: "invalid", 2: "invalid"}, 0),
            # Multiple valid across cells
            ([1, 2], {1: "valid", 2: "valid"}, 2),
            # Territory includes a cell with no fungi pool entry
            ([1, 2], {1: "valid"}, 1),
        ],
    )
    def test_get_soil_fungi_pools(
        self,
        territory,
        cell_soil_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_soil_fungi_pools with per-cell dict[str, SoilPool] mapping.

        Builds a singleton 'fungi' entry per cell using simple objects and filters
        with `can_forage_on` to count only those marked as valid.
        """

        from types import SimpleNamespace

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create dummy cohort with defined territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Build soil_pools: dict[int, dict[str, SoilPool-like]]
        soil_pools = {}  # dict[int, dict[str, object]]
        all_fungi = []  # list[tuple[object, bool]]

        for cell_id, label in cell_soil_map.items():
            pool = SimpleNamespace(cell_id=cell_id)
            soil_pools[cell_id] = {"fungi": pool}
            all_fungi.append((pool, label == "valid"))

        # Filter: keep only objects flagged "valid" above
        cohort.can_forage_on = lambda resource: any(
            resource is res and is_valid for res, is_valid in all_fungi
        )

        result = cohort.get_soil_fungi_pools(soil_pools)
        assert len(result) == expected

    @pytest.mark.parametrize(
        "territory, cell_soil_map, expected",
        [
            # Single valid POM pool
            ([1], {1: "valid"}, 1),
            # Valid and invalid in separate cells
            ([1, 2], {1: "valid", 2: "invalid"}, 1),
            # All invalid
            ([1, 2], {1: "invalid", 2: "invalid"}, 0),
            # Multiple valid across cells
            ([1, 2], {1: "valid", 2: "valid"}, 2),
            # Territory includes a cell with no POM entry
            ([1, 2], {1: "valid"}, 1),
        ],
    )
    def test_get_pom_pools(
        self,
        territory,
        cell_soil_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_pom_pools with per-cell dict[str, SoilPool] mapping.

        Builds a singleton 'pom' entry per cell using simple objects and filters with
        `can_forage_on` to count only those marked as valid.
        """
        from types import SimpleNamespace

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create dummy cohort with defined territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Build soil_pools: dict[int, dict[str, SoilPool-like]]
        soil_pools = {}  # dict[int, dict[str, object]]
        all_pom = []  # list[tuple[object, bool]]

        for cell_id, label in cell_soil_map.items():
            pool = SimpleNamespace(cell_id=cell_id)
            soil_pools[cell_id] = {"pom": pool}
            all_pom.append((pool, label == "valid"))

        # Filter: keep only objects flagged "valid" above
        cohort.can_forage_on = lambda resource: any(
            resource is res and is_valid for res, is_valid in all_pom
        )

        result = cohort.get_pom_pools(soil_pools)
        assert len(result) == expected

    @pytest.mark.parametrize(
        "territory, cell_soil_map, expected",
        [
            # Single valid bacteria pool
            ([1], {1: "valid"}, 1),
            # Valid and invalid in separate cells
            ([1, 2], {1: "valid", 2: "invalid"}, 1),
            # All invalid
            ([1, 2], {1: "invalid", 2: "invalid"}, 0),
            # Multiple valid across cells
            ([1, 2], {1: "valid", 2: "valid"}, 2),
            # Territory includes a cell with no bacteria entry
            ([1, 2], {1: "valid"}, 1),
        ],
    )
    def test_get_bacteria_pools(
        self,
        territory,
        cell_soil_map,
        expected,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test get_bacteria_pools with per-cell dict[str, SoilPool] mapping.

        Builds a singleton 'bacteria' entry per cell using simple objects and filters
        with `can_forage_on` to count only those marked as valid.
        """
        from types import SimpleNamespace

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        # Create dummy cohort with defined territory
        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Build soil_pools: dict[int, dict[str, SoilPool-like]]
        soil_pools = {}  # dict[int, dict[str, object]]
        all_bacteria = []  # list[tuple[object, bool]]

        for cell_id, label in cell_soil_map.items():
            pool = SimpleNamespace(cell_id=cell_id)
            soil_pools[cell_id] = {"bacteria": pool}
            all_bacteria.append((pool, label == "valid"))

        # Filter: keep only objects flagged "valid" above
        cohort.can_forage_on = lambda resource: any(
            resource is res and is_valid for res, is_valid in all_bacteria
        )

        result = cohort.get_bacteria_pools(soil_pools)
        assert len(result) == expected

    @pytest.mark.parametrize(
        "cohort_occupancy, resource_occupancy, expected",
        [
            ("soil", "soil", True),
            ("soil", "soil_ground", True),
            ("soil", "ground", False),
            ("soil", "canopy", False),
            ("soil", "ground_canopy", False),
            ("soil", "soil_ground_canopy", True),
            ("ground", "ground", True),
            ("ground", "soil_ground", True),
            ("ground", "ground_canopy", True),
            ("ground", "soil", False),
            ("ground", "canopy", False),
            ("ground", "soil_ground_canopy", True),
            ("canopy", "canopy", True),
            ("canopy", "ground_canopy", True),
            ("canopy", "ground", False),
            ("canopy", "soil", False),
            ("canopy", "soil_ground", False),
            ("canopy", "soil_ground_canopy", True),
            ("soil_ground", "soil", True),
            ("soil_ground", "ground", True),
            ("soil_ground", "soil_ground", True),
            ("soil_ground", "ground_canopy", True),
            ("soil_ground", "canopy", False),
            ("soil_ground", "soil_ground_canopy", True),
            ("ground_canopy", "ground", True),
            ("ground_canopy", "canopy", True),
            ("ground_canopy", "soil_ground", True),
            ("ground_canopy", "ground_canopy", True),
            ("ground_canopy", "soil", False),
            ("ground_canopy", "soil_ground_canopy", True),
            ("soil_ground_canopy", "soil", True),
            ("soil_ground_canopy", "ground", True),
            ("soil_ground_canopy", "canopy", True),
            ("soil_ground_canopy", "soil_ground", True),
            ("soil_ground_canopy", "ground_canopy", True),
            ("soil_ground_canopy", "soil_ground_canopy", True),
        ],
    )
    def test_match_vertical(
        self,
        cohort_occupancy,
        resource_occupancy,
        expected,
        constants_instance,
    ):
        """Test match_vertical correctly identifies overlapping vertical occupancy."""

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
        from virtual_ecosystem.models.animal.functional_group import FunctionalGroup

        # Setup grid
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)

        # Create functional group with given vertical occupancy
        group = FunctionalGroup(
            name="test",
            taxa="mammal",
            diet="herbivore",
            metabolic_type="endothermic",
            reproductive_environment="terrestrial",
            reproductive_type="iteroparous",
            development_type="direct",
            development_status="adult",
            offspring_functional_group="test",
            excretion_type="ureotelic",
            migration_type="none",
            vertical_occupancy=cohort_occupancy,
            birth_mass=1.0,
            adult_mass=10.0,
            constants=constants_instance,
        )

        # Create test cohort
        cohort = AnimalCohort(
            functional_group=group,
            mass=10.0,
            age=100.0,
            individuals=5,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )

        # Test match_vertical result

        result = cohort.match_vertical(VerticalOccupancy.parse(resource_occupancy))
        assert result is expected

    @pytest.mark.parametrize(
        "territory, cell_pool_map, expected",
        [
            # Single pool in one cell
            ([1], {1: ["above_metabolic"]}, 1),
            # Multiple pools in one cell
            ([1], {1: ["above_metabolic", "woody"]}, 2),
            # Pools in multiple cells
            ([1, 2], {1: ["above_metabolic"], 2: ["woody"]}, 2),
            # One cell has no pool
            ([1, 2], {1: ["above_metabolic"]}, 1),
            # No overlapping cells
            ([3], {1: ["above_metabolic"], 2: ["woody"]}, 0),
        ],
    )
    def test_get_litter_pools(
        self,
        territory,
        cell_pool_map,
        expected,
        functional_group_list_instance,
        constants_instance,
        litter_pools_dict_by_cell_instance,
    ):
        """Test get_litter_pools."""

        from virtual_ecosystem.core.grid import Grid
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Setup grid and functional group
        grid = Grid(grid_type="square", cell_nx=3, cell_ny=3)
        herbivore_group = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )

        cohort = AnimalCohort(
            functional_group=herbivore_group,
            mass=10.0,
            age=20.0,
            individuals=10,
            centroid_key=0,
            grid=grid,
            constants=constants_instance,
        )
        cohort.territory = territory

        # Extract only requested pools from the full fixture
        test_litter_pools = {
            cell_id: {
                pool_name: litter_pools_dict_by_cell_instance[cell_id][pool_name]
                for pool_name in pool_names
            }
            for cell_id, pool_names in cell_pool_map.items()
            if cell_id in litter_pools_dict_by_cell_instance
        }

        result = cohort.get_litter_pools(test_litter_pools)

        assert len(result) == expected

    @pytest.mark.parametrize(
        "C, N, P, initial_largest_mass, expected_largest_mass",
        [
            # Grows, still under adult mass
            (6.0, 1.0, 0.5, 5.0, 7.5),
            # Grows past adult mass, should cap
            (50.0, 10.0, 5.0, 20.0, "cap_to_adult"),
            # No growth, mass lower than previous largest
            (4.0, 0.5, 0.2, 10.0, 10.0),
        ],
    )
    def test_update_largest_mass(
        self,
        herbivore_cohort_instance,
        C,
        N,
        P,
        initial_largest_mass,
        expected_largest_mass,
    ):
        """Test update_largest_mass."""

        # Set up current mass via mass_cnp
        herbivore_cohort_instance.mass_cnp.C = C
        herbivore_cohort_instance.mass_cnp.N = N
        herbivore_cohort_instance.mass_cnp.P = P

        # Set initial largest_mass_achieved
        herbivore_cohort_instance.largest_mass_achieved = initial_largest_mass

        # Call update
        herbivore_cohort_instance.update_largest_mass()

        # Determine expected value
        if expected_largest_mass == "cap_to_adult":
            expected = herbivore_cohort_instance.functional_group.adult_mass
        else:
            expected = expected_largest_mass

        # Assertion
        assert herbivore_cohort_instance.largest_mass_achieved == expected

    def test_get_array_resources(self, mocker):
        """Test get_array_resources."""
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import (
            DietType,
            VerticalOccupancy,
        )

        cohort = mocker.Mock()
        cohort.territory = [0, 1, 2]
        cohort.functional_group.diet = DietType.FOLIAGE | DietType.SEEDS
        cohort.functional_group.vertical_occupancy = VerticalOccupancy.GROUND

        # Pool A: forageable
        pool_a = mocker.MagicMock()
        pool_a.is_forageable.return_value = True
        pool_a.__getitem__.side_effect = lambda cell_id: f"a_{cell_id}"

        # Pool B: not forageable
        pool_b = mocker.MagicMock()
        pool_b.is_forageable.return_value = False
        pool_b.__getitem__.side_effect = lambda cell_id: f"b_{cell_id}"

        result = AnimalCohort.get_array_resources(cohort, [pool_a, pool_b])

        pool_a.is_forageable.assert_called_once_with(
            diet=cohort.functional_group.diet,
            vertical_occupancy=cohort.functional_group.vertical_occupancy,
        )
        pool_b.is_forageable.assert_called_once_with(
            diet=cohort.functional_group.diet,
            vertical_occupancy=cohort.functional_group.vertical_occupancy,
        )

        assert result == ["a_0", "a_1", "a_2"]
        pool_a.__getitem__.assert_any_call(0)
        pool_a.__getitem__.assert_any_call(1)
        pool_a.__getitem__.assert_any_call(2)
        pool_b.__getitem__.assert_not_called()

    @pytest.mark.parametrize(
        "self_territory, other_territory, expected_cells, expected_cell_count",
        [
            pytest.param([0, 1, 2], [1, 2, 3], {1, 2}, 2, id="partial_overlap"),
            pytest.param([0, 1], [2, 3], set(), 0, id="no_overlap"),
        ],
    )
    def test_get_territory_intersection(
        self,
        herbivore_cohort_instance,
        predator_cohort_instance,
        self_territory,
        other_territory,
        expected_cells,
        expected_cell_count,
    ):
        """Test get_territory_intersection."""
        herbivore_cohort_instance.territory = self_territory
        predator_cohort_instance.territory = other_territory

        intersection_cells, intersection_area = (
            herbivore_cohort_instance.get_territory_intersection(
                predator_cohort_instance
            )
        )

        assert intersection_cells == expected_cells
        assert intersection_area == pytest.approx(
            expected_cell_count * herbivore_cohort_instance.grid.cell_area
        )

    @pytest.mark.parametrize(
        "self_territory, other_territory, expected_cell_ids",
        [
            pytest.param([0, 1, 2], [1, 2, 3], {1, 2}, id="partial_overlap"),
            pytest.param([0, 1], [2, 3], set(), id="no_overlap"),
        ],
    )
    def test_find_intersecting_carcass_pools(
        self,
        herbivore_cohort_instance,
        predator_cohort_instance,
        carcass_pools_by_cell_instance,
        self_territory,
        other_territory,
        expected_cell_ids,
    ):
        """Test find_intersecting_carcass_pools."""
        herbivore_cohort_instance.territory = self_territory
        predator_cohort_instance.territory = other_territory

        result = herbivore_cohort_instance.find_intersecting_carcass_pools(
            predator_cohort_instance, carcass_pools_by_cell_instance
        )

        expected = [
            pool
            for cell_id in expected_cell_ids
            for pool in carcass_pools_by_cell_instance[cell_id]
        ]
        assert result == expected
