"""Test module for dummy_plants_and_soil.py."""

import pytest


@pytest.fixture
def excrement_instance():
    """Fixture for a soil pool used in tests."""
    from virtual_rainforest.models.animals.decay import ExcrementPool

    return ExcrementPool(100000.0, 0.0)


@pytest.fixture
def plant_instance():
    """Fixture for a plant community used in tests."""
    from virtual_rainforest.models.animals.dummy_plants_and_soil import PlantCommunity

    return PlantCommunity(10000.0)


@pytest.fixture
def herb_functional_group_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list[3]


@pytest.fixture
def herbivore_instance(herb_functional_group_instance):
    """Fixture for an animal cohort used in tests."""
    from virtual_rainforest.models.animals.animal_cohorts import AnimalCohort

    return AnimalCohort(herb_functional_group_instance, 100.0, 1)


class TestPlantCommunity:
    """Test Plant class."""

    @pytest.mark.parametrize(
        "initial, final",
        [(182000000000.0, 182000000000.0), (10000.0, 19999.999450), (0.0, 0.0)],
    )
    def test_grow(self, plant_instance, initial, final):
        """Testing grow at 100%, 50%, and 0% maximum energy."""
        plant_instance.stored_energy = initial
        plant_instance.grow()
        assert plant_instance.stored_energy == pytest.approx(final, rel=1e-6)

    def test_die(self, plant_instance):
        """Testing die."""
        assert plant_instance.is_alive
        plant_instance.die()
        assert not plant_instance.is_alive

    def test_get_eaten(self, plant_instance, herbivore_instance, excrement_instance):
        """Testing get_eaten.

        Currently, this just tests rough execution. As the model gets paramterized,
        these tests will be expanded to specific values.
        """

        initial_plant_energy = plant_instance.stored_energy
        initial_decay_pool_energy = excrement_instance.decomposed_energy

        # Execution
        plant_instance.get_eaten(herbivore_instance, excrement_instance)

        # Assertions
        assert plant_instance.stored_energy < initial_plant_energy
        assert excrement_instance.decomposed_energy > initial_decay_pool_energy
