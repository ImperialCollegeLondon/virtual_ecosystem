"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import numpy as np
import pytest

from tests.conftest import log_check


@pytest.fixture
def prepared_animal_model_instance(
    dummy_animal_data,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Animal model instance in which setup has already been run."""
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    model = AnimalModel(
        data=dummy_animal_data,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )
    model.setup()  # Ensure setup is called
    return model


class TestAnimalModel:
    """Test the AnimalModel class."""

    def test_animal_model_initialization(
        self,
        dummy_animal_data,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test `AnimalModel` initialization."""
        from virtual_ecosystem.core.base_model import BaseModel
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Initialize model
        model = AnimalModel(
            data=dummy_animal_data,
            core_components=fixture_core_components,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
        )

        # In cases where it passes then checks that the object has the right properties
        assert isinstance(model, BaseModel)
        assert model.model_name == "animal"
        assert str(model) == "A animal model instance"
        assert repr(model) == "AnimalModel(update_interval=1209600 seconds)"
        assert isinstance(model.communities, dict)

    @pytest.mark.parametrize(
        "raises,expected_log_entries",
        [
            pytest.param(
                does_not_raise(),
                (
                    (INFO, "Initialised animal.AnimalConsts from config"),
                    (
                        INFO,
                        "Information required to initialise the animal model"
                        " successfully extracted.",
                    ),
                    (INFO, "Replacing data array for 'total_animal_respiration'"),
                    (INFO, "Adding data array for 'population_densities'"),
                    (INFO, "Adding data array for 'decomposed_excrement'"),
                    (INFO, "Adding data array for 'decomposed_carcasses'"),
                ),
                id="success",
            ),
        ],
    )
    def test_generate_animal_model(
        self,
        caplog,
        dummy_animal_data,
        animal_fixture_config,  # Use the config fixture
        raises,
        expected_log_entries,
    ):
        """Test that the function to initialise the animal model behaves as expected."""
        from virtual_ecosystem.core.core_components import CoreComponents
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Build the config object and core components using the fixture
        config = animal_fixture_config
        core_components = CoreComponents(config)
        caplog.clear()

        # Check whether model is initialised (or not) as expected
        with raises:
            model = AnimalModel.from_config(
                data=dummy_animal_data,
                core_components=core_components,
                config=config,
            )

            # Run the update step (once this does something should check output)
            model.update(time_index=0)

        # Print the captured log messages to debug
        for record in caplog.records:
            print(f"Log Level: {record.levelno}, Message: {record.message}")

        # Filter out stochastic log entries
        filtered_records = [
            record
            for record in caplog.records
            if "No individuals in cohort to forage." not in record.message
        ]

        # Create a new caplog object to pass to log_check
        class FilteredCaplog:
            records = filtered_records

        filtered_caplog = FilteredCaplog()

        # Final check that expected logging entries are produced
        log_check(filtered_caplog, expected_log_entries)

        for record in caplog.records:
            print(f"Level: {record.levelname}, Message: {record.message}")

    def test_update_method_sequence(self, mocker, prepared_animal_model_instance):
        """Test update to ensure it runs the community methods in order."""

        # List of methods that should be called in the update sequence
        method_names = [
            "forage_community",
            "migrate_community",
            "birth_community",
            "metamorphose_community",
            "metabolize_community",
            "inflict_non_predation_mortality_community",
            "remove_dead_cohort_community",
            "increase_age_community",
        ]

        # Setup mock methods using spy on the prepared_animal_model_instance itself
        for method_name in method_names:
            mocker.spy(prepared_animal_model_instance, method_name)

        # Call the update method
        prepared_animal_model_instance.update(time_index=0)

        # Verify the order of the method calls
        called_methods = []
        for method_name in method_names:
            method = getattr(prepared_animal_model_instance, method_name)
            # If the method was called, add its name to the list
            if method.spy_return is not None or method.call_count > 0:
                called_methods.append(method_name)

        # Ensure the methods were called in the expected order
        assert (
            called_methods == method_names
        ), f"Methods called in wrong order: {called_methods}"

    def test_update_method_time_index_argument(
        self,
        prepared_animal_model_instance,
    ):
        """Test update to ensure the time index argument does not create an error."""

        time_index = 5
        prepared_animal_model_instance.update(time_index=time_index)

        assert True

    def test_calculate_litter_additions(
        self, functional_group_list_instance, animal_data_for_model_instance
    ):
        """Test that litter additions from animal model are calculated correctly."""

        from virtual_ecosystem.core.config import Config
        from virtual_ecosystem.core.core_components import CoreComponents
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Build the config object and core components
        config = Config(cfg_strings='[core.timing]\nupdate_interval="1 week"')
        core_components = CoreComponents(config)

        # Use it to initialize the model
        model = AnimalModel(
            data=animal_data_for_model_instance,
            core_components=core_components,
            functional_groups=functional_group_list_instance,
        )

        # Update the waste pools
        decomposed_excrement = [3.5e3, 5.6e4, 5.9e4, 2.3e6, 0, 0, 0, 0, 0]
        for energy, excrement_pools in zip(
            decomposed_excrement, model.excrement_pools.values()
        ):
            for excrement_pool in excrement_pools:
                excrement_pool.decomposed_energy = energy

        decomposed_carcasses = [7.5e6, 3.4e7, 8.1e7, 1.7e8, 0, 0, 0, 0, 0]
        for energy, carcass_pools in zip(
            decomposed_carcasses, model.carcass_pools.values()
        ):
            for carcass_pool in carcass_pools:
                carcass_pool.decomposed_energy = energy

        # Calculate litter additions
        litter_additions = model.calculate_litter_additions()

        # Check that litter addition pools are as expected
        assert np.allclose(
            litter_additions["decomposed_excrement"],
            [5e-08, 8e-07, 8.42857e-07, 3.28571e-05, 0, 0, 0, 0, 0],
        )
        assert np.allclose(
            litter_additions["decomposed_carcasses"],
            [1.0714e-4, 4.8571e-4, 1.15714e-3, 2.42857e-3, 0, 0, 0, 0, 0],
        )

        # Check that the function has reset the pools correctly
        for excrement_pools in model.excrement_pools.values():
            assert np.allclose(
                [pool.decomposed_energy for pool in excrement_pools], 0.0
            )

        for carcass_pools in model.carcass_pools.values():
            assert np.allclose([pool.decomposed_energy for pool in carcass_pools], 0.0)

    def test_setup_initializes_total_animal_respiration(
        self,
        prepared_animal_model_instance,
    ):
        """Test that the setup method for the total_animal_respiration variable."""
        import numpy as np
        from xarray import DataArray

        # Check if 'total_animal_respiration' is in the data object
        assert (
            "total_animal_respiration" in prepared_animal_model_instance.data
        ), "'total_animal_respiration' should be initialized in the data object."

        # Retrieve the total_animal_respiration DataArray from the model's data object
        total_animal_respiration = prepared_animal_model_instance.data[
            "total_animal_respiration"
        ]

        # Check that total_animal_respiration is an instance of xarray.DataArray
        assert isinstance(
            total_animal_respiration, DataArray
        ), "'total_animal_respiration' should be an instance of xarray.DataArray."

        # Check the initial values of total_animal_respiration are all zeros
        assert np.all(
            total_animal_respiration.values == 0
        ), "Initial values of 'total_animal_respiration' should be all zeros."

        # Optionally, you can also check the dimensions and coordinates
        # This is useful if your setup method is supposed to initialize the data
        # variable with specific dimensions or coordinates based on your model's
        # structure
        assert (
            "cell_id" in total_animal_respiration.dims
        ), "'cell_id' should be a dimension of 'total_animal_respiration'."

    def test_population_density_initialization(
        self,
        prepared_animal_model_instance,
    ):
        """Test the initialization of the population density data variable."""

        # Check that 'population_densities' is in the data
        assert (
            "population_densities" in prepared_animal_model_instance.data.data.data_vars
        ), "'population_densities' data variable not found in Data object after setup."

        # Retrieve the population densities data variable
        population_densities = prepared_animal_model_instance.data[
            "population_densities"
        ]

        # Check dimensions
        expected_dims = ["community_id", "functional_group_id"]
        assert all(
            dim in population_densities.dims for dim in expected_dims
        ), f"Expected dimensions {expected_dims} not found in 'population_densities'."

        # Check coordinates
        # you should adjust according to actual community IDs and functional group names
        expected_community_ids = list(prepared_animal_model_instance.communities.keys())
        expected_functional_group_names = [
            fg.name for fg in prepared_animal_model_instance.functional_groups
        ]
        assert (
            population_densities.coords["community_id"].values.tolist()
            == expected_community_ids
        ), "Community IDs in 'population_densities' do not match expected values."
        assert (
            population_densities.coords["functional_group_id"].values.tolist()
            == expected_functional_group_names
        ), "Functional group names in 'population_densities' do not match"
        "expected values."

        # Assuming densities have been updated, check if densities are greater than or
        #  equal to zero
        assert np.all(
            population_densities.values >= 0
        ), "Population densities should be greater than or equal to zero."

    def test_update_population_densities(self, prepared_animal_model_instance):
        """Test that the update_population_densities method correctly updates."""

        # Set up expected densities
        expected_densities = {}

        # Manually calculate expected densities based on the cohorts in the community
        for (
            community_id,
            community,
        ) in prepared_animal_model_instance.communities.items():
            expected_densities[community_id] = {}

            # Iterate through the list of cohorts in each community
            for cohort in community:
                fg_name = cohort.functional_group.name
                total_individuals = cohort.individuals
                community_area = prepared_animal_model_instance.data.grid.cell_area
                density = total_individuals / community_area

                # Accumulate density for each functional group
                if fg_name not in expected_densities[community_id]:
                    expected_densities[community_id][fg_name] = 0.0
                expected_densities[community_id][fg_name] += density

        # Run the method under test
        prepared_animal_model_instance.update_population_densities()

        # Retrieve the updated population densities data variable
        population_densities = prepared_animal_model_instance.data[
            "population_densities"
        ]

        # Verify updated densities match expected values
        for community_id in expected_densities:
            for fg_name in expected_densities[community_id]:
                calculated_density = population_densities.sel(
                    community_id=community_id, functional_group_id=fg_name
                ).item()
                expected_density = expected_densities[community_id][fg_name]
                assert calculated_density == pytest.approx(expected_density), (
                    f"Mismatch in density for community {community_id}"
                    " and FG {fg_name}. "
                    f"Expected: {expected_density}, Found: {calculated_density}"
                )

    def test_calculate_density_for_cohort(self, prepared_animal_model_instance, mocker):
        """Test the calculate_density_for_cohort method."""

        mock_cohort = mocker.MagicMock()
        mock_cohort.individuals = 100  # Example number of individuals

        # Set a known community area in the model's data.grid.cell_area
        prepared_animal_model_instance.data.grid.cell_area = 2000  # Example area in m2

        # Expected density = individuals / area
        expected_density = (
            mock_cohort.individuals / prepared_animal_model_instance.data.grid.cell_area
        )

        # Calculate density using the method under test
        calculated_density = (
            prepared_animal_model_instance.calculate_density_for_cohort(mock_cohort)
        )

        # Assert the calculated density matches the expected density
        assert calculated_density == pytest.approx(expected_density), (
            f"Calculated density ({calculated_density}) "
            f"did not match expected density ({expected_density})."
        )

    def test_initialize_communities(
        self,
        animal_data_for_model_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test that `_initialize_communities` generates cohorts."""

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Initialize the model
        model = AnimalModel(
            data=animal_data_for_model_instance,
            core_components=fixture_core_components,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
        )

        # Call the method to initialize communities
        model._initialize_communities(functional_group_list_instance)

        # Assert that cohorts have been generated in each community
        for cell_id in animal_data_for_model_instance.grid.cell_id:
            assert len(model.communities[cell_id]) > 0
            for cohort in model.communities[cell_id]:
                assert isinstance(cohort, AnimalCohort)

        # Assert that cohorts are stored in the model's cohort dictionary
        assert len(model.cohorts) > 0

    def test_abandon_communities(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
    ):
        """Test that `abandon_communities` removes a cohort from all communities."""

        # Assign the cohort to multiple territories (two cells)
        cohort = herbivore_cohort_instance
        cohort.territory = [
            animal_model_instance.data.grid.cell_id[0],
            animal_model_instance.data.grid.cell_id[1],
        ]

        # Add the cohort to multiple communities in the animal model
        animal_model_instance.communities[
            animal_model_instance.data.grid.cell_id[0]
        ].append(cohort)
        animal_model_instance.communities[
            animal_model_instance.data.grid.cell_id[1]
        ].append(cohort)

        # Assert that the cohort is present in the communities before abandonment
        assert (
            cohort
            in animal_model_instance.communities[
                animal_model_instance.data.grid.cell_id[0]
            ]
        )
        assert (
            cohort
            in animal_model_instance.communities[
                animal_model_instance.data.grid.cell_id[1]
            ]
        )

        # Call the abandon_communities method to remove the cohort
        animal_model_instance.abandon_communities(cohort)

        # Assert that the cohort is removed from both communities
        assert (
            cohort
            not in animal_model_instance.communities[
                animal_model_instance.data.grid.cell_id[0]
            ]
        )
        assert (
            cohort
            not in animal_model_instance.communities[
                animal_model_instance.data.grid.cell_id[1]
            ]
        )

    def test_update_community_occupancy(
        self, animal_model_instance, herbivore_cohort_instance, mocker
    ):
        """Test update_community_occupancy."""

        # Mock the get_territory_cells method to return specific territory cells
        mocker.patch.object(
            herbivore_cohort_instance,
            "get_territory_cells",
            return_value=[
                animal_model_instance.data.grid.cell_id[0],
                animal_model_instance.data.grid.cell_id[1],
            ],
        )

        # Spy on the update_territory method to check if it's called
        spy_update_territory = mocker.spy(herbivore_cohort_instance, "update_territory")

        # Choose a centroid key (e.g., the first grid cell)
        centroid_key = animal_model_instance.data.grid.cell_id[0]

        # Call the method to update community occupancy
        animal_model_instance.update_community_occupancy(
            herbivore_cohort_instance, centroid_key
        )

        # Check if the cohort's territory was updated correctly
        spy_update_territory.assert_called_once_with(
            [
                animal_model_instance.data.grid.cell_id[0],
                animal_model_instance.data.grid.cell_id[1],
            ]
        )

        # Check if the cohort has been added to the appropriate communities
        assert (
            herbivore_cohort_instance
            in animal_model_instance.communities[
                animal_model_instance.data.grid.cell_id[0]
            ]
        )
        assert (
            herbivore_cohort_instance
            in animal_model_instance.communities[
                animal_model_instance.data.grid.cell_id[1]
            ]
        )

    def test_migrate(self, animal_model_instance, herbivore_cohort_instance, mocker):
        """Test that `migrate` correctly moves an AnimalCohort between grid cells."""

        # Mock the abandonment and community occupancy update methods
        mock_abandon_communities = mocker.patch.object(
            animal_model_instance, "abandon_communities"
        )
        mock_update_community_occupancy = mocker.patch.object(
            animal_model_instance, "update_community_occupancy"
        )

        # Assign the cohort to a specific starting grid cell
        initial_cell = animal_model_instance.data.grid.cell_id[0]
        destination_cell = animal_model_instance.data.grid.cell_id[1]

        herbivore_cohort_instance.centroid_key = initial_cell
        animal_model_instance.communities[initial_cell].append(
            herbivore_cohort_instance
        )

        # Check that the cohort is in the initial community before migration
        assert (
            herbivore_cohort_instance in animal_model_instance.communities[initial_cell]
        )

        # Call the migrate method to move the cohort to the destination cell
        animal_model_instance.migrate(herbivore_cohort_instance, destination_cell)

        # Assert that the cohort is no longer in the initial community
        assert (
            herbivore_cohort_instance
            not in animal_model_instance.communities[initial_cell]
        )

        # Assert that the cohort is now in the destination community
        assert (
            herbivore_cohort_instance
            in animal_model_instance.communities[destination_cell]
        )

        # Assert that the centroid of the cohort has been updated
        assert herbivore_cohort_instance.centroid_key == destination_cell

        # Check that abandon_communities and update_community_occupancy were called
        mock_abandon_communities.assert_called_once_with(herbivore_cohort_instance)
        mock_update_community_occupancy.assert_called_once_with(
            herbivore_cohort_instance, destination_cell
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
                1.0,
                True,
            ),  # Well-fed juvenile, high probability (1.0), should migrate
            (
                0.5,
                0.0,
                1.0,
                True,
            ),  # Starving juvenile, high probability (1.0), should migrate
            (
                0.5,
                0.0,
                0.0,
                True,
            ),  # Starving juvenile, low probability (0.0), should migrate
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
        animal_model_instance,
        herbivore_cohort_instance,
        mocker,
        mass_ratio,
        age,
        probability_output,
        should_migrate,
    ):
        """Test migrate_community."""

        # Empty the communities and cohorts before the test
        animal_model_instance.communities = {
            cell_id: [] for cell_id in animal_model_instance.communities
        }
        animal_model_instance.cohorts = {}

        # Set up mock cohort with dynamic mass and age values
        cohort_id = herbivore_cohort_instance.id
        herbivore_cohort_instance.age = age
        herbivore_cohort_instance.mass_current = (
            herbivore_cohort_instance.functional_group.adult_mass * mass_ratio
        )
        animal_model_instance.cohorts[cohort_id] = herbivore_cohort_instance

        # Mock `is_below_mass_threshold` to simulate starvation
        is_starving = mass_ratio < 1.0
        mocker.patch.object(
            herbivore_cohort_instance,
            "is_below_mass_threshold",
            return_value=is_starving,
        )

        # Mock the juvenile migration probability based on the test parameter
        mocker.patch.object(
            herbivore_cohort_instance,
            "migrate_juvenile_probability",
            return_value=probability_output,
        )

        # Mock the migrate method
        mock_migrate = mocker.patch.object(animal_model_instance, "migrate")

        # Call the migrate_community method
        animal_model_instance.migrate_community()

        # Check migration behavior
        if should_migrate:
            # Assert migrate was called with correct cohort
            mock_migrate.assert_called_once_with(herbivore_cohort_instance, mocker.ANY)
        else:
            # Assert migrate was NOT called
            mock_migrate.assert_not_called()

        # Assert that starvation check was applied
        herbivore_cohort_instance.is_below_mass_threshold.assert_called_once()

    @pytest.mark.parametrize(
        "is_cohort_in_model, expected_exception",
        [
            (True, None),  # Cohort exists, should be removed
            (False, KeyError),  # Cohort does not exist, KeyError expected
        ],
    )
    def test_remove_dead_cohort(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        mocker,
        is_cohort_in_model,
        expected_exception,
    ):
        """Test the remove_dead_cohort method for both success and error cases."""

        # Setup cohort ID and mock territory
        cohort_id = herbivore_cohort_instance.id
        herbivore_cohort_instance.territory = [
            1,
            2,
        ]  # Simulate a territory covering two cells

        # If cohort should exist, add it to model's cohorts and communities
        if is_cohort_in_model:
            animal_model_instance.cohorts[cohort_id] = herbivore_cohort_instance
            animal_model_instance.communities = {
                1: [herbivore_cohort_instance],
                2: [herbivore_cohort_instance],
            }

        # If cohort doesn't exist, make sure it's not in the model
        else:
            animal_model_instance.cohorts = {}

        if expected_exception:
            # Expect KeyError if cohort does not exist
            with pytest.raises(
                KeyError, match=f"Cohort with ID {cohort_id} does not exist."
            ):
                animal_model_instance.remove_dead_cohort(herbivore_cohort_instance)
        else:
            # Call the method to remove the cohort if it exists
            animal_model_instance.remove_dead_cohort(herbivore_cohort_instance)

            # Assert that the cohort has been removed from both communities
            assert herbivore_cohort_instance not in animal_model_instance.communities[1]
            assert herbivore_cohort_instance not in animal_model_instance.communities[2]

            # Assert that the cohort has been removed from the model's cohorts
            assert cohort_id not in animal_model_instance.cohorts

    @pytest.mark.parametrize(
        "cohort_individuals, should_be_removed",
        [
            (0, True),  # Cohort with 0 individuals, should be removed
            (10, False),  # Cohort with >0 individuals, should not be removed
        ],
    )
    def test_remove_dead_cohort_community(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        mocker,
        cohort_individuals,
        should_be_removed,
    ):
        """Test remove_dead_cohort_community for both dead and alive cohorts."""

        # Set up cohort with individuals count
        herbivore_cohort_instance.individuals = cohort_individuals
        cohort_id = herbivore_cohort_instance.id

        # Add the cohort to the model's cohorts and communities
        animal_model_instance.cohorts[cohort_id] = herbivore_cohort_instance
        herbivore_cohort_instance.territory = [1, 2]  # Simulate a territory
        animal_model_instance.communities = {
            1: [herbivore_cohort_instance],
            2: [herbivore_cohort_instance],
        }

        # Mock remove_dead_cohort to track when it is called
        mock_remove_dead_cohort = mocker.patch.object(
            animal_model_instance, "remove_dead_cohort"
        )

        # Call the method to remove dead cohorts from the community
        animal_model_instance.remove_dead_cohort_community()

        if should_be_removed:
            # If the cohort should be removed, check if remove_dead_cohort was called
            mock_remove_dead_cohort.assert_called_once_with(herbivore_cohort_instance)
            assert (
                herbivore_cohort_instance.is_alive is False
            )  # Cohort should be marked as not alive
        else:
            # If cohort should not be removed, ensure remove_dead_cohort wasn't called
            mock_remove_dead_cohort.assert_not_called()
            assert (
                herbivore_cohort_instance.is_alive is True
            )  # Cohort should still be alive

    @pytest.mark.parametrize(
        "functional_group_type, reproductive_mass, mass_current, birth_mass,"
        "individuals, is_semelparous, expected_offspring",
        [
            # Test case for semelparous organism
            ("herbivore", 100.0, 1000.0, 10.0, 5, False, 50),
            # Test case for iteroparous organism
            ("butterfly", 50.0, 200.0, 0.5, 50, True, 15000),
        ],
    )
    def test_birth(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        butterfly_cohort_instance,
        functional_group_type,
        reproductive_mass,
        mass_current,
        birth_mass,
        individuals,
        is_semelparous,
        expected_offspring,
    ):
        """Test the birth method with semelparous and iteroparous cohorts."""

        from uuid import uuid4

        # Choose the appropriate cohort instance based on the test case
        parent_cohort = (
            herbivore_cohort_instance
            if functional_group_type == "herbivore"
            else butterfly_cohort_instance
        )

        # Mock the attributes of the parent cohort for the test case
        parent_cohort.reproductive_mass = reproductive_mass
        parent_cohort.mass_current = mass_current
        parent_cohort.functional_group.birth_mass = birth_mass
        parent_cohort.individuals = individuals
        parent_cohort.functional_group.reproductive_type = (
            "semelparous" if is_semelparous else "iteroparous"
        )
        parent_cohort.functional_group.offspring_functional_group = (
            parent_cohort.functional_group.name
        )

        # Set a mock cohort ID
        cohort_id = uuid4()
        parent_cohort.id = cohort_id

        # Add the parent cohort to the model's cohorts dictionary
        animal_model_instance.cohorts[cohort_id] = parent_cohort

        # Store the initial number of cohorts in the model
        initial_num_cohorts = len(animal_model_instance.cohorts)

        # Call the birth method (without mocking `get_functional_group_by_name`)
        animal_model_instance.birth(parent_cohort)

        # Check if the parent cohort is dead (only if semelparous)
        if is_semelparous:
            assert parent_cohort.is_alive is False
        else:
            assert parent_cohort.is_alive is True

        # Check that reproductive mass is reset
        assert parent_cohort.reproductive_mass == 0.0

        # Check the number of offspring generated and added to the cohort list
        if is_semelparous:
            # For semelparous organisms, the parent dies and the offspring cohort
            # replaces it
            assert (
                len(animal_model_instance.cohorts) == initial_num_cohorts
            ), f"Expected {initial_num_cohorts} cohorts but"
            " found {len(animal_model_instance.cohorts)}"
        else:
            # For iteroparous organisms, the parent survives and the offspring is added
            assert (
                len(animal_model_instance.cohorts) == initial_num_cohorts + 1
            ), f"Expected {initial_num_cohorts + 1} cohorts but"
            " found {len(animal_model_instance.cohorts)}"

        # Get the offspring cohort (assuming it was added correctly)
        offspring_cohort = list(animal_model_instance.cohorts.values())[-1]

        # Validate the attributes of the offspring cohort
        assert (
            offspring_cohort.functional_group.name
            == parent_cohort.functional_group.name
        )
        assert (
            offspring_cohort.mass_current == parent_cohort.functional_group.birth_mass
        )
        assert offspring_cohort.individuals == expected_offspring

    def test_forage_community(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        predator_cohort_instance,
        mocker,
    ):
        """Test that forage_cohort is called correctly."""

        from virtual_ecosystem.models.animal.animal_traits import DietType

        # Mock the methods for herbivore and predator cohorts using the mocker fixture
        mock_forage_herbivore = mocker.Mock()
        mock_forage_predator = mocker.Mock()
        mock_get_excrement_pools_herbivore = mocker.Mock(
            return_value=["excrement_pools_herbivore"]
        )
        mock_get_excrement_pools_predator = mocker.Mock(
            return_value=["excrement_pools_predator"]
        )
        mock_get_plant_resources = mocker.Mock(return_value=["plant_resources"])
        mock_get_prey = mocker.Mock(return_value=["prey"])

        # Set up herbivore cohort
        herbivore_cohort_instance.functional_group.diet = DietType.HERBIVORE
        mocker.patch.object(
            herbivore_cohort_instance, "get_plant_resources", mock_get_plant_resources
        )
        mocker.patch.object(
            herbivore_cohort_instance, "get_prey", mocker.Mock()
        )  # Should not be called for herbivores
        mocker.patch.object(
            herbivore_cohort_instance,
            "get_excrement_pools",
            mock_get_excrement_pools_herbivore,
        )
        mocker.patch.object(
            herbivore_cohort_instance, "forage_cohort", mock_forage_herbivore
        )

        # Set up predator cohort
        predator_cohort_instance.functional_group.diet = DietType.CARNIVORE
        mocker.patch.object(
            predator_cohort_instance, "get_plant_resources", mocker.Mock()
        )  # Should not be called for predators
        mocker.patch.object(predator_cohort_instance, "get_prey", mock_get_prey)
        mocker.patch.object(
            predator_cohort_instance,
            "get_excrement_pools",
            mock_get_excrement_pools_predator,
        )
        mocker.patch.object(
            predator_cohort_instance, "forage_cohort", mock_forage_predator
        )

        # Add cohorts to the animal_model_instance
        animal_model_instance.cohorts = {
            "herbivore": herbivore_cohort_instance,
            "predator": predator_cohort_instance,
        }

        # Run the forage_community method
        animal_model_instance.forage_community()

        # Verify that herbivores forage plant resources and not animal prey
        mock_get_plant_resources.assert_called_once_with(
            animal_model_instance.plant_resources
        )
        herbivore_cohort_instance.get_prey.assert_not_called()
        mock_forage_herbivore.assert_called_once_with(
            plant_list=["plant_resources"],
            animal_list=[],
            excrement_pools=["excrement_pools_herbivore"],
            carcass_pools=animal_model_instance.carcass_pools,
        )

        # Verify that predators forage prey and not plant resources
        mock_get_prey.assert_called_once_with(animal_model_instance.communities)
        predator_cohort_instance.get_plant_resources.assert_not_called()
        mock_forage_predator.assert_called_once_with(
            plant_list=[],
            animal_list=["prey"],
            excrement_pools=["excrement_pools_predator"],
            carcass_pools=animal_model_instance.carcass_pools,
        )

    def test_metabolize_community(
        self, animal_model_instance, dummy_animal_data, mocker
    ):
        """Test metabolize_community using real data from fixture."""

        from numpy import timedelta64

        # Assign the data from the fixture to the animal model
        animal_model_instance.data = dummy_animal_data
        air_temperature_data = dummy_animal_data["air_temperature"]

        print(air_temperature_data.shape)

        # Create mock cohorts and their behaviors
        mock_cohort_1 = mocker.Mock()
        mock_cohort_2 = mocker.Mock()

        # Mock return values for metabolize and respire
        mock_cohort_1.metabolize.return_value = (
            10.0  # Metabolic waste mass for cohort 1
        )
        mock_cohort_2.metabolize.return_value = (
            15.0  # Metabolic waste mass for cohort 2
        )
        mock_cohort_1.respire.return_value = 5.0  # Carbonaceous waste for cohort 1
        mock_cohort_2.respire.return_value = 8.0  # Carbonaceous waste for cohort 2

        # Setup the community and excrement pools in the animal model
        animal_model_instance.communities = {
            1: [mock_cohort_1, mock_cohort_2],  # Community in cell 1 with two cohorts
            2: [],  # Empty community in cell 2
        }
        animal_model_instance.excrement_pools = {
            1: "excrement_pool_1",
            2: "excrement_pool_2",
        }

        # Run the metabolize_community method
        dt = timedelta64(1, "D")  # 1 day as the time delta
        animal_model_instance.metabolize_community(dt)

        # Assertions for the first cohort in cell 1
        mock_cohort_1.metabolize.assert_called_once_with(
            16.145945, dt
        )  # Temperature for cell 1 from the fixture (25.0)
        mock_cohort_1.respire.assert_called_once_with(
            10.0
        )  # Metabolic waste returned by metabolize
        mock_cohort_1.excrete.assert_called_once_with(10.0, "excrement_pool_1")

        # Assertions for the second cohort in cell 1
        mock_cohort_2.metabolize.assert_called_once_with(
            16.145945, dt
        )  # Temperature for cell 1 from the fixture (25.0)
        mock_cohort_2.respire.assert_called_once_with(
            15.0
        )  # Metabolic waste returned by metabolize
        mock_cohort_2.excrete.assert_called_once_with(15.0, "excrement_pool_1")

        # Assert total animal respiration was updated for cell 1
        total_animal_respiration = animal_model_instance.data[
            "total_animal_respiration"
        ]
        assert total_animal_respiration.loc[{"cell_id": 1}] == 13.0  # 5.0 + 8.0

        # Ensure no cohort methods were called for the empty community in cell 2
        mock_cohort_1.reset_mock()
        mock_cohort_2.reset_mock()
        mock_cohort_1.metabolize.assert_not_called()
        mock_cohort_2.metabolize.assert_not_called()

    def test_increase_age_community(self, animal_model_instance, mocker):
        """Test increase_age."""

        from numpy import timedelta64

        # Create mock cohorts
        mock_cohort_1 = mocker.Mock()
        mock_cohort_2 = mocker.Mock()

        # Setup the animal model with mock cohorts
        animal_model_instance.cohorts = {
            "cohort_1": mock_cohort_1,
            "cohort_2": mock_cohort_2,
        }

        # Define the time delta
        dt = timedelta64(10, "D")  # 10 days

        # Run the increase_age_community method
        animal_model_instance.increase_age_community(dt)

        # Assert that increase_age was called with the correct time delta
        mock_cohort_1.increase_age.assert_called_once_with(dt)
        mock_cohort_2.increase_age.assert_called_once_with(dt)

    def test_inflict_non_predation_mortality_community(
        self, animal_model_instance, mocker
    ):
        """Test inflict_non_predation_mortality_community."""

        from numpy import timedelta64

        # Create mock cohorts
        mock_cohort_1 = mocker.Mock()
        mock_cohort_2 = mocker.Mock()

        # Setup the animal model with mock cohorts
        animal_model_instance.cohorts = {
            "cohort_1": mock_cohort_1,
            "cohort_2": mock_cohort_2,
        }

        # Mock return values for cohort methods
        mock_cohort_1.get_carcass_pools.return_value = "carcass_pool_1"
        mock_cohort_2.get_carcass_pools.return_value = "carcass_pool_2"

        # Define the number of individuals
        mock_cohort_1.individuals = 100
        mock_cohort_2.individuals = 0  # This cohort should be marked as dead

        # Mock the remove_dead_cohort method
        mock_remove_dead_cohort = mocker.patch.object(
            animal_model_instance, "remove_dead_cohort"
        )

        # Define the time delta
        dt = timedelta64(10, "D")  # 10 days

        # Run the inflict_non_predation_mortality_community method
        animal_model_instance.inflict_non_predation_mortality_community(dt)

        # Calculate the number of days from dt
        number_of_days = float(dt / timedelta64(1, "D"))

        # Assert that inflict_non_predation_mortality called with the correct arguments
        mock_cohort_1.inflict_non_predation_mortality.assert_called_once_with(
            number_of_days, "carcass_pool_1"
        )
        mock_cohort_2.inflict_non_predation_mortality.assert_called_once_with(
            number_of_days, "carcass_pool_2"
        )

        # Assert that remove_dead_cohort was called for the cohort with zero individuals
        mock_remove_dead_cohort.assert_called_once_with(mock_cohort_2)

        # Ensure that the cohort with zero individuals is marked as dead
        assert mock_cohort_2.is_alive is False

        # Ensure that the cohort with individuals is not marked as dead
        assert mock_cohort_1.is_alive is not False

    def test_metamorphose(
        self,
        animal_model_instance,
        caterpillar_cohort_instance,
    ):
        """Test metamorphose.

        TODO: add broader assertions


        """

        from math import ceil

        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Clear the cohorts list to ensure it is empty
        animal_model_instance.cohorts = {}

        # Add the caterpillar cohort to the animal model's cohorts
        animal_model_instance.cohorts[caterpillar_cohort_instance.id] = (
            caterpillar_cohort_instance
        )

        # Set the larval cohort (caterpillar) properties
        caterpillar_cohort_instance.functional_group.offspring_functional_group = (
            "butterfly"
        )

        initial_individuals = 100
        caterpillar_cohort_instance.individuals = initial_individuals

        # Calculate the expected number of individuals lost due to mortality
        number_dead = ceil(
            initial_individuals
            * caterpillar_cohort_instance.constants.metamorph_mortality
        )

        # Set up functional groups in the animal model instance
        butterfly_functional_group = get_functional_group_by_name(
            animal_model_instance.functional_groups,
            caterpillar_cohort_instance.functional_group.offspring_functional_group,
        )

        # Ensure the butterfly functional group is found
        assert (
            butterfly_functional_group is not None
        ), "Butterfly functional group not found"

        # Run the metamorphose method on the caterpillar cohort
        animal_model_instance.metamorphose(caterpillar_cohort_instance)

        # Assert that the number of individuals in the caterpillar cohort was reduced
        assert (
            caterpillar_cohort_instance.individuals == initial_individuals - number_dead
        ), "Caterpillar cohort's individuals count is incorrect after metamorphosis"

        # Assert that a new butterfly cohort was created from the caterpillar
        adult_cohort = next(
            (
                cohort
                for cohort in animal_model_instance.cohorts.values()
                if cohort.functional_group == butterfly_functional_group
            ),
            None,
        )
        assert adult_cohort is not None, "Butterfly cohort was not created"

        # Assert that the number of individuals in the butterfly cohort is correct
        assert (
            adult_cohort.individuals == caterpillar_cohort_instance.individuals
        ), "Butterfly cohort's individuals count does not match the expected value"

        # Assert that the caterpillar cohort is marked as dead and removed
        assert (
            not caterpillar_cohort_instance.is_alive
        ), "Caterpillar cohort should be marked as dead"
        assert (
            caterpillar_cohort_instance not in animal_model_instance.cohorts.values()
        ), "Caterpillar cohort should be removed from the model"

    def test_metamorphose_community(self, animal_model_instance, mocker):
        """Test metamorphose_community."""

        from virtual_ecosystem.models.animal.animal_traits import DevelopmentType

        # Create mock cohorts
        mock_cohort_1 = mocker.Mock()
        mock_cohort_2 = mocker.Mock()
        mock_cohort_3 = mocker.Mock()

        # Setup the animal model with mock cohorts
        animal_model_instance.cohorts = {
            "cohort_1": mock_cohort_1,
            "cohort_2": mock_cohort_2,
            "cohort_3": mock_cohort_3,
        }

        # Set the properties for each cohort
        mock_cohort_1.functional_group.development_type = DevelopmentType.INDIRECT
        mock_cohort_1.mass_current = 20.0
        mock_cohort_1.functional_group.adult_mass = 15.0  # Ready for metamorphosis

        mock_cohort_2.functional_group.development_type = DevelopmentType.INDIRECT
        mock_cohort_2.mass_current = 10.0
        mock_cohort_2.functional_group.adult_mass = 15.0  # Not ready for metamorphosis

        mock_cohort_3.functional_group.development_type = DevelopmentType.DIRECT
        mock_cohort_3.mass_current = 20.0
        mock_cohort_3.functional_group.adult_mass = (
            15.0  # Direct development, should not metamorphose
        )

        # Mock the metamorphose method
        mock_metamorphose = mocker.patch.object(animal_model_instance, "metamorphose")

        # Run the metamorphose_community method
        animal_model_instance.metamorphose_community()

        # Assert that metamorphose was called only for cohort that is ready and indirect
        mock_metamorphose.assert_called_once_with(mock_cohort_1)

        # Assert that the other cohorts did not trigger metamorphosis
        mock_metamorphose.assert_called_once()  # Ensure it was called exactly once
