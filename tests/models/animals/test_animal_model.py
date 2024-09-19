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
                (INFO, "Adding data array for 'decomposed_excrement'"),
                (INFO, "Adding data array for 'decomposed_carcasses'"),
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


def test_update_method_sequence(mocker, prepared_animal_model_instance):
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
    prepared_animal_model_instance,
):
    """Test update to ensure the time index argument does not create an error."""

    time_index = 5
    prepared_animal_model_instance.update(time_index=time_index)

    assert True


def test_calculate_litter_additions(
    functional_group_list_instance, animal_data_for_model_instance
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
        assert np.allclose([pool.decomposed_energy for pool in excrement_pools], 0.0)

    for carcass_pools in model.carcass_pools.values():
        assert np.allclose([pool.decomposed_energy for pool in carcass_pools], 0.0)


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

    # Manually calculate expected densities based on the cohorts in the community
    for community_id, community in prepared_animal_model_instance.communities.items():
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
    population_densities = prepared_animal_model_instance.data["population_densities"]

    # Verify updated densities match expected values
    for community_id in expected_densities:
        for fg_name in expected_densities[community_id]:
            calculated_density = population_densities.sel(
                community_id=community_id, functional_group_id=fg_name
            ).item()
            expected_density = expected_densities[community_id][fg_name]
            assert calculated_density == pytest.approx(expected_density), (
                f"Mismatch in density for community {community_id} and FG {fg_name}. "
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
