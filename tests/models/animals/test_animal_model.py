"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import numpy as np
import pytest

from tests.conftest import log_check


@pytest.fixture
def prepared_animal_model_instance(
    animal_data_for_model_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Animal model instance in which setup has already been run."""
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    model = AnimalModel(
        data=animal_data_for_model_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )
    model.setup()  # Ensure setup is called
    return model


def test_animal_model_initialization(
    animal_data_for_model_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Test `AnimalModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    # Initialize model
    model = AnimalModel(
        data=animal_data_for_model_instance,
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
    "config_string,raises,expected_log_entries",
    [
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "7 days"
            [[animal.functional_groups]]
            name = "carnivorous_bird"
            taxa = "bird"
            diet = "carnivore"
            metabolic_type = "endothermic"
            reproductive_type = "iteroparous"
            development_type = "direct"
            development_status = "adult"
            offspring_functional_group = "carnivorous_bird"
            excretion_type = "uricotelic"
            birth_mass = 0.1
            adult_mass = 1.0
            [[animal.functional_groups]]
            name = "herbivorous_bird"
            taxa = "bird"
            diet = "herbivore"
            metabolic_type = "endothermic"
            reproductive_type = "iteroparous"
            development_type = "direct"
            development_status = "adult"
            offspring_functional_group = "herbivorous_bird"
            excretion_type = "uricotelic"
            birth_mass = 0.05
            adult_mass = 0.5
            [[animal.functional_groups]]
            name = "carnivorous_mammal"
            taxa = "mammal"
            diet = "carnivore"
            metabolic_type = "endothermic"
            reproductive_type = "iteroparous"
            development_type = "direct"
            development_status = "adult"
            offspring_functional_group = "carnivorous_mammal"
            excretion_type = "ureotelic"
            birth_mass = 4.0
            adult_mass = 40.0
            [[animal.functional_groups]]
            name = "herbivorous_mammal"
            taxa = "mammal"
            diet = "herbivore"
            metabolic_type = "endothermic"
            reproductive_type = "iteroparous"
            development_type = "direct"
            development_status = "adult"
            offspring_functional_group = "herbivorous_mammal"
            excretion_type = "ureotelic"
            birth_mass = 1.0
            adult_mass = 10.0
            [[animal.functional_groups]]
            name = "carnivorous_insect"
            taxa = "insect"
            diet = "carnivore"
            metabolic_type = "ectothermic"
            reproductive_type = "iteroparous"
            development_type = "direct"
            development_status = "adult"
            offspring_functional_group = "carnivorous_insect"
            excretion_type = "uricotelic"
            birth_mass = 0.001
            adult_mass = 0.01
            [[animal.functional_groups]]
            name = "herbivorous_insect"
            taxa = "insect"
            diet = "herbivore"
            metabolic_type = "ectothermic"
            reproductive_type = "semelparous"
            development_type = "direct"
            development_status = "adult"
            offspring_functional_group = "herbivorous_insect"
            excretion_type = "uricotelic"
            birth_mass = 0.0005
            adult_mass = 0.005
            [[animal.functional_groups]]
            name = "butterfly"
            taxa = "insect"
            diet = "herbivore"
            metabolic_type = "ectothermic"
            reproductive_type = "semelparous"
            development_type = "indirect"
            development_status = "adult"
            offspring_functional_group = "caterpillar"
            excretion_type = "uricotelic"
            birth_mass = 0.0005
            adult_mass = 0.005
            [[animal.functional_groups]]
            name = "caterpillar"
            taxa = "insect"
            diet = "herbivore"
            metabolic_type = "ectothermic"
            reproductive_type = "nonreproductive"
            development_type = "indirect"
            development_status = "larval"
            offspring_functional_group = "butterfly"
            excretion_type = "uricotelic"
            birth_mass = 0.0005
            adult_mass = 0.005
            """,
            does_not_raise(),
            (
                (INFO, "Initialised animal.AnimalConsts from config"),
                (
                    INFO,
                    "Information required to initialise the animal model successfully "
                    "extracted.",
                ),
                (INFO, "Adding data array for 'total_animal_respiration'"),
                (INFO, "Adding data array for 'population_densities'"),
                (INFO, "Adding data array for 'decomposed_excrement_carbon'"),
                (INFO, "Adding data array for 'decomposed_excrement_nitrogen'"),
                (INFO, "Adding data array for 'decomposed_excrement_phosphorus'"),
                (INFO, "Adding data array for 'decomposed_carcasses_carbon'"),
                (INFO, "Adding data array for 'decomposed_carcasses_nitrogen'"),
                (INFO, "Adding data array for 'decomposed_carcasses_phosphorus'"),
            ),
            id="success",
        ),
    ],
)
def test_generate_animal_model(
    caplog,
    animal_data_for_model_instance,
    config_string,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the animal model behaves as expected."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    # Build the config object and core components
    config = Config(cfg_strings=config_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AnimalModel.from_config(
            data=animal_data_for_model_instance,
            core_components=core_components,
            config=config,
        )

        # Run the update step (once this does something should check output)
        model.update(time_index=0)

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)

    for record in caplog.records:
        print(f"Level: {record.levelname}, Message: {record.message}")


def test_get_community_by_key(animal_model_instance):
    """Test the `get_community_by_key` method."""

    from virtual_ecosystem.models.animal.animal_model import AnimalCommunity

    # If you know that your model_instance should have a community with key 0
    community_0 = animal_model_instance.get_community_by_key(0)

    # Ensure it returns the right type and the community key matches
    assert isinstance(
        community_0, AnimalCommunity
    ), "Expected instance of AnimalCommunity"
    assert community_0.community_key == 0, "Expected the community with key 0"

    # Perhaps you have more keys you expect, you can add similar checks:
    community_1 = animal_model_instance.get_community_by_key(1)
    assert isinstance(community_1, AnimalCommunity)
    assert community_1.community_key == 1, "Expected the community with key 1"

    # Test for an invalid key, expecting an error
    with pytest.raises(KeyError):
        animal_model_instance.get_community_by_key(999)


def test_update_method_sequence(mocker, prepared_animal_model_instance):
    """Test update to ensure it runs the community methods in order."""
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

    # Setup mock methods using spy
    for community in prepared_animal_model_instance.communities.values():
        for method_name in method_names:
            mocker.spy(community, method_name)

    prepared_animal_model_instance.update(time_index=0)

    # Now, let's verify the order of the calls for each community
    for community in prepared_animal_model_instance.communities.values():
        called_methods = []
        for method_name in method_names:
            method = getattr(community, method_name)
            # If the method was called, add its name to the list
            if method.spy_return is not None or method.call_count > 0:
                called_methods.append(method_name)

        # Verify the called_methods list matches the expected method_names list
        assert (
            called_methods == method_names
        ), f"Methods called in wrong order: {called_methods} for community {community}"


def test_update_method_time_index_argument(
    prepared_animal_model_instance,
):
    """Test update to ensure the time index argument does not create an error."""

    time_index = 5
    prepared_animal_model_instance.update(time_index=time_index)

    assert True


def test_populate_litter_pools(
    litter_data_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Test that function to populate animal consumable litter pool works properly."""
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    model = AnimalModel(
        data=litter_data_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )

    litter_pools = model.populate_litter_pools()
    # Check that all five pools have been populated, with the correct values
    pool_names = [
        "above_metabolic",
        "above_structural",
        "woody",
        "below_metabolic",
        "below_structural",
    ]
    for pool_name in pool_names:
        assert np.allclose(
            litter_pools[pool_name].mass_current,
            litter_data_instance[f"litter_pool_{pool_name}"]
            * fixture_core_components.grid.cell_area,
        )
        assert np.allclose(
            litter_pools[pool_name].c_n_ratio,
            litter_data_instance[f"c_n_ratio_{pool_name}"],
        )
        assert np.allclose(
            litter_pools[pool_name].c_p_ratio,
            litter_data_instance[f"c_p_ratio_{pool_name}"],
        )


def test_calculate_total_litter_consumption(
    litter_data_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Test that calculation of total consumption of litter by animals is correct."""
    from copy import deepcopy

    from virtual_ecosystem.models.animal.animal_model import AnimalModel
    from virtual_ecosystem.models.animal.decay import LitterPool

    model = AnimalModel(
        data=litter_data_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )

    new_data = deepcopy(litter_data_instance)
    # Add new values for each pool
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

    # Make an updated set of litter pools
    pool_names = [
        "above_metabolic",
        "above_structural",
        "woody",
        "below_metabolic",
        "below_structural",
    ]
    new_litter_pools = {
        pool_name: LitterPool(
            pool_name=pool_name,
            data=new_data,
            cell_area=fixture_core_components.grid.cell_area,
        )
        for pool_name in pool_names
    }

    # Calculate litter consumption
    consumption = model.calculate_total_litter_consumption(
        litter_pools=new_litter_pools
    )

    assert np.allclose(
        consumption["litter_consumption_above_metabolic"],
        0.03 * np.ones(4),
    )
    assert np.allclose(
        consumption["litter_consumption_above_structural"],
        0.04 * np.ones(4),
    )
    assert np.allclose(
        consumption["litter_consumption_woody"],
        1.2 * np.ones(4),
    )
    assert np.allclose(
        consumption["litter_consumption_below_metabolic"],
        0.06 * np.ones(4),
    )
    assert np.allclose(
        consumption["litter_consumption_below_structural"],
        0.01 * np.ones(4),
    )


def test_calculate_soil_additions(functional_group_list_instance):
    """Test that soil additions from animal model are calculated correctly."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.animal.animal_model import AnimalModel

    # Build the config object and core components
    config = Config(cfg_strings='[core.timing]\nupdate_interval="1 week"')
    core_components = CoreComponents(config)

    # Create a small data object to work with
    grid = Grid(cell_nx=2, cell_ny=2)
    data = Data(grid)

    # Use it to initialise the model
    model = AnimalModel(
        data=data,
        core_components=core_components,
        functional_groups=functional_group_list_instance,
    )

    # Update the waste pools
    decomposed_excrement_carbon = [3.5e-3, 5.6e-2, 5.9e-2, 2.3e0]
    for carbon, community in zip(
        decomposed_excrement_carbon, model.communities.values()
    ):
        community.excrement_pool.decomposed_carbon = carbon
    decomposed_excrement_nitrogen = [2.4e-4, 7.3e-3, 3.4e-3, 9.3e-2]
    for nitrogen, community in zip(
        decomposed_excrement_nitrogen, model.communities.values()
    ):
        community.excrement_pool.decomposed_nitrogen = nitrogen
    decomposed_excrement_phosphorus = [5.4e-6, 1.7e-4, 4.5e-5, 9.8e-5]
    for phosphorus, community in zip(
        decomposed_excrement_phosphorus, model.communities.values()
    ):
        community.excrement_pool.decomposed_phosphorus = phosphorus

    decomposed_carcasses_carbon = [1.7e2, 7.5e0, 3.4e1, 8.1e1]
    for carbon, community in zip(
        decomposed_carcasses_carbon, model.communities.values()
    ):
        community.carcass_pool.decomposed_carbon = carbon
    decomposed_carcasses_nitrogen = [9.3e-2, 2.4e-4, 7.3e-3, 3.4e-3]
    for nitrogen, community in zip(
        decomposed_carcasses_nitrogen, model.communities.values()
    ):
        community.carcass_pool.decomposed_nitrogen = nitrogen
    decomposed_carcasses_phosphorus = [9.8e-5, 5.4e-6, 1.7e-4, 4.5e-5]
    for phosphorus, community in zip(
        decomposed_carcasses_phosphorus, model.communities.values()
    ):
        community.carcass_pool.decomposed_phosphorus = phosphorus

    # Calculate litter additions
    soil_additions = model.calculate_soil_additions()

    # Check that litter addition pools are as expected
    assert np.allclose(
        soil_additions["decomposed_excrement_carbon"],
        [5e-08, 8e-07, 8.42857e-07, 3.28571e-05],
    )
    assert np.allclose(
        soil_additions["decomposed_excrement_nitrogen"],
        [3.4285714e-9, 1.0428571e-7, 4.8571429e-8, 1.3285714e-6],
    )
    assert np.allclose(
        soil_additions["decomposed_excrement_phosphorus"],
        [7.7142857e-11, 2.4285714e-9, 6.4285714e-10, 1.4e-9],
    )
    assert np.allclose(
        soil_additions["decomposed_carcasses_carbon"],
        [2.42857e-3, 1.0714e-4, 4.8571e-4, 1.15714e-3],
    )
    assert np.allclose(
        soil_additions["decomposed_carcasses_nitrogen"],
        [1.3285714e-6, 3.4285714e-9, 1.0428571e-7, 4.8571429e-8],
    )
    assert np.allclose(
        soil_additions["decomposed_carcasses_phosphorus"],
        [1.4e-9, 7.7142857e-11, 2.4285714e-9, 6.4285714e-10],
    )

    # Check that the function has reset the pools correctly
    assert np.allclose(
        [
            community.excrement_pool.decomposed_carbon
            for community in model.communities.values()
        ],
        0.0,
    )
    assert np.allclose(
        [
            community.carcass_pool.decomposed_carbon
            for community in model.communities.values()
        ],
        0.0,
    )
    assert np.allclose(
        [
            community.excrement_pool.decomposed_nitrogen
            for community in model.communities.values()
        ],
        0.0,
    )
    assert np.allclose(
        [
            community.carcass_pool.decomposed_nitrogen
            for community in model.communities.values()
        ],
        0.0,
    )
    assert np.allclose(
        [
            community.excrement_pool.decomposed_phosphorus
            for community in model.communities.values()
        ],
        0.0,
    )
    assert np.allclose(
        [
            community.carcass_pool.decomposed_phosphorus
            for community in model.communities.values()
        ],
        0.0,
    )


def test_setup_initializes_total_animal_respiration(
    prepared_animal_model_instance,
):
    """Test that the setup method initializes the total_animal_respiration variable."""
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
    # This is useful if your setup method is supposed to initialize the data variable
    # with specific dimensions or coordinates based on your model's structure
    assert (
        "cell_id" in total_animal_respiration.dims
    ), "'cell_id' should be a dimension of 'total_animal_respiration'."


def test_population_density_initialization(
    prepared_animal_model_instance,
):
    """Test the initialization of the population density data variable."""

    # Check that 'population_densities' is in the data
    assert (
        "population_densities" in prepared_animal_model_instance.data.data.data_vars
    ), "'population_densities' data variable not found in Data object after setup."

    # Retrieve the population densities data variable
    population_densities = prepared_animal_model_instance.data["population_densities"]

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
    ), "Functional group names in 'population_densities' do not match expected values."

    # Assuming densities have been updated, check if densities are greater than or equal
    # to zero
    assert np.all(
        population_densities.values >= 0
    ), "Population densities should be greater than or equal to zero."


def test_update_population_densities(prepared_animal_model_instance):
    """Test that the update_population_densities method correctly updates."""

    # Set up expected densities
    expected_densities = {}

    # For simplicity in this example, assume we manually calculate expected densities
    # based on your cohort setup logic. In practice, you would calculate these
    # based on your specific test setup conditions.
    for community_id, community in prepared_animal_model_instance.communities.items():
        expected_densities[community_id] = {}
        for fg_name, cohorts in community.animal_cohorts.items():
            total_individuals = sum(cohort.individuals for cohort in cohorts)
            community_area = prepared_animal_model_instance.data.grid.cell_area
            density = total_individuals / community_area
            expected_densities[community_id][fg_name] = density

    # Run the method under test
    prepared_animal_model_instance.update_population_densities()

    # Retrieve the updated population densities data variable
    population_densities = prepared_animal_model_instance.data["population_densities"]

    # Verify updated densities match expected values
    for community_id in expected_densities:
        for fg_name in expected_densities[community_id]:
            calculated_density = population_densities.sel(
                community_id=community_id, functional_group_id=fg_name
            ).item()
            expected_density = expected_densities[community_id][fg_name]
            assert calculated_density == pytest.approx(expected_density), (
                f"Mismatch in density for community {community_id} and FG{fg_name}. "
                f"Expected: {expected_density}, Found: {calculated_density}"
            )


def test_calculate_density_for_cohort(prepared_animal_model_instance, mocker):
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
    calculated_density = prepared_animal_model_instance.calculate_density_for_cohort(
        mock_cohort
    )

    # Assert the calculated density matches the expected density
    assert calculated_density == pytest.approx(expected_density), (
        f"Calculated density ({calculated_density}) "
        f"did not match expected density ({expected_density})."
    )
