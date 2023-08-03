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
def animal_community_instance(functional_group_list_instance):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(functional_group_list_instance)


@pytest.fixture
def animal_community_destination_instance(functional_group_list_instance):
    """Fixture for an animal community used in tests."""
    from virtual_rainforest.models.animals.animal_communities import AnimalCommunity

    return AnimalCommunity(functional_group_list_instance)


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
            assert isinstance(
                kwargs.get("soil_pool", None), type(animal_community_instance.soil_pool)
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
