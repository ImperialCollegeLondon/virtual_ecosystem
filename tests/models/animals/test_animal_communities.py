"""Test module for animal_communities.py."""

import pytest


@pytest.fixture
def animal_community_destination_instance(
    functional_group_list_instance,
    animal_model_instance,
    plant_data_instance,
    constants_instance,
):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(
        functional_groups=functional_group_list_instance,
        data=plant_data_instance,
        community_key=4,
        neighbouring_keys=[1, 3, 5, 7],
        get_destination=animal_model_instance.get_community_by_key,
        constants=constants_instance,
    )


@pytest.fixture
def functional_group_instance(shared_datadir, constants_instance):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file, constants_instance)

    return fg_list[3]


@pytest.fixture
def animal_cohort_instance(functional_group_instance, constants_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

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
            "carnivorous_insect",
            "herbivorous_insect",
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

    def test_migrate_community(
        self,
        animal_community_instance,
        animal_community_destination_instance,
        animal_cohort_instance,
        mocker,
    ):
        """Test migration of cohorts below the mass threshold."""

        # Mock the get_destination callable in this specific test context.
        mocker.patch.object(
            animal_community_instance,
            "get_destination",
            return_value=animal_community_destination_instance,
        )

        # Create a low mass cohort and append it to the source community.
        low_mass_cohort = animal_cohort_instance
        low_mass_cohort.mass_current = low_mass_cohort.functional_group.adult_mass / 2
        animal_community_instance.animal_cohorts["herbivorous_mammal"].append(
            low_mass_cohort
        )

        # Perform the migration
        animal_community_instance.migrate_community()

        # Check that the cohort has been removed from the source community
        assert (
            low_mass_cohort
            not in animal_community_instance.animal_cohorts["herbivorous_mammal"]
        )

        # Check that the cohort has been added to the destination community
        assert (
            low_mass_cohort
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

    def test_birth(
        self, animal_community_instance, animal_cohort_instance, constants_instance
    ):
        """Test the birth method in AnimalCommunity."""

        # Setup initial conditions
        parent_cohort_name = animal_cohort_instance.name
        animal_community_instance.animal_cohorts[parent_cohort_name].append(
            animal_cohort_instance
        )
        initial_cohort_count = len(
            animal_community_instance.animal_cohorts[parent_cohort_name]
        )

        # Set the reproductive mass of the parent cohort to ensure it can reproduce
        required_mass_for_birth = (
            animal_cohort_instance.functional_group.adult_mass
            * constants_instance.birth_mass_threshold
            - animal_cohort_instance.functional_group.adult_mass
        )

        animal_cohort_instance.reproductive_mass = required_mass_for_birth

        # Call the birth method
        animal_community_instance.birth(animal_cohort_instance)

        # Assertions
        # 1. Check that a new cohort is added
        new_cohort_count = len(
            animal_community_instance.animal_cohorts[parent_cohort_name]
        )
        assert new_cohort_count == initial_cohort_count + 1

        # 2. Check that the reproductive mass of the parent cohort is reduced to 0
        assert animal_cohort_instance.reproductive_mass == 0

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

    def test_collect_prey_finds_eligible_prey(
        self,
        animal_cohort_instance,
        animal_community_instance,
        functional_group_instance,
    ):
        """Testing collect_prey with eligible prey items."""
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

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
        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

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

        initial_age = list(
            chain.from_iterable(animal_community_instance.animal_cohorts.values())
        )[0].age
        animal_community_instance.increase_age_community(timedelta64(5, "D"))
        new_age = list(
            chain.from_iterable(animal_community_instance.animal_cohorts.values())
        )[0].age
        assert new_age == initial_age + 5

    def test_metabolize_community(
        self, dummy_climate_data, animal_community_instance, mocker
    ):
        """Testing metabolize_community."""
        from itertools import chain

        from numpy import timedelta64

        from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

        mock_metabolize = mocker.patch.object(AnimalCohort, "metabolize")
        animal_community_instance.metabolize_community(25.0, timedelta64(5, "D"))
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
