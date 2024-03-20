"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import numpy as np
import pytest

from tests.conftest import log_check


@pytest.fixture
def prepared_animal_model_instance(
    plant_climate_data_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Animal model instance in which setup has already been run."""
    from virtual_ecosystem.models.animals.animal_model import AnimalModel

    model = AnimalModel(
        data=plant_climate_data_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )
    model.setup()  # Ensure setup is called
    return model


def test_animal_model_initialization(
    plant_climate_data_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Test `AnimalModel` initialization."""
    from virtual_ecosystem.core.base_model import BaseModel
    from virtual_ecosystem.models.animals.animal_model import AnimalModel

    # Initialize model
    model = AnimalModel(
        data=plant_climate_data_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )

    # In cases where it passes then checks that the object has the right properties
    assert isinstance(model, BaseModel)
    assert model.model_name == "animals"
    assert str(model) == "A animals model instance"
    assert repr(model) == "AnimalModel(update_interval=1209600 seconds)"
    assert isinstance(model.communities, dict)


@pytest.mark.parametrize(
    "config_string,raises,expected_log_entries",
    [
        pytest.param(
            """[core.timing]
            start_date = "2020-01-01"
            update_interval = "7 days"
            [[animals.functional_groups]]
            name = "carnivorous_bird"
            taxa = "bird"
            diet = "carnivore"
            metabolic_type = "endothermic"
            birth_mass = 0.1
            adult_mass = 1.0
            [[animals.functional_groups]]
            name = "herbivorous_bird"
            taxa = "bird"
            diet = "herbivore"
            metabolic_type = "endothermic"
            birth_mass = 0.05
            adult_mass = 0.5
            [[animals.functional_groups]]
            name = "carnivorous_mammal"
            taxa = "mammal"
            diet = "carnivore"
            metabolic_type = "endothermic"
            birth_mass = 4.0
            adult_mass = 40.0
            [[animals.functional_groups]]
            name = "herbivorous_mammal"
            taxa = "mammal"
            diet = "herbivore"
            metabolic_type = "endothermic"
            birth_mass = 1.0
            adult_mass = 10.0
            """,
            does_not_raise(),
            (
                (INFO, "Initialised animals.AnimalConsts from config"),
                (
                    INFO,
                    "Information required to initialise the animal model successfully "
                    "extracted.",
                ),
                (INFO, "Adding data array for 'total_animal_respiration'"),
                (INFO, "Adding data array for 'decomposed_excrement'"),
                (INFO, "Adding data array for 'decomposed_carcasses'"),
            ),
            id="success",
        ),
    ],
)
def test_generate_animal_model(
    caplog,
    plant_climate_data_instance,
    config_string,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the animal model behaves as expected."""
    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.models.animals.animal_model import AnimalModel

    # Build the config object and core components
    config = Config(cfg_strings=config_string)
    core_components = CoreComponents(config)
    caplog.clear()

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AnimalModel.from_config(
            data=plant_climate_data_instance,
            core_components=core_components,
            config=config,
        )

        # Run the update step (once this does something should check output)
        model.update(time_index=0)

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_get_community_by_key(animal_model_instance):
    """Test the `get_community_by_key` method."""

    from virtual_ecosystem.models.animals.animal_model import AnimalCommunity

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


def test_update_method_sequence(
    plant_climate_data_instance,
    fixture_core_components,
    functional_group_list_instance,
    constants_instance,
):
    """Test update to ensure it runs the community methods in order.

    As a bonus this test checks that the litter output pools have all been created.
    """
    from unittest.mock import MagicMock

    from virtual_ecosystem.models.animals.animal_model import AnimalModel

    model = AnimalModel(
        data=plant_climate_data_instance,
        core_components=fixture_core_components,
        functional_groups=functional_group_list_instance,
        model_constants=constants_instance,
    )

    # Mock all the methods that are supposed to be called by update
    method_names = [
        "forage_community",
        "migrate_community",
        "birth_community",
        "metabolize_community",
        "inflict_natural_mortality_community",
        "die_cohort_community",
        "increase_age_community",
    ]

    mock_methods = {}
    for method_name in method_names:
        for community in model.communities.values():
            mock_method = MagicMock(name=method_name)
            setattr(community, method_name, mock_method)
            mock_methods[method_name] = mock_method

    model.update(time_index=0)

    # Collect the call sequence
    call_sequence = []
    for mock in mock_methods.values():
        if mock.call_args_list:
            call_sequence.append(mock._mock_name)

    # Assert the methods were called in the expected order
    assert call_sequence == method_names
    # Check that excrement and carcass data is created, all elements are zero as no
    # actual updates have occurred
    assert np.allclose(model.data["decomposed_excrement"], 0.0)
    assert np.allclose(model.data["decomposed_carcasses"], 0.0)


def test_update_method_time_index_argument(
    prepared_animal_model_instance,
):
    """Test update to ensure the time index argument does not create an error."""

    time_index = 5
    prepared_animal_model_instance.update(time_index=time_index)

    assert True


def test_calculate_litter_additions(functional_group_list_instance):
    """Test that litter additions from animal model are calculated correctly."""

    from virtual_ecosystem.core.config import Config
    from virtual_ecosystem.core.core_components import CoreComponents
    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.models.animals.animal_model import AnimalModel

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
    decomposed_excrement = [3.5e3, 5.6e4, 5.9e4, 2.3e6]
    for energy, community in zip(decomposed_excrement, model.communities.values()):
        community.excrement_pool.decomposed_energy = energy

    decomposed_carcasses = [7.5e6, 3.4e7, 8.1e7, 1.7e8]
    for energy, community in zip(decomposed_carcasses, model.communities.values()):
        community.carcass_pool.decomposed_energy = energy

    # Calculate litter additions
    litter_additions = model.calculate_litter_additions()

    # Check that litter addition pools are as expected
    assert np.allclose(
        litter_additions["decomposed_excrement"],
        [5e-08, 8e-07, 8.42857e-07, 3.28571e-05],
    )
    assert np.allclose(
        litter_additions["decomposed_carcasses"],
        [1.0714e-4, 4.8571e-4, 1.15714e-3, 2.42857e-3],
    )

    # Check that the function has reset the pools correctly
    assert np.allclose(
        [
            community.excrement_pool.decomposed_energy
            for community in model.communities.values()
        ],
        0.0,
    )
    assert np.allclose(
        [
            community.carcass_pool.decomposed_energy
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
