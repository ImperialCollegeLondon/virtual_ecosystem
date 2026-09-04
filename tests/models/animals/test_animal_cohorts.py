"""Test module for animal_cohorts.py."""

import uuid
from math import exp

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
def canopy_cohort_instance(
    shared_datadir,
    animal_data_for_cohorts_instance,
    constants_instance,
):
    """Fixture for a canopy-only cohort (swallow, index 11)."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)
    return AnimalCohort(
        fg_list[11],
        0.1,
        1,
        10,
        1,
        animal_data_for_cohorts_instance.grid,
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
        "mass_consumed, unassimilated_mass, stoichiometric_waste, expected_waste",
        [
            # Normal cases
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                {"C": 20.0, "N": 2.0, "P": 0.2},
                {"C": 60.0, "N": 6.0, "P": 0.6},
            ),
            (
                {"C": 50.0, "N": 5.0, "P": 0.5},
                {"C": 20.0, "N": 2.0, "P": 0.2},
                {"C": 10.0, "N": 1.0, "P": 0.1},
                {"C": 30.0, "N": 3.0, "P": 0.3},
            ),
            # Only unassimilated waste, growth consumes all assimilated mass
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
            ),
            # Only stoichiometric waste, perfect assimilation
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 20.0, "N": 2.0, "P": 0.2},
                {"C": 20.0, "N": 2.0, "P": 0.2},
            ),
            # Edge cases
            (
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
            ),  # Zero consumption
            (
                {"C": 1e9, "N": 1e9, "P": 1e9},
                {"C": 4e8, "N": 4e8, "P": 4e8},
                {"C": 2e8, "N": 2e8, "P": 2e8},
                {"C": 6e8, "N": 6e8, "P": 6e8},
            ),  # Extremely high consumption
            (
                {"C": 1e-6, "N": 1e-6, "P": 1e-6},
                {"C": 4e-7, "N": 4e-7, "P": 4e-7},
                {"C": 2e-7, "N": 2e-7, "P": 2e-7},
                {"C": 6e-7, "N": 6e-7, "P": 6e-7},
            ),  # Minimum nonzero consumption
        ],
    )
    def test_eat(
        self,
        mocker,
        herbivore_cohort_instance,
        mass_consumed,
        unassimilated_mass,
        stoichiometric_waste,
        expected_waste,
        excrement_pools_by_cell_instance,
    ):
        """Test that `eat` combines both waste streams before defecating.

        `grow` and `defecate` are mocked to isolate the routing logic: the waste
        passed to `defecate` must be the sum of the unassimilated fraction supplied
        by the caller and the stoichiometric excess returned by `grow`.
        """

        # Mock grow to return a controlled stoichiometric excess
        mock_grow = mocker.patch.object(
            herbivore_cohort_instance, "grow", return_value=stoichiometric_waste
        )

        # Mock the defecate method
        mock_defecate = mocker.patch.object(herbivore_cohort_instance, "defecate")

        # Call eat method
        herbivore_cohort_instance.eat(
            mass_consumed, unassimilated_mass, excrement_pools_by_cell_instance
        )

        # Growth is applied to the assimilated mass only
        mock_grow.assert_called_once_with(mass_consumed)

        # Defecate receives the combined waste, not either stream alone
        mock_defecate.assert_called_once()
        call_pools, call_waste = mock_defecate.call_args.args
        assert call_pools is excrement_pools_by_cell_instance
        assert call_waste == pytest.approx(expected_waste)

    @pytest.mark.parametrize(
        "mass_consumed, unassimilated_mass, excrement_pools, expected_error_message",
        [
            # Missing required keys in mass_consumed
            (
                {"C": 100.0, "N": 10.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "mass_consumed must contain all required keys",
            ),
            (
                {"C": 100.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "mass_consumed must contain all required keys",
            ),
            (
                {"N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "mass_consumed must contain all required keys",
            ),
            # Missing required keys in unassimilated_mass
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0},
                ["mock_pool"],
                "unassimilated_mass must contain all required keys",
            ),
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"N": 4.0, "P": 0.4},
                ["mock_pool"],
                "unassimilated_mass must contain all required keys",
            ),
            # Negative values in mass_consumed
            (
                {"C": -100.0, "N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "Values in mass_consumed must be non-negative",
            ),
            (
                {"C": 100.0, "N": -10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "Values in mass_consumed must be non-negative",
            ),
            (
                {"C": 100.0, "N": 10.0, "P": -1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "Values in mass_consumed must be non-negative",
            ),
            # Negative values in unassimilated_mass
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": -40.0, "N": 4.0, "P": 0.4},
                ["mock_pool"],
                "Values in unassimilated_mass must be non-negative",
            ),
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": -0.4},
                ["mock_pool"],
                "Values in unassimilated_mass must be non-negative",
            ),
            # No excrement pools
            (
                {"C": 100.0, "N": 10.0, "P": 1.0},
                {"C": 40.0, "N": 4.0, "P": 0.4},
                [],
                "At least one excrement pool must be provided.",
            ),
        ],
    )
    def test_eat_errors(
        self,
        herbivore_cohort_instance,
        mass_consumed,
        unassimilated_mass,
        excrement_pools,
        expected_error_message,
    ):
        """Test that `eat` raises appropriate ValueErrors for invalid inputs."""
        with pytest.raises(ValueError, match=expected_error_message):
            herbivore_cohort_instance.eat(
                mass_consumed, unassimilated_mass, excrement_pools
            )

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

    def test_calculate_total_handling_time_for_herbivory(
        self, mocker, herbivore_cohort_instance
    ):
        """Test aggregation of handling times across plant resources."""
        import numpy as np

        from virtual_ecosystem.models.animal.array_resources import CellResource

        plant_list = []
        for i in range(3):
            plant_list.append(
                CellResource(
                    resource=object(),
                    available_elemental_masses=np.array([1.0, 0.0, 0.0], dtype=float),
                    consumed_total_mass=np.zeros(1, dtype=float),
                    vertical_occupancy=herbivore_cohort_instance.functional_group.vertical_occupancy,
                    lignin_proportion=0.0,
                    cell_id=i,
                )
            )

        alpha = 0.1

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

        expected_handling_time = 0.2 * (3 * 20.0)
        assert total_handling_time == pytest.approx(expected_handling_time, rel=1e-6)

    @pytest.mark.parametrize(
        "potential_biomass_consumed, total_handling_t, plant_biomass, scenario_id",
        [
            pytest.param(20.0, 40.4, 100.0, "low_alpha_high_mass"),
            pytest.param(30.0, 20.2, 200.0, "high_alpha_high_mass"),
        ],
    )
    def test_F_i_k(
        self,
        mocker,
        potential_biomass_consumed,
        total_handling_t,
        plant_biomass,
        scenario_id,
        herbivore_cohort_instance,
    ):
        """Test instantaneous consumption rate calculation."""
        from virtual_ecosystem.models.animal.protocols import Resource

        resource = mocker.MagicMock(spec=Resource, mass_current=plant_biomass)

        rate = herbivore_cohort_instance.F_i_k(
            resource, potential_biomass_consumed, total_handling_t
        )

        N = herbivore_cohort_instance.individuals
        expected = (
            N
            * (potential_biomass_consumed / (1.0 + total_handling_t))
            / (plant_biomass * 1000.0)  # kg -> g, matches F_i_k
        )

        assert rate == pytest.approx(expected, rel=1e-6), (
            f"Rate mismatch for scenario {scenario_id}"
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
        """Test calculation of potential number of prey consumed.

        The prey cohort's abundance ``n_prey`` (Madingley ``N_j,t``) is the value
        forwarded to ``k_i_j``; it is deliberately set different from the predator
        cohort's own ``individuals`` so a regression to the predator-count swap would
        fail this test.
        """
        alpha = 0.8
        n_prey = 1234.0
        theta_i_j = 0.7
        intersection_area = 5000.0
        mock_k_i_j = mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.k_i_j",
            return_value=15.0,
        )

        result = herbivore_cohort_instance.calculate_potential_prey_consumed(
            alpha, n_prey, theta_i_j, intersection_area
        )

        mock_k_i_j.assert_called_once_with(
            alpha,
            n_prey,
            intersection_area,
            theta_i_j,
        )
        assert result == 15.0, "Expected potential prey consumed not returned."

    @pytest.mark.parametrize(
        "cohort_specs, bin_densities, intersection_areas, expected",
        [
            pytest.param(
                [],
                {},
                {},
                0.0,
                id="empty_list_returns_zero",
            ),
            pytest.param(
                [(50.0,), (100.0,)],
                {5: 0.001, 6: 0.002},
                None,  # built from cohort ids in test body
                12.0,  # two prey, each H_i_j(2.0) * k_i_j(3.0) = 6.0
                id="two_prey_sums_handling_time",
            ),
        ],
    )
    def test_calculate_total_handling_time_for_predation(
        self,
        predator_cohort_instance,
        mocker,
        cohort_specs,
        bin_densities,
        intersection_areas,
        expected,
    ):
        """Test total handling time sums H_i_j * k_i_j correctly across prey list.

        Scaling functions and _mass_bin are mocked to isolate accumulation logic.
        intersection_areas is built from cohort ids in the test body when None.
        """
        animal_list = []
        bin_side_effects = []
        for i, (mass,) in enumerate(cohort_specs):
            prey = mocker.Mock()
            prey.mass_current = mass
            animal_list.append(prey)
            bin_side_effects.append(i + 5)

        if intersection_areas is None:
            intersection_areas = {
                id(prey): 5000.0 * (i + 1) for i, prey in enumerate(animal_list)
            }

        mocker.patch.object(
            predator_cohort_instance, "_mass_bin", side_effect=bin_side_effects
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.w_bar_i_j",
            return_value=0.5,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.alpha_i_j",
            return_value=0.8,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.H_i_j",
            return_value=2.0,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.k_i_j",
            return_value=3.0,
        )

        result = predator_cohort_instance.calculate_total_handling_time_for_predation(
            animal_list, 0.1, bin_densities, intersection_areas
        )

        assert result == pytest.approx(expected)

    def test_calculate_total_handling_time_for_predation_uses_precomputed_values(
        self,
        predator_cohort_instance,
        mocker,
    ):
        """Test that get_territory_intersection is never called.

        Verifies the redundant recomputation has been eliminated in favour of the
        pre-computed bin_densities and intersection_areas dicts.
        """
        prey = mocker.Mock()
        prey.mass_current = 50.0
        prey.individuals = 10

        mock_territory = mocker.patch.object(
            predator_cohort_instance, "get_territory_intersection"
        )
        mocker.patch.object(predator_cohort_instance, "_mass_bin", return_value=5)
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.w_bar_i_j",
            return_value=0.5,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.alpha_i_j",
            return_value=0.8,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.H_i_j",
            return_value=2.0,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.k_i_j",
            return_value=3.0,
        )

        predator_cohort_instance.calculate_total_handling_time_for_predation(
            [prey], 0.1, {5: 0.001}, {id(prey): 5000.0}
        )

        mock_territory.assert_not_called()

    def test_calculate_total_handling_time_for_predation_missing_bin_defaults_to_zero(
        self,
        predator_cohort_instance,
        mocker,
    ):
        """Test that a prey bin absent from bin_densities passes 0.0 to k_i_j."""
        prey = mocker.Mock()
        prey.mass_current = 50.0

        mocker.patch.object(predator_cohort_instance, "_mass_bin", return_value=99)
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.w_bar_i_j",
            return_value=0.5,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.alpha_i_j",
            return_value=0.8,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.H_i_j",
            return_value=2.0,
        )
        mock_k = mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.k_i_j",
            return_value=0.0,
        )

        predator_cohort_instance.calculate_total_handling_time_for_predation(
            [prey], 0.1, {}, {id(prey): 5000.0}
        )

        assert mock_k.call_args[0][3] == pytest.approx(0.0)

    @pytest.mark.parametrize(
        "n_target, expected",
        [
            pytest.param(0, 0.0, id="zero_individuals_returns_zero"),
            pytest.param(10, None, id="normal_case_uses_functional_response"),
        ],
    )
    def test_F_i_j_individual(
        self,
        predator_cohort_instance,
        mocker,
        n_target,
        expected,
    ):
        """Test instantaneous predation rate on a target cohort.

        Zero-individual prey returns 0.0 immediately. For the normal case the
        return value is derived from mocked sub-methods and verified via the
        Holling type II formula: N_i * (k / (1 + H)) * (1 / N_target).
        total_handling_time is passed directly as a pre-computed value.
        """
        target = mocker.Mock()
        target.mass_current = 50.0
        target.individuals = n_target
        bin_densities = {5: 0.001}

        mocker.patch.object(predator_cohort_instance, "_mass_bin", return_value=5)
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.w_bar_i_j",
            return_value=0.5,
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_predation_search_rate",
            return_value=0.8,
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_potential_prey_consumed",
            return_value=4.0,
        )

        result = predator_cohort_instance.F_i_j_individual(
            target, 5000.0, 0.1, bin_densities, 1.0
        )

        if expected is not None:
            assert result == pytest.approx(expected)
        else:
            # N_i=10, k=4.0, H=1.0, N_target=10 → 10 * (4/(1+1)) * (1/10) = 2.0
            assert result == pytest.approx(2.0)

    def test_F_i_j_individual_does_not_draw_theta_opt(
        self,
        predator_cohort_instance,
        mocker,
    ):
        """Test that calculate_theta_opt_i is never called.

        theta_opt is drawn once per encounter in delta_mass_predation and passed in.
        """
        target = mocker.Mock()
        target.mass_current = 50.0
        target.individuals = 10

        mock_draw = mocker.patch.object(
            predator_cohort_instance, "calculate_theta_opt_i"
        )
        mocker.patch.object(predator_cohort_instance, "_mass_bin", return_value=5)
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.sf.w_bar_i_j",
            return_value=0.5,
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_predation_search_rate",
            return_value=0.8,
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_potential_prey_consumed",
            return_value=4.0,
        )

        predator_cohort_instance.F_i_j_individual(target, 5000.0, 0.1, {5: 0.001}, 1.0)

        mock_draw.assert_not_called()

    @pytest.mark.parametrize(
        "F_value, mass_current, individuals, expected_behavior",
        [
            pytest.param(0.05, 10.0, 5, "formula", id="normal_case"),
            pytest.param(0.0, 10.0, 5, 0.0, id="zero_F_consumes_nothing"),
            pytest.param(1e6, 10.0, 5, "max", id="high_F_consumes_all"),
            pytest.param(0.05, 10.0, 0, 0.0, id="zero_individuals"),
            pytest.param(0.05, 0.0, 5, 0.0, id="zero_mass"),
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
        """Test consumed mass formula across F values, mass, and individual counts.

        total_handling_time is passed directly as a pre-computed value.
        """
        from math import exp, isclose

        from numpy import timedelta64

        prey = mocker.Mock()
        prey.mass_current = mass_current
        prey.individuals = individuals

        adjusted_dt = timedelta64(8, "D")
        dt_days = float(adjusted_dt / timedelta64(1, "D"))
        bin_densities = {5: 0.001}

        mocker.patch.object(
            predator_cohort_instance, "F_i_j_individual", return_value=F_value
        )

        result = predator_cohort_instance.calculate_consumed_mass_predation(
            prey, adjusted_dt, 5000.0, 0.1, bin_densities, 1.0
        )

        if expected_behavior == "formula":
            expected = mass_current * individuals * (1.0 - exp(-F_value * dt_days))
            assert isclose(result, expected, rel_tol=1e-9)
        elif expected_behavior == "max":
            assert isclose(result, mass_current * individuals, rel_tol=1e-3)
        else:
            assert result == pytest.approx(expected_behavior)

    def test_calculate_consumed_mass_predation_passes_through_to_F_i_j(
        self,
        predator_cohort_instance,
        mocker,
    ):
        """Test that arguments are forwarded correctly to F_i_j_individual."""
        from numpy import timedelta64

        prey = mocker.Mock()
        prey.mass_current = 10.0
        prey.individuals = 5

        bin_densities = {5: 0.001}

        mock_F = mocker.patch.object(
            predator_cohort_instance, "F_i_j_individual", return_value=0.05
        )

        predator_cohort_instance.calculate_consumed_mass_predation(
            prey,
            timedelta64(8, "D"),
            5000.0,
            0.1,
            bin_densities,
            1.0,
        )

        mock_F.assert_called_once_with(prey, 5000.0, 0.1, bin_densities, 1.0)

    @pytest.mark.parametrize(
        "animal_list_spec, carcass_pools_spec, should_raise, error_match, "
        "mock_consumed_mass, mock_actual_cnp, expected_gain, expected_unassimilated",
        [
            pytest.param(
                [],
                {1: [True]},
                False,
                None,
                None,
                None,
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                id="empty_list_returns_zero",
            ),
            pytest.param(
                [True],
                {1: [True]},
                False,
                None,
                10.0,
                {"C": 8.0, "N": 1.5, "P": 0.8},
                {"C": 4.0, "N": 0.75, "P": 0.4},
                {"C": 4.0, "N": 0.75, "P": 0.4},
                id="single_prey_accumulates_cnp",
            ),
            pytest.param(
                [True, True],
                {1: [True]},
                False,
                None,
                5.0,
                {"C": 4.0, "N": 0.8, "P": 0.4},
                {"C": 4.0, "N": 0.8, "P": 0.4},
                {"C": 4.0, "N": 0.8, "P": 0.4},
                id="two_prey_cnp_summed",
            ),
            pytest.param(
                None,
                {1: [True]},
                True,
                "animal_list cannot be None",
                None,
                None,
                None,
                None,
                id="none_animal_list_raises",
            ),
            pytest.param(
                [True],
                None,
                True,
                "carcass_pools cannot be None",
                None,
                None,
                None,
                None,
                id="none_carcass_pools_raises",
            ),
            pytest.param(
                [True],
                {1: [True]},
                True,
                "calculate_consumed_mass_predation.*returned None",
                None,
                {"C": 8.0, "N": 1.5, "P": 0.8},
                None,
                None,
                id="none_consumed_mass_raises",
            ),
            pytest.param(
                [True],
                {1: [True]},
                True,
                "get_eaten.*returned None",
                10.0,
                None,
                None,
                None,
                id="none_get_eaten_raises",
            ),
        ],
    )
    def test_delta_mass_predation(
        self,
        mocker,
        predator_cohort_instance,
        animal_list_spec,
        carcass_pools_spec,
        should_raise,
        error_match,
        mock_consumed_mass,
        mock_actual_cnp,
        expected_gain,
        expected_unassimilated,
    ):
        """Test delta_mass_predation accumulation, empty list, and error cases.

        calculate_consumed_mass_predation returns a float (kg), get_eaten returns
        the CNP dict. Both are mocked here to isolate orchestration logic.
        Conversion efficiency is pinned to 0.5 so that the expected assimilated and
        unassimilated fractions are fixed values rather than being derived from the
        implementation's own arithmetic.
        """
        from numpy import timedelta64

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import CarcassPool

        animal_list = (
            [mocker.MagicMock(spec=AnimalCohort) for _ in animal_list_spec]
            if animal_list_spec is not None
            else None
        )
        if animal_list:
            for prey in animal_list:
                prey.id = uuid.uuid4()
                mocker.patch.object(prey, "get_eaten", return_value=mock_actual_cnp)

        carcass_pools = (
            {
                k: [mocker.MagicMock(spec=CarcassPool) for _ in v]
                for k, v in carcass_pools_spec.items()
            }
            if carcass_pools_spec is not None
            else None
        )

        mocker.patch.object(
            predator_cohort_instance.functional_group,
            "conversion_efficiency",
            0.5,
        )
        mocker.patch.object(
            predator_cohort_instance, "calculate_theta_opt_i", return_value=0.1
        )
        mocker.patch.object(
            predator_cohort_instance,
            "get_territory_intersection",
            return_value=(set(), 5000.0),
        )
        mocker.patch.object(
            predator_cohort_instance,
            "_build_prey_bin_densities",
            return_value={5: 0.001},
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_total_handling_time_for_predation",
            return_value=1.0,
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_consumed_mass_predation",
            return_value=mock_consumed_mass,
        )

        if should_raise:
            with pytest.raises(ValueError, match=error_match):
                predator_cohort_instance.delta_mass_predation(
                    animal_list, carcass_pools, timedelta64(10, "D")
                )
        else:
            gain, unassimilated = predator_cohort_instance.delta_mass_predation(
                animal_list, carcass_pools, timedelta64(10, "D")
            )

            assert gain == pytest.approx(expected_gain)
            assert unassimilated == pytest.approx(expected_unassimilated)

            # The two fractions must together account for all ingested mass.
            n_prey = len(animal_list)
            ingested = (
                {
                    element: mock_actual_cnp[element] * n_prey
                    for element in ("C", "N", "P")
                }
                if mock_actual_cnp is not None
                else {"C": 0.0, "N": 0.0, "P": 0.0}
            )
            for element in ("C", "N", "P"):
                assert gain[element] + unassimilated[element] == pytest.approx(
                    ingested[element]
                )

    def test_delta_mass_predation_precomputes_once(
        self,
        mocker,
        predator_cohort_instance,
    ):
        """Test that theta_opt, intersection_areas, and bin_densities compute once."""
        from numpy import timedelta64

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import CarcassPool

        prey_a = mocker.MagicMock(spec=AnimalCohort)
        prey_b = mocker.MagicMock(spec=AnimalCohort)
        for prey in (prey_a, prey_b):
            prey.id = uuid.uuid4()
            mocker.patch.object(
                prey, "get_eaten", return_value={"C": 1.0, "N": 0.1, "P": 0.01}
            )

        carcass_pools = {1: [mocker.MagicMock(spec=CarcassPool)]}

        mock_theta = mocker.patch.object(
            predator_cohort_instance, "calculate_theta_opt_i", return_value=0.1
        )
        mock_intersection = mocker.patch.object(
            predator_cohort_instance,
            "get_territory_intersection",
            return_value=(set(), 5000.0),
        )
        mock_bin_densities = mocker.patch.object(
            predator_cohort_instance,
            "_build_prey_bin_densities",
            return_value={5: 0.001},
        )
        mock_handling = mocker.patch.object(
            predator_cohort_instance,
            "calculate_total_handling_time_for_predation",
            return_value=1.0,
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_consumed_mass_predation",
            return_value=5.0,
        )

        predator_cohort_instance.delta_mass_predation(
            [prey_a, prey_b], carcass_pools, timedelta64(10, "D")
        )

        mock_theta.assert_called_once()
        assert mock_intersection.call_count == 2
        mock_bin_densities.assert_called_once()
        mock_handling.assert_called_once()

    def test_delta_mass_predation_skips_zero_intersection(
        self,
        mocker,
        predator_cohort_instance,
    ):
        """Test that prey with zero territory intersection are skipped.

        calculate_consumed_mass_predation must not be called when intersection
        area is 0.0. calculate_total_handling_time_for_predation is still called
        once before the loop since it does not depend on individual prey areas.
        """
        from numpy import timedelta64

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.decay import CarcassPool

        prey = mocker.MagicMock(spec=AnimalCohort)
        prey.id = uuid.uuid4()

        mocker.patch.object(
            predator_cohort_instance, "calculate_theta_opt_i", return_value=0.1
        )
        mocker.patch.object(
            predator_cohort_instance,
            "get_territory_intersection",
            return_value=(set(), 0.0),
        )
        mocker.patch.object(
            predator_cohort_instance, "_build_prey_bin_densities", return_value={}
        )
        mocker.patch.object(
            predator_cohort_instance,
            "calculate_total_handling_time_for_predation",
            return_value=1.0,
        )
        mock_consume = mocker.patch.object(
            predator_cohort_instance, "calculate_consumed_mass_predation"
        )

        predator_cohort_instance.delta_mass_predation(
            [prey],
            {1: [mocker.MagicMock(spec=CarcassPool)]},
            timedelta64(10, "D"),
        )

        mock_consume.assert_not_called()

    @pytest.mark.parametrize(
        "gain, litter, lignin, expected_gain, expected_unassimilated, "
        "expect_waste_call, expect_error, test_id",
        [
            (
                {"C": 10.0, "N": 5.0, "P": 2.0},
                {"C": 3.0, "N": 1.0, "P": 0.5},
                0.1,
                {"C": 10.0, "N": 5.0, "P": 2.0},
                {"C": 10.0, "N": 5.0, "P": 2.0},
                2,
                None,
                "standard",
            ),
            (
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                0.0,
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                2,
                None,
                "no_gain",
            ),
            (
                {"C": 4.0, "N": 2.0, "P": 1.0},
                {"C": 1.0, "N": 0.5, "P": 0.25},
                0.2,
                None,
                None,
                0,
                KeyError,
                "no_waste_pool",
            ),
            (
                {"C": 5.0, "N": 2.5, "P": 1.0},
                {},
                0.0,
                {"C": 5.0, "N": 2.5, "P": 1.0},
                {"C": 5.0, "N": 2.5, "P": 1.0},
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
        lignin,
        expected_gain,
        expected_unassimilated,
        expect_waste_call,
        expect_error,
        test_id,
    ):
        """Test `forage_resource_list` with different gain/litter scenarios.

        Conversion efficiency is pinned to 0.5, so with two identical resources the
        assimilated and unassimilated fractions each equal the single-resource gain.
        Expected values are given as literals rather than derived from the
        implementation's own arithmetic.
        """
        herbivore = herbivore_cohort_instance
        herbivore.functional_group.conversion_efficiency = 0.5

        # Mock cohort-level precomputations so the test focuses on gain/waste logic
        mocker.patch.object(herbivore, "calculate_alpha", return_value=0.5)
        mocker.patch.object(
            herbivore, "calculate_total_handling_time_for_herbivory", return_value=0.1
        )
        mocker.patch.object(herbivore, "F_i_k", return_value=0.1)

        # Create two mock resources
        resource1 = mocker.Mock()
        resource1.mass_current = 10.0
        resource1.cell_id = 1
        resource1.get_eaten.return_value = (gain, litter, lignin)
        resource2 = mocker.Mock()
        resource2.mass_current = 5.0
        resource2.cell_id = 2
        resource2.get_eaten.return_value = (gain, litter, lignin)

        # Waste pool, with conditional presence based on test
        if test_id == "no_waste_pool":
            waste_pools = {1: mocker.Mock()}  # Only one key, missing key 2
        else:
            waste = mocker.Mock()
            waste_pools = {1: waste, 2: waste}

        if expect_error:
            with pytest.raises(expect_error):
                herbivore.forage_resource_list(
                    resources=[resource1, resource2],
                    adjusted_dt=timedelta64(10, "D"),
                    herbivory_waste_pools=waste_pools,
                    resource_kind="plant_resource",
                )
        else:
            result_gain, result_unassimilated = herbivore.forage_resource_list(
                resources=[resource1, resource2],
                adjusted_dt=timedelta64(10, "D"),
                herbivory_waste_pools=waste_pools,
                resource_kind="plant_resource",
            )

            assert result_gain == pytest.approx(expected_gain)
            assert result_unassimilated == pytest.approx(expected_unassimilated)

            # The two fractions must together account for all ingested mass across
            # both resources.
            for element in ("C", "N", "P"):
                assert result_gain[element] + result_unassimilated[
                    element
                ] == pytest.approx(gain[element] * 2)

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
            resource_kind="bacteria_pool",
        )
        assert result == {"C": 10, "N": 11, "P": 12}

    @pytest.mark.parametrize(
        "cohort_instance, diet_string, plant_list, animal_list, soil_fungi_list,"
        "pom_list, bacteria_list, expected_nutrient_gain, expected_unassimilated,"
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
                {"C": 60.0, "N": 30.0, "P": 10.0},
                {"C": 20.0, "N": 10.0, "P": 5.0},
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
                {"C": 120.0, "N": 60.0, "P": 20.0},
                {"C": 40.0, "N": 20.0, "P": 10.0},
                "delta_mass_predation",
            ),
        ],
        ids=["herbivore", "carnivore"],
    )
    def test_forage_cohort(
        self,
        mocker,
        request,
        cohort_instance,
        diet_string,
        plant_list,
        animal_list,
        soil_fungi_list,
        pom_list,
        bacteria_list,
        expected_nutrient_gain,
        expected_unassimilated,
        delta_mass_mock,
        array_plant_list_instance,
        animal_list_instance,
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

        # Herbivory waste pools: keyed by cell_id for plant-like resources.
        herbivory_waste_pools = {
            plant.cell_id: herbivory_waste_pool_instance
            for plant in array_plant_list_instance
        }

        mock_delta_mass = mocker.patch.object(
            cohort,
            delta_mass_mock,
            return_value=(expected_nutrient_gain, expected_unassimilated),
        )

        # Mock eat to capture the accumulated totals without triggering growth.
        mock_eat = mocker.patch.object(cohort, "eat")

        empty_list = []
        dt = timedelta64(30, "D")

        cohort.forage_cohort(
            array_resource_list=plant_list,
            animal_list=animal_list,
            soil_fungi_list=soil_fungi_list,
            pom_list=pom_list,
            bacteria_list=bacteria_list,
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

        # Both accumulated streams must reach eat, in order.
        mock_eat.assert_called_once()
        eat_gain, eat_unassimilated, eat_pools = mock_eat.call_args.args
        assert eat_gain == pytest.approx(expected_nutrient_gain)
        assert eat_unassimilated == pytest.approx(expected_unassimilated)
        assert eat_pools == [excrement_pool_instance]

        if diet_string == "foliage_fruit":
            assert kwargs["plant_list"] == array_plant_list_instance
            assert kwargs["herbivory_waste_pools"] == herbivory_waste_pools
            assert kwargs["adjusted_dt"] > 0

        elif diet_string == "vertebrates_invertebrates_carcasses":
            assert kwargs["animal_list"] == animal_list_instance
            assert kwargs["carcass_pools"] == carcass_pools_by_cell_instance
            assert kwargs["adjusted_dt"] > 0

        else:
            assert False, f"Unhandled diet_string: {diet_string}"

    def test_forage_cohort_earthworm_multisoil(
        self,
        mocker,
        array_litter_list_instance,
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
        expected_gain = {"C": 1.0, "N": 0.5, "P": 0.1}
        expected_unassimilated = {"C": 0.4, "N": 0.2, "P": 0.04}
        expected = (expected_gain, expected_unassimilated)
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
        mock_eat = mocker.patch.object(cohort, "eat")

        cohort.forage_cohort(
            array_resource_list=array_litter_list_instance,
            animal_list=[],
            soil_fungi_list=soil_fungi_list_instance,
            pom_list=pom_list_instance,
            bacteria_list=bacteria_list_instance,
            excrement_pools=[excrement_pool_instance],
            carcass_pool_map=carcass_pools_by_cell_instance,
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools={},
            dt=timedelta64(30, "D"),
        )

        # Each relevant path should be called exactly once with correct args.
        m_det.assert_called_once()
        m_fungi.assert_called_once()
        m_pom.assert_called_once()
        m_bact.assert_called_once()

        assert m_det.call_args.kwargs["litter_pools"] == array_litter_list_instance
        assert m_fungi.call_args.kwargs["soil_fungi_list"] == soil_fungi_list_instance
        assert m_pom.call_args.kwargs["pom_list"] == pom_list_instance
        assert m_bact.call_args.kwargs["bacteria_list"] == bacteria_list_instance

        # Both streams accumulate across all four foraging paths.
        mock_eat.assert_called_once()
        eat_gain, eat_unassimilated, _ = mock_eat.call_args.args
        for element in ("C", "N", "P"):
            assert eat_gain[element] == pytest.approx(expected_gain[element] * 4)
            assert eat_unassimilated[element] == pytest.approx(
                expected_unassimilated[element] * 4
            )

        # Basic sanity: adjusted_dt is numeric for each call.
        for m in (m_det, m_fungi, m_pom, m_bact):
            assert isinstance(m.call_args.kwargs["adjusted_dt"], timedelta64)

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
            array_resource_list=[],
            animal_list=[],
            soil_fungi_list=[],
            pom_list=[],
            bacteria_list=[],
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
            array_resource_list=[],
            animal_list=[],
            soil_fungi_list=[],
            pom_list=[],
            bacteria_list=[],
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
        "distance_in_cell_sides, expected_probability",
        [
            pytest.param(0.5, 0.5, id="half_a_cell"),
            pytest.param(1.0, 1.0, id="exactly_one_cell"),
            pytest.param(2.5, 1.0, id="cap_at_1"),
            pytest.param(0.0, 0.0, id="zero_distance"),
        ],
    )
    def test_migrate_juvenile_probability(
        self,
        mocker,
        distance_in_cell_sides,
        expected_probability,
        herbivore_cohort_instance,
    ):
        """Test the calculation of juvenile migration probability.

        The probability is the proportion of a cell side the cohort can clear in one
        timestep, clamped at one.
        """
        from math import sqrt

        cohort = herbivore_cohort_instance
        grid_side = sqrt(cohort.grid.cell_area)

        mocker.patch.object(
            cohort,
            "get_dispersal_distance",
            return_value=distance_in_cell_sides * grid_side,
        )

        probability_of_dispersal = cohort.migrate_juvenile_probability(dt_days=30.0)

        assert probability_of_dispersal == pytest.approx(expected_probability)
        cohort.get_dispersal_distance.assert_called_once_with(30.0)

    @pytest.mark.parametrize(
        "is_mature, mock_dead, pop_size, expected_survivors",
        [
            pytest.param(True, 12, 100, 88, id="mature_all_mortalities"),
            pytest.param(False, 3, 100, 97, id="immature_no_senescence"),
            pytest.param(False, 0, 1, 1, id="single_large_animal_no_death"),
            pytest.param(False, 1, 1, 0, id="single_large_animal_one_death"),
        ],
    )
    def test_inflict_non_predation_mortality(
        self,
        mocker,
        is_mature,
        mock_dead,
        pop_size,
        expected_survivors,
        predator_cohort_instance,
        carcass_pool_instance,
    ):
        """Test that non-predation mortality removes the correct number of individuals.

        ``binomial`` is mocked to return a fixed number of deaths, decoupling the
        test from the stochastic draw and from the specific mortality rate values.
        The ``single_large_animal`` cases are the primary regression: the old
        ``ceil`` implementation would guarantee at least one death per timestep
        regardless of how low the mortality rate was.
        """
        cohort = predator_cohort_instance
        cohort.individuals = pop_size
        cohort.is_mature = is_mature

        mocker.patch.object(
            type(cohort),
            "mass_current",
            new_callable=mocker.PropertyMock,
            return_value=600,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.background_mortality",
            return_value=0.001,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.senescence_mortality",
            return_value=0.003,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.scaling_functions.starvation_mortality",
            return_value=0.001,
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.binomial",
            return_value=mock_dead,
        )

        cohort.inflict_non_predation_mortality(30, [carcass_pool_instance])

        assert cohort.individuals == expected_survivors, (
            f"Expected {expected_survivors} survivors, got {cohort.individuals}."
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
            lignin_proportion=None,
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
        herbivory_waste = {cell_id: HerbivoryWaste() for cell_id in pool_map.keys()}

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

    @pytest.mark.parametrize(
        "predator_mass, prey_mass, theta_opt, expected_bin",
        [
            pytest.param(
                100.0,
                100.0 * exp(0.1),
                0.1,
                6,
                id="prey_at_optimal_ratio_gives_offset_bin",
            ),
            pytest.param(
                100.0,
                100.0 * exp(0.1 + 0.35),
                0.1,
                7,
                id="prey_one_half_sigma_above_optimal",
            ),
            pytest.param(
                100.0,
                100.0 * exp(0.1 - 0.35),
                0.1,
                5,
                id="prey_one_half_sigma_below_optimal",
            ),
            pytest.param(
                100.0,
                100.0 * exp(0.1 + 0.70),
                0.1,
                8,
                id="prey_two_half_sigma_steps_above_optimal",
            ),
            pytest.param(
                100.0,
                100.0 * exp(0.1 - 0.70),
                0.1,
                4,
                id="prey_two_half_sigma_steps_below_optimal",
            ),
            pytest.param(
                100.0,
                100.0 * exp(0.0),
                0.0,
                6,
                id="zero_theta_opt_equal_mass_gives_offset_bin",
            ),
        ],
    )
    def test_mass_bin_expected_values(
        self,
        predator_cohort_instance,
        predator_mass,
        prey_mass,
        theta_opt,
        expected_bin,
    ):
        """Test _mass_bin returns the correct integer bin index for known inputs.

        Expected values derive from Eq. 39 of Harfoot et al. (2014) with default
        constants sigma_opt_pred_prey=0.7 and N_sigma_opt_pred_prey=3.0, giving
        bin = round((log(prey/pred) - theta_opt) / 0.35 + 6). Prey placed at
        exactly the optimal ratio produces the offset bin (6); each half-sigma
        step (0.35 in log-mass space) shifts the bin by one.
        """

        from virtual_ecosystem.models.animal.cnp import CNP

        proportions = predator_cohort_instance.cnp_proportions
        predator_cohort_instance.mass_cnp = CNP(
            C=predator_mass * proportions["C"],
            N=predator_mass * proportions["N"],
            P=predator_mass * proportions["P"],
        )

        result = predator_cohort_instance._mass_bin(prey_mass, theta_opt)

        assert result == expected_bin

    def test_mass_bin_raises_on_zero_predator_mass(self, predator_cohort_instance):
        """Test that zero predator mass_current raises ValueError."""
        from virtual_ecosystem.models.animal.cnp import CNP

        predator_cohort_instance.mass_cnp = CNP(C=0.0, N=0.0, P=0.0)

        with pytest.raises(ValueError, match="Predator mass_current must be positive"):
            predator_cohort_instance._mass_bin(100.0, 0.1)

    def test_mass_bin_raises_on_zero_prey_mass(self, predator_cohort_instance):
        """Test that zero prey_mass raises ValueError."""
        with pytest.raises(ValueError, match="prey_mass must be positive"):
            predator_cohort_instance._mass_bin(0.0, 0.1)

    def test_mass_bin_raises_on_negative_prey_mass(self, predator_cohort_instance):
        """Test that negative prey_mass raises ValueError."""
        with pytest.raises(ValueError, match="prey_mass must be positive"):
            predator_cohort_instance._mass_bin(-50.0, 0.1)

    def test_mass_bin_depends_on_ratio_not_absolute_mass(
        self, predator_cohort_instance
    ):
        """Test that bin index depends on prey/predator ratio, not absolute masses.

        A predator of 10 kg and prey of 10*exp(0.1) kg should produce the same
        bin as predator 100 kg and prey 100*exp(0.1) kg, since the log ratio is
        identical in both cases.
        """
        from virtual_ecosystem.models.animal.cnp import CNP

        proportions = predator_cohort_instance.cnp_proportions

        predator_cohort_instance.mass_cnp = CNP(
            C=10.0 * proportions["C"],
            N=10.0 * proportions["N"],
            P=10.0 * proportions["P"],
        )
        bin_small = predator_cohort_instance._mass_bin(10.0 * exp(0.1), 0.1)

        predator_cohort_instance.mass_cnp = CNP(
            C=100.0 * proportions["C"],
            N=100.0 * proportions["N"],
            P=100.0 * proportions["P"],
        )
        bin_large = predator_cohort_instance._mass_bin(100.0 * exp(0.1), 0.1)

        assert bin_small == bin_large

    def test_build_prey_bin_densities_empty_list(self, predator_cohort_instance):
        """Test that an empty animal_list returns an empty dict."""
        result = predator_cohort_instance._build_prey_bin_densities([], 0.1)

        assert result == {}

    def test_build_prey_bin_densities_single_cohort(
        self, predator_cohort_instance, mocker
    ):
        """Test that a single cohort produces one bin entry with correct density.

        Density is individuals / cell_area_ha (native individuals/ha). With
        cell_area=10000 m^2 (1 ha) and individuals=10, expected density is 10.0.
        """
        prey = mocker.Mock()
        prey.mass_current = 50.0
        prey.individuals = 10

        mocker.patch.object(predator_cohort_instance, "_mass_bin", return_value=5)

        result = predator_cohort_instance._build_prey_bin_densities([prey], 0.1)

        cell_area_ha = predator_cohort_instance.grid.cell_area / 10000.0
        assert result == {5: pytest.approx(10 / cell_area_ha)}

    def test_build_prey_bin_densities_two_cohorts_different_bins(
        self, predator_cohort_instance, mocker
    ):
        """Test that cohorts in different bins produce separate entries."""
        prey_a = mocker.Mock()
        prey_a.mass_current = 50.0
        prey_a.individuals = 10

        prey_b = mocker.Mock()
        prey_b.mass_current = 500.0
        prey_b.individuals = 20

        mocker.patch.object(
            predator_cohort_instance,
            "_mass_bin",
            side_effect=[5, 7],
        )

        result = predator_cohort_instance._build_prey_bin_densities(
            [prey_a, prey_b], 0.1
        )

        cell_area_ha = predator_cohort_instance.grid.cell_area / 10000.0
        assert result == {
            5: pytest.approx(10 / cell_area_ha),
            7: pytest.approx(20 / cell_area_ha),
        }

    def test_build_prey_bin_densities_two_cohorts_same_bin(
        self, predator_cohort_instance, mocker
    ):
        """Test that cohorts in the same bin have their densities summed."""
        prey_a = mocker.Mock()
        prey_a.mass_current = 50.0
        prey_a.individuals = 10

        prey_b = mocker.Mock()
        prey_b.mass_current = 55.0
        prey_b.individuals = 30

        mocker.patch.object(
            predator_cohort_instance,
            "_mass_bin",
            return_value=5,
        )

        result = predator_cohort_instance._build_prey_bin_densities(
            [prey_a, prey_b], 0.1
        )

        cell_area_ha = predator_cohort_instance.grid.cell_area / 10000.0
        assert result == {5: pytest.approx(40 / cell_area_ha)}

    def test_build_prey_bin_densities_calls_mass_bin_once_per_cohort(
        self, predator_cohort_instance, mocker
    ):
        """Test that _mass_bin is called exactly once per cohort."""
        prey_a = mocker.Mock()
        prey_a.mass_current = 50.0
        prey_a.individuals = 10

        prey_b = mocker.Mock()
        prey_b.mass_current = 200.0
        prey_b.individuals = 5

        mock_bin = mocker.patch.object(
            predator_cohort_instance,
            "_mass_bin",
            side_effect=[5, 6],
        )

        predator_cohort_instance._build_prey_bin_densities([prey_a, prey_b], 0.1)

        assert mock_bin.call_count == 2
        mock_bin.assert_any_call(50.0, 0.1)
        mock_bin.assert_any_call(200.0, 0.1)

    @pytest.mark.parametrize(
        "cohort_type, temperature, diurnal_temp_range, annual_mean_temp,"
        " annual_temp_sd, expected_sigma, check_type",
        [
            pytest.param(
                "herbivore",
                31.0,
                4.0,
                20.0,
                5.0,
                1.0,
                "equal",
                id="endotherm_always_1",
            ),
            pytest.param(
                "ectotherm",
                31.0,
                4.0,
                20.0,
                5.0,
                1.0,
                "equal",
                id="ectotherm_fully_within_window",
            ),
            pytest.param(
                "ectotherm",
                10.0,
                4.0,
                20.0,
                5.0,
                0.0,
                "equal",
                id="ectotherm_always_too_cold",
            ),
            pytest.param(
                "ectotherm",
                30.0,
                10.0,
                20.0,
                5.0,
                None,
                "between",
                id="ectotherm_partial_overlap",
            ),
            # CSV override path — same climate inputs as ectotherm_fully_within_window
            # but thermophilic_lizard has t_min_crit=30 so temp=31 is only partially
            # within window, giving a different result than the toy parameter path
            pytest.param(
                "thermophilic_lizard",
                31.0,
                4.0,
                20.0,
                5.0,
                0.6666666666666667,
                "equal",
                id="csv_override_partial_window",
            ),
        ],
    )
    def test_update_activity_window(
        self,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        thermophilic_lizard_cohort_instance,
        cohort_type,
        temperature,
        diurnal_temp_range,
        annual_mean_temp,
        annual_temp_sd,
        expected_sigma,
        check_type,
    ):
        """Test that update_activity_window sets sigma_f_t correctly."""
        cohort = {
            "herbivore": herbivore_cohort_instance,
            "ectotherm": ectotherm_cohort_instance,
            "thermophilic_lizard": thermophilic_lizard_cohort_instance,
        }[cohort_type]

        cohort.update_activity_window(
            temperature=temperature,
            diurnal_temp_range=diurnal_temp_range,
            annual_mean_temp=annual_mean_temp,
            annual_temp_sd=annual_temp_sd,
        )

        if check_type == "equal":
            assert cohort.sigma_f_t == pytest.approx(expected_sigma)
        else:
            assert 0.0 < cohort.sigma_f_t < 1.0

    @pytest.mark.parametrize(
        "temperature, diurnal_temp_range, annual_mean_temp, annual_temp_sd, t_opt,"
        "t_max_crit, t_min_crit",
        [
            pytest.param(
                25.0,
                10.0,
                25.0,
                5.0,
                None,
                None,
                None,
                id="typical_derived_tolerance",
            ),
            pytest.param(
                100.0,
                1.0,
                100.0,
                5.0,
                None,
                None,
                None,
                id="extreme_heat_ectotherm_would_be_zero",
            ),
            pytest.param(
                -50.0,
                1.0,
                -50.0,
                5.0,
                None,
                None,
                None,
                id="extreme_cold_ectotherm_would_be_zero",
            ),
            pytest.param(
                25.0,
                10.0,
                25.0,
                5.0,
                30.0,
                40.0,
                20.0,
                id="explicit_thermal_tolerances",
            ),
            pytest.param(
                25.0,
                0.0,
                25.0,
                5.0,
                None,
                None,
                None,
                id="zero_diurnal_range_ectotherm_would_divide_by_zero",
            ),
        ],
    )
    def test_activity_window_endotherm_always_one(
        self,
        temperature,
        diurnal_temp_range,
        annual_mean_temp,
        annual_temp_sd,
        t_opt,
        t_max_crit,
        t_min_crit,
    ):
        """Endotherms return sigma_f_t = 1.0 regardless of all other arguments."""
        from virtual_ecosystem.models.animal.animal_traits import MetabolicType
        from virtual_ecosystem.models.animal.scaling_functions import activity_window

        assert (
            activity_window(
                MetabolicType.ENDOTHERMIC,
                temperature=temperature,
                diurnal_temp_range=diurnal_temp_range,
                annual_mean_temp=annual_mean_temp,
                annual_temp_sd=annual_temp_sd,
                t_opt=t_opt,
                t_max_crit=t_max_crit,
                t_min_crit=t_min_crit,
            )
            == 1.0
        )

    @pytest.mark.parametrize(
        "cohort_type, canopy_t, ground_t, soil_t, canopy_d, ground_d, soil_d, "
        "cell_id, expected_temp, expected_diurnal",
        [
            # GROUND only — herbivorous_mammal (index 3)
            pytest.param(
                "herbivore",
                25.0,
                20.0,
                15.0,
                8.0,
                5.0,
                2.0,
                0,
                20.0,
                5.0,
                id="ground_only_cell_0",
            ),
            # GROUND only, different cell — confirms cell_id indexing
            pytest.param(
                "herbivore",
                25.0,
                30.0,
                15.0,
                8.0,
                5.0,
                2.0,
                1,
                30.0,
                5.0,
                id="ground_only_cell_1",
            ),
            # CANOPY only — swallow (index 11)
            pytest.param(
                "canopy",
                25.0,
                20.0,
                15.0,
                8.0,
                5.0,
                2.0,
                0,
                25.0,
                8.0,
                id="canopy_only",
            ),
            # SOIL | GROUND | CANOPY — herbivorous_insect (index 5)
            pytest.param(
                "ectotherm",
                30.0,
                20.0,
                10.0,
                8.0,
                4.0,
                2.0,
                0,
                20.0,
                4.666666666666667,
                id="all_strata_mean",
            ),
        ],
    )
    def test_get_stratum_climate(
        self,
        herbivore_cohort_instance,
        ectotherm_cohort_instance,
        canopy_cohort_instance,
        cohort_type,
        canopy_t,
        ground_t,
        soil_t,
        canopy_d,
        ground_d,
        soil_d,
        cell_id,
        expected_temp,
        expected_diurnal,
    ):
        """Test per-cell temperature and diurnal range based on vertical occupancy."""
        import numpy as np

        cohort = {
            "herbivore": herbivore_cohort_instance,
            "ectotherm": ectotherm_cohort_instance,
            "canopy": canopy_cohort_instance,
        }[cohort_type]

        n_cells = 9
        result_temp, result_diurnal = cohort.get_stratum_climate(
            cell_id=cell_id,
            canopy_temperature=np.full(n_cells, canopy_t),
            ground_temperature=np.full(n_cells, ground_t),
            soil_temperature=np.full(n_cells, soil_t),
            canopy_diurnal_range=np.full(n_cells, canopy_d),
            ground_diurnal_range=np.full(n_cells, ground_d),
            soil_diurnal_range=np.full(n_cells, soil_d),
        )

        assert result_temp == pytest.approx(expected_temp)
        assert result_diurnal == pytest.approx(expected_diurnal)

    def test_get_stratum_climate_soil_only_matches_soil_ground_when_strata_equal(
        self, animal_model_instance, monkeypatch
    ):
        """SOIL-only and SOIL|GROUND produce identical climate when soil==ground."""
        import numpy as np

        from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy

        n = animal_model_instance.data.grid.n_cells
        soil_temp = np.full(n, 18.0)
        ground_temp = np.full(n, 18.0)  # identical to soil
        canopy_temp = np.full(
            n, 35.0
        )  # distinct: accidental inclusion would change mean

        soil_diurnal = np.full(n, 4.0)
        ground_diurnal = np.full(n, 4.0)  # identical to soil
        canopy_diurnal = np.full(
            n, 12.0
        )  # distinct: accidental inclusion would change mean

        cohort = next(iter(animal_model_instance.active_cohorts.values()))
        cell_id = cohort.territory[0]

        monkeypatch.setattr(
            cohort.functional_group, "vertical_occupancy", VerticalOccupancy.SOIL
        )
        temp_soil, diurnal_soil = cohort.get_stratum_climate(
            cell_id,
            canopy_temp,
            ground_temp,
            soil_temp,
            canopy_diurnal,
            ground_diurnal,
            soil_diurnal,
        )

        monkeypatch.setattr(
            cohort.functional_group,
            "vertical_occupancy",
            VerticalOccupancy.SOIL | VerticalOccupancy.GROUND,
        )
        temp_soil_ground, diurnal_soil_ground = cohort.get_stratum_climate(
            cell_id,
            canopy_temp,
            ground_temp,
            soil_temp,
            canopy_diurnal,
            ground_diurnal,
            soil_diurnal,
        )

        assert temp_soil == pytest.approx(temp_soil_ground)
        assert diurnal_soil == pytest.approx(diurnal_soil_ground)

    def test_get_mean_territory_climate(
        self,
        herbivore_cohort_instance,
    ):
        """Test that territory temperature and diurnal range are means across cells."""
        import numpy as np

        cohort = herbivore_cohort_instance
        n_cells = 9

        ground_temperature = np.arange(n_cells, dtype=float)
        ground_diurnal_range = np.arange(n_cells, dtype=float)
        canopy_temperature = np.zeros(n_cells)
        canopy_diurnal_range = np.zeros(n_cells)
        soil_temperature = np.zeros(n_cells)
        soil_diurnal_range = np.zeros(n_cells)

        result_temp, result_diurnal = cohort.get_mean_territory_climate(
            canopy_temperature=canopy_temperature,
            ground_temperature=ground_temperature,
            soil_temperature=soil_temperature,
            canopy_diurnal_range=canopy_diurnal_range,
            ground_diurnal_range=ground_diurnal_range,
            soil_diurnal_range=soil_diurnal_range,
        )

        assert result_temp == pytest.approx(4.0)
        assert result_diurnal == pytest.approx(4.0)

    def test_get_mean_territory_climate_multi_strata(
        self,
        ectotherm_cohort_instance,
    ):
        """Test territory climate averaging for a cohort occupying all three strata.

        Uses spatially varying arrays where each stratum scales cell index by a
        different factor, confirming both strata averaging and territory averaging
        interact correctly.
        """
        import numpy as np

        cohort = ectotherm_cohort_instance
        n_cells = 9

        result_temp, result_diurnal = cohort.get_mean_territory_climate(
            canopy_temperature=np.arange(n_cells, dtype=float) * 2,
            ground_temperature=np.arange(n_cells, dtype=float),
            soil_temperature=np.arange(n_cells, dtype=float) * 0.5,
            canopy_diurnal_range=np.arange(n_cells, dtype=float) * 2,
            ground_diurnal_range=np.arange(n_cells, dtype=float),
            soil_diurnal_range=np.arange(n_cells, dtype=float) * 0.5,
        )

        assert result_temp == pytest.approx(1.1666666666666667)
        assert result_diurnal == pytest.approx(1.1666666666666667)

    @pytest.mark.parametrize(
        "input_cnp, expected_cnp, test_id",
        [
            pytest.param(
                {"C": 1.0, "N": 0.5, "P": 0.25},
                {"C": 1.0, "N": 0.5, "P": 0.25},
                "all_positive",
            ),
            pytest.param(
                {"C": 3.0e-12, "N": -4.7e-15, "P": 4.8e-15},
                {"C": 3.0e-12, "N": 0.0, "P": 4.8e-15},
                "noise_level_negative",
            ),
            pytest.param(
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
                "all_zero",
            ),
            pytest.param(
                {"C": 1.0, "N": -1e-10 + 1e-15, "P": 0.0},
                {"C": 1.0, "N": 0.0, "P": 0.0},
                "just_within_tolerance",
            ),
            pytest.param(
                {"C": 1.0, "N": -1e-10, "P": 0.0},
                {"C": 1.0, "N": -1e-10, "P": 0.0},
                "at_tolerance_boundary_not_clamped",
            ),
            pytest.param(
                {"C": 1.0, "N": -0.5, "P": 0.0},
                {"C": 1.0, "N": -0.5, "P": 0.0},
                "genuinely_negative_not_clamped",
            ),
        ],
        ids=lambda p: p if isinstance(p, str) else None,
    )
    def test_clamp_cnp_noise(
        self, herbivore_cohort_instance, input_cnp, expected_cnp, test_id
    ):
        """Test _clamp_cnp_noise."""
        result = herbivore_cohort_instance._clamp_cnp_noise(input_cnp)
        assert result == pytest.approx(expected_cnp), f"Failed for scenario: {test_id}"
