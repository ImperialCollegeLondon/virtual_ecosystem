"""Test module for animal_territories.py."""

import pytest


class TestAnimalTerritories:
    """For testing the AnimalTerritories class."""

    @pytest.fixture
    def get_community_by_key(self, animal_community_instance):
        """Fixture for get_community_by_key."""

        def _get_community_by_key(key):
            return animal_community_instance

        return _get_community_by_key

    @pytest.fixture
    def animal_territory_instance(self, get_community_by_key):
        """Fixture for animal territories."""
        from virtual_ecosystem.models.animal.animal_territories import AnimalTerritory

        return AnimalTerritory(
            grid_cell_keys=[1, 2, 3], get_community_by_key=get_community_by_key
        )

    def test_update_territory(
        self, mocker, animal_territory_instance, herbivore_cohort_instance
    ):
        """Test for update_territory method."""
        mock_get_prey = mocker.patch.object(
            animal_territory_instance, "get_prey", return_value=[]
        )
        mock_get_plant_resources = mocker.patch.object(
            animal_territory_instance, "get_plant_resources", return_value=[]
        )
        mock_get_excrement_pools = mocker.patch.object(
            animal_territory_instance, "get_excrement_pools", return_value=[]
        )
        mock_get_carcass_pool = mocker.patch.object(
            animal_territory_instance, "get_carcass_pool", return_value=[]
        )

        animal_territory_instance.update_territory(herbivore_cohort_instance)

        mock_get_prey.assert_called_once_with(herbivore_cohort_instance)
        mock_get_plant_resources.assert_called_once()
        mock_get_excrement_pools.assert_called_once()
        mock_get_carcass_pool.assert_called_once()

    def test_get_prey(
        self,
        mocker,
        animal_territory_instance,
        herbivore_cohort_instance,
        animal_community_instance,
    ):
        """Test for get_prey method."""
        mock_collect_prey = mocker.patch.object(
            animal_community_instance, "collect_prey", return_value=[]
        )

        prey = animal_territory_instance.get_prey(herbivore_cohort_instance)
        assert prey == []
        for cell_id in animal_territory_instance.grid_cell_keys:
            mock_collect_prey.assert_any_call(herbivore_cohort_instance)

    def test_get_plant_resources(self, animal_territory_instance):
        """Test for get_plant_resources method."""
        from virtual_ecosystem.models.animal.plant_resources import PlantResources

        plant_resources = animal_territory_instance.get_plant_resources()
        assert len(plant_resources) == len(animal_territory_instance.grid_cell_keys)
        for plant in plant_resources:
            assert isinstance(plant, PlantResources)

    def test_get_excrement_pools(self, animal_territory_instance):
        """Test for get_excrement pools method."""
        from virtual_ecosystem.models.animal.decay import ExcrementPool

        excrement_pools = animal_territory_instance.get_excrement_pools()
        assert len(excrement_pools) == len(animal_territory_instance.grid_cell_keys)
        for excrement in excrement_pools:
            assert isinstance(excrement, ExcrementPool)

    def test_get_carcass_pool(self, animal_territory_instance):
        """Test for get carcass pool method."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcass_pools = animal_territory_instance.get_carcass_pool()
        assert len(carcass_pools) == len(animal_territory_instance.grid_cell_keys)
        for carcass in carcass_pools:
            assert isinstance(carcass, CarcassPool)
