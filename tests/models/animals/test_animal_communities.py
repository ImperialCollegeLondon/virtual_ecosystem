"""Test module for animal_communities.py."""

from math import ceil

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def animal_community_destination_instance(
    functional_group_list_instance,
    animal_model_instance,
    animal_data_for_community_instance,
    constants_instance,
):
    """Fixture for an animal community used in tests."""
    from virtual_ecosystem.models.animal.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_groups=functional_group_list_instance,
        data=animal_data_for_community_instance,
        community_key=4,
        neighbouring_keys=[1, 3, 5, 7],
        get_destination=animal_model_instance.get_community_by_key,
        constants=constants_instance,
    )


@pytest.fixture
def functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_ecosystem.models.animal.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[3]


@pytest.fixture
def animal_cohort_instance(functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

    return AnimalCohort(
        functional_group_instance,
        functional_group_instance.adult_mass,
        1.0,
        10,
        constants_instance,
    )


class TestAnimalCommunity:
    """Test AnimalCommunity class."""

    def test_initialization(self, animal_community_instance):
        """Testing initialization of derived parameters for animal cohorts."""
        assert list(animal_community_instance.animal_cohorts.keys()) == [
            "carnivorous_bird",
            "herbivorous_bird",
            "carnivorous_mammal",
            "herbivorous_mammal",
            "carnivorous_insect_iteroparous",
            "herbivorous_insect_iteroparous",
            "carnivorous_insect_semelparous",
            "herbivorous_insect_semelparous",
            "butterfly",
            "caterpillar",
        ]

    def test_all_animal_cohorts_property(
        self, animal_community_instance, animal_cohort_instance
    ):
        """Test the all_animal_cohorts property."""
        from collections.abc import Iterable

        # Add an animal cohort to the community
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )

        # Check if the added cohort is in the all_animal_cohorts property
        assert animal_cohort_instance in animal_community_instance.all_animal_cohorts
        # Check the type of all_animal_cohorts
        assert isinstance(animal_community_instance.all_animal_cohorts, Iterable)

    def test_populate_community(self, animal_community_instance):
        """Testing populate_community."""
        animal_community_instance.populate_community()
        for cohorts in animal_community_instance.animal_cohorts.values():
            assert len(cohorts) == 1  # since it should have populated one of each

    def test_migrate(
        self,
        animal_cohort_instance,
        animal_community_instance,
        animal_community_destination_instance,
    ):
        """Testing migrate."""
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        assert (
            animal_cohort_instance
            in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )
        animal_community_instance.migrate(
            animal_community_instance.animal_cohorts["herbivorous_mammal"][0],
            animal_community_destination_instance,
        )
        assert (
            animal_cohort_instance
            not in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )
        assert (
            animal_cohort_instance
            in animal_community_destination_instance.animal_cohorts[
                "herbivorous_mammal"
            ]
        )

    @pytest.mark.parametrize(
        "mass_ratio, age, probability_output, should_migrate",
        [
            (0.5, 5.0, False, True),  # Starving non-juvenile, should migrate
            (
                1.0,
                0.0,
                False,
                False,
            ),  # Well-fed juvenile, low probability, should not migrate
            (
                1.0,
                0.0,
                True,
                True,
            ),  # Well-fed juvenile, high probability, should migrate
            (
                0.5,
                0.0,
                True,
                True,
            ),  # Starving juvenile, high probability, should migrate
            (
                0.5,
                0.0,
                False,
                True,
            ),  # Starving juvenile, low probability, should migrate due to starvation
            (1.0, 5.0, False, False),  # Well-fed non-juvenile, should not migrate
        ],
        ids=[
            "starving_non_juvenile",
            "well_fed_juvenile_low_prob",
            "well_fed_juvenile_high_prob",
            "starving_juvenile_high_prob",
            "starving_juvenile_low_prob",
            "well_fed_non_juvenile",
        ],
    )
    def test_migrate_community(
        self,
        mocker,
        animal_community_instance,
        animal_community_destination_instance,
        animal_cohort_instance,
        mass_ratio,
        age,
        probability_output,
        should_migrate,
    ):
        """Test migration of cohorts for both starving and juvenile conditions."""

        cohort = animal_cohort_instance
        cohort.age = age
        cohort.mass_current = cohort.functional_group.adult_mass * mass_ratio

        # Mock the get_destination callable to return a specific community.
        mocker.patch.object(
            animal_community_instance,
            "get_destination",
            return_value=animal_community_destination_instance,
        )

        # Append cohort to the source community
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(cohort)

        # Mock `migrate_juvenile_probability` to control juvenile migration logic
        mocker.patch.object(
            cohort, "migrate_juvenile_probability", return_value=probability_output
        )

        # Perform the migration
        animal_community_instance.migrate_community()

        # Check migration outcome based on expected results
        if should_migrate:
            assert (
                cohort
                not in animal_community_instance.animal_cohorts["herbivorous_mammal"]
            )
            assert (
                cohort
                in animal_community_destination_instance.animal_cohorts[
                    "herbivorous_mammal"
                ]
            )
        else:
            assert (
                cohort in animal_community_instance.animal_cohorts["herbivorous_mammal"]
            )

    def test_remove_dead_cohort(
        self, animal_cohort_instance, animal_community_instance
    ):
        """Testing remove_dead_cohort."""
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        assert (
            animal_cohort_instance
            in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )
        assert animal_cohort_instance.is_alive
        animal_community_instance.remove_dead_cohort(animal_cohort_instance)
        assert (
            animal_cohort_instance
            in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )
        animal_cohort_instance.is_alive = False
        assert not animal_cohort_instance.is_alive
        animal_community_instance.remove_dead_cohort(animal_cohort_instance)
        assert (
            animal_cohort_instance
            not in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )

    @pytest.mark.parametrize(
        "reproductive_type, initial_mass, expected_offspring",
        [
            pytest.param("iteroparous", 10, 1, id="iteroparous_survival"),
            pytest.param("semelparous", 10, 1, id="semelparous_death"),
        ],
    )
    def test_birth(
        self,
        reproductive_type,
        initial_mass,
        expected_offspring,
        animal_community_instance,
        animal_cohort_instance,
    ):
        """Test the birth method in AnimalCommunity under various conditions."""

        # Setup initial conditions
        parent_cohort_name = animal_cohort_instance.name
        animal_cohort_instance.functional_group.reproductive_type = reproductive_type
        animal_cohort_instance.functional_group.birth_mass = 2
        animal_cohort_instance.mass_current = initial_mass
        animal_cohort_instance.individuals = 10

        # Prepare the community
        animal_community_instance.animal_cohorts[parent_cohort_name] = [
            animal_cohort_instance
        ]

        number_cohorts = len(
            animal_community_instance.animal_cohorts[parent_cohort_name]
        )

        animal_community_instance.birth(animal_cohort_instance)

        # Assertions
        # 1. Check for changes in the parent cohort based on reproductive type
        if reproductive_type == "semelparous":
            # The parent should be removed if it dies
            assert (
                animal_cohort_instance
                not in animal_community_instance.animal_cohorts[parent_cohort_name]
            )
        else:
            # Reproductive mass should be reset
            assert animal_cohort_instance.reproductive_mass == 0
            # The parent should still be present in the community
            assert (
                animal_cohort_instance
                in animal_community_instance.animal_cohorts[parent_cohort_name]
            )

        # 2. Check that the offspring were added if reproduction occurred

        if expected_offspring and reproductive_type == "semelparous":
            assert (
                len(animal_community_instance.animal_cohorts[parent_cohort_name])
                == number_cohorts
            )
        elif expected_offspring and reproductive_type == "iteroparous":
            assert (
                len(animal_community_instance.animal_cohorts[parent_cohort_name])
                == number_cohorts + 1
            )
        else:
            assert (
                len(animal_community_instance.animal_cohorts[parent_cohort_name])
                == number_cohorts
            )

    def test_birth_community(self, animal_community_instance, constants_instance):
        """Test the thresholding behavior of birth_community."""

        from itertools import chain

        # Preparation: populate the community
        animal_community_instance.populate_community()

        # Choose a cohort to track
        all_cohorts = list(
            chain.from_iterable(animal_community_instance.animal_cohorts.values())
        )
        initial_cohort = all_cohorts[0]

        # Set mass to just below the threshold
        threshold_mass = (
            initial_cohort.functional_group.adult_mass
            * constants_instance.birth_mass_threshold
            - initial_cohort.functional_group.adult_mass
        )

        initial_cohort.reproductive_mass = threshold_mass - 0.1
        initial_count_below_threshold = len(
            animal_community_instance.animal_cohorts[initial_cohort.name]
        )

        # Execution: apply birth to the community
        animal_community_instance.birth_community()

        # Assertion: check if the cohort count remains unchanged
        new_count_below_threshold = len(
            animal_community_instance.animal_cohorts[initial_cohort.name]
        )
        assert new_count_below_threshold == initial_count_below_threshold

        # Set mass to just above the threshold
        initial_cohort.reproductive_mass = threshold_mass + 0.1
        initial_count_above_threshold = len(
            animal_community_instance.animal_cohorts[initial_cohort.name]
        )

        # Execution: apply birth to the community again
        animal_community_instance.birth_community()

        # Assertion: check if the cohort count increased by 1 for the above case
        new_count_above_threshold = len(
            animal_community_instance.animal_cohorts[initial_cohort.name]
        )
        assert new_count_above_threshold == initial_count_above_threshold + 1

    def test_forage_community(
        self, animal_cohort_instance, animal_community_instance, mocker
    ):
        """Testing forage_community."""
        import unittest
        from copy import deepcopy

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_communities import AnimalCommunity

        # Prepare data
        animal_cohort_instance_2 = deepcopy(animal_cohort_instance)
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            animal_cohort_instance_2
        )

        # Mock methods
        mock_forage_cohort = mocker.patch.object(AnimalCohort, "forage_cohort")

        mock_collect_prey = mocker.patch.object(
            AnimalCommunity, "collect_prey", return_value=mocker.MagicMock()
        )

        # Execute method
        animal_community_instance.forage_community()

        # Check if the forage_cohort and collect_prey methods have been called for each
        # cohort
        assert mock_forage_cohort.call_count == 2
        assert mock_collect_prey.call_count == 2

        # Check if the forage_cohort and collect_prey methods were called correctly
        for call in mock_forage_cohort.call_args_list:
            _, kwargs = call
            assert isinstance(kwargs.get("plant_list", None), list)
            assert isinstance(kwargs.get("animal_list", None), unittest.mock.MagicMock)
            assert isinstance(
                kwargs.get("carcass_pool", None),
                type(animal_community_instance.carcass_pool),
            )

    def test_collect_prey_finds_eligible_prey(
        self,
        animal_cohort_instance,
        animal_community_instance,
        functional_group_instance,
    ):
        """Testing collect_prey with eligible prey items."""
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

        prey_cohort = AnimalCohort(functional_group_instance, 5000.0, 1, 10)
        animal_community_instance.animal_cohorts[functional_group_instance.name].append(
            prey_cohort
        )

        animal_cohort_instance.prey_groups = {
            functional_group_instance.name: (0, 10000)
        }

        collected_prey = animal_community_instance.collect_prey(animal_cohort_instance)

        assert prey_cohort in collected_prey

    def test_collect_prey_filters_out_ineligible_prey(
        self,
        animal_cohort_instance,
        animal_community_instance,
        functional_group_instance,
    ):
        """Testing collect_prey with no eligible prey items."""
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

        prey_cohort = AnimalCohort(functional_group_instance, 20000.0, 1, 10)
        animal_community_instance.animal_cohorts[functional_group_instance.name].append(
            prey_cohort
        )

        animal_cohort_instance.prey_groups = {
            functional_group_instance.name: (0, 10000)
        }

        collected_prey = animal_community_instance.collect_prey(animal_cohort_instance)

        assert prey_cohort not in collected_prey

    def test_increase_age_community(self, animal_community_instance):
        """Testing increase_age_community."""
        from itertools import chain

        from numpy import timedelta64

        animal_community_instance.populate_community()

        initial_age = next(
            iter(chain.from_iterable(animal_community_instance.animal_cohorts.values()))
        ).age
        animal_community_instance.increase_age_community(timedelta64(5, "D"))
        new_age = next(
            iter(chain.from_iterable(animal_community_instance.animal_cohorts.values()))
        ).age
        assert new_age == initial_age + 5

    def test_metabolize_community(
        self, animal_community_instance, mocker: MockerFixture
    ):
        """Testing metabolize_community."""
        from itertools import chain

        from numpy import timedelta64

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

        # Mocking the AnimalCohort methods
        mock_metabolize = mocker.patch.object(
            AnimalCohort, "metabolize", return_value=100.0
        )
        mock_respire = mocker.patch.object(AnimalCohort, "respire", return_value=90.0)
        mock_excrete = mocker.patch.object(AnimalCohort, "excrete")

        # Initial value of total animal respiration
        initial_respiration = (
            animal_community_instance.data["total_animal_respiration"]
            .loc[{"cell_id": animal_community_instance.community_key}]
            .item()
        )

        # Call the metabolize_community method
        animal_community_instance.metabolize_community(25.0, timedelta64(5, "D"))

        # Calculate expected respiration after the method call
        num_cohorts = len(
            list(chain.from_iterable(animal_community_instance.animal_cohorts.values()))
        )
        expected_total_respiration = initial_respiration + num_cohorts * 90.0

        # Check that metabolize was called the correct number of times
        assert mock_metabolize.call_count == num_cohorts

        # Check that respire was called the correct number of times
        assert mock_respire.call_count == num_cohorts

        # Check that excrete was called the correct number of times
        assert mock_excrete.call_count == num_cohorts

        # Verify that total_animal_respiration was updated correctly
        updated_respiration = (
            animal_community_instance.data["total_animal_respiration"]
            .loc[{"cell_id": animal_community_instance.community_key}]
            .item()
        )
        assert updated_respiration == expected_total_respiration

    @pytest.mark.parametrize(
        "days",
        [
            pytest.param(1, id="one_day"),
            pytest.param(5, id="five_days"),
            pytest.param(10, id="ten_days"),
        ],
    )
    def test_inflict_non_predation_mortality_community(
        self, mocker, animal_community_instance, days
    ):
        """Testing natural mortality infliction for the entire community."""
        from numpy import timedelta64

        dt = timedelta64(days, "D")

        animal_community_instance.populate_community()

        # Mock the inflict_non_predation_mortality method
        mock_mortality = mocker.patch(
            "virtual_ecosystem.models.animal.animal_cohorts.AnimalCohort."
            "inflict_non_predation_mortality"
        )

        # Call the community method to inflict natural mortality
        animal_community_instance.inflict_non_predation_mortality_community(dt)

        number_of_days = float(dt / timedelta64(1, "D"))

        # Assert the inflict_non_predation_mortality method was called for each cohort
        for cohorts in animal_community_instance.animal_cohorts.values():
            for cohort in cohorts:
                mock_mortality.assert_called_with(
                    number_of_days, animal_community_instance.carcass_pool
                )

        # Check if cohorts with no individuals left are flagged as not alive
        for cohorts in animal_community_instance.animal_cohorts.values():
            for cohort in cohorts:
                if cohort.individuals <= 0:
                    assert (
                        not cohort.is_alive
                    ), "Cohort with no individuals should be marked as not alive"
                    assert (
                        cohort
                        not in animal_community_instance.animal_cohorts[cohort.name]
                    ), "Dead cohort should be removed from the community"

    def test_metamorphose(
        self,
        mocker,
        animal_community_instance,
        caterpillar_cohort_instance,
        butterfly_cohort_instance,
    ):
        """Test the metamorphose method for different scenarios."""

        larval_cohort = caterpillar_cohort_instance
        larval_cohort.is_alive = True

        adult_functional_group = butterfly_cohort_instance.functional_group
        adult_functional_group.birth_mass = 5.0
        mock_get_functional_group_by_name = mocker.patch(
            "virtual_ecosystem.models.animal.animal_communities.get_functional_group_by_name",
            return_value=adult_functional_group,
        )
        animal_community_instance.animal_cohorts["butterfly"] = []

        mock_remove_dead_cohort = mocker.patch.object(
            animal_community_instance, "remove_dead_cohort"
        )

        # Verify
        number_dead = ceil(
            larval_cohort.individuals * larval_cohort.constants.metamorph_mortality
        )
        expected_individuals = larval_cohort.individuals - number_dead

        animal_community_instance.metamorphose(larval_cohort)

        assert not larval_cohort.is_alive
        assert len(animal_community_instance.animal_cohorts["butterfly"]) == 1
        assert (
            animal_community_instance.animal_cohorts["butterfly"][0].individuals
            == expected_individuals
        )
        mock_remove_dead_cohort.assert_called_once_with(larval_cohort)
        mock_get_functional_group_by_name.assert_called_once_with(
            animal_community_instance.functional_groups,
            larval_cohort.functional_group.offspring_functional_group,
        )

    @pytest.mark.parametrize(
        "mass_current, expected_caterpillar_count, expected_butterfly_count,"
        "expected_is_alive",
        [
            pytest.param(
                0.9,  # Caterpillar mass is below the adult mass threshold
                1,  # Caterpillar count should remain the same
                0,  # Butterfly count should remain the same
                True,  # Caterpillar should still be alive
                id="Below_mass_threshold",
            ),
            pytest.param(
                1.1,  # Caterpillar mass is above the adult mass threshold
                0,  # Caterpillar count should decrease
                1,  # Butterfly count should increase
                False,  # Caterpillar should no longer be alive
                id="Above_mass_threshold",
            ),
        ],
    )
    def test_metamorphose_community(
        self,
        animal_community_instance,
        caterpillar_cohort_instance,
        mass_current,
        expected_caterpillar_count,
        expected_butterfly_count,
        expected_is_alive,
    ):
        """Test the metamorphosis behavior of metamorphose_community."""

        # Manually set the mass_current for the caterpillar cohort
        caterpillar_cohort = caterpillar_cohort_instance
        caterpillar_cohort.mass_current = (
            caterpillar_cohort.functional_group.adult_mass * mass_current
        )

        # Initialize the animal_cohorts with both caterpillar and butterfly entries
        animal_community_instance.animal_cohorts = {
            "caterpillar": [caterpillar_cohort],
            "butterfly": [],
        }

        # Initial counts
        initial_caterpillar_count = len(
            animal_community_instance.animal_cohorts.get("caterpillar", [])
        )
        initial_butterfly_count = len(
            animal_community_instance.animal_cohorts.get("butterfly", [])
        )

        assert initial_caterpillar_count == 1
        assert initial_butterfly_count == 0

        # Execution: apply metamorphose to the community
        animal_community_instance.metamorphose_community()

        # New counts after metamorphosis
        new_caterpillar_count = len(
            animal_community_instance.animal_cohorts.get("caterpillar", [])
        )
        new_butterfly_count = len(
            animal_community_instance.animal_cohorts.get("butterfly", [])
        )

        # Assertions
        assert new_caterpillar_count == expected_caterpillar_count
        assert new_butterfly_count == expected_butterfly_count
        assert caterpillar_cohort.is_alive == expected_is_alive
