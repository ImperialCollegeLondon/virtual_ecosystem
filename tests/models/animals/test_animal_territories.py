"""Test module for animal_territories.py."""

import pytest


class TestAnimalTerritories:
    """For testing the AnimalTerritories class."""

    @pytest.fixture
    def mock_get_plant_resources(self, mocker, animal_territory_instance):
        """Mock get_plant_resources method."""
        return mocker.patch.object(
            animal_territory_instance, "get_plant_resources", return_value=[]
        )

    @pytest.fixture
    def mock_get_excrement_pools(self, mocker, animal_territory_instance):
        """Mock get_excrement_pools method."""
        return mocker.patch.object(
            animal_territory_instance, "get_excrement_pools", return_value=[]
        )

    @pytest.fixture
    def mock_get_carcass_pools(self, mocker, animal_territory_instance):
        """Mock get_carcass_pools method."""
        return mocker.patch.object(
            animal_territory_instance, "get_carcass_pools", return_value=[]
        )

    def test_update_territory(self, animal_territory_instance):
        """Test for update_territory method."""
        # Define new grid cell keys for updating the territory
        new_grid_cell_keys = [4, 5, 6]

        # Call update_territory with new grid cell keys
        animal_territory_instance.update_territory(new_grid_cell_keys)

        # Check if the territory was updated correctly
        assert animal_territory_instance.grid_cell_keys == new_grid_cell_keys

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

    def test_get_carcass_pools(self, animal_territory_instance):
        """Test for get carcass pool method."""
        from virtual_ecosystem.models.animal.decay import CarcassPool

        carcass_pools = animal_territory_instance.get_carcass_pools()
        assert len(carcass_pools) == len(animal_territory_instance.grid_cell_keys)
        for carcass in carcass_pools:
            assert isinstance(carcass, CarcassPool)

    @pytest.fixture
    def mock_carcass_pool(self, mocker):
        """Fixture for a mock CarcassPool."""
        mock_pool = mocker.Mock()
        mock_pool.scavengeable_energy = 10000.0
        mock_pool.decomposed_energy = 0.0
        return mock_pool

    @pytest.fixture
    def mock_community(self, mocker, mock_carcass_pool):
        """Fixture for a mock AnimalCommunity with a carcass pool."""
        community_mock = mocker.Mock()
        community_mock.carcass_pool = mock_carcass_pool
        return community_mock

    @pytest.fixture
    def mock_get_community_by_key(self, mocker, mock_community):
        """Fixture for get_community_by_key, returning a mock community."""
        return mocker.Mock(side_effect=lambda key: mock_community)

    @pytest.fixture
    def animal_territory_instance_1(self, mock_get_community_by_key):
        """Fixture for the first animal territory with mock get_community_by_key."""
        from virtual_ecosystem.models.animal.animal_territories import AnimalTerritory

        return AnimalTerritory(
            centroid=0,
            grid_cell_keys=[1, 2, 3],
            get_community_by_key=mock_get_community_by_key,
        )

    @pytest.fixture
    def animal_territory_instance_2(self, mock_get_community_by_key):
        """Fixture for the second animal territory with mock get_community_by_key."""
        from virtual_ecosystem.models.animal.animal_territories import AnimalTerritory

        return AnimalTerritory(
            centroid=1,
            grid_cell_keys=[2, 3, 4],
            get_community_by_key=mock_get_community_by_key,
        )

    def test_find_intersecting_carcass_pools(
        self,
        animal_territory_instance_1,
        animal_territory_instance_2,
        mock_carcass_pool,
    ):
        """Test for find_intersecting_carcass_pools method."""
        intersecting_pools = (
            animal_territory_instance_1.find_intersecting_carcass_pools(
                animal_territory_instance_2
            )
        )

        # Since the same mock object is returned, we need to repeat it for the
        # expected value.
        expected_pools = [mock_carcass_pool, mock_carcass_pool]
        assert intersecting_pools == expected_pools


@pytest.mark.parametrize(
    "centroid_key, target_cell_number, cell_nx, cell_ny, expected",
    [
        (0, 1, 3, 3, {0}),  # Single cell territory
        (4, 5, 3, 3, {4, 3, 5, 1, 7}),  # Small territory in the center
        (0, 4, 3, 3, {0, 1, 3, 6}),  # Territory starting at the corner
        (8, 4, 3, 3, {8, 2, 5, 7}),  # Territory starting at another corner
        (4, 9, 3, 3, {4, 3, 5, 1, 7, 0, 2, 6, 8}),  # Full grid territory
    ],
    ids=[
        "single_cell",
        "small_center",
        "corner_start",
        "another_corner",
        "full_grid",
    ],
)
def test_bfs_territory(centroid_key, target_cell_number, cell_nx, cell_ny, expected):
    """Test bfs_territory with various parameters."""
    from virtual_ecosystem.models.animal.animal_territories import bfs_territory

    result = set(bfs_territory(centroid_key, target_cell_number, cell_nx, cell_ny))
    assert result == expected, f"Expected {expected}, but got {result}"
