"""Test module for animal_communities.py."""

import pytest


@pytest.fixture
def functional_group_list_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list


@pytest.fixture
def animal_model_instance(data_instance, functional_group_list_instance):
    """Fixture for an animal model object used in tests."""
    from pint import Quantity

    from virtual_rainforest.models.animals.animal_model import AnimalModel

    return AnimalModel(data_instance, Quantity("1 day"), functional_group_list_instance)


@pytest.fixture
def animal_community_instance(functional_group_list_instance, animal_model_instance):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_group_list_instance,
        0,
        [0, 1, 3],
        animal_model_instance.get_community_by_key,
    )


@pytest.fixture
def animal_community_destination_instance(
    functional_group_list_instance, animal_model_instance
):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_group_list_instance,
        1,
        [0, 1, 2, 4],
        animal_model_instance.get_community_by_key,
    )


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

    return AnimalCohort(
        functional_group_instance, functional_group_instance.adult_mass, 1.0
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
            "carnivorous_insect",
            "herbivorous_insect",
        ]

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

    def test_migrate_community(
        self,
        animal_community_instance,
        animal_community_destination_instance,
        animal_cohort_instance,
        mocker,
    ):
        """Test migration of cohorts below the energy threshold."""

        # Mock the get_destination callable in this specific test context.
        mocker.patch.object(
            animal_community_instance,
            "get_destination",
            return_value=animal_community_destination_instance,
        )

        low_energy_cohort = animal_cohort_instance
        low_energy_cohort.stored_energy = 5.0
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            low_energy_cohort
        )

        # Now let's simulate migration
        animal_community_instance.migrate_community()

        # Ensure cohort was migrated
        assert (
            low_energy_cohort
            not in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )
        assert (
            low_energy_cohort
            in animal_community_destination_instance.animal_cohorts[
                "herbivorous_mammal"
            ]
        )

    def test_die_cohort(self, animal_cohort_instance, animal_community_instance):
        """Testing die_cohort."""
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        assert (
            animal_cohort_instance
            in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )
        assert animal_cohort_instance.is_alive
        animal_community_instance.die_cohort(animal_cohort_instance)
        assert not animal_cohort_instance.is_alive
        assert (
            animal_cohort_instance
            not in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )

    def test_birth(self, animal_community_instance, animal_cohort_instance):
        """Test the birth method in AnimalCommunity."""

        # Setup initial conditions
        parent_cohort_name = animal_cohort_instance.name
        animal_community_instance.animal_cohorts[parent_cohort_name].append(
            animal_cohort_instance
        )
        initial_cohort_count = len(
            animal_community_instance.animal_cohorts[parent_cohort_name]
        )

        # Set up the energy level of the parent cohort to ensure it can reproduce
        required_energy_for_birth = animal_cohort_instance.reproduction_cost

        animal_cohort_instance.stored_energy = (
            required_energy_for_birth + 10
        )  # Setting it 10 units above the required

        initial_stored_energy = animal_cohort_instance.stored_energy

        # Call the birth method
        animal_community_instance.birth(animal_cohort_instance)

        # Assertions
        # 1. Check that a new cohort of the same type as the parent cohort is added
        new_cohort_count = len(
            animal_community_instance.animal_cohorts[parent_cohort_name]
        )
        assert new_cohort_count == initial_cohort_count + 1

        # 2. Check that the stored energy of the parent cohort is reduced correctly
        expected_energy_after_birth = initial_stored_energy - required_energy_for_birth
        assert animal_cohort_instance.stored_energy == expected_energy_after_birth

    def test_birth_community(self, animal_community_instance):
        """Test the thresholding behavior of birth_community."""

        from itertools import chain

        # Preparation: populate the community
        animal_community_instance.populate_community()

        # Choose a cohort to track
        all_cohorts = list(
            chain.from_iterable(animal_community_instance.animal_cohorts.values())
        )
        initial_cohort = all_cohorts[0]

        # Set energy to just below the threshold
        threshold_energy = initial_cohort.reproduction_energy_threshold

        initial_cohort.stored_energy = threshold_energy - 0.1
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

        # Set energy to just above the threshold
        initial_cohort.stored_energy = threshold_energy + 0.1
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

        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort
        from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

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

    def test_collect_prey(
        self,
        animal_cohort_instance,
        animal_community_instance,
        functional_group_instance,
    ):
        """Testing collect_prey."""
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

        # Prepare data
        prey_cohort = AnimalCohort(functional_group_instance, 5000.0, 1)
        animal_community_instance.animal_cohorts[functional_group_instance.name].append(
            prey_cohort
        )

        # Set prey groups for the test cohort
        animal_cohort_instance.prey_groups = {
            functional_group_instance.name: (0, 10000)
        }

        collected_prey = animal_community_instance.collect_prey(animal_cohort_instance)

        assert prey_cohort in collected_prey

        # Test with prey outside of size range
        prey_cohort.mass = 20000.0

        collected_prey = animal_community_instance.collect_prey(animal_cohort_instance)

        assert prey_cohort not in collected_prey

        # Test when cohort has no prey groups
        animal_cohort_instance.prey_groups = {}

        collected_prey = animal_community_instance.collect_prey(animal_cohort_instance)

        assert collected_prey == []

        # Test when there are no cohorts that match the size criteria
        animal_cohort_instance.prey_groups = {
            functional_group_instance.name: (0, 10000)
        }
        prey_cohort.mass = 50000.0

        collected_prey = animal_community_instance.collect_prey(animal_cohort_instance)

        assert collected_prey == []

    def test_increase_age_community(self, animal_community_instance):
        """Testing increase_age_community."""
        from itertools import chain

        from numpy import timedelta64

        animal_community_instance.populate_community()

        initial_age = list(
            chain.from_iterable(animal_community_instance.animal_cohorts.values())
        )[0].age
        animal_community_instance.increase_age_community(timedelta64(5, "D"))
        new_age = list(
            chain.from_iterable(animal_community_instance.animal_cohorts.values())
        )[0].age
        assert new_age == initial_age + 5

    def test_metabolize_community(self, animal_community_instance, mocker):
        """Testing metabolize_community."""
        from itertools import chain

        from numpy import timedelta64

        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

        mock_metabolize = mocker.patch.object(AnimalCohort, "metabolize")
        animal_community_instance.metabolize_community(timedelta64(5, "D"))
        assert mock_metabolize.call_count == len(
            list(chain.from_iterable(animal_community_instance.animal_cohorts.values()))
        )

    def test_inflict_natural_mortality_community(
        self, animal_community_instance, mocker
    ):
        """Testing natural mortality infliction for the entire community."""
        from numpy import timedelta64

        # Create a time delta (for example, 5 days)
        dt = timedelta64(5, "D")

        animal_community_instance.populate_community()

        # Iterate over the animal cohorts within the community
        for cohorts in animal_community_instance.animal_cohorts.values():
            for cohort in cohorts:
                # Mock the cohort's inflict_natural_mortality method
                cohort.inflict_natural_mortality = mocker.MagicMock()

        # Call the community method to inflict natural mortality
        animal_community_instance.inflict_natural_mortality_community(dt)

        # Check that the inflict_natural_mortality method was called correctly for each
        # #cohort
        number_of_days = float(dt / timedelta64(1, "D"))
        for cohorts in animal_community_instance.animal_cohorts.values():
            for cohort in cohorts:
                cohort.inflict_natural_mortality.assert_called_once_with(
                    animal_community_instance.carcass_pool, number_of_days
                )
