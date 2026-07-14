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
    microbial_c_n_p_ratios,
    dummy_animal_exporter,
    dummy_resource_pool_exporter,
):
    """Animal model instance in which setup has already been run."""
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    model = AnimalModel(
        data=dummy_animal_data,
        core_components=fixture_core_components,
        animal_cohort_exporter=dummy_animal_exporter,
        resource_pool_exporter=dummy_resource_pool_exporter,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
        microbial_c_n_p_ratios=microbial_c_n_p_ratios,
    )
    return model


class TestAnimalModel:
    """Test the AnimalModel class."""

    @pytest.mark.parametrize(
        "scaling_method",
        ["madingley", "damuth"],
        ids=["default_madingley", "explicit_damuth"],
    )
    def test_animal_model_initialization(
        self,
        scaling_method,
        dummy_animal_data,
        fixture_core_components,
        functional_group_list_instance,
        microbial_c_n_p_ratios,
        dummy_animal_exporter,
        dummy_resource_pool_exporter,
    ):
        """Test `AnimalModel` initialization with both scaling methods."""
        from virtual_ecosystem.core.base_model import BaseModel
        from virtual_ecosystem.models.animal.animal_model import AnimalModel
        from virtual_ecosystem.models.animal.model_config import AnimalConstants

        # Initialize the model
        model = AnimalModel(
            data=dummy_animal_data,
            core_components=fixture_core_components,
            animal_cohort_exporter=dummy_animal_exporter,
            resource_pool_exporter=dummy_resource_pool_exporter,
            functional_groups=functional_group_list_instance,
            model_constants=AnimalConstants(density_scaling_method=scaling_method),
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
        )

        # Basic type and attribute checks
        assert isinstance(model, BaseModel)
        assert model.model_name == "animal"
        assert isinstance(model.communities, dict)

        # Density scaling method should match input
        assert model.density_scaling_method == scaling_method
        assert model.model_constants.density_scaling_method == scaling_method

    @pytest.mark.parametrize(
        "raises,expected_log_entries",
        [
            pytest.param(
                does_not_raise(),
                (
                    [
                        (INFO, "Animal cohort data exporter not active."),
                        (INFO, "Resource pool data exporter not active."),
                        (
                            INFO,
                            "Information required to initialise the animal model "
                            "successfully extracted.",
                        ),
                        (
                            INFO,
                            "animal model: required initial data variables checked",
                        ),
                        (
                            INFO,
                            "Adding data array for "
                            "'litter_consumed_above_metabolic_cnp'",
                        ),
                        (
                            INFO,
                            "Adding data array for "
                            "'litter_consumed_above_structural_cnp'",
                        ),
                        (INFO, "Adding data array for 'litter_consumed_woody_cnp'"),
                        (
                            INFO,
                            "Adding data array for "
                            "'litter_consumed_below_metabolic_cnp'",
                        ),
                        (
                            INFO,
                            "Adding data array for "
                            "'litter_consumed_below_structural_cnp'",
                        ),
                        (INFO, "Adding data array for 'total_animal_respiration'"),
                        (INFO, "Adding data array for 'population_densities'"),
                        (INFO, "Updating animal model"),
                        (
                            INFO,
                            "Adding data array for 'decay_of_fungal_fruiting_bodies'",
                        ),
                        (INFO, "Adding data array for 'decomposed_excrement_cnp'"),
                        (INFO, "Adding data array for 'decomposed_carcasses_cnp'"),
                        (INFO, "Adding data array for 'animal_pom_consumption_cnp'"),
                        (INFO, "Adding data array for 'animal_bacteria_consumption'"),
                        (
                            INFO,
                            "Adding data array for "
                            "'animal_saprotrophic_fungi_consumption'",
                        ),
                        (
                            INFO,
                            "Adding data array for 'animal_ectomycorrhiza_consumption'",
                        ),
                        (
                            INFO,
                            "Adding data array for "
                            "'animal_arbuscular_mycorrhiza_consumption'",
                        ),
                        (INFO, "Adding data array for 'herbivory_waste_above_cnp'"),
                        (INFO, "Adding data array for 'herbivory_waste_above_lignin'"),
                        (INFO, "Adding data array for 'herbivory_waste_below_cnp'"),
                        (INFO, "Adding data array for 'herbivory_waste_below_lignin'"),
                    ]
                ),
                id="success",
            ),
        ],
    )
    def test_generate_animal_model(
        self,
        caplog,
        dummy_animal_data,
        animal_fixture_configuration,
        raises,
        expected_log_entries,
    ):
        """Test that the function to initialise the animal model behaves as expected."""
        from virtual_ecosystem.core.core_components import CoreComponents
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Build the config object and core components using the fixture
        core_components = CoreComponents(animal_fixture_configuration.core)
        caplog.clear()

        # Check whether model is initialised (or not) as expected
        with raises:
            model = AnimalModel.from_config(
                data=dummy_animal_data,
                configuration=animal_fixture_configuration,
                core_components=core_components,
            )

            # Run the update step (once this does something should check output)
            model.update(time_index=0)

        # Print the captured log messages to debug
        for record in caplog.records:
            print(f"Log Level: {record.levelno}, Message: {record.message}")

        # Filter out stochastic log entries and overwrite the underlying log handler
        # data so that the caplog.records property returns the filtered records.
        caplog.handler.records = [
            record
            for record in caplog.records
            if "No individuals in cohort to forage." not in record.message
        ]

        # Final check that expected logging entries are produced
        log_check(caplog, expected_log_entries)

        for record in caplog.records:
            print(f"Level: {record.levelname}, Message: {record.message}")

    @pytest.mark.parametrize(
        "scaling_method",
        ["madingley", "damuth"],
        ids=["default_madingley", "explicit_damuth"],
    )
    def test_from_config(
        self,
        scaling_method,
        dummy_animal_data,
        animal_fixture_configuration,
        fixture_core_components,
    ):
        """Test that AnimalModel.from_config correctly sets density_scaling_method."""
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Update the constants to set the scaling method
        # Configuration classes are frozen so update via the __dict__ entries
        animal_fixture_configuration.animal.constants.__dict__[
            "density_scaling_method"
        ] = scaling_method

        # Create the model using from_config
        model = AnimalModel.from_config(
            data=dummy_animal_data,
            configuration=animal_fixture_configuration,
            core_components=fixture_core_components,
        )

        # Check that the model has the correct scaling method set
        assert model.density_scaling_method == scaling_method
        assert model.model_constants.density_scaling_method == scaling_method

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

    def test_populate_soil_pools(self, animal_model_instance):
        """Test that populating of the soil resource pools works as expected."""

        expected_pool_set = {"pom", "bacteria", "fungi"}
        expected_carbon = {
            "pom": np.full(9, 303.75),
            "bacteria": np.full(9, 303.75),
            "fungi": np.full(9, 911.25),
        }
        expected_nitrogen = {
            "pom": np.full(9, 303.75),
            "bacteria": np.full(9, 58.413461),
            "fungi": np.full(9, 80.480769),
        }
        expected_phosphorus = {
            "pom": np.full(9, 303.75),
            "bacteria": np.full(9, 18.984375),
            "fungi": np.full(9, 12.65625),
        }

        soil_pools = animal_model_instance.populate_soil_pools()

        for cell_id, pool_dict in soil_pools.items():
            assert set(pool_dict.keys()) == expected_pool_set
            for pool_name, pool in pool_dict.items():
                assert np.isclose(
                    pool.mass_current, expected_carbon[pool_name][cell_id]
                )
                assert np.isclose(
                    pool.mass_cnp.N, expected_nitrogen[pool_name][cell_id]
                )
                assert np.isclose(
                    pool.mass_cnp.P,
                    expected_phosphorus[pool_name][cell_id],
                )

    def test_populate_fungal_fruiting_bodies(self, animal_model_instance):
        """Test that populating of fungal fruiting bodies pools works as expected."""

        expected_carbon = np.full(9, 12150.0)
        expected_nitrogen = np.full(9, 1215.0)
        expected_phosphorus = np.full(9, 162.0)

        fungal_fruiting_bodies = animal_model_instance.populate_fungal_fruiting_bodies()

        for cell_id, pool in fungal_fruiting_bodies.items():
            assert np.isclose(pool.mass_current, expected_carbon[cell_id])
            assert np.isclose(pool.mass_cnp.N, expected_nitrogen[cell_id])
            assert np.isclose(pool.mass_cnp.P, expected_phosphorus[cell_id])

    def test_populate_soil_pools_negative(self, animal_model_instance):
        """Test that trying to populate a negative soil pool causes an error."""
        from xarray import DataArray

        animal_model_instance.data["soil_cnp_pool_pom"].loc[:, "C"] = DataArray(
            np.full(9, -3.75), dims=["cell_id"]
        )

        with pytest.raises(ValueError) as err:
            _ = animal_model_instance.populate_soil_pools()

        assert "pom: negative mass detected in cell 0" in str(err.value)

    def test_calculate_total_soil_consumption(
        self,
        litter_soil_data_instance,
        fixture_core_components,
        fixture_core_constants,
        functional_group_list_instance,
        constants_instance,
        microbial_c_n_p_ratios,
        dummy_animal_exporter,
        dummy_resource_pool_exporter,
    ):
        """Test calculation of total consumption of soil by animals is correct."""
        from copy import deepcopy

        import numpy as np
        from xarray import DataArray

        from virtual_ecosystem.models.animal.animal_model import AnimalModel
        from virtual_ecosystem.models.animal.decay import SoilPool

        # Create AnimalModel instance with test data
        model = AnimalModel(
            data=litter_soil_data_instance,
            core_components=fixture_core_components,
            animal_cohort_exporter=dummy_animal_exporter,
            resource_pool_exporter=dummy_resource_pool_exporter,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
        )

        # Copy data and simulate biomass loss from each soil pool
        new_data = deepcopy(litter_soil_data_instance)
        pom_change = 0.03
        pom_c_n_ratio = (
            litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "C"]
            / litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "N"]
        )
        pom_c_p_ratio = (
            litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "C"]
            / litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "P"]
        )
        new_data["soil_cnp_pool_pom"] = DataArray(
            np.stack(
                [
                    litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "C"]
                    - pom_change,
                    litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "N"]
                    - (pom_change / pom_c_n_ratio),
                    litter_soil_data_instance["soil_cnp_pool_pom"].loc[:, "P"]
                    - (pom_change / pom_c_p_ratio),
                ],
                axis=1,
            ),
            dims=("cell_id", "element"),
            coords=dict(
                cell_id=np.arange(litter_soil_data_instance.grid.n_cells),
                element=["C", "N", "P"],
            ),
        )
        new_data["soil_c_pool_bacteria"] = (
            litter_soil_data_instance["soil_c_pool_bacteria"] - 0.55
        )
        fungal_loss = 0.33
        total_fungi = (
            litter_soil_data_instance["soil_c_pool_saprotrophic_fungi"]
            + litter_soil_data_instance["soil_c_pool_arbuscular_mycorrhiza"]
            + litter_soil_data_instance["soil_c_pool_ectomycorrhiza"]
        )
        new_data["soil_c_pool_saprotrophic_fungi"] = litter_soil_data_instance[
            "soil_c_pool_saprotrophic_fungi"
        ] - (
            fungal_loss
            * litter_soil_data_instance["soil_c_pool_saprotrophic_fungi"]
            / total_fungi
        )
        new_data["soil_c_pool_ectomycorrhiza"] = litter_soil_data_instance[
            "soil_c_pool_ectomycorrhiza"
        ] - (
            fungal_loss
            * litter_soil_data_instance["soil_c_pool_ectomycorrhiza"]
            / total_fungi
        )
        new_data["soil_c_pool_arbuscular_mycorrhiza"] = litter_soil_data_instance[
            "soil_c_pool_arbuscular_mycorrhiza"
        ] - (
            fungal_loss
            * litter_soil_data_instance["soil_c_pool_arbuscular_mycorrhiza"]
            / total_fungi
        )

        pool_names = ["pom", "fungi", "bacteria"]

        cell_ids = fixture_core_components.grid.cell_id
        cell_area = fixture_core_components.grid.cell_area

        # Construct the nested dict: cell_id → pool_name → LitterPool
        new_soil_pools = {
            cid: {
                pool_name: SoilPool(
                    pool_name=pool_name,
                    cell_id=cid,
                    data=new_data,
                    cell_area=cell_area,
                    max_depth_microbial_activity=fixture_core_constants.max_depth_of_microbial_activity,
                    c_n_p_ratios=microbial_c_n_p_ratios,
                )
                for pool_name in pool_names
            }
            for cid in cell_ids
        }

        # Run consumption calculation
        consumption = model.calculate_total_soil_consumption(soil_pools=new_soil_pools)

        # Validate consumption matches expected loss per cell
        for consumption_type, expected_consumption in [
            (
                "animal_pom_consumption_cnp",
                np.stack(
                    [
                        np.full(4, 0.002142857),
                        np.array([0.000153061, 1.530536e-6, 8.746347e-6, 8.746353e-5]),
                        np.array([6.122143e-7, 6.122443e-7, 3.498539e-7, 3.498541e-6]),
                    ],
                    axis=1,
                ),
            ),
            ("animal_bacteria_consumption", np.full(4, 0.03928571)),
            (
                "animal_saprotrophic_fungi_consumption",
                np.array([0.0104371, 0.0177721, 0.0050429, 0.0061680]),
            ),
            (
                "animal_ectomycorrhiza_consumption",
                np.array([0.0055117, 0.0027438, 0.0095837, 0.0051219]),
            ),
            (
                "animal_arbuscular_mycorrhiza_consumption",
                np.array([0.0076226, 0.00305556, 0.00894482, 0.0122816]),
            ),
        ]:
            actual = consumption[consumption_type].values
            assert np.allclose(actual, expected_consumption), (
                f"Mismatch for {consumption_type}."
            )

    def test_calculate_litter_additions_from_herbivory(
        self,
        litter_soil_data_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
        microbial_c_n_p_ratios,
        dummy_animal_exporter,
        dummy_resource_pool_exporter,
    ):
        """Test calculation of litter addition via herbivory is correct."""

        import numpy as np
        from xarray import DataArray

        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Create AnimalModel instance with test data
        model = AnimalModel(
            data=litter_soil_data_instance,
            core_components=fixture_core_components,
            animal_cohort_exporter=dummy_animal_exporter,
            resource_pool_exporter=dummy_resource_pool_exporter,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
        )

        above_mass_cnp = [
            {"C": 1.0, "N": 1.5, "P": 2.0},
            {"C": 2.5, "N": 3.0, "P": 3.5},
            {"C": 4.0, "N": 4.5, "P": 5.0},
            {"C": 5.5, "N": 6.0, "P": 6.5},
        ]
        below_mass_cnp = [
            {"C": 7.0, "N": 7.5, "P": 8.0},
            {"C": 8.5, "N": 9.0, "P": 9.5},
            {"C": 10.0, "N": 10.5, "P": 11.0},
            {"C": 11.5, "N": 12.0, "P": 12.5},
        ]
        above_lignin = [0.01, 0.05, 0.1, 0.15]
        below_lignin = [0.2, 0.25, 0.3, 0.35]

        cell_ids = np.arange(litter_soil_data_instance.grid.n_cells)
        elements = np.array(["C", "N", "P"])
        expected_above_cnp = DataArray(
            np.stack(
                [
                    [1.0, 2.5, 4.0, 5.5],
                    [1.5, 3.0, 4.5, 6.0],
                    [2.0, 3.5, 5.0, 6.5],
                ],
                axis=1,
            ),
            dims=("cell_id", "element"),
            coords=dict(cell_id=cell_ids, element=elements),
        )
        expected_below_cnp = DataArray(
            np.stack(
                [
                    [7.0, 8.5, 10.0, 11.5],
                    [7.5, 9.0, 10.5, 12.0],
                    [8.0, 9.5, 11.0, 12.5],
                ],
                axis=1,
            ),
            dims=("cell_id", "element"),
            coords=dict(cell_id=cell_ids, element=elements),
        )

        # Populate the herbivory waste pools
        for cell_id in range(model.grid.n_cells):
            model.herbivory_waste_pools[cell_id].above_ground_mass_cnp = above_mass_cnp[
                cell_id
            ]
            model.herbivory_waste_pools[cell_id].below_ground_mass_cnp = below_mass_cnp[
                cell_id
            ]
            model.herbivory_waste_pools[
                cell_id
            ].above_ground_lignin_proportion = above_lignin[cell_id]
            model.herbivory_waste_pools[
                cell_id
            ].below_ground_lignin_proportion = below_lignin[cell_id]

        litter_additions = model.calculate_litter_additions_from_herbivory()

        # Check that waste has been added to the pools as expected
        assert np.allclose(
            litter_additions["herbivory_waste_above_cnp"], expected_above_cnp
        )
        assert np.allclose(
            litter_additions["herbivory_waste_below_cnp"], expected_below_cnp
        )
        assert np.allclose(
            litter_additions["herbivory_waste_above_lignin"], above_lignin
        )
        assert np.allclose(
            litter_additions["herbivory_waste_below_lignin"], below_lignin
        )

        # Check that all values have been reset to zero
        for cell_id in range(model.grid.n_cells):
            assert model.herbivory_waste_pools[cell_id].above_ground_mass_cnp == {
                "C": 0.0,
                "N": 0.0,
                "P": 0.0,
            }
            assert model.herbivory_waste_pools[cell_id].below_ground_mass_cnp == {
                "C": 0.0,
                "N": 0.0,
                "P": 0.0,
            }

        assert np.allclose(
            model.herbivory_waste_pools[cell_id].above_ground_lignin_proportion, 0.0
        )
        assert np.allclose(
            model.herbivory_waste_pools[cell_id].below_ground_lignin_proportion, 0.0
        )

    def test_update_fungal_fruiting_bodies(
        self,
        litter_soil_data_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
        microbial_c_n_p_ratios,
        dummy_animal_exporter,
        dummy_resource_pool_exporter,
    ):
        """Test that the function to update fungal fruiting bodies works as expected."""
        import numpy as np

        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        expected_decay = [0.01008051, 0.00957649, 0.00819042, 0.00724537]
        expected_new_carbon_mass = [5336.86979, 5070.02630, 4336.20671, 3835.87516]
        expected_new_nitrogen_mass = [533.686979, 507.002630, 433.620671, 383.587516]
        expected_new_phosphorus_mass = [71.1582639, 67.6003507, 57.8160895, 51.1450021]

        # Create AnimalModel instance with test data
        model = AnimalModel(
            data=litter_soil_data_instance,
            core_components=fixture_core_components,
            animal_cohort_exporter=dummy_animal_exporter,
            resource_pool_exporter=dummy_resource_pool_exporter,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
        )
        actual_decay = model.update_fungal_fruiting_bodies()

        actual_new_carbon_mass = [
            model.fungal_fruiting_bodies[cell_id].mass_current
            for cell_id in model.fungal_fruiting_bodies
        ]
        actual_new_nitrogen_mass = [
            model.fungal_fruiting_bodies[cell_id].mass_cnp["N"]
            for cell_id in model.fungal_fruiting_bodies
        ]
        actual_new_phosphorus_mass = [
            model.fungal_fruiting_bodies[cell_id].mass_cnp["P"]
            for cell_id in model.fungal_fruiting_bodies
        ]

        assert np.allclose(actual_new_carbon_mass, expected_new_carbon_mass)
        assert np.allclose(actual_new_nitrogen_mass, expected_new_nitrogen_mass)
        assert np.allclose(actual_new_phosphorus_mass, expected_new_phosphorus_mass)
        assert np.allclose(
            actual_decay["decay_of_fungal_fruiting_bodies"], expected_decay
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

    def test_update_fungal_fruiting_bodies_in_data(
        self,
        litter_soil_data_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
        microbial_c_n_p_ratios,
        dummy_animal_exporter,
        dummy_resource_pool_exporter,
    ):
        """Test that updating the data object based on FungalFruitPool changes works."""
        import numpy as np

        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        expected_pool = [0.65887281, 0.62592917, 0.53533416, 0.47356483]

        # Create AnimalModel instance with test data
        model = AnimalModel(
            data=litter_soil_data_instance,
            core_components=fixture_core_components,
            animal_cohort_exporter=dummy_animal_exporter,
            resource_pool_exporter=dummy_resource_pool_exporter,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
        )
        _ = model.update_fungal_fruiting_bodies()
        # Update the data object based on the changes caused by previous method
        model.update_fungal_fruiting_bodies_in_data()

        assert np.allclose(model.data["fungal_fruiting_bodies"], expected_pool)

    def test_initialize_communities(
        self,
        mocker,
        animal_data_for_model_instance,
        fixture_core_components,
        functional_group_list_instance,
        constants_instance,
        microbial_c_n_p_ratios,
        dummy_animal_exporter,
        dummy_resource_pool_exporter,
    ):
        """Test _initialize_communities."""

        from virtual_ecosystem.models.animal.animal_cohorts import AnimalCohort
        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        mocker.patch(
            "virtual_ecosystem.models.animal.animal_model.AnimalModel.populate_soil_pools",
            return_value={},
        )
        mocker.patch(
            "virtual_ecosystem.models.animal.animal_model.AnimalModel.populate_fungal_fruiting_bodies",
            return_value={},
        )

        model = AnimalModel(
            data=animal_data_for_model_instance,
            core_components=fixture_core_components,
            animal_cohort_exporter=dummy_animal_exporter,
            resource_pool_exporter=dummy_resource_pool_exporter,
            functional_groups=functional_group_list_instance,
            model_constants=constants_instance,
            microbial_c_n_p_ratios=microbial_c_n_p_ratios,
        )

        model.active_cohorts = {}
        model.communities = {
            cell_id: [] for cell_id in animal_data_for_model_instance.grid.cell_id
        }

        model._initialize_communities(functional_group_list_instance)

        # Every cell has a community list.
        for cell_id in animal_data_for_model_instance.grid.cell_id:
            assert isinstance(model.communities[cell_id], list)

        # Every functional group has at least one cohort.
        fg_names_with_cohorts = {
            c.functional_group.name for c in model.active_cohorts.values()
        }
        expected_fg_names = {fg.name for fg in functional_group_list_instance}
        assert fg_names_with_cohorts == expected_fg_names

        # Every cohort has the correct initial state and is registered in its community.
        for cohort in model.active_cohorts.values():
            assert isinstance(cohort, AnimalCohort)
            assert cohort.age == 0.0
            assert cohort.mass_current == pytest.approx(
                cohort.functional_group.birth_mass
            )
            assert cohort.individuals >= model.minimum_cohort_size
            assert cohort.centroid_key in model.data.grid.cell_id
            assert cohort in model.communities[cohort.centroid_key]

    @pytest.mark.parametrize(
        "total_individuals,target_cohorts,min_cohort_size,expected_n_cohorts",
        [
            (100, 10, 5, 10),  # even split
            (103, 10, 5, 10),  # split with remainder
            (25, 10, 5, 5),  # not enough for 10 * 5, reduces to 5
            (0, 10, 5, 1),  # zero total
            (3, 10, 5, 1),  # too small, forced single cohort
        ],
        ids=[
            "even_split",
            "split_with_remainder",
            "reduce_for_min_size",
            "zero_total",
            "below_min_size",
        ],
    )
    def test_distribute_individuals_to_cohorts(
        self,
        animal_model_instance,
        total_individuals,
        target_cohorts,
        min_cohort_size,
        expected_n_cohorts,
    ):
        """Test _distribute_individuals_to_cohorts produces correct cohort sizes."""
        model = animal_model_instance

        # Override these attributes for test
        model.target_cohorts_per_fg = target_cohorts
        model.minimum_cohort_size = min_cohort_size

        cohort_sizes = model._distribute_individuals_to_cohorts(total_individuals)

        # All cohort sizes >= minimum (unless total < min_size)
        for size in cohort_sizes:
            if total_individuals >= min_cohort_size:
                assert size >= min_cohort_size
            else:
                assert size <= total_individuals

        # Sum matches total_individuals exactly
        assert sum(cohort_sizes) == total_individuals

        # Number of cohorts matches expected (given reductions)
        assert len(cohort_sizes) == expected_n_cohorts

    @pytest.mark.parametrize(
        "n_cohorts",
        [
            2,  # fewer than cells
            4,  # exactly equal to cells
            6,  # more than cells
            0,  # zero cohorts
        ],
        ids=[
            "fewer_than_cells",
            "equal_to_cells",
            "more_than_cells",
            "zero_cohorts",
        ],
    )
    def test_assign_cohort_locations(self, mocker, animal_model_instance, n_cohorts):
        """Test _assign_cohort_locations for various cohort counts."""
        import numpy as np

        # Patch random.choice in the model to use numpy's choice
        mocker.patch("virtual_ecosystem.models.animal.animal_model.random", np.random)

        model = animal_model_instance
        cell_ids = list(model.data.grid.cell_id)
        n_cells = len(cell_ids)

        # Safety check for test assumptions
        assert n_cells >= 4, "Test grid should have at least 4 cells."

        # Call the method under test
        locations = model._assign_cohort_locations(n_cohorts)

        # Always returns exactly n_cohorts entries
        assert len(locations) == n_cohorts

        # All locations must be valid cell IDs
        for loc in locations:
            assert loc in cell_ids

        unique_cells = set(locations)

        if n_cohorts <= n_cells:
            # When cohorts ≤ cells, all must be unique
            assert len(unique_cells) == n_cohorts
        else:
            # When more cohorts than cells, ensure full coverage
            for cid in cell_ids:
                assert cid in unique_cells

        # Edge case: zero cohorts should yield empty list
        if n_cohorts == 0:
            assert locations == []

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
        cohort.mass_cnp.C = (
            cohort.functional_group.adult_mass
            * mass_ratio
            * cohort.cnp_proportions["C"]
        )
        cohort.mass_cnp.N = (
            cohort.functional_group.adult_mass
            * mass_ratio
            * cohort.cnp_proportions["N"]
        )
        cohort.mass_cnp.P = (
            cohort.functional_group.adult_mass
            * mass_ratio
            * cohort.cnp_proportions["P"]
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
            "C": 1.0,
            "N": 0.1,
            "P": 0.05,
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
                {"C": 0.0, "N": 0.0, "P": 0.0},
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {"C": 0.5, "N": 0.1, "P": 0.05},
            ),
            # Case 2: Semelparous species with mass loss contribution
            (
                {"C": 0.2, "N": 0.05, "P": 0.01},
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {"C": 0.7, "N": 0.15, "P": 0.06},
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
        assert result["C"] == pytest.approx(expected_total_mass["C"])
        assert result["N"] == pytest.approx(expected_total_mass["N"])
        assert result["P"] == pytest.approx(expected_total_mass["P"])

    @pytest.mark.parametrize(
        "birth_mass_cnp, reproductive_mass, individuals, expected_offspring",
        [
            # Case 1: Exactly 1 offspring per parent
            (
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {"C": 0.5, "N": 0.1, "P": 0.05},
                1,
                1,
            ),
            # Case 2: Exactly 2 offspring per parent
            (
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {"C": 1.0, "N": 0.2, "P": 0.1},
                1,
                2,
            ),
            # Case 3: Not enough for any offspring
            (
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {"C": 0.2, "N": 0.05, "P": 0.02},
                1,
                0,
            ),
            # Case 4: Multiple parents, each able to make 2 offspring
            (
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {"C": 1.0, "N": 0.2, "P": 0.1},
                2,
                4,
            ),
            # Limiting nutrient - phosphorus
            (
                {"C": 0.5, "N": 0.1, "P": 0.05},
                {
                    "C": 10.0,
                    "N": 10.0,
                    "P": 0.1,
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
                birth_mass_cnp["C"],
                birth_mass_cnp["N"],
                birth_mass_cnp["P"],
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
                {"C": 2.0, "N": 0.5, "P": 0.2},
                2,
                (0.5, 0.1, 0.05),  # Per offspring birth mass C, N, P
                {"C": 1.0, "N": 0.3, "P": 0.1},
                False,
            ),
            # Semelparous parent - reproductive mass reduces and parent dies
            (
                "semelparous",
                {"C": 2.0, "N": 0.5, "P": 0.2},
                2,
                (0.5, 0.1, 0.05),
                {"C": 1.0, "N": 0.3, "P": 0.1},
                True,
            ),
            # More offspring than available reproductive mass - cap at available mass
            (
                "iteroparous",
                {"C": 0.5, "N": 0.2, "P": 0.1},
                5,
                (0.5, 0.1, 0.05),
                {"C": 0.0, "N": 0.0, "P": 0.0},
                False,
            ),
            # No offspring at all - nothing should change
            (
                "iteroparous",
                {"C": 2.0, "N": 0.5, "P": 0.2},
                0,
                (0.5, 0.1, 0.05),  # Doesn't matter since 0 offspring
                {"C": 2.0, "N": 0.5, "P": 0.2},
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
        assert herbivore_cohort_instance.reproductive_mass_cnp.C == pytest.approx(
            expected_remaining_mass["C"]
        )
        assert herbivore_cohort_instance.reproductive_mass_cnp.N == pytest.approx(
            expected_remaining_mass["N"]
        )
        assert herbivore_cohort_instance.reproductive_mass_cnp.P == pytest.approx(
            expected_remaining_mass["P"]
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
        herbivore_cohort_instance.mass_cnp = CNP(C=5.0, N=1.0, P=0.5)

        # Mock the loss from calculate_semelparous_mass_loss
        semelparous_loss = {"C": 2.0, "N": 0.5, "P": 0.2}
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
        assert herbivore_cohort_instance.mass_cnp.C == pytest.approx(3.0)
        assert herbivore_cohort_instance.mass_cnp.N == pytest.approx(0.5)
        assert herbivore_cohort_instance.mass_cnp.P == pytest.approx(0.3)

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
                {"C": 10.0, "N": 2.0, "P": 1.0},
                {"C": 5.0, "N": 1.0, "P": 0.5},
            ),
            # Case 2: Iteroparous species (no loss applied)
            (
                "iteroparous",
                {"C": 10.0, "N": 2.0, "P": 1.0},
                {"C": 0.0, "N": 0.0, "P": 0.0},
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
        assert result["C"] == pytest.approx(expected_loss["C"])
        assert result["N"] == pytest.approx(expected_loss["N"])
        assert result["P"] == pytest.approx(expected_loss["P"])

    @pytest.mark.parametrize(
        "birth_mass, cnp_proportions, expected_birth_cnp",
        [
            # Standard balanced case
            (
                1.0,
                {"C": 0.5, "N": 0.3, "P": 0.2},
                (0.5, 0.3, 0.2),
            ),
            # Larger birth mass
            (
                10.0,
                {"C": 0.5, "N": 0.3, "P": 0.2},
                (5.0, 3.0, 2.0),
            ),
            # Zero birth mass (should return all zeros)
            (
                0.0,
                {"C": 0.5, "N": 0.3, "P": 0.2},
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
        from numpy import timedelta64

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
        mock_get_array_resources = mocker.Mock(return_value=["array_resources"])
        mock_get_prey = mocker.Mock(return_value=["prey"])

        # Set up herbivore cohort
        herbivore_cohort_instance.functional_group.diet = DietType.parse(
            "foliage_fruit"
        )
        mocker.patch.object(
            herbivore_cohort_instance, "get_array_resources", mock_get_array_resources
        )
        mocker.patch.object(herbivore_cohort_instance, "get_prey", mocker.Mock())
        mocker.patch.object(
            herbivore_cohort_instance,
            "get_excrement_pools",
            mock_get_excrement_pools_herbivore,
        )
        mocker.patch.object(
            herbivore_cohort_instance, "forage_cohort", mock_forage_herbivore
        )

        # Set up predator cohort
        predator_cohort_instance.functional_group.diet = DietType.parse("vertebrates")
        mocker.patch.object(
            predator_cohort_instance, "get_plant_resources", mocker.Mock()
        )
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

        # Show where AnimalModel comes from (guards against stray imports)
        import inspect

        from virtual_ecosystem.models.animal.animal_model import AnimalModel

        # Guard updated to match new wiring
        assert hasattr(animal_model_instance, "array_resource_pools"), (
            "array_resource_pools missing. "
            f"_setup defined at: {inspect.getsourcefile(AnimalModel._setup)}:"
            f"{inspect.getsourcelines(AnimalModel._setup)[1]} | "
            f"attrs={sorted(vars(animal_model_instance))}"
        )

        for name in (
            "communities",
            "excrement_pools",
            "carcass_pools",
            "herbivory_waste_pools",
        ):
            assert hasattr(animal_model_instance, name), f"Missing {name}"

        # Run the forage_community method
        dt = timedelta64(30, "D")
        animal_model_instance.forage_community(dt=dt)

        # Herbivore: uses array resources, not prey
        mock_get_array_resources.assert_called_once_with(
            animal_model_instance.array_resource_pools
        )
        herbivore_cohort_instance.get_prey.assert_not_called()
        mock_forage_herbivore.assert_called_once_with(
            array_resource_list=["array_resources"],
            animal_list=[],
            fungal_fruit_list=[],
            soil_fungi_list=[],
            pom_list=[],
            bacteria_list=[],
            excrement_pools=["excrement_pools_herbivore"],
            carcass_pool_map=animal_model_instance.carcass_pools,
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools=animal_model_instance.herbivory_waste_pools,
            dt=dt,
        )

        # Predator: uses prey, not plant resources
        expected_prey_flags = predator_cohort_instance.functional_group.diet & (
            DietType.BLOOD
            | DietType.INVERTEBRATES
            | DietType.FISH
            | DietType.VERTEBRATES
        )
        mock_get_prey.assert_called_once_with(
            communities=animal_model_instance.communities,
            prey_diet=expected_prey_flags,
        )
        predator_cohort_instance.get_plant_resources.assert_not_called()
        mock_forage_predator.assert_called_once_with(
            array_resource_list=[],
            animal_list=["prey"],
            fungal_fruit_list=[],
            soil_fungi_list=[],
            pom_list=[],
            bacteria_list=[],
            excrement_pools=["excrement_pools_predator"],
            carcass_pool_map=animal_model_instance.carcass_pools,
            scavenge_carcass_pools=[],
            scavenge_excrement_pools=[],
            herbivory_waste_pools=animal_model_instance.herbivory_waste_pools,
            dt=dt,
        )

    @pytest.mark.parametrize(
        "layout, expected_resp",
        [
            pytest.param(
                {0: [(22.0, 0.40)], 1: []},
                {0: 0.40, 1: 0.0},
                id="single_cohort_occupied_and_empty_cell",
            ),
            pytest.param(
                {0: [(22.0, 0.40), (28.0, 0.90)], 1: []},
                {0: 1.30, 1: 0.0},
                id="two_cohorts_distinct_temperatures",
            ),
            pytest.param(
                {0: [(22.0, 0.40)], 1: [(15.0, 0.20)]},
                {0: 0.40, 1: 0.20},
                id="cohorts_across_two_cells",
            ),
            pytest.param(
                {0: [], 1: []},
                {0: 0.0, 1: 0.0},
                id="all_empty_cells",
            ),
        ],
    )
    def test_metabolize_community(
        self, animal_model_instance, mocker, layout, expected_resp
    ):
        """Test metabolize_community routes climate state and waste across layouts."""
        import numpy as np

        dt = np.timedelta64(1, "D")

        # Build one mock cohort per layout spec entry.
        cell_mocks: dict[int, list] = {}
        for cell_id, specs in layout.items():
            cohorts = []
            for temp, respire_ret in specs:
                m = mocker.Mock()
                m.current_temperature = temp
                m.respire.return_value = respire_ret
                cohorts.append(m)
            cell_mocks[cell_id] = cohorts

        pools = {cell_id: mocker.Mock() for cell_id in layout}

        animal_model_instance.communities = {
            cell_id: cell_mocks[cell_id] for cell_id in layout
        }
        animal_model_instance.excrement_pools = pools
        animal_model_instance.data["total_animal_respiration"].values[:] = 0.0

        animal_model_instance.metabolize_community(dt)

        for cell_id, specs in layout.items():
            for mock, (temp, _) in zip(cell_mocks[cell_id], specs):
                # Temperature routing: cohort's own current_temperature is used.
                mock.metabolize.assert_called_once_with(temp, dt)
                # Waste chaining: respire and excrete both receive the exact object
                # that metabolize returned, confirming it is threaded through once.
                mock.respire.assert_called_once_with(mock.metabolize.return_value)
                mock.excrete.assert_called_once_with(
                    mock.metabolize.return_value, pools[cell_id]
                )

        # Respiration accumulation and empty-cell guard: empty cells contribute 0.0.
        resp = animal_model_instance.data["total_animal_respiration"]
        for cell_id, expected in expected_resp.items():
            assert resp.sel(cell_id=cell_id).item() == pytest.approx(expected)

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
        """Test that update_cohort_bookkeeping calls both age and ontogeny methods."""

        # Spy on the model-level methods
        mocker.spy(prepared_animal_model_instance, "increase_age_community")
        mocker.spy(prepared_animal_model_instance, "handle_ontogeny")

        # Call the method
        prepared_animal_model_instance.update_cohort_bookkeeping(
            dt=np.timedelta64(30, "D")
        )

        # Assert both were called once
        assert prepared_animal_model_instance.increase_age_community.call_count == 1
        assert prepared_animal_model_instance.handle_ontogeny.call_count == 1

    def test_handle_ontogeny_calls_update_on_immature_cohorts(
        self, mocker, prepared_animal_model_instance
    ):
        """Test handle_ontogeny."""

        # Create two mock cohorts
        mock_mature = mocker.Mock()
        mock_mature.is_mature = True
        mock_immature = mocker.Mock()
        mock_immature.is_mature = False

        # Add them to active_cohorts
        prepared_animal_model_instance.active_cohorts = {
            "mature": mock_mature,
            "immature": mock_immature,
        }

        # Call the method
        prepared_animal_model_instance.handle_ontogeny()

        # Assert that only the immature cohort's update_largest_mass was called
        mock_immature.update_largest_mass.assert_called_once()
        mock_mature.update_largest_mass.assert_not_called()

    def test_update_activity_windows_community(self, prepared_animal_model_instance):
        """Test that update_activity_windows_community sets sigma_f_t correctly."""
        from virtual_ecosystem.models.animal.animal_traits import MetabolicType

        prepared_animal_model_instance.update_activity_windows_community()

        for cohort in prepared_animal_model_instance.active_cohorts.values():
            if cohort.functional_group.metabolic_type == MetabolicType.ENDOTHERMIC:
                assert cohort.sigma_f_t == pytest.approx(1.0)
            else:
                assert 0.0 <= cohort.sigma_f_t <= 1.0

    def test_update_activity_windows_community_uses_per_cell_values(
        self, prepared_animal_model_instance
    ):
        """Test that activity windows reflect spatial and strata temperature variation.

        Ectotherm insects have a 1-cell territory. Setting all three strata warm
        in cell 0 and cold everywhere else — including diurnal range — means
        ectotherms centred in cell 0 should have a larger sigma_f_t than those
        centred in cell 1.
        """
        from virtual_ecosystem.models.animal.animal_traits import MetabolicType

        model = prepared_animal_model_instance
        lyr_str = model.layer_structure

        warm = 23.0
        cold = 5.0

        for key in ("air_temperature", "canopy_temperature", "soil_temperature"):
            arr = model.data[key].values
            if key == "air_temperature":
                arr[lyr_str.index_surface_scalar, :] = cold
                arr[lyr_str.index_surface_scalar, 0] = warm
            elif key == "canopy_temperature":
                arr[lyr_str.index_filled_canopy, :] = cold
                arr[lyr_str.index_filled_canopy, 0] = warm
            elif key == "soil_temperature":
                arr[lyr_str.index_topsoil_scalar, :] = cold
                arr[lyr_str.index_topsoil_scalar, 0] = warm

        diurnal = model.data["diurnal_temperature_range"].values
        diurnal[lyr_str.index_filled_canopy, :] = 4.0
        diurnal[lyr_str.index_surface_scalar, :] = 4.0
        diurnal[lyr_str.index_topsoil_scalar, :] = 4.0

        model.update_activity_windows_community()

        ecto_centred_0 = [
            c
            for c in model.active_cohorts.values()
            if c.functional_group.metabolic_type == MetabolicType.ECTOTHERMIC
            and c.centroid_key == 0
        ]
        ecto_centred_1 = [
            c
            for c in model.active_cohorts.values()
            if c.functional_group.metabolic_type == MetabolicType.ECTOTHERMIC
            and c.centroid_key == 1
        ]

        if ecto_centred_0 and ecto_centred_1:
            assert ecto_centred_0[0].sigma_f_t > ecto_centred_1[0].sigma_f_t


def test_to_per_day(prepared_animal_model_instance):
    """Test that helper function to convert to per day rates works."""

    rates = prepared_animal_model_instance.to_per_day(
        change=np.array([10.0, 25.0, 99.0, 34.7])
    )

    assert np.allclose(rates, [0.714285714, 1.7857143, 7.0714286, 2.4785714])
