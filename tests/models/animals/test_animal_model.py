"""Test module for animal_model.py."""

from contextlib import nullcontext as does_not_raise
from logging import INFO

import numpy as np
import pint
import pytest

from tests.conftest import log_check


@pytest.fixture
def functional_group_list_instance(shared_datadir):
    """Fixture for an animal functional group used in tests."""
    from virtual_rainforest.models.animals.functional_group import (
        import_functional_groups,
    )

    file = shared_datadir / "example_functional_group_import.csv"
    fg_list = import_functional_groups(file)

    return fg_list


def test_animal_model_initialization(
    caplog, data_instance, functional_group_list_instance
):
    """Test `AnimalModel` initialization."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Initialize model
    model = AnimalModel(
        data_instance,
        pint.Quantity("1 week"),
        functional_group_list_instance,
    )

    # In cases where it passes then checks that the object has the right properties
    assert set(["setup", "spinup", "update", "cleanup"]).issubset(dir(model))
    assert model.model_name == "animals"
    assert str(model) == "A animals model instance"
    assert repr(model) == "AnimalModel(update_interval = 1 week)"
    assert type(model.communities) is dict


@pytest.mark.parametrize(
    "config,time_interval,raises,expected_log_entries",
    [
        (
            {},
            None,
            pytest.raises(KeyError),
            (),  # This error isn't handled so doesn't generate logging
        ),
        (
            {
                "core": {
                    "timing": {
                        "start_date": "2020-01-01",
                        "update_interval": "7 days",
                    }
                },
                "animals": {
                    "model_time_step": "12 hours",
                    "functional_groups": (
                        (
                            "carnivorous_bird",
                            "bird",
                            "carnivore",
                            "endothermic",
                            0.1,
                            1.0,
                        ),
                        (
                            "herbivorous_bird",
                            "bird",
                            "herbivore",
                            "endothermic",
                            0.05,
                            0.5,
                        ),
                        (
                            "carnivorous_mammal",
                            "mammal",
                            "carnivore",
                            "endothermic",
                            4.0,
                            40.0,
                        ),
                        (
                            "herbivorous_mammal",
                            "mammal",
                            "herbivore",
                            "endothermic",
                            1.0,
                            10.0,
                        ),
                    ),
                },
            },
            pint.Quantity("7 days"),
            does_not_raise(),
            (
                (
                    INFO,
                    "Information required to initialise the animal model successfully "
                    "extracted.",
                ),
                (INFO, "Adding data array for 'decomposed_excrement'"),
            ),
        ),
    ],
)
def test_generate_animal_model(
    caplog,
    data_instance,
    config,
    time_interval,
    raises,
    expected_log_entries,
):
    """Test that the function to initialise the animal model behaves as expected."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    # Check whether model is initialised (or not) as expected
    with raises:
        model = AnimalModel.from_config(
            data_instance,
            config,
            pint.Quantity(config["core"]["timing"]["update_interval"]),
        )
        assert model.update_interval == time_interval
        # Run the update step (once this does something should check output)
        model.update(time_index=0)

    # Final check that expected logging entries are produced
    log_check(caplog, expected_log_entries)


def test_update_method_sequence(data_instance, functional_group_list_instance):
    """Test update to ensure it runs the community methods in order.

    As a bonus this test checks that the litter output pools have all been created.
    """
    from unittest.mock import MagicMock

    from virtual_rainforest.models.animals.animal_model import AnimalModel

    model = AnimalModel(
        data_instance, pint.Quantity("1 week"), functional_group_list_instance
    )

    # Mock all the methods that are supposed to be called by update
    method_names = [
        "forage_community",
        "migrate_community",
        "birth_community",
        "metabolize_community",
        "mortality_community",
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
    # Check that excrement data is created, all elements are zero as no actual updates
    # have occurred
    assert all(element == 0.0 for element in model.data["decomposed_excrement"])


def test_update_method_time_index_argument(
    data_instance, functional_group_list_instance
):
    """Test update to ensure the time index argument does not create an error."""
    from virtual_rainforest.models.animals.animal_model import AnimalModel

    model = AnimalModel(
        data_instance, pint.Quantity("1 week"), functional_group_list_instance
    )

    time_index = 5
    model.update(time_index=time_index)

    assert True


def test_calculate_litter_additions(functional_group_list_instance):
    """Test that litter additions from animal model are calculated correctly."""

    from virtual_rainforest.core.data import Data
    from virtual_rainforest.core.grid import Grid
    from virtual_rainforest.models.animals import AnimalModel

    # Create a small data object to work with
    grid = Grid(cell_nx=2, cell_ny=2)
    data = Data(grid)

    # Use it to initialise the model
    model = AnimalModel(data, pint.Quantity("1 week"), functional_group_list_instance)

    # Update the waste pools
    decomposed_excrement = [3.5e3, 5.6e4, 5.9e4, 2.3e6]
    for ind, community in enumerate(model.communities.values()):
        community.excrement_pool.decomposed_energy = decomposed_excrement[ind]

    # Calculate litter additions
    litter_additions = model.calculate_litter_additions()

    # Check that litter addition pools are as expected
    assert np.allclose(
        litter_additions["decomposed_excrement"],
        [5e-08, 8e-07, 8.42857e-07, 3.28571e-05],
    )

    # Check that the function has reset the pools correctly
    for community in model.communities.values():
        community.excrement_pool.decomposed_energy = 0.0
