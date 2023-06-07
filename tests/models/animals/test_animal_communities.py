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
        assert list(animal_community_instance.cohorts.keys()) == [
            "carnivorous_bird",
            "herbivorous_bird",
            "carnivorous_mammal",
            "herbivorous_mammal",
            "carnivorous_insect",
            "herbivorous_insect",
        ]

    def test_immigrate(
        self,
        animal_cohort_instance,
        animal_community_instance,
        animal_community_destination_instance,
    ):
        """Testing immigrate."""
        animal_community_instance.cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        assert (
            animal_cohort_instance
            in animal_community_instance.cohorts["herbivorous_mammal"]
        )
        animal_community_instance.immigrate(
            animal_community_instance.cohorts["herbivorous_mammal"][0],
            animal_community_destination_instance,
        )
        assert (
            animal_cohort_instance
            not in animal_community_instance.cohorts["herbivorous_mammal"]
        )
        assert (
            animal_cohort_instance
            in animal_community_destination_instance.cohorts["herbivorous_mammal"]
        )

    def test_die_cohort(self, animal_cohort_instance, animal_community_instance):
        """Testing die_cohort."""
        animal_community_instance.cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        assert (
            animal_cohort_instance
            in animal_community_instance.cohorts["herbivorous_mammal"]
        )
        assert animal_cohort_instance.is_alive
        animal_community_instance.die_cohort(animal_cohort_instance)
        assert not animal_cohort_instance.is_alive
        assert (
            animal_cohort_instance
            not in animal_community_instance.cohorts["herbivorous_mammal"]
        )

    def test_birth(self, animal_cohort_instance, animal_community_instance):
        """Testing birth."""
        animal_community_instance.cohorts["herbivorous_mammal"].append(
            animal_cohort_instance
        )
        baby_instance = animal_community_instance.birth(animal_cohort_instance)
        assert baby_instance.name == "herbivorous_mammal"
        assert baby_instance.mass == 10000.0
        assert baby_instance.age == 0.0
        assert baby_instance in animal_community_instance.cohorts["herbivorous_mammal"]
