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
                    (INFO, "Adding data array for 'total_animal_respiration'"),
                    (INFO, "Adding data array for 'population_densities'"),
                    (INFO, "Adding data array for 'decomposed_excrement_carbon'"),
                    (INFO, "Adding data array for 'decomposed_excrement_nitrogen'"),
                    (INFO, "Adding data array for 'decomposed_excrement_phosphorus'"),
                    (INFO, "Adding data array for 'decomposed_carcasses_carbon'"),
                    (INFO, "Adding data array for 'decomposed_carcasses_nitrogen'"),
                    (INFO, "Adding data array for 'decomposed_carcasses_phosphorus'"),
                    (
                        INFO,
                        "Adding data array for 'litter_consumption_above_metabolic'",
                    ),
                    (
                        INFO,
                        "Adding data array for 'litter_consumption_above_structural'",
                    ),
                    (INFO, "Adding data array for 'litter_consumption_woody'"),
                    (
                        INFO,
                        "Adding data array for 'litter_consumption_below_metabolic'",
                    ),
                    (
                        INFO,
                        "Adding data array for 'litter_consumption_below_structural'",
                    ),
                    (INFO, "Adding data array for 'herbivory_waste_leaf_carbon'"),
                    (INFO, "Adding data array for 'herbivory_waste_leaf_nitrogen'"),
                    (INFO, "Adding data array for 'herbivory_waste_leaf_phosphorus'"),
                    (INFO, "Adding data array for 'herbivory_waste_leaf_lignin'"),
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
            "update_community_bookkeeping",
            "update_cohort_bookkeeping",
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
        assert called_methods == method_names, (
            f"Methods called in wrong order: {called_methods}"
        )

    def test_update_method_time_index_argument(
        self,
        prepared_animal_model_instance,
    ):
        """Test update to ensure the time index argument does not create an error."""

        time_index = 5
        prepared_animal_model_instance.update(time_index=time_index)

        assert True

    def test_setup_initializes_total_animal_respiration(
        self,
        prepared_animal_model_instance,
    ):
        """Test that the setup method for the total_animal_respiration variable."""
        import numpy as np
        from xarray import DataArray

        # Check if 'total_animal_respiration' is in the data object
        assert "total_animal_respiration" in prepared_animal_model_instance.data, (
            "'total_animal_respiration' should be initialized in the data object."
        )

        # Retrieve the total_animal_respiration DataArray from the model's data object
        total_animal_respiration = prepared_animal_model_instance.data[
            "total_animal_respiration"
        ]

        # Check that total_animal_respiration is an instance of xarray.DataArray
        assert isinstance(total_animal_respiration, DataArray), (
            "'total_animal_respiration' should be an instance of xarray.DataArray."
        )

        # Check the initial values of total_animal_respiration are all zeros
        assert np.all(total_animal_respiration.values == 0), (
            "Initial values of 'total_animal_respiration' should be all zeros."
        )

        # Optionally, you can also check the dimensions and coordinates
        # This is useful if your setup method is supposed to initialize the data
        # variable with specific dimensions or coordinates based on your model's
        # structure
        assert "cell_id" in total_animal_respiration.dims, (
            "'cell_id' should be a dimension of 'total_animal_respiration'."
        )

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
        assert all(dim in population_densities.dims for dim in expected_dims), (
            f"Expected dimensions {expected_dims} not found in 'population_densities'."
        )

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
        assert np.all(population_densities.values >= 0), (
            "Population densities should be greater than or equal to zero."
        )

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

    @pytest.mark.parametrize(
        "density_key, expected_key, c_n_key, c_p_key, expect_error",
        [
            ("zeros", "zeros", "ones", "ones", False),
            ("small", "small", "tens", "twenties", False),
            ("large", "large", "fifties", "hundreds", False),
            ("negative", "zeros", "tens", "twenties", True),
            ("medium", "medium", "huge", "huge", False),
        ],
    )
    def test_populate_litter_pools(
        self,
        animal_model_instance,
        density_key,
        expected_key,
        c_n_key,
        c_p_key,
        expect_error,
    ):
        """Test litter pool population with full structure-aware validation."""
        import numpy as np
        import xarray as xr

        from virtual_ecosystem.models.animal.decay import LitterPool

        value_map = {
            "zeros": np.zeros(9),
            "small": np.full(9, 1e-10),
            "large": np.full(9, 1e5),
            "negative": np.full(9, -1.0),
            "medium": np.full(9, 10.0),
            "ones": np.ones(9),
            "tens": np.full(9, 10.0),
            "twenties": np.full(9, 20.0),
            "fifties": np.full(9, 50.0),
            "hundreds": np.full(9, 100.0),
            "huge": np.full(9, 1e6),
        }

        cell_area = animal_model_instance.data.grid.cell_area
        density_values = xr.DataArray(value_map[density_key], dims=["cell_id"])
        expected_mass = xr.DataArray(
            value_map[expected_key] * cell_area, dims=["cell_id"]
        )
        c_n_ratio = xr.DataArray(value_map[c_n_key], dims=["cell_id"])
        c_p_ratio = xr.DataArray(value_map[c_p_key], dims=["cell_id"])

        pool_names = [
            "above_metabolic",
            "above_structural",
            "woody",
            "below_metabolic",
            "below_structural",
        ]
        for name in pool_names:
            animal_model_instance.data[f"litter_pool_{name}"] = density_values
            animal_model_instance.data[f"c_n_ratio_{name}"] = c_n_ratio
            animal_model_instance.data[f"c_p_ratio_{name}"] = c_p_ratio

        if expect_error:
            with pytest.raises(ValueError):
                animal_model_instance.populate_litter_pools()
        else:
            litter_pools = animal_model_instance.populate_litter_pools()
            expected_pool_set = set(pool_names)

            for cell_id, pool_dict in litter_pools.items():
                assert set(pool_dict.keys()) == expected_pool_set
                for pool_name, pool in pool_dict.items():
                    assert isinstance(pool, LitterPool)
                    assert pool.pool_name == pool_name

                    expected_carbon = expected_mass.values[cell_id]
                    expected_n = expected_carbon / c_n_ratio.values[cell_id]
                    expected_p = expected_carbon / c_p_ratio.values[cell_id]

                    assert np.isclose(pool.mass_current, expected_carbon)
                    assert np.isclose(pool.mass_cnp.nitrogen, expected_n)
                    assert np.isclose(pool.mass_cnp.phosphorus, expected_p)

    def test_calculate_total_litter_consumption(
        self,
        litter_data_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test calculation of total consumption of litter by animals is correct."""
        from copy import deepcopy

        import numpy as np

        from virtual_ecosystem.models.animal.animal_model import AnimalModel
        from virtual_ecosystem.models.animal.decay import LitterPool

        # Create AnimalModel instance with test data
        model = AnimalModel(
            data=litter_data_instance,
            core_components=fixture_core_components,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
        )

        # Copy data and simulate biomass loss from each litter pool
        new_data = deepcopy(litter_data_instance)
        new_data["litter_pool_above_metabolic"] = (
            litter_data_instance["litter_pool_above_metabolic"] - 0.03
        )
        new_data["litter_pool_above_structural"] = (
            litter_data_instance["litter_pool_above_structural"] - 0.04
        )
        new_data["litter_pool_woody"] = litter_data_instance["litter_pool_woody"] - 1.2
        new_data["litter_pool_below_metabolic"] = (
            litter_data_instance["litter_pool_below_metabolic"] - 0.06
        )
        new_data["litter_pool_below_structural"] = (
            litter_data_instance["litter_pool_below_structural"] - 0.01
        )

        pool_names = [
            "above_metabolic",
            "above_structural",
            "woody",
            "below_metabolic",
            "below_structural",
        ]

        cell_ids = fixture_core_components.grid.cell_id
        cell_area = fixture_core_components.grid.cell_area

        # Construct the nested dict: cell_id → pool_name → LitterPool
        new_litter_pools = {
            cid: {
                pool_name: LitterPool(
                    pool_name=pool_name,
                    cell_id=cid,
                    data=new_data,
                    cell_area=cell_area,
                )
                for pool_name in pool_names
            }
            for cid in cell_ids
        }

        # Run consumption calculation
        consumption = model.calculate_total_litter_consumption(
            litter_pools=new_litter_pools
        )

        # Validate consumption matches expected loss per cell
        for pool_name, expected_loss in [
            ("above_metabolic", 0.03),
            ("above_structural", 0.04),
            ("woody", 1.2),
            ("below_metabolic", 0.06),
            ("below_structural", 0.01),
        ]:
            expected = expected_loss * np.ones(len(cell_ids))
            actual = consumption[f"litter_consumption_{pool_name}"].values
            assert np.allclose(actual, expected), (
                f"Mismatch in {pool_name} consumption."
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
        mocker,
        animal_data_for_model_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
    ):
        """Test that `_initialize_communities` generates cohorts."""

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        mocker.patch(
            "virtual_ecosystem.models.animal.animal_model.AnimalModel.populate_litter_pools",
            return_value={},
        )

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
        assert len(model.active_cohorts) > 0

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
        mocker,
        mass_ratio,
        age,
        probability_output,
        should_migrate,
        animal_model_instance,
        herbivore_cohort_instance,
    ):
        """Test migrate_community method in the AnimalModel class."""

        # Empty the communities and cohorts before the test
        animal_model_instance.communities = {
            cell_id: [] for cell_id in animal_model_instance.communities
        }
        animal_model_instance.active_cohorts = {}

        # Set up mock cohort with dynamic mass and age values
        cohort = herbivore_cohort_instance
        cohort.age = age
        cohort.mass_cnp.carbon = (
            cohort.functional_group.adult_mass
            * mass_ratio
            * cohort.cnp_proportions["carbon"]
        )
        cohort.mass_cnp.nitrogen = (
            cohort.functional_group.adult_mass
            * mass_ratio
            * cohort.cnp_proportions["nitrogen"]
        )
        cohort.mass_cnp.phosphorus = (
            cohort.functional_group.adult_mass
            * mass_ratio
            * cohort.cnp_proportions["phosphorus"]
        )

        cohort_id = cohort.id
        animal_model_instance.active_cohorts[cohort_id] = cohort

        # Mock `is_below_mass_threshold` to simulate starvation
        is_starving = mass_ratio < 1.0
        mocker.patch.object(
            cohort,
            "is_below_mass_threshold",
            return_value=is_starving,
        )

        # Mock the juvenile migration probability based on the test parameter
        mocker.patch.object(
            cohort,
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
            mock_migrate.assert_called_once_with(cohort, mocker.ANY)
        else:
            # Assert migrate was NOT called
            mock_migrate.assert_not_called()

        # Assert that starvation check was applied
        cohort.is_below_mass_threshold.assert_called_once()

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
            animal_model_instance.active_cohorts[cohort_id] = herbivore_cohort_instance
            animal_model_instance.communities = {
                1: [herbivore_cohort_instance],
                2: [herbivore_cohort_instance],
            }

        # If cohort doesn't exist, make sure it's not in the model
        else:
            animal_model_instance.active_cohorts = {}

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
            assert cohort_id not in animal_model_instance.active_cohorts

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
        animal_model_instance.active_cohorts[cohort_id] = herbivore_cohort_instance
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
        "offspring_count, expect_creation_called",
        [
            (3, True),  # Offspring possible, all helpers should be called
            (1, True),  # Exactly one offspring
            (0, False),  # No offspring possible, creation and updates skipped
        ],
    )
    def test_birth(
        self,
        mocker,
        animal_model_instance,
        herbivore_cohort_instance,
        offspring_count,
        expect_creation_called,
    ):
        """Test birth calls helpers correctly based on offspring count."""

        # Mock the helpers via mocker (pytest-mock compliant)
        mock_calculate_mass = mocker.patch.object(
            animal_model_instance, "calculate_total_reproductive_mass"
        )
        mock_calculate_count = mocker.patch.object(
            animal_model_instance, "calculate_offspring_count"
        )
        mock_create_offspring = mocker.patch.object(
            animal_model_instance, "create_offspring"
        )
        mock_handle_updates = mocker.patch.object(
            animal_model_instance, "handle_post_birth_parent_updates"
        )

        # Set return values for helpers
        mock_calculate_mass.return_value = {
            "carbon": 1.0,
            "nitrogen": 0.1,
            "phosphorus": 0.05,
        }
        mock_calculate_count.return_value = offspring_count

        # Run the method
        animal_model_instance.birth(herbivore_cohort_instance)

        # Check calls
        mock_calculate_mass.assert_called_once_with(herbivore_cohort_instance)
        mock_calculate_count.assert_called_once_with(
            herbivore_cohort_instance, mock_calculate_mass.return_value
        )

        if expect_creation_called:
            mock_create_offspring.assert_called_once_with(
                herbivore_cohort_instance, offspring_count
            )
            mock_handle_updates.assert_called_once_with(
                herbivore_cohort_instance, offspring_count
            )
        else:
            mock_create_offspring.assert_not_called()
            mock_handle_updates.assert_not_called()

    @pytest.mark.parametrize(
        "semelparous_loss, initial_reproductive_mass, expected_total_mass",
        [
            # Case 1: No semelparous loss (iteroparous species)
            (
                {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0},
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
            ),
            # Case 2: Semelparous species with mass loss contribution
            (
                {"carbon": 0.2, "nitrogen": 0.05, "phosphorus": 0.01},
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {"carbon": 0.7, "nitrogen": 0.15, "phosphorus": 0.06},
            ),
        ],
    )
    def test_calculate_total_reproductive_mass(
        self,
        mocker,
        animal_model_instance,
        herbivore_cohort_instance,
        semelparous_loss,
        initial_reproductive_mass,
        expected_total_mass,
    ):
        """Test calculation of total reproductive mass."""
        from virtual_ecosystem.models.animal.cnp import CNP

        # Mock the parent cohort's reproductive mass CNP
        herbivore_cohort_instance.reproductive_mass_cnp = CNP(
            **initial_reproductive_mass
        )

        # Mock the semelparous loss calculation
        mocker.patch.object(
            animal_model_instance,
            "calculate_semelparous_mass_loss",
            return_value=semelparous_loss,
        )

        # Run the method
        result = animal_model_instance.calculate_total_reproductive_mass(
            herbivore_cohort_instance
        )

        # Check result using pytest.approx for floats
        assert result["carbon"] == pytest.approx(expected_total_mass["carbon"])
        assert result["nitrogen"] == pytest.approx(expected_total_mass["nitrogen"])
        assert result["phosphorus"] == pytest.approx(expected_total_mass["phosphorus"])

    @pytest.mark.parametrize(
        "birth_mass_cnp, reproductive_mass, individuals, expected_offspring",
        [
            # Case 1: Exactly 1 offspring per parent
            (
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                1,
                1,
            ),
            # Case 2: Exactly 2 offspring per parent
            (
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {"carbon": 1.0, "nitrogen": 0.2, "phosphorus": 0.1},
                1,
                2,
            ),
            # Case 3: Not enough for any offspring
            (
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {"carbon": 0.2, "nitrogen": 0.05, "phosphorus": 0.02},
                1,
                0,
            ),
            # Case 4: Multiple parents, each able to make 2 offspring
            (
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {"carbon": 1.0, "nitrogen": 0.2, "phosphorus": 0.1},
                2,
                4,
            ),
            # Limiting nutrient - phosphorus
            (
                {"carbon": 0.5, "nitrogen": 0.1, "phosphorus": 0.05},
                {
                    "carbon": 10.0,
                    "nitrogen": 10.0,
                    "phosphorus": 0.1,
                },  # 1 parent, P limits to 2 offspring
                1,
                2,
            ),
        ],
    )
    def test_calculate_offspring_count(
        self,
        mocker,
        animal_model_instance,
        herbivore_cohort_instance,
        birth_mass_cnp,
        reproductive_mass,
        individuals,
        expected_offspring,
    ):
        """Test offspring count calculation."""
        # Set parent cohort individuals directly
        herbivore_cohort_instance.individuals = individuals

        # Mock `calculate_birth_mass_cnp` to return the test birth mass CNP
        mocker.patch.object(
            animal_model_instance,
            "calculate_birth_mass_cnp",
            return_value=(
                birth_mass_cnp["carbon"],
                birth_mass_cnp["nitrogen"],
                birth_mass_cnp["phosphorus"],
            ),
        )

        # Run the method
        result = animal_model_instance.calculate_offspring_count(
            herbivore_cohort_instance, reproductive_mass
        )

        # Check result
        assert result == expected_offspring

    @pytest.mark.parametrize(
        "reproductive_type, initial_reproductive_mass, offspring_count, birth_mass_cnp,"
        "expected_remaining_mass, expect_semelparous_death_called",
        [
            # Iteroparous parent - reproductive mass reduces but parent survives
            (
                "iteroparous",
                {"carbon": 2.0, "nitrogen": 0.5, "phosphorus": 0.2},
                2,
                (0.5, 0.1, 0.05),  # Per offspring birth mass C, N, P
                {"carbon": 1.0, "nitrogen": 0.3, "phosphorus": 0.1},
                False,
            ),
            # Semelparous parent - reproductive mass reduces and parent dies
            (
                "semelparous",
                {"carbon": 2.0, "nitrogen": 0.5, "phosphorus": 0.2},
                2,
                (0.5, 0.1, 0.05),
                {"carbon": 1.0, "nitrogen": 0.3, "phosphorus": 0.1},
                True,
            ),
            # More offspring than available reproductive mass - cap at available mass
            (
                "iteroparous",
                {"carbon": 0.5, "nitrogen": 0.2, "phosphorus": 0.1},
                5,
                (0.5, 0.1, 0.05),
                {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0},
                False,
            ),
            # No offspring at all - nothing should change
            (
                "iteroparous",
                {"carbon": 2.0, "nitrogen": 0.5, "phosphorus": 0.2},
                0,
                (0.5, 0.1, 0.05),  # Doesn't matter since 0 offspring
                {"carbon": 2.0, "nitrogen": 0.5, "phosphorus": 0.2},
                False,
            ),
        ],
    )
    def test_handle_post_birth_parent_updates(
        self,
        mocker,
        animal_model_instance,
        herbivore_cohort_instance,
        reproductive_type,
        initial_reproductive_mass,
        offspring_count,
        birth_mass_cnp,
        expected_remaining_mass,
        expect_semelparous_death_called,
    ):
        """Test reproductive mass update and parent death handling after birth."""
        from virtual_ecosystem.models.animal.cnp import CNP

        # Mock parent cohort's reproductive type and initial reproductive mass
        herbivore_cohort_instance.functional_group.reproductive_type = reproductive_type
        herbivore_cohort_instance.reproductive_mass_cnp = CNP(
            **initial_reproductive_mass
        )

        # Mock `calculate_birth_mass_cnp`
        mocker.patch.object(
            animal_model_instance,
            "calculate_birth_mass_cnp",
            return_value=birth_mass_cnp,
        )

        # Mock `handle_semelparous_parent_death`
        mock_semelparous_death = mocker.patch.object(
            animal_model_instance, "handle_semelparous_parent_death"
        )

        # Run the method
        animal_model_instance.handle_post_birth_parent_updates(
            herbivore_cohort_instance, offspring_count
        )

        # Check that the reproductive mass was correctly updated (with float tolerance)
        assert herbivore_cohort_instance.reproductive_mass_cnp.carbon == pytest.approx(
            expected_remaining_mass["carbon"]
        )
        assert (
            herbivore_cohort_instance.reproductive_mass_cnp.nitrogen
            == pytest.approx(expected_remaining_mass["nitrogen"])
        )
        assert (
            herbivore_cohort_instance.reproductive_mass_cnp.phosphorus
            == pytest.approx(expected_remaining_mass["phosphorus"])
        )

        # Check if semelparous death was correctly triggered or skipped
        if expect_semelparous_death_called:
            mock_semelparous_death.assert_called_once_with(herbivore_cohort_instance)
        else:
            mock_semelparous_death.assert_not_called()

    def test_handle_semelparous_parent_death(
        self, mocker, animal_model_instance, herbivore_cohort_instance
    ):
        """Test mass loss, death flag, and removal for semelparous parent death."""
        from virtual_ecosystem.models.animal.cnp import CNP

        # Set initial CNP mass (arbitrary non-zero starting mass)
        herbivore_cohort_instance.mass_cnp = CNP(
            carbon=5.0, nitrogen=1.0, phosphorus=0.5
        )

        # Mock the loss from calculate_semelparous_mass_loss
        semelparous_loss = {"carbon": 2.0, "nitrogen": 0.5, "phosphorus": 0.2}
        mocker.patch.object(
            animal_model_instance,
            "calculate_semelparous_mass_loss",
            return_value=semelparous_loss,
        )

        # Mock remove_dead_cohort
        mock_remove_dead = mocker.patch.object(
            animal_model_instance, "remove_dead_cohort"
        )

        # Run the method
        animal_model_instance.handle_semelparous_parent_death(herbivore_cohort_instance)

        # Check mass was reduced correctly
        assert herbivore_cohort_instance.mass_cnp.carbon == pytest.approx(3.0)
        assert herbivore_cohort_instance.mass_cnp.nitrogen == pytest.approx(0.5)
        assert herbivore_cohort_instance.mass_cnp.phosphorus == pytest.approx(0.3)

        # Check parent marked as dead
        assert herbivore_cohort_instance.is_alive is False

        # Check parent was removed from population
        mock_remove_dead.assert_called_once_with(herbivore_cohort_instance)

    @pytest.mark.parametrize(
        "reproductive_type, initial_mass_cnp, expected_loss",
        [
            # Case 1: Semelparous species with 50% loss applied
            (
                "semelparous",
                {"carbon": 10.0, "nitrogen": 2.0, "phosphorus": 1.0},
                {"carbon": 5.0, "nitrogen": 1.0, "phosphorus": 0.5},
            ),
            # Case 2: Iteroparous species (no loss applied)
            (
                "iteroparous",
                {"carbon": 10.0, "nitrogen": 2.0, "phosphorus": 1.0},
                {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0},
            ),
        ],
    )
    def test_calculate_semelparous_mass_loss(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        reproductive_type,
        initial_mass_cnp,
        expected_loss,
    ):
        """Test semelparous mass loss calculation with fixed 50% loss."""
        from virtual_ecosystem.models.animal.cnp import CNP

        # Set parent cohort's functional group and initial mass
        herbivore_cohort_instance.functional_group.reproductive_type = reproductive_type
        herbivore_cohort_instance.mass_cnp = CNP(**initial_mass_cnp)

        # Run the method — since semelparity loss is fixed at 0.5, no need to mock
        result = animal_model_instance.calculate_semelparous_mass_loss(
            herbivore_cohort_instance
        )

        # Check result matches expected loss (with float tolerance)
        assert result["carbon"] == pytest.approx(expected_loss["carbon"])
        assert result["nitrogen"] == pytest.approx(expected_loss["nitrogen"])
        assert result["phosphorus"] == pytest.approx(expected_loss["phosphorus"])

    @pytest.mark.parametrize(
        "birth_mass, cnp_proportions, expected_birth_cnp",
        [
            # Standard balanced case
            (
                1.0,
                {"carbon": 0.5, "nitrogen": 0.3, "phosphorus": 0.2},
                (0.5, 0.3, 0.2),
            ),
            # Larger birth mass
            (
                10.0,
                {"carbon": 0.5, "nitrogen": 0.3, "phosphorus": 0.2},
                (5.0, 3.0, 2.0),
            ),
            # Zero birth mass (should return all zeros)
            (
                0.0,
                {"carbon": 0.5, "nitrogen": 0.3, "phosphorus": 0.2},
                (0.0, 0.0, 0.0),
            ),
        ],
    )
    def test_calculate_birth_mass_cnp(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        birth_mass,
        cnp_proportions,
        expected_birth_cnp,
    ):
        """Test conversion of birth mass into carbon, nitrogen, and phosphorus."""
        # Set parent cohort's stoichiometric proportions
        herbivore_cohort_instance.cnp_proportions = cnp_proportions

        # Run the method
        result = animal_model_instance.calculate_birth_mass_cnp(
            birth_mass, herbivore_cohort_instance
        )

        # Check result (with float tolerance)
        assert result[0] == pytest.approx(expected_birth_cnp[0])
        assert result[1] == pytest.approx(expected_birth_cnp[1])
        assert result[2] == pytest.approx(expected_birth_cnp[2])

    @pytest.mark.parametrize(
        "parent_group_name, reproductive_environment",
        [
            (
                "herbivorous_bird",
                "terrestrial",
            ),  # Terrestrial = no special residence time
            ("frog", "aquatic"),  # Aquatic = residence time applied
        ],
    )
    def test_create_offspring(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        functional_group_list_instance,
        parent_group_name,
        reproductive_environment,
    ):
        """Test offspring creation uses correct functional group and properties."""
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import (
            ReproductiveEnvironment,
        )
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        # Parent cohort setup
        parent_group = get_functional_group_by_name(
            functional_group_list_instance, parent_group_name
        )
        herbivore_cohort_instance.functional_group = parent_group
        herbivore_cohort_instance.functional_group.reproductive_environment = (
            reproductive_environment
        )
        # Pick a valid community cell
        valid_cell_id = next(iter(animal_model_instance.communities.keys()))
        herbivore_cohort_instance.centroid_key = valid_cell_id

        # Make sure the AnimalModel has the full list of functional groups
        animal_model_instance.functional_groups = functional_group_list_instance

        # Run the method
        offspring = animal_model_instance.create_offspring(herbivore_cohort_instance, 5)

        # Assertions - functional group & basic properties
        assert isinstance(offspring, AnimalCohort)
        assert offspring.functional_group == get_functional_group_by_name(
            functional_group_list_instance,
            parent_group.offspring_functional_group,
        )
        assert offspring.mass_current == parent_group.birth_mass
        assert offspring.age == 0.0
        assert offspring.individuals == 5
        assert offspring.centroid_key == valid_cell_id

        # Check aquatic residence time handling
        if reproductive_environment == ReproductiveEnvironment.AQUATIC:
            assert (
                offspring.remaining_time_away
                == parent_group.constants.aquatic_residence_time
            )
        else:
            assert offspring.remaining_time_away == 0.0

    @pytest.mark.parametrize(
        "cohort_id, is_below_mass_threshold, reproductive_type, expect_birth_call",
        [
            ("eligible", False, "iteroparous", True),  # Eligible - should reproduce
            ("below_threshold", True, "iteroparous", False),  # Too small - skipped
            (
                "nonreproductive",
                False,
                "nonreproductive",
                False,
            ),  # Nonreproductive - skipped
            ("edge_case_zero_mass", True, "nonreproductive", False),
        ],
    )
    def test_birth_community(
        self,
        mocker,
        animal_model_instance,
        cohort_id,
        is_below_mass_threshold,
        reproductive_type,
        expect_birth_call,
    ):
        """Test birth_community filters cohorts correctly."""
        # Create a mock cohort
        cohort = mocker.MagicMock()
        cohort.is_below_mass_threshold.return_value = is_below_mass_threshold
        cohort.functional_group.reproductive_type = reproductive_type

        # Place this single cohort into the active cohorts dictionary
        animal_model_instance.active_cohorts = {cohort_id: cohort}

        # Patch `birth` so we only check whether it's called
        mock_birth = mocker.patch.object(animal_model_instance, "birth")

        # Run the method
        animal_model_instance.birth_community()

        # Check that `is_below_mass_threshold` was checked
        cohort.is_below_mass_threshold.assert_called_once_with(1.5)

        # Check if `birth` was called or not
        if expect_birth_call:
            mock_birth.assert_called_once_with(cohort)
        else:
            mock_birth.assert_not_called()

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
            herbivore_cohort_instance, "get_litter_pools", mocker.Mock(return_value=[])
        )
        mocker.patch.object(
            herbivore_cohort_instance, "forage_cohort", mock_forage_herbivore
        )

        # Set up predator cohort
        predator_cohort_instance.functional_group.diet = DietType.VERTEBRATES
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
        animal_model_instance.active_cohorts = {
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
            litter_pools=[],
            excrement_pools=["excrement_pools_herbivore"],
            carcass_pool_map=animal_model_instance.carcass_pools,
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools=animal_model_instance.leaf_waste_pools,
        )

        # Verify that predators forage prey and not plant resources
        mock_get_prey.assert_called_once_with(animal_model_instance.communities)
        predator_cohort_instance.get_plant_resources.assert_not_called()
        mock_forage_predator.assert_called_once_with(
            plant_list=[],
            animal_list=["prey"],
            litter_pools=[],
            excrement_pools=["excrement_pools_predator"],
            carcass_pool_map=animal_model_instance.carcass_pools,
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools=animal_model_instance.leaf_waste_pools,
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
        animal_model_instance.active_cohorts = {
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
        animal_model_instance.active_cohorts = {
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
        animal_model_instance.active_cohorts = {}

        # Add the caterpillar cohort to the animal model's cohorts
        animal_model_instance.active_cohorts[caterpillar_cohort_instance.id] = (
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
        assert butterfly_functional_group is not None, (
            "Butterfly functional group not found"
        )

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
                for cohort in animal_model_instance.active_cohorts.values()
                if cohort.functional_group == butterfly_functional_group
            ),
            None,
        )
        assert adult_cohort is not None, "Butterfly cohort was not created"

        # Assert that the number of individuals in the butterfly cohort is correct
        assert adult_cohort.individuals == caterpillar_cohort_instance.individuals, (
            "Butterfly cohort's individuals count does not match the expected value"
        )

        # Assert that the caterpillar cohort is marked as dead and removed
        assert not caterpillar_cohort_instance.is_alive, (
            "Caterpillar cohort should be marked as dead"
        )
        assert (
            caterpillar_cohort_instance
            not in animal_model_instance.active_cohorts.values()
        ), "Caterpillar cohort should be removed from the model"

    def test_metamorphose_community(self, animal_model_instance, mocker):
        """Test metamorphose_community."""

        from virtual_ecosystem.models.animal.animal_traits import DevelopmentType

        # Create mock cohorts
        mock_cohort_1 = mocker.Mock()
        mock_cohort_2 = mocker.Mock()
        mock_cohort_3 = mocker.Mock()

        # Setup the animal model with mock cohorts
        animal_model_instance.active_cohorts = {
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

    @pytest.mark.parametrize(
        "cohort_type, initial_time_away, dt_days, expected_time_away,"
        "expect_reintegration",
        [
            # Migrated cohort with plenty of time left - no reintegration
            ("migrated", 10.0, 2.0, 8.0, False),
            # Migrated cohort with exactly enough time left - reintegrate
            ("migrated", 2.0, 2.0, 0.0, True),
            # Aquatic cohort with excess time - no reintegration
            ("aquatic", 5.0, 1.0, 4.0, False),
            # Aquatic cohort ready for reintegration
            ("aquatic", 1.5, 2.0, -0.5, True),
        ],
    )
    def test_update_migrated_and_aquatic(
        self,
        mocker,
        animal_model_instance,
        cohort_type,
        initial_time_away,
        dt_days,
        expected_time_away,
        expect_reintegration,
    ):
        """Test timing updates and reintegration for migrated and aquatic cohorts."""
        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort

        # Create mock cohort
        cohort = mocker.MagicMock(spec=AnimalCohort)
        cohort.remaining_time_away = initial_time_away

        # Place the cohort into the appropriate pool
        if cohort_type == "migrated":
            animal_model_instance.migrated_cohorts = {"cohort1": cohort}
            animal_model_instance.aquatic_cohorts = {}
        elif cohort_type == "aquatic":
            animal_model_instance.aquatic_cohorts = {"cohort1": cohort}
            animal_model_instance.migrated_cohorts = {}

        # Patch reintegrate_cohort so we track if it's called
        mock_reintegrate = mocker.patch.object(
            animal_model_instance, "reintegrate_cohort"
        )

        # Run the method
        dt = np.timedelta64(int(dt_days), "D")
        animal_model_instance.update_migrated_and_aquatic(dt)

        # Check time was reduced correctly
        assert cohort.remaining_time_away == pytest.approx(expected_time_away)

        # Check reintegration call
        if expect_reintegration:
            mock_reintegrate.assert_called_once_with(cohort, source=cohort_type)
        else:
            mock_reintegrate.assert_not_called()

    @pytest.mark.parametrize(
        "source, initial_individuals, mortality_rate, expected_individuals,"
        "expect_active, expect_dead",
        [
            # Migrated cohort with survival
            ("migrated", 100, 0.1, 90, True, False),
            # Migrated cohort with complete mortality
            ("migrated", 10, 1.0, 0, False, True),
            # Aquatic cohort with survival (fixed aquatic mortality at 0.1)
            ("aquatic", 200, None, 180, True, False),
            # Aquatic cohort with no individuals left
            ("aquatic", 5, None, 5, True, False),
        ],
    )
    def test_reintegrate_cohort(
        self,
        animal_model_instance,
        herbivore_cohort_instance,
        source,
        initial_individuals,
        mortality_rate,
        expected_individuals,
        expect_active,
        expect_dead,
    ):
        """Test reintegration logic for migrated and aquatic cohorts."""

        # Set initial conditions for the cohort
        herbivore_cohort_instance.individuals = initial_individuals
        herbivore_cohort_instance.id = "cohort1"
        herbivore_cohort_instance.is_alive = True
        herbivore_cohort_instance.location_status = "frozen"

        # Set the correct mortality rate based on source
        if source == "migrated":
            herbivore_cohort_instance.constants = herbivore_cohort_instance.constants
            object.__setattr__(
                herbivore_cohort_instance.constants,
                "migration_mortality",
                mortality_rate,
            )
            animal_model_instance.migrated_cohorts = {
                "cohort1": herbivore_cohort_instance
            }
            animal_model_instance.aquatic_cohorts = {}
        elif source == "aquatic":
            mortality_rate = 0.1  # Aquatic mortality is fixed at 0.1
            animal_model_instance.aquatic_cohorts = {
                "cohort1": herbivore_cohort_instance
            }
            animal_model_instance.migrated_cohorts = {}

        # Run the method
        animal_model_instance.reintegrate_cohort(herbivore_cohort_instance, source)

        # Check individuals count after mortality applied
        assert herbivore_cohort_instance.individuals == expected_individuals

        # Check final cohort state
        if expect_active:
            assert herbivore_cohort_instance.location_status == "active"
            assert "cohort1" in animal_model_instance.active_cohorts
            assert (
                animal_model_instance.active_cohorts["cohort1"]
                == herbivore_cohort_instance
            )
            assert herbivore_cohort_instance.is_alive is True
        elif expect_dead:
            assert herbivore_cohort_instance.is_alive is False
            assert "cohort1" not in animal_model_instance.active_cohorts

        # Check cohort removal from the source pool
        if source == "migrated":
            assert "cohort1" not in animal_model_instance.migrated_cohorts
        elif source == "aquatic":
            assert "cohort1" not in animal_model_instance.aquatic_cohorts

    @pytest.mark.parametrize(
        "is_seasonal, migration_check, expected_migrations",
        [
            (True, True, 1),  # Seasonal migrator & migration season → Should migrate
            (
                True,
                False,
                0,
            ),  # Seasonal migrator but not migration season → No migration
            (False, True, 0),  # Non-seasonal → Should not migrate
            (False, False, 0),  # Non-seasonal & not migration season → No migration
        ],
    )
    def test_migrate_external_community(
        self,
        mocker,
        animal_model_instance,
        herbivore_cohort_instance,
        is_seasonal,
        migration_check,
        expected_migrations,
    ):
        """Test whether migrate_external_community correctly triggers migration."""

        # Set up cohort attributes
        cohort = herbivore_cohort_instance
        cohort.functional_group.migration_type = "seasonal" if is_seasonal else "none"

        # Mock is_migration_season to return the given test condition
        mocker.patch.object(cohort, "is_migration_season", return_value=migration_check)

        # Mock migrate_external so we can count how many times it's called
        mock_migrate_external = mocker.patch.object(
            animal_model_instance, "migrate_external"
        )

        # Add the cohort to active cohorts
        animal_model_instance.active_cohorts[cohort.id] = cohort

        # Run function
        animal_model_instance.migrate_external_community()

        # Assert migrate_external was called the expected number of times
        assert mock_migrate_external.call_count == expected_migrations, (
            f"Expected {expected_migrations} migrations, but got"
            f"{mock_migrate_external.call_count}"
        )

    @pytest.mark.parametrize(
        "remaining_time, is_migrated, is_aquatic, expected_reintegrations",
        [
            (0, True, False, 1),  # Migrated & ready for reintegration
            (-1, True, False, 1),  # Migrated & overdue → Reintegration should happen
            (5, True, False, 0),  # Migrated but still has time left → No reintegration
            (0, False, True, 1),  # Aquatic & ready for reintegration
            (-1, False, True, 1),  # Aquatic & overdue → Reintegration should happen
            (5, False, True, 0),  # Aquatic but still has time left → No reintegration
            (5, False, False, 0),  # Not migrated or aquatic → No reintegration
        ],
    )
    def test_reintegrate_community(
        self,
        mocker,
        animal_model_instance,
        herbivore_cohort_instance,
        remaining_time,
        is_migrated,
        is_aquatic,
        expected_reintegrations,
    ):
        """Test whether reintegrate_community correctly triggers reintegration."""

        # Set up cohort attributes
        cohort = herbivore_cohort_instance
        cohort.remaining_time_away = remaining_time

        # Mock reintegrate_cohort so we can count how many times it's called
        mock_reintegrate = mocker.patch.object(
            animal_model_instance, "reintegrate_cohort"
        )

        # Add cohort to the correct list based on test case
        if is_migrated:
            animal_model_instance.migrated_cohorts[cohort.id] = cohort
        elif is_aquatic:
            animal_model_instance.aquatic_cohorts[cohort.id] = cohort

        # Run function
        animal_model_instance.reintegrate_community()

        # Assert reintegrate_cohort was called the expected number of times
        assert mock_reintegrate.call_count == expected_reintegrations, (
            f"Expected {expected_reintegrations} reintegrations, "
            f"but got {mock_reintegrate.call_count}"
        )

    def test_assign_prey_groups(self, animal_model_instance, predator_cohort_instance):
        """Test assign_prey_groups correctly filters and assigns prey groups."""
        # Run assign_prey_groups
        animal_model_instance.assign_prey_groups(predator_cohort_instance)

        # Extract assigned prey groups
        prey_groups = predator_cohort_instance.prey_groups

        # Assertions on structure
        assert hasattr(predator_cohort_instance, "prey_groups")
        assert isinstance(prey_groups, dict)

        # Check all prey group entries are well formed
        for group_name, mass_range in prey_groups.items():
            assert isinstance(group_name, str)
            assert isinstance(mass_range, tuple)
            assert len(mass_range) == 2
            assert all(isinstance(val, float) for val in mass_range)
            assert 0.0 <= mass_range[0] <= mass_range[1]

        # Check that known prey group names are included
        known_possible_prey = {
            "herbivorous_mammal",
            "herbivorous_insect",
            "herbivorous_bird",
            "caterpillar",
        }
        assert any(group in prey_groups for group in known_possible_prey)

    def test_create_new_cohort_registers_active(
        self,
        mocker,
        animal_model_instance,
        functional_group_list_instance,
    ):
        """Test for create new cohort registration."""

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_traits import (
            ReproductiveEnvironment,
        )
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        terrestrial_fg = get_functional_group_by_name(
            functional_group_list_instance, "herbivorous_mammal"
        )
        # Confirm this is indeed a terrestrial reproducer
        assert (
            terrestrial_fg.reproductive_environment
            is ReproductiveEnvironment.TERRESTRIAL
        )

        # Spy on helper methods
        spy_assign = mocker.patch.object(animal_model_instance, "assign_prey_groups")
        spy_occupancy = mocker.patch.object(
            animal_model_instance, "update_community_occupancy"
        )

        cohort = animal_model_instance.create_new_cohort(
            functional_group=terrestrial_fg,
            mass=terrestrial_fg.adult_mass,
            age=0.0,
            individuals=10,
            centroid_key=0,
            is_birth=False,
        )

        # Returned object
        assert isinstance(cohort, AnimalCohort)

        # Correct registration: active, not aquatic
        assert cohort.id in animal_model_instance.active_cohorts
        assert cohort.id not in animal_model_instance.aquatic_cohorts

        # Helper methods called exactly once
        spy_assign.assert_called_once_with(cohort)
        spy_occupancy.assert_called_once_with(cohort, 0)

    @pytest.mark.parametrize(
        "fg_name, is_birth, goes_aquatic",
        [
            ("frog", True, True),  # tadpoles
            ("frog", False, False),  # adult frog at init
            ("herbivorous_mammal", True, False),  # always terrestrial
        ],
    )
    def test_create_new_cohort_routing(
        self,
        mocker,
        animal_model_instance,
        functional_group_list_instance,
        fg_name,
        is_birth,
        goes_aquatic,
    ):
        """Test for create new cohort to ensure routing works."""
        from virtual_ecosystem.models.animal.functional_group import (
            get_functional_group_by_name,
        )

        fg = get_functional_group_by_name(functional_group_list_instance, fg_name)

        spy_occ = mocker.spy(animal_model_instance, "update_community_occupancy")

        cohort = animal_model_instance.create_new_cohort(
            fg, fg.birth_mass, 0.0, 5, 0, is_birth=is_birth
        )

        if goes_aquatic:
            assert cohort.id in animal_model_instance.aquatic_cohorts
            assert cohort.id not in animal_model_instance.active_cohorts
            spy_occ.assert_not_called()
        else:
            assert cohort.id in animal_model_instance.active_cohorts
            spy_occ.assert_called_once_with(cohort, 0)

    def test_update_community_bookkeeping(self, mocker, prepared_animal_model_instance):
        """Test update_community_bookkeeping."""

        # Spy on the three submethods
        mocker.spy(prepared_animal_model_instance, "update_migrated_and_aquatic")
        mocker.spy(prepared_animal_model_instance, "reintegrate_community")
        mocker.spy(prepared_animal_model_instance, "remove_dead_cohort_community")

        # Call the bookkeeping method
        prepared_animal_model_instance.update_community_bookkeeping(
            dt=np.timedelta64(1, "D")
        )

        # Assert each method was called exactly once
        assert (
            prepared_animal_model_instance.update_migrated_and_aquatic.call_count == 1
        )
        assert prepared_animal_model_instance.reintegrate_community.call_count == 1
        assert (
            prepared_animal_model_instance.remove_dead_cohort_community.call_count == 1
        )

    def test_update_cohort_bookkeeping(self, mocker, prepared_animal_model_instance):
        """Test update_cohort_bookkeeping."""

        # Spy on each cohort's methods
        for cohort in prepared_animal_model_instance.active_cohorts.values():
            mocker.spy(cohort, "increase_age")
            mocker.spy(cohort, "update_largest_mass")

        # Call the bookkeeping method
        prepared_animal_model_instance.update_cohort_bookkeeping(
            dt=np.timedelta64(1, "D")
        )

        # Assert each cohort's methods were called once
        for cohort in prepared_animal_model_instance.active_cohorts.values():
            assert cohort.increase_age.call_count == 1
            assert cohort.update_largest_mass.call_count == 1
