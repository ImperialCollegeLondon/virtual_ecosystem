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